"""
Unit tests for the DERIM storage backends.

Tests cover:
- SQLite storage: connect, write, query, device registration.
- Storage factory: backend selection based on configuration.
- Edge cases: empty queries, large batch writes.
"""

from datetime import datetime, timedelta, timezone

import pytest

from derim.config import Settings, StorageBackendType
from derim.models.common import DERDevice, DERTelemetry, DERType, DeviceState
from derim.storage.sqlite import SQLiteStorage


class TestSQLiteStorage:
    """Tests for the SQLite storage backend."""

    @pytest.mark.asyncio
    async def test_connect_creates_database(self, tmp_path):
        """Connecting should create the database file and tables."""
        db_path = str(tmp_path / "test.db")
        storage = SQLiteStorage(db_path=db_path)
        await storage.connect()

        assert storage._db is not None
        await storage.disconnect()

    @pytest.mark.asyncio
    async def test_write_and_query_telemetry(self, sqlite_storage, sample_telemetry):
        """Written telemetry should be retrievable via query_range."""
        await sqlite_storage.write_points(sample_telemetry)

        results = await sqlite_storage.query_range(
            device_id="test-solar-001",
            start=datetime(2025, 6, 1, 0, 0, 0, tzinfo=timezone.utc),
            end=datetime(2025, 6, 2, 0, 0, 0, tzinfo=timezone.utc),
            limit=100,
        )

        assert len(results) == 10
        assert results[0].device_id == "test-solar-001"
        assert results[0].power_kw == pytest.approx(3.5, abs=0.01)

    @pytest.mark.asyncio
    async def test_query_empty_range(self, sqlite_storage):
        """Querying an empty range should return an empty list."""
        results = await sqlite_storage.query_range(
            device_id="nonexistent-device",
            start=datetime(2025, 1, 1, tzinfo=timezone.utc),
            end=datetime(2025, 1, 2, tzinfo=timezone.utc),
        )
        assert results == []

    @pytest.mark.asyncio
    async def test_query_with_limit(self, sqlite_storage, sample_telemetry):
        """Query should respect the limit parameter."""
        await sqlite_storage.write_points(sample_telemetry)

        results = await sqlite_storage.query_range(
            device_id="test-solar-001",
            start=datetime(2025, 6, 1, 0, 0, 0, tzinfo=timezone.utc),
            end=datetime(2025, 6, 2, 0, 0, 0, tzinfo=timezone.utc),
            limit=5,
        )
        assert len(results) == 5

    @pytest.mark.asyncio
    async def test_write_empty_list(self, sqlite_storage):
        """Writing an empty list should not raise an error."""
        await sqlite_storage.write_points([])

    @pytest.mark.asyncio
    async def test_register_and_get_device(self, sqlite_storage, sample_device):
        """Registered devices should be retrievable."""
        await sqlite_storage.register_device(sample_device)

        device = await sqlite_storage.get_device("test-solar-001")
        assert device is not None
        assert device.name == "Test Solar Inverter"
        assert device.device_type == DERType.SOLAR_PV

    @pytest.mark.asyncio
    async def test_get_nonexistent_device(self, sqlite_storage):
        """Getting a non-existent device should return None."""
        device = await sqlite_storage.get_device("nonexistent")
        assert device is None

    @pytest.mark.asyncio
    async def test_list_devices(
        self, sqlite_storage, sample_device, sample_battery_device
    ):
        """get_devices should return all registered devices."""
        await sqlite_storage.register_device(sample_device)
        await sqlite_storage.register_device(sample_battery_device)

        devices = await sqlite_storage.get_devices()
        assert len(devices) == 2
        device_ids = {d.device_id for d in devices}
        assert "test-solar-001" in device_ids
        assert "test-bess-001" in device_ids

    @pytest.mark.asyncio
    async def test_upsert_device(self, sqlite_storage, sample_device):
        """Registering the same device_id should update the record."""
        await sqlite_storage.register_device(sample_device)

        updated = DERDevice(
            device_id="test-solar-001",
            device_type=DERType.SOLAR_PV,
            name="Updated Solar Inverter",
            location="New Location",
            rated_power_kw=7.5,
            state=DeviceState.ON,
        )
        await sqlite_storage.register_device(updated)

        device = await sqlite_storage.get_device("test-solar-001")
        assert device is not None
        assert device.name == "Updated Solar Inverter"
        assert device.rated_power_kw == 7.5

    @pytest.mark.asyncio
    async def test_telemetry_ordering(self, sqlite_storage, sample_telemetry):
        """Results should be ordered by timestamp ascending."""
        await sqlite_storage.write_points(sample_telemetry)

        results = await sqlite_storage.query_range(
            device_id="test-solar-001",
            start=datetime(2025, 6, 1, 0, 0, 0, tzinfo=timezone.utc),
            end=datetime(2025, 6, 2, 0, 0, 0, tzinfo=timezone.utc),
        )

        for i in range(1, len(results)):
            assert results[i].timestamp >= results[i - 1].timestamp

    @pytest.mark.asyncio
    async def test_large_batch_write(self, sqlite_storage):
        """Writing a large batch should succeed without errors."""
        base_time = datetime(2025, 6, 1, 0, 0, 0, tzinfo=timezone.utc)
        records = [
            DERTelemetry(
                timestamp=base_time + timedelta(minutes=15 * i),
                device_id="batch-device",
                power_kw=float(i % 50) / 10,
            )
            for i in range(500)
        ]
        await sqlite_storage.write_points(records)

        results = await sqlite_storage.query_range(
            device_id="batch-device",
            start=base_time,
            end=base_time + timedelta(days=10),
            limit=1000,
        )
        assert len(results) == 500


class TestStorageFactory:
    """Tests for the storage factory function."""

    def test_create_sqlite_storage(self, tmp_path):
        """Factory should create SQLiteStorage for 'sqlite' backend."""
        from derim.storage import get_storage_backend

        settings = Settings(
            storage_backend=StorageBackendType.SQLITE,
            sqlite_db_path=str(tmp_path / "factory_test.db"),
        )

        storage = get_storage_backend(settings)
        assert isinstance(storage, SQLiteStorage)

    def test_create_influxdb_storage(self, tmp_path):
        """Factory should create InfluxDBStorage for 'influxdb' backend."""
        from derim.storage import get_storage_backend
        from derim.storage.influxdb import InfluxDBStorage

        settings = Settings(
            storage_backend=StorageBackendType.INFLUXDB,
            influxdb_url="http://localhost:8086",
            influxdb_token="test-token",
            influxdb_org="test-org",
            influxdb_bucket="test-bucket",
        )

        storage = get_storage_backend(settings)
        assert isinstance(storage, InfluxDBStorage)
