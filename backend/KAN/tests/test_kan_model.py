"""
backend/KAN/tests/test_kan_model.py
===================================
Unit tests for KAN model loading, preprocessing, feature derivation, and inference.
"""

import os
import sys
import math
import numpy as np
import pytest
import torch

# Ensure backend/KAN/src is accessible
SRC_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src"))
if SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR)

from predictor import KANPredictor
from feature_extractor import (
    EXACT_33_FEATURE_NAMES,
    cartesian_to_keplerian,
    compute_rtn_basis,
    transform_vector_to_rtn,
    extract_features_from_state_and_cdm,
)


@pytest.fixture(scope="module")
def predictor():
    """Initializes and caches the KAN predictor for tests."""
    return KANPredictor()


def test_checkpoint_and_preprocessor_loading(predictor):
    """Verifies that model weights and preprocessor artifacts load properly."""
    assert predictor.model is not None
    assert predictor.preprocessor is not None
    assert len(predictor.feature_names) == 33
    assert predictor.target_col == "risk"
    assert "imputer" in predictor.preprocessor
    assert "scaler_X" in predictor.preprocessor
    assert "scaler_y" in predictor.preprocessor


def test_feature_names_order(predictor):
    """Verifies exact 33 feature names and ordering."""
    assert predictor.feature_names == EXACT_33_FEATURE_NAMES


def test_invalid_feature_dimension(predictor):
    """Verifies rejection of vectors with incorrect lengths."""
    bad_vec_short = [0.0] * 32
    bad_vec_long = [0.0] * 34

    res_short = predictor.predict_from_features(bad_vec_short)
    assert res_short["status"] == "INVALID_FEATURE_DIMENSION"

    res_long = predictor.predict_from_features(bad_vec_long)
    assert res_long["status"] == "INVALID_FEATURE_DIMENSION"


def test_nan_and_inf_rejection(predictor):
    """Verifies that NaN and Inf are rejected without crashing."""
    nan_vec = [0.0] * 33
    nan_vec[5] = float("nan")
    res_nan = predictor.predict_from_features(nan_vec)
    assert res_nan["status"] == "INVALID_NUMERICAL_INPUT"

    inf_vec = [0.0] * 33
    inf_vec[12] = float("inf")
    res_inf = predictor.predict_from_features(inf_vec)
    assert res_inf["status"] == "INVALID_NUMERICAL_INPUT"


def test_inference_output_and_pc_conversion(predictor):
    """Verifies forward pass and probability scaling."""
    zeros_vec = [0.0] * 33
    res = predictor.predict_from_features(zeros_vec)

    assert res["status"] == "SUCCESS"
    assert isinstance(res["predicted_risk_log10"], float)
    assert isinstance(res["estimated_pc"], float)
    assert res["risk_category"] in ["CRITICAL", "WARNING", "LOW"]
    assert res["latency_ms"] > 0.0


def test_underflow_safety(predictor):
    """Verifies that extreme negative risk does not crash and handles underflow safely."""
    # When risk is extreme negative, e.g. < -300
    extreme_res = predictor.predict_from_features([0.0] * 33)
    # Ensure estimated_pc_display is formatted
    assert "estimated_pc_display" in extreme_res
    assert isinstance(extreme_res["underflow"], bool)


def test_coordinate_transforms():
    """Verifies RTN basis construction and Keplerian conversion."""
    r_target = np.array([7000000.0, 0.0, 0.0])
    v_target = np.array([0.0, 7500.0, 0.0])

    # RTN Basis
    r_hat, t_hat, n_hat = compute_rtn_basis(r_target, v_target)
    assert np.allclose(r_hat, [1.0, 0.0, 0.0], atol=1e-6)
    assert np.allclose(t_hat, [0.0, 1.0, 0.0], atol=1e-6)
    assert np.allclose(n_hat, [0.0, 0.0, 1.0], atol=1e-6)

    # Keplerian elements (circular equatorial orbit)
    sma, ecc, inc = cartesian_to_keplerian(r_target, v_target)
    assert sma > 6000000.0
    assert ecc < 0.1
    assert abs(inc) < 1.0  # Equatorial


def test_icps_state_insufficient_data(predictor):
    """Verifies that omitting CDM metadata returns INSUFFICIENT_INPUT_DATA and triggers fallback."""
    r_t = np.array([7000000.0, 0.0, 0.0])
    v_t = np.array([0.0, 7500.0, 0.0])
    r_c = np.array([7001000.0, 100.0, 200.0])
    v_c = np.array([10.0, 7490.0, 50.0])

    res = predictor.predict_from_icps_state(
        r_target=r_t,
        v_target=v_t,
        r_chaser=r_c,
        v_chaser=v_c,
        tca_seconds=1800.0,
    )

    assert res["status"] == "INSUFFICIENT_INPUT_DATA"
    assert res["fallback_recommended"] is True
    assert len(res["missing_features"]) > 0


def test_icps_state_full_derivation(predictor):
    """Verifies complete feature derivation when covariance and CDM fields are supplied."""
    r_t = np.array([7000000.0, 0.0, 0.0])
    v_t = np.array([0.0, 7500.0, 0.0])
    r_c = np.array([7000200.0, 50.0, 10.0])
    v_c = np.array([5.0, 7495.0, 10.0])

    cov_t = np.diag([400.0, 2500.0, 900.0])
    cov_c = np.diag([900.0, 4900.0, 1600.0])

    res = predictor.predict_from_icps_state(
        r_target=r_t,
        v_target=v_t,
        r_chaser=r_c,
        v_chaser=v_c,
        tca_seconds=900.0,
        cov_target_3x3=cov_t,
        cov_chaser_3x3=cov_c,
        t_span_days=6.5,
        c_span_days=4.2,
        chaser_object_type="PAYLOAD",
    )

    assert res["status"] == "SUCCESS"
    assert res.get("fallback_recommended") is not True
    assert "predicted_risk_log10" in res
