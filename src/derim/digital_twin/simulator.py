"""
Digital twin simulation engine.

The ``Simulator`` class creates a virtual replica of a physical DER
device by combining a trained ML model with real-time telemetry data.
It continuously compares predicted values with actual measurements to
detect anomalies, estimate performance degradation, and support
what-if scenario analysis.

Key Capabilities
----------------
- **Real-time comparison**: Overlay model predictions on live telemetry
  to compute residuals and detect deviations.
- **Anomaly detection**: Flag data points where the residual exceeds a
  configurable threshold (e.g. 3 standard deviations).
- **Scenario simulation**: Run the model with modified inputs (e.g.
  different irradiance profiles) to evaluate hypothetical outcomes.
- **Performance metrics**: Track model accuracy over time using MAE,
  RMSE, and drift indicators.

Usage
-----
::

    from derim.digital_twin.simulator import Simulator

    sim = Simulator(device_id="solar-inv-001")
    sim.load_model()
    result = sim.compare(actual_values, predicted_values)
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Optional

import numpy as np

from derim.config import Settings, get_settings
from derim.models.common import ForecastPoint
from derim.utils.logger import get_logger

logger = get_logger(__name__)


@dataclass
class SimulationResult:
    """
    Container for digital twin simulation outputs.

    Attributes
    ----------
    device_id : str
        Device being simulated.
    timestamp : datetime
        Time of the simulation run.
    actual_values : list[float]
        Observed power values (kW).
    predicted_values : list[float]
        Model-predicted power values (kW).
    residuals : list[float]
        Difference (actual - predicted) for each time step.
    mae : float
        Mean Absolute Error.
    rmse : float
        Root Mean Squared Error.
    anomaly_indices : list[int]
        Indices of data points flagged as anomalous.
    anomaly_threshold : float
        Threshold used for anomaly detection (in kW).
    """

    device_id: str
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    actual_values: list[float] = field(default_factory=list)
    predicted_values: list[float] = field(default_factory=list)
    residuals: list[float] = field(default_factory=list)
    mae: float = 0.0
    rmse: float = 0.0
    anomaly_indices: list[int] = field(default_factory=list)
    anomaly_threshold: float = 0.0


class Simulator:
    """
    Digital twin simulation engine for a single DER device.

    Parameters
    ----------
    device_id : str
        Identifier of the device to simulate.
    settings : Settings, optional
        Application settings.
    anomaly_sigma : float
        Number of standard deviations for anomaly detection (default 3.0).
    """

    def __init__(
        self,
        device_id: str,
        settings: Optional[Settings] = None,
        anomaly_sigma: float = 3.0,
    ):
        self.device_id = device_id
        self.settings = settings or get_settings()
        self.anomaly_sigma = anomaly_sigma
        self._forecaster: Any = None
        self._history: list[SimulationResult] = []

    def load_model(self) -> bool:
        """
        Load the trained LSTM model for this device.

        Returns
        -------
        bool
            ``True`` if the model was loaded successfully.
        """
        try:
            from derim.digital_twin.models.lstm_forecaster import LSTMForecaster

            self._forecaster = LSTMForecaster(settings=self.settings)
            if self._forecaster.is_model_available(self.device_id):
                logger.info("simulator_model_loaded", device_id=self.device_id)
                return True
            else:
                logger.warning("simulator_no_model", device_id=self.device_id)
                return False
        except Exception as exc:
            logger.error(
                "simulator_model_load_failed",
                device_id=self.device_id,
                error=str(exc),
            )
            return False

    def compare(
        self,
        actual_values: list[float],
        predicted_values: list[float],
    ) -> SimulationResult:
        """
        Compare actual telemetry with model predictions.

        Parameters
        ----------
        actual_values : list[float]
            Observed power values (kW).
        predicted_values : list[float]
            Model-predicted power values (kW).

        Returns
        -------
        SimulationResult
            Comparison metrics and anomaly flags.
        """
        actual = np.array(actual_values)
        predicted = np.array(predicted_values)

        # Align lengths.
        min_len = min(len(actual), len(predicted))
        actual = actual[:min_len]
        predicted = predicted[:min_len]

        residuals = actual - predicted
        mae = float(np.mean(np.abs(residuals)))
        rmse = float(np.sqrt(np.mean(residuals**2)))

        # Anomaly detection: flag points where |residual| > sigma * std.
        std = float(np.std(residuals)) if len(residuals) > 1 else 0.0
        threshold = self.anomaly_sigma * std
        anomaly_indices = [
            int(i)
            for i, r in enumerate(residuals)
            if abs(r) > threshold and threshold > 0
        ]

        result = SimulationResult(
            device_id=self.device_id,
            actual_values=actual.tolist(),
            predicted_values=predicted.tolist(),
            residuals=residuals.tolist(),
            mae=round(mae, 4),
            rmse=round(rmse, 4),
            anomaly_indices=anomaly_indices,
            anomaly_threshold=round(threshold, 4),
        )

        self._history.append(result)

        logger.info(
            "simulation_comparison_complete",
            device_id=self.device_id,
            mae=result.mae,
            rmse=result.rmse,
            anomalies=len(anomaly_indices),
        )
        return result

    def run_scenario(
        self,
        input_values: list[float],
        horizon_hours: int = 24,
    ) -> list[ForecastPoint]:
        """
        Run a what-if scenario using the trained model.

        Parameters
        ----------
        input_values : list[float]
            Hypothetical input sequence (e.g. modified irradiance).
        horizon_hours : int
            Forecast horizon in hours.

        Returns
        -------
        list[ForecastPoint]
            Predicted output under the given scenario.

        Raises
        ------
        RuntimeError
            If no model is loaded.
        """
        if self._forecaster is None:
            raise RuntimeError("No model loaded. Call load_model() first.")

        predictions = self._forecaster.predict(
            device_id=self.device_id,
            horizon_hours=horizon_hours,
            recent_values=input_values,
        )

        logger.info(
            "scenario_simulation_complete",
            device_id=self.device_id,
            horizon_hours=horizon_hours,
            points=len(predictions),
        )
        return predictions

    def get_history(self) -> list[SimulationResult]:
        """Return the history of simulation results."""
        return list(self._history)

    def get_drift_indicator(self) -> float:
        """
        Compute a model drift indicator based on recent simulation history.

        The drift indicator is the ratio of the most recent MAE to the
        average MAE across all historical comparisons.  A value
        significantly above 1.0 suggests model degradation.

        Returns
        -------
        float
            Drift ratio (1.0 = no drift).
        """
        if len(self._history) < 2:
            return 1.0

        recent_mae = self._history[-1].mae
        avg_mae = float(np.mean([r.mae for r in self._history]))

        if avg_mae < 1e-6:
            return 1.0

        drift = recent_mae / avg_mae
        logger.debug(
            "drift_indicator",
            device_id=self.device_id,
            drift=round(drift, 4),
        )
        return round(drift, 4)
