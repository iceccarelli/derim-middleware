"""
Unit tests for the DERIM data models.

Tests cover:
- DERTelemetry creation and validation.
- Device-specific telemetry extensions (Solar, Battery, EV).
- DERDevice registration model.
- CommandRequest and CommandResponse models.
- ForecastPoint and ForecastResponse models.
- Serialisation and deserialisation (JSON round-trip).
- Validation error handling for invalid inputs.
"""

from datetime import datetime, timezone

import pytest
from pydantic import ValidationError

from derim.models.common import (
    BatteryTelemetry,
    CommandRequest,
    CommandResponse,
    ConnectorStatus,
    DERDevice,
    DERTelemetry,
    DERType,
    DeviceState,
    EVChargerTelemetry,
    ForecastPoint,
    ForecastResponse,
    SolarTelemetry,
)


class TestDERTelemetry:
    """Tests for the base DERTelemetry model."""

    def test_create_valid_telemetry(self):
        """Valid telemetry record should be created successfully."""
        t = DERTelemetry(
            device_id="solar-001",
            device_type=DERType.SOLAR_PV,
            power_kw=4.5,
            energy_kwh=100.0,
            voltage_v=230.0,
            current_a=19.6,
            frequency_hz=50.0,
            state=DeviceState.ON,
        )
        assert t.device_id == "solar-001"
        assert t.power_kw == 4.5
        assert t.state == DeviceState.ON
        assert t.timestamp is not None

    def test_default_values(self):
        """Default values should be applied for optional fields."""
        t = DERTelemetry(device_id="dev-001")
        assert t.power_kw == 0.0
        assert t.energy_kwh == 0.0
        assert t.voltage_v == 0.0
        assert t.current_a == 0.0
        assert t.frequency_hz == 50.0
        assert t.state == DeviceState.UNKNOWN
        assert t.device_type == DERType.GENERIC
        assert t.power_factor is None
        assert t.reactive_power_kvar is None
        assert t.metadata is None

    def test_json_round_trip(self):
        """Telemetry should survive JSON serialisation and deserialisation."""
        original = DERTelemetry(
            device_id="test-001",
            power_kw=3.14,
            voltage_v=231.5,
            state=DeviceState.ON,
        )
        json_str = original.model_dump_json()
        restored = DERTelemetry.model_validate_json(json_str)
        assert restored.device_id == original.device_id
        assert restored.power_kw == original.power_kw
        assert restored.state == original.state

    def test_metadata_dict(self):
        """Metadata should accept arbitrary key-value pairs."""
        t = DERTelemetry(
            device_id="dev-001",
            metadata={"protocol": "modbus", "unit_id": 1},
        )
        assert t.metadata["protocol"] == "modbus"
        assert t.metadata["unit_id"] == 1


class TestSolarTelemetry:
    """Tests for the SolarTelemetry extension."""

    def test_solar_specific_fields(self):
        """Solar telemetry should include irradiance and temperature."""
        s = SolarTelemetry(
            device_id="solar-002",
            power_kw=4.0,
            irradiance_w_m2=850.0,
            panel_temperature_c=42.5,
            dc_voltage_v=380.0,
            dc_current_a=10.5,
        )
        assert s.device_type == DERType.SOLAR_PV
        assert s.irradiance_w_m2 == 850.0
        assert s.panel_temperature_c == 42.5

    def test_solar_defaults(self):
        """Solar-specific fields should default to None."""
        s = SolarTelemetry(device_id="solar-003")
        assert s.irradiance_w_m2 is None
        assert s.panel_temperature_c is None


class TestBatteryTelemetry:
    """Tests for the BatteryTelemetry extension."""

    def test_battery_specific_fields(self):
        """Battery telemetry should include SOC and SOH."""
        b = BatteryTelemetry(
            device_id="bess-001",
            power_kw=-5.0,
            soc_percent=65.0,
            soh_percent=98.5,
            temperature_c=28.0,
            charge_rate_kw=5.0,
            discharge_rate_kw=0.0,
        )
        assert b.device_type == DERType.BATTERY
        assert b.soc_percent == 65.0
        assert b.power_kw == -5.0  # Negative = charging


class TestEVChargerTelemetry:
    """Tests for the EVChargerTelemetry extension."""

    def test_ev_charger_fields(self):
        """EV charger telemetry should include session data."""
        ev = EVChargerTelemetry(
            device_id="evse-001",
            power_kw=7.4,
            connector_status=ConnectorStatus.OCCUPIED,
            session_energy_kwh=12.5,
            vehicle_soc_percent=45.0,
        )
        assert ev.device_type == DERType.EV_CHARGER
        assert ev.connector_status == ConnectorStatus.OCCUPIED
        assert ev.session_energy_kwh == 12.5


class TestDERDevice:
    """Tests for the DERDevice registration model."""

    def test_create_device(self):
        """Device should be created with all required fields."""
        d = DERDevice(
            device_id="solar-inv-001",
            device_type=DERType.SOLAR_PV,
            name="Rooftop Solar",
            location="Building A",
            protocol="modbus",
            rated_power_kw=5.0,
            state=DeviceState.ON,
        )
        assert d.device_id == "solar-inv-001"
        assert d.rated_power_kw == 5.0

    def test_device_requires_name(self):
        """Device should require name field."""
        with pytest.raises(ValidationError):
            DERDevice(device_id="dev-001")


class TestCommandModels:
    """Tests for command request and response models."""

    def test_command_request(self):
        """Command request should validate correctly."""
        cmd = CommandRequest(
            command="setpoint",
            value=3.5,
            parameters={"ramp_rate": 0.5},
        )
        assert cmd.command == "setpoint"
        assert cmd.value == 3.5

    def test_command_response(self):
        """Command response should include status and message."""
        resp = CommandResponse(
            device_id="dev-001",
            command="setpoint",
            status="accepted",
            message="Command dispatched",
        )
        assert resp.status == "accepted"


class TestForecastModels:
    """Tests for forecast-related models."""

    def test_forecast_point(self):
        """Forecast point should include power and optional confidence."""
        fp = ForecastPoint(
            timestamp=datetime.now(timezone.utc),
            power_kw=4.2,
            confidence_lower=3.5,
            confidence_upper=4.9,
        )
        assert fp.power_kw == 4.2
        assert fp.confidence_lower == 3.5

    def test_forecast_response(self):
        """Forecast response should contain predictions list."""
        now = datetime.now(timezone.utc)
        fr = ForecastResponse(
            device_id="solar-001",
            model_name="lstm",
            horizon_hours=24,
            predictions=[
                ForecastPoint(timestamp=now, power_kw=3.0),
                ForecastPoint(timestamp=now, power_kw=3.5),
            ],
        )
        assert len(fr.predictions) == 2
        assert fr.model_name == "lstm"
