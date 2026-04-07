"""
Model training pipeline for the digital twin module.

The ``Trainer`` class provides a high-level interface for loading
historical DER telemetry data (from CSV files or the storage backend),
preprocessing it, training ML models (LSTM or baseline), and persisting
the trained artefacts to disk.

Usage
-----
::

    from derim.digital_twin.trainer import Trainer

    trainer = Trainer()
    metrics = trainer.train_from_csv(
        device_id="solar-inv-001",
        csv_path="data/sample_solar_data.csv",
        target_column="power_kw",
    )
    print(metrics)
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Optional

import numpy as np
import pandas as pd

from derim.config import Settings, get_settings
from derim.utils.logger import get_logger

logger = get_logger(__name__)


class Trainer:
    """
    Training pipeline for DER forecasting models.

    Parameters
    ----------
    settings : Settings, optional
        Application settings.  Defaults to the global singleton.
    """

    def __init__(self, settings: Optional[Settings] = None):
        self.settings = settings or get_settings()

    def load_csv(
        self,
        csv_path: str | Path,
        timestamp_column: str = "timestamp",
        parse_dates: bool = True,
    ) -> pd.DataFrame:
        """
        Load and validate a CSV file containing historical telemetry.

        Parameters
        ----------
        csv_path : str or Path
            Path to the CSV file.
        timestamp_column : str
            Name of the timestamp column.
        parse_dates : bool
            Whether to parse the timestamp column as datetime.

        Returns
        -------
        pd.DataFrame
            Loaded and sorted DataFrame.

        Raises
        ------
        FileNotFoundError
            If the CSV file does not exist.
        ValueError
            If required columns are missing.
        """
        path = Path(csv_path)
        if not path.exists():
            raise FileNotFoundError(f"CSV file not found: {path}")

        df = pd.read_csv(path, parse_dates=[timestamp_column] if parse_dates else False)
        df = df.sort_values(timestamp_column).reset_index(drop=True)

        logger.info(
            "csv_loaded",
            path=str(path),
            rows=len(df),
            columns=list(df.columns),
        )
        return df

    def preprocess(
        self,
        df: pd.DataFrame,
        target_column: str = "power_kw",
        fill_method: str = "ffill",
    ) -> pd.DataFrame:
        """
        Preprocess the DataFrame for model training.

        Steps:

        1. Drop rows where the target column is entirely NaN.
        2. Forward-fill (or interpolate) missing values.
        3. Clip negative power values to zero (for solar generation).
        4. Reset the index.

        Parameters
        ----------
        df : pd.DataFrame
            Raw telemetry DataFrame.
        target_column : str
            Name of the target variable column.
        fill_method : str
            Method for filling missing values (``"ffill"`` or ``"interpolate"``).

        Returns
        -------
        pd.DataFrame
            Cleaned DataFrame.
        """
        if target_column not in df.columns:
            raise ValueError(
                f"Target column '{target_column}' not found in DataFrame. "
                f"Available columns: {list(df.columns)}"
            )

        df = df.copy()

        # Fill missing values.
        if fill_method == "interpolate":
            df[target_column] = df[target_column].interpolate(method="linear")
        else:
            df[target_column] = df[target_column].ffill().bfill()

        # Clip negative values.
        df[target_column] = df[target_column].clip(lower=0.0)

        # Drop remaining NaNs.
        df = df.dropna(subset=[target_column]).reset_index(drop=True)

        logger.info(
            "data_preprocessed",
            rows=len(df),
            target_column=target_column,
            fill_method=fill_method,
        )
        return df

    def train_from_csv(
        self,
        device_id: str,
        csv_path: str | Path,
        target_column: str = "power_kw",
        epochs: Optional[int] = None,
        batch_size: Optional[int] = None,
    ) -> dict[str, Any]:
        """
        End-to-end training pipeline: load CSV, preprocess, train LSTM.

        Parameters
        ----------
        device_id : str
            Device identifier for model persistence.
        csv_path : str or Path
            Path to the historical data CSV.
        target_column : str
            Column containing the target variable.
        epochs : int, optional
            Number of training epochs.
        batch_size : int, optional
            Training batch size.

        Returns
        -------
        dict[str, Any]
            Training metrics including loss history.
        """
        df = self.load_csv(csv_path)
        df = self.preprocess(df, target_column=target_column)

        from derim.digital_twin.models.lstm_forecaster import LSTMForecaster

        forecaster = LSTMForecaster(settings=self.settings)
        metrics = forecaster.train(
            device_id=device_id,
            data=df,
            target_column=target_column,
            epochs=epochs,
            batch_size=batch_size,
        )

        logger.info(
            "training_pipeline_complete",
            device_id=device_id,
            csv_path=str(csv_path),
            best_val_loss=metrics.get("best_val_loss"),
        )
        return metrics

    def evaluate(
        self,
        device_id: str,
        test_data: pd.DataFrame,
        target_column: str = "power_kw",
    ) -> dict[str, float]:
        """
        Evaluate a trained model on held-out test data.

        Computes MAE, RMSE, and MAPE metrics.

        Parameters
        ----------
        device_id : str
            Device identifier.
        test_data : pd.DataFrame
            Test DataFrame with the target column.
        target_column : str
            Column containing actual values.

        Returns
        -------
        dict[str, float]
            Evaluation metrics.
        """
        from derim.digital_twin.models.lstm_forecaster import LSTMForecaster

        forecaster = LSTMForecaster(settings=self.settings)
        actual = test_data[target_column].values

        # Use the first seq_length values as input.
        seq_len = self.settings.lstm_sequence_length
        if len(actual) <= seq_len:
            raise ValueError(
                f"Test data must have more than {seq_len} rows. Got {len(actual)}."
            )

        input_values = actual[:seq_len].tolist()
        horizon_steps = min(
            len(actual) - seq_len, self.settings.forecast_horizon_hours * 4
        )
        horizon_hours = max(1, horizon_steps // 4)

        predictions = forecaster.predict(
            device_id=device_id,
            horizon_hours=horizon_hours,
            recent_values=input_values,
        )

        pred_values = np.array([p.power_kw for p in predictions[:horizon_steps]])
        actual_values = actual[seq_len : seq_len + len(pred_values)]

        # Compute metrics.
        mae = float(np.mean(np.abs(actual_values - pred_values)))
        rmse = float(np.sqrt(np.mean((actual_values - pred_values) ** 2)))

        # MAPE (avoid division by zero).
        nonzero_mask = actual_values > 0.01
        if nonzero_mask.any():
            mape = float(
                np.mean(
                    np.abs(
                        (actual_values[nonzero_mask] - pred_values[nonzero_mask])
                        / actual_values[nonzero_mask]
                    )
                )
                * 100
            )
        else:
            mape = 0.0

        metrics = {
            "mae_kw": round(mae, 4),
            "rmse_kw": round(rmse, 4),
            "mape_pct": round(mape, 2),
        }

        logger.info(
            "model_evaluation_complete",
            device_id=device_id,
            **metrics,
        )
        return metrics
