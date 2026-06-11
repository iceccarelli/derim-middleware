"""Tests for the protocol-to-adapter registry."""

from derim.adapters.modbus import ModbusAdapter
from derim.adapters.mqtt import MQTTAdapter
from derim.adapters.ocpp import OCPPAdapter
from derim.adapters.registry import (
    ADAPTER_REGISTRY,
    SUPPORTED_PROTOCOLS,
    get_adapter_class,
)
from derim.adapters.sunspec import SunSpecAdapter


def test_builtin_protocols_resolve():
    assert get_adapter_class("modbus") is ModbusAdapter
    assert get_adapter_class("mqtt") is MQTTAdapter
    assert get_adapter_class("sunspec") is SunSpecAdapter
    assert get_adapter_class("ocpp") is OCPPAdapter


def test_protocol_lookup_is_case_insensitive():
    assert get_adapter_class("Modbus") is ModbusAdapter
    assert get_adapter_class("  OCPP ") is OCPPAdapter


def test_unknown_and_missing_protocol_return_none():
    assert get_adapter_class("carrier-pigeon") is None
    assert get_adapter_class(None) is None
    assert get_adapter_class("") is None


def test_all_supported_protocols_are_resolvable():
    for proto in SUPPORTED_PROTOCOLS:
        assert get_adapter_class(proto) is not None


def test_runtime_override_takes_precedence():
    class _Custom(ModbusAdapter):
        pass

    ADAPTER_REGISTRY["modbus"] = _Custom
    try:
        assert get_adapter_class("modbus") is _Custom
    finally:
        ADAPTER_REGISTRY.pop("modbus", None)
    assert get_adapter_class("modbus") is ModbusAdapter
