"""
LSTM-based time-series forecaster for DER power prediction.

This module implements a multi-layer LSTM neural network using PyTorch
for forecasting solar generation, battery output, or load profiles.
The model ingests a sequence of historical telemetry values and outputs
a sequence of predicted future values.

Architecture
------------
::

    Input (seq_len, n_features)
        |
    LSTM (hidden_size, num_layers, dropout)
        |
    Linear (hidden_size -> forecast_horizon)
        |
    Output (forecast_horizon,)

The model is trained on sliding-window sequences extracted from
historical time-series data.  Feature scaling (min-max or standard)
is applied before training and persisted alongside the model weights.

Usage
-----
::

    from derim.digital_twin.models.lstm_forecaster import LSTMForecaster

    forecaster = LSTMForecaster(settings=settings)
    forecaster.train(device_id="solar-001", data=historical_df)
    predictions = forecaster.predict(device_id="solar-001", horizon_hours=24)
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Optional

import joblib
import numpy as np

from derim.config import Settings, get_settings
from derim.models.common import ForecastPoint
from derim.utils.logger import get_logger

logger = get_logger(__name__)


class SolarLSTM:
    """
    PyTorch LSTM model definition (lazy import to avoid hard dependency).

    This inner class is only instantiated when PyTorch is available.
    """

    def __init__(
        self,
        input_size: int = 1,
        hidden_size: int = 64,
        num_layers: int = 2,
        output_size: int = 96,
        dropout: float = 0.2,
    ):
        import torch  # noqa: F401
        import torch.nn as nn

        self.model = nn.Sequential()

        class _LSTMModel(nn.Module):
            def __init__(
                self,
                input_size: int,
                hidden_size: int,
                num_layers: int,
                output_size: int,
                dropout: float,
            ):
                super().__init__()
                self.hidden_size = hidden_size
                self.num_layers = num_layers
                self.lstm = nn.LSTM(
                    input_size=input_size,
                    hidden_size=hidden_size,
                    num_layers=num_layers,
                    batch_first=True,
                    dropout=dropout if num_layers > 1 else 0.0,
                )
                self.fc = nn.Sequential(
                    nn.Linear(hidden_size, hidden_size // 2),
                    nn.ReLU(),
                    nn.Dropout(dropout),
                    nn.Linear(hidden_size // 2, output_size),
                )

            def forward(self, x: Any) -> Any:
                # x shape: (batch, seq_len, input_size)
                lstm_out, _ = self.lstm(x)
                # Use the last time step's output.
                last_output = lstm_out[:, -1, :]
                return self.fc(last_output)

        self.model = _LSTMModel(
            input_size, hidden_size, num_layers, output_size, dropout
        )
        self.input_size = input_size
        self.hidden_size = hidden_size
        self.num_layers = num_layers
        self.output_size = output_size


class LSTMForecaster:
    """
    High-level LSTM forecaster for DER power prediction.

    This class wraps model creation, training, saving/loading, and
    inference behind a simple API.

    Parameters
    ----------
    settings : Settings, optional
        Application settings.  If not provided, the global settings
        singleton is used.
    """

    def __init__(self, settings: Optional[Settings] = None):
        self.settings = settings or get_settings()
        self.model_dir = Path(self.settings.model_save_dir)
        self.model_dir.mkdir(parents=True, exist_ok=True)
        self.seq_length = self.settings.lstm_sequence_length
        self.forecast_steps = self.settings.forecast_horizon_hours * 4  # 15-min
        self._models: dict[str, Any] = {}
        self._scalers: dict[str, Any] = {}

    def _model_path(self, device_id: str) -> Path:
        """Return the file path for a device's saved model."""
        return self.model_dir / f"{device_id}_lstm.pt"

    def _scaler_path(self, device_id: str) -> Path:
        """Return the file path for a device's saved scaler."""
        return self.model_dir / f"{device_id}_scaler.pkl"

    def is_model_available(self, device_id: str) -> bool:
        """Check whether a trained model exists for the given device."""
        return self._model_path(device_id).exists()

    def train(
        self,
        device_id: str,
        data: Any,
        target_column: str = "power_kw",
        epochs: Optional[int] = None,
        batch_size: Optional[int] = None,
        learning_rate: float = 0.001,
        validation_split: float = 0.2,
    ) -> dict[str, Any]:
        """
        Train an LSTM model on historical time-series data.

        Parameters
        ----------
        device_id : str
            Device identifier (used for model persistence).
        data : pandas.DataFrame
            Historical data with at least a ``target_column``.
        target_column : str
            Column name containing the target variable.
        epochs : int, optional
            Training epochs (defaults to settings value).
        batch_size : int, optional
            Mini-batch size (defaults to settings value).
        learning_rate : float
            Adam optimiser learning rate.
        validation_split : float
            Fraction of data reserved for validation.

        Returns
        -------
        dict[str, Any]
            Training metrics (train_loss, val_loss, epochs).
        """
        import torch
        import torch.nn as nn
        from sklearn.preprocessing import MinMaxScaler
        from torch.utils.data import DataLoader, TensorDataset

        epochs = epochs or self.settings.lstm_epochs
        batch_size = batch_size or self.settings.lstm_batch_size

        # Extract and scale target values.
        values = data[target_column].values.astype(np.float32).reshape(-1, 1)
        scaler = MinMaxScaler(feature_range=(0, 1))
        scaled = scaler.fit_transform(values)

        # Create sliding-window sequences.
        X, y = [], []
        for i in range(len(scaled) - self.seq_length - self.forecast_steps + 1):
            X.append(scaled[i : i + self.seq_length])
            y.append(
                scaled[
                    i + self.seq_length : i + self.seq_length + self.forecast_steps, 0
                ]
            )

        X_arr = np.array(X, dtype=np.float32)
        y_arr = np.array(y, dtype=np.float32)

        # Train / validation split.
        split_idx = int(len(X_arr) * (1 - validation_split))
        X_train, X_val = X_arr[:split_idx], X_arr[split_idx:]
        y_train, y_val = y_arr[:split_idx], y_arr[split_idx:]

        train_ds = TensorDataset(torch.from_numpy(X_train), torch.from_numpy(y_train))
        val_ds = TensorDataset(torch.from_numpy(X_val), torch.from_numpy(y_val))
        train_loader = DataLoader(train_ds, batch_size=batch_size, shuffle=True)
        val_loader = DataLoader(val_ds, batch_size=batch_size)

        # Build model.
        device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        lstm = SolarLSTM(
            input_size=1,
            hidden_size=64,
            num_layers=2,
            output_size=self.forecast_steps,
            dropout=0.2,
        )
        model = lstm.model.to(device)
        criterion = nn.MSELoss()
        optimiser = torch.optim.Adam(model.parameters(), lr=learning_rate)
        scheduler = torch.optim.lr_scheduler.ReduceLROnPlateau(
            optimiser, mode="min", factor=0.5, patience=5
        )

        # Training loop.
        best_val_loss = float("inf")
        history: dict[str, list[float]] = {"train_loss": [], "val_loss": []}

        for epoch in range(epochs):
            model.train()
            train_losses = []
            for X_batch, y_batch in train_loader:
                X_batch, y_batch = X_batch.to(device), y_batch.to(device)
                optimiser.zero_grad()
                output = model(X_batch)
                loss = criterion(output, y_batch)
                loss.backward()
                torch.nn.utils.clip_grad_norm_(model.parameters(), max_norm=1.0)
                optimiser.step()
                train_losses.append(loss.item())

            # Validation.
            model.eval()
            val_losses = []
            with torch.no_grad():
                for X_batch, y_batch in val_loader:
                    X_batch, y_batch = X_batch.to(device), y_batch.to(device)
                    output = model(X_batch)
                    loss = criterion(output, y_batch)
                    val_losses.append(loss.item())

            avg_train = float(np.mean(train_losses))
            avg_val = float(np.mean(val_losses)) if val_losses else avg_train
            history["train_loss"].append(avg_train)
            history["val_loss"].append(avg_val)

            scheduler.step(avg_val)

            if avg_val < best_val_loss:
                best_val_loss = avg_val
                torch.save(model.state_dict(), self._model_path(device_id))

            if (epoch + 1) % 10 == 0:
                logger.info(
                    "lstm_training_progress",
                    device_id=device_id,
                    epoch=epoch + 1,
                    train_loss=round(avg_train, 6),
                    val_loss=round(avg_val, 6),
                )

        # Save scaler.
        joblib.dump(scaler, self._scaler_path(device_id))

        logger.info(
            "lstm_training_complete",
            device_id=device_id,
            epochs=epochs,
            best_val_loss=round(best_val_loss, 6),
        )

        return {
            "device_id": device_id,
            "epochs": epochs,
            "best_val_loss": best_val_loss,
            "history": history,
        }

    def predict(
        self,
        device_id: str,
        horizon_hours: int = 24,
        recent_values: Optional[list[float]] = None,
    ) -> list[ForecastPoint]:
        """
        Generate a forecast using the trained LSTM model.

        Parameters
        ----------
        device_id : str
            Device identifier.
        horizon_hours : int
            Forecast horizon in hours.
        recent_values : list[float], optional
            Recent power values to use as input.  If not provided,
            zeros are used (the model will still produce output but
            accuracy will be lower).

        Returns
        -------
        list[ForecastPoint]
            Predicted power values at 15-minute intervals.
        """
        import torch

        model_path = self._model_path(device_id)
        scaler_path = self._scaler_path(device_id)

        if not model_path.exists() or not scaler_path.exists():
            raise FileNotFoundError(
                f"No trained model found for device '{device_id}'. "
                "Train a model first using the Trainer."
            )

        # Load model and scaler.
        device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        forecast_steps = horizon_hours * 4

        lstm = SolarLSTM(
            input_size=1,
            hidden_size=64,
            num_layers=2,
            output_size=forecast_steps,
            dropout=0.0,
        )
        model = lstm.model
        model.load_state_dict(
            torch.load(model_path, map_location=device, weights_only=True)
        )
        model.to(device)
        model.eval()

        scaler = joblib.load(scaler_path)

        # Prepare input sequence.
        if recent_values is None:
            recent_values = [0.0] * self.seq_length

        # Pad or truncate to seq_length.
        if len(recent_values) < self.seq_length:
            recent_values = [0.0] * (
                self.seq_length - len(recent_values)
            ) + recent_values
        else:
            recent_values = recent_values[-self.seq_length :]

        input_arr = np.array(recent_values, dtype=np.float32).reshape(-1, 1)
        input_scaled = scaler.transform(input_arr)
        input_tensor = torch.from_numpy(input_scaled.reshape(1, self.seq_length, 1)).to(
            device
        )

        # Inference.
        with torch.no_grad():
            output = model(input_tensor).cpu().numpy().flatten()

        # Inverse-scale predictions.
        predictions_scaled = output.reshape(-1, 1)
        predictions_raw = scaler.inverse_transform(predictions_scaled).flatten()

        # Build forecast points.
        now = datetime.now(timezone.utc)
        forecast_points: list[ForecastPoint] = []
        for i, value in enumerate(predictions_raw):
            power = max(0.0, float(value))  # Clamp negative values.
            forecast_points.append(
                ForecastPoint(
                    timestamp=now + timedelta(minutes=15 * i),
                    power_kw=round(power, 3),
                    confidence_lower=round(power * 0.85, 3),
                    confidence_upper=round(power * 1.15, 3),
                )
            )

        logger.info(
            "lstm_forecast_generated",
            device_id=device_id,
            horizon_hours=horizon_hours,
            points=len(forecast_points),
        )
        return forecast_points
