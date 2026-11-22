"""
tests/test_ml_service.py
========================
Verification test suite for Python ML inference service and data contracts.
Follows Section 10 of the Technical Development Guide:
- Schema serialization and validation (Section 10.1 & 10.2)
- Rejection of malformed, unphysical, and stale messages (Section 10.3)
- Rejection of wrong coordinate frames
- Transparent baseline rule-based risk classification
- Untrusted manoeuvre proposal physical constraint verification
"""

import numpy as np
import pytest

from MLService.schemas import (
    MLInferenceRequest,
    SpaceObjectFeature,
    CURRENT_SCHEMA_VERSION,
)
from MLService.inference_service import MLInferenceService
from D2.manoeuvres.manoeuvre_model import ManoeuvreConstraints


def create_sample_payload():
    return {
        "schema_version": "1.0",
        "scenario_id": "leo_demo_001",
        "epoch_utc": "2026-11-18T13:00:00Z",
        "frame": "DECLARED_ECI_FRAME",
        "timestamp_s": 10.0,
        "primary": {
            "id": "SAT_A",
            "position_m": [6871000.0, 1200.0, 800.0],
            "velocity_mps": [-1.0, 7540.0, 120.0],
            "covariance_6x6": None
        },
        "secondary": {
            "id": "DEBRIS_B",
            "position_m": [6871300.0, 800.0, 900.0],
            "velocity_mps": [-2.0, 7530.0, 100.0],
            "covariance_6x6": None
        },
        "observation_source": "simulated_tracking"
    }


def test_valid_inference_request():
    """Verify processing of valid input payload matching Section 10.1."""
    service = MLInferenceService()
    payload = create_sample_payload()
    resp = service.process_request(payload)

    assert "error" not in resp
    assert resp["schema_version"] == "1.0"
    assert resp["scenario_id"] == "leo_demo_001"
    assert resp["model_version"] == "baseline_rule_based_v1.0"
    assert "prediction" in resp
    assert "recommended_action" in resp
    assert resp["prediction"]["miss_distance_m"] > 0.0
    assert resp["recommended_action"]["frame"] == "RTN"


def test_wrong_frame_rejection():
    """Verify rejection of non-ECI reference frames (e.g. ECEF). (Section 10.3)"""
    service = MLInferenceService()
    payload = create_sample_payload()
    payload["frame"] = "ECEF_EARTH_FIXED"  # Invalid for orbital propagation

    resp = service.process_request(payload)
    assert resp.get("error") == "MALFORMED_PAYLOAD"
    assert "Invalid reference frame" in resp["message"]


def test_stale_timestamp_rejection():
    """Verify rejection of stale or backwards-moving timestamps. (Section 10.3)"""
    service = MLInferenceService()
    p1 = create_sample_payload()
    p1["timestamp_s"] = 100.0
    resp1 = service.process_request(p1)
    assert "error" not in resp1

    # Send message with timestamp older than 100.0 s
    p2 = create_sample_payload()
    p2["timestamp_s"] = 50.0
    resp2 = service.process_request(p2)
    assert resp2.get("error") == "STALE_TIMESTAMP"


def test_unphysical_input_rejection():
    """Verify rejection of NaN or infinite state elements."""
    service = MLInferenceService()
    payload = create_sample_payload()
    payload["primary"]["position_m"] = [np.nan, 0.0, 0.0]

    resp = service.process_request(payload)
    assert resp.get("error") == "UNPHYSICAL_INPUT"


def test_untrusted_proposal_validation_gate():
    """
    Verify safety gate: ML proposed manoeuvre MUST be validated against physical limits.
    (Technical Guide Section 10.3)
    """
    constraints = ManoeuvreConstraints(max_delta_v=5.0)

    # Valid proposal
    valid_proposal = {
        "recommended_action": {
            "type": "PROPOSE_MANEUVER",
            "delta_v_mps": [0.0, -2.0, 0.0],
            "epoch_offset_seconds": 120.0,
            "frame": "RTN"
        }
    }
    is_valid, msg = MLInferenceService.validate_proposal_physics(valid_proposal, constraints)
    assert is_valid is True
    assert msg == "PASSED_PHYSICAL_VALIDATION"

    # Excessive delta-v proposal: must be rejected
    excessive_proposal = {
        "recommended_action": {
            "type": "PROPOSE_MANEUVER",
            "delta_v_mps": [0.0, 15.0, 0.0],  # 15 m/s > 5.0 m/s limit
            "epoch_offset_seconds": 120.0,
            "frame": "RTN"
        }
    }
    is_valid_exc, msg_exc = MLInferenceService.validate_proposal_physics(excessive_proposal, constraints)
    assert is_valid_exc is False
    assert "exceeds max allowed" in msg_exc

    # Negative lead time: must be rejected
    negative_lead_proposal = {
        "recommended_action": {
            "type": "PROPOSE_MANEUVER",
            "delta_v_mps": [0.0, 1.0, 0.0],
            "epoch_offset_seconds": -50.0,  # Negative lead time
            "frame": "RTN"
        }
    }
    is_valid_neg, msg_neg = MLInferenceService.validate_proposal_physics(negative_lead_proposal, constraints)
    assert is_valid_neg is False
    assert "Negative lead time" in msg_neg


if __name__ == "__main__":
    test_valid_inference_request()
    test_wrong_frame_rejection()
    test_stale_timestamp_rejection()
    test_unphysical_input_rejection()
    test_untrusted_proposal_validation_gate()
    print("ALL ML SERVICE TESTS PASSED")
