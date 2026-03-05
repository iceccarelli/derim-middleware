# Protocol Adapter Guide

This guide explains how to use the built-in protocol adapters and how to create custom adapters for new DER communication protocols.

## Overview

DERIM's adapter layer provides a uniform interface for communicating with distributed energy resources regardless of their native protocol. Every adapter inherits from `BaseAdapter` and implements four core methods that handle the full lifecycle of device interaction.

| Method | Signature | Purpose |
|--------|-----------|---------|
| `connect()` | `async def connect() -> None` | Establish a connection to the device or message broker |
| `disconnect()` | `async def disconnect() -> None` | Gracefully close the connection and release resources |
| `read_data()` | `async def read_data() -> DERTelemetry` | Read current telemetry and return a normalised model |
| `write_command()` | `async def write_command(command, value, **kwargs) -> bool` | Send a control command to the device |

## Modbus Adapter

The `ModbusAdapter` supports both Modbus TCP and Modbus RTU communication, making it suitable for a wide range of industrial DER devices including solar inverters, power meters, and battery management systems.

### Configuration

```python
from derim.adapters.modbus import ModbusAdapter

adapter = ModbusAdapter(
    device_id="solar-inv-001",
    config={
        "host": "192.168.1.100",
        "port": 502,
        "unit_id": 1,
        "mode": "tcp",           # "tcp" or "rtu"
        "timeout": 5.0,
        "register_map": {
            "power_kw": {"address": 40001, "count": 2, "type": "float32", "scale": 0.1},
            "voltage_v": {"address": 40003, "count": 2, "type": "float32", "scale": 0.1},
            "current_a": {"address": 40005, "count": 2, "type": "float32", "scale": 0.01},
        },
    },
)
```

### Usage

```python
await adapter.connect()
telemetry = await adapter.read_data()
print(f"Power: {telemetry.power_kw} kW")
await adapter.disconnect()
```

## MQTT Adapter

The `MQTTAdapter` subscribes to MQTT topics published by DER devices or IoT gateways. It supports MQTT 3.1.1 with optional TLS and authentication.

### Configuration

```python
from derim.adapters.mqtt import MQTTAdapter

adapter = MQTTAdapter(
    device_id="gateway-001",
    config={
        "broker_host": "mqtt.example.com",
        "broker_port": 1883,
        "topics": ["der/solar/+/telemetry", "der/battery/+/telemetry"],
        "qos": 1,
        "username": "derim",
        "password": "secret",
        "client_id": "derim-middleware",
    },
)
```

### Message Format

The adapter expects JSON messages on subscribed topics with fields that map to the `DERTelemetry` model. Unrecognised fields are stored in the `metadata` dictionary.

```json
{
  "timestamp": "2026-03-04T12:00:00Z",
  "power_kw": 3.45,
  "voltage_v": 230.1,
  "current_a": 15.0,
  "state": "on"
}
```

## SunSpec Adapter

The `SunSpecAdapter` reads data from solar inverters that implement the SunSpec Modbus register map standard. It automatically discovers the SunSpec model block and reads standardised registers for power, energy, voltage, and current.

### Configuration

```python
from derim.adapters.sunspec import SunSpecAdapter

adapter = SunSpecAdapter(
    device_id="sunspec-inv-001",
    config={
        "host": "192.168.1.50",
        "port": 502,
        "unit_id": 1,
        "base_address": 40000,
    },
)
```

## OCPP Adapter

The `OCPPAdapter` implements the Open Charge Point Protocol (OCPP) 1.6-J for communicating with EV charging stations over WebSocket. It can receive meter values, status notifications, and send remote start/stop commands.

### Configuration

```python
from derim.adapters.ocpp import OCPPAdapter

adapter = OCPPAdapter(
    device_id="evse-001",
    config={
        "ws_url": "ws://charger.example.com:9000/ocpp/evse-001",
        "charge_point_id": "EVSE-001",
        "protocol_version": "1.6",
    },
)
```

## Creating a Custom Adapter

To add support for a new protocol, create a new module in `src/derim/adapters/` that inherits from `BaseAdapter`.

```python
"""Example: DNP3 protocol adapter."""

from derim.adapters.base import BaseAdapter
from derim.models.common import DERTelemetry


class DNP3Adapter(BaseAdapter):
    """Adapter for DNP3 (IEEE 1815) protocol."""

    def __init__(self, device_id: str, config: dict | None = None):
        super().__init__(device_id=device_id, protocol="dnp3", config=config)
        # Initialise DNP3-specific attributes.

    async def connect(self) -> None:
        """Establish DNP3 connection."""
        # Implementation here.
        self._connected = True

    async def disconnect(self) -> None:
        """Close DNP3 connection."""
        self._connected = False

    async def read_data(self) -> DERTelemetry:
        """Read DNP3 data points and normalise."""
        # Read from device, then normalise.
        return DERTelemetry(
            device_id=self.device_id,
            power_kw=...,
            voltage_v=...,
        )

    async def write_command(self, command: str, value: float = 0.0, **kwargs) -> bool:
        """Send DNP3 control command."""
        # Implementation here.
        return True
```

After creating the adapter, add tests in `tests/test_adapters.py` and update this documentation.
