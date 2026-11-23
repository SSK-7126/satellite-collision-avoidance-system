"""
backend/KAN/api/schemas.py
==========================
Pydantic v2 Request/Response Data Validation Schemas for KAN REST Service.
"""

from typing import List, Dict, Any, Optional, Union
from pydantic import BaseModel, Field, field_validator
import math


class HealthResponse(BaseModel):
    status: str = Field(default="OK", description="Service health state")
    service: str = Field(default="KAN Collision Prediction Service")
    model_version: str = Field(default="pykan_esa_kelvins_v1.0")
    timestamp_utc: str


class ModelInfoResponse(BaseModel):
    model_name: str
    model_version: str
    framework: str
    target: str
    input_features_count: int
    architecture: List[int]
    grid_size: int
    spline_order_k: int
    feature_names: List[str]
    training_dataset: str
    test_metrics: List[Dict[str, Any]]


class SpaceObjectState(BaseModel):
    id: str = Field(description="Unique object identifier")
    position_m: List[float] = Field(description="Cartesian position vector [x, y, z] in meters")
    velocity_mps: List[float] = Field(description="Cartesian velocity vector [vx, vy, vz] in m/s")
    covariance_6x6: Optional[List[List[float]]] = Field(
        default=None,
        description="Optional 6x6 covariance matrix in (m, m/s)"
    )
    object_type: Optional[str] = Field(
        default=None,
        description="Object classification: PAYLOAD, ROCKET BODY, DEBRIS, UNKNOWN"
    )

    @field_validator("position_m")
    @classmethod
    def validate_position(cls, v: List[float]) -> List[float]:
        if len(v) != 3:
            raise ValueError(f"position_m must contain exactly 3 coordinates, got {len(v)}")
        for val in v:
            if math.isnan(val) or math.isinf(val):
                raise ValueError("position_m contains NaN or infinite values")
        return v

    @field_validator("velocity_mps")
    @classmethod
    def validate_velocity(cls, v: List[float]) -> List[float]:
        if len(v) != 3:
            raise ValueError(f"velocity_mps must contain exactly 3 coordinates, got {len(v)}")
        for val in v:
            if math.isnan(val) or math.isinf(val):
                raise ValueError("velocity_mps contains NaN or infinite values")
        return v

    @field_validator("covariance_6x6")
    @classmethod
    def validate_covariance(cls, v: Optional[List[List[float]]]) -> Optional[List[List[float]]]:
        if v is not None:
            if len(v) != 6 or any(len(row) != 6 for row in v):
                raise ValueError("covariance_6x6 must be a 6x6 matrix")
            for row in v:
                for val in row:
                    if math.isnan(val) or math.isinf(val):
                        raise ValueError("covariance_6x6 contains NaN or infinite values")
        return v


class ConjunctionPredictionRequest(BaseModel):
    schema_version: str = Field(default="1.0", description="Schema version")
    scenario_id: Optional[str] = Field(default=None, description="Identifier for test or mission scenario")
    epoch_utc: Optional[str] = Field(default=None, description="ISO-8601 timestamp")
    frame: str = Field(default="ECI_J2000", description="Inertial reference frame")
    tca_seconds: float = Field(default=0.0, description="Seconds until TCA from epoch")
    primary: Optional[SpaceObjectState] = Field(default=None, description="Primary spacecraft state")
    secondary: Optional[SpaceObjectState] = Field(default=None, description="Secondary (chaser/debris) state")
    t_span_days: Optional[float] = Field(default=None, description="Primary tracking observation span in days")
    c_span_days: Optional[float] = Field(default=None, description="Secondary tracking observation span in days")
    features_33: Optional[List[float]] = Field(default=None, description="Direct 33-feature vector for testing")

    @field_validator("features_33")
    @classmethod
    def validate_direct_features(cls, v: Optional[List[float]]) -> Optional[List[float]]:
        if v is not None:
            if len(v) != 33:
                raise ValueError(f"features_33 must contain exactly 33 elements, got {len(v)}")
            for val in v:
                if math.isnan(val) or math.isinf(val):
                    raise ValueError("features_33 contains NaN or infinite values")
        return v


class PredictionResponse(BaseModel):
    status: str = Field(description="SUCCESS, INSUFFICIENT_INPUT_DATA, INVALID_FEATURE_DIMENSION, ERROR")
    model_name: str
    model_version: str
    predicted_risk_log10: Optional[float] = Field(default=None, description="Continuous log10(Pc) output")
    estimated_pc: Optional[float] = Field(default=None, description="Physical Pc = 10^risk (0.0 if underflow)")
    estimated_pc_display: Optional[str] = Field(default=None, description="Human/telemetry readable Pc")
    risk_category: Optional[str] = Field(default=None, description="CRITICAL, WARNING, LOW")
    underflow: bool = Field(default=False, description="Flag indicating Pc < 1e-300 underflow")
    latency_ms: float = Field(description="Inference execution latency in milliseconds")
    missing_features: Optional[List[str]] = Field(default=None, description="List of unprovided features")
    fallback_to_physics: bool = Field(default=False, description="True if physics engine should be used")
    message: Optional[str] = Field(default=None, description="Status or error message")
    provenance: Optional[Dict[str, Any]] = Field(default=None, description="Model lineage metadata")


class CreateSatelliteRequest(BaseModel):
    display_name: str
    input_mode: str = "ORBITAL_ELEMENTS"
    orbital_elements: Optional[Dict[str, float]] = None
    true_anomaly_deg: float = 0.0
    position_m: Optional[List[float]] = None
    velocity_mps: Optional[List[float]] = None
    dry_mass_kg: float = 300.0
    propellant_kg: float = 30.0
    bus_model: str = "CUSTOM_BUS"
    satellite_id: Optional[str] = None


class CreateDebrisRequest(BaseModel):
    display_name: str
    input_mode: str = "CARTESIAN_STATE"
    position_m: Optional[List[float]] = None
    velocity_mps: Optional[List[float]] = None
    orbital_elements: Optional[Dict[str, float]] = None
    true_anomaly_deg: float = 0.0
    mass_kg: Optional[float] = None
    dimensions_xyz_m: Optional[List[float]] = None
    shape_type: str = "IRREGULAR_FRAGMENT"
    material: str = "ALUMINUM"
    debris_id: Optional[str] = None


class AcknowledgeAlertRequest(BaseModel):
    operator: str = "OPERATOR"
    notes: str = ""


class ApproveManoeuvreRequest(BaseModel):
    option_id: str
    operator_id: str = "FLIGHT_DIRECTOR"
    notes: str = ""

