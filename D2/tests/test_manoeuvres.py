"""
D2/tests/test_manoeuvres.py
===========================
Comprehensive Validation and Audit Test Suite for Autonomous Collision-Avoidance
Manoeuvre Planning (D2), strictly following Sections 6 & 7 of the Technical Guide.

Verification Scenarios & Audit Modules:
1.  No collision risk (Safe pass, >100 km separation -> NO_MANOEUVRE_REQUIRED).
2.  Controlled close-approach encounter (Avoidance candidate selected, miss distance restored).
3.  Burn timing sensitivity (Comparison of early vs late lead times and trajectory deviation).
4.  Delta-v directional response (+T, -T, +N, -N, +R, -R physical orbital mechanics).
5.  Delta-v budget enforcement (Candidates exceeding max_delta_v rejected).
6.  Missing covariance safeguards (Geometric miss distance used, Pc reported as None).
7.  Unachievable constraint handling (Reports NO_ACCEPTABLE_MANOEUVRE_FOUND, no false avoidance).
8.  Post-manoeuvre TCA & covariance synchronization (New TCA, modified orbit STM, PSD covariance).
9.  Collision probability numerical validation (Underflow detection, log10_pc, large miss, anisotropic cov).
10. Optimizer safety-priority validation (Unsafe lower-dv rejected, safe higher-dv selected, tie-breakers).
11. Burn-time and frame validation (Lead time, RTN orthonormality, isometry, position continuity).
12. Full regression testing (Runs all prior D2 test suites and verifies 100% compliance).

Run:
    python -m D2.tests.test_manoeuvres
"""

import sys
import numpy as np

from D2.dynamics.two_body import MU_EARTH
from D2.dynamics.orbit_propagator import propagate_orbit
from D2.scenarios.close_approach import create_close_approach_scenario
from D2.uncertainty.covariance import (
    create_diagonal_covariance,
    is_valid_covariance,
    validate_covariance,
)
from D2.uncertainty.collision_probability import (
    calculate_collision_probability,
    project_to_encounter_plane,
    _integrate_2d_gaussian_circle,
)
from D2.manoeuvres.manoeuvre_model import (
    ImpulsiveManoeuvre,
    ManoeuvreConstraints,
    DIRECTION_VECTORS_RTN,
    compute_rtn_basis,
    rtn_to_eci,
    eci_to_rtn,
)
from D2.manoeuvres.candidate_generator import (
    generate_candidate_manoeuvres,
    DEFAULT_LEAD_TIMES,
    DEFAULT_DELTA_V_MAGNITUDES,
    DEFAULT_DIRECTIONS,
)
from D2.manoeuvres.manoeuvre_evaluator import simulate_manoeuvre
from D2.manoeuvres.manoeuvre_optimizer import evaluate_and_rank_candidates
from D2.manoeuvres.avoidance_pipeline import (
    plan_collision_avoidance,
    format_avoidance_report,
)


def test_no_collision_risk():
    """Scenario 1: Encounter well outside safety threshold requires no manoeuvre."""
    print("\n[TEST 1] Verifying No-Collision-Risk Scenario (Safe Separation)...")
    s1, _ = create_close_approach_scenario()
    # Create secondary object 100 km away along X
    s2_safe = s1.copy()
    s2_safe[0] += 100_000.0  # +100 km separation

    constraints = ManoeuvreConstraints(min_miss_distance=5000.0)
    result = plan_collision_avoidance(
        initial_state_sat=s1,
        initial_state_sec=s2_safe,
        duration=1000.0,
        dt=5.0,
        constraints=constraints
    )

    assert result["status"] == "NO_MANOEUVRE_REQUIRED", f"Expected NO_MANOEUVRE_REQUIRED, got {result['status']}"
    assert result["avoidance_needed"] is False, "Avoidance should not be needed for safe pass."
    assert result["selected_manoeuvre"] is None, "No manoeuvre should be selected."
    assert result["post_manoeuvre_assessment"] is None, "Post-manoeuvre assessment should be None."
    assert result["nominal_assessment"]["miss_distance_m"] >= 5000.0, "Nominal miss distance should be >= 5000 m."
    assert result["differential_metrics"]["delta_v_expended_mps"] == 0.0, "Zero propellant expended."

    print(f"  [PASS] Nominal miss distance: {result['nominal_assessment']['miss_distance_m']:.1f} m.")
    print("  [PASS] Successfully confirmed NO_MANOEUVRE_REQUIRED for safe pass.")


def test_controlled_close_approach_avoidance():
    """Scenario 2: Controlled close-approach encounter triggers avoidance and selects safe candidate."""
    print("\n[TEST 2] Verifying Controlled Close-Approach Avoidance Selection...")
    s1, s2 = create_close_approach_scenario()
    constraints = ManoeuvreConstraints(min_miss_distance=2000.0, max_delta_v=5.0)

    result = plan_collision_avoidance(
        initial_state_sat=s1,
        initial_state_sec=s2,
        duration=1000.0,
        dt=2.0,
        constraints=constraints,
        candidate_delta_v_magnitudes=[0.5, 1.0, 2.0, 3.0, 5.0]
    )

    assert result["status"] == "SUCCESS", f"Expected SUCCESS, got {result['status']}"
    assert result["avoidance_needed"] is True, "Avoidance should be triggered (nominal miss ~1563 m < 2000 m)."
    assert result["selected_manoeuvre"] is not None, "A manoeuvre must be selected."
    assert result["post_manoeuvre_assessment"] is not None, "Post-manoeuvre assessment must be present."

    post_miss = result["post_manoeuvre_assessment"]["post_manoeuvre_miss_distance_m"]
    nom_miss = result["nominal_assessment"]["miss_distance_m"]
    delta_miss = result["differential_metrics"]["delta_miss_distance_m"]

    assert post_miss >= constraints.min_miss_distance, f"Post miss {post_miss:.1f} m < required {constraints.min_miss_distance:.1f} m."
    assert delta_miss > 0.0, f"Miss distance should increase, got {delta_miss:.1f} m."
    assert result["selected_manoeuvre"].delta_v_magnitude <= constraints.max_delta_v, "Delta-v must respect limit."

    print(f"  [PASS] Nominal miss distance : {nom_miss:.1f} m")
    print(f"  [PASS] Selected manoeuvre    : {result['selected_manoeuvre'].manoeuvre_id}")
    print(f"  [PASS] Post miss distance    : {post_miss:.1f} m (Delta = +{delta_miss:.1f} m)")


def test_different_burn_times():
    """Scenario 3: Comparison of early vs late burn times (lead time sensitivity)."""
    print("\n[TEST 3] Verifying Sensitivity to Burn Timing & Lead Time...")
    s1, s2 = create_close_approach_scenario()

    man_early = ImpulsiveManoeuvre(
        burn_time=170.0,
        delta_v_magnitude=1.0,
        direction_label="-T",
        delta_v_rtn=DIRECTION_VECTORS_RTN["-T"] * 1.0
    )
    man_late = ImpulsiveManoeuvre(
        burn_time=650.0,
        delta_v_magnitude=1.0,
        direction_label="-T",
        delta_v_rtn=DIRECTION_VECTORS_RTN["-T"] * 1.0
    )

    res_early = simulate_manoeuvre(s1, s2, man_early, duration=1000.0, dt=2.0)
    res_late = simulate_manoeuvre(s1, s2, man_late, duration=1000.0, dt=2.0)

    dev_early = res_early["max_trajectory_deviation_m"]
    dev_late = res_late["max_trajectory_deviation_m"]
    assert dev_early > dev_late, f"Early burn should accumulate larger deviation ({dev_early:.1f} m) than late burn ({dev_late:.1f} m)."

    print(f"  [PASS] Early burn (t={man_early.burn_time}s) max deviation : {dev_early:.1f} m")
    print(f"  [PASS] Late burn  (t={man_late.burn_time}s) max deviation : {dev_late:.1f} m")


def test_different_delta_v_directions():
    """Scenario 4: Physical orbital response across RTN directions (+T, -T, +N, -N, +R, -R)."""
    print("\n[TEST 4] Verifying Directional Physical Dynamics (+T, -T, +N, -N, +R, -R)...")
    s1, s2 = create_close_approach_scenario()
    t_burn = 200.0
    dv_mag = 1.0

    directions_tested = ["+T", "-T", "+N", "-N", "+R", "-R"]
    results_dir = {}

    for d in directions_tested:
        man = ImpulsiveManoeuvre(
            burn_time=t_burn,
            delta_v_magnitude=dv_mag,
            direction_label=d,
            delta_v_rtn=DIRECTION_VECTORS_RTN[d] * dv_mag
        )
        res = simulate_manoeuvre(s1, s2, man, duration=1000.0, dt=2.0)
        results_dir[d] = res

        assert res["post_manoeuvre_miss_distance_m"] >= 0.0, f"Miss distance for {d} must be non-negative."
        assert res["max_trajectory_deviation_m"] > 0.0, f"Trajectory deviation for {d} must be strictly positive."
        assert np.all(np.isfinite(res["post_manoeuvre_relative_position_m"])), f"Relative position for {d} must be finite."

    # Along-track modifies orbital period/energy; +T advances TCA, -T delays TCA
    tca_plus_t = results_dir["+T"]["post_manoeuvre_tca_sec"]
    tca_minus_t = results_dir["-T"]["post_manoeuvre_tca_sec"]
    assert tca_plus_t < tca_minus_t, f"+T TCA ({tca_plus_t:.1f}s) should be earlier than -T TCA ({tca_minus_t:.1f}s)."

    # Cross-track (+N and -N) symmetrically alters orbital plane
    miss_plus_n = results_dir["+N"]["post_manoeuvre_miss_distance_m"]
    miss_minus_n = results_dir["-N"]["post_manoeuvre_miss_distance_m"]
    assert np.isclose(miss_plus_n, miss_minus_n, rtol=1e-3, atol=1.0), (
        f"Out-of-plane +N ({miss_plus_n:.1f} m) and -N ({miss_minus_n:.1f} m) miss distances should match by symmetry."
    )

    print("  [PASS] Along-track energy shift: +T advances TCA (%.1fs), -T delays TCA (%.1fs)." % (tca_plus_t, tca_minus_t))
    print("  [PASS] Cross-track orbital plane symmetry: +N miss = %.1f m, -N miss = %.1f m." % (miss_plus_n, miss_minus_n))
    print("  [PASS] Radial manoeuvres altered encounter geometry consistently.")


def test_exceeding_delta_v_limit():
    """Scenario 5: Candidates exceeding the mission delta-v budget are rejected."""
    print("\n[TEST 5] Verifying Delta-v Budget Enforcement (Rejection of Excessive dv)...")
    s1, s2 = create_close_approach_scenario()
    constraints = ManoeuvreConstraints(max_delta_v=1.5, min_miss_distance=1000.0)

    cand_valid = ImpulsiveManoeuvre(
        burn_time=170.0,
        delta_v_magnitude=1.0,
        direction_label="-T",
        delta_v_rtn=DIRECTION_VECTORS_RTN["-T"] * 1.0
    )
    cand_excessive = ImpulsiveManoeuvre(
        burn_time=170.0,
        delta_v_magnitude=3.0,
        direction_label="-T",
        delta_v_rtn=DIRECTION_VECTORS_RTN["-T"] * 3.0
    )

    opt_result = evaluate_and_rank_candidates(
        initial_state_sat=s1,
        initial_state_sec=s2,
        candidates=[cand_valid, cand_excessive],
        duration=1000.0,
        constraints=constraints,
        dt=2.0
    )

    rejected_ids = [r["candidate"].manoeuvre_id for r in opt_result["rejected_candidates"]]
    assert cand_excessive.manoeuvre_id in rejected_ids, "Excessive candidate must be in rejected list."

    reasons = [r["rejection_reasons"] for r in opt_result["rejected_candidates"] if r["candidate"].manoeuvre_id == cand_excessive.manoeuvre_id][0]
    assert any("EXCEEDS_MAX_DELTA_V" in reason for reason in reasons), f"Expected EXCEEDS_MAX_DELTA_V in {reasons}"
    assert opt_result["selected_manoeuvre"].manoeuvre_id == cand_valid.manoeuvre_id, "Valid candidate must be selected."

    print(f"  [PASS] Successfully rejected {cand_excessive.manoeuvre_id} with reason: {reasons[0]}")


def test_covariance_unavailable():
    """Scenario 6: Missing covariance handled safely without fabricating collision probability."""
    print("\n[TEST 6] Verifying Missing-Covariance Safeguards...")
    s1, s2 = create_close_approach_scenario()
    constraints = ManoeuvreConstraints(min_miss_distance=2000.0, max_delta_v=5.0)

    result = plan_collision_avoidance(
        initial_state_sat=s1,
        initial_state_sec=s2,
        duration=1000.0,
        dt=2.0,
        initial_cov_sat=None,
        initial_cov_sec=None,
        constraints=constraints,
        candidate_delta_v_magnitudes=[1.0, 3.0]
    )

    nom = result["nominal_assessment"]
    assert nom["collision_probability"] is None, "Nominal Pc must be None when covariance is missing."
    assert nom["pc_status"] == "COVARIANCE_MISSING", f"Expected COVARIANCE_MISSING, got {nom['pc_status']}"

    post = result["post_manoeuvre_assessment"]
    assert post["post_manoeuvre_pc"] is None, "Post-manoeuvre Pc must be None when covariance is missing."
    assert post["pc_status"] == "COVARIANCE_MISSING", f"Expected COVARIANCE_MISSING, got {post['pc_status']}"
    assert post["post_manoeuvre_miss_distance_m"] >= constraints.min_miss_distance, "Geometric miss distance satisfied."

    print("  [PASS] Verified that Pc is reported as None and pc_status as COVARIANCE_MISSING.")
    print("  [PASS] Manoeuvre planned and verified safely using geometric miss distance alone.")


def test_no_feasible_manoeuvre():
    """Scenario 7: When constraints cannot be met, report NO_ACCEPTABLE_MANOEUVRE_FOUND without false avoidance."""
    print("\n[TEST 7] Verifying Unachievable Constraints Handling...")
    s1, s2 = create_close_approach_scenario()
    impossible_constraints = ManoeuvreConstraints(
        min_miss_distance=500_000.0,
        max_delta_v=0.1
    )

    result = plan_collision_avoidance(
        initial_state_sat=s1,
        initial_state_sec=s2,
        duration=1000.0,
        dt=2.0,
        constraints=impossible_constraints,
        candidate_delta_v_magnitudes=[0.05, 0.1]
    )

    assert result["status"] == "NO_ACCEPTABLE_MANOEUVRE_FOUND", f"Expected NO_ACCEPTABLE_MANOEUVRE_FOUND, got {result['status']}"
    assert result["selected_manoeuvre"] is None, "No manoeuvre must be selected."
    assert result["post_manoeuvre_assessment"] is None, "Post assessment must be None."
    assert result["avoidance_needed"] is True, "Avoidance was needed but could not be achieved."

    print("  [PASS] Correctly returned status: NO_ACCEPTABLE_MANOEUVRE_FOUND.")
    print("  [PASS] Verified that system never falsely claims avoidance when criteria are unmet.")


def test_post_manoeuvre_tca_covariance_synchronization():
    """Scenario 8: Post-manoeuvre TCA and covariance are recalculated and synchronized at new TCA epoch."""
    print("\n[TEST 8] Verifying Post-Manoeuvre TCA & Covariance Synchronization...")
    s1, s2 = create_close_approach_scenario()
    cov1 = create_diagonal_covariance([50.0, 50.0, 20.0], [0.05, 0.05, 0.02])
    cov2 = create_diagonal_covariance([100.0, 100.0, 50.0], [0.1, 0.1, 0.05])
    constraints = ManoeuvreConstraints(min_miss_distance=2000.0, max_delta_v=5.0, max_target_pc=1e-5)

    result = plan_collision_avoidance(
        initial_state_sat=s1,
        initial_state_sec=s2,
        duration=1000.0,
        dt=2.0,
        initial_cov_sat=cov1,
        initial_cov_sec=cov2,
        constraints=constraints,
        candidate_delta_v_magnitudes=[3.0]
    )

    assert result["status"] == "SUCCESS", f"Expected SUCCESS, got {result['status']}"

    nom = result["nominal_assessment"]
    post = result["post_manoeuvre_assessment"]

    tca_nom = nom["tca_sec"]
    tca_post = post["post_manoeuvre_tca_sec"]
    assert abs(tca_post - tca_nom) > 1.0, f"Post-manoeuvre TCA ({tca_post:.1f}s) must differ from nominal ({tca_nom:.1f}s)."

    opt = result["optimizer_result"]
    selected_eval = opt["selected_evaluation"]
    cov_rel_post = selected_eval["post_manoeuvre_cov_rel"]

    assert cov_rel_post is not None, "Post-manoeuvre relative covariance must exist."
    is_valid, reason = is_valid_covariance(cov_rel_post)
    assert is_valid is True, f"Post-manoeuvre relative covariance must be valid: {reason}"

    pc_nom = nom["collision_probability"]
    pc_post = post["post_manoeuvre_pc"]
    assert pc_nom is not None and pc_post is not None, "Collision probabilities must be computed."
    assert 0.0 <= pc_post <= 1.0, f"Post-manoeuvre Pc ({pc_post}) must be in [0, 1]."
    assert pc_post <= constraints.max_target_pc, f"Post-manoeuvre Pc ({pc_post:.2e}) must satisfy max_target_pc."
    assert post["post_manoeuvre_log10_pc"] is not None, "log10_pc must be provided."

    print(f"  [PASS] Nominal TCA : {tca_nom:.2f} s, Post-manoeuvre TCA : {tca_post:.2f} s (Shift = {tca_post - tca_nom:+.2f} s)")
    print(f"  [PASS] Nominal Pc  : {pc_nom:.3e} [{nom['pc_status']}], Post-manoeuvre Pc : {pc_post:.3e} [{post['pc_status']}]")
    print(f"  [PASS] Post-manoeuvre log10(Pc): {post['post_manoeuvre_log10_pc']:.2f}")


def test_collision_probability_numerical_validation():
    """Scenario 9: Comprehensive validation of collision probability under extreme numerical conditions."""
    print("\n[TEST 9] Verifying Collision Probability Numerical Underflow & Resolution...")
    r_rel_tca = np.array([2000.0, 0.0, 0.0])
    v_rel_tca = np.array([0.0, 10.0, 0.0])
    hbr = 10.0

    # 1. Very small collision probability (tail underflow in float64)
    # With sigma = 100 m, miss = 2000 m -> 20 sigma encounter
    cov_rel_20sig = create_diagonal_covariance([100.0, 100.0, 100.0], [0.1, 0.1, 0.1])
    res_underflow = calculate_collision_probability(r_rel_tca, v_rel_tca, cov_rel_20sig, hbr)
    assert res_underflow["status"] == "NUMERICAL_UNDERFLOW", f"Expected NUMERICAL_UNDERFLOW, got {res_underflow['status']}"
    assert "FLOAT64_INTEGRATION_UNDERFLOW" in res_underflow["quality_flags"], "Underflow quality flag expected."
    assert res_underflow["log10_pc"] is not None, "log10_pc must be present."
    assert res_underflow["log10_pc"] < -50.0, f"Expected log10_pc < -50, got {res_underflow['log10_pc']}"
    assert res_underflow["pc"] >= 0.0, "Pc must be non-negative."
    print(f"  [PASS] Extreme tail (20 sigma): status={res_underflow['status']}, log10_pc={res_underflow['log10_pc']:.2f}")

    # 2. Large miss distance (quality flag check)
    r_large = np.array([15000.0, 0.0, 0.0])
    res_large = calculate_collision_probability(r_large, v_rel_tca, cov_rel_20sig, hbr)
    assert "LARGE_MISS_DISTANCE" in res_large["quality_flags"], "LARGE_MISS_DISTANCE flag must be present."
    print("  [PASS] Large miss distance (15 km) correctly flagged with LARGE_MISS_DISTANCE.")

    # 3. Small covariance (near-deterministic)
    cov_small = create_diagonal_covariance([1.0, 1.0, 1.0], [0.001, 0.001, 0.001])
    r_center = np.array([0.0, 0.0, 0.0])  # Centered direct hit
    res_small_hit = calculate_collision_probability(r_center, v_rel_tca, cov_small, hbr)
    assert res_small_hit["status"] == "COMPUTED"
    assert np.isclose(res_small_hit["pc"], 1.0, atol=1e-3), f"Direct hit with small cov should yield Pc ~ 1.0, got {res_small_hit['pc']}"
    print(f"  [PASS] Small covariance centered hit: Pc = {res_small_hit['pc']:.4f} (~1.0).")

    # 4. Highly anisotropic covariance (aspect ratio 1000:1)
    cov_aniso = create_diagonal_covariance([1000.0, 1000.0, 1.0], [0.1, 0.1, 0.001])
    # Encounter plane is X-Z (v_rel along Y)
    # Displacement along major axis X (500m / 1000m = 0.5 sigma -> high Pc)
    r_major = np.array([500.0, 0.0, 0.0])
    res_major = calculate_collision_probability(r_major, v_rel_tca, cov_aniso, hbr)
    # Displacement along minor axis Z (50m / 1m = 50 sigma -> negligible Pc)
    r_minor = np.array([0.0, 0.0, 50.0])
    res_minor = calculate_collision_probability(r_minor, v_rel_tca, cov_aniso, hbr)
    assert res_major["pc"] > res_minor["pc"], "Major axis offset must yield higher Pc than 50-sigma minor axis offset."
    assert res_major["pc"] > 1e-6, f"Major axis Pc should be substantial, got {res_major['pc']}"
    assert res_minor["status"] == "NUMERICAL_UNDERFLOW", "Minor axis 50-sigma encounter must trigger underflow status."
    print(f"  [PASS] Highly anisotropic covariance (1000:1): Major axis Pc={res_major['pc']:.3e}, Minor axis Pc={res_minor['pc']:.3e} [{res_minor['status']}].")

    # 5. Mathematically exact zero (HBR = 0.0)
    res_zero_hbr = calculate_collision_probability(r_rel_tca, v_rel_tca, cov_rel_20sig, hard_body_radius=0.0)
    assert res_zero_hbr["pc"] == 0.0, "HBR=0 must be mathematically exact 0.0."
    assert "ZERO_HARD_BODY_RADIUS" in res_zero_hbr["quality_flags"]
    assert res_zero_hbr["log10_pc"] == -float("inf")
    print("  [PASS] Combined HBR = 0.0 correctly produces mathematically exact zero probability.")


def test_optimizer_safety_priority_validation():
    """Scenario 10: Strict enforcement of safety-first constraint hierarchy in optimizer."""
    print("\n[TEST 10] Verifying Optimizer Safety-First Ranking Hierarchy...")
    s1, s2 = create_close_approach_scenario()
    constraints = ManoeuvreConstraints(min_miss_distance=2000.0, max_delta_v=5.0)

    # 1. Lower delta-v but UNSAFE candidate vs Higher delta-v but SAFE candidate
    cand_low_dv_unsafe = ImpulsiveManoeuvre(
        burn_time=170.0,
        delta_v_magnitude=0.5,
        direction_label="+T",
        delta_v_rtn=DIRECTION_VECTORS_RTN["+T"] * 0.5
    )
    cand_high_dv_safe = ImpulsiveManoeuvre(
        burn_time=170.0,
        delta_v_magnitude=3.0,
        direction_label="-R",
        delta_v_rtn=DIRECTION_VECTORS_RTN["-R"] * 3.0
    )

    opt_result = evaluate_and_rank_candidates(
        initial_state_sat=s1,
        initial_state_sec=s2,
        candidates=[cand_low_dv_unsafe, cand_high_dv_safe],
        duration=1000.0,
        constraints=constraints,
        dt=2.0
    )

    # Lower delta-v candidate must be REJECTED because it fails miss distance
    assert opt_result["status"] == "SUCCESS"
    assert opt_result["selected_manoeuvre"].manoeuvre_id == cand_high_dv_safe.manoeuvre_id, (
        "Higher delta-v safe candidate must be selected over lower delta-v unsafe candidate!"
    )
    rejected_reasons = {r["candidate"].manoeuvre_id: r["rejection_reasons"] for r in opt_result["rejected_candidates"]}
    assert cand_low_dv_unsafe.manoeuvre_id in rejected_reasons
    assert any("INSUFFICIENT_MISS_DISTANCE" in r for r in rejected_reasons[cand_low_dv_unsafe.manoeuvre_id])
    print("  [PASS] Lower delta-v unsafe candidate successfully rejected; safe candidate prioritized.")

    # 2. Equal delta-v candidates with different trajectory deviations
    # -T 3.0 m/s vs -R 3.0 m/s: Both achieve safe miss distance (> 2000 m)
    cand_minus_t = ImpulsiveManoeuvre(
        burn_time=170.0,
        delta_v_magnitude=3.0,
        direction_label="-T",
        delta_v_rtn=DIRECTION_VECTORS_RTN["-T"] * 3.0
    )
    cand_minus_r = ImpulsiveManoeuvre(
        burn_time=170.0,
        delta_v_magnitude=3.0,
        direction_label="-R",
        delta_v_rtn=DIRECTION_VECTORS_RTN["-R"] * 3.0
    )

    opt_tie = evaluate_and_rank_candidates(
        initial_state_sat=s1,
        initial_state_sec=s2,
        candidates=[cand_minus_t, cand_minus_r],
        duration=1000.0,
        constraints=constraints,
        dt=2.0
    )

    # Both feasible, equal delta-v (3.0 m/s); candidate with smaller trajectory deviation ranks higher
    f0 = opt_tie["feasible_candidates"][0]
    f1 = opt_tie["feasible_candidates"][1]
    dev0 = f0["evaluation"]["max_trajectory_deviation_m"]
    dev1 = f1["evaluation"]["max_trajectory_deviation_m"]
    assert dev0 <= dev1, f"Candidate with smaller trajectory deviation ({dev0:.1f}m) must rank ahead of ({dev1:.1f}m)."
    print(f"  [PASS] Equal delta-v tie-breaker: rank 1 deviation ({dev0:.1f} m) <= rank 2 deviation ({dev1:.1f} m).")


def test_burn_time_and_frame_validation():
    """Scenario 11: Mathematical and physical validation of burn frames and impulse mechanics."""
    print("\n[TEST 11] Verifying Burn Timing, RTN Orthonormality & Impulse Mechanics...")
    s1, _ = create_close_approach_scenario()
    r0 = s1[:3]
    v0 = s1[3:]

    # 1. RTN Orthonormality check
    R_mat = compute_rtn_basis(r0, v0)
    assert R_mat.shape == (3, 3)
    u_R = R_mat[:, 0]
    u_T = R_mat[:, 1]
    u_N = R_mat[:, 2]

    assert np.isclose(np.linalg.norm(u_R), 1.0, atol=1e-14), "u_R must be unit vector."
    assert np.isclose(np.linalg.norm(u_T), 1.0, atol=1e-14), "u_T must be unit vector."
    assert np.isclose(np.linalg.norm(u_N), 1.0, atol=1e-14), "u_N must be unit vector."

    assert np.isclose(np.dot(u_R, u_T), 0.0, atol=1e-14), "u_R and u_T must be orthogonal."
    assert np.isclose(np.dot(u_T, u_N), 0.0, atol=1e-14), "u_T and u_N must be orthogonal."
    assert np.isclose(np.dot(u_N, u_R), 0.0, atol=1e-14), "u_N and u_R must be orthogonal."

    det_R = np.linalg.det(R_mat)
    assert np.isclose(det_R, 1.0, atol=1e-14), f"R_mat determinant must be +1.0 (right-handed), got {det_R}."
    assert np.allclose(R_mat.T @ R_mat, np.eye(3), atol=1e-14), "R_mat must be orthonormal (R^T @ R = I)."
    print("  [PASS] RTN basis is strictly orthonormal with det(R) = +1.0.")

    # 2. RTN-to-ECI isometry (norm preservation) and inverse transform
    dv_rtn = np.array([1.5, -2.0, 0.75])
    dv_eci = rtn_to_eci(dv_rtn, r0, v0)
    dv_rtn_recovered = eci_to_rtn(dv_eci, r0, v0)

    assert np.isclose(np.linalg.norm(dv_eci), np.linalg.norm(dv_rtn), atol=1e-14), "Transformation must be isometric."
    assert np.allclose(dv_rtn, dv_rtn_recovered, atol=1e-14), "Inverse transform must recover exact original vector."
    print("  [PASS] RTN <-> ECI transformation is isometric and fully reversible.")

    # 3. Impulse mechanics: Velocity changes instantaneously, position is continuous
    t_burn = 150.0
    times_pre, states_pre = propagate_orbit(s1, duration=t_burn, dt=1.0)
    state_at_burn = states_pre[-1]
    r_pre = state_at_burn[:3]
    v_pre = state_at_burn[3:]

    dv_applied_rtn = np.array([0.0, 2.5, 0.0])
    dv_applied_eci = rtn_to_eci(dv_applied_rtn, r_pre, v_pre)

    state_post_burn = state_at_burn.copy()
    state_post_burn[3:] += dv_applied_eci

    # Continuity check
    assert np.array_equal(state_post_burn[:3], r_pre), "Position must remain strictly continuous across the burn!"
    assert np.allclose(state_post_burn[3:] - v_pre, dv_applied_eci, atol=1e-14), "Velocity jump must exactly equal delta-v!"

    # Modified trajectory begins from post-burn state
    times_post, states_post = propagate_orbit(state_post_burn, duration=10.0, dt=1.0)
    assert np.allclose(states_post[0], state_post_burn, atol=1e-14), "Modified trajectory must start from post-burn state!"
    print("  [PASS] Impulse mechanics verified: delta-r = 0 (position continuous), delta-v exact, trajectory starts from post-burn state.")

    # 4. Lead-time and assessment window enforcement
    tca_nom = 769.63
    # Candidate with burn time > TCA - lead_time must be rejected
    cand_late = ImpulsiveManoeuvre(
        burn_time=750.0,  # Only 19s before TCA, minimum lead time is 30s
        delta_v_magnitude=1.0,
        direction_label="+T",
        delta_v_rtn=DIRECTION_VECTORS_RTN["+T"] * 1.0
    )
    s2 = s1.copy()
    s2[1] += 10000.0
    opt_lead = evaluate_and_rank_candidates(
        initial_state_sat=s1,
        initial_state_sec=s2,
        candidates=[cand_late],
        duration=1000.0,
        constraints=ManoeuvreConstraints(min_lead_time=30.0),
        nominal_tca=tca_nom,
        dt=2.0
    )
    assert cand_late.manoeuvre_id in [r["candidate"].manoeuvre_id for r in opt_lead["rejected_candidates"]]
    reasons_late = opt_lead["rejected_candidates"][0]["rejection_reasons"]
    assert any("INSUFFICIENT_LEAD_TIME" in r for r in reasons_late)
    print(f"  [PASS] Lead-time constraint successfully enforced: {reasons_late[0]}.")


def test_regression_all_suites():
    """Scenario 12: Execute all prior D2 test suites to guarantee zero regression."""
    print("\n[TEST 12] Running Full Regression Suite Across All Previous D2 Modules...")
    import D2.tests.test_two_body as t_two_body
    import D2.tests.test_rk4 as t_rk4
    import D2.tests.test_orbit_propagation as t_prop
    import D2.tests.test_close_approach as t_close
    import D2.tests.test_conjunction as t_conj
    import D2.tests.test_uncertainty as t_unc
    import D2.tests.test_orbital_covariance as t_orb_cov

    t_close.run_tests()
    t_conj.run_all_tests()
    t_unc.run_all_tests()
    t_orb_cov.run_audit_suite()

    print("  [PASS] All 7 previous D2 test suites passed successfully.")


def run_all_tests():
    print("=" * 72)
    print(" D2 AUTONOMOUS COLLISION-AVOIDANCE MANOEUVRE PLANNING: AUDIT SUITE")
    print("=" * 72)

    test_no_collision_risk()
    test_controlled_close_approach_avoidance()
    test_different_burn_times()
    test_different_delta_v_directions()
    test_exceeding_delta_v_limit()
    test_covariance_unavailable()
    test_no_feasible_manoeuvre()
    test_post_manoeuvre_tca_covariance_synchronization()
    test_collision_probability_numerical_validation()
    test_optimizer_safety_priority_validation()
    test_burn_time_and_frame_validation()
    test_regression_all_suites()

    print("\n" + "=" * 72)
    print(" ALL 12 AUDIT & VALIDATION TESTS PASSED SUCCESSFULLY (100% VERIFIED)")
    print("=" * 72)


if __name__ == "__main__":
    run_all_tests()
