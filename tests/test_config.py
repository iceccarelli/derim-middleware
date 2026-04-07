"""
Unit tests for the DERIM configuration module.

Tests cover:
- Default settings values.
- Custom settings values.
- ML-related settings.
"""

from derim.config import Settings, StorageBackendType


class TestSettings:
    """Tests for the Settings configuration model."""

    def test_default_values(self):
        """Settings should have sensible defaults."""
        settings = Settings()
        assert settings.app_name == "derim-middleware"
        assert settings.storage_backend == StorageBackendType.SQLITE
        assert settings.app_host == "127.0.0.1"
        assert settings.app_port == 8000
        assert settings.log_level == "INFO"

    def test_custom_values(self):
        """Settings should accept custom values."""
        settings = Settings(
            app_port=9000,
            log_level="DEBUG",
            storage_backend=StorageBackendType.INFLUXDB,
        )
        assert settings.app_port == 9000
        assert settings.log_level == "DEBUG"
        assert settings.storage_backend == StorageBackendType.INFLUXDB

    def test_ml_settings(self):
        """ML-related settings should have defaults."""
        settings = Settings()
        assert settings.lstm_epochs > 0
        assert settings.lstm_batch_size > 0
        assert settings.lstm_sequence_length > 0
        assert settings.forecast_horizon_hours > 0

    def test_model_save_dir(self, tmp_path):
        """Model save directory should be configurable."""
        settings = Settings(model_save_dir=str(tmp_path / "models"))
        assert "models" in settings.model_save_dir
