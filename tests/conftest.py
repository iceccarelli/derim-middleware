"""
Shared pytest fixtures for the DERIM middleware test suite.

This module provides reusable fixtures for database connections,
API test clients, sample data, and mock adapters.
"""

from __future__ import annotations

import asyncio
from datetime import datetime, timedelta, timezone
from typing import Generator

import pytest
import pytest_asyncio
from fastapi.testclient import TestClient

from derim.config import Settings
from derim.models.common import (
    CommandRequest,
    DERDevice,
    DERTelemetry,
    DERType,
    DeviceState,
)


@pytest.fixture(scope="session")
def event_loop():
    """Create an event loop for the test session."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def settings(tmp_path) -> Settings:
    """Provide test-specific settings with a temporary database."""
    return Settings(
        storage_backend="sqlite",
        sqlite_db_path=str(tmp_path / "test_derim.db"),
        model_save_dir=str(tmp_path / "models"),
        log_level="DEBUG",
    )


@pytest.fixture
def sample_device() -> DERDevice:
    """Provide a sample DER device for testing."""
    return DERDevice(
        device_id="test-solar-001",
        device_type=DERType.SOLAR_PV,
        name="Test Solar Inverter",
        location="Test Lab",
        protocol="modbus",
        rated_power_kw=5.0,
        state=DeviceState.ON,
    )


@pytest.fixture
def sample_battery_device() -> DERDevice:
    """Provide a sample battery device for testing."""
    return DERDevice(
        device_id="test-bess-001",
        device_type=DERType.BATTERY,
        name="Test Battery",
        location="Test Lab",
        protocol="mqtt",
        rated_power_kw=10.0,
        state=DeviceState.ON,
    )


@pytest.fixture
def sample_telemetry() -> list[DERTelemetry]:
    """Provide a list of sample telemetry records."""
    base_time = datetime(2025, 6, 1, 12, 0, 0, tzinfo=timezone.utc)
    records = []
    for i in range(10):
        records.append(
            DERTelemetry(
                timestamp=base_time + timedelta(minutes=15 * i),
                device_id="test-solar-001",
                device_type=DERType.SOLAR_PV,
                power_kw=3.5 + i * 0.1,
                energy_kwh=100.0 + i * 0.875,
                voltage_v=230.0 + i * 0.1,
                current_a=15.2 + i * 0.05,
                frequency_hz=50.0,
                state=DeviceState.ON,
            )
        )
    return records


@pytest.fixture
def sample_command() -> CommandRequest:
    """Provide a sample control command."""
    return CommandRequest(
        command="setpoint",
        value=3.5,
        parameters={"ramp_rate_kw_s": 0.5},
    )


@pytest_asyncio.fixture
async def sqlite_storage(settings):
    """Provide an initialised SQLite storage backend."""
    from derim.storage.sqlite import SQLiteStorage

    storage = SQLiteStorage(db_path=settings.sqlite_db_path)
    await storage.connect()
    yield storage
    await storage.disconnect()


@pytest.fixture
def api_client(settings, tmp_path) -> Generator[TestClient, None, None]:
    """Provide a FastAPI test client with SQLite storage."""
    from derim.api.dependencies import get_app_settings
    from derim.main import app

    # Override settings for testing.
    app.dependency_overrides[get_app_settings] = lambda: settings

    with TestClient(app) as client:
        yield client

    app.dependency_overrides.clear()
