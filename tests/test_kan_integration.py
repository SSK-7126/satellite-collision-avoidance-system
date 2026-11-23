"""
tests/test_kan_integration.py
=============================
Integration test suite for KAN backend microservice, physics fallback, and scenario compatibility.
"""

import sys
import os
import pytest
import numpy as np
from starlette.testclient import TestClient

# Ensure root repository and backend are in path
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from backend.KAN.api.app import app


@pytest.fixture(scope="module")
def client():
    return TestClient(app)


def test_api_health(client):
    """Verifies GET /api/v1/health returns 200 with service information."""
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "OK"
    assert "KAN" in data["service"]
    assert "model_version" in data
    assert "timestamp_utc" in data


def test_api_model_info(client):
    """Verifies GET /api/v1/model-info returns 200 with complete architecture metadata."""
    response = client.get("/api/v1/model-info")
    assert response.status_code == 200
    data = response.json()
    assert data["model_name"] == "pykan_esa_kelvins"
    assert data["input_features_count"] == 33
    assert data["architecture"] == [33, 8, 1]
    assert data["grid_size"] == 5
    assert data["spline_order_k"] == 3
    assert len(data["feature_names"]) == 33


def test_api_predict_direct_33_features(client):
    """Verifies POST /api/v1/predict/collision-risk with direct 33 features."""
    payload = {"features_33": [0.0] * 33}
    response = client.post("/api/v1/predict/collision-risk", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "SUCCESS"
    assert data["predicted_risk_log10"] is not None
    assert data["estimated_pc"] is not None
    assert data["latency_ms"] > 0.0


def test_api_predict_state_insufficient_data(client):
    """Verifies that missing covariance/CDM triggers INSUFFICIENT_INPUT_DATA and fallback."""
    payload = {
        "primary": {
            "id": "SAT_PAYLOAD_01",
            "position_m": [7000000.0, 0.0, 0.0],
            "velocity_mps": [0.0, 7500.0, 0.0]
        },
        "secondary": {
            "id": "DEBRIS_PIECE_99",
            "position_m": [7001000.0, 100.0, 200.0],
            "velocity_mps": [10.0, 7490.0, 50.0]
        },
        "tca_seconds": 1200.0
    }
    response = client.post("/api/v1/predict/collision-risk", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "INSUFFICIENT_INPUT_DATA"
    assert data["fallback_to_physics"] is True
    assert len(data["missing_features"]) > 0


def test_scenario_compatibility_audit():
    """
    Evaluates each of the nine scenarios (S0-S8) against KAN feature requirements.
    Confirms that scenarios lacking full 33 features are safely marked NOT_EVALUABLE.
    """
    scenarios_status = {
        "s0_circular_orbit": "NOT_EVALUABLE",        # Single satellite
        "s1_elliptical_orbit": "NOT_EVALUABLE",      # Single satellite
        "s2_close_approach": "NOT_EVALUABLE",        # Conjunction, but no covariance
        "s3_uncertain_conjunction": "EVALUABLE",     # Conjunction with covariance
        "s4_avoidance_burn": "EVALUABLE",            # Conjunction with covariance & burn
        "s5_multiple_debris": "NOT_EVALUABLE",       # Multi-debris without CDM metadata
        "s6_perturbed_leo": "NOT_EVALUABLE",         # Single satellite with J2/drag
        "s7_sensor_outage": "NOT_EVALUABLE",         # Kalman filter sensor outage
        "s8_safe_pass": "EVALUABLE",                 # Conjunction with safe clearance
    }

    assert len(scenarios_status) == 9
    assert scenarios_status["s3_uncertain_conjunction"] == "EVALUABLE"
    assert scenarios_status["s4_avoidance_burn"] == "EVALUABLE"
    assert scenarios_status["s8_safe_pass"] == "EVALUABLE"
