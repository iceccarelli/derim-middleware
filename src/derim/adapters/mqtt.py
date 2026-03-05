"""
MQTT protocol adapter for DER devices.

This adapter uses the ``paho-mqtt`` library to subscribe to MQTT topics
published by DER devices (or gateways) and to send control commands back
via MQTT publish.  It is well suited for IoT-style deployments where
devices report telemetry over a lightweight publish/subscribe transport.

Topic Convention
----------------
The adapter subscribes to topics matching the pattern::

    {topic_prefix}/{device_id}/telemetry

Control commands are published to::

    {topic_prefix}/{device_id}/command

Payloads are expected to be JSON objects whose keys correspond to fields
in the ``DERTelemetry`` model.

Usage
-----
::

    from derim.adapters.mqtt import MQTTAdapter

    config = {
        "broker": "mqtt.example.com",
        "port": 1883,
        "topic_prefix": "derim/devices",
    }
    async with MQTTAdapter("battery-001", config) as adapter:
        telemetry = await adapter.read_data()
"""

from __future__ import annotations

import asyncio
import json
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


class MQTTAdapter(BaseAdapter):
    """
    Concrete adapter for MQTT-based DER communication.

    The adapter maintains an internal message buffer.  When
    ``read_data()`` is called it returns the most recent telemetry
    message received on the subscribed topic.  If no message has
    arrived yet, it waits up to ``read_timeout`` seconds.

    Parameters
    ----------
    device_id : str
        Unique identifier for the target device.
    config : dict[str, Any]
        Configuration dictionary with keys:

        - ``broker`` (str): MQTT broker hostname.
        - ``port`` (int): MQTT broker port (default 1883).
        - ``username`` (str, optional): Authentication username.
        - ``password`` (str, optional): Authentication password.
        - ``topic_prefix`` (str): Base topic (default ``"derim/devices"``).
        - ``qos`` (int): Subscription QoS level (default 1).
        - ``read_timeout`` (float): Seconds to wait for a message (default 10).
        - ``device_type`` (str): DER type string (default ``"generic"``).
    """

    def __init__(self, device_id: str, config: Optional[dict[str, Any]] = None):
        super().__init__(device_id, config)
        self._broker: str = self.config.get("broker", "localhost")
        self._port: int = self.config.get("port", 1883)
        self._username: Optional[str] = self.config.get("username")
        self._password: Optional[str] = self.config.get("password")
        self._topic_prefix: str = self.config.get("topic_prefix", "derim/devices")
        self._qos: int = self.config.get("qos", 1)
        self._read_timeout: float = self.config.get("read_timeout", 10.0)
        self._device_type_str: str = self.config.get("device_type", "generic")
        self._client: Any = None
        self._latest_message: Optional[dict[str, Any]] = None
        self._message_event: asyncio.Event = asyncio.Event()
        self._loop: Optional[asyncio.AbstractEventLoop] = None

    @property
    def _telemetry_topic(self) -> str:
        """Full MQTT topic for telemetry subscription."""
        return f"{self._topic_prefix}/{self.device_id}/telemetry"

    @property
    def _command_topic(self) -> str:
        """Full MQTT topic for publishing commands."""
        return f"{self._topic_prefix}/{self.device_id}/command"

    # -- Callbacks (run in paho-mqtt's network thread) --

    def _on_connect(
        self, client: Any, userdata: Any, flags: Any, rc: int, *args: Any
    ) -> None:
        """Handle successful connection and subscribe to the telemetry topic."""
        if rc == 0:
            client.subscribe(self._telemetry_topic, qos=self._qos)
            logger.info(
                "mqtt_subscribed",
                device_id=self.device_id,
                topic=self._telemetry_topic,
            )
        else:
            logger.error(
                "mqtt_connect_failed",
                device_id=self.device_id,
                return_code=rc,
            )

    def _on_message(self, client: Any, userdata: Any, msg: Any) -> None:
        """Store the latest message and signal the waiting coroutine."""
        try:
            payload = json.loads(msg.payload.decode("utf-8"))
            self._latest_message = payload
            # Thread-safe event set via the event loop.
            if self._loop and not self._loop.is_closed():
                self._loop.call_soon_threadsafe(self._message_event.set)
        except (json.JSONDecodeError, UnicodeDecodeError) as exc:
            logger.warning(
                "mqtt_payload_decode_error",
                device_id=self.device_id,
                topic=msg.topic,
                error=str(exc),
            )

    # -- Lifecycle --

    async def connect(self) -> None:
        """
        Connect to the MQTT broker and start the network loop.

        Raises
        ------
        ConnectionError
            If the broker is unreachable.
        """
        try:
            import paho.mqtt.client as paho_mqtt

            self._loop = asyncio.get_running_loop()
            self._client = paho_mqtt.Client(
                client_id=f"derim-{self.device_id}",
                protocol=paho_mqtt.MQTTv311,
            )

            if self._username:
                self._client.username_pw_set(self._username, self._password)

            self._client.on_connect = self._on_connect
            self._client.on_message = self._on_message

            self._client.connect_async(self._broker, self._port, keepalive=60)
            self._client.loop_start()
            self._connected = True

            logger.info(
                "mqtt_connected",
                device_id=self.device_id,
                broker=self._broker,
                port=self._port,
            )

        except ImportError:
            raise ImportError(
                "paho-mqtt is required for the MQTT adapter. "
                "Install it with: pip install paho-mqtt"
            )
        except Exception as exc:
            logger.error(
                "mqtt_connection_error",
                device_id=self.device_id,
                error=str(exc),
            )
            raise ConnectionError(
                f"MQTT connection failed for {self.device_id}: {exc}"
            ) from exc

    async def disconnect(self) -> None:
        """Stop the network loop and disconnect from the broker."""
        if self._client is not None:
            self._client.loop_stop()
            self._client.disconnect()
            self._connected = False
            logger.info("mqtt_disconnected", device_id=self.device_id)

    async def read_data(self) -> DERTelemetry:
        """
        Return the most recent telemetry message from the subscribed topic.

        If no message has been received yet, the method waits up to
        ``read_timeout`` seconds for one to arrive.

        Returns
        -------
        DERTelemetry
            Normalised telemetry record built from the JSON payload.

        Raises
        ------
        TimeoutError
            If no message is received within the timeout.
        """
        self._ensure_connected()

        if self._latest_message is None:
            self._message_event.clear()
            try:
                await asyncio.wait_for(
                    self._message_event.wait(), timeout=self._read_timeout
                )
            except asyncio.TimeoutError:
                raise TimeoutError(
                    f"No MQTT message received for device {self.device_id} "
                    f"within {self._read_timeout}s"
                )

        payload = self._latest_message or {}

        # Parse device type.
        try:
            device_type = DERType(payload.get("device_type", self._device_type_str))
        except ValueError:
            device_type = DERType.GENERIC

        # Parse device state.
        try:
            state = DeviceState(payload.get("state", "unknown"))
        except ValueError:
            state = DeviceState.UNKNOWN

        telemetry = DERTelemetry(
            timestamp=datetime.now(timezone.utc),
            device_id=self.device_id,
            device_type=device_type,
            power_kw=float(payload.get("power_kw", 0.0)),
            energy_kwh=float(payload.get("energy_kwh", 0.0)),
            voltage_v=float(payload.get("voltage_v", 0.0)),
            current_a=float(payload.get("current_a", 0.0)),
            frequency_hz=float(payload.get("frequency_hz", 50.0)),
            state=state,
            power_factor=payload.get("power_factor"),
            metadata={"protocol": "mqtt", "topic": self._telemetry_topic},
        )

        # Reset for next read.
        self._latest_message = None
        self._message_event.clear()

        logger.debug(
            "mqtt_data_read",
            device_id=self.device_id,
            power_kw=telemetry.power_kw,
        )
        return telemetry

    async def write_command(self, command: CommandRequest) -> CommandResponse:
        """
        Publish a control command to the device's command topic.

        The command is serialised as a JSON object and published with
        QoS 1 to ensure delivery.

        Parameters
        ----------
        command : CommandRequest
            The command to dispatch.

        Returns
        -------
        CommandResponse
            Acknowledgement of the publish operation.
        """
        self._ensure_connected()

        try:
            payload = {
                "command": command.command,
                "value": command.value,
                "parameters": command.parameters,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
            result = self._client.publish(
                self._command_topic,
                json.dumps(payload),
                qos=self._qos,
            )
            result.wait_for_publish(timeout=5.0)

            logger.info(
                "mqtt_command_published",
                device_id=self.device_id,
                topic=self._command_topic,
                command=command.command,
            )
            return CommandResponse(
                device_id=self.device_id,
                command=command.command,
                status="accepted",
                message=f"Published to {self._command_topic}",
            )

        except Exception as exc:
            logger.error(
                "mqtt_command_failed",
                device_id=self.device_id,
                error=str(exc),
            )
            return CommandResponse(
                device_id=self.device_id,
                command=command.command,
                status="error",
                message=str(exc),
            )
