"""
Protocol-specific data models used by individual adapters.

These models represent the raw or semi-structured data formats received
from each protocol before normalisation into the common ``DERTelemetry``
schema.  They are intentionally kept close to the wire format so that
adapters can validate incoming payloads before transformation.
"""

from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, Field

# ---------------------------------------------------------------------------
# Modbus
# ---------------------------------------------------------------------------


class ModbusRegisterBlock(BaseModel):
    """
    A contiguous block of Modbus holding or input registers.

    Attributes
    ----------
    unit_id : int
        Modbus slave / unit identifier.
    start_address : int
        Starting register address.
    values : list[int]
        Raw 16-bit register values.
    timestamp : datetime
        Time at which the registers were read.
    """

    unit_id: int = Field(..., description="Modbus unit ID")
    start_address: int = Field(..., description="Starting register address")
    values: list[int] = Field(default_factory=list, description="Raw register values")
    timestamp: datetime = Field(default_factory=datetime.utcnow)


# ---------------------------------------------------------------------------
# MQTT
# ---------------------------------------------------------------------------


class MQTTMessage(BaseModel):
    """
    Representation of an MQTT message received from a DER device.

    The ``payload`` is expected to be a JSON-serialisable dictionary
    whose keys map to telemetry fields.
    """

    topic: str = Field(..., description="MQTT topic")
    payload: dict[str, Any] = Field(..., description="Decoded JSON payload")
    qos: int = Field(default=0, ge=0, le=2, description="Quality of Service")
    retain: bool = Field(default=False, description="Retain flag")
    timestamp: datetime = Field(default_factory=datetime.utcnow)


# ---------------------------------------------------------------------------
# SunSpec
# ---------------------------------------------------------------------------


class SunSpecModelData(BaseModel):
    """
    Data extracted from a SunSpec model block.

    SunSpec defines standardised Modbus register maps (models) for
    solar inverters and other DER equipment.  This model captures the
    decoded values from a single SunSpec model.
    """

    model_id: int = Field(..., description="SunSpec model ID (e.g. 101, 103)")
    model_name: Optional[str] = Field(
        default=None, description="Human-readable model name"
    )
    values: dict[str, Any] = Field(
        default_factory=dict,
        description="Decoded point values keyed by SunSpec point name",
    )
    timestamp: datetime = Field(default_factory=datetime.utcnow)


# ---------------------------------------------------------------------------
# OCPP
# ---------------------------------------------------------------------------


class OCPPMeterValue(BaseModel):
    """
    OCPP MeterValues payload from an EV charging station.

    Represents a single set of sampled meter values as defined in
    OCPP 1.6 / 2.0.1.
    """

    connector_id: int = Field(..., description="Connector identifier")
    transaction_id: Optional[int] = Field(
        default=None, description="Active transaction ID"
    )
    meter_values: dict[str, Any] = Field(
        default_factory=dict,
        description="Sampled values (measurand -> value)",
    )
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class OCPPStatusNotification(BaseModel):
    """
    OCPP StatusNotification payload.

    Carries the current status of a connector on the charging station.
    """

    connector_id: int
    status: str = Field(..., description="Connector status string")
    error_code: str = Field(default="NoError")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
