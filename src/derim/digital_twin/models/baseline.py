"""
Baseline forecasting models for benchmarking.

These simple models serve as performance baselines against which the
LSTM forecaster is evaluated.  They require no training and operate
directly on historical telemetry data.

Models
------
- **PersistenceForecaster**: Repeats the last observed value (or the
  last 24-hour pattern) over the forecast horizon.
- **MovingAverageForecaster**: Uses a rolling mean of recent
  observations as the forecast.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Optional

import numpy as np

from derim.models.common import ForecastPoint
from derim.utils.logger import get_logger

logger = get_logger(__name__)


class PersistenceForecaster:
    """
    Persistence (naive) forecaster.

    Assumes that future values will be identical to the most recent
    observed values.  For solar forecasting, this typically means
    repeating yesterday's generation profile.

    Parameters
    ----------
    interval_minutes : int
        Time interval between forecast points (default 15).
    """

    def __init__(self, interval_minutes: int = 15):
        self.interval_minutes = interval_minutes

    def predict(
        self,
        history: list[float],
        horizon_hours: int = 24,
        start_time: Optional[datetime] = None,
    ) -> list[ForecastPoint]:
        """
        Generate a persistence forecast.

        Parameters
        ----------
        history : list[float]
            Recent power values (kW) at ``interval_minutes`` resolution.
        horizon_hours : int
            Number of hours to forecast.
        start_time : datetime, optional
            Forecast start time (defaults to now UTC).

        Returns
        -------
        list[ForecastPoint]
            Forecast data points.
        """
        if start_time is None:
            start_time = datetime.now(timezone.utc)

        n_points = int(horizon_hours * 60 / self.interval_minutes)

        if not history:
            return [
                ForecastPoint(
                    timestamp=start_time + timedelta(minutes=self.interval_minutes * i),
                    power_kw=0.0,
                )
                for i in range(n_points)
            ]

        predictions: list[ForecastPoint] = []
        for i in range(n_points):
            idx = i % len(history)
            value = history[idx]
            predictions.append(
                ForecastPoint(
                    timestamp=start_time + timedelta(minutes=self.interval_minutes * i),
                    power_kw=value,
                    confidence_lower=value * 0.8,
                    confidence_upper=value * 1.2,
                )
            )

        logger.debug(
            "persistence_forecast_generated",
            horizon_hours=horizon_hours,
            points=len(predictions),
        )
        return predictions


class MovingAverageForecaster:
    """
    Moving-average forecaster.

    Uses the mean of the last ``window_size`` observations as a flat
    forecast over the entire horizon.

    Parameters
    ----------
    window_size : int
        Number of recent observations to average (default 96 = 24h at
        15-min intervals).
    interval_minutes : int
        Time interval between forecast points (default 15).
    """

    def __init__(self, window_size: int = 96, interval_minutes: int = 15):
        self.window_size = window_size
        self.interval_minutes = interval_minutes

    def predict(
        self,
        history: list[float],
        horizon_hours: int = 24,
        start_time: Optional[datetime] = None,
    ) -> list[ForecastPoint]:
        """
        Generate a moving-average forecast.

        Parameters
        ----------
        history : list[float]
            Recent power values (kW).
        horizon_hours : int
            Number of hours to forecast.
        start_time : datetime, optional
            Forecast start time.

        Returns
        -------
        list[ForecastPoint]
            Forecast data points (flat line at the moving average).
        """
        if start_time is None:
            start_time = datetime.now(timezone.utc)

        n_points = int(horizon_hours * 60 / self.interval_minutes)

        if not history:
            avg = 0.0
        else:
            window = history[-self.window_size :]
            avg = float(np.mean(window))

        std = float(np.std(history[-self.window_size :])) if len(history) > 1 else 0.0

        predictions = [
            ForecastPoint(
                timestamp=start_time + timedelta(minutes=self.interval_minutes * i),
                power_kw=avg,
                confidence_lower=max(0.0, avg - 1.96 * std),
                confidence_upper=avg + 1.96 * std,
            )
            for i in range(n_points)
        ]

        logger.debug(
            "moving_average_forecast_generated",
            avg_power_kw=avg,
            horizon_hours=horizon_hours,
            points=len(predictions),
        )
        return predictions
