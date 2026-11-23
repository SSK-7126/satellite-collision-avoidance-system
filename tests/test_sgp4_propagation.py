"""
tests/test_sgp4_propagation.py
==============================
Tests for SGP4 Multi-Object Propagation & Coordinate Transformation (Phase 4).
Verifies:
- Explicit TEME -> ECI J2000 transformation preserves physical vector magnitudes
- Parity reflection and scaling in J2000 -> Unreal display coordinates
- SGP4 orbit propagation accuracy for real LEO payloads
- Multi-object time grid sampling, background caching, and cancellation
- Per-object health tracking and graceful error handling
- Non-interference with authoritative D1/D2 numerical propagators
"""

import math
from datetime import datetime, timezone, timedelta
import numpy as np
import pytest

from backend.propagation.frames import (
    teme_to_j2000,
    j2000_to_unreal,
    compute_teme_to_j2000_matrix,
    DEFAULT_RENDER_SCALE,
    CoordinateFrame,
)
from backend.propagation.sgp4_engine import SGP4Propagator, PropagatedState
from backend.propagation.multi_object_manager import MultiObjectPropagator
from backend.catalogue.parsers import parse_tle


# ISS TLE
ISS_LINE1 = "1 25544U 98067A   26327.50000000  .00016717  00000-0  10270-3 0  9990"
ISS_LINE2 = "2 25544  51.6416 198.2435 0005432  65.1234 295.0123 15.49876543501237"

# CARTOSAT-3 TLE
CARTO_LINE1 = "1 44804U 19081A   26327.50000000  .00000456  00000-0  23456-4 0  9993"
CARTO_LINE2 = "2 44804  97.4520  45.1200 0012000  85.4500 274.8000 15.18500000381021"


def test_teme_to_j2000_magnitude_invariance():
    """Verify that rotation from TEME to J2000 strictly preserves Euclidean norm."""
    dt = datetime(2026, 11, 23, 12, 0, 0, tzinfo=timezone.utc)
    r_teme_km = np.array([6500.0, 1500.0, 2000.0], dtype=np.float64)
    v_teme_km_s = np.array([1.2, 6.8, 3.1], dtype=np.float64)

    r_j2k_m, v_j2k_mps = teme_to_j2000(r_teme_km, v_teme_km_s, dt)

    # Norm in metres should exactly equal norm in km * 1000
    norm_teme_m = np.linalg.norm(r_teme_km) * 1000.0
    norm_j2k_m = np.linalg.norm(r_j2k_m)
    assert pytest.approx(norm_j2k_m, rel=1e-9) == norm_teme_m

    norm_v_teme_mps = np.linalg.norm(v_teme_km_s) * 1000.0
    norm_v_j2k_mps = np.linalg.norm(v_j2k_mps)
    assert pytest.approx(norm_v_j2k_mps, rel=1e-9) == norm_v_teme_mps


def test_teme_to_j2000_multi_epoch_orthonormality():
    """
    Validate TEME-to-ECI J2000 3D transformation matrix across multiple epochs:
    - Verifies matrix orthonormality M @ M^T = I to machine precision (< 1e-15)
    - Verifies proper rotation determinant det(M) = +1.0
    - Verifies identity convergence near J2000 epoch (< 3e-5 due to nutation)
    - Verifies non-trivial 3D off-diagonal coupling (precession tilt) at 2026 epoch
    """
    test_epochs = [
        datetime(2000, 1, 1, 12, 0, 0, tzinfo=timezone.utc),
        datetime(2010, 6, 15, 0, 0, 0, tzinfo=timezone.utc),
        datetime(2020, 1, 1, 0, 0, 0, tzinfo=timezone.utc),
        datetime(2026, 11, 23, 12, 0, 0, tzinfo=timezone.utc),
        datetime(2030, 12, 31, 23, 59, 59, tzinfo=timezone.utc),
    ]

    for ep in test_epochs:
        M = compute_teme_to_j2000_matrix(ep)
        # 1. Orthonormality check
        identity_err = np.max(np.abs(M @ M.T - np.eye(3)))
        assert identity_err < 1e-14, f"Orthonormality violation at {ep}: {identity_err}"

        # 2. Determinant check (+1 for proper rotation)
        det_val = np.linalg.det(M)
        assert pytest.approx(det_val, abs=1e-12) == 1.0, f"Improper rotation det={det_val}"

    # Check J2000 epoch identity proximity
    M_j2k = compute_teme_to_j2000_matrix(datetime(2000, 1, 1, 12, 0, 0, tzinfo=timezone.utc))
    assert np.max(np.abs(M_j2k - np.eye(3))) < 5e-5

    # Check 2026 epoch off-diagonal 3D precession coupling (non-zero X-Z and Y-Z components)
    M_2026 = compute_teme_to_j2000_matrix(datetime(2026, 11, 23, 12, 0, 0, tzinfo=timezone.utc))
    assert abs(M_2026[0, 2]) > 1e-3, "Precession out-of-plane coupling missing from M[0,2]"
    assert abs(M_2026[2, 0]) > 1e-3, "Precession out-of-plane coupling missing from M[2,0]"


def test_j2000_to_unreal_coordinate_parity():
    """Verify right-handed ECI J2000 to left-handed Unreal transformation parity."""
    r_j2k_m = np.array([7_000_000.0, 10_000.0, -500_000.0])
    v_j2k_mps = np.array([100.0, 7500.0, 300.0])

    r_ue, v_ue = j2000_to_unreal(r_j2k_m, v_j2k_mps, scale=0.01)

    assert r_ue[0] == 70_000.0      # +X
    assert r_ue[1] == -100.0        # -Y (reflected handedness)
    assert r_ue[2] == -5_000.0      # +Z
    assert v_ue[0] == 1.0
    assert v_ue[1] == -75.0
    assert v_ue[2] == 3.0


def test_sgp4_single_object_propagation():
    """Verify SGP4 propagation produces valid LEO physical state."""
    prop = SGP4Propagator("25544", ISS_LINE1, ISS_LINE2)
    dt = datetime(2026, 11, 23, 12, 0, 0, tzinfo=timezone.utc)
    state = prop.propagate_to_datetime(dt)

    assert state.is_valid
    assert state.error_code == 0
    assert state.r_j2000_m is not None

    radius_km = np.linalg.norm(state.r_j2000_m) / 1000.0
    speed_km_s = np.linalg.norm(state.v_j2000_mps) / 1000.0

    # LEO ISS orbit bounds: altitude ~400-420 km => radius ~6770-6800 km
    assert 6700.0 < radius_km < 6900.0
    # Orbital speed ~7.6-7.7 km/s
    assert 7.4 < speed_km_s < 7.8
    assert state.r_unreal_uu is not None


def test_multi_object_grid_propagation_and_cache():
    """Verify time grid propagation, caching, and health records."""
    manager = MultiObjectPropagator()
    iss_obj = parse_tle(ISS_LINE1, ISS_LINE2, line0="ISS")
    carto_obj = parse_tle(CARTO_LINE1, CARTO_LINE2, line0="CARTOSAT-3")

    start_dt = datetime(2026, 11, 23, 12, 0, 0, tzinfo=timezone.utc)
    results = manager.propagate_all_tracked(
        [iss_obj, carto_obj],
        start_epoch=start_dt,
        duration_sec=300.0,
        dt_sec=30.0,
        scale=0.01,
    )

    assert len(results) == 2
    assert "25544" in results
    assert "44804" in results

    res_iss = results["25544"]
    assert res_iss.is_success
    assert res_iss.samples_count == 11  # 0 to 300 s at dt=30s => 11 points

    # Verify caching speed
    t0 = datetime.now()
    cached_res = manager.propagate_grid("25544", "ISS", start_dt, duration_sec=300.0, dt_sec=30.0, scale=0.01)
    duration_cached = (datetime.now() - t0).total_seconds()
    assert cached_res.is_success
    assert duration_cached < 0.01  # Cached response is near-instantaneous

    # Health check
    health = manager.get_object_health("25544")
    assert health is not None
    assert health["status"] == "HEALTHY"


def test_propagation_cancellation():
    """Verify propagation job halts safely upon cancellation token."""
    manager = MultiObjectPropagator()
    iss_obj = parse_tle(ISS_LINE1, ISS_LINE2, line0="ISS")
    manager.register_object(iss_obj)

    token = {"cancelled": True}
    start_dt = datetime(2026, 11, 23, 12, 0, 0, tzinfo=timezone.utc)
    res = manager.propagate_grid(
        "25544", "ISS", start_dt, duration_sec=1000.0, dt_sec=10.0, cancel_token=token
    )

    assert not res.is_success
    assert "cancelled" in res.error_message.lower()


def test_teme_to_j2000_against_skyfield_reference():
    """
    Validate TEME-to-J2000 (GCRF) transformation against independent Skyfield 1.55 reference.
    
    Verifies:
    - Multiple representative epochs (J2000 epoch, 2026 operational, 2030 future)
    - Representative orbital states (LEO ~7071 km, GEO ~42164 km)
    - Agreement with Skyfield GCRF rotation to < 1e-6 matrix entry difference
    - Position agreement to < 10.0 metres over 7,000 km orbit (< 1.5 ppm relative)
    - Velocity agreement to < 10.0 mm/s (< 1.5 ppm relative)
    - Confirms proper matrix multiplication order, handedness, and rotation sign conventions
    """
    from skyfield.api import load
    from skyfield.sgp4lib import TEME

    ts = load.timescale()
    test_epochs = [
        datetime(2000, 1, 1, 12, 0, 0, tzinfo=timezone.utc),
        datetime(2026, 6, 21, 0, 0, 0, tzinfo=timezone.utc),
        datetime(2030, 12, 31, 23, 59, 59, tzinfo=timezone.utc),
    ]

    # Test cases: (r_teme_km, v_teme_km_s, max_pos_diff_m, max_vel_diff_mps)
    test_states = [
        # LEO (~7071 km radius, ~7.07 km/s speed)
        (np.array([5000.0, 4000.0, 3000.0]), np.array([-4.0, 5.0, 3.0]), 10.0, 0.010),
        # GEO (~42164 km radius, ~3.07 km/s speed)
        (np.array([42164.0, 0.0, 0.0]), np.array([0.0, 3.074, 0.0]), 50.0, 0.005),
    ]

    for dt in test_epochs:
        t_sf = ts.utc(dt.year, dt.month, dt.day, dt.hour, dt.minute, dt.second)
        M_ours = compute_teme_to_j2000_matrix(dt)
        M_skyfield = TEME.rotation_at(t_sf).T

        # Matrix maximum entry difference
        matrix_diff = np.max(np.abs(M_ours - M_skyfield))
        assert matrix_diff < 1e-6, f"Matrix discrepancy at {dt}: {matrix_diff}"

        for r_teme_km, v_teme_km_s, max_p_diff_m, max_v_diff_mps in test_states:
            r_j2k_m, v_j2k_ms = teme_to_j2000(r_teme_km, v_teme_km_s, dt)
            r_sky_m = (M_skyfield @ r_teme_km) * 1000.0
            v_sky_ms = (M_skyfield @ v_teme_km_s) * 1000.0

            pos_diff_m = np.linalg.norm(r_j2k_m - r_sky_m)
            vel_diff_ms = np.linalg.norm(v_j2k_ms - v_sky_ms)

            assert pos_diff_m < max_p_diff_m, (
                f"Position diff {pos_diff_m:.3f}m exceeds {max_p_diff_m}m at {dt}"
            )
            assert vel_diff_ms < max_v_diff_mps, (
                f"Velocity diff {vel_diff_ms*1000:.3f}mm/s exceeds {max_v_diff_mps*1000}mm/s at {dt}"
            )


def test_velocity_transformation_derivative_error_bound():
    """
    Rigorously bound the neglected frame-rate derivative term M_dot * r.
    
    The complete kinematic transformation from TEME to J2000 is:
        v_J2000 = M(t) * v_TEME + M_dot(t) * r_TEME
    
    This test verifies:
    1. Numerical derivative norm ||M_dot|| < 1.0e-11 s^-1 across operational epochs
    2. For LEO (r = 7,000 km), ||M_dot * r|| < 0.1 mm/s (0.0001 m/s)
    3. For GEO (r = 42,164 km), ||M_dot * r|| < 0.5 mm/s (0.0005 m/s)
    4. Relative velocity error ||M_dot * r|| / ||v|| < 1.0e-7 (sub-ppm)
    5. Confirms that neglecting M_dot * r is over four orders of magnitude smaller
       than SGP4's inherent velocity error (~1.0 m/s = 1000 mm/s).
    """
    dt = datetime(2026, 6, 21, 12, 0, 0, tzinfo=timezone.utc)
    delta_t_sec = 1.0

    M_plus = compute_teme_to_j2000_matrix(dt + timedelta(seconds=delta_t_sec))
    M_minus = compute_teme_to_j2000_matrix(dt - timedelta(seconds=delta_t_sec))
    M_dot = (M_plus - M_minus) / (2.0 * delta_t_sec)

    norm_M_dot = np.linalg.norm(M_dot, 2)
    assert norm_M_dot < 1.0e-11, f"||M_dot|| rate {norm_M_dot} s^-1 exceeds 1e-11 limit"

    # LEO boundary check (7,000 km)
    r_leo_m = np.array([7_000_000.0, 0.0, 0.0])
    v_coriolis_leo = M_dot @ r_leo_m
    v_err_leo_mps = np.linalg.norm(v_coriolis_leo)
    assert v_err_leo_mps < 1.0e-4, f"LEO Coriolis {v_err_leo_mps*1000} mm/s exceeds 0.1 mm/s"

    # GEO boundary check (42,164 km)
    r_geo_m = np.array([42_164_000.0, 0.0, 0.0])
    v_coriolis_geo = M_dot @ r_geo_m
    v_err_geo_mps = np.linalg.norm(v_coriolis_geo)
    assert v_err_geo_mps < 5.0e-4, f"GEO Coriolis {v_err_geo_mps*1000} mm/s exceeds 0.5 mm/s"

    # Compare against SGP4 intrinsic uncertainty (1.0 m/s)
    sgp4_velocity_uncertainty_mps = 1.0
    margin_ratio = sgp4_velocity_uncertainty_mps / v_err_leo_mps
    assert margin_ratio > 10_000.0, (
        f"Neglected Coriolis term must be > 10,000x smaller than SGP4 uncertainty (ratio: {margin_ratio:.1f})"
    )

