"""
backend/custom_objects/models.py
================================
Data schemas for user-created satellites and debris pieces.
Strictly distinguishes real catalogue objects from user-created simulation objects,
and keeps visual scaling separate from physical dimensions.
"""

from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from enum import Enum
from typing import Dict, Any, List, Optional, Union

from backend.catalogue.models import OrbitalElements
from backend.resources.models import ThrusterSpecification


class ObjectOrigin(str, Enum):
    REAL_CATALOGUE_OBJECT = "REAL_CATALOGUE_OBJECT"                 # Ingested from Space-Track/CelesTrak
    USER_CREATED_SIMULATION_OBJECT = "USER_CREATED_SIMULATION"      # Created in custom object editor
    IMPORTED_EXTERNAL_OBJECT = "IMPORTED_EXTERNAL"                  # Imported via user CDM or JSON


@dataclass
class VisualAppearance:
    """Configures 3D visual styling in Unreal Engine without modifying physical physics."""
    mesh_template: str = "DEFAULT_CUBESAT"  # CUBESAT, COMM_SAT, DEBRIS_TUMBLER, ROCKET_BODY, SPHERE
    primary_color: List[float] = field(default_factory=lambda: [0.0, 0.85, 1.0, 1.0]) # RGBA
    emissive_multiplier: float = 2.0
    visual_scale_multiplier: float = 1.0   # Visual sizing only; separate from physical dimensions
    show_orbit_path: bool = True
    path_color: List[float] = field(default_factory=lambda: [0.0, 0.85, 1.0, 0.8])


@dataclass
class CustomSatellite:
    """First-class user-created satellite specification."""
    id: str                                # Stable unique ID, e.g. "SAT-CUST-001"
    display_name: str                      # Human-readable name
    epoch_utc: str                         # Reference epoch
    frame: str = "ECI_J2000"               # Coordinate reference frame
    origin: ObjectOrigin = ObjectOrigin.USER_CREATED_SIMULATION_OBJECT
    external_catalog_id: Optional[str] = None
    input_mode: str = "ORBITAL_ELEMENTS"   # "ORBITAL_ELEMENTS" or "CARTESIAN_STATE"

    # Orbital parameters
    orbital_elements: Optional[OrbitalElements] = None
    true_anomaly_deg: Optional[float] = None
    cartesian_position_m: Optional[List[float]] = None
    cartesian_velocity_mps: Optional[List[float]] = None
    covariance_6x6: Optional[List[List[float]]] = None

    # Hardware & Propulsion
    bus_model: str = "CUSTOM_BUS"
    dimensions_xyz_m: List[float] = field(default_factory=lambda: [1.0, 1.0, 1.5])
    dry_mass_kg: float = 300.0
    propellant_kg: float = 30.0
    propellant_type: str = "HYDRAZINE_MONOPROPELLANT"
    thrusters: List[ThrusterSpecification] = field(default_factory=list)

    # Visual Presentation & Simulation State
    visual: VisualAppearance = field(default_factory=VisualAppearance)
    enabled_in_scenario: bool = True
    tags: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "CustomSatellite":
        elems = None
        if data.get("orbital_elements"):
            elems = OrbitalElements(**data["orbital_elements"])
        thrusters = [ThrusterSpecification(**t) for t in data.get("thrusters", [])]
        vis_data = data.get("visual") or {}
        visual = VisualAppearance(**vis_data)
        origin_val = ObjectOrigin(data.get("origin", ObjectOrigin.USER_CREATED_SIMULATION_OBJECT.value))

        return cls(
            id=str(data["id"]),
            display_name=data["display_name"],
            epoch_utc=data["epoch_utc"],
            frame=data.get("frame", "ECI_J2000"),
            origin=origin_val,
            external_catalog_id=data.get("external_catalog_id"),
            input_mode=data.get("input_mode", "ORBITAL_ELEMENTS"),
            orbital_elements=elems,
            true_anomaly_deg=data.get("true_anomaly_deg"),
            cartesian_position_m=data.get("cartesian_position_m"),
            cartesian_velocity_mps=data.get("cartesian_velocity_mps"),
            covariance_6x6=data.get("covariance_6x6"),
            bus_model=data.get("bus_model", "CUSTOM_BUS"),
            dimensions_xyz_m=data.get("dimensions_xyz_m", [1.0, 1.0, 1.5]),
            dry_mass_kg=float(data.get("dry_mass_kg", 300.0)),
            propellant_kg=float(data.get("propellant_kg", 30.0)),
            propellant_type=data.get("propellant_type", "HYDRAZINE_MONOPROPELLANT"),
            thrusters=thrusters,
            visual=visual,
            enabled_in_scenario=data.get("enabled_in_scenario", True),
            tags=data.get("tags", []),
            metadata=data.get("metadata", {}),
        )


@dataclass
class CustomDebris:
    """First-class user-created debris specification."""
    id: str                                # Stable unique ID, e.g. "DEB-CUST-001"
    display_name: str                      # Human-readable name
    epoch_utc: str                         # Reference epoch
    frame: str = "ECI_J2000"               # Coordinate reference frame
    origin: ObjectOrigin = ObjectOrigin.USER_CREATED_SIMULATION_OBJECT
    input_mode: str = "CARTESIAN_STATE"    # "ORBITAL_ELEMENTS" or "CARTESIAN_STATE"

    # State parameters
    orbital_elements: Optional[OrbitalElements] = None
    true_anomaly_deg: Optional[float] = None
    cartesian_position_m: Optional[List[float]] = None
    cartesian_velocity_mps: Optional[List[float]] = None
    covariance_6x6: Optional[List[List[float]]] = None # May be None if unknown; never invent

    # Physical properties (permit unknown, but explicitly labeled)
    mass_kg: Optional[float] = None        # None = UNKNOWN
    dimensions_xyz_m: Optional[List[float]] = None # None = UNKNOWN
    shape_type: str = "IRREGULAR_FRAGMENT" # FRAGMENT, CYLINDER, PLATE, SPHERE, UNKNOWN
    material: str = "ALUMINUM"             # ALUMINUM, TITANIUM, COMPOSITE, UNKNOWN
    tumbling_rate_deg_s: Optional[float] = 15.0
    tumbling_axis: List[float] = field(default_factory=lambda: [0.0, 1.0, 0.0])

    # Visual Presentation & Simulation State
    visual: VisualAppearance = field(default_factory=lambda: VisualAppearance(
        mesh_template="DEBRIS_TUMBLER",
        primary_color=[1.0, 0.58, 0.08, 1.0],
        path_color=[1.0, 0.58, 0.08, 0.8],
    ))
    enabled_in_scenario: bool = True
    tags: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "CustomDebris":
        elems = None
        if data.get("orbital_elements"):
            elems = OrbitalElements(**data["orbital_elements"])
        vis_data = data.get("visual") or {}
        visual = VisualAppearance(**vis_data)
        origin_val = ObjectOrigin(data.get("origin", ObjectOrigin.USER_CREATED_SIMULATION_OBJECT.value))

        return cls(
            id=str(data["id"]),
            display_name=data["display_name"],
            epoch_utc=data["epoch_utc"],
            frame=data.get("frame", "ECI_J2000"),
            origin=origin_val,
            input_mode=data.get("input_mode", "CARTESIAN_STATE"),
            orbital_elements=elems,
            true_anomaly_deg=data.get("true_anomaly_deg"),
            cartesian_position_m=data.get("cartesian_position_m"),
            cartesian_velocity_mps=data.get("cartesian_velocity_mps"),
            covariance_6x6=data.get("covariance_6x6"),
            mass_kg=data.get("mass_kg"),
            dimensions_xyz_m=data.get("dimensions_xyz_m"),
            shape_type=data.get("shape_type", "IRREGULAR_FRAGMENT"),
            material=data.get("material", "ALUMINUM"),
            tumbling_rate_deg_s=data.get("tumbling_rate_deg_s"),
            tumbling_axis=data.get("tumbling_axis", [0.0, 1.0, 0.0]),
            visual=visual,
            enabled_in_scenario=data.get("enabled_in_scenario", True),
            tags=data.get("tags", []),
            metadata=data.get("metadata", {}),
        )
