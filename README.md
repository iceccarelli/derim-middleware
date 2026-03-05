# DERIM Middleware

**Smart Grid Digital Twin Middleware for Distributed Energy Resource Integration**

[![CI](https://github.com/iceccarelli/DERIM-Middleware-project/actions/workflows/ci.yml/badge.svg)](https://github.com/iceccarelli/DERIM-Middleware-project/actions/workflows/ci.yml)
[![Python 3.11+](https://img.shields.io/badge/python-3.11%2B-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

---

## Why DERIM Exists

The global energy landscape is undergoing its most significant transformation in a century. Millions of distributed energy resources -- rooftop solar panels, home batteries, electric vehicle chargers, community microgrids -- are being connected to power grids that were never designed for bidirectional, decentralised energy flows. Grid operators struggle with fragmented vendor ecosystems, proprietary protocols, and a lack of unified tooling to monitor, forecast, and control these assets in real time.

**DERIM solves this problem.** It is the open-source middleware layer that sits between physical DER hardware and grid management software, translating the babel of industrial protocols into a single, standards-aligned data model that any application can consume. Whether you are a utility engineer integrating 10,000 rooftop inverters, a researcher modelling battery degradation, or a startup building the next-generation virtual power plant -- DERIM gives you a production-ready foundation to build on immediately.

> **"The clean energy transition will not be won by hardware alone. It will be won by the software that makes millions of distributed assets work together as one."**

---

## Overview

DERIM (Distributed Energy Resource Integration Middleware) is an open-source, modular middleware platform that bridges the gap between heterogeneous distributed energy resources (DERs) and modern smart grid management systems. It ingests real-time data from solar PV inverters, battery energy storage systems, and EV charging stations through standard industrial protocols, normalises it into a vendor-neutral common information model aligned with IEEE 2030.5 and IEC 61968 CIM, stores time-series telemetry, exposes a RESTful API for monitoring and control, and includes a digital twin module for ML-based forecasting and anomaly detection.

The middleware is designed for **grid operators**, **DER manufacturers**, **energy researchers**, and **smart grid developers** who need a unified, extensible platform for integrating and managing distributed energy resources at scale.

### Who Should Use DERIM

| Audience | Use Case |
|----------|----------|
| **Grid Operators and Utilities** | Unified DER visibility, real-time monitoring, demand response dispatch, fleet control |
| **DER Manufacturers** | Standards-compliant integration testing, protocol validation, interoperability certification |
| **Energy Researchers** | Time-series analysis, forecasting model benchmarking, digital twin experimentation |
| **Smart Grid Developers** | REST API for building dashboards, mobile apps, VPP platforms, and DERMS solutions |
| **Standards Bodies and Regulators** | Reference implementation for IEEE 2030.5, IEC 61968 CIM, and OCPP compliance |
| **Universities and Students** | Hands-on learning platform for smart grid, IoT, and ML in energy systems |

---

## Key Features

| Feature | Description |
|---------|-------------|
| **Multi-Protocol Adapters** | Modbus TCP/RTU, MQTT, SunSpec, and OCPP 1.6/2.0.1 with a pluggable adapter architecture |
| **Standards-Aligned Data Model** | Pydantic models aligned with IEEE 2030.5 (SEP 2.0) and IEC 61968/61970 CIM |
| **Time-Series Storage** | InfluxDB for production workloads with SQLite fallback for zero-dependency development |
| **REST API** | FastAPI with automatic OpenAPI/Swagger documentation, device management, telemetry, and control |
| **Digital Twin Engine** | LSTM neural network forecaster (PyTorch), baseline models, simulation with anomaly detection |
| **Containerised Deployment** | Docker and Docker Compose with InfluxDB, Grafana, Mosquitto MQTT broker, and Jupyter |
| **Production-Grade Quality** | 79 unit tests, CI/CD via GitHub Actions, structured logging, type-safe configuration |
| **Immediate Interoperability** | Designed to plug into existing SCADA, ADMS, DERMS, and VPP platforms via REST or protocol bridges |

---

## Standards Compliance and Interoperability

DERIM is built from the ground up around open standards, ensuring that it integrates seamlessly with existing utility infrastructure, vendor equipment, and regulatory frameworks. Every data model, protocol adapter, and API response is designed for immediate compatibility with the systems that grid operators and DER manufacturers already use.

| Standard / Protocol | Role in DERIM | Interoperability Benefit |
|---------------------|---------------|--------------------------|
| **IEEE 2030.5** (SEP 2.0) | Core data model alignment | Direct compatibility with smart inverters, demand response programmes, and utility head-end systems |
| **IEC 61968 / 61970 CIM** | Telemetry field naming and device taxonomy | Seamless data exchange with SCADA, EMS, DMS, and ADMS platforms |
| **Modbus TCP/RTU** | Protocol adapter | Connects to 90%+ of industrial meters, inverters, and battery controllers worldwide |
| **MQTT 3.1.1** | Protocol adapter | IoT-native pub/sub for edge gateways, smart sensors, and cloud brokers |
| **SunSpec** (Modbus maps) | Protocol adapter | Plug-and-play with SunSpec-certified solar inverters (SMA, Fronius, SolarEdge, Enphase) |
| **OCPP 1.6-J / 2.0.1** | Protocol adapter | Full EV charging station management via WebSocket (ABB, Schneider, ChargePoint) |
| **OpenAPI 3.0** | REST API specification | Auto-generated interactive docs; client SDK generation in any language |

This means DERIM can serve as a **protocol translation layer** between legacy SCADA systems and modern cloud platforms, a **data normalisation engine** for multi-vendor DER fleets, or a **digital twin backend** for research and optimisation -- all without vendor lock-in.

---

## Architecture

```
+------------------------------------------------------------------+
|                        DERIM Middleware                           |
|                                                                  |
|  +----------+  +----------+  +----------+  +----------+         |
|  |  Modbus   |  |   MQTT   |  | SunSpec  |  |   OCPP   |        |
|  |  Adapter  |  |  Adapter |  |  Adapter |  |  Adapter |        |
|  +-----+----+  +-----+----+  +-----+----+  +-----+----+        |
|        |              |              |              |             |
|        +--------------+--------------+--------------+            |
|                              |                                   |
|                    +---------v---------+                         |
|                    |  Data Normaliser   |                        |
|                    |  (Common Model)    |                        |
|                    +---------+---------+                         |
|                              |                                   |
|              +---------------+---------------+                   |
|              |               |               |                   |
|    +---------v------+ +-----v------+ +------v---------+         |
|    |  REST API       | |  Storage   | |  Digital Twin  |        |
|    |  (FastAPI)      | |  Backend   | |  (LSTM + Sim)  |        |
|    |                 | |            | |                 |        |
|    | - /devices      | | - InfluxDB | | - Forecasting  |        |
|    | - /telemetry    | | - SQLite   | | - Anomaly Det. |        |
|    | - /control      | |            | | - Scenarios    |        |
|    | - /forecast     | |            | |                |        |
|    +----------------+  +------------+ +-----------------+        |
+------------------------------------------------------------------+
```

---

## Quick Start

### Prerequisites

DERIM requires **Python 3.11** or later. Docker is recommended for the full stack but is not required for local development.

### Installation

```bash
# Clone the repository.
git clone https://github.com/iceccarelli/DERIM-Middleware-project.git
cd DERIM-Middleware-project

# Create a virtual environment.
python3.11 -m venv .venv
source .venv/bin/activate

# Install dependencies.
pip install --upgrade pip
pip install -r requirements/base.txt
pip install -e .

# Copy and customise the environment file.
cp .env.example .env
```

### Running the API

```bash
# Start with SQLite storage (zero external dependencies).
uvicorn derim.main:app --reload

# The API is now available at http://localhost:8000
# Interactive docs at http://localhost:8000/docs
```

### Running with Docker

```bash
# Start the full stack (API + InfluxDB + MQTT broker).
docker compose up -d

# Include Grafana monitoring dashboards.
docker compose --profile monitoring up -d

# Include Jupyter notebooks for ML experimentation.
docker compose --profile ml up -d
```

### Running Tests

```bash
pip install -r requirements/dev.txt
pytest tests/ -v
```

All **79 tests** pass with zero warnings. Black, isort, and flake8 all report clean.

---

## Project Structure

```
DERIM-Middleware-project/
├── src/derim/                  # Main application package
│   ├── adapters/               # Protocol adapters
│   │   ├── base.py             #   Abstract base adapter
│   │   ├── modbus.py           #   Modbus TCP/RTU
│   │   ├── mqtt.py             #   MQTT pub/sub
│   │   ├── sunspec.py          #   SunSpec solar inverters
│   │   └── ocpp.py             #   OCPP EV chargers
│   ├── api/                    # FastAPI REST API
│   │   ├── dependencies.py     #   Dependency injection
│   │   └── routes/             #   Endpoint handlers
│   │       ├── data.py         #     Devices and telemetry
│   │       ├── control.py      #     Device control
│   │       └── digital_twin.py #     Forecasting
│   ├── digital_twin/           # ML forecasting module
│   │   ├── models/             #   Forecasting models
│   │   │   ├── baseline.py     #     Persistence and Moving Average
│   │   │   └── lstm_forecaster.py  # PyTorch LSTM
│   │   ├── simulator.py        #   Digital twin engine
│   │   └── trainer.py          #   Training pipeline
│   ├── models/                 # Pydantic data models
│   │   ├── common.py           #   Core telemetry models (IEEE 2030.5 aligned)
│   │   └── adapters.py         #   Adapter configuration models
│   ├── storage/                # Storage backends
│   │   ├── base.py             #   Abstract interface
│   │   ├── influxdb.py         #   InfluxDB client
│   │   └── sqlite.py           #   SQLite fallback
│   ├── utils/                  # Utilities
│   │   └── logger.py           #   Structured logging (structlog)
│   ├── config.py               # Pydantic Settings configuration
│   └── main.py                 # FastAPI app factory
├── tests/                      # Test suite (79 tests)
├── notebooks/                  # Jupyter demonstrations
│   ├── 01_data_exploration.ipynb
│   ├── 02_protocol_demo.ipynb
│   ├── 03_digital_twin_training.ipynb
│   └── 04_api_client_demo.ipynb
├── data/                       # Sample datasets
├── docs/                       # Extended documentation
│   ├── architecture.md
│   ├── deployment.md
│   ├── api_reference.md
│   ├── adapters.md
│   └── digital_twin.md
├── docker-compose.yml          # Full-stack deployment
├── Dockerfile                  # Multi-stage container build
├── requirements/               # Dependency groups (base, dev, ml)
├── .github/                    # CI/CD workflows and templates
├── CONTRIBUTING.md             # Contribution guidelines
├── CHANGELOG.md                # Release history
└── LICENSE                     # MIT License
```

---

## API Reference

The DERIM REST API is served at `http://localhost:8000/api/v1/` with automatic interactive documentation available at `/docs` (Swagger UI) and `/redoc` (ReDoc).

### Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/health` | Health check with version, uptime, and storage status |
| `GET` | `/api/v1/devices` | List all registered DER devices |
| `POST` | `/api/v1/devices` | Register a new DER device |
| `GET` | `/api/v1/devices/{device_id}` | Get a single device by ID |
| `GET` | `/api/v1/telemetry/{device_id}` | Query telemetry (with `start`, `end`, `limit` params) |
| `POST` | `/api/v1/telemetry/{device_id}` | Ingest telemetry records |
| `POST` | `/api/v1/control/{device_id}` | Send a control command (setpoint, on/off) |
| `GET` | `/api/v1/forecast/{device_id}` | Get ML forecast (with `horizon_hours` param) |
| `GET` | `/api/v1/forecast/models` | List available trained models |

### Example: Register a Device

```bash
curl -X POST http://localhost:8000/api/v1/devices \
  -H "Content-Type: application/json" \
  -d '{
    "device_id": "solar-inv-001",
    "device_type": "solar_pv",
    "name": "Rooftop Solar Inverter",
    "location": "Building A",
    "protocol": "modbus",
    "rated_power_kw": 5.0,
    "state": "on"
  }'
```

### Example: Query Telemetry

```bash
curl "http://localhost:8000/api/v1/telemetry/solar-inv-001?start=2026-03-01T00:00:00&end=2026-03-04T23:59:59&limit=100"
```

### Example: Send Control Command

```bash
curl -X POST http://localhost:8000/api/v1/control/solar-inv-001 \
  -H "Content-Type: application/json" \
  -d '{
    "command": "setpoint",
    "value": 3.5,
    "parameters": {"ramp_rate_kw_s": 0.5}
  }'
```

### Example: Get Forecast

```bash
curl "http://localhost:8000/api/v1/forecast/solar-inv-001?horizon_hours=24"
```

---

## Data Models

DERIM uses Pydantic models aligned with IEEE 2030.5 (Smart Energy Profile 2.0) and IEC 61968/61970 CIM standards. The base `DERTelemetry` model provides a vendor-neutral schema that all protocol adapters normalise into.

| Model | Purpose | Key Fields |
|-------|---------|------------|
| `DERTelemetry` | Base telemetry record | `timestamp`, `device_id`, `power_kw`, `energy_kwh`, `voltage_v`, `current_a`, `frequency_hz`, `state` |
| `SolarTelemetry` | Solar PV extension | `irradiance_w_m2`, `panel_temperature_c`, `dc_voltage_v`, `dc_current_a` |
| `BatteryTelemetry` | BESS extension | `soc_percent`, `soh_percent`, `temperature_c`, `charge_rate_kw` |
| `EVChargerTelemetry` | EVSE extension | `connector_status`, `session_energy_kwh`, `vehicle_soc_percent` |
| `DERDevice` | Device registration | `device_id`, `device_type`, `name`, `location`, `protocol`, `rated_power_kw` |
| `CommandRequest` | Control command | `command`, `value`, `parameters` |
| `ForecastResponse` | ML forecast | `device_id`, `model_name`, `predictions[]` |

---

## Protocol Adapters

Each adapter inherits from `BaseAdapter` and implements four core methods: `connect()`, `disconnect()`, `read_data()`, and `write_command()`. All adapters normalise raw device data into the common `DERTelemetry` model, ensuring **plug-and-play interoperability** regardless of the underlying hardware vendor.

| Adapter | Protocol | Typical Devices | Transport |
|---------|----------|-----------------|-----------|
| `ModbusAdapter` | Modbus TCP/RTU | Solar inverters, power meters, BMS | TCP socket / Serial |
| `MQTTAdapter` | MQTT 3.1.1 | IoT gateways, smart sensors, edge devices | TCP (pub/sub) |
| `SunSpecAdapter` | SunSpec (Modbus) | Solar inverters (SMA, Fronius, SolarEdge, Enphase) | TCP socket |
| `OCPPAdapter` | OCPP 1.6-J | EV charging stations (ABB, Schneider, ChargePoint) | WebSocket |

### Adding a Custom Adapter

Creating a new adapter for any protocol takes minutes:

```python
from derim.adapters.base import BaseAdapter
from derim.models.common import DERTelemetry, CommandRequest, CommandResponse

class MyCustomAdapter(BaseAdapter):
    async def connect(self) -> None: ...
    async def disconnect(self) -> None: ...
    async def read_data(self) -> DERTelemetry: ...
    async def write_command(self, command: CommandRequest) -> CommandResponse: ...
```

---

## Digital Twin Module

The digital twin module provides ML-based power forecasting and real-time anomaly detection for DER devices.

**Forecasting Models.** The module includes an LSTM neural network (PyTorch) for sequence-to-sequence power forecasting, along with persistence and moving-average baselines for benchmarking. The LSTM model is trained on historical telemetry data and can generate forecasts from 1 to 168 hours ahead with confidence intervals.

**Simulation Engine.** The `Simulator` class creates a virtual replica of a physical device by comparing model predictions with actual telemetry. It computes MAE, RMSE, and residual statistics, flags anomalous data points using configurable sigma thresholds, tracks model drift over time, and supports what-if scenario analysis with modified input profiles.

**Training Pipeline.** The `Trainer` class provides an end-to-end pipeline for loading CSV data, preprocessing (missing value imputation, negative clipping), training the LSTM model, and persisting trained artefacts to disk.

---

## Configuration

DERIM uses [Pydantic Settings](https://docs.pydantic.dev/latest/concepts/pydantic_settings/) for type-safe, validated configuration. All values can be set via environment variables or a `.env` file.

| Variable | Default | Description |
|----------|---------|-------------|
| `STORAGE_BACKEND` | `sqlite` | Storage backend (`sqlite` or `influxdb`) |
| `SQLITE_DB_PATH` | `./data/derim.db` | SQLite database file path |
| `INFLUXDB_URL` | `http://localhost:8086` | InfluxDB server URL |
| `INFLUXDB_TOKEN` | `my-super-secret-token` | InfluxDB authentication token |
| `INFLUXDB_ORG` | `derim` | InfluxDB organisation |
| `INFLUXDB_BUCKET` | `derim_telemetry` | InfluxDB bucket name |
| `APP_PORT` | `8000` | API server port |
| `LOG_LEVEL` | `INFO` | Logging level |
| `MODEL_SAVE_DIR` | `./saved_models` | Directory for trained ML models |
| `FORECAST_HORIZON_HOURS` | `24` | Default forecast horizon |
| `LSTM_EPOCHS` | `50` | LSTM training epochs |
| `LSTM_BATCH_SIZE` | `32` | LSTM training batch size |
| `LSTM_SEQUENCE_LENGTH` | `96` | LSTM input sequence length |

---

## Jupyter Notebooks

Four demonstration notebooks are included in the `notebooks/` directory for hands-on exploration.

| Notebook | Description |
|----------|-------------|
| `01_data_exploration.ipynb` | Load and visualise the sample solar PV dataset with statistical analysis |
| `02_protocol_demo.ipynb` | Demonstrate protocol adapter configuration and simulated data reads |
| `03_digital_twin_training.ipynb` | Train the LSTM forecaster and evaluate against baselines |
| `04_api_client_demo.ipynb` | Interact with the DERIM REST API using Python `requests` |

---

## Real-World Applications

DERIM is designed to be immediately useful in solving today's most pressing energy challenges.

| Challenge | How DERIM Helps |
|-----------|-----------------|
| **Multi-vendor DER fleet management** | Normalise data from hundreds of device types into one unified API |
| **Grid visibility and situational awareness** | Real-time telemetry aggregation with time-series storage |
| **Solar generation forecasting** | LSTM digital twin predicts output 1 to 168 hours ahead |
| **EV charging load management** | OCPP adapter enables remote start/stop and load balancing |
| **Battery dispatch optimisation** | Control API combined with forecasting enables peak shaving and arbitrage |
| **Regulatory compliance reporting** | Standards-aligned data model simplifies audit trails |
| **Research and benchmarking** | Jupyter notebooks and sample data for reproducible experiments |
| **Virtual power plant (VPP) backends** | REST API serves as the data layer for VPP orchestration |
| **Microgrid control systems** | Protocol adapters and control endpoints for islanded operation |

---

## Roadmap

The following features are planned for future releases. Contributions in any of these areas are especially welcome.

| Priority | Feature | Description |
|----------|---------|-------------|
| High | DNP3 Adapter | Utility-grade SCADA protocol support |
| High | IEC 61850 Adapter | Substation automation (MMS/GOOSE) |
| High | WebSocket Streaming | Real-time telemetry push to clients |
| Medium | OpenADR 2.0b | Demand response programme integration |
| Medium | Fleet Optimisation | Multi-device coordination and dispatch |
| Medium | Grafana Dashboards | Pre-built monitoring templates |
| Low | Edge Deployment | Lightweight mode for Raspberry Pi and edge gateways |
| Low | IEEE 2030.5 Server | Full Smart Energy Profile 2.0 compliance |

---

## Contributing

Contributions are warmly welcomed and deeply appreciated. Whether you are fixing a typo, adding a protocol adapter, improving the digital twin models, or sharing real-world DER datasets, your contribution helps advance the state of open-source smart grid tooling.

**This project aims to become a community-driven standard for distributed energy resource integration.** We believe that open, interoperable middleware is essential for accelerating the clean energy transition, and we invite grid operators, researchers, manufacturers, and developers from around the world to join us in building it.

Please read [CONTRIBUTING.md](CONTRIBUTING.md) for detailed guidelines on how to get started.

---

## License

This project is licensed under the MIT License. See [LICENSE](LICENSE) for the full text.

---

## Acknowledgements

DERIM builds upon the work of many open-source projects and standards bodies. We gratefully acknowledge the contributions of the IEEE 2030.5 working group, the SunSpec Alliance, the Open Charge Alliance (OCPP), and the developers of FastAPI, PyTorch, InfluxDB, and the many Python libraries that make this project possible.

---

**Built with purpose. Built for the grid. Built for everyone.**
