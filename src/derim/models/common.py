"""
Common data models for Distributed Energy Resources.

These Pydantic models define the canonical representation of DER telemetry
data within the DERIM middleware.  The design is informed by the IEEE 2030.5
(Smart Energy Profile 2.0) and IEC 61968/61970 Common Information Model (CIM)
standards, providing a vendor-neutral schema that all protocol adapters
normalise into.

Key models
----------
- ``DERTelemetry``: Base telemetry record shared by all DER types.
- ``SolarTelemetry``: Extension for photovoltaic inverters.
- ``BatteryTelemetry``: Extension for battery energy storage systems.
- ``EVChargerTelemetry``: Extension for electric vehicle supply equipment.
- ``DERDevice``: Device registration / metadata record.
- ``CommandRequest`` / ``CommandResponse``: Control-plane messages.
- ``ForecastResponse``: ML forecast payload.
"""

from datetime import datetime
from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel, ConfigDict, Field

# ---------------------------------------------------------------------------
# Enumerations
# ---------------------------------------------------------------------------


class DeviceState(str, Enum):
    """Operational state of a DER device."""

    ON = "on"
    OFF = "off"
    STANDBY = "standby"
    FAULT = "fault"
    UNKNOWN = "unknown"


class DERType(str, Enum):
    """Classification of distributed energy resource types."""

    SOLAR_PV = "solar_pv"
    BATTERY = "battery"
    EV_CHARGER = "ev_charger"
    WIND = "wind"
    GENERIC = "generic"


class ConnectorStatus(str, Enum):
    """OCPP-aligned connector status for EV chargers."""

    AVAILABLE = "Available"
    OCCUPIED = "Occupied"
    FAULTED = "Faulted"
    UNAVAILABLE = "Unavailable"
    RESERVED = "Reserved"


# ---------------------------------------------------------------------------
# Telemetry Models
# ---------------------------------------------------------------------------


class DERTelemetry(BaseModel):
    """
    Base telemetry record for any distributed energy resource.

    All protocol adapters must normalise their raw readings into this
    schema (or one of its device-specific subclasses) before passing
    data to the storage layer.

    Attributes
    ----------
    timestamp : datetime
        UTC timestamp of the measurement.
    device_id : str
        Unique identifier of the reporting device.
    device_type : DERType
        Classification of the device.
    power_kw : float
        Instantaneous active power in kilowatts.  Positive values
        indicate generation; negative values indicate consumption.
    energy_kwh : float
        Cumulative energy in kilowatt-hours.
    voltage_v : float
        RMS voltage in volts (line-to-neutral or line-to-line
        depending on device configuration).
    current_a : float
        RMS current in amperes.
    frequency_hz : float
        Grid frequency in hertz.
    state : DeviceState
        Current operational state of the device.
    power_factor : float | None
        Power factor (0.0 to 1.0).
    reactive_power_kvar : float | None
        Reactive power in kVAR.
    metadata : dict | None
        Arbitrary key-value pairs for protocol-specific extras.
    """

    timestamp: datetime = Field(
        default_factory=datetime.utcnow,
        description="UTC timestamp of the measurement",
    )
    device_id: str = Field(..., description="Unique device identifier")
    device_type: DERType = Field(
        default=DERType.GENERIC, description="Type of DER device"
    )
    power_kw: float = Field(
        default=0.0, description="Active power in kW (positive = generation)"
    )
    energy_kwh: float = Field(default=0.0, description="Cumulative energy in kWh")
    voltage_v: float = Field(default=0.0, description="Voltage in volts")
    current_a: float = Field(default=0.0, description="Current in amperes")
    frequency_hz: float = Field(default=50.0, description="Grid frequency in Hz")
    state: DeviceState = Field(
        default=DeviceState.UNKNOWN, description="Operational state"
    )
    power_factor: Optional[float] = Field(
        default=None, ge=0.0, le=1.0, description="Power factor"
    )
    reactive_power_kvar: Optional[float] = Field(
        default=None, description="Reactive power in kVAR"
    )
    metadata: Optional[dict[str, Any]] = Field(
        default=None, description="Protocol-specific metadata"
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "timestamp": "2026-03-04T12:00:00Z",
                "device_id": "solar-inv-001",
                "device_type": "solar_pv",
                "power_kw": 4.75,
                "energy_kwh": 1234.5,
                "voltage_v": 230.1,
                "current_a": 20.6,
                "frequency_hz": 50.01,
                "state": "on",
            }
        }
    )


class SolarTelemetry(DERTelemetry):
    """
    Extended telemetry for photovoltaic inverters.

    Adds solar-specific measurements such as irradiance, panel
    temperature, and DC-side values.
    """

    device_type: DERType = Field(default=DERType.SOLAR_PV)
    irradiance_w_m2: Optional[float] = Field(
        default=None, ge=0.0, description="Solar irradiance in W/m^2"
    )
    panel_temperature_c: Optional[float] = Field(
        default=None, description="Panel temperature in Celsius"
    )
    dc_voltage_v: Optional[float] = Field(
        default=None, description="DC bus voltage in volts"
    )
    dc_current_a: Optional[float] = Field(
        default=None, description="DC current in amperes"
    )


class BatteryTelemetry(DERTelemetry):
    """
    Extended telemetry for battery energy storage systems (BESS).

    Adds state-of-charge, temperature, and charge/discharge mode.
    """

    device_type: DERType = Field(default=DERType.BATTERY)
    soc_percent: Optional[float] = Field(
        default=None,
        ge=0.0,
        le=100.0,
        description="State of charge in percent",
    )
    soh_percent: Optional[float] = Field(
        default=None,
        ge=0.0,
        le=100.0,
        description="State of health in percent",
    )
    temperature_c: Optional[float] = Field(
        default=None, description="Battery temperature in Celsius"
    )
    charge_rate_kw: Optional[float] = Field(
        default=None, description="Charging rate in kW"
    )
    discharge_rate_kw: Optional[float] = Field(
        default=None, description="Discharging rate in kW"
    )


class EVChargerTelemetry(DERTelemetry):
    """
    Extended telemetry for electric vehicle supply equipment (EVSE).

    Adds connector status, session energy, and OCPP-related fields.
    """

    device_type: DERType = Field(default=DERType.EV_CHARGER)
    connector_status: ConnectorStatus = Field(
        default=ConnectorStatus.UNAVAILABLE,
        description="OCPP connector status",
    )
    session_energy_kwh: Optional[float] = Field(
        default=None, description="Energy delivered in current session"
    )
    max_power_kw: Optional[float] = Field(
        default=None, description="Maximum rated power of the charger"
    )
    vehicle_soc_percent: Optional[float] = Field(
        default=None,
        ge=0.0,
        le=100.0,
        description="Connected vehicle state of charge",
    )


# ---------------------------------------------------------------------------
# Device Registration
# ---------------------------------------------------------------------------


class DERDevice(BaseModel):
    """
    Registration record for a distributed energy resource.

    This model is used by the REST API to list and manage known devices.
    """

    device_id: str = Field(..., description="Unique device identifier")
    device_type: DERType = Field(..., description="Type of DER device")
    name: str = Field(..., description="Human-readable device name")
    location: Optional[str] = Field(
        default=None, description="Physical location or site"
    )
    protocol: Optional[str] = Field(
        default=None, description="Communication protocol (modbus, mqtt, ...)"
    )
    rated_power_kw: Optional[float] = Field(
        default=None, description="Rated / nameplate power in kW"
    )
    state: DeviceState = Field(default=DeviceState.UNKNOWN, description="Current state")
    metadata: Optional[dict[str, Any]] = Field(
        default=None, description="Additional device metadata"
    )


# ---------------------------------------------------------------------------
# Control Models
# ---------------------------------------------------------------------------


class CommandRequest(BaseModel):
    """
    Control command sent to a DER device via the REST API.

    Attributes
    ----------
    command : str
        Command type, e.g. ``"setpoint"``, ``"on"``, ``"off"``,
        ``"charge"``, ``"discharge"``.
    value : float | None
        Numeric parameter for the command (e.g. power setpoint in kW).
    parameters : dict | None
        Arbitrary additional parameters.
    """

    command: str = Field(..., description="Command type")
    value: Optional[float] = Field(
        default=None, description="Numeric command parameter"
    )
    parameters: Optional[dict[str, Any]] = Field(
        default=None, description="Additional command parameters"
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "command": "setpoint",
                "value": 5.0,
                "parameters": {"ramp_rate_kw_s": 0.5},
            }
        }
    )


class CommandResponse(BaseModel):
    """Response payload after a control command is dispatched."""

    device_id: str
    command: str
    status: str = Field(
        default="accepted",
        description="Execution status: accepted, rejected, error",
    )
    message: Optional[str] = Field(
        default=None, description="Human-readable status message"
    )


# ---------------------------------------------------------------------------
# Forecast Models
# ---------------------------------------------------------------------------


class ForecastPoint(BaseModel):
    """A single forecast data point."""

    timestamp: datetime
    power_kw: float
    confidence_lower: Optional[float] = None
    confidence_upper: Optional[float] = None


class ForecastResponse(BaseModel):
    """
    ML forecast response returned by the digital twin module.

    Contains the device identifier, the model used, and a list of
    predicted values over the forecast horizon.
    """

    device_id: str
    model_name: str = Field(default="lstm", description="Name of the forecasting model")
    horizon_hours: int = Field(default=24, description="Forecast horizon in hours")
    predictions: list[ForecastPoint] = Field(
        default_factory=list, description="Forecast data points"
    )
    generated_at: datetime = Field(default_factory=datetime.utcnow)
