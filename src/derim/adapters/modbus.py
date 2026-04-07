"""
Modbus TCP / RTU protocol adapter for DER devices.

This adapter uses the ``pymodbus`` library to communicate with devices
that expose telemetry through Modbus holding registers and input
registers.  It supports both **TCP** (Ethernet) and **RTU** (serial)
transport layers.

Typical devices addressed by this adapter include solar inverters,
battery management systems, and power meters that implement a
vendor-specific Modbus register map.

Register Map Convention
-----------------------
The default register map (``DEFAULT_REGISTER_MAP``) assumes a common
layout used by many solar inverters.  Integrators should override this
map via the ``config["register_map"]`` dictionary to match their
specific hardware.

Usage
-----
::

    from derim.adapters.modbus import ModbusAdapter

    config = {
        "host": "192.168.1.100",
        "port": 502,
        "unit_id": 1,
        "protocol": "tcp",
    }
    async with ModbusAdapter("solar-inv-001", config) as adapter:
        telemetry = await adapter.read_data()
        print(telemetry.power_kw)
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Optional

from derim.adapters.base import BaseAdapter
from derim.models.common import (
    CommandRequest,
    CommandResponse,
    DERTelemetry,
    DERType,
    DeviceState,
)
from derim.utils.logger import get_logger

logger = get_logger(__name__)

# Default register map: register_name -> (address, count, scale_factor, unit)
# Scale factor converts raw integer to engineering unit.
DEFAULT_REGISTER_MAP: dict[str, tuple[int, int, float, str]] = {
    "power_kw": (40083, 1, 0.1, "kW"),
    "energy_kwh": (40093, 2, 0.1, "kWh"),
    "voltage_v": (40079, 1, 0.1, "V"),
    "current_a": (40071, 1, 0.01, "A"),
    "frequency_hz": (40085, 1, 0.01, "Hz"),
    "power_factor": (40091, 1, 0.001, ""),
    "status_code": (40107, 1, 1.0, ""),
}

# Status code to DeviceState mapping.
STATUS_MAP: dict[int, DeviceState] = {
    0: DeviceState.OFF,
    1: DeviceState.ON,
    2: DeviceState.STANDBY,
    3: DeviceState.FAULT,
}


class ModbusAdapter(BaseAdapter):
    """
    Concrete adapter for Modbus TCP and RTU communication.

    Parameters
    ----------
    device_id : str
        Unique identifier for the target device.
    config : dict[str, Any]
        Configuration dictionary with keys:

        - ``host`` (str): IP address or hostname (TCP) or serial port (RTU).
        - ``port`` (int): TCP port (default 502) or baud rate for RTU.
        - ``unit_id`` (int): Modbus slave / unit ID.
        - ``protocol`` (str): ``"tcp"`` or ``"rtu"``.
        - ``register_map`` (dict, optional): Custom register map override.
        - ``timeout`` (float, optional): Connection timeout in seconds.
    """

    def __init__(self, device_id: str, config: Optional[dict[str, Any]] = None):
        super().__init__(device_id, config)
        self._client: Any = None
        self._host: str = self.config.get("host", "127.0.0.1")
        self._port: int = self.config.get("port", 502)
        self._unit_id: int = self.config.get("unit_id", 1)
        self._protocol: str = self.config.get("protocol", "tcp").lower()
        self._timeout: float = self.config.get("timeout", 5.0)
        self._register_map: dict[str, tuple[int, int, float, str]] = self.config.get(
            "register_map", DEFAULT_REGISTER_MAP
        )

    async def connect(self) -> None:
        """
        Establish a Modbus connection using ``pymodbus``.

        For TCP, an ``AsyncModbusTcpClient`` is created.  For RTU, an
        ``AsyncModbusSerialClient`` is used.

        Raises
        ------
        ConnectionError
            If the connection cannot be established within the timeout.
        """
        try:
            if self._protocol == "tcp":
                from pymodbus.client import AsyncModbusTcpClient

                self._client = AsyncModbusTcpClient(
                    host=self._host,
                    port=self._port,
                    timeout=self._timeout,
                )
            elif self._protocol == "rtu":
                from pymodbus.client import AsyncModbusSerialClient

                self._client = AsyncModbusSerialClient(
                    port=self._host,  # serial port path
                    baudrate=self._port,
                    timeout=self._timeout,
                )
            else:
                raise ValueError(
                    f"Unsupported Modbus protocol: {self._protocol}. "
                    "Use 'tcp' or 'rtu'."
                )

            connected = await self._client.connect()
            if not connected:
                raise ConnectionError(
                    f"Failed to connect to Modbus device at {self._host}:{self._port}"
                )

            self._connected = True
            logger.info(
                "modbus_connected",
                device_id=self.device_id,
                host=self._host,
                port=self._port,
                protocol=self._protocol,
            )

        except ImportError as exc:
            raise ImportError(
                "pymodbus is required for the Modbus adapter. "
                "Install it with: pip install pymodbus"
            ) from exc
        except Exception as exc:
            logger.error(
                "modbus_connection_failed",
                device_id=self.device_id,
                error=str(exc),
            )
            raise ConnectionError(
                f"Modbus connection failed for {self.device_id}: {exc}"
            ) from exc

    async def disconnect(self) -> None:
        """Close the Modbus connection gracefully."""
        if self._client is not None:
            self._client.close()
            self._connected = False
            logger.info("modbus_disconnected", device_id=self.device_id)

    async def read_data(self) -> DERTelemetry:
        """
        Read all configured registers and return normalised telemetry.

        Each entry in the register map is read individually.  The raw
        integer values are scaled by the configured scale factor and
        assembled into a ``DERTelemetry`` instance.

        Returns
        -------
        DERTelemetry
            Normalised telemetry record.
        """
        self._ensure_connected()

        raw_values: dict[str, float] = {}

        for field_name, (address, count, scale, _unit) in self._register_map.items():
            try:
                result = await self._client.read_holding_registers(
                    address=address,
                    count=count,
                    slave=self._unit_id,
                )
                if result.isError():
                    logger.warning(
                        "modbus_read_error",
                        device_id=self.device_id,
                        register=field_name,
                        address=address,
                        error=str(result),
                    )
                    raw_values[field_name] = 0.0
                    continue

                # Combine multiple registers (big-endian) for 32-bit values.
                if count == 1:
                    raw = result.registers[0]
                else:
                    raw = sum(
                        v << (16 * (count - 1 - i))
                        for i, v in enumerate(result.registers)
                    )

                raw_values[field_name] = raw * scale

            except Exception as exc:
                logger.warning(
                    "modbus_register_read_failed",
                    device_id=self.device_id,
                    register=field_name,
                    error=str(exc),
                )
                raw_values[field_name] = 0.0

        # Map status code to DeviceState.
        status_code = int(raw_values.get("status_code", -1))
        device_state = STATUS_MAP.get(status_code, DeviceState.UNKNOWN)

        telemetry = DERTelemetry(
            timestamp=datetime.now(timezone.utc),
            device_id=self.device_id,
            device_type=DERType.SOLAR_PV,
            power_kw=raw_values.get("power_kw", 0.0),
            energy_kwh=raw_values.get("energy_kwh", 0.0),
            voltage_v=raw_values.get("voltage_v", 0.0),
            current_a=raw_values.get("current_a", 0.0),
            frequency_hz=raw_values.get("frequency_hz", 50.0),
            state=device_state,
            power_factor=raw_values.get("power_factor"),
            metadata={"protocol": "modbus", "unit_id": self._unit_id},
        )

        logger.debug(
            "modbus_data_read",
            device_id=self.device_id,
            power_kw=telemetry.power_kw,
        )
        return telemetry

    async def write_command(self, command: CommandRequest) -> CommandResponse:
        """
        Write a control command to the device via Modbus registers.

        Supported commands:

        - ``"setpoint"``: Write a power setpoint to register 40100.
        - ``"on"`` / ``"off"``: Write 1 or 0 to the control register 40110.

        Parameters
        ----------
        command : CommandRequest
            The command to dispatch.

        Returns
        -------
        CommandResponse
            Result of the write operation.
        """
        self._ensure_connected()

        try:
            if command.command == "setpoint" and command.value is not None:
                # Write power setpoint (scaled to integer).
                register_address = self.config.get("setpoint_register", 40100)
                raw_value = int(command.value * 10)  # scale factor 0.1
                result = await self._client.write_register(
                    address=register_address,
                    value=raw_value,
                    slave=self._unit_id,
                )
                if result.isError():
                    return CommandResponse(
                        device_id=self.device_id,
                        command=command.command,
                        status="error",
                        message=f"Modbus write error: {result}",
                    )

            elif command.command in ("on", "off"):
                control_register = self.config.get("control_register", 40110)
                value = 1 if command.command == "on" else 0
                result = await self._client.write_register(
                    address=control_register,
                    value=value,
                    slave=self._unit_id,
                )
                if result.isError():
                    return CommandResponse(
                        device_id=self.device_id,
                        command=command.command,
                        status="error",
                        message=f"Modbus write error: {result}",
                    )
            else:
                return CommandResponse(
                    device_id=self.device_id,
                    command=command.command,
                    status="rejected",
                    message=f"Unsupported command: {command.command}",
                )

            logger.info(
                "modbus_command_sent",
                device_id=self.device_id,
                command=command.command,
                value=command.value,
            )
            return CommandResponse(
                device_id=self.device_id,
                command=command.command,
                status="accepted",
                message="Command executed successfully",
            )

        except Exception as exc:
            logger.error(
                "modbus_command_failed",
                device_id=self.device_id,
                command=command.command,
                error=str(exc),
            )
            return CommandResponse(
                device_id=self.device_id,
                command=command.command,
                status="error",
                message=str(exc),
            )
