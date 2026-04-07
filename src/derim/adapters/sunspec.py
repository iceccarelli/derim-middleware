"""
SunSpec protocol adapter for solar inverters and DER devices.

SunSpec is an industry-standard communication specification that defines
Modbus register maps (called *models*) for solar inverters, meters, and
other DER equipment.  This adapter reads SunSpec-compliant Modbus
registers and maps them to the common ``DERTelemetry`` / ``SolarTelemetry``
model.

Key SunSpec Models Used
-----------------------
- **Model 1** (Common): Manufacturer, model, serial number.
- **Model 101/103** (Inverter - Single/Three Phase): AC power, energy,
  voltage, current, frequency, operating state.
- **Model 120** (Nameplate Ratings): Rated power, voltage, current.
- **Model 122** (Measurements - Status): Detailed inverter status.

The adapter falls back to direct ``pymodbus`` register reads with a
SunSpec-aware register map when the ``pysunspec2`` library is not
available.

Usage
-----
::

    from derim.adapters.sunspec import SunSpecAdapter

    config = {
        "host": "192.168.1.50",
        "port": 502,
        "slave_id": 1,
    }
    async with SunSpecAdapter("solar-inv-002", config) as adapter:
        telemetry = await adapter.read_data()
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Optional, cast

from derim.adapters.base import BaseAdapter
from derim.models.common import (
    CommandRequest,
    CommandResponse,
    DERType,
    DeviceState,
    SolarTelemetry,
)
from derim.utils.logger import get_logger

logger = get_logger(__name__)

# SunSpec Model 103 (Three-Phase Inverter) register offsets relative to
# the model base address.  Addresses assume the model starts at 40069.
SUNSPEC_MODEL_103_MAP: dict[str, tuple[int, int, float]] = {
    "ac_current_a": (0, 1, 0.01),  # A (total)
    "phase_a_current": (1, 1, 0.01),  # A phase A
    "phase_b_current": (2, 1, 0.01),  # A phase B
    "phase_c_current": (3, 1, 0.01),  # A phase C
    "ac_voltage_ab": (5, 1, 0.01),  # V line-line AB
    "ac_voltage_bc": (6, 1, 0.01),  # V line-line BC
    "ac_voltage_ca": (7, 1, 0.01),  # V line-line CA
    "ac_voltage_an": (8, 1, 0.01),  # V line-neutral A
    "ac_power_w": (12, 1, 1.0),  # W
    "frequency_hz": (13, 1, 0.01),  # Hz
    "apparent_power_va": (14, 1, 1.0),  # VA
    "reactive_power_var": (15, 1, 1.0),  # var
    "power_factor": (16, 1, 0.01),  # cos(phi) * 100
    "energy_wh": (17, 2, 1.0),  # Wh (32-bit)
    "dc_current_a": (19, 1, 0.01),  # A DC
    "dc_voltage_v": (20, 1, 0.1),  # V DC
    "dc_power_w": (21, 1, 1.0),  # W DC
    "operating_state": (23, 1, 1.0),  # Enumerated
}

# SunSpec operating state codes (Model 103, point St).
SUNSPEC_STATE_MAP: dict[int, DeviceState] = {
    1: DeviceState.OFF,  # Off
    2: DeviceState.STANDBY,  # Sleeping
    3: DeviceState.STANDBY,  # Starting
    4: DeviceState.ON,  # MPPT (normal operation)
    5: DeviceState.ON,  # Throttled
    6: DeviceState.OFF,  # Shutting down
    7: DeviceState.FAULT,  # Fault
    8: DeviceState.STANDBY,  # Standby
}


class SunSpecAdapter(BaseAdapter):
    """
    Adapter for SunSpec-compliant solar inverters over Modbus TCP.

    Parameters
    ----------
    device_id : str
        Unique identifier for the target inverter.
    config : dict[str, Any]
        Configuration with keys:

        - ``host`` (str): Inverter IP address.
        - ``port`` (int): Modbus TCP port (default 502).
        - ``slave_id`` (int): Modbus slave ID (default 1).
        - ``model_base_address`` (int): Starting register of SunSpec
          Model 103 block (default 40069).
        - ``timeout`` (float): Connection timeout in seconds.
    """

    def __init__(self, device_id: str, config: Optional[dict[str, Any]] = None):
        super().__init__(device_id, config)
        self._host: str = self.config.get("host", "127.0.0.1")
        self._port: int = self.config.get("port", 502)
        self._slave_id: int = self.config.get("slave_id", 1)
        self._model_base: int = self.config.get("model_base_address", 40069)
        self._timeout: float = self.config.get("timeout", 5.0)
        self._client: Any = None

    async def connect(self) -> None:
        """
        Connect to the SunSpec inverter via Modbus TCP.

        Raises
        ------
        ConnectionError
            If the inverter is unreachable.
        """
        try:
            from pymodbus.client import AsyncModbusTcpClient

            self._client = AsyncModbusTcpClient(
                host=self._host,
                port=self._port,
                timeout=self._timeout,
            )
            connected = await self._client.connect()
            if not connected:
                raise ConnectionError(
                    f"Cannot reach SunSpec device at {self._host}:{self._port}"
                )

            self._connected = True
            logger.info(
                "sunspec_connected",
                device_id=self.device_id,
                host=self._host,
                port=self._port,
            )

        except ImportError as exc:
            raise ImportError(
                "pymodbus is required for the SunSpec adapter. "
                "Install it with: pip install pymodbus"
            ) from exc
        except Exception as exc:
            logger.error(
                "sunspec_connection_failed",
                device_id=self.device_id,
                error=str(exc),
            )
            raise ConnectionError(
                f"SunSpec connection failed for {self.device_id}: {exc}"
            ) from exc

    async def disconnect(self) -> None:
        """Close the Modbus TCP connection."""
        if self._client is not None:
            self._client.close()
            self._connected = False
            logger.info("sunspec_disconnected", device_id=self.device_id)

    async def _read_register(self, offset: int, count: int) -> list[int]:
        """Read *count* holding registers at *model_base + offset*."""
        address = self._model_base + offset
        result = await self._client.read_holding_registers(
            address=address, count=count, slave=self._slave_id
        )
        if result.isError():
            logger.warning(
                "sunspec_register_error",
                device_id=self.device_id,
                address=address,
                error=str(result),
            )
            return [0] * count
        return cast(list[int], result.registers)

    async def read_data(self) -> SolarTelemetry:
        """
        Read SunSpec Model 103 registers and return ``SolarTelemetry``.

        Returns
        -------
        SolarTelemetry
            Normalised solar inverter telemetry.
        """
        self._ensure_connected()

        values: dict[str, float] = {}
        for name, (offset, count, scale) in SUNSPEC_MODEL_103_MAP.items():
            try:
                regs = await self._read_register(offset, count)
                if count == 1:
                    raw = regs[0]
                else:
                    raw = (regs[0] << 16) | regs[1]
                values[name] = raw * scale
            except Exception as exc:
                logger.warning(
                    "sunspec_read_failed",
                    device_id=self.device_id,
                    point=name,
                    error=str(exc),
                )
                values[name] = 0.0

        # Map operating state.
        op_state_code = int(values.get("operating_state", 0))
        device_state = SUNSPEC_STATE_MAP.get(op_state_code, DeviceState.UNKNOWN)

        telemetry = SolarTelemetry(
            timestamp=datetime.now(timezone.utc),
            device_id=self.device_id,
            device_type=DERType.SOLAR_PV,
            power_kw=values.get("ac_power_w", 0.0) / 1000.0,
            energy_kwh=values.get("energy_wh", 0.0) / 1000.0,
            voltage_v=values.get("ac_voltage_an", 0.0),
            current_a=values.get("ac_current_a", 0.0),
            frequency_hz=values.get("frequency_hz", 50.0),
            state=device_state,
            power_factor=min(abs(values.get("power_factor", 0.0)), 1.0) or None,
            reactive_power_kvar=values.get("reactive_power_var", 0.0) / 1000.0,
            dc_voltage_v=values.get("dc_voltage_v"),
            dc_current_a=values.get("dc_current_a"),
            metadata={
                "protocol": "sunspec",
                "model": 103,
                "slave_id": self._slave_id,
            },
        )

        logger.debug(
            "sunspec_data_read",
            device_id=self.device_id,
            power_kw=telemetry.power_kw,
            state=telemetry.state.value,
        )
        return telemetry

    async def write_command(self, command: CommandRequest) -> CommandResponse:
        """
        Send a control command to the SunSpec inverter.

        SunSpec Model 123 (Immediate Controls) defines writable points
        for power curtailment and reactive power control.  This
        implementation supports ``"setpoint"`` (active power limit) and
        ``"on"`` / ``"off"`` commands.

        Parameters
        ----------
        command : CommandRequest
            The command to dispatch.

        Returns
        -------
        CommandResponse
            Result of the operation.
        """
        self._ensure_connected()

        try:
            if command.command == "setpoint" and command.value is not None:
                # Write to Model 123, WMaxLim_Ena (enable) + WMaxLimPct.
                enable_addr = self.config.get("curtail_enable_register", 40236)
                pct_addr = self.config.get("curtail_pct_register", 40237)

                # Enable power limit.
                await self._client.write_register(
                    address=enable_addr, value=1, slave=self._slave_id
                )
                # Set percentage (0-100 scaled by 100).
                pct_value = int(command.value * 100)
                await self._client.write_register(
                    address=pct_addr, value=pct_value, slave=self._slave_id
                )

                logger.info(
                    "sunspec_setpoint_written",
                    device_id=self.device_id,
                    value=command.value,
                )
                return CommandResponse(
                    device_id=self.device_id,
                    command=command.command,
                    status="accepted",
                    message=f"Power limit set to {command.value}%",
                )

            elif command.command in ("on", "off"):
                # Write to Conn (connect/disconnect) register.
                conn_addr = self.config.get("connect_register", 40238)
                value = 1 if command.command == "on" else 0
                await self._client.write_register(
                    address=conn_addr, value=value, slave=self._slave_id
                )
                return CommandResponse(
                    device_id=self.device_id,
                    command=command.command,
                    status="accepted",
                    message=f"Inverter {'connected' if value else 'disconnected'}",
                )

            else:
                return CommandResponse(
                    device_id=self.device_id,
                    command=command.command,
                    status="rejected",
                    message=f"Unsupported SunSpec command: {command.command}",
                )

        except Exception as exc:
            logger.error(
                "sunspec_command_failed",
                device_id=self.device_id,
                error=str(exc),
            )
            return CommandResponse(
                device_id=self.device_id,
                command=command.command,
                status="error",
                message=str(exc),
            )
