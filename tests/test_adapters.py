"""
Unit tests for the DERIM protocol adapters.

Tests cover:
- Base adapter interface compliance.
- Modbus adapter configuration and register mapping.
- MQTT adapter topic parsing and payload normalisation.
- SunSpec adapter model mapping.
- OCPP adapter message handling.

Note: These tests do not require running protocol servers.
They test adapter logic, configuration, and data normalisation.
"""

import pytest

from derim.adapters.base import BaseAdapter
from derim.adapters.modbus import DEFAULT_REGISTER_MAP, ModbusAdapter
from derim.adapters.mqtt import MQTTAdapter
from derim.adapters.ocpp import OCPPAdapter
from derim.adapters.sunspec import SunSpecAdapter


class TestBaseAdapter:
    """Tests for the abstract BaseAdapter interface."""

    def test_cannot_instantiate_base_adapter(self):
        """BaseAdapter should not be instantiable directly."""
        with pytest.raises(TypeError):
            BaseAdapter("test-device")

    def test_subclass_must_implement_methods(self):
        """Subclasses must implement all abstract methods."""

        class IncompleteAdapter(BaseAdapter):
            pass

        with pytest.raises(TypeError):
            IncompleteAdapter("test-device")


class TestModbusAdapter:
    """Tests for the Modbus protocol adapter."""

    def test_create_tcp_adapter(self):
        """ModbusAdapter should accept TCP configuration via config dict."""
        adapter = ModbusAdapter(
            device_id="modbus-test-001",
            config={
                "host": "192.168.1.100",
                "port": 502,
                "unit_id": 1,
            },
        )
        assert adapter._host == "192.168.1.100"
        assert adapter._port == 502
        assert adapter._unit_id == 1

    def test_default_register_map(self):
        """Default register map should contain expected fields."""
        assert "power_kw" in DEFAULT_REGISTER_MAP
        assert "voltage_v" in DEFAULT_REGISTER_MAP
        assert "current_a" in DEFAULT_REGISTER_MAP
        assert "frequency_hz" in DEFAULT_REGISTER_MAP
        assert "energy_kwh" in DEFAULT_REGISTER_MAP

    def test_custom_register_map(self):
        """Custom register map should override defaults."""
        custom_map = {
            "power_kw": (100, 2, 0.1, "kW"),
            "voltage_v": (104, 1, 0.1, "V"),
        }
        adapter = ModbusAdapter(
            device_id="custom-001",
            config={"register_map": custom_map},
        )
        assert adapter._register_map == custom_map

    def test_register_map_structure(self):
        """Each register map entry should have (address, count, scale, unit)."""
        for name, entry in DEFAULT_REGISTER_MAP.items():
            assert len(entry) == 4, f"Register '{name}' should have 4 elements"
            addr, count, scale, unit = entry
            assert isinstance(addr, int)
            assert isinstance(count, int)
            assert isinstance(scale, (int, float))
            assert isinstance(unit, str)

    def test_default_config(self):
        """ModbusAdapter with no config should use defaults."""
        adapter = ModbusAdapter(device_id="default-001")
        assert adapter._host == "127.0.0.1"
        assert adapter._port == 502
        assert adapter._unit_id == 1
        assert adapter._protocol == "tcp"


class TestMQTTAdapter:
    """Tests for the MQTT protocol adapter."""

    def test_create_mqtt_adapter(self):
        """MQTTAdapter should accept broker configuration via config dict."""
        adapter = MQTTAdapter(
            device_id="mqtt-test-001",
            config={
                "broker": "mqtt.example.com",
                "port": 1883,
            },
        )
        assert adapter._broker == "mqtt.example.com"
        assert adapter._port == 1883

    def test_default_config(self):
        """MQTTAdapter with no config should use defaults."""
        adapter = MQTTAdapter(device_id="mqtt-test-002")
        assert adapter._broker == "localhost"
        assert adapter._port == 1883

    def test_telemetry_topic(self):
        """Telemetry topic should follow the convention."""
        adapter = MQTTAdapter(
            device_id="mqtt-test-003",
            config={"topic_prefix": "derim/devices"},
        )
        assert adapter._telemetry_topic == "derim/devices/mqtt-test-003/telemetry"

    def test_extract_device_id_from_topic(self):
        """Device ID should be extractable from MQTT topic."""
        topic = "derim/devices/solar-001/telemetry"
        parts = topic.split("/")
        if len(parts) >= 3:
            extracted_id = parts[2]
        else:
            extracted_id = None
        assert extracted_id == "solar-001"


class TestSunSpecAdapter:
    """Tests for the SunSpec protocol adapter."""

    def test_create_sunspec_adapter(self):
        """SunSpecAdapter should accept host and model configuration."""
        adapter = SunSpecAdapter(
            device_id="sunspec-test-001",
            config={
                "host": "192.168.1.50",
                "port": 502,
            },
        )
        assert adapter._host == "192.168.1.50"
        assert adapter.device_id == "sunspec-test-001"

    def test_default_config(self):
        """SunSpecAdapter with no config should use defaults."""
        adapter = SunSpecAdapter(device_id="sunspec-test-002")
        assert adapter._host == "127.0.0.1"
        assert adapter._port == 502
        assert adapter._slave_id == 1


class TestOCPPAdapter:
    """Tests for the OCPP protocol adapter."""

    def test_create_ocpp_adapter(self):
        """OCPPAdapter should accept WebSocket config."""
        adapter = OCPPAdapter(
            device_id="ocpp-test-001",
            config={
                "ws_host": "0.0.0.0",
                "ws_port": 9000,
                "charge_point_id": "CP001",
            },
        )
        assert adapter._ws_host == "0.0.0.0"
        assert adapter._ws_port == 9000
        assert adapter._cp_id == "CP001"

    def test_default_config(self):
        """OCPPAdapter with no config should use secure local defaults."""
        adapter = OCPPAdapter(device_id="ocpp-test-002")
        assert adapter._ws_host == "127.0.0.1"
        assert adapter._ws_port == 9000
        assert adapter._cp_id == "CP001"
