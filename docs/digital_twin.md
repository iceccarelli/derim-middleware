# Digital Twin Module Guide

This guide explains the DERIM digital twin module, including the ML forecasting models, the simulation engine, and the training pipeline.

## Overview

The digital twin module creates virtual replicas of physical DER devices by combining trained machine learning models with real-time telemetry data. It serves three primary functions: forecasting future power output, detecting anomalies by comparing predictions with actual measurements, and evaluating hypothetical scenarios through simulation.

## Forecasting Models

### LSTM Forecaster

The primary forecasting model is a Long Short-Term Memory (LSTM) neural network implemented in PyTorch. LSTM networks are well-suited for time-series forecasting because they can capture long-range temporal dependencies in sequential data, such as daily and seasonal patterns in solar generation.

**Architecture.** The model consists of a configurable number of LSTM layers followed by a fully connected output layer. The input is a sequence of historical power values, and the output is a sequence of predicted future values.

**Training.** The model is trained on historical telemetry data using the `Trainer` class. Training data is split into input sequences (lookback window) and target sequences (forecast horizon). The model minimises Mean Squared Error (MSE) loss using the Adam optimiser.

```python
from derim.digital_twin.trainer import Trainer

trainer = Trainer()
metrics = trainer.train_from_csv(
    device_id="solar-inv-001",
    csv_path="data/sample_solar_data.csv",
    target_column="power_kw",
    epochs=50,
    batch_size=32,
)
print(f"Best validation loss: {metrics['best_val_loss']:.4f}")
```

**Prediction.** Once trained, the model generates forecasts with confidence intervals.

```python
from derim.digital_twin.models.lstm_forecaster import LSTMForecaster

forecaster = LSTMForecaster()
predictions = forecaster.predict(
    device_id="solar-inv-001",
    horizon_hours=24,
    recent_values=[3.2, 3.5, 3.8, 4.0, ...],  # Last 96 values
)

for point in predictions[:5]:
    print(f"{point.timestamp}: {point.power_kw:.2f} kW "
          f"[{point.confidence_lower:.2f}, {point.confidence_upper:.2f}]")
```

### Baseline Models

Two baseline models are provided for benchmarking the LSTM forecaster.

**Persistence Forecaster.** Assumes that future values will repeat the most recent observed pattern. For solar forecasting, this effectively predicts that tomorrow's generation will match today's. This is a strong baseline for short-horizon forecasts.

**Moving Average Forecaster.** Uses the rolling mean of recent observations as a flat forecast over the entire horizon. The window size is configurable (default: 96 points = 24 hours at 15-minute intervals).

```python
from derim.digital_twin.models.baseline import (
    PersistenceForecaster,
    MovingAverageForecaster,
)

persistence = PersistenceForecaster()
ma = MovingAverageForecaster(window_size=96)

history = [3.2, 3.5, 3.8, 4.0, ...]

p_forecast = persistence.predict(history, horizon_hours=24)
ma_forecast = ma.predict(history, horizon_hours=24)
```

## Simulation Engine

The `Simulator` class creates a digital twin of a specific device by combining a trained model with real-time telemetry.

### Comparison and Anomaly Detection

The `compare()` method overlays model predictions on actual measurements to compute residuals, error metrics, and anomaly flags.

```python
from derim.digital_twin.simulator import Simulator

sim = Simulator(device_id="solar-inv-001", anomaly_sigma=3.0)

result = sim.compare(
    actual_values=[3.2, 3.5, 3.8, 4.0, 3.9],
    predicted_values=[3.1, 3.4, 3.7, 4.1, 3.8],
)

print(f"MAE: {result.mae:.4f} kW")
print(f"RMSE: {result.rmse:.4f} kW")
print(f"Anomalies: {result.anomaly_indices}")
```

Anomaly detection uses a configurable sigma threshold. Data points where the absolute residual exceeds `sigma * std(residuals)` are flagged as anomalous. The default threshold is 3 standard deviations.

### Model Drift Detection

The `get_drift_indicator()` method tracks model accuracy over time by comparing the most recent MAE to the historical average. A drift indicator significantly above 1.0 suggests that the model is degrading and should be retrained.

```python
drift = sim.get_drift_indicator()
if drift > 1.5:
    print("Model drift detected — consider retraining.")
```

### Scenario Simulation

The `run_scenario()` method runs the trained model with modified inputs to evaluate hypothetical outcomes, such as the impact of different irradiance profiles on solar generation.

```python
sim.load_model()
scenario_forecast = sim.run_scenario(
    input_values=[5.0, 5.2, 5.5, 5.8, ...],  # Modified irradiance
    horizon_hours=24,
)
```

## Training Pipeline

The `Trainer` class provides an end-to-end pipeline for preparing data and training models.

### Data Loading

```python
trainer = Trainer()
df = trainer.load_csv("data/sample_solar_data.csv")
```

### Preprocessing

The preprocessing step handles missing values (forward-fill or interpolation), clips negative power values to zero (common in solar data), and drops remaining NaN rows.

```python
df = trainer.preprocess(df, target_column="power_kw", fill_method="ffill")
```

### Model Evaluation

```python
metrics = trainer.evaluate(
    device_id="solar-inv-001",
    test_data=test_df,
    target_column="power_kw",
)
print(f"MAE: {metrics['mae_kw']:.4f} kW")
print(f"RMSE: {metrics['rmse_kw']:.4f} kW")
print(f"MAPE: {metrics['mape_pct']:.2f}%")
```

## Configuration

The digital twin module is configured through the application settings.

| Setting | Default | Description |
|---------|---------|-------------|
| `LSTM_EPOCHS` | 50 | Number of training epochs |
| `LSTM_BATCH_SIZE` | 32 | Training batch size |
| `LSTM_SEQUENCE_LENGTH` | 96 | Input sequence length (96 = 24h at 15-min) |
| `FORECAST_HORIZON_HOURS` | 24 | Default forecast horizon |
| `MODEL_SAVE_DIR` | `./saved_models` | Directory for persisted model artefacts |
