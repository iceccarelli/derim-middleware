# DERIM Architecture Guide

This document provides a detailed technical overview of the DERIM middleware architecture, its components, data flows, and design decisions.

## Design Principles

DERIM is built around five core design principles that guide all architectural decisions.

**Protocol Agnosticism.** The middleware abstracts away protocol-specific details behind a common adapter interface. New protocols can be added without modifying the core data pipeline, storage layer, or API. This ensures that the system can integrate with any DER device regardless of its native communication protocol.

**Standards Alignment.** All internal data models are aligned with IEEE 2030.5 (Smart Energy Profile 2.0) and IEC 61968/61970 Common Information Model (CIM). This ensures interoperability with utility-grade systems and compliance with emerging smart grid standards.

**Separation of Concerns.** Each layer of the middleware has a well-defined responsibility and communicates with adjacent layers through clean interfaces. Protocol adapters handle device communication, the normalisation layer handles data transformation, the storage layer handles persistence, and the API layer handles external access.

**Extensibility.** The middleware is designed as a framework of interfaces. Adding a new protocol adapter, storage backend, or forecasting model requires implementing a well-defined abstract base class without modifying existing code.

**Operational Simplicity.** The system can run with zero external dependencies (SQLite storage, no broker) for development and testing, while supporting production-grade infrastructure (InfluxDB, MQTT broker, Docker orchestration) for deployment.

## Component Architecture

### Protocol Adapter Layer

The adapter layer is responsible for communicating with physical DER devices using their native protocols. Each adapter inherits from `BaseAdapter` and implements four core methods.

| Method | Purpose |
|--------|---------|
| `connect()` | Establish a connection to the device or broker |
| `disconnect()` | Gracefully close the connection |
| `read_data()` | Read current telemetry from the device |
| `write_command()` | Send a control command to the device |

The `read_data()` method returns a `DERTelemetry` object (or a device-specific subclass), ensuring that all downstream components work with a consistent data format regardless of the source protocol.

### Data Normalisation Layer

The normalisation layer is implemented through Pydantic models in `derim.models.common`. The base `DERTelemetry` model defines the minimum set of fields that every DER device must report. Device-specific extensions (`SolarTelemetry`, `BatteryTelemetry`, `EVChargerTelemetry`) add fields relevant to particular device types while maintaining backward compatibility with the base schema.

### Storage Layer

The storage layer provides an abstract `StorageBackend` interface with two implementations. The `InfluxDBStorage` backend is optimised for high-throughput time-series workloads in production environments. The `SQLiteStorage` backend provides a zero-dependency fallback for development, testing, and edge deployments. A factory function (`get_storage_backend`) selects the appropriate backend based on the application configuration.

### REST API Layer

The API layer is built with FastAPI and organised into three route modules. The `data` module handles device registration and telemetry queries. The `control` module handles command dispatch to devices. The `digital_twin` module exposes ML forecasting endpoints. All routes use dependency injection for storage access and settings, making them easily testable.

### Digital Twin Module

The digital twin module combines ML forecasting with real-time simulation. The `LSTMForecaster` uses a PyTorch LSTM network trained on historical telemetry to predict future power output. The `Simulator` class creates a virtual replica of a device by comparing predictions with actual measurements, detecting anomalies, and tracking model drift. The `Trainer` class provides an end-to-end pipeline for data loading, preprocessing, model training, and artefact persistence.

## Data Flow

```
Physical Device
     │
     ▼
Protocol Adapter (Modbus/MQTT/SunSpec/OCPP)
     │
     ▼
Data Normalisation (DERTelemetry Pydantic model)
     │
     ├──▶ Storage Backend (InfluxDB / SQLite)
     │
     ├──▶ REST API (FastAPI) ──▶ External Clients
     │
     └──▶ Digital Twin (LSTM Forecaster + Simulator)
              │
              ├──▶ Forecast API Endpoint
              └──▶ Anomaly Alerts
```

## Deployment Topologies

DERIM supports three deployment topologies depending on scale and requirements.

**Development Mode.** A single Python process with SQLite storage, suitable for local development and testing. No external services required. Start with `uvicorn derim.main:app --reload`.

**Single-Node Production.** Docker Compose stack with the DERIM API container, InfluxDB for time-series storage, and optional Grafana for monitoring. Suitable for single-site deployments managing up to hundreds of devices.

**Distributed Production.** Multiple DERIM API instances behind a load balancer, shared InfluxDB cluster, MQTT broker for event-driven adapter communication, and separate ML training infrastructure. Suitable for utility-scale deployments managing thousands of devices across multiple sites.

## Security Considerations

The current release focuses on core functionality. Production deployments should implement the following security measures.

| Concern | Recommendation |
|---------|---------------|
| API Authentication | Add OAuth 2.0 or API key middleware to FastAPI |
| Transport Encryption | Use TLS for all API and adapter connections |
| Storage Encryption | Enable InfluxDB TLS and at-rest encryption |
| Input Validation | Already implemented via Pydantic models |
| Rate Limiting | Add FastAPI middleware for API rate limiting |
| Network Segmentation | Isolate OT (adapter) and IT (API) networks |
