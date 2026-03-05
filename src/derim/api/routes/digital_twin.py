"""
Digital Twin / Forecasting API routes.

Endpoints
---------
- ``GET  /forecast/models``       - List available trained models.
- ``GET  /forecast/{device_id}``  - Generate an ML forecast for a device.

These endpoints integrate with the ``derim.digital_twin`` module to
provide machine-learning-based power generation and load forecasting.

Note: ``/forecast/models`` is defined *before* ``/forecast/{device_id}``
so that FastAPI matches the literal path before the parameterised one.
"""

from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, Query

from derim.api.dependencies import get_app_settings, get_storage
from derim.config import Settings
from derim.models.common import ForecastPoint, ForecastResponse
from derim.storage.base import StorageBackend
from derim.utils.logger import get_logger

logger = get_logger(__name__)

router = APIRouter()


# ---- /forecast/models MUST come before /forecast/{device_id} ----


@router.get(
    "/forecast/models",
    summary="List available trained models",
    description="Returns a list of model files found in the model save directory.",
)
async def list_models(
    settings: Settings = Depends(get_app_settings),
) -> dict[str, list[str]]:
    """List trained model files available for forecasting."""
    from pathlib import Path

    model_dir = Path(settings.model_save_dir)
    if not model_dir.exists():
        return {"models": []}

    model_files = [
        f.name
        for f in model_dir.iterdir()
        if f.is_file() and f.suffix in (".pt", ".pth", ".h5", ".pkl", ".joblib")
    ]
    return {"models": sorted(model_files)}


# ---- /forecast/{device_id} ----


@router.get(
    "/forecast/{device_id}",
    response_model=ForecastResponse,
    summary="Get ML forecast for a device",
    description=(
        "Generate a power forecast for the specified device using the "
        "digital twin's trained LSTM model.  If no trained model is "
        "available, a simple persistence baseline is used instead.\n\n"
        "The forecast horizon defaults to 24 hours and can be adjusted "
        "via the ``horizon_hours`` query parameter."
    ),
)
async def get_forecast(
    device_id: str,
    horizon_hours: int = Query(
        default=24,
        ge=1,
        le=168,
        description="Forecast horizon in hours (1-168)",
    ),
    storage: StorageBackend = Depends(get_storage),
    settings: Settings = Depends(get_app_settings),
) -> ForecastResponse:
    """
    Generate a forecast for the given device.

    The handler attempts to load a trained LSTM model from the model
    save directory.  If no model is found, it falls back to a
    persistence baseline that repeats the last known value.
    """
    # Verify device exists.
    device = await storage.get_device(device_id)
    if device is None:
        raise HTTPException(
            status_code=404,
            detail=f"Device '{device_id}' not found.",
        )

    # Attempt to use the digital twin forecaster.
    try:
        from derim.digital_twin.models.lstm_forecaster import LSTMForecaster

        forecaster = LSTMForecaster(settings=settings)
        if forecaster.is_model_available(device_id):
            predictions = forecaster.predict(
                device_id=device_id,
                horizon_hours=horizon_hours,
            )
            logger.info(
                "api_forecast_lstm",
                device_id=device_id,
                horizon_hours=horizon_hours,
                points=len(predictions),
            )
            return ForecastResponse(
                device_id=device_id,
                model_name="lstm",
                horizon_hours=horizon_hours,
                predictions=predictions,
            )
    except Exception as exc:
        logger.warning(
            "api_forecast_lstm_unavailable",
            device_id=device_id,
            error=str(exc),
        )

    # Fallback: persistence baseline using recent telemetry.
    now = datetime.now(timezone.utc)
    recent = await storage.query_range(
        device_id=device_id,
        start=now - timedelta(hours=24),
        end=now,
        limit=96,  # ~15-min intervals for 24h
    )

    if not recent:
        # No historical data available; return a flat zero forecast.
        predictions = [
            ForecastPoint(
                timestamp=now + timedelta(minutes=15 * i),
                power_kw=0.0,
            )
            for i in range(horizon_hours * 4)
        ]
    else:
        # Persistence: repeat the most recent 24h pattern.
        predictions = []
        for i in range(horizon_hours * 4):
            idx = i % len(recent)
            predictions.append(
                ForecastPoint(
                    timestamp=now + timedelta(minutes=15 * i),
                    power_kw=recent[idx].power_kw,
                    confidence_lower=recent[idx].power_kw * 0.8,
                    confidence_upper=recent[idx].power_kw * 1.2,
                )
            )

    logger.info(
        "api_forecast_baseline",
        device_id=device_id,
        horizon_hours=horizon_hours,
        points=len(predictions),
    )

    return ForecastResponse(
        device_id=device_id,
        model_name="persistence_baseline",
        horizon_hours=horizon_hours,
        predictions=predictions,
    )
