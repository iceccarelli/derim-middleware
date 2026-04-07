"""
InfluxDB time-series storage backend.

This module implements the ``StorageBackend`` interface using InfluxDB v2.x
as the underlying database.  It uses the official ``influxdb-client``
Python library for both writes (line protocol) and queries (Flux).

InfluxDB is the recommended backend for production deployments due to its
purpose-built time-series engine, automatic downsampling, and high write
throughput.

Data Layout
-----------
- **Measurement**: ``der_telemetry``
- **Tags**: ``device_id``, ``device_type``, ``state``
- **Fields**: ``power_kw``, ``energy_kwh``, ``voltage_v``, ``current_a``,
  ``frequency_hz``, ``power_factor``, ``reactive_power_kvar``
- **Timestamp**: nanosecond-precision UTC

Device registry records are stored in a separate measurement
``der_devices``.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Optional

from derim.models.common import DERDevice, DERTelemetry, DERType, DeviceState
from derim.storage.base import StorageBackend
from derim.utils.logger import get_logger

logger = get_logger(__name__)


class InfluxDBStorage(StorageBackend):
    """
    InfluxDB v2.x storage backend.

    Parameters
    ----------
    url : str
        InfluxDB server URL (e.g. ``http://localhost:8086``).
    token : str
        Authentication token with read/write permissions.
    org : str
        InfluxDB organisation name.
    bucket : str
        Target bucket for telemetry data.
    """

    def __init__(
        self,
        url: str = "http://localhost:8086",
        token: str = "",
        org: str = "derim",
        bucket: str = "derim_telemetry",
    ):
        self._url = url
        self._token = token
        self._org = org
        self._bucket = bucket
        self._client: Any = None
        self._write_api: Any = None
        self._query_api: Any = None

        # In-memory device registry (mirrored to InfluxDB).
        self._devices: dict[str, DERDevice] = {}

    async def connect(self) -> None:
        """
        Initialise the InfluxDB client and verify connectivity.

        Raises
        ------
        ConnectionError
            If InfluxDB is unreachable or credentials are invalid.
        """
        try:
            from influxdb_client import InfluxDBClient
            from influxdb_client.client.write_api import SYNCHRONOUS

            self._client = InfluxDBClient(
                url=self._url,
                token=self._token,
                org=self._org,
            )

            # Verify connectivity.
            health = self._client.health()
            if health.status != "pass":
                raise ConnectionError(f"InfluxDB health check failed: {health.message}")

            self._write_api = self._client.write_api(write_options=SYNCHRONOUS)
            self._query_api = self._client.query_api()

            logger.info(
                "influxdb_connected",
                url=self._url,
                org=self._org,
                bucket=self._bucket,
            )

        except ImportError as exc:
            raise ImportError(
                "influxdb-client is required. "
                "Install it with: pip install influxdb-client"
            ) from exc
        except Exception as exc:
            logger.error("influxdb_connection_failed", error=str(exc))
            raise ConnectionError(f"InfluxDB connection failed: {exc}") from exc

    async def disconnect(self) -> None:
        """Close the InfluxDB client connection."""
        if self._client is not None:
            self._client.close()
            logger.info("influxdb_disconnected")

    async def write_points(self, data: list[DERTelemetry]) -> None:
        """
        Write telemetry records to InfluxDB using line protocol.

        Parameters
        ----------
        data : list[DERTelemetry]
            Telemetry records to persist.
        """
        if not data:
            return

        try:
            from influxdb_client import Point, WritePrecision

            points = []
            for record in data:
                point = (
                    Point("der_telemetry")
                    .tag("device_id", record.device_id)
                    .tag("device_type", record.device_type.value)
                    .tag("state", record.state.value)
                    .field("power_kw", record.power_kw)
                    .field("energy_kwh", record.energy_kwh)
                    .field("voltage_v", record.voltage_v)
                    .field("current_a", record.current_a)
                    .field("frequency_hz", record.frequency_hz)
                    .time(record.timestamp, WritePrecision.NS)
                )

                if record.power_factor is not None:
                    point = point.field("power_factor", record.power_factor)
                if record.reactive_power_kvar is not None:
                    point = point.field(
                        "reactive_power_kvar", record.reactive_power_kvar
                    )

                points.append(point)

            self._write_api.write(bucket=self._bucket, org=self._org, record=points)

            logger.debug(
                "influxdb_points_written",
                count=len(points),
                device_id=data[0].device_id,
            )

        except Exception as exc:
            logger.error("influxdb_write_failed", error=str(exc))
            raise IOError(f"InfluxDB write failed: {exc}") from exc

    async def query_range(
        self,
        device_id: str,
        start: datetime,
        end: datetime,
        limit: int = 1000,
    ) -> list[DERTelemetry]:
        """
        Query telemetry records from InfluxDB using Flux.

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
            Matching records ordered by time.
        """
        try:
            flux_query = f"""
                from(bucket: "{self._bucket}")
                    |> range(start: {start.isoformat()}Z, stop: {end.isoformat()}Z)
                    |> filter(fn: (r) => r._measurement == "der_telemetry")
                    |> filter(fn: (r) => r.device_id == "{device_id}")
                    |> pivot(rowKey: ["_time"], columnKey: ["_field"], valueColumn: "_value")
                    |> sort(columns: ["_time"])
                    |> limit(n: {limit})
            """

            tables = self._query_api.query(flux_query, org=self._org)
            results: list[DERTelemetry] = []

            for table in tables:
                for record in table.records:
                    vals = record.values
                    try:
                        device_type = DERType(vals.get("device_type", "generic"))
                    except ValueError:
                        device_type = DERType.GENERIC
                    try:
                        state = DeviceState(vals.get("state", "unknown"))
                    except ValueError:
                        state = DeviceState.UNKNOWN

                    results.append(
                        DERTelemetry(
                            timestamp=record.get_time(),
                            device_id=device_id,
                            device_type=device_type,
                            power_kw=vals.get("power_kw", 0.0),
                            energy_kwh=vals.get("energy_kwh", 0.0),
                            voltage_v=vals.get("voltage_v", 0.0),
                            current_a=vals.get("current_a", 0.0),
                            frequency_hz=vals.get("frequency_hz", 50.0),
                            state=state,
                            power_factor=vals.get("power_factor"),
                            reactive_power_kvar=vals.get("reactive_power_kvar"),
                        )
                    )

            return results

        except Exception as exc:
            logger.error(
                "influxdb_query_failed",
                device_id=device_id,
                error=str(exc),
            )
            return []

    async def register_device(self, device: DERDevice) -> None:
        """Register or update a device in the in-memory registry."""
        self._devices[device.device_id] = device
        logger.info("device_registered", device_id=device.device_id)

    async def get_devices(self) -> list[DERDevice]:
        """Return all registered devices."""
        return list(self._devices.values())

    async def get_device(self, device_id: str) -> Optional[DERDevice]:
        """Return a device by ID, or ``None`` if not found."""
        return self._devices.get(device_id)
