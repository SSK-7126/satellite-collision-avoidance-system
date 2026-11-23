"""
backend/catalogue/__init__.py
============================
Real Satellite Catalogue and Registry module for ICPS.
Provides CelesTrak GP and Space-Track ingestion, TLE and OMM parsing,
local caching, search, and tracking management.
"""

from .models import (
    CatalogueObject,
    OrbitalElements,
    CatalogueSource,
    RecordFormat,
)
from .parsers import (
    parse_tle,
    parse_omm_json,
    parse_omm_csv,
    compute_tle_checksum,
)
from .client import CelesTrakClient, SpaceTrackClient
from .registry import CatalogueRegistry

__all__ = [
    "CatalogueObject",
    "OrbitalElements",
    "CatalogueSource",
    "RecordFormat",
    "parse_tle",
    "parse_omm_json",
    "parse_omm_csv",
    "compute_tle_checksum",
    "CelesTrakClient",
    "SpaceTrackClient",
    "CatalogueRegistry",
]
