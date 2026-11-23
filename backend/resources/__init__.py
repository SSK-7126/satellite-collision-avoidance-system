"""
backend/resources/__init__.py
============================
Satellite Hardware and Resource Registry module for ICPS.
Provides hardware metadata models, Tsiolkovsky propellant estimation,
burn event auditing, and field-level provenance tracking.
"""

from .models import (
    ProvenanceType,
    FieldProvenance,
    ThrusterSpecification,
    FuelEvent,
    SpacecraftHardwareRecord,
)
from .fuel_calculator import (
    estimate_propellant_consumption,
    estimate_delta_v_capacity,
    G0_STANDARD,
)
from .registry import HardwareRegistry

__all__ = [
    "ProvenanceType",
    "FieldProvenance",
    "ThrusterSpecification",
    "FuelEvent",
    "SpacecraftHardwareRecord",
    "estimate_propellant_consumption",
    "estimate_delta_v_capacity",
    "G0_STANDARD",
    "HardwareRegistry",
]
