# DERIM Roadmap

DERIM is open source under the MIT license. This roadmap reflects current priorities and is open to community input — propose changes via [issues](https://github.com/iceccarelli/derim-middleware/issues) or pull requests.

> Status legend: **Planned** = scoped, not started · **In progress** = actively being built · **Shipped** = released.

## High Priority
- **DNP3 and IEC 61850 protocol adapters** — Planned
- **Native WebSocket streaming for real-time telemetry** — Planned
- **OpenADR 2.0b demand response integration** — Planned
- **End-to-end adapter dispatch for control commands** — Planned

## Medium Priority
- **Pre-built Grafana dashboard library** — Planned
- **Advanced edge-optimized deployment profiles** — Planned
- **Automated model drift detection** — Planned
- **Expanded test coverage on adapter I/O paths** — In progress

## Longer Term
- **Kubernetes operator for large-scale orchestration** — Planned
- **Federated learning across multiple DERIM instances** — Planned
- **Agent-based digital twin simulation** — Planned

## Shipped
- **v0.1.1** — 4 protocol adapters (Modbus, MQTT, SunSpec, OCPP), digital-twin baseline + LSTM forecaster, CIM-aligned Pydantic models, SQLite/InfluxDB storage, FastAPI REST API, Docker Compose stack.

---
Contributions that align with any of these areas — or introduce new ones — are welcome. See [CONTRIBUTING.md](CONTRIBUTING.md).
