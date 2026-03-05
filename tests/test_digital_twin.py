"""
Unit tests for the DERIM digital twin module.

Tests cover:
- Baseline forecasters (Persistence, Moving Average).
- Simulator comparison and anomaly detection.
- Trainer data loading and preprocessing.
"""

import numpy as np
import pytest

from derim.digital_twin.models.baseline import (
    MovingAverageForecaster,
    PersistenceForecaster,
)
from derim.digital_twin.simulator import SimulationResult, Simulator


class TestPersistenceForecaster:
    """Tests for the persistence baseline model."""

    def test_predict_with_history(self):
        """Predictions should repeat the input pattern."""
        forecaster = PersistenceForecaster(interval_minutes=15)
        history = [1.0, 2.0, 3.0, 4.0]

        predictions = forecaster.predict(history, horizon_hours=1)

        assert len(predictions) == 4  # 1 hour at 15-min intervals
        assert predictions[0].power_kw == 1.0
        assert predictions[1].power_kw == 2.0
        assert predictions[2].power_kw == 3.0
        assert predictions[3].power_kw == 4.0

    def test_predict_wraps_around(self):
        """Predictions should wrap around when horizon > history length."""
        forecaster = PersistenceForecaster(interval_minutes=15)
        history = [1.0, 2.0]

        predictions = forecaster.predict(history, horizon_hours=1)

        assert len(predictions) == 4
        assert predictions[0].power_kw == 1.0
        assert predictions[1].power_kw == 2.0
        assert predictions[2].power_kw == 1.0  # Wraps
        assert predictions[3].power_kw == 2.0  # Wraps

    def test_predict_empty_history(self):
        """Empty history should produce zero predictions."""
        forecaster = PersistenceForecaster()
        predictions = forecaster.predict([], horizon_hours=1)

        assert len(predictions) == 4
        assert all(p.power_kw == 0.0 for p in predictions)

    def test_confidence_intervals(self):
        """Predictions should include confidence bounds."""
        forecaster = PersistenceForecaster()
        predictions = forecaster.predict([5.0], horizon_hours=1)

        for p in predictions:
            assert p.confidence_lower is not None
            assert p.confidence_upper is not None
            assert p.confidence_lower <= p.power_kw
            assert p.confidence_upper >= p.power_kw


class TestMovingAverageForecaster:
    """Tests for the moving average baseline model."""

    def test_predict_flat_line(self):
        """Moving average should produce a flat forecast."""
        forecaster = MovingAverageForecaster(window_size=4, interval_minutes=15)
        history = [2.0, 4.0, 6.0, 8.0]

        predictions = forecaster.predict(history, horizon_hours=1)

        assert len(predictions) == 4
        expected_avg = 5.0  # mean of [2, 4, 6, 8]
        for p in predictions:
            assert p.power_kw == pytest.approx(expected_avg, abs=0.01)

    def test_window_size_respected(self):
        """Only the last window_size values should be averaged."""
        forecaster = MovingAverageForecaster(window_size=2)
        history = [1.0, 2.0, 10.0, 20.0]

        predictions = forecaster.predict(history, horizon_hours=1)

        expected_avg = 15.0  # mean of [10, 20]
        assert predictions[0].power_kw == pytest.approx(expected_avg, abs=0.01)

    def test_empty_history(self):
        """Empty history should produce zero average."""
        forecaster = MovingAverageForecaster()
        predictions = forecaster.predict([], horizon_hours=1)

        assert all(p.power_kw == 0.0 for p in predictions)

    def test_confidence_intervals_with_std(self):
        """Confidence intervals should reflect data variability."""
        forecaster = MovingAverageForecaster(window_size=4)
        history = [1.0, 5.0, 1.0, 5.0]  # High variance

        predictions = forecaster.predict(history, horizon_hours=1)

        for p in predictions:
            assert p.confidence_lower < p.power_kw
            assert p.confidence_upper > p.power_kw


class TestSimulator:
    """Tests for the digital twin simulator."""

    def test_compare_identical(self):
        """Comparing identical values should yield zero error."""
        sim = Simulator(device_id="test-001")
        actual = [1.0, 2.0, 3.0, 4.0, 5.0]
        predicted = [1.0, 2.0, 3.0, 4.0, 5.0]

        result = sim.compare(actual, predicted)

        assert result.mae == 0.0
        assert result.rmse == 0.0
        assert len(result.anomaly_indices) == 0

    def test_compare_with_errors(self):
        """Comparison should compute correct MAE and RMSE."""
        sim = Simulator(device_id="test-002")
        actual = [1.0, 2.0, 3.0, 4.0, 5.0]
        predicted = [1.5, 2.5, 3.5, 4.5, 5.5]

        result = sim.compare(actual, predicted)

        assert result.mae == pytest.approx(0.5, abs=0.01)
        assert result.rmse == pytest.approx(0.5, abs=0.01)

    def test_anomaly_detection(self):
        """Points with large residuals should be flagged as anomalies."""
        sim = Simulator(device_id="test-003", anomaly_sigma=2.0)
        actual = [1.0, 1.0, 1.0, 1.0, 10.0]  # Last point is anomalous
        predicted = [1.0, 1.0, 1.0, 1.0, 1.0]

        result = sim.compare(actual, predicted)

        assert len(result.anomaly_indices) > 0
        assert 4 in result.anomaly_indices

    def test_different_length_arrays(self):
        """Comparison should handle arrays of different lengths."""
        sim = Simulator(device_id="test-004")
        actual = [1.0, 2.0, 3.0]
        predicted = [1.0, 2.0, 3.0, 4.0, 5.0]

        result = sim.compare(actual, predicted)

        assert len(result.residuals) == 3  # Truncated to shorter

    def test_history_tracking(self):
        """Simulator should track comparison history."""
        sim = Simulator(device_id="test-005")
        sim.compare([1.0, 2.0], [1.0, 2.0])
        sim.compare([3.0, 4.0], [3.0, 4.0])

        history = sim.get_history()
        assert len(history) == 2

    def test_drift_indicator_no_drift(self):
        """Drift indicator should be ~1.0 when errors are consistent."""
        sim = Simulator(device_id="test-006")
        for _ in range(5):
            sim.compare([1.0, 2.0, 3.0], [1.1, 2.1, 3.1])

        drift = sim.get_drift_indicator()
        assert drift == pytest.approx(1.0, abs=0.1)

    def test_simulation_result_dataclass(self):
        """SimulationResult should be properly structured."""
        result = SimulationResult(
            device_id="test-007",
            actual_values=[1.0, 2.0],
            predicted_values=[1.5, 2.5],
            residuals=[-0.5, -0.5],
            mae=0.5,
            rmse=0.5,
        )
        assert result.device_id == "test-007"
        assert result.timestamp is not None


class TestTrainerPreprocessing:
    """Tests for the Trainer data preprocessing."""

    def test_load_csv(self, tmp_path):
        """Trainer should load CSV files correctly."""
        import pandas as pd

        from derim.digital_twin.trainer import Trainer

        # Create a test CSV.
        csv_path = tmp_path / "test_data.csv"
        df = pd.DataFrame(
            {
                "timestamp": pd.date_range("2025-01-01", periods=100, freq="15min"),
                "power_kw": np.random.uniform(0, 5, 100),
            }
        )
        df.to_csv(csv_path, index=False)

        trainer = Trainer()
        loaded = trainer.load_csv(csv_path)
        assert len(loaded) == 100
        assert "power_kw" in loaded.columns

    def test_preprocess_fills_missing(self, tmp_path):
        """Preprocessing should fill missing values."""
        import pandas as pd

        from derim.digital_twin.trainer import Trainer

        df = pd.DataFrame(
            {
                "timestamp": pd.date_range("2025-01-01", periods=10, freq="15min"),
                "power_kw": [1.0, None, 3.0, None, 5.0, 6.0, None, 8.0, 9.0, 10.0],
            }
        )

        trainer = Trainer()
        processed = trainer.preprocess(df, target_column="power_kw")

        assert processed["power_kw"].isnull().sum() == 0
        assert len(processed) == 10

    def test_preprocess_clips_negative(self, tmp_path):
        """Preprocessing should clip negative power values to zero."""
        import pandas as pd

        from derim.digital_twin.trainer import Trainer

        df = pd.DataFrame(
            {
                "timestamp": pd.date_range("2025-01-01", periods=5, freq="15min"),
                "power_kw": [-1.0, 2.0, -3.0, 4.0, 5.0],
            }
        )

        trainer = Trainer()
        processed = trainer.preprocess(df, target_column="power_kw")

        assert processed["power_kw"].min() >= 0.0

    def test_preprocess_missing_column_raises(self):
        """Preprocessing should raise ValueError for missing target column."""
        import pandas as pd

        from derim.digital_twin.trainer import Trainer

        df = pd.DataFrame({"timestamp": [1, 2, 3], "voltage": [230, 231, 229]})

        trainer = Trainer()
        with pytest.raises(ValueError, match="Target column"):
            trainer.preprocess(df, target_column="power_kw")
