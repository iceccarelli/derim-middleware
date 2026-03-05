"""
Unit tests for the DERIM REST API endpoints.

Tests cover:
- Health check endpoint.
- Device registration and listing.
- Telemetry ingestion and retrieval.
- Control command dispatch.
- Forecast endpoint (baseline fallback).
- Error handling (404, validation errors).
"""

from fastapi.testclient import TestClient


class TestHealthEndpoint:
    """Tests for the health check endpoint."""

    def test_health_check(self, api_client: TestClient):
        """Health endpoint should return 200 with status info."""
        resp = api_client.get("/health")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "healthy"
        assert "version" in data


class TestDeviceEndpoints:
    """Tests for device registration and retrieval."""

    def test_register_device(self, api_client: TestClient):
        """POST /devices should register a new device."""
        device = {
            "device_id": "api-solar-001",
            "device_type": "solar_pv",
            "name": "API Test Solar",
            "location": "Test Lab",
            "protocol": "modbus",
            "rated_power_kw": 5.0,
            "state": "on",
        }
        resp = api_client.post("/api/v1/devices", json=device)
        assert resp.status_code == 201
        data = resp.json()
        assert data["device_id"] == "api-solar-001"

    def test_list_devices(self, api_client: TestClient):
        """GET /devices should return registered devices."""
        # Register a device first.
        device = {
            "device_id": "api-solar-002",
            "device_type": "solar_pv",
            "name": "API Test Solar 2",
            "state": "on",
        }
        api_client.post("/api/v1/devices", json=device)

        resp = api_client.get("/api/v1/devices")
        assert resp.status_code == 200
        devices = resp.json()
        assert isinstance(devices, list)

    def test_get_device_by_id(self, api_client: TestClient):
        """GET /devices/{device_id} should return the device."""
        device = {
            "device_id": "api-solar-003",
            "device_type": "solar_pv",
            "name": "API Test Solar 3",
            "state": "on",
        }
        api_client.post("/api/v1/devices", json=device)

        resp = api_client.get("/api/v1/devices/api-solar-003")
        assert resp.status_code == 200
        data = resp.json()
        assert data["device_id"] == "api-solar-003"

    def test_get_nonexistent_device(self, api_client: TestClient):
        """GET /devices/{device_id} should return 404 for unknown device."""
        resp = api_client.get("/api/v1/devices/nonexistent")
        assert resp.status_code == 404


class TestTelemetryEndpoints:
    """Tests for telemetry ingestion and retrieval."""

    def test_ingest_telemetry(self, api_client: TestClient):
        """POST /telemetry/{device_id} should accept telemetry records."""
        records = [
            {
                "device_id": "telem-001",
                "device_type": "solar_pv",
                "power_kw": 3.5,
                "energy_kwh": 100.0,
                "voltage_v": 230.0,
                "current_a": 15.2,
                "state": "on",
            }
        ]
        resp = api_client.post("/api/v1/telemetry/telem-001", json=records)
        assert resp.status_code == 201
        data = resp.json()
        assert data["records_written"] == 1

    def test_query_telemetry(self, api_client: TestClient):
        """GET /telemetry/{device_id} should return stored records."""
        # Ingest first.
        records = [
            {
                "device_id": "telem-002",
                "power_kw": 4.0,
                "state": "on",
            }
        ]
        api_client.post("/api/v1/telemetry/telem-002", json=records)

        resp = api_client.get("/api/v1/telemetry/telem-002")
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, list)

    def test_query_with_time_range(self, api_client: TestClient):
        """GET /telemetry with start/end should filter results."""
        resp = api_client.get(
            "/api/v1/telemetry/telem-002",
            params={
                "start": "2025-01-01T00:00:00",
                "end": "2025-12-31T23:59:59",
                "limit": 10,
            },
        )
        assert resp.status_code == 200


class TestControlEndpoints:
    """Tests for device control commands."""

    def test_send_valid_command(self, api_client: TestClient):
        """POST /control/{device_id} should accept valid commands."""
        # Register device first.
        device = {
            "device_id": "ctrl-001",
            "device_type": "solar_pv",
            "name": "Control Test",
            "state": "on",
        }
        api_client.post("/api/v1/devices", json=device)

        cmd = {"command": "setpoint", "value": 3.5}
        resp = api_client.post("/api/v1/control/ctrl-001", json=cmd)
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "accepted"

    def test_send_unknown_command(self, api_client: TestClient):
        """Unknown commands should be rejected."""
        device = {
            "device_id": "ctrl-002",
            "device_type": "battery",
            "name": "Control Test 2",
            "state": "on",
        }
        api_client.post("/api/v1/devices", json=device)

        cmd = {"command": "explode"}
        resp = api_client.post("/api/v1/control/ctrl-002", json=cmd)
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "rejected"

    def test_control_nonexistent_device(self, api_client: TestClient):
        """Control command to unknown device should return 404."""
        cmd = {"command": "on"}
        resp = api_client.post("/api/v1/control/nonexistent", json=cmd)
        assert resp.status_code == 404


class TestForecastEndpoints:
    """Tests for the digital twin forecast endpoints."""

    def test_forecast_baseline(self, api_client: TestClient):
        """Forecast should fall back to baseline when no model exists."""
        # Register device.
        device = {
            "device_id": "forecast-001",
            "device_type": "solar_pv",
            "name": "Forecast Test",
            "state": "on",
        }
        api_client.post("/api/v1/devices", json=device)

        resp = api_client.get(
            "/api/v1/forecast/forecast-001",
            params={"horizon_hours": 6},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["device_id"] == "forecast-001"
        assert "predictions" in data
        assert len(data["predictions"]) > 0

    def test_forecast_nonexistent_device(self, api_client: TestClient):
        """Forecast for unknown device should return 404."""
        resp = api_client.get("/api/v1/forecast/nonexistent")
        assert resp.status_code == 404

    def test_list_models(self, api_client: TestClient):
        """GET /forecast/models should return a list."""
        resp = api_client.get("/api/v1/forecast/models")
        assert resp.status_code == 200
        data = resp.json()
        assert "models" in data
        assert isinstance(data["models"], list)
