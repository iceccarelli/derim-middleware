"""
Abstract base class for time-series storage backends.

All storage implementations must inherit from ``StorageBackend`` and
provide concrete implementations of the lifecycle and data-access
methods defined here.  This abstraction allows the rest of the
middleware to remain agnostic of the underlying database technology.
"""

from abc import ABC, abstractmethod
from datetime import datetime
from typing import Optional

from derim.models.common import DERDevice, DERTelemetry


class StorageBackend(ABC):
    """
    Abstract interface for time-series telemetry storage.

    Implementations must support:

    1. **Connection lifecycle** - ``connect()`` and ``disconnect()``.
    2. **Telemetry persistence** - ``write_points()`` to store one or
       more ``DERTelemetry`` records.
    3. **Telemetry retrieval** - ``query_range()`` to fetch records for
       a device within a time window.
    4. **Device registry** - ``register_device()``, ``get_devices()``,
       and ``get_device()`` for managing known DER devices.
    """

    # -- Lifecycle --

    @abstractmethod
    async def connect(self) -> None:
        """
        Establish a connection to the storage backend.

        This method is called once during application startup.

        Raises
        ------
        ConnectionError
            If the backend is unreachable.
        """

    @abstractmethod
    async def disconnect(self) -> None:
        """
        Gracefully close the connection to the storage backend.

        This method is called during application shutdown and must be
        idempotent.
        """

    # -- Telemetry --

    @abstractmethod
    async def write_points(self, data: list[DERTelemetry]) -> None:
        """
        Persist one or more telemetry records.

        Parameters
        ----------
        data : list[DERTelemetry]
            Telemetry records to store.  Each record contains its own
            ``device_id`` and ``timestamp``.

        Raises
        ------
        IOError
            If the write operation fails.
        """

    @abstractmethod
    async def query_range(
        self,
        device_id: str,
        start: datetime,
        end: datetime,
        limit: int = 1000,
    ) -> list[DERTelemetry]:
        """
        Retrieve telemetry records for a device within a time range.

        Parameters
        ----------
        device_id : str
            Device to query.
        start : datetime
            Inclusive start of the time range (UTC).
        end : datetime
            Inclusive end of the time range (UTC).
        limit : int
            Maximum number of records to return (default 1000).

        Returns
        -------
        list[DERTelemetry]
            Matching telemetry records ordered by timestamp ascending.
        """

    # -- Device Registry --

    @abstractmethod
    async def register_device(self, device: DERDevice) -> None:
        """
        Register or update a DER device in the device registry.

        Parameters
        ----------
        device : DERDevice
            Device metadata to persist.
        """

    @abstractmethod
    async def get_devices(self) -> list[DERDevice]:
        """
        Return all registered DER devices.

        Returns
        -------
        list[DERDevice]
            List of known devices.
        """

    @abstractmethod
    async def get_device(self, device_id: str) -> Optional[DERDevice]:
        """
        Return a single device by its identifier.

        Parameters
        ----------
        device_id : str
            Unique device identifier.

        Returns
        -------
        DERDevice or None
            The device record, or ``None`` if not found.
        """
