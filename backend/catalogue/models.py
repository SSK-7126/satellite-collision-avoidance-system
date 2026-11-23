"""
backend/catalogue/models.py
===========================
Data models and schemas for space objects in the catalogue registry.
Strictly preserves scientific units, provenance, and data freshness.
"""

from dataclasses import dataclass, field, asdict
from typing import Optional, Dict, Any, Union, List
from enum import Enum
import math


class CatalogueSource(str, Enum):
    CELESTRAK_GP = "CELESTRAK_GP"
    SPACE_TRACK = "SPACE_TRACK"
    LOCAL_CACHE = "LOCAL_CACHE"
    USER_SIMULATION = "USER_SIMULATION"
    FILE_IMPORT = "FILE_IMPORT"
    MANUAL_ENTRY = "MANUAL_ENTRY"


class RecordFormat(str, Enum):
    TLE_2LINE = "TLE_2LINE"
    TLE_3LINE = "TLE_3LINE"
    OMM_JSON = "OMM_JSON"
    OMM_CSV = "OMM_CSV"
    STATE_VECTOR = "STATE_VECTOR"


@dataclass
class OrbitalElements:
    """
    Standard Keplerian and mean orbital elements.
    All angular units in degrees, distances in kilometres.
    """
    semi_major_axis_km: float
    eccentricity: float
    inclination_deg: float
    raan_deg: float
    arg_perigee_deg: float
    mean_anomaly_deg: float
    mean_motion_rev_per_day: float
    bstar: float = 0.0
    epoch_utc: str = ""
    period_minutes: float = 0.0
    apoapsis_km: float = 0.0
    periapsis_km: float = 0.0

    def validate(self) -> List[str]:
        """Validate physical sanity of orbital elements."""
        errors = []
        if self.semi_major_axis_km <= 0.0:
            errors.append(f"Semi-major axis must be positive, got {self.semi_major_axis_km}")
        if self.eccentricity < 0.0:
            errors.append(f"Eccentricity cannot be negative, got {self.eccentricity}")
        if self.eccentricity >= 1.0:
            errors.append(f"Bound Earth orbits require eccentricity < 1.0, got {self.eccentricity}")
        if not (0.0 <= self.inclination_deg <= 180.0):
            errors.append(f"Inclination must be within [0, 180] deg, got {self.inclination_deg}")
        if self.periapsis_km < 6378.137:
            errors.append(f"Periapsis ({self.periapsis_km:.1f} km) is below Earth's mean radius (6378.1 km)")
        return errors


@dataclass
class CatalogueObject:
    """
    Unified space object representation in the ICPS Catalogue & Registry.
    Decoupled from visualization and hardware models.
    """
    object_id: str                     # NORAD Cat ID (e.g. "25544") or unique custom ID
    name: str                          # Standard display name (e.g. "ISS (ZARYA)")
    epoch_utc: str                     # ISO-8601 UTC timestamp of orbital elements
    source: str                        # Provider provenance (CelesTrak, Space-Track, etc.)
    format: str                        # Source format (TLE, OMM, etc.)
    retrieval_time_utc: str            # Timestamp when record was ingested/retrieved
    raw_record: Union[str, Dict[str, Any]] # Original unparsed record

    international_designator: Optional[str] = None
    object_type: str = "UNKNOWN"       # PAYLOAD, ROCKET BODY, DEBRIS, UNKNOWN
    elements: Optional[OrbitalElements] = None
    is_tracked: bool = False           # Whether user selected this for active monitoring
    group: Optional[str] = None        # e.g. "stations", "active", "debris", "custom"
    is_stale: bool = False             # Flag indicating element epoch > staleness threshold
    stale_warning: Optional[str] = None
    error_state: Optional[str] = None
    provenance: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Serialize object to dictionary."""
        d = asdict(self)
        return d

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "CatalogueObject":
        """Deserialize from dictionary."""
        elems_data = data.get("elements")
        elems = None
        if elems_data:
            elems = OrbitalElements(**elems_data)
        
        return cls(
            object_id=str(data["object_id"]),
            name=data["name"],
            epoch_utc=data["epoch_utc"],
            source=data["source"],
            format=data["format"],
            retrieval_time_utc=data.get("retrieval_time_utc", ""),
            raw_record=data.get("raw_record", ""),
            international_designator=data.get("international_designator"),
            object_type=data.get("object_type", "UNKNOWN"),
            elements=elems,
            is_tracked=data.get("is_tracked", False),
            group=data.get("group"),
            is_stale=data.get("is_stale", False),
            stale_warning=data.get("stale_warning"),
            error_state=data.get("error_state"),
            provenance=data.get("provenance", {}),
        )
