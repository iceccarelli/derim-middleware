"""
Time-series storage backends for the DERIM middleware.

This package provides an abstract ``StorageBackend`` interface and two
concrete implementations:

- ``InfluxDBStorage``: High-performance time-series database for
  production deployments.
- ``SQLiteStorage``: Lightweight file-based fallback for development,
  testing, and single-node deployments.

The ``get_storage_backend()`` factory function selects the appropriate
backend based on the application configuration.
"""

from derim.config import Settings, StorageBackendType
from derim.storage.base import StorageBackend


def get_storage_backend(settings: Settings) -> StorageBackend:
    """
    Factory function that returns the configured storage backend.

    Parameters
    ----------
    settings : Settings
        Application settings containing the ``storage_backend`` choice
        and backend-specific connection parameters.

    Returns
    -------
    StorageBackend
        An instance of the selected storage backend (not yet connected).

    Raises
    ------
    ValueError
        If the configured backend type is not recognised.
    """
    if settings.storage_backend == StorageBackendType.INFLUXDB:
        from derim.storage.influxdb import InfluxDBStorage

        return InfluxDBStorage(
            url=settings.influxdb_url,
            token=settings.influxdb_token,
            org=settings.influxdb_org,
            bucket=settings.influxdb_bucket,
        )

    elif settings.storage_backend == StorageBackendType.SQLITE:
        from derim.storage.sqlite import SQLiteStorage

        return SQLiteStorage(db_path=settings.sqlite_db_path)

    else:
        raise ValueError(
            f"Unknown storage backend: {settings.storage_backend}. "
            "Supported values: 'influxdb', 'sqlite'."
        )


__all__ = ["StorageBackend", "get_storage_backend"]
