"""
backend/custom_objects/__init__.py
==================================
Custom Satellite and Debris Configuration & Management module for ICPS.
Provides full CRUD workflows for user-created simulation objects, orbital conversion,
physical validation, schema versioning, JSON import/export, and scenario isolation.
"""

from .models import (
    ObjectOrigin,
    VisualAppearance,
    CustomSatellite,
    CustomDebris,
)
from .orbital_conversions import (
    keplerian_to_cartesian,
    cartesian_to_keplerian,
    validate_orbital_parameters,
)
from .scenario_manager import (
    CustomScenario,
    CustomObjectManager,
)

__all__ = [
    "ObjectOrigin",
    "VisualAppearance",
    "CustomSatellite",
    "CustomDebris",
    "keplerian_to_cartesian",
    "cartesian_to_keplerian",
    "validate_orbital_parameters",
    "CustomScenario",
    "CustomObjectManager",
]
