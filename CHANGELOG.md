# Changelog

All notable changes to the DERIM Middleware project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Planned

- DNP3 protocol adapter for utility-grade SCADA integration.
- IEC 61850 (MMS/GOOSE) adapter for substation automation.
- OpenADR 2.0b adapter for demand response programmes.
- Grafana dashboard templates for real-time DER monitoring.
- Multi-device fleet optimisation in the digital twin module.
- WebSocket streaming API for real-time telemetry push.

## [0.1.0] - 2026-03-04

### Added

- **Protocol Adapters**: Modbus TCP/RTU, MQTT, SunSpec, and OCPP 1.6 adapters with a common `BaseAdapter` interface.
- **Data Models**: Pydantic models for DER telemetry (`DERTelemetry`, `SolarTelemetry`, `BatteryTelemetry`, `EVChargerTelemetry`), device registration (`DERDevice`), control commands, and forecast responses. Aligned with IEEE 2030.5 and CIM standards.
- **Storage Backends**: InfluxDB client for production time-series storage and SQLite fallback for development and testing. Abstract `StorageBackend` interface with factory function.
- **REST API**: FastAPI-based API with endpoints for device management, telemetry ingestion and query, control command dispatch, and ML forecasting. Automatic OpenAPI documentation at `/docs`.
- **Digital Twin Module**: LSTM-based power forecaster using PyTorch, persistence and moving-average baseline models, simulation engine with anomaly detection and drift monitoring, and a training pipeline with CSV data loading.
- **Jupyter Notebooks**: Four demonstration notebooks covering data exploration, protocol adapter usage, digital twin model training, and API client interaction.
- **Sample Data**: Realistic synthetic solar PV telemetry dataset (30 days, 15-minute intervals).
- **Docker Support**: Multi-stage Dockerfile, Docker Compose stack with InfluxDB, optional Grafana and Mosquitto services.
- **CI/CD**: GitHub Actions workflow with linting, multi-version testing, Docker build, and security scanning.
- **Testing**: Comprehensive pytest suite with 79 tests covering models, storage, API, adapters, and digital twin modules.
- **Documentation**: README with architecture diagram, quick start guide, API reference, and contribution guidelines.
- **Configuration**: Pydantic Settings with environment variable support, `.env.example` template.
- **Code Quality**: Pre-commit hooks for Black, isort, and Flake8. Structured logging with structlog.
