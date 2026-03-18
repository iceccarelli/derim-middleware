```markdown
# DERIM Middleware

**Distributed Energy Resource Integration Middleware**

[![CI](https://github.com/iceccarelli/DERIM-Middleware-project/actions/workflows/ci.yml/badge.svg)](https://github.com/iceccarelli/DERIM-Middleware-project/actions/workflows/ci.yml)
[![Python 3.11+](https://img.shields.io/badge/python-3.11%2B-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![Docker](https://img.shields.io/badge/docker-2496ED?style=flat&logo=docker&logoColor=white)](https://www.docker.com)
[![FastAPI](https://img.shields.io/badge/FastAPI-009688?style=flat&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)

---

## Table of Contents

- [Motivation](#motivation)
- [Overview](#overview)
- [Who Should Use DERIM](#who-should-use-derim)
- [Key Features](#key-features)
- [Standards Compliance and Interoperability](#standards-compliance-and-interoperability)
- [Architecture](#architecture)
- [Quick Start](#quick-start)
- [Project Structure](#project-structure)
- [API Reference](#api-reference)
- [Data Models](#data-models)
- [Protocol Adapters](#protocol-adapters)
- [Digital Twin Module](#digital-twin-module)
- [Configuration](#configuration)
- [Jupyter Notebooks](#jupyter-notebooks)
- [Real-World Applications](#real-world-applications)
- [Roadmap](#roadmap)
- [Contributing](#contributing)
- [License](#license)
- [Acknowledgements](#acknowledgements)

---

## Motivation

The integration of distributed energy resources (DERs) — rooftop solar, battery storage, electric vehicle chargers, and microgrids — continues to reshape power systems worldwide. Grid operators and developers often encounter fragmented protocols, vendor-specific interfaces, and the need for consistent data handling across diverse hardware.

DERIM is an open-source middleware layer intended to simplify this integration. It translates between industrial protocols and a unified, standards-aligned data model, providing a stable foundation for monitoring, control, and analysis. The project is developed with a focus on modularity, reliability, and adherence to established standards, so that engineers, researchers, and organisations can build upon it without starting from scratch.

> "The clean energy transition will not be won by hardware alone. It will be won by the software that makes millions of distributed assets work together as one."

---

## Overview

DERIM is a modular middleware platform that connects heterogeneous distributed energy resources to modern smart-grid applications. It ingests real-time data via standard industrial protocols, normalises it into vendor-neutral models aligned with IEEE 2030.5 and IEC 61968/61970 CIM, persists time-series telemetry, exposes a documented REST API, and includes a lightweight digital-twin component for forecasting and basic anomaly detection.

The platform is built for **grid operators**, **DER manufacturers**, **energy researchers**, and **smart-grid developers** who require a clean, extensible integration layer.

### Who Should Use DERIM

| Audience                        | Typical Use Case                                      |
|---------------------------------|-------------------------------------------------------|
| **Grid Operators and Utilities** | Unified visibility, monitoring, demand-response dispatch |
| **DER Manufacturers**           | Compliance testing, protocol validation, interoperability checks |
| **Energy Researchers**          | Time-series analysis, model benchmarking, simulation studies |
| **Smart Grid Developers**       | Building dashboards, VPP platforms, or DERMS applications |
| **Standards Bodies & Regulators**| Reference implementation for IEEE 2030.5, CIM, and OCPP |
| **Universities and Students**   | Practical learning in smart grids, IoT, and energy ML |

---

## Key Features

| Feature                    | Description |
|----------------------------|-------------|
| **Multi-Protocol Adapters** | Modbus TCP/RTU, MQTT, SunSpec, OCPP 1.6/2.0.1 with pluggable design |
| **Standards-Aligned Data Model** | Pydantic models following IEEE 2030.5 and IEC 61968/61970 CIM |
| **Time-Series Storage**    | InfluxDB for production; SQLite fallback for development |
| **REST API**               | FastAPI with OpenAPI/Swagger documentation and full CRUD operations |
| **Digital Twin Engine**    | LSTM forecaster (PyTorch) plus baseline models and anomaly detection |
| **Containerised Deployment** | Docker Compose including InfluxDB, Grafana, Mosquitto, and Jupyter |
| **Production-Grade Quality** | 79 unit tests, GitHub Actions CI/CD, structured logging, type-safe config |

---

## Standards Compliance and Interoperability

DERIM is constructed around widely adopted open standards to ensure seamless interaction with existing utility infrastructure and vendor equipment.

| Standard / Protocol      | Role in DERIM                          | Interoperability Benefit |
|--------------------------|----------------------------------------|--------------------------|
| **IEEE 2030.5 (SEP 2.0)** | Core data model alignment              | Compatibility with smart inverters and utility head-end systems |
| **IEC 61968 / 61970 CIM** | Telemetry and device taxonomy          | Exchange with SCADA, EMS, DMS, and ADMS platforms |
| **Modbus TCP/RTU**       | Primary industrial adapter             | Connects to the majority of meters, inverters, and controllers |
| **MQTT 3.1.1**           | Pub/sub for IoT and edge devices       | Lightweight communication with gateways and sensors |
| **SunSpec**              | Solar-specific Modbus maps             | Plug-and-play with certified inverters (SMA, Fronius, SolarEdge, Enphase) |
| **OCPP 1.6-J / 2.0.1**   | EV charging management                 | WebSocket support for major charger brands |
| **OpenAPI 3.0**          | REST API specification                 | Interactive docs and client SDK generation |

---

## Architecture

```mermaid
flowchart TD
    subgraph "DER Hardware Layer"
        A[Modbus Devices] 
        B[MQTT Sensors]
        C[SunSpec Inverters]
        D[OCPP Chargers]
    end

    subgraph "DERIM Middleware"
        E[Protocol Adapters\n(Modbus, MQTT, SunSpec, OCPP)]
        F[Data Normaliser\n(Common Information Model)]
        
        G[REST API\n(FastAPI)]
        H[Storage Backend\n(InfluxDB / SQLite)]
        I[Digital Twin\n(LSTM + Simulation)]
    end

    A --> E
    B --> E
    C --> E
    D --> E
    E --> F
    F --> G
    F --> H
    F --> I

    style E fill:#e3f2fd
    style F fill:#f3e5f5
    style G fill:#e8f5e9
    style H fill:#fff3e0
    style I fill:#ffebee
```

---

## Quick Start

### Prerequisites
Python 3.11+ is required. Docker is recommended for the complete stack but optional for core development.

### Installation
```bash
git clone https://github.com/iceccarelli/DERIM-Middleware-project.git
cd DERIM-Middleware-project

python3.11 -m venv .venv
source .venv/bin/activate

pip install --upgrade pip
pip install -r requirements/base.txt
pip install -e .

cp .env.example .env
```

### Running the API
```bash
# Development mode with SQLite (no external services)
uvicorn derim.main:app --reload

# API available at http://localhost:8000
# Interactive documentation: http://localhost:8000/docs
```

### Running with Docker
```bash
# Full stack (API + InfluxDB + MQTT)
docker compose up -d

# With monitoring dashboards
docker compose --profile monitoring up -d

# With Jupyter for ML experimentation
docker compose --profile ml up -d
```

### Running Tests
```bash
pip install -r requirements/dev.txt
pytest tests/ -v
```

All tests pass cleanly; code is formatted with Black, isort, and linted with flake8.

---

## Project Structure
```
DERIM-Middleware-project/
├── src/derim/                  # Main package
│   ├── adapters/               # Protocol implementations
│   ├── api/                    # FastAPI routes & dependencies
│   ├── digital_twin/           # Forecasting and simulation
│   ├── models/                 # Pydantic schemas
│   ├── storage/                # Backend abstractions
│   ├── utils/                  # Logging and helpers
│   ├── config.py
│   └── main.py
├── tests/                      # 79 unit tests
├── notebooks/                  # Demonstrations
├── data/                       # Sample datasets
├── docs/                       # Detailed guides
├── docker-compose.yml
├── Dockerfile
├── requirements/               # Split dependency groups
├── .github/                    # CI workflows
├── CONTRIBUTING.md
├── CHANGELOG.md
└── LICENSE
```

---

## API Reference

The REST API is served at `/api/v1/` with automatic Swagger UI (`/docs`) and ReDoc (`/redoc`).

### Core Endpoints

| Method | Path                        | Description |
|--------|-----------------------------|-------------|
| `GET`  | `/health`                   | Service status and version |
| `GET`  | `/api/v1/devices`           | List registered devices |
| `POST` | `/api/v1/devices`           | Register new device |
| `GET`  | `/api/v1/telemetry/{id}`    | Query historical data |
| `POST` | `/api/v1/telemetry/{id}`    | Ingest new telemetry |
| `POST` | `/api/v1/control/{id}`      | Send control command |
| `GET`  | `/api/v1/forecast/{id}`     | Retrieve ML forecast |

**Example requests** are provided in the interactive documentation. Sample curl commands are available in the `docs/api_reference.md` file.

---

## Data Models

All data is modelled with Pydantic v2 and aligned with IEEE 2030.5 and IEC 61968 CIM. The base `DERTelemetry` class serves as the normalisation target for every adapter.

| Model              | Purpose                          | Notable Fields |
|--------------------|----------------------------------|----------------|
| `DERTelemetry`     | Core telemetry record            | `timestamp`, `power_kw`, `voltage_v`, `state` |
| `SolarTelemetry`   | Solar PV extension               | `irradiance_w_m2`, `dc_voltage_v` |
| `BatteryTelemetry` | Battery storage extension        | `soc_percent`, `soh_percent` |
| `EVChargerTelemetry` | EVSE extension                 | `connector_status`, `session_energy_kwh` |
| `DERDevice`        | Device registration              | `device_id`, `protocol`, `rated_power_kw` |

---

## Protocol Adapters

Each adapter inherits from `BaseAdapter` and implements `connect()`, `disconnect()`, `read_data()`, and `write_command()`. Data is automatically normalised to the common model.

| Adapter         | Protocol          | Typical Devices                     |
|-----------------|-------------------|-------------------------------------|
| `ModbusAdapter` | Modbus TCP/RTU    | Inverters, meters, BMS              |
| `MQTTAdapter`   | MQTT 3.1.1        | IoT gateways and sensors            |
| `SunSpecAdapter`| SunSpec over Modbus | Certified solar inverters         |
| `OCPPAdapter`   | OCPP 1.6-J        | EV charging stations                |

Adding a new adapter requires only implementing the four abstract methods — a process that typically takes under an hour for common protocols.

---

## Digital Twin Module

The digital twin component offers basic forecasting and anomaly detection capabilities.

- **Forecasting**: LSTM network (PyTorch) with persistence and moving-average baselines. Forecasts are generated for horizons of 1–168 hours.
- **Simulation**: Compares predictions against live telemetry, computes error metrics (MAE, RMSE), and flags anomalies using configurable thresholds.
- **Training**: End-to-end pipeline with data preprocessing and model persistence.

The module is intentionally lightweight and designed to be extended or replaced with more sophisticated models as needed.

---

## Configuration

Configuration is managed through Pydantic Settings and environment variables (or `.env` file). All values are validated at startup.

| Variable                  | Default               | Description |
|---------------------------|-----------------------|-------------|
| `STORAGE_BACKEND`         | `sqlite`              | `sqlite` or `influxdb` |
| `INFLUXDB_URL`            | `http://localhost:8086` | InfluxDB endpoint |
| `APP_PORT`                | `8000`                | API listening port |
| `LOG_LEVEL`               | `INFO`                | Logging verbosity |
| `LSTM_EPOCHS`             | `50`                  | Training iterations (example) |

Full list and descriptions are in `src/derim/config.py`.

---

## Jupyter Notebooks

The `notebooks/` directory contains ready-to-run demonstrations:

- `01_data_exploration.ipynb` – Dataset visualisation and statistics
- `02_protocol_demo.ipynb` – Adapter usage examples
- `03_digital_twin_training.ipynb` – Model training workflow
- `04_api_client_demo.ipynb` – REST API interaction

---

## Real-World Applications

DERIM has been structured to support common energy-system workflows:

- Multi-vendor fleet monitoring
- Real-time telemetry aggregation
- Solar generation and load forecasting
- EV charging coordination
- Battery dispatch for peak shaving
- Regulatory reporting preparation
- Research experimentation
- Virtual power plant data layers

---

## Roadmap

Future development will focus on the following areas (contributions welcomed):

| Priority | Feature                  | Status |
|----------|--------------------------|--------|
| High     | DNP3 and IEC 61850 adapters | Planned |
| High     | WebSocket telemetry streaming | Planned |
| Medium   | OpenADR 2.0b support     | Planned |
| Medium   | Pre-built Grafana dashboards | In progress |
| Low      | Lightweight edge deployment | Planned |

---

## Contributing

Contributions of any size are welcome and appreciated. Whether you are reporting an issue, improving documentation, adding an adapter, or sharing datasets, your help advances the project.

Please read [CONTRIBUTING.md](CONTRIBUTING.md) before submitting a pull request. All contributors are expected to follow the project's code of conduct.

---

## License

This project is licensed under the MIT License. See [LICENSE](LICENSE) for details.

---

## Acknowledgements

DERIM builds on the excellent work of the IEEE 2030.5 working group, the SunSpec Alliance, the Open Charge Alliance, and the open-source communities behind FastAPI, PyTorch, InfluxDB, and Pydantic. Thank you to everyone whose tools and standards made this project possible.

**Built with care. Open for collaboration.**
```
