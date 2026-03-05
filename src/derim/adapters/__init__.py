"""
Protocol adapters for communicating with distributed energy resources.

Each adapter implements the ``BaseAdapter`` interface and is responsible for
translating protocol-specific data into the common ``DERTelemetry`` model.
"""

from derim.adapters.base import BaseAdapter

__all__ = ["BaseAdapter"]
