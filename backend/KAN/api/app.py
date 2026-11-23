"""
backend/KAN/api/app.py
======================
FastAPI REST microservice exposing Kolmogorov-Arnold Network collision risk predictions.
"""

import sys
import os
import json
import warnings
from datetime import datetime, timezone
from typing import Dict, Any, Optional

from fastapi import FastAPI, HTTPException, status
import numpy as np

# Suppress PyTorch batch size 1 std warning
warnings.filterwarnings("ignore", category=UserWarning)

# Ensure backend/KAN/src and repository root are on Python path
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
SRC_DIR = os.path.abspath(os.path.join(CURRENT_DIR, "..", "src"))
REPO_ROOT = os.path.abspath(os.path.join(CURRENT_DIR, "..", "..", ".."))
if SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR)
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from predictor import KANPredictor
from .schemas import (
    HealthResponse,
    ModelInfoResponse,
    ConjunctionPredictionRequest,
    PredictionResponse,
    CreateSatelliteRequest,
    CreateDebrisRequest,
    AcknowledgeAlertRequest,
    ApproveManoeuvreRequest,
)

from backend.catalogue.registry import CatalogueRegistry
from backend.custom_objects.scenario_manager import CustomObjectManager
from backend.conjunction.alert_manager import AlertManager
from backend.conjunction.screener import CoarseScreener
from backend.conjunction.models import ConjunctionCandidate, AlertSeverity
from backend.resources.registry import HardwareRegistry
from backend.decision_support.planner import ResourceAwareManoeuvrePlanner

app = FastAPI(
    title="ICPS Satellite Collision Avoidance Mission Control API",
    description="Comprehensive aerospace microservice providing KAN collision-risk evaluation, real catalogue tracking, custom object management, and decision support.",
    version="2.0.0",
)

# Global singleton instances
_predictor: Optional[KANPredictor] = None
_catalogue_registry: Optional[CatalogueRegistry] = None
_custom_obj_mgr: Optional[CustomObjectManager] = None
_alert_mgr: Optional[AlertManager] = None
_hardware_registry: Optional[HardwareRegistry] = None
_planner: Optional[ResourceAwareManoeuvrePlanner] = None


def get_predictor() -> KANPredictor:
    global _predictor
    if _predictor is None:
        _predictor = KANPredictor()
    return _predictor

def get_catalogue_registry() -> CatalogueRegistry:
    global _catalogue_registry
    if _catalogue_registry is None:
        _catalogue_registry = CatalogueRegistry()
    return _catalogue_registry

def get_custom_object_manager() -> CustomObjectManager:
    global _custom_obj_mgr
    if _custom_obj_mgr is None:
        _custom_obj_mgr = CustomObjectManager()
    return _custom_obj_mgr

def get_alert_manager() -> AlertManager:
    global _alert_mgr
    if _alert_mgr is None:
        _alert_mgr = AlertManager()
        # Seed with initial demo conjunction alert matching CARTOSAT-3 vs SL-16 R/B
        demo_cand = ConjunctionCandidate(
            primary_id="44804",
            secondary_id="22285",
            primary_name="CARTOSAT-3",
            secondary_name="SL-16 R/B (DEBRIS SOURCE)",
            tca_seconds_from_epoch=769.63,
            tca_epoch_utc=datetime.now(timezone.utc).isoformat(),
            miss_distance_m=1563.48,
            relative_speed_mps=14.171,
            primary_r_j2000_m=[7000000.0, 0.0, 0.0],
            primary_v_j2000_mps=[0.0, 7546.0, 0.0],
            secondary_r_j2000_m=[7000000.0, 1563.48, 0.0],
            secondary_v_j2000_mps=[0.0, 7546.0, 14.171],
            collision_probability=3.9575e-14,
            collision_log10_pc=-13.40,
            pc_status="NUMERICAL_OK",
        )
        _alert_mgr.create_or_update_alert(demo_cand)
    return _alert_mgr

def get_hardware_registry() -> HardwareRegistry:
    global _hardware_registry
    if _hardware_registry is None:
        _hardware_registry = HardwareRegistry()
    return _hardware_registry

def get_decision_support_planner() -> ResourceAwareManoeuvrePlanner:
    global _planner
    if _planner is None:
        _planner = ResourceAwareManoeuvrePlanner()
    return _planner


@app.get("/api/v1/health", response_model=HealthResponse, tags=["Monitoring"])
def get_health():
    """Returns the operational status of the KAN prediction service."""
    predictor = get_predictor()
    return HealthResponse(
        status="OK",
        service="KAN Collision Prediction Service",
        model_version=predictor.model_version,
        timestamp_utc=datetime.now(timezone.utc).isoformat(),
    )


@app.get("/api/v1/model-info", response_model=ModelInfoResponse, tags=["Metadata"])
def get_model_info():
    """Returns architecture, training lineage, and evaluation metrics for the active KAN model."""
    predictor = get_predictor()
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    metadata_path = os.path.join(base_dir, "models", "model_metadata.json")

    with open(metadata_path, "r", encoding="utf-8") as f:
        meta = json.load(f)

    return ModelInfoResponse(
        model_name="pykan_esa_kelvins",
        model_version=predictor.model_version,
        framework="PyTorch / PyKAN",
        target=meta.get("target", "risk [base 10 log]"),
        input_features_count=meta.get("n_features", 33),
        architecture=meta.get("kan_architecture", [33, 8, 1]),
        grid_size=meta.get("grid", 5),
        spline_order_k=meta.get("k", 3),
        feature_names=predictor.feature_names,
        training_dataset=meta.get("dataset", "ESA Collision Avoidance Challenge (Kelvins)"),
        test_metrics=meta.get("test_metrics", []),
    )


@app.post("/api/v1/predict/collision-risk", response_model=PredictionResponse, tags=["Inference"])
def predict_collision_risk(req: ConjunctionPredictionRequest):
    """
    Evaluates collision risk (log10 Pc) using the Kolmogorov-Arnold Network.
    
    Supports two input modes:
    1. Direct 33-feature array via 'features_33' (for CDM validation / testing).
    2. Physical state vectors with covariance and CDM observation metadata via 'primary' and 'secondary'.
    """
    predictor = get_predictor()

    # Mode 1: Direct 33-feature vector
    if req.features_33 is not None:
        res = predictor.predict_from_features(req.features_33)
        return PredictionResponse(
            status=res["status"],
            model_name=res.get("model_name", "pykan_esa_kelvins"),
            model_version=res.get("model_version", predictor.model_version),
            predicted_risk_log10=res.get("predicted_risk_log10"),
            estimated_pc=res.get("estimated_pc"),
            estimated_pc_display=res.get("estimated_pc_display"),
            risk_category=res.get("risk_category"),
            underflow=res.get("underflow", False),
            latency_ms=res.get("latency_ms", 0.0),
            fallback_to_physics=False,
            message=res.get("error"),
            provenance=res.get("provenance"),
        )

    # Mode 2: Astrodynamic State Vectors & Covariance
    if req.primary is None or req.secondary is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Request must provide either 'features_33' or both 'primary' and 'secondary' space object states.",
        )

    r_target = np.array(req.primary.position_m, dtype=np.float64)
    v_target = np.array(req.primary.velocity_mps, dtype=np.float64)
    r_chaser = np.array(req.secondary.position_m, dtype=np.float64)
    v_chaser = np.array(req.secondary.velocity_mps, dtype=np.float64)

    cov_target = None
    if req.primary.covariance_6x6 is not None:
        cov_6x6 = np.array(req.primary.covariance_6x6, dtype=np.float64)
        cov_target = cov_6x6[:3, :3]  # Position block

    cov_chaser = None
    if req.secondary.covariance_6x6 is not None:
        cov_6x6 = np.array(req.secondary.covariance_6x6, dtype=np.float64)
        cov_chaser = cov_6x6[:3, :3]  # Position block

    res = predictor.predict_from_icps_state(
        r_target=r_target,
        v_target=v_target,
        r_chaser=r_chaser,
        v_chaser=v_chaser,
        tca_seconds=req.tca_seconds,
        cov_target_3x3=cov_target,
        cov_chaser_3x3=cov_chaser,
        t_span_days=req.t_span_days,
        c_span_days=req.c_span_days,
        chaser_object_type=req.secondary.object_type,
    )

    return PredictionResponse(
        status=res["status"],
        model_name=res.get("model_name", "pykan_esa_kelvins"),
        model_version=res.get("model_version", predictor.model_version),
        predicted_risk_log10=res.get("predicted_risk_log10"),
        estimated_pc=res.get("estimated_pc"),
        estimated_pc_display=res.get("estimated_pc_display"),
        risk_category=res.get("risk_category"),
        underflow=res.get("underflow", False),
        latency_ms=res.get("latency_ms", 0.0),
        missing_features=res.get("missing_features"),
        fallback_to_physics=res.get("fallback_recommended", False),
        message=res.get("error") or res.get("input_derivation_status"),
        provenance=res.get("provenance"),
    )


# =========================================================================
# REAL SATELLITE CATALOGUE ENDPOINTS
# =========================================================================

@app.get("/api/v1/catalogue/search", tags=["Catalogue"])
def search_catalogue(q: str = "", group: Optional[str] = None):
    reg = get_catalogue_registry()
    results = reg.search(query=q, group=group)
    return {"total": len(results), "objects": [o.to_dict() for o in results]}


@app.get("/api/v1/catalogue/tracked", tags=["Catalogue"])
def list_tracked_objects():
    reg = get_catalogue_registry()
    tracked = reg.list_tracked()
    return {"total_tracked": len(tracked), "tracked_objects": [o.to_dict() for o in tracked]}


@app.post("/api/v1/catalogue/track/{object_id}", tags=["Catalogue"])
def track_object(object_id: str):
    reg = get_catalogue_registry()
    success = reg.track_object(object_id)
    if not success:
        raise HTTPException(status_code=404, detail=f"Object {object_id} not found in catalogue.")
    return {"status": "SUCCESS", "object_id": object_id, "is_tracked": True}


@app.post("/api/v1/catalogue/untrack/{object_id}", tags=["Catalogue"])
def untrack_object(object_id: str):
    reg = get_catalogue_registry()
    success = reg.untrack_object(object_id)
    if not success:
        raise HTTPException(status_code=404, detail=f"Object {object_id} not in tracked list.")
    return {"status": "SUCCESS", "object_id": object_id, "is_tracked": False, "note": "Untracked locally; preserved in catalogue."}


# =========================================================================
# CUSTOM SATELLITES AND DEBRIS ENDPOINTS
# =========================================================================

@app.get("/api/v1/custom-objects/scenario", tags=["Custom Objects"])
def get_custom_scenario():
    mgr = get_custom_object_manager()
    return mgr.active_scenario.to_dict()


@app.post("/api/v1/custom-objects/satellites", tags=["Custom Objects"])
def create_custom_satellite(req: CreateSatelliteRequest):
    mgr = get_custom_object_manager()
    try:
        sat = mgr.create_satellite(
            display_name=req.display_name,
            input_mode=req.input_mode,
            orbital_elements_dict=req.orbital_elements,
            true_anomaly_deg=req.true_anomaly_deg,
            position_m=req.position_m,
            velocity_mps=req.velocity_mps,
            dry_mass_kg=req.dry_mass_kg,
            propellant_kg=req.propellant_kg,
            bus_model=req.bus_model,
            satellite_id=req.satellite_id,
        )
        return {"status": "CREATED", "satellite": sat.to_dict()}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/api/v1/custom-objects/debris", tags=["Custom Objects"])
def create_custom_debris(req: CreateDebrisRequest):
    mgr = get_custom_object_manager()
    try:
        deb = mgr.create_debris(
            display_name=req.display_name,
            input_mode=req.input_mode,
            position_m=req.position_m,
            velocity_mps=req.velocity_mps,
            orbital_elements_dict=req.orbital_elements,
            true_anomaly_deg=req.true_anomaly_deg,
            mass_kg=req.mass_kg,
            dimensions_xyz_m=req.dimensions_xyz_m,
            shape_type=req.shape_type,
            material=req.material,
            debris_id=req.debris_id,
        )
        return {"status": "CREATED", "debris": deb.to_dict()}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/api/v1/custom-objects/reset", tags=["Custom Objects"])
def reset_custom_scenario():
    mgr = get_custom_object_manager()
    mgr.reset_to_original()
    return {"status": "SUCCESS", "message": "Custom scenario reset to original state; baseline demonstration preserved."}


# =========================================================================
# CONJUNCTION SCREENING AND ALERTS ENDPOINTS
# =========================================================================

@app.get("/api/v1/conjunction/alerts", tags=["Conjunction & Alerts"])
def list_conjunction_alerts():
    alert_mgr = get_alert_manager()
    alerts = alert_mgr.list_alerts()
    return {"total_alerts": len(alerts), "alerts": [a.to_dict() for a in alerts]}


@app.post("/api/v1/conjunction/alerts/{alert_id}/acknowledge", tags=["Conjunction & Alerts"])
def acknowledge_conjunction_alert(alert_id: str, req: AcknowledgeAlertRequest):
    alert_mgr = get_alert_manager()
    success = alert_mgr.acknowledge_alert(alert_id, operator=req.operator, notes=req.notes)
    if not success:
        raise HTTPException(status_code=404, detail=f"Alert {alert_id} not found.")
    return {"status": "SUCCESS", "alert_id": alert_id, "state": "ACKNOWLEDGED"}


# =========================================================================
# HARDWARE & RESOURCE REGISTRY ENDPOINTS
# =========================================================================

@app.get("/api/v1/resources/{object_id}", tags=["Resources"])
def get_hardware_resource(object_id: str):
    hw_reg = get_hardware_registry()
    rec = hw_reg.get_record(object_id)
    if not rec:
        raise HTTPException(status_code=404, detail=f"No hardware record for object {object_id}")
    return rec.to_dict()


# =========================================================================
# DECISION SUPPORT ENDPOINTS
# =========================================================================

@app.post("/api/v1/decision-support/plan/{primary_id}/{secondary_id}", tags=["Decision Support"])
def plan_avoidance_manoeuvres(primary_id: str, secondary_id: str):
    hw_reg = get_hardware_registry()
    planner = get_decision_support_planner()
    hw = hw_reg.get_record(primary_id)

    alert_mgr = get_alert_manager()
    candidate = None
    for a in alert_mgr.list_alerts():
        if a.candidate.primary_id == primary_id and a.candidate.secondary_id == secondary_id:
            candidate = a.candidate
            break

    if not candidate:
        candidate = ConjunctionCandidate(
            primary_id=primary_id,
            secondary_id=secondary_id,
            primary_name="PRIMARY_SAT",
            secondary_name="SECONDARY_OBJ",
            tca_seconds_from_epoch=769.63,
            tca_epoch_utc=datetime.now(timezone.utc).isoformat(),
            miss_distance_m=1563.48,
            relative_speed_mps=14.171,
            primary_r_j2000_m=[7000000.0, 0.0, 0.0],
            primary_v_j2000_mps=[0.0, 7546.0, 0.0],
            secondary_r_j2000_m=[7000000.0, 1563.48, 0.0],
            secondary_v_j2000_mps=[0.0, 7546.0, 14.171],
            collision_probability=3.9575e-14,
        )

    proposal = planner.plan_avoidance_options(conjunction=candidate, hardware=hw)
    return proposal.to_dict()

