"""
MLService/schemas.py
====================
Versioned JSON / Data Transfer Schemas for Python ML Inference Service.
Strictly following Section 10 of the Satellite Anti-Collision Technical Guide.
"""

from dataclasses import dataclass, field, asdict
from typing import List, Dict, Any, Optional
import json


ALLOWED_FRAMES = ["DECLARED_ECI_FRAME", "ECI_J2000", "ECI", "GCRF"]
CURRENT_SCHEMA_VERSION = "1.0"


@dataclass
class SpaceObjectFeature:
    """Features of a space object received for ML inference."""
    id: str
    position_m: List[float]       # 3 elements
    velocity_mps: List[float]     # 3 elements
    covariance_6x6: Optional[List[List[float]]] = None

    def validate(self):
        if len(self.position_m) != 3:
            raise ValueError(f"position_m must have 3 elements, got {len(self.position_m)}")
        if len(self.velocity_mps) != 3:
            raise ValueError(f"velocity_mps must have 3 elements, got {len(self.velocity_mps)}")
        if self.covariance_6x6 is not None:
            if len(self.covariance_6x6) != 6 or any(len(row) != 6 for row in self.covariance_6x6):
                raise ValueError("covariance_6x6 must have dimensions 6x6")


@dataclass
class MLInferenceRequest:
    """
    Standardized ML Inference Request Payload. (Technical Guide Section 10.1)
    """
    schema_version: str
    scenario_id: str
    epoch_utc: str
    frame: str
    primary: SpaceObjectFeature
    secondary: SpaceObjectFeature
    observation_source: str = "simulated_tracking"
    timestamp_s: float = 0.0

    def validate(self):
        if self.schema_version != CURRENT_SCHEMA_VERSION:
            raise ValueError(f"Unsupported schema_version '{self.schema_version}', expected '{CURRENT_SCHEMA_VERSION}'")
        if self.frame not in ALLOWED_FRAMES:
            raise ValueError(f"Invalid reference frame '{self.frame}'. Allowed frames: {ALLOWED_FRAMES}")
        if not self.scenario_id or not self.scenario_id.strip():
            raise ValueError("scenario_id cannot be empty")
        self.primary.validate()
        self.secondary.validate()

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "MLInferenceRequest":
        return cls(
            schema_version=data.get("schema_version", ""),
            scenario_id=data.get("scenario_id", ""),
            epoch_utc=data.get("epoch_utc", ""),
            frame=data.get("frame", ""),
            primary=SpaceObjectFeature(**data["primary"]),
            secondary=SpaceObjectFeature(**data["secondary"]),
            observation_source=data.get("observation_source", "simulated_tracking"),
            timestamp_s=float(data.get("timestamp_s", 0.0))
        )

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class RecommendedAction:
    """Recommended avoidance action from ML service. (Technical Guide Section 10.2)"""
    type: str                     # 'PROPOSE_MANEUVER' or 'MONITOR'
    epoch_offset_seconds: float    # Lead time offset
    delta_v_mps: List[float]       # [dv_R, dv_T, dv_N] in RTN
    frame: str = "RTN"


@dataclass
class PredictionOutput:
    """Predicted conjunction metrics from ML service. (Technical Guide Section 10.2)"""
    tca_seconds: float
    miss_distance_m: float
    collision_probability: Optional[float]
    risk_class: str               # 'LOW', 'MEDIUM', 'HIGH', 'CRITICAL'


@dataclass
class MLInferenceResponse:
    """
    Standardized ML Inference Response Payload. (Technical Guide Section 10.2)
    """
    schema_version: str
    scenario_id: str
    prediction: PredictionOutput
    recommended_action: RecommendedAction
    model_version: str = "baseline_rule_based_v1.0"
    is_validated: bool = False
    validation_status: str = "UNVALIDATED_PROPOSAL"

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)
