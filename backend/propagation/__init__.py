"""
backend/propagation/__init__.py
==============================
SGP4 Multi-Object Propagation and Coordinate Transformation Module.
Provides SGP4 propagation for TLE/OMM, explicit TEME-to-ECI J2000 transformations,
Unreal coordinates transformation, common time grid propagation, and per-object health monitoring.
"""

from .frames import (
    teme_to_j2000,
    j2000_to_unreal,
    CoordinateFrame,
    TransformRecord,
)
from .sgp4_engine import SGP4Propagator, PropagatedState
from .multi_object_manager import MultiObjectPropagator, PropagationJobResult

__all__ = [
    "teme_to_j2000",
    "j2000_to_unreal",
    "CoordinateFrame",
    "TransformRecord",
    "SGP4Propagator",
    "PropagatedState",
    "MultiObjectPropagator",
    "PropagationJobResult",
]
