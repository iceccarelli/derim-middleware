"""
Digital Twin module for ML-based forecasting and simulation.

This package provides:

- **LSTMForecaster**: A PyTorch LSTM model for solar generation and
  load forecasting.
- **BaselineForecaster**: Simple persistence and moving-average baselines.
- **Trainer**: A training pipeline that loads historical data, trains
  models, and persists them to disk.
- **Simulator**: A digital twin simulation engine that compares model
  predictions with real-time telemetry.
"""
