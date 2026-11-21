"""
D2/tests/test_uncertainty.py
============================
Verification test suite for D2 Covariance and Collision Probability modules,
strictly following Section 6 of the Satellite Anti-Collision Technical Guide.

Tests:
1. Valid 6x6 covariance matrices (symmetry, positive-semidefinite).
2. Invalid covariance dimensions (rejection of non-6x6 shapes).
3. Asymmetric covariance rejection.
4. Positive-semidefinite validation (rejection of negative eigenvalues).
5. Independent covariance combination (P_rel = P1 + P2, frame & epoch checks).
6. Covariance propagation (P(t) = Phi * P(0) * Phi^T + Q).
7. Missing covariance handling (ensures no zero-uncertainty fabrication).
8. Numerical validity of collision probability (analytical benchmarks, Foster method, bounds).

Run:
    python -m D2.tests.test_uncertainty
"""

import numpy as np

from D2.scenarios.close_approach import create_close_approach_scenario
from D2.conjunction.tca import calculate_numerical_tca
from D2.uncertainty.covariance import (
    validate_covariance,
    is_valid_covariance,
    combine_relative_covariance,
    propagate_covariance,
    compute_linear_stm,
    create_diagonal_covariance,
)
from D2.uncertainty.collision_probability import (
    project_to_encounter_plane,
    calculate_collision_probability,
    calculate_simplified_risk_proxy,
    calculate_max_collision_probability,
)


def test_valid_covariance():
    print("\n[TEST 1] Verifying Valid 6x6 Covariance Representation...")
    # 1. Diagonal covariance
    cov_diag = create_diagonal_covariance(
        pos_std_m=[100.0, 100.0, 50.0],
        vel_std_mps=[0.1, 0.1, 0.05]
    )
    validated = validate_covariance(cov_diag)
    assert validated.shape == (6, 6)
    assert np.all(np.isfinite(validated))
    assert np.allclose(validated, validated.T)
    assert np.all(np.linalg.eigvalsh(validated) >= 0.0)

    # 2. Fully populated non-diagonal positive-definite covariance: P = A @ A^T
    rng = np.random.default_rng(42)
    a_mat = rng.standard_normal((6, 6))
    cov_dense = a_mat @ a_mat.T + 1e-4 * np.eye(6)
    is_valid, reason = is_valid_covariance(cov_dense)
    assert is_valid is True, f"Dense covariance should be valid: {reason}"

    print("  [PASS] 6x6 covariance representation validated.")


def test_invalid_dimensions():
    print("\n[TEST 2] Verifying Rejection of Invalid Covariance Dimensions...")
    invalid_shapes = [
        np.eye(3),
        np.eye(5),
        np.ones((6, 5)),
        np.ones(6),
        None,
    ]

    for inv in invalid_shapes:
        is_valid, reason = is_valid_covariance(inv)
        assert is_valid is False, f"Shape {getattr(inv, 'shape', None)} should have been rejected."

    print("  [PASS] Invalid covariance dimensions correctly rejected.")


def test_asymmetric_covariance_rejection():
    print("\n[TEST 3] Verifying Rejection of Asymmetric Matrices...")
    cov_asym = np.eye(6)
    cov_asym[0, 1] = 50.0
    cov_asym[1, 0] = -50.0  # Asymmetric entries

    is_valid, reason = is_valid_covariance(cov_asym)
    assert is_valid is False
    assert "not symmetric" in reason

    try:
        validate_covariance(cov_asym)
        assert False, "Should have raised ValueError on asymmetric matrix."
    except ValueError as exc:
        assert "not symmetric" in str(exc)

    print("  [PASS] Asymmetric covariance correctly rejected.")


def test_positive_semidefinite_validation():
    print("\n[TEST 4] Verifying Positive-Semidefinite (PSD) Checks...")
    # Construct symmetric matrix with a strictly negative eigenvalue
    cov_non_psd = np.eye(6)
    cov_non_psd[0, 0] = -10.0  # Eigenvalue is negative

    is_valid, reason = is_valid_covariance(cov_non_psd)
    assert is_valid is False
    assert "positive-semidefinite" in reason

    try:
        validate_covariance(cov_non_psd)
        assert False, "Should have raised ValueError on non-PSD matrix."
    except ValueError as exc:
        assert "not positive-semidefinite" in str(exc)

    # Matrix with exact zero eigenvalue (singular PSD) is mathematically valid
    cov_singular = np.zeros((6, 6))
    cov_singular[0, 0] = 100.0
    val_sing = validate_covariance(cov_singular)
    assert val_sing[0, 0] == 100.0

    print("  [PASS] Positive-semidefinite checks strictly enforced.")


def test_independent_covariance_combination():
    print("\n[TEST 5] Verifying Independent Covariance Combination (P_rel = P1 + P2)...")
    cov1 = create_diagonal_covariance([100.0, 100.0, 50.0], [0.1, 0.1, 0.05])
    cov2 = create_diagonal_covariance([200.0, 150.0, 80.0], [0.2, 0.15, 0.08])

    cov_rel = combine_relative_covariance(
        cov1,
        cov2,
        frame1="ECI",
        frame2="ECI",
        epoch1="2026-09-29T03:44:40Z",
        epoch2="2026-09-29T03:44:40Z",
    )

    # Position variance addition under independent error assumption
    expected_var_x = 100.0**2 + 200.0**2  # 10000 + 40000 = 50000
    expected_var_y = 100.0**2 + 150.0**2  # 10000 + 22500 = 32500
    assert np.isclose(cov_rel[0, 0], expected_var_x)
    assert np.isclose(cov_rel[1, 1], expected_var_y)
    assert np.allclose(cov_rel, cov_rel.T)
    assert np.all(np.linalg.eigvalsh(cov_rel) >= 0.0)

    # Test frame mismatch rejection
    try:
        combine_relative_covariance(cov1, cov2, frame1="ECI", frame2="ECEF")
        assert False, "Should have raised ValueError on frame mismatch."
    except ValueError as exc:
        assert "Frame mismatch" in str(exc)

    # Test epoch mismatch rejection
    try:
        combine_relative_covariance(cov1, cov2, epoch1="2026-01-01", epoch2="2026-01-02")
        assert False, "Should have raised ValueError on epoch mismatch."
    except ValueError as exc:
        assert "Epoch mismatch" in str(exc)

    print("  [PASS] Independent covariance combination and frame/epoch checks validated.")


def test_covariance_propagation():
    print("\n[TEST 6] Verifying Covariance Propagation (P(t) = Phi * P0 * Phi^T + Q)...")
    dt = 10.0
    phi = compute_linear_stm(dt=dt)

    p0 = create_diagonal_covariance(pos_std_m=100.0, vel_std_mps=0.1)
    q = create_diagonal_covariance(pos_std_m=1.0, vel_std_mps=0.01)

    p_t = propagate_covariance(p0, phi, q=q)

    # Analytical verification:
    # delta_x(t) = delta_x(0) + dt * delta_v(0) + w_x
    # Var(x(t)) = Var(x(0)) + dt^2 * Var(v(0)) + Q_x
    #           = 100^2 + 10^2 * (0.1)^2 + 1^2 = 10000 + 100 * 0.01 + 1 = 10002.0
    expected_var_x = 10000.0 + (dt**2) * (0.1**2) + 1.0**2
    assert np.isclose(p_t[0, 0], expected_var_x)
    assert np.allclose(p_t, p_t.T)
    assert np.all(np.linalg.eigvalsh(p_t) >= 0.0)

    print("  [PASS] Covariance propagation matches analytical mechanics.")


def test_missing_covariance_handling():
    print("\n[TEST 7] Verifying Missing Covariance Handling & Risk Proxy Safeguards...")
    r_rel = np.array([100.0, 50.0, 0.0])
    v_rel = np.array([0.0, 0.0, 10.0])
    hbr = 10.0

    # Call with missing covariance (cov_rel_tca = None)
    res = calculate_collision_probability(
        r_rel_tca=r_rel,
        v_rel_tca=v_rel,
        cov_rel_tca=None,
        hard_body_radius=hbr
    )

    print(f"  Missing covariance status: {res['status']}")
    print(f"  Pc value                 : {res['pc']}")
    print(f"  Quality flags            : {res['quality_flags']}")
    print(f"  Risk proxy metric type   : {res['risk_proxy']['metric_type']}")
    print(f"  Is probability           : {res['risk_proxy']['is_probability']}")

    assert res["pc"] is None, "Pc must be None when covariance is missing."
    assert res["status"] == "COVARIANCE_MISSING"
    assert res["is_valid"] is False
    assert "COVARIANCE_MISSING" in res["quality_flags"]

    # Verify risk proxy is explicitly non-probabilistic
    proxy = res["risk_proxy"]
    assert proxy["is_probability"] is False
    assert proxy["metric_type"] == "GEOMETRIC_PROXIMITY_PROXY"
    assert np.isclose(proxy["proximity_ratio"], hbr / np.linalg.norm(r_rel))

    print("  [PASS] Missing covariance handled safely without zero-uncertainty fabrication.")


def test_numerical_collision_probability():
    print("\n[TEST 8] Verifying Numerical Validity of Collision Probability (Pc)...")

    # -----------------------------------------------------------------
    # Benchmark 1: Exact Analytical Isotropic Centered Gaussian
    # For mu = [0, 0], sigma_x = sigma_y = sigma, hard body radius R:
    # Pc_exact = 1 - exp(-R^2 / (2 * sigma^2))
    # -----------------------------------------------------------------
    r_center = np.array([0.0, 0.0, 0.0])
    v_enc = np.array([0.0, 0.0, 10.0])
    sigma_val = 100.0
    r_hbr = 100.0
    cov_iso = create_diagonal_covariance(pos_std_m=sigma_val, vel_std_mps=0.1)

    res_iso = calculate_collision_probability(
        r_rel_tca=r_center,
        v_rel_tca=v_enc,
        cov_rel_tca=cov_iso,
        hard_body_radius=r_hbr
    )
    expected_iso_pc = 1.0 - np.exp(-(r_hbr**2) / (2.0 * sigma_val**2))  # 1 - exp(-0.5) ~ 0.39346934
    print(f"  Isotropic Centered Pc    : {res_iso['pc']:.8f} (Expected: {expected_iso_pc:.8f})")
    assert np.isclose(res_iso["pc"], expected_iso_pc, rtol=1e-5)

    # -----------------------------------------------------------------
    # Benchmark 2: Foster (1992) Analytical Benchmark
    # Offset mu = [100, 50], sigmas = [200, 100], R = 10
    # Expected Pc ~ 1.9447e-3
    # -----------------------------------------------------------------
    r_foster = np.array([100.0, 50.0, 0.0])
    cov_foster = create_diagonal_covariance(pos_std_m=[200.0, 100.0, 50.0], vel_std_mps=0.1)
    res_foster = calculate_collision_probability(
        r_rel_tca=r_foster,
        v_rel_tca=v_enc,
        cov_rel_tca=cov_foster,
        hard_body_radius=10.0
    )
    print(f"  Foster Benchmark Pc      : {res_foster['pc']:.6e} (Expected: ~1.9447e-3)")
    assert np.isclose(res_foster["pc"], 1.9447e-3, rtol=1e-3)

    # -----------------------------------------------------------------
    # Benchmark 3: D2 Controlled Close-Approach Scenario Integration
    # -----------------------------------------------------------------
    sat_state, deb_state = create_close_approach_scenario()
    tca_report = calculate_numerical_tca(sat_state, deb_state, duration=1200.0, dt=1.0)

    # Miss distance is ~1563.5 m, relative speed ~13.2 m/s
    r_tca = tca_report["relative_position"]
    v_tca = tca_report["relative_velocity"]
    miss_dist = tca_report["miss_distance"]

    # Combine typical LEO state uncertainties (150m for primary, 200m for debris)
    cov_sat = create_diagonal_covariance(pos_std_m=150.0, vel_std_mps=0.2)
    cov_deb = create_diagonal_covariance(pos_std_m=200.0, vel_std_mps=0.3)
    cov_tca_rel = combine_relative_covariance(cov_sat, cov_deb)

    res_d2 = calculate_collision_probability(
        r_rel_tca=r_tca,
        v_rel_tca=v_tca,
        cov_rel_tca=cov_tca_rel,
        hard_body_radius=10.0  # 10m combined radius
    )
    print(f"  D2 Close-Approach Pc     : {res_d2['pc']:.6e} (Miss dist: {miss_dist:.1f} m)")
    assert 0.0 <= res_d2["pc"] <= 1.0
    assert res_d2["pc"] < 1e-5  # Safe miss distance (~1.5 km vs 250m sigma) yields small Pc

    # -----------------------------------------------------------------
    # Benchmark 4: Conservative Upper Bound (Max Pc)
    # -----------------------------------------------------------------
    max_pc = calculate_max_collision_probability(miss_distance=miss_dist, hard_body_radius=10.0)
    print(f"  Analytical Max Pc Bound  : {max_pc:.6e}")
    assert res_d2["pc"] <= max_pc, "Computed Pc must not exceed the theoretical Max Pc upper bound."

    # -----------------------------------------------------------------
    # Benchmark 5: Extreme Physical Boundary Checks
    # -----------------------------------------------------------------
    # A. Zero radius -> Pc = 0
    res_zero_r = calculate_collision_probability(r_foster, v_enc, cov_foster, hard_body_radius=0.0)
    assert res_zero_r["pc"] == 0.0

    # B. Huge miss distance -> Pc -> 0
    r_distant = np.array([1_000_000.0, 0.0, 0.0])  # 1000 km
    res_distant = calculate_collision_probability(r_distant, v_enc, cov_foster, hard_body_radius=10.0)
    assert np.isclose(res_distant["pc"], 0.0)

    # C. Degenerate velocity -> Pc is None
    res_degen = calculate_collision_probability(r_foster, np.zeros(3), cov_foster, hard_body_radius=10.0)
    assert res_degen["pc"] is None
    assert res_degen["status"] == "DEGENERATE_VELOCITY"

    print("  [PASS] Collision probability calculations are numerically valid and fully bounded.")


def run_all_tests():
    print("=" * 70)
    print("D2 UNCERTAINTY & COLLISION PROBABILITY VERIFICATION SUITE")
    print("=" * 70)

    test_valid_covariance()
    test_invalid_dimensions()
    test_asymmetric_covariance_rejection()
    test_positive_semidefinite_validation()
    test_independent_covariance_combination()
    test_covariance_propagation()
    test_missing_covariance_handling()
    test_numerical_collision_probability()

    print("\n" + "=" * 70)
    print("ALL UNCERTAINTY AND COLLISION PROBABILITY TESTS PASSED")
    print("=" * 70)


if __name__ == "__main__":
    run_all_tests()
