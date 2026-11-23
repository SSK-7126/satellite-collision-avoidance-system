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

# Ensure backend/KAN/src is on Python path
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
SRC_DIR = os.path.abspath(os.path.join(CURRENT_DIR, "..", "src"))
if SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR)

from predictor import KANPredictor
from .schemas import (
    HealthResponse,
    ModelInfoResponse,
    ConjunctionPredictionRequest,
    PredictionResponse,
)

app = FastAPI(
    title="ICPS KAN Collision-Risk Prediction Service",
    description="Empirical AI prediction service evaluating orbital conjunction risk via Kolmogorov-Arnold Networks.",
    version="1.0.0",
)

# Global singleton predictor instance
_predictor: Optional[KANPredictor] = None


def get_predictor() -> KANPredictor:
    global _predictor
    if _predictor is None:
        _predictor = KANPredictor()
    return _predictor


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
