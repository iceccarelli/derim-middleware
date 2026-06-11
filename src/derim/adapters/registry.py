"""
Protocol-to-adapter registry.

Maps a device's ``protocol`` string (e.g. ``"modbus"``) to the concrete
:class:`~derim.adapters.base.BaseAdapter` subclass that can talk to it.

Adapter classes are imported lazily so that importing this module never
pulls in heavy protocol libraries (``pymodbus``, ``paho-mqtt``, ``ocpp``)
unless an adapter is actually requested. Plugins and tests can register or
override adapters at runtime via :data:`ADAPTER_REGISTRY`.
"""

from __future__ import annotations

from typing import Optional, Type

from derim.adapters.base import BaseAdapter

SUPPORTED_PROTOCOLS: tuple[str, ...] = ("modbus", "mqtt", "sunspec", "ocpp")

ADAPTER_REGISTRY: dict[str, Type[BaseAdapter]] = {}


def _load_builtin(protocol: str) -> Optional[Type[BaseAdapter]]:
    """Lazily import and return the built-in adapter for ``protocol``."""
    if protocol == "modbus":
        from derim.adapters.modbus import ModbusAdapter

        return ModbusAdapter
    if protocol == "mqtt":
        from derim.adapters.mqtt import MQTTAdapter

        return MQTTAdapter
    if protocol == "sunspec":
        from derim.adapters.sunspec import SunSpecAdapter

        return SunSpecAdapter
    if protocol == "ocpp":
        from derim.adapters.ocpp import OCPPAdapter

        return OCPPAdapter
    return None


def get_adapter_class(protocol: Optional[str]) -> Optional[Type[BaseAdapter]]:
    """
    Resolve the adapter class for a given protocol string.

    Resolution order: runtime ``ADAPTER_REGISTRY`` overrides first, then the
    built-in adapters. Returns ``None`` if the protocol is unknown or missing.
    """
    if not protocol:
        return None
    key = protocol.strip().lower()
    if key in ADAPTER_REGISTRY:
        return ADAPTER_REGISTRY[key]
    return _load_builtin(key)
