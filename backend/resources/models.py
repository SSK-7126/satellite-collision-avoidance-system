"""
backend/resources/models.py
===========================
Hardware, propulsion, and resource metadata models.
Strictly records field-level provenance, distinguishes estimates from telemetry,
and enforces that TLE/OMM is never treated as a source for hardware facts.
"""

from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from enum import Enum
from typing import Dict, Any, List, Optional, Union


class ProvenanceType(str, Enum):
    OPERATOR_SUPPLIED = "OPERATOR_SUPPLIED" # Manual operator entry or simulation database record
    PUBLIC_DATABASE = "PUBLIC_DATABASE"     # ESA DISCOS, UCS Satellite Database
    USER_ENTERED = "USER_ENTERED"           # Configured manually by operator
    SIMULATED_DEMO = "SIMULATED_DEMO"       # Synthetic demonstration scenario baseline
    UNKNOWN = "UNKNOWN"                     # Unspecified / unavailable


@dataclass
class FieldProvenance:
    """Provenance and acquisition timestamp for a specific metadata property."""
    value: Any
    source: ProvenanceType
    updated_utc: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    confidence: str = "ESTIMATED"           # MEASURED, ESTIMATED, ASSUMED, UNKNOWN


@dataclass
class ThrusterSpecification:
    """Physical characteristics of spacecraft reaction control or apogee thrusters."""
    thruster_type: str                      # e.g. "HYDRAZINE_MONOPROPELLANT", "COLD_GAS", "HALL_EFFECT"
    count: int = 1
    thrust_n: float = 10.0                  # Thrust in Newtons
    isp_sec: float = 220.0                  # Specific impulse in seconds
    max_continuous_burn_sec: float = 300.0  # Duty cycle thermal limit
    min_impulse_bit_ns: float = 0.05        # Minimum controllable impulse bit


@dataclass
class FuelEvent:
    """Audit log of a delta-v manoeuvre and estimated propellant consumption."""
    event_id: str
    manoeuvre_id: str
    timestamp_utc: str
    delta_v_mps: float
    estimated_propellant_used_kg: float
    mass_before_kg: float
    mass_after_kg: float
    remaining_propellant_kg: float
    assumptions: str
    is_estimate: bool = True                # Always true: analytical model estimate, not sensor reading


@dataclass
class SpacecraftHardwareRecord:
    """Complete physical specification of a protected or tracked space object."""
    object_id: str
    owner_operator: str = "UNKNOWN"
    spacecraft_model: str = "GENERIC_BUS"
    dimensions_xyz_m: List[float] = field(default_factory=lambda: [2.0, 2.0, 2.0])
    dry_mass_kg: float = 500.0
    initial_propellant_kg: float = 50.0
    current_propellant_kg: float = 50.0
    propellant_type: str = "HYDRAZINE"
    thrusters: List[ThrusterSpecification] = field(default_factory=list)
    fuel_events: List[FuelEvent] = field(default_factory=list)
    field_provenances: Dict[str, Dict[str, Any]] = field(default_factory=dict)

    @property
    def total_mass_kg(self) -> float:
        """Current total spacecraft mass."""
        return self.dry_mass_kg + max(0.0, self.current_propellant_kg)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SpacecraftHardwareRecord":
        thrusters = [ThrusterSpecification(**t) for t in data.get("thrusters", [])]
        events = [FuelEvent(**e) for e in data.get("fuel_events", [])]
        return cls(
            object_id=str(data["object_id"]),
            owner_operator=data.get("owner_operator", "UNKNOWN"),
            spacecraft_model=data.get("spacecraft_model", "GENERIC_BUS"),
            dimensions_xyz_m=data.get("dimensions_xyz_m", [2.0, 2.0, 2.0]),
            dry_mass_kg=float(data.get("dry_mass_kg", 500.0)),
            initial_propellant_kg=float(data.get("initial_propellant_kg", 50.0)),
            current_propellant_kg=float(data.get("current_propellant_kg", 50.0)),
            propellant_type=data.get("propellant_type", "HYDRAZINE"),
            thrusters=thrusters,
            fuel_events=events,
            field_provenances=data.get("field_provenances", {}),
        )
