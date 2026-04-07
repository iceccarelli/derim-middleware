# DERIM API Reference

This document provides a comprehensive reference for the DERIM REST API. The API is served by FastAPI with automatic interactive documentation available at `/docs` (Swagger UI) and `/redoc` (ReDoc) when the server is running.

## Base URL

All API endpoints are prefixed with `/api/v1/`. The health check endpoint is available at the root level.

```
http://localhost:8000/api/v1/
```

## Authentication

The current release does not enforce authentication. Production deployments should add OAuth 2.0 or API key middleware. See the [deployment guide](deployment.md) for recommendations.

## Endpoints

### Health Check

```
GET /health
```

Returns the application health status, version, storage backend type, and storage connectivity.

**Response (200 OK):**

```json
{
  "status": "healthy",
  "version": "0.1.1",
  "storage_backend": "sqlite",
  "storage_connected": true
}
```

### List Devices

```
GET /api/v1/devices
```

Returns all registered DER devices.

**Response (200 OK):**

```json
[
  {
    "device_id": "solar-inv-001",
    "device_type": "solar_pv",
    "name": "Rooftop Solar Inverter",
    "location": "Building A",
    "protocol": "modbus",
    "rated_power_kw": 5.0,
    "state": "on",
    "metadata": {}
  }
]
```

### Register Device

```
POST /api/v1/devices
```

Register a new DER device or update an existing one.

**Request Body:**

```json
{
  "device_id": "bess-001",
  "device_type": "battery",
  "name": "Lithium-Ion BESS",
  "location": "Substation 3",
  "protocol": "mqtt",
  "rated_power_kw": 100.0,
  "state": "on",
  "metadata": {
    "manufacturer": "Tesla",
    "model": "Megapack"
  }
}
```

**Response (201 Created):** Returns the registered device object.

### Get Device

```
GET /api/v1/devices/{device_id}
```

Retrieve a single device by its unique identifier.

**Response (200 OK):** Returns the device object.

**Response (404 Not Found):**

```json
{
  "detail": "Device 'nonexistent' not found"
}
```

### Query Telemetry

```
GET /api/v1/telemetry/{device_id}?start=2026-03-01T00:00:00&end=2026-03-04T23:59:59&limit=1000
```

Retrieve time-series telemetry data for a device within a time range.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `start` | ISO 8601 datetime | 24 hours ago | Start of the query range |
| `end` | ISO 8601 datetime | now | End of the query range |
| `limit` | integer (1-10000) | 1000 | Maximum records to return |

**Response (200 OK):**

```json
[
  {
    "timestamp": "2026-03-04T12:00:00Z",
    "device_id": "solar-inv-001",
    "device_type": "solar_pv",
    "power_kw": 3.45,
    "energy_kwh": 12.8,
    "voltage_v": 230.1,
    "current_a": 15.0,
    "frequency_hz": 50.0,
    "state": "on"
  }
]
```

### Ingest Telemetry

```
POST /api/v1/telemetry/{device_id}
```

Submit one or more telemetry records for a device.

**Request Body:**

```json
[
  {
    "timestamp": "2026-03-04T12:00:00Z",
    "device_id": "solar-inv-001",
    "power_kw": 3.45,
    "energy_kwh": 12.8,
    "voltage_v": 230.1,
    "current_a": 15.0,
    "frequency_hz": 50.0,
    "state": "on"
  }
]
```

**Response (201 Created):**

```json
{
  "status": "ok",
  "device_id": "solar-inv-001",
  "records_written": 1
}
```

### Send Control Command

```
POST /api/v1/control/{device_id}
```

Dispatch a control command to a registered device.

**Supported Commands:**

| Command | Description | Value Field |
|---------|-------------|-------------|
| `setpoint` | Set active power output | Power in kW |
| `on` | Enable the device | Not used |
| `off` | Disable the device | Not used |
| `charge` | Set battery to charge mode | Charge rate in kW |
| `discharge` | Set battery to discharge mode | Discharge rate in kW |
| `start` | Start EV charging session | Not used |
| `stop` | Stop EV charging session | Not used |

**Request Body:**

```json
{
  "command": "setpoint",
  "value": 3.5,
  "parameters": {
    "ramp_rate_kw_s": 0.5
  }
}
```

**Response (200 OK):**

```json
{
  "device_id": "solar-inv-001",
  "command": "setpoint",
  "status": "accepted",
  "message": "Command 'setpoint' accepted for device 'solar-inv-001' (protocol: modbus). Adapter dispatch pending."
}
```

### Get Forecast

```
GET /api/v1/forecast/{device_id}?horizon_hours=24
```

Generate an ML-based power forecast for a device.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `horizon_hours` | integer (1-168) | 24 | Forecast horizon in hours |

**Response (200 OK):**

```json
{
  "device_id": "solar-inv-001",
  "model_name": "persistence",
  "horizon_hours": 24,
  "generated_at": "2026-03-04T12:00:00Z",
  "predictions": [
    {
      "timestamp": "2026-03-04T12:15:00Z",
      "power_kw": 3.2,
      "confidence_lower": 2.56,
      "confidence_upper": 3.84
    }
  ]
}
```

### List Trained Models

```
GET /api/v1/forecast/models
```

List all available trained forecasting models.

**Response (200 OK):**

```json
{
  "available_models": ["persistence", "moving_average", "lstm"],
  "trained_devices": ["solar-inv-001"],
  "default_model": "persistence"
}
```

## Error Responses

All error responses follow a consistent format.

```json
{
  "detail": "Human-readable error description"
}
```

| Status Code | Meaning |
|-------------|---------|
| 400 | Bad Request (invalid parameters) |
| 404 | Resource not found |
| 422 | Validation Error (Pydantic) |
| 500 | Internal Server Error |
