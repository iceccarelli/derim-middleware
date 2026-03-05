"""
Telemetry and device management API routes.

Endpoints
---------
- ``GET  /devices``                  - List all registered DER devices.
- ``POST /devices``                  - Register a new DER device.
- ``GET  /devices/{device_id}``      - Get a single device by ID.
- ``GET  /telemetry/{device_id}``    - Query telemetry for a device.
- ``POST /telemetry/{device_id}``    - Ingest telemetry for a device.
"""

from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query

from derim.api.dependencies import get_storage
from derim.models.common import DERDevice, DERTelemetry
from derim.storage.base import StorageBackend
from derim.utils.logger import get_logger

logger = get_logger(__name__)

router = APIRouter()


# ---------------------------------------------------------------------------
# Device endpoints
# ---------------------------------------------------------------------------


@router.get(
    "/devices",
    response_model=list[DERDevice],
    summary="List all registered DER devices",
    description=(
        "Returns a list of all distributed energy resource devices that "
        "have been registered with the middleware."
    ),
)
async def list_devices(
    storage: StorageBackend = Depends(get_storage),
) -> list[DERDevice]:
    """Retrieve every registered device from the storage backend."""
    devices = await storage.get_devices()
    logger.info("api_list_devices", count=len(devices))
    return devices


@router.post(
    "/devices",
    response_model=DERDevice,
    status_code=201,
    summary="Register a new DER device",
    description=(
        "Register a new distributed energy resource device with the "
        "middleware.  If a device with the same ``device_id`` already "
        "exists, its record is updated."
    ),
)
async def register_device(
    device: DERDevice,
    storage: StorageBackend = Depends(get_storage),
) -> DERDevice:
    """Register or update a DER device."""
    await storage.register_device(device)
    logger.info("api_device_registered", device_id=device.device_id)
    return device


@router.get(
    "/devices/{device_id}",
    response_model=DERDevice,
    summary="Get a single device by ID",
    description="Returns the registration record for the specified device.",
)
async def get_device(
    device_id: str,
    storage: StorageBackend = Depends(get_storage),
) -> DERDevice:
    """Retrieve a single device by its unique identifier."""
    device = await storage.get_device(device_id)
    if device is None:
        raise HTTPException(status_code=404, detail=f"Device '{device_id}' not found")
    return device


# ---------------------------------------------------------------------------
# Telemetry endpoints
# ---------------------------------------------------------------------------


@router.get(
    "/telemetry/{device_id}",
    response_model=list[DERTelemetry],
    summary="Query telemetry for a device",
    description=(
        "Retrieve time-series telemetry data for a specific device within "
        "an optional time range.  If no range is specified, the last 24 "
        "hours of data are returned."
    ),
)
async def get_telemetry(
    device_id: str,
    start: Optional[datetime] = Query(
        default=None,
        description="Start of the time range (ISO 8601 UTC)",
    ),
    end: Optional[datetime] = Query(
        default=None,
        description="End of the time range (ISO 8601 UTC)",
    ),
    limit: int = Query(
        default=1000,
        ge=1,
        le=10000,
        description="Maximum number of records to return",
    ),
    storage: StorageBackend = Depends(get_storage),
) -> list[DERTelemetry]:
    """Query telemetry records for a device within a time window."""
    now = datetime.now(timezone.utc)
    if end is None:
        end = now
    if start is None:
        start = now - timedelta(hours=24)

    results = await storage.query_range(
        device_id=device_id,
        start=start,
        end=end,
        limit=limit,
    )
    logger.info(
        "api_telemetry_query",
        device_id=device_id,
        start=start.isoformat(),
        end=end.isoformat(),
        count=len(results),
    )
    return results


@router.post(
    "/telemetry/{device_id}",
    status_code=201,
    summary="Ingest telemetry data",
    description=(
        "Submit one or more telemetry records for a device.  This "
        "endpoint is typically called by protocol adapters or data "
        "ingestion pipelines."
    ),
)
async def ingest_telemetry(
    device_id: str,
    data: list[DERTelemetry],
    storage: StorageBackend = Depends(get_storage),
) -> dict[str, str | int]:
    """Persist incoming telemetry records."""
    # Ensure device_id consistency.
    for record in data:
        record.device_id = device_id

    await storage.write_points(data)
    logger.info(
        "api_telemetry_ingested",
        device_id=device_id,
        count=len(data),
    )
    return {"status": "ok", "device_id": device_id, "records_written": len(data)}
