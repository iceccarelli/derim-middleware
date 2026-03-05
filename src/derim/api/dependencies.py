"""
FastAPI dependency injection providers.

This module defines reusable dependencies that are injected into route
handlers via FastAPI's ``Depends()`` mechanism.  The primary dependency
is the storage backend, which is attached to the application state
during startup and retrieved here for use in endpoint handlers.
"""

from fastapi import Request

from derim.config import Settings, get_settings
from derim.storage.base import StorageBackend


def get_storage(request: Request) -> StorageBackend:
    """
    Retrieve the active storage backend from the application state.

    This dependency is injected into route handlers that need to read
    or write telemetry data.

    Parameters
    ----------
    request : Request
        The incoming FastAPI request (provides access to ``app.state``).

    Returns
    -------
    StorageBackend
        The initialised storage backend instance.

    Raises
    ------
    RuntimeError
        If the storage backend has not been initialised (indicates a
        startup lifecycle error).
    """
    storage: StorageBackend | None = getattr(request.app.state, "storage", None)
    if storage is None:
        raise RuntimeError(
            "Storage backend is not available. "
            "Ensure the application lifespan initialised correctly."
        )
    return storage


def get_app_settings() -> Settings:
    """
    Return the application settings singleton.

    This is a thin wrapper around ``get_settings()`` that can be
    overridden in tests via ``app.dependency_overrides``.

    Returns
    -------
    Settings
        The validated application configuration.
    """
    return get_settings()
