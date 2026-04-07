"""
FastAPI application entry point for the DERIM middleware.

This module creates the FastAPI application instance, registers API routers,
configures middleware, and sets up application lifecycle events (startup and
shutdown hooks for storage backends and protocol adapters).

Run with::

    uvicorn derim.main:app --reload
"""

from contextlib import asynccontextmanager
from typing import AsyncIterator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from derim.api.routes import control, data, digital_twin
from derim.config import get_settings
from derim.storage import get_storage_backend
from derim.utils.logger import configure_logging, get_logger

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """
    Manage application startup and shutdown lifecycle.

    On startup the logging subsystem is initialised and the configured
    storage backend is connected.  On shutdown the storage backend is
    closed gracefully.
    """
    configure_logging()
    settings = get_settings()
    logger.info(
        "starting_derim_middleware",
        app_name=settings.app_name,
        environment=settings.app_env,
        storage=settings.storage_backend.value,
    )

    # Initialise storage backend and attach to app state.
    storage = get_storage_backend(settings)
    await storage.connect()
    app.state.storage = storage

    yield

    # Shutdown: close storage connections.
    await storage.disconnect()
    logger.info("derim_middleware_stopped")


def create_app() -> FastAPI:
    """
    Factory function that builds and returns the configured FastAPI app.

    Returns
    -------
    FastAPI
        The fully configured application instance.
    """
    settings = get_settings()

    application = FastAPI(
        title="DERIM Middleware API",
        description=(
            "Smart Grid Digital Twin Middleware for Distributed Energy "
            "Resource Integration.  Provides REST endpoints for device "
            "telemetry, control commands, and ML-based forecasting."
        ),
        version="0.1.1",
        docs_url="/docs",
        redoc_url="/redoc",
        lifespan=lifespan,
    )

    # CORS - allow all origins in development; restrict in production.
    application.add_middleware(
        CORSMiddleware,
        allow_origins=["*"] if settings.app_debug else [],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Register API routers.
    application.include_router(data.router, prefix="/api/v1", tags=["Telemetry"])
    application.include_router(control.router, prefix="/api/v1", tags=["Control"])
    application.include_router(
        digital_twin.router, prefix="/api/v1", tags=["Digital Twin"]
    )

    @application.get("/", tags=["Health"])
    async def root() -> dict[str, str]:
        """Health-check endpoint."""
        return {"status": "ok", "service": settings.app_name}

    @application.get("/health", tags=["Health"])
    async def health() -> dict[str, str]:
        """Detailed health check."""
        return {
            "status": "healthy",
            "service": settings.app_name,
            "version": "0.1.1",
            "storage": settings.storage_backend.value,
        }

    return application


# Application instance used by ``uvicorn``.
app = create_app()
