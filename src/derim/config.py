"""
Application configuration using Pydantic Settings.

All configuration values are loaded from environment variables or a .env file.
This module provides a centralized, validated configuration object used
throughout the DERIM middleware.
"""

from enum import Enum
from functools import lru_cache
from typing import Optional

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class StorageBackendType(str, Enum):
    """Supported storage backend types."""

    INFLUXDB = "influxdb"
    SQLITE = "sqlite"


class ModbusProtocol(str, Enum):
    """Supported Modbus protocol variants."""

    TCP = "tcp"
    RTU = "rtu"


class Settings(BaseSettings):
    """
    Central configuration for the DERIM middleware.

    Values are loaded from environment variables. A .env file in the project
    root is also supported for local development.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # --- Application ---
    app_name: str = Field(default="derim-middleware", description="Application name")
    app_env: str = Field(default="development", description="Runtime environment")
    app_debug: bool = Field(default=False, description="Enable debug mode")
    app_host: str = Field(default="0.0.0.0", description="API server bind address")
    app_port: int = Field(default=8000, description="API server port")
    log_level: str = Field(default="INFO", description="Logging level")

    # --- Storage ---
    storage_backend: StorageBackendType = Field(
        default=StorageBackendType.SQLITE,
        description="Active storage backend (influxdb or sqlite)",
    )

    # --- InfluxDB ---
    influxdb_url: str = Field(
        default="http://localhost:8086", description="InfluxDB server URL"
    )
    influxdb_token: str = Field(
        default="my-super-secret-token", description="InfluxDB authentication token"
    )
    influxdb_org: str = Field(default="derim", description="InfluxDB organization")
    influxdb_bucket: str = Field(
        default="derim_telemetry", description="InfluxDB bucket name"
    )

    # --- SQLite ---
    sqlite_db_path: str = Field(
        default="./data/derim.db", description="SQLite database file path"
    )

    # --- Modbus ---
    modbus_host: str = Field(
        default="127.0.0.1", description="Modbus device host address"
    )
    modbus_port: int = Field(default=502, description="Modbus TCP port")
    modbus_unit_id: int = Field(default=1, description="Modbus unit/slave ID")
    modbus_protocol: ModbusProtocol = Field(
        default=ModbusProtocol.TCP, description="Modbus protocol variant"
    )

    # --- MQTT ---
    mqtt_broker: str = Field(default="localhost", description="MQTT broker hostname")
    mqtt_port: int = Field(default=1883, description="MQTT broker port")
    mqtt_username: Optional[str] = Field(
        default=None, description="MQTT authentication username"
    )
    mqtt_password: Optional[str] = Field(
        default=None, description="MQTT authentication password"
    )
    mqtt_topic_prefix: str = Field(
        default="derim/devices", description="MQTT topic prefix for DER data"
    )

    # --- SunSpec ---
    sunspec_host: str = Field(
        default="127.0.0.1", description="SunSpec device host address"
    )
    sunspec_port: int = Field(default=502, description="SunSpec Modbus port")
    sunspec_slave_id: int = Field(default=1, description="SunSpec Modbus slave ID")

    # --- OCPP ---
    ocpp_ws_url: str = Field(
        default="ws://localhost:9000",
        description="OCPP WebSocket server URL",
    )
    ocpp_charge_point_id: str = Field(
        default="CP001", description="OCPP charge point identifier"
    )

    # --- Digital Twin / ML ---
    model_save_dir: str = Field(
        default="./saved_models",
        description="Directory for persisting trained ML models",
    )
    forecast_horizon_hours: int = Field(
        default=24, description="Forecast horizon in hours"
    )
    lstm_epochs: int = Field(default=50, description="LSTM training epochs")
    lstm_batch_size: int = Field(default=32, description="LSTM training batch size")
    lstm_sequence_length: int = Field(
        default=96,
        description="Number of time steps in each LSTM input sequence",
    )


@lru_cache()
def get_settings() -> Settings:
    """
    Return a cached singleton of the application settings.

    Using ``lru_cache`` ensures the .env file is read only once and the same
    ``Settings`` instance is reused across the application lifetime.
    """
    return Settings()
