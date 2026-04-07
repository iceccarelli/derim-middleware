"""
OCPP 1.6 / 2.0.1 protocol adapter for EV charging stations.

This adapter implements an OCPP Central System (CSMS) that communicates
with EV Supply Equipment (EVSE) charge points over WebSocket.  It uses
the ``ocpp`` library to handle the OCPP-J (JSON over WebSocket) protocol.

The adapter can:

- Receive **MeterValues** and **StatusNotification** messages from
  charge points and normalise them into ``EVChargerTelemetry``.
- Send **RemoteStartTransaction**, **RemoteStopTransaction**, and
  **ChangeConfiguration** commands.

Architecture
------------
The adapter spawns a lightweight WebSocket server that listens for
incoming charge point connections.  Each charge point is identified by
its ``charge_point_id`` in the WebSocket URL path.

Usage
-----
::

    from derim.adapters.ocpp import OCPPAdapter

    config = {
        "ws_host": "0.0.0.0",
        "ws_port": 9000,
        "charge_point_id": "CP001",
    }
    async with OCPPAdapter("evse-001", config) as adapter:
        telemetry = await adapter.read_data()
"""

from __future__ import annotations

import asyncio
from datetime import datetime, timezone
from typing import Any, Optional, cast

from derim.adapters.base import BaseAdapter
from derim.models.common import (
    CommandRequest,
    CommandResponse,
    ConnectorStatus,
    DERType,
    DeviceState,
    EVChargerTelemetry,
)
from derim.utils.logger import get_logger

logger = get_logger(__name__)

# Map OCPP status strings to our ConnectorStatus enum.
OCPP_STATUS_MAP: dict[str, ConnectorStatus] = {
    "Available": ConnectorStatus.AVAILABLE,
    "Preparing": ConnectorStatus.AVAILABLE,
    "Charging": ConnectorStatus.OCCUPIED,
    "SuspendedEVSE": ConnectorStatus.OCCUPIED,
    "SuspendedEV": ConnectorStatus.OCCUPIED,
    "Finishing": ConnectorStatus.OCCUPIED,
    "Reserved": ConnectorStatus.RESERVED,
    "Unavailable": ConnectorStatus.UNAVAILABLE,
    "Faulted": ConnectorStatus.FAULTED,
}


class OCPPAdapter(BaseAdapter):
    """
    Concrete adapter for OCPP 1.6-J EV charging stations.

    This adapter acts as a simplified OCPP Central System.  It starts a
    WebSocket server, waits for the configured charge point to connect,
    and then exchanges OCPP messages.

    Parameters
    ----------
    device_id : str
        Unique identifier for the EVSE device.
    config : dict[str, Any]
        Configuration with keys:

        - ``ws_host`` (str): WebSocket bind address (default ``"127.0.0.1"``).
        - ``ws_port`` (int): WebSocket port (default 9000).
        - ``charge_point_id`` (str): Expected charge point identity.
        - ``read_timeout`` (float): Seconds to wait for telemetry (default 30).
    """

    def __init__(self, device_id: str, config: Optional[dict[str, Any]] = None):
        super().__init__(device_id, config)
        self._ws_host: str = self.config.get("ws_host", "127.0.0.1")
        self._ws_port: int = self.config.get("ws_port", 9000)
        self._cp_id: str = self.config.get("charge_point_id", "CP001")
        self._read_timeout: float = self.config.get("read_timeout", 30.0)

        # Internal state.
        self._server: Any = None
        self._server_task: Optional[asyncio.Task[None]] = None
        self._latest_telemetry: Optional[EVChargerTelemetry] = None
        self._telemetry_event: asyncio.Event = asyncio.Event()
        self._charge_point: Any = None
        self._connector_status: ConnectorStatus = ConnectorStatus.UNAVAILABLE
        self._meter_values: dict[str, float] = {}

    async def connect(self) -> None:
        """
        Start the OCPP WebSocket server and wait for a charge point.

        Raises
        ------
        ConnectionError
            If the server cannot be started.
        """
        try:
            import websockets

            self._server = await websockets.serve(
                cast(Any, self._on_charge_point_connect),
                self._ws_host,
                self._ws_port,
                subprotocols=cast(Any, ["ocpp1.6", "ocpp2.0.1"]),
            )
            self._connected = True
            logger.info(
                "ocpp_server_started",
                device_id=self.device_id,
                host=self._ws_host,
                port=self._ws_port,
            )

        except ImportError as exc:
            raise ImportError(
                "websockets and ocpp are required for the OCPP adapter. "
                "Install them with: pip install websockets ocpp"
            ) from exc
        except Exception as exc:
            logger.error(
                "ocpp_server_start_failed",
                device_id=self.device_id,
                error=str(exc),
            )
            raise ConnectionError(f"OCPP server start failed: {exc}") from exc

    async def _on_charge_point_connect(self, websocket: Any, path: str) -> None:
        """
        Handle an incoming charge point WebSocket connection.

        This callback is invoked by the WebSocket server for each new
        connection.  It creates an OCPP ``ChargePoint`` handler and
        processes messages until the connection is closed.
        """
        # Extract charge point ID from the URL path.
        cp_id = path.strip("/").split("/")[-1] if "/" in path else path.strip("/")
        logger.info(
            "ocpp_charge_point_connected",
            charge_point_id=cp_id,
            path=path,
        )

        try:
            from ocpp.routing import on
            from ocpp.v16 import ChargePoint as CP16
            from ocpp.v16 import call_result
            from ocpp.v16.enums import Action, RegistrationStatus

            class ChargePointHandler(CP16):
                """OCPP 1.6 charge point message handler."""

                def __init__(self, cp_id: str, connection: Any, adapter: OCPPAdapter):
                    super().__init__(cp_id, connection)
                    self._adapter = adapter

                @on(Action.BootNotification)
                async def on_boot_notification(
                    self,
                    charge_point_vendor: str,
                    charge_point_model: str,
                    **kwargs: Any,
                ) -> call_result.BootNotification:
                    logger.info(
                        "ocpp_boot_notification",
                        vendor=charge_point_vendor,
                        model=charge_point_model,
                    )
                    return call_result.BootNotification(
                        current_time=datetime.now(timezone.utc).isoformat(),
                        interval=300,
                        status=RegistrationStatus.accepted,
                    )

                @on(Action.Heartbeat)
                async def on_heartbeat(self, **kwargs: Any) -> call_result.Heartbeat:
                    return call_result.Heartbeat(
                        current_time=datetime.now(timezone.utc).isoformat()
                    )

                @on(Action.StatusNotification)
                async def on_status_notification(
                    self,
                    connector_id: int,
                    error_code: str,
                    status: str,
                    **kwargs: Any,
                ) -> call_result.StatusNotification:
                    self._adapter._connector_status = OCPP_STATUS_MAP.get(
                        status, ConnectorStatus.UNAVAILABLE
                    )
                    self._adapter._build_telemetry()
                    logger.info(
                        "ocpp_status_notification",
                        connector_id=connector_id,
                        status=status,
                    )
                    return call_result.StatusNotification()

                @on(Action.MeterValues)
                async def on_meter_values(
                    self,
                    connector_id: int,
                    meter_value: list[dict[str, Any]],
                    **kwargs: Any,
                ) -> call_result.MeterValues:
                    for mv in meter_value:
                        for sv in mv.get("sampled_value", []):
                            measurand = sv.get(
                                "measurand", "Energy.Active.Import.Register"
                            )
                            value = float(sv.get("value", 0))
                            self._adapter._meter_values[measurand] = value

                    self._adapter._build_telemetry()
                    return call_result.MeterValues()

            handler = ChargePointHandler(cp_id, websocket, self)
            self._charge_point = handler
            await handler.start()

        except Exception as exc:
            logger.error(
                "ocpp_handler_error",
                charge_point_id=cp_id,
                error=str(exc),
            )

    def _build_telemetry(self) -> None:
        """Assemble the latest telemetry from accumulated meter values."""
        power_w = self._meter_values.get("Power.Active.Import", 0.0)
        energy_wh = self._meter_values.get("Energy.Active.Import.Register", 0.0)
        voltage = self._meter_values.get("Voltage", 0.0)
        current = self._meter_values.get("Current.Import", 0.0)

        is_charging = self._connector_status == ConnectorStatus.OCCUPIED
        state = DeviceState.ON if is_charging else DeviceState.STANDBY

        self._latest_telemetry = EVChargerTelemetry(
            timestamp=datetime.now(timezone.utc),
            device_id=self.device_id,
            device_type=DERType.EV_CHARGER,
            power_kw=power_w / 1000.0,
            energy_kwh=energy_wh / 1000.0,
            voltage_v=voltage,
            current_a=current,
            frequency_hz=50.0,
            state=state,
            connector_status=self._connector_status,
            session_energy_kwh=energy_wh / 1000.0,
            metadata={
                "protocol": "ocpp",
                "charge_point_id": self._cp_id,
            },
        )
        self._telemetry_event.set()

    async def disconnect(self) -> None:
        """Stop the WebSocket server and clean up."""
        if self._server is not None:
            self._server.close()
            await self._server.wait_closed()
            self._connected = False
            logger.info("ocpp_server_stopped", device_id=self.device_id)

    async def read_data(self) -> EVChargerTelemetry:
        """
        Return the most recent telemetry from the charge point.

        Blocks until a MeterValues or StatusNotification message is
        received, or until ``read_timeout`` expires.

        Returns
        -------
        EVChargerTelemetry
            Normalised EV charger telemetry.
        """
        self._ensure_connected()

        if self._latest_telemetry is None:
            self._telemetry_event.clear()
            try:
                await asyncio.wait_for(
                    self._telemetry_event.wait(),
                    timeout=self._read_timeout,
                )
            except asyncio.TimeoutError:
                # Return a default telemetry record if no data yet.
                return EVChargerTelemetry(
                    timestamp=datetime.now(timezone.utc),
                    device_id=self.device_id,
                    device_type=DERType.EV_CHARGER,
                    state=DeviceState.UNKNOWN,
                    connector_status=ConnectorStatus.UNAVAILABLE,
                    metadata={"protocol": "ocpp", "note": "no data received"},
                )

        telemetry = self._latest_telemetry
        self._telemetry_event.clear()
        if telemetry is None:
            raise RuntimeError("Telemetry was not available after wait completion.")
        return telemetry

    async def write_command(self, command: CommandRequest) -> CommandResponse:
        """
        Send a control command to the charge point via OCPP.

        Supported commands:

        - ``"start"``: Trigger RemoteStartTransaction.
        - ``"stop"``: Trigger RemoteStopTransaction.
        - ``"setpoint"``: Change max charging power (via ChangeConfiguration).

        Parameters
        ----------
        command : CommandRequest
            The command to dispatch.

        Returns
        -------
        CommandResponse
            Result of the OCPP call.
        """
        self._ensure_connected()

        if self._charge_point is None:
            return CommandResponse(
                device_id=self.device_id,
                command=command.command,
                status="rejected",
                message="No charge point connected",
            )

        try:
            from ocpp.v16 import call

            if command.command == "start":
                id_tag = (
                    command.parameters.get("id_tag", "DERIM0001")
                    if command.parameters
                    else "DERIM0001"
                )
                request = call.RemoteStartTransaction(id_tag=id_tag)
                response = await self._charge_point.call(request)
                return CommandResponse(
                    device_id=self.device_id,
                    command=command.command,
                    status="accepted" if response.status == "Accepted" else "rejected",
                    message=f"RemoteStartTransaction: {response.status}",
                )

            elif command.command == "stop":
                tx_id = int(
                    command.parameters.get("transaction_id", 1)
                    if command.parameters
                    else 1
                )
                request = call.RemoteStopTransaction(transaction_id=tx_id)
                response = await self._charge_point.call(request)
                return CommandResponse(
                    device_id=self.device_id,
                    command=command.command,
                    status="accepted" if response.status == "Accepted" else "rejected",
                    message=f"RemoteStopTransaction: {response.status}",
                )

            elif command.command == "setpoint" and command.value is not None:
                # Use ChangeConfiguration to set max power.
                request = call.ChangeConfiguration(
                    key="MaxChargingPowerKW",
                    value=str(command.value),
                )
                response = await self._charge_point.call(request)
                return CommandResponse(
                    device_id=self.device_id,
                    command=command.command,
                    status="accepted" if response.status == "Accepted" else "rejected",
                    message=f"ChangeConfiguration: {response.status}",
                )

            else:
                return CommandResponse(
                    device_id=self.device_id,
                    command=command.command,
                    status="rejected",
                    message=f"Unsupported OCPP command: {command.command}",
                )

        except Exception as exc:
            logger.error(
                "ocpp_command_failed",
                device_id=self.device_id,
                error=str(exc),
            )
            return CommandResponse(
                device_id=self.device_id,
                command=command.command,
                status="error",
                message=str(exc),
            )
