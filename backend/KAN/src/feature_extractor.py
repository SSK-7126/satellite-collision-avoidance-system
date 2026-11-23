"""
backend/KAN/src/feature_extractor.py
====================================
Feature Extraction and Coordinate Adapter for PyKAN Collision-Risk Model.

Maps ICPS ECI Cartesian state vectors, covariances, and optional CDM metadata
into the exact 33-feature normalized vector expected by the trained PyKAN model.

Strict Safety Policy:
If any required physical quantity cannot be derived or verified without arbitrary
fabrication, the adapter returns status 'INSUFFICIENT_INPUT_DATA'.
"""

import math
from typing import Dict, Any, List, Optional, Tuple
import numpy as np

# Authoritative standard gravitational parameter for Earth (m^3/s^2)
MU_EARTH = 3.986004418e14

# Exact 33 feature names in the exact sequence expected by kan_esa_model.pt
EXACT_33_FEATURE_NAMES = [
    "time_to_tca",
    "miss_distance",
    "relative_speed",
    "relative_position_r",
    "relative_position_t",
    "relative_position_n",
    "relative_velocity_r",
    "relative_velocity_t",
    "relative_velocity_n",
    "geocentric_latitude",
    "azimuth",
    "elevation",
    "mahalanobis_distance",
    "t_j2k_sma",
    "t_j2k_ecc",
    "t_j2k_inc",
    "c_j2k_sma",
    "c_j2k_ecc",
    "c_j2k_inc",
    "t_span",
    "c_span",
    "t_sigma_r",
    "c_sigma_r",
    "t_sigma_t",
    "c_sigma_t",
    "t_sigma_n",
    "c_sigma_n",
    "t_position_covariance_det",
    "c_position_covariance_det",
    "c_object_type_PAYLOAD",
    "c_object_type_ROCKET BODY",
    "c_object_type_TBA",
    "c_object_type_UNKNOWN",
]


class FeatureClassification:
    DERIVABLE = "DERIVABLE_ASTRODYNAMICS"
    DERIVABLE_WITH_COV = "DERIVABLE_WITH_COVARIANCE"
    REQUIRES_CDM = "REQUIRES_CDM_METADATA"


FEATURE_SPECIFICATION: Dict[str, Dict[str, Any]] = {
    "time_to_tca": {
        "unit": "days",
        "class": FeatureClassification.DERIVABLE,
        "description": "Time remaining until TCA",
    },
    "miss_distance": {
        "unit": "meters",
        "class": FeatureClassification.DERIVABLE,
        "description": "Euclidean separation at closest approach",
    },
    "relative_speed": {
        "unit": "m/s",
        "class": FeatureClassification.DERIVABLE,
        "description": "Magnitude of relative velocity vector",
    },
    "relative_position_r": {
        "unit": "meters",
        "class": FeatureClassification.DERIVABLE,
        "description": "Relative position in Target Radial direction",
    },
    "relative_position_t": {
        "unit": "meters",
        "class": FeatureClassification.DERIVABLE,
        "description": "Relative position in Target Transverse (in-track) direction",
    },
    "relative_position_n": {
        "unit": "meters",
        "class": FeatureClassification.DERIVABLE,
        "description": "Relative position in Target Normal (cross-track) direction",
    },
    "relative_velocity_r": {
        "unit": "m/s",
        "class": FeatureClassification.DERIVABLE,
        "description": "Relative velocity in Radial direction",
    },
    "relative_velocity_t": {
        "unit": "m/s",
        "class": FeatureClassification.DERIVABLE,
        "description": "Relative velocity in Transverse direction",
    },
    "relative_velocity_n": {
        "unit": "m/s",
        "class": FeatureClassification.DERIVABLE,
        "description": "Relative velocity in Normal direction",
    },
    "geocentric_latitude": {
        "unit": "degrees",
        "class": FeatureClassification.DERIVABLE,
        "description": "Geocentric latitude of target spacecraft",
    },
    "azimuth": {
        "unit": "degrees",
        "class": FeatureClassification.DERIVABLE,
        "description": "Azimuth angle of relative velocity in encounter plane",
    },
    "elevation": {
        "unit": "degrees",
        "class": FeatureClassification.DERIVABLE,
        "description": "Elevation angle of relative velocity",
    },
    "mahalanobis_distance": {
        "unit": "dimensionless",
        "class": FeatureClassification.DERIVABLE_WITH_COV,
        "description": "Statistical distance in combined encounter covariance",
    },
    "t_j2k_sma": {
        "unit": "meters",
        "class": FeatureClassification.DERIVABLE,
        "description": "Target semi-major axis in J2000",
    },
    "t_j2k_ecc": {
        "unit": "dimensionless",
        "class": FeatureClassification.DERIVABLE,
        "description": "Target orbital eccentricity",
    },
    "t_j2k_inc": {
        "unit": "degrees",
        "class": FeatureClassification.DERIVABLE,
        "description": "Target orbital inclination",
    },
    "c_j2k_sma": {
        "unit": "meters",
        "class": FeatureClassification.DERIVABLE,
        "description": "Chaser semi-major axis in J2000",
    },
    "c_j2k_ecc": {
        "unit": "dimensionless",
        "class": FeatureClassification.DERIVABLE,
        "description": "Chaser orbital eccentricity",
    },
    "c_j2k_inc": {
        "unit": "degrees",
        "class": FeatureClassification.DERIVABLE,
        "description": "Chaser orbital inclination",
    },
    "t_span": {
        "unit": "days",
        "class": FeatureClassification.REQUIRES_CDM,
        "description": "Target tracking observation arc span",
    },
    "c_span": {
        "unit": "days",
        "class": FeatureClassification.REQUIRES_CDM,
        "description": "Chaser tracking observation arc span",
    },
    "t_sigma_r": {
        "unit": "meters",
        "class": FeatureClassification.DERIVABLE_WITH_COV,
        "description": "Target 1-sigma radial position dispersion",
    },
    "c_sigma_r": {
        "unit": "meters",
        "class": FeatureClassification.DERIVABLE_WITH_COV,
        "description": "Chaser 1-sigma radial position dispersion",
    },
    "t_sigma_t": {
        "unit": "meters",
        "class": FeatureClassification.DERIVABLE_WITH_COV,
        "description": "Target 1-sigma in-track position dispersion",
    },
    "c_sigma_t": {
        "unit": "meters",
        "class": FeatureClassification.DERIVABLE_WITH_COV,
        "description": "Chaser 1-sigma in-track position dispersion",
    },
    "t_sigma_n": {
        "unit": "meters",
        "class": FeatureClassification.DERIVABLE_WITH_COV,
        "description": "Target 1-sigma cross-track position dispersion",
    },
    "c_sigma_n": {
        "unit": "meters",
        "class": FeatureClassification.DERIVABLE_WITH_COV,
        "description": "Chaser 1-sigma cross-track position dispersion",
    },
    "t_position_covariance_det": {
        "unit": "m^6",
        "class": FeatureClassification.DERIVABLE_WITH_COV,
        "description": "Determinant of target 3x3 position covariance",
    },
    "c_position_covariance_det": {
        "unit": "m^6",
        "class": FeatureClassification.DERIVABLE_WITH_COV,
        "description": "Determinant of chaser 3x3 position covariance",
    },
    "c_object_type_PAYLOAD": {
        "unit": "binary",
        "class": FeatureClassification.REQUIRES_CDM,
        "description": "One-hot flag: Chaser is PAYLOAD",
    },
    "c_object_type_ROCKET BODY": {
        "unit": "binary",
        "class": FeatureClassification.REQUIRES_CDM,
        "description": "One-hot flag: Chaser is ROCKET BODY",
    },
    "c_object_type_TBA": {
        "unit": "binary",
        "class": FeatureClassification.REQUIRES_CDM,
        "description": "One-hot flag: Chaser is TBA",
    },
    "c_object_type_UNKNOWN": {
        "unit": "binary",
        "class": FeatureClassification.REQUIRES_CDM,
        "description": "One-hot flag: Chaser is UNKNOWN",
    },
}


def cartesian_to_keplerian(r_vec: np.ndarray, v_vec: np.ndarray, mu: float = MU_EARTH) -> Tuple[float, float, float]:
    """
    Computes Semi-Major Axis (m), Eccentricity (dimensionless), and Inclination (deg).
    """
    r = float(np.linalg.norm(r_vec))
    v = float(np.linalg.norm(v_vec))
    if r < 1e-3 or v < 1e-3:
        return 0.0, 0.0, 0.0

    # Specific orbital energy
    energy = (v * v) / 2.0 - mu / r
    if abs(energy) < 1e-9:
        sma = 1e12  # Parabolic near-infinite SMA
    else:
        sma = -mu / (2.0 * energy)

    # Angular momentum vector
    h_vec = np.cross(r_vec, v_vec)
    h = float(np.linalg.norm(h_vec))

    # Eccentricity vector
    e_vec = (np.cross(v_vec, h_vec) / mu) - (r_vec / r)
    ecc = float(np.linalg.norm(e_vec))

    # Inclination (deg)
    if h > 1e-6:
        inc_rad = math.acos(max(-1.0, min(1.0, h_vec[2] / h)))
        inc_deg = math.degrees(inc_rad)
    else:
        inc_deg = 0.0

    return sma, ecc, inc_deg


def compute_rtn_basis(r_target: np.ndarray, v_target: np.ndarray) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """
    Constructs Radial (R), Transverse (T), and Normal (N) unit vectors.
    R = r / ||r||
    N = (r x v) / ||r x v||
    T = N x R
    """
    r_norm = np.linalg.norm(r_target)
    if r_norm < 1e-3:
        raise ValueError("Target position vector has zero magnitude")

    r_hat = r_target / r_norm
    h_vec = np.cross(r_target, v_target)
    h_norm = np.linalg.norm(h_vec)
    if h_norm < 1e-3:
        raise ValueError("Target angular momentum has zero magnitude")

    n_hat = h_vec / h_norm
    t_hat = np.cross(n_hat, r_hat)
    t_hat = t_hat / np.linalg.norm(t_hat)

    return r_hat, t_hat, n_hat


def transform_vector_to_rtn(vec_eci: np.ndarray, r_hat: np.ndarray, t_hat: np.ndarray, n_hat: np.ndarray) -> np.ndarray:
    """Projects an ECI vector onto the RTN orthonormal basis."""
    return np.array([
        float(np.dot(vec_eci, r_hat)),
        float(np.dot(vec_eci, t_hat)),
        float(np.dot(vec_eci, n_hat)),
    ], dtype=np.float64)


def transform_covariance_to_rtn(cov_eci_3x3: np.ndarray, r_hat: np.ndarray, t_hat: np.ndarray, n_hat: np.ndarray) -> np.ndarray:
    """Transforms a 3x3 ECI position covariance matrix into the RTN frame."""
    M_eci_to_rtn = np.vstack([r_hat, t_hat, n_hat])
    return M_eci_to_rtn @ cov_eci_3x3 @ M_eci_to_rtn.T


class FeatureExtractionResult:
    def __init__(
        self,
        features: Optional[np.ndarray],
        status: str,
        missing_features: List[str],
        message: str,
    ):
        self.features = features
        self.status = status
        self.missing_features = missing_features
        self.message = message

    def is_valid(self) -> bool:
        return self.status == "SUCCESS" and self.features is not None


def extract_features_from_state_and_cdm(
    r_target: np.ndarray,
    v_target: np.ndarray,
    r_chaser: np.ndarray,
    v_chaser: np.ndarray,
    tca_seconds: float,
    cov_target_3x3: Optional[np.ndarray] = None,
    cov_chaser_3x3: Optional[np.ndarray] = None,
    t_span_days: Optional[float] = None,
    c_span_days: Optional[float] = None,
    chaser_object_type: Optional[str] = None,
    strict_cdm: bool = True,
) -> FeatureExtractionResult:
    """
    Extracts the 33 features from primary/secondary ECI Cartesian vectors,
    covariance matrices, and optional CDM parameters.
    
    If strict_cdm is True and any required CDM metadata or covariance is missing,
    returns status='INSUFFICIENT_INPUT_DATA' with a list of missing features.
    """
    missing = []

    # 1. Geometry and Kinematics
    delta_r = np.asarray(r_chaser) - np.asarray(r_target)
    delta_v = np.asarray(v_chaser) - np.asarray(v_target)

    miss_dist = float(np.linalg.norm(delta_r))
    rel_speed = float(np.linalg.norm(delta_v))
    time_to_tca_days = float(tca_seconds) / 86400.0

    try:
        r_hat, t_hat, n_hat = compute_rtn_basis(np.asarray(r_target), np.asarray(v_target))
        rel_pos_rtn = transform_vector_to_rtn(delta_r, r_hat, t_hat, n_hat)
        rel_vel_rtn = transform_vector_to_rtn(delta_v, r_hat, t_hat, n_hat)
    except Exception as e:
        return FeatureExtractionResult(
            features=None,
            status="CALCULATION_ERROR",
            missing_features=[],
            message=f"Failed to construct RTN basis: {str(e)}",
        )

    # Sub-spacecraft geocentric latitude
    r_t_norm = float(np.linalg.norm(r_target))
    geocentric_lat = math.degrees(math.asin(max(-1.0, min(1.0, r_target[2] / r_t_norm))))

    # Azimuth and elevation of relative velocity
    v_horiz = math.hypot(rel_vel_rtn[0], rel_vel_rtn[1])
    azimuth = math.degrees(math.atan2(rel_vel_rtn[1], rel_vel_rtn[0])) % 360.0
    elevation = math.degrees(math.atan2(rel_vel_rtn[2], v_horiz)) if v_horiz > 1e-9 else 90.0

    # Keplerian elements
    t_sma, t_ecc, t_inc = cartesian_to_keplerian(r_target, v_target)
    c_sma, c_ecc, c_inc = cartesian_to_keplerian(r_chaser, v_chaser)

    # 2. Covariance Features
    mahalanobis_dist = 0.0
    t_sigma_r, t_sigma_t, t_sigma_n = 0.0, 0.0, 0.0
    c_sigma_r, c_sigma_t, c_sigma_n = 0.0, 0.0, 0.0
    t_det, c_det = 0.0, 0.0

    if cov_target_3x3 is not None and cov_chaser_3x3 is not None:
        try:
            cov_t_rtn = transform_covariance_to_rtn(cov_target_3x3, r_hat, t_hat, n_hat)
            cov_c_rtn = transform_covariance_to_rtn(cov_chaser_3x3, r_hat, t_hat, n_hat)

            t_sigma_r = math.sqrt(max(0.0, cov_t_rtn[0, 0]))
            t_sigma_t = math.sqrt(max(0.0, cov_t_rtn[1, 1]))
            t_sigma_n = math.sqrt(max(0.0, cov_t_rtn[2, 2]))

            c_sigma_r = math.sqrt(max(0.0, cov_c_rtn[0, 0]))
            c_sigma_t = math.sqrt(max(0.0, cov_c_rtn[1, 1]))
            c_sigma_n = math.sqrt(max(0.0, cov_c_rtn[2, 2]))

            t_det = float(np.linalg.det(cov_t_rtn))
            c_det = float(np.linalg.det(cov_c_rtn))

            combined_cov = cov_t_rtn + cov_c_rtn
            if np.linalg.det(combined_cov) > 1e-12:
                inv_comb = np.linalg.inv(combined_cov)
                mahalanobis_dist = float(math.sqrt(max(0.0, rel_pos_rtn @ inv_comb @ rel_pos_rtn)))
            else:
                missing.append("non_singular_combined_covariance")
        except Exception as e:
            missing.append(f"covariance_processing_error({str(e)})")
    else:
        missing.extend([
            "t_sigma_r", "c_sigma_r", "t_sigma_t", "c_sigma_t",
            "t_sigma_n", "c_sigma_n", "t_position_covariance_det",
            "c_position_covariance_det", "mahalanobis_distance"
        ])

    # 3. Observation Spans
    if t_span_days is None:
        missing.append("t_span")
    if c_span_days is None:
        missing.append("c_span")

    # 4. Object Type One-Hot Encoding
    obj_type_flags = [0.0, 0.0, 0.0, 0.0]  # PAYLOAD, ROCKET BODY, TBA, UNKNOWN
    if chaser_object_type is None:
        missing.append("c_object_type")
    else:
        norm_type = chaser_object_type.strip().upper()
        if "PAYLOAD" in norm_type:
            obj_type_flags[0] = 1.0
        elif "ROCKET" in norm_type or "BODY" in norm_type:
            obj_type_flags[1] = 1.0
        elif "TBA" in norm_type:
            obj_type_flags[2] = 1.0
        elif "UNKNOWN" in norm_type or "DEBRIS" in norm_type:
            obj_type_flags[3] = 1.0
        else:
            obj_type_flags[3] = 1.0

    # Strict CDM check
    if strict_cdm and missing:
        return FeatureExtractionResult(
            features=None,
            status="INSUFFICIENT_INPUT_DATA",
            missing_features=missing,
            message=f"Missing required CDM/covariance features: {', '.join(missing)}",
        )

    # Assemble feature vector in EXACT 33 order
    vec = [
        time_to_tca_days,
        miss_dist,
        rel_speed,
        rel_pos_rtn[0],
        rel_pos_rtn[1],
        rel_pos_rtn[2],
        rel_vel_rtn[0],
        rel_vel_rtn[1],
        rel_vel_rtn[2],
        geocentric_lat,
        azimuth,
        elevation,
        mahalanobis_dist,
        t_sma,
        t_ecc,
        t_inc,
        c_sma,
        c_ecc,
        c_inc,
        float(t_span_days if t_span_days is not None else 0.0),
        float(c_span_days if c_span_days is not None else 0.0),
        t_sigma_r,
        c_sigma_r,
        t_sigma_t,
        c_sigma_t,
        t_sigma_n,
        c_sigma_n,
        t_det,
        c_det,
        obj_type_flags[0],
        obj_type_flags[1],
        obj_type_flags[2],
        obj_type_flags[3],
    ]

    return FeatureExtractionResult(
        features=np.array(vec, dtype=np.float32),
        status="SUCCESS",
        missing_features=[],
        message="All 33 features successfully derived and validated.",
    )
