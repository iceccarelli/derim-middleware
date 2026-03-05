"""
Abstract base class for all DER protocol adapters.

Every concrete adapter (Modbus, MQTT, SunSpec, OCPP) must inherit from
``BaseAdapter`` and implement the four core lifecycle methods:

1. ``connect()``   - Establish a connection to the device or broker.
2. ``disconnect()`` - Tear down the connection gracefully.
3. ``read_data()``  - Poll or receive telemetry and return normalised data.
4. ``write_command()`` - Send a control command to the device.

Adapters are designed to be used as async context managers::

    async with ModbusAdapter(config) as adapter:
        data = await adapter.read_data()
"""

from abc import ABC, abstractmethod
from typing import Any, Optional

from derim.models.common import CommandRequest, CommandResponse, DERTelemetry
from derim.utils.logger import get_logger

logger = get_logger(__name__)


class BaseAdapter(ABC):
    """
    Abstract base class for DER protocol adapters.

    Parameters
    ----------
    device_id : str
        Unique identifier assigned to the device this adapter manages.
    config : dict[str, Any]
        Protocol-specific configuration (host, port, credentials, etc.).
    """

    def __init__(self, device_id: str, config: Optional[dict[str, Any]] = None):
        self.device_id = device_id
        self.config = config or {}
        self._connected = False

    @property
    def is_connected(self) -> bool:
        """Return ``True`` if the adapter has an active connection."""
        return self._connected

    # -- Async context manager support --

    async def __aenter__(self) -> "BaseAdapter":
        await self.connect()
        return self

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        await self.disconnect()

    # -- Abstract interface --

    @abstractmethod
    async def connect(self) -> None:
        """
        Establish a connection to the target device or message broker.

        Raises
        ------
        ConnectionError
            If the connection cannot be established.
        """

    @abstractmethod
    async def disconnect(self) -> None:
        """
        Gracefully close the connection.

        This method must be idempotent - calling it on an already
        disconnected adapter should be a no-op.
        """

    @abstractmethod
    async def read_data(self) -> DERTelemetry:
        """
        Read the latest telemetry from the device.

        Returns
        -------
        DERTelemetry
            Normalised telemetry record.

        Raises
        ------
        RuntimeError
            If the adapter is not connected.
        IOError
            If the read operation fails.
        """

    @abstractmethod
    async def write_command(self, command: CommandRequest) -> CommandResponse:
        """
        Send a control command to the device.

        Parameters
        ----------
        command : CommandRequest
            The command to dispatch.

        Returns
        -------
        CommandResponse
            Acknowledgement from the device or adapter.
        """

    # -- Helpers --

    def _ensure_connected(self) -> None:
        """Raise ``RuntimeError`` if the adapter is not connected."""
        if not self._connected:
            raise RuntimeError(
                f"Adapter for device '{self.device_id}' is not connected. "
                "Call connect() first."
            )
