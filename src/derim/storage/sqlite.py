"""
SQLite time-series storage backend (fallback).

This module implements the ``StorageBackend`` interface using SQLite as
a lightweight, zero-configuration alternative to InfluxDB.  It is ideal
for development, testing, and single-node deployments where installing
a dedicated time-series database is not practical.

The implementation uses ``aiosqlite`` for non-blocking database access
within the async FastAPI application.

Schema
------
Two tables are created automatically on first connection:

- ``telemetry``: Stores ``DERTelemetry`` records as JSON blobs with
  indexed ``device_id`` and ``timestamp`` columns for efficient range
  queries.
- ``devices``: Stores ``DERDevice`` registration records.
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

import aiosqlite

from derim.models.common import DERDevice, DERTelemetry, DERType, DeviceState
from derim.storage.base import StorageBackend
from derim.utils.logger import get_logger

logger = get_logger(__name__)

# SQL statements for schema creation.
CREATE_TELEMETRY_TABLE = """
CREATE TABLE IF NOT EXISTS telemetry (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    device_id   TEXT    NOT NULL,
    timestamp   TEXT    NOT NULL,
    device_type TEXT    NOT NULL DEFAULT 'generic',
    power_kw    REAL    NOT NULL DEFAULT 0.0,
    energy_kwh  REAL    NOT NULL DEFAULT 0.0,
    voltage_v   REAL    NOT NULL DEFAULT 0.0,
    current_a   REAL    NOT NULL DEFAULT 0.0,
    frequency_hz REAL   NOT NULL DEFAULT 50.0,
    state       TEXT    NOT NULL DEFAULT 'unknown',
    power_factor REAL,
    reactive_power_kvar REAL,
    metadata_json TEXT
);
"""

CREATE_TELEMETRY_INDEX = """
CREATE INDEX IF NOT EXISTS idx_telemetry_device_time
    ON telemetry (device_id, timestamp);
"""

CREATE_DEVICES_TABLE = """
CREATE TABLE IF NOT EXISTS devices (
    device_id    TEXT PRIMARY KEY,
    device_type  TEXT NOT NULL,
    name         TEXT NOT NULL,
    location     TEXT,
    protocol     TEXT,
    rated_power_kw REAL,
    state        TEXT NOT NULL DEFAULT 'unknown',
    metadata_json TEXT
);
"""


class SQLiteStorage(StorageBackend):
    """
    SQLite-based storage backend for development and testing.

    Parameters
    ----------
    db_path : str
        Path to the SQLite database file.  The file and any missing
        parent directories are created automatically.
    """

    def __init__(self, db_path: str = "./data/derim.db"):
        self._db_path = db_path
        self._db: Optional[aiosqlite.Connection] = None

    async def connect(self) -> None:
        """
        Open the SQLite database and create tables if needed.

        Raises
        ------
        ConnectionError
            If the database file cannot be opened.
        """
        try:
            # Ensure parent directory exists.
            Path(self._db_path).parent.mkdir(parents=True, exist_ok=True)

            self._db = await aiosqlite.connect(self._db_path)
            self._db.row_factory = aiosqlite.Row

            # Enable WAL mode for better concurrent read performance.
            await self._db.execute("PRAGMA journal_mode=WAL;")
            await self._db.execute("PRAGMA synchronous=NORMAL;")

            # Create schema.
            await self._db.execute(CREATE_TELEMETRY_TABLE)
            await self._db.execute(CREATE_TELEMETRY_INDEX)
            await self._db.execute(CREATE_DEVICES_TABLE)
            await self._db.commit()

            logger.info("sqlite_connected", db_path=self._db_path)

        except Exception as exc:
            logger.error("sqlite_connection_failed", error=str(exc))
            raise ConnectionError(f"SQLite connection failed: {exc}") from exc

    async def disconnect(self) -> None:
        """Close the SQLite database connection."""
        if self._db is not None:
            await self._db.close()
            self._db = None
            logger.info("sqlite_disconnected")

    async def write_points(self, data: list[DERTelemetry]) -> None:
        """
        Insert telemetry records into the ``telemetry`` table.

        Parameters
        ----------
        data : list[DERTelemetry]
            Records to persist.
        """
        if not data or self._db is None:
            return

        try:
            rows = [
                (
                    record.device_id,
                    record.timestamp.isoformat(),
                    record.device_type.value,
                    record.power_kw,
                    record.energy_kwh,
                    record.voltage_v,
                    record.current_a,
                    record.frequency_hz,
                    record.state.value,
                    record.power_factor,
                    record.reactive_power_kvar,
                    json.dumps(record.metadata) if record.metadata else None,
                )
                for record in data
            ]

            await self._db.executemany(
                """
                INSERT INTO telemetry
                    (device_id, timestamp, device_type, power_kw, energy_kwh,
                     voltage_v, current_a, frequency_hz, state,
                     power_factor, reactive_power_kvar, metadata_json)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                rows,
            )
            await self._db.commit()

            logger.debug(
                "sqlite_points_written",
                count=len(rows),
                device_id=data[0].device_id,
            )

        except Exception as exc:
            logger.error("sqlite_write_failed", error=str(exc))
            raise IOError(f"SQLite write failed: {exc}") from exc

    async def query_range(
        self,
        device_id: str,
        start: datetime,
        end: datetime,
        limit: int = 1000,
    ) -> list[DERTelemetry]:
        """
        Query telemetry records for a device within a time range.

        Parameters
        ----------
        device_id : str
            Device to query.
        start : datetime
            Start of the time range (UTC).
        end : datetime
            End of the time range (UTC).
        limit : int
            Maximum number of records.

        Returns
        -------
        list[DERTelemetry]
            Matching records ordered by timestamp.
        """
        if self._db is None:
            return []

        try:
            cursor = await self._db.execute(
                """
                SELECT device_id, timestamp, device_type, power_kw,
                       energy_kwh, voltage_v, current_a, frequency_hz,
                       state, power_factor, reactive_power_kvar,
                       metadata_json
                FROM telemetry
                WHERE device_id = ?
                  AND timestamp >= ?
                  AND timestamp <= ?
                ORDER BY timestamp ASC
                LIMIT ?
                """,
                (device_id, start.isoformat(), end.isoformat(), limit),
            )

            rows = await cursor.fetchall()
            results: list[DERTelemetry] = []

            for row in rows:
                try:
                    device_type = DERType(row["device_type"])
                except ValueError:
                    device_type = DERType.GENERIC
                try:
                    state = DeviceState(row["state"])
                except ValueError:
                    state = DeviceState.UNKNOWN

                metadata = None
                if row["metadata_json"]:
                    try:
                        metadata = json.loads(row["metadata_json"])
                    except json.JSONDecodeError:
                        pass

                results.append(
                    DERTelemetry(
                        timestamp=datetime.fromisoformat(row["timestamp"]),
                        device_id=row["device_id"],
                        device_type=device_type,
                        power_kw=row["power_kw"],
                        energy_kwh=row["energy_kwh"],
                        voltage_v=row["voltage_v"],
                        current_a=row["current_a"],
                        frequency_hz=row["frequency_hz"],
                        state=state,
                        power_factor=row["power_factor"],
                        reactive_power_kvar=row["reactive_power_kvar"],
                        metadata=metadata,
                    )
                )

            return results

        except Exception as exc:
            logger.error(
                "sqlite_query_failed",
                device_id=device_id,
                error=str(exc),
            )
            return []

    async def register_device(self, device: DERDevice) -> None:
        """
        Insert or update a device in the ``devices`` table.

        Uses SQLite ``INSERT OR REPLACE`` (upsert) semantics.
        """
        if self._db is None:
            return

        try:
            await self._db.execute(
                """
                INSERT OR REPLACE INTO devices
                    (device_id, device_type, name, location, protocol,
                     rated_power_kw, state, metadata_json)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    device.device_id,
                    device.device_type.value,
                    device.name,
                    device.location,
                    device.protocol,
                    device.rated_power_kw,
                    device.state.value,
                    json.dumps(device.metadata) if device.metadata else None,
                ),
            )
            await self._db.commit()
            logger.info("sqlite_device_registered", device_id=device.device_id)

        except Exception as exc:
            logger.error(
                "sqlite_device_register_failed",
                device_id=device.device_id,
                error=str(exc),
            )

    async def get_devices(self) -> list[DERDevice]:
        """Return all registered devices from the ``devices`` table."""
        if self._db is None:
            return []

        try:
            cursor = await self._db.execute("SELECT * FROM devices ORDER BY device_id")
            rows = await cursor.fetchall()
            return [self._row_to_device(row) for row in rows]
        except Exception as exc:
            logger.error("sqlite_get_devices_failed", error=str(exc))
            return []

    async def get_device(self, device_id: str) -> Optional[DERDevice]:
        """Return a single device by ID."""
        if self._db is None:
            return None

        try:
            cursor = await self._db.execute(
                "SELECT * FROM devices WHERE device_id = ?", (device_id,)
            )
            row = await cursor.fetchone()
            if row is None:
                return None
            return self._row_to_device(row)
        except Exception as exc:
            logger.error(
                "sqlite_get_device_failed",
                device_id=device_id,
                error=str(exc),
            )
            return None

    @staticmethod
    def _row_to_device(row: Any) -> DERDevice:
        """Convert a database row to a ``DERDevice`` instance."""
        try:
            device_type = DERType(row["device_type"])
        except ValueError:
            device_type = DERType.GENERIC
        try:
            state = DeviceState(row["state"])
        except ValueError:
            state = DeviceState.UNKNOWN

        metadata = None
        if row["metadata_json"]:
            try:
                metadata = json.loads(row["metadata_json"])
            except json.JSONDecodeError:
                pass

        return DERDevice(
            device_id=row["device_id"],
            device_type=device_type,
            name=row["name"],
            location=row["location"],
            protocol=row["protocol"],
            rated_power_kw=row["rated_power_kw"],
            state=state,
            metadata=metadata,
        )
