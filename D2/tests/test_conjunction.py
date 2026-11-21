"""
D2/tests/test_conjunction.py
============================
Verification test suite for D2 Conjunction Assessment module, strictly
following Sections 5.1–5.4 of the Satellite Anti-Collision Technical Guide.

Tests:
1. Controlled close-approach encounter (TCA, miss distance, relative speed, screening).
2. Safe pass encounter (large miss distance, screening filter rejection).
3. Near-zero relative velocity safe handling (no division by zero).
4. Window-constrained TCA and candidate CPA time limits.
5. Non-negativity of miss distance and CPA distance.
6. Explicit comparison of linear CPA vs. numerical trajectory minimization.
7. Batch screening of a secondary object catalog.

Run:
    python -m D2.tests.test_conjunction
"""

import numpy as np

from D2.dynamics.two_body import MU_EARTH
from D2.scenarios.close_approach import create_close_approach_scenario
from D2.conjunction.tca import (
    calculate_relative_state,
    calculate_linear_cpa,
    calculate_numerical_tca,
)
from D2.conjunction.screening import (
    screen_conjunction,
    filter_conjunction_candidates,
    DEFAULT_SCREENING_THRESHOLD_M,
)


def test_controlled_close_approach():
    print("\n[TEST 1] Verifying Controlled Close-Approach Conjunction...")
    sat_state, deb_state = create_close_approach_scenario()
    duration = 1200.0
    dt = 1.0
    threshold = 25_000.0  # 25 km

    report = screen_conjunction(
        initial_state1=sat_state,
        initial_state2=deb_state,
        duration=duration,
        dt=dt,
        threshold_m=threshold,
        object1_id="PROTECTED_SAT_1",
        object2_id="DEBRIS_OBJ_2",
        epoch="2026-09-29T03:44:40Z",
    )

    lin = report["linear_cpa"]
    num = report["numerical_tca"]
    comp = report["comparison"]

    print(f"  Object IDs                : {report['object1_id']} vs {report['object2_id']}")
    print(f"  Linear CPA time (t_CPA)   : {lin['t_cpa_sec']:.2f} s")
    print(f"  Linear CPA distance (d_CPA): {lin['d_cpa_m']:.2f} m")
    print(f"  Numerical TCA             : {num['tca_sec']:.2f} s")
    print(f"  Numerical Miss Distance   : {num['miss_distance_m']:.2f} m")
    print(f"  Relative Speed at TCA     : {num['relative_speed_mps']:.3f} m/s")
    print(f"  Screening Threshold       : {report['screening_threshold_m']:.1f} m")
    print(f"  Conjunction Candidate     : {report['is_candidate']} [{report['classification']}]")
    print(f"  Delta TCA (Linear - Num)  : {comp['delta_t_sec']:.2f} s")
    print(f"  Delta Distance            : {comp['delta_distance_m']:.2f} m")

    # Assertions
    assert report["is_candidate"] is True, "Controlled close approach should pass screening threshold"
    assert report["classification"] == "CONJUNCTION_CANDIDATE"
    assert np.isclose(lin["t_cpa_sec"], 1000.0), f"Linear t_CPA expected 1000s, got {lin['t_cpa_sec']}"
    assert np.isclose(lin["d_cpa_m"], 0.0), f"Linear d_CPA expected 0m, got {lin['d_cpa_m']}"

    # Numerical TCA occurs earlier than linear prediction (~770s) due to orbital acceleration
    assert 760.0 <= num["tca_sec"] <= 780.0, f"Numerical TCA unexpected: {num['tca_sec']}"
    assert 1500.0 <= num["miss_distance_m"] <= 1600.0, f"Miss distance unexpected: {num['miss_distance_m']}"
    assert np.isclose(lin["relative_speed_mps"], 10.0), "Initial relative speed should be 10.0 m/s"
    assert np.isclose(num["relative_speed_mps"], 13.234, atol=0.5), (
        f"Relative speed at TCA unexpected: {num['relative_speed_mps']}"
    )
    assert num["miss_distance_m"] >= 0.0, "Miss distance must be non-negative"
    assert 0.0 <= num["tca_sec"] <= duration, "TCA must lie within assessment interval"

    print("  [PASS] Controlled close approach validated.")


def test_safe_pass():
    print("\n[TEST 2] Verifying Safe Pass (Non-Candidate Filtered by Screening)...")
    radius_sat = 7_000_000.0
    radius_sec = 7_100_000.0  # 100 km higher altitude
    v_sat = np.sqrt(MU_EARTH / radius_sat)
    v_sec = np.sqrt(MU_EARTH / radius_sec)

    sat_state = np.array([radius_sat, 0.0, 0.0, 0.0, v_sat, 0.0])
    sec_state = np.array([radius_sec, 0.0, 0.0, 0.0, v_sec, 0.0])

    duration = 1200.0
    threshold = 25_000.0  # 25 km screening threshold

    report = screen_conjunction(
        initial_state1=sat_state,
        initial_state2=sec_state,
        duration=duration,
        dt=1.0,
        threshold_m=threshold,
        object1_id="PROTECTED_SAT_1",
        object2_id="SAFE_SECONDARY_2",
    )

    num = report["numerical_tca"]
    print(f"  Numerical Miss Distance   : {num['miss_distance_m']:.2f} m")
    print(f"  Screening Threshold       : {report['screening_threshold_m']:.1f} m")
    print(f"  Conjunction Candidate     : {report['is_candidate']} [{report['classification']}]")

    # Assertions
    assert report["is_candidate"] is False, "Safe pass should be rejected by screening filter"
    assert report["classification"] == "SAFE_PASS"
    assert num["miss_distance_m"] >= 95_000.0, f"Separation should remain near 100 km, got {num['miss_distance_m']}"
    assert num["miss_distance_m"] >= 0.0, "Miss distance must be non-negative"

    print("  [PASS] Safe pass correctly filtered without false alert.")


def test_near_zero_relative_velocity():
    print("\n[TEST 3] Verifying Near-Zero Relative Velocity Safeguards...")
    # Two co-orbiting objects with identical velocity vectors
    r_rel = np.array([0.0, 5000.0, 0.0])
    v_rel_zero = np.array([0.0, 0.0, 0.0])

    # Case A: Exact zero relative velocity
    res_zero = calculate_linear_cpa(r_rel, v_rel_zero)
    print(f"  Exact zero: t_CPA = {res_zero['t_cpa']}, d_CPA = {res_zero['d_cpa']} m, near_zero = {res_zero['near_zero_velocity']}")
    assert res_zero["near_zero_velocity"] is True
    assert res_zero["t_cpa"] == 0.0
    assert np.isclose(res_zero["d_cpa"], 5000.0)

    # Case B: Infinitesimal velocity magnitude (below numerical tolerance)
    v_rel_tiny = np.array([1e-8, 1e-8, 0.0])  # norm^2 = 2e-16 < 1e-12
    res_tiny = calculate_linear_cpa(r_rel, v_rel_tiny, tol=1e-12)
    print(f"  Infinitesimal: t_CPA = {res_tiny['t_cpa']}, d_CPA = {res_tiny['d_cpa']} m, near_zero = {res_tiny['near_zero_velocity']}")
    assert res_tiny["near_zero_velocity"] is True
    assert res_tiny["t_cpa"] == 0.0
    assert np.isclose(res_tiny["d_cpa"], 5000.0)

    print("  [PASS] Near-zero relative velocity safely handled without division by zero.")


def test_window_constraints():
    print("\n[TEST 4] Verifying Assessment Window Constraints...")
    sat_state, deb_state = create_close_approach_scenario()

    # The unconstrained linear CPA occurs at t = 1000s
    # Truncate the assessment window to [0, 500s]
    truncated_duration = 500.0
    report = screen_conjunction(
        initial_state1=sat_state,
        initial_state2=deb_state,
        duration=truncated_duration,
        dt=1.0,
    )

    lin = report["linear_cpa"]
    num = report["numerical_tca"]

    print(f"  Truncated window          : [0.0, {truncated_duration:.1f}] s")
    print(f"  Linear t_CPA unconstrained: {lin['t_cpa_unconstrained_sec']:.2f} s")
    print(f"  Linear t_CPA constrained  : {lin['t_cpa_sec']:.2f} s (is_constrained: {lin['is_constrained']})")
    print(f"  Numerical TCA             : {num['tca_sec']:.2f} s")

    # Linear CPA should be clamped to 500.0s
    assert lin["is_constrained"] is True
    assert np.isclose(lin["t_cpa_sec"], 500.0)
    assert lin["t_cpa_unconstrained_sec"] > 500.0

    # Numerical TCA must remain within [0.0, 500.0]
    assert 0.0 <= num["tca_sec"] <= truncated_duration
    # At t=500s, objects are approaching; closest approach within this truncated window is at t=500s
    assert np.isclose(num["tca_sec"], truncated_duration)

    print("  [PASS] Window constraints strictly enforced.")


def test_miss_distance_non_negativity():
    print("\n[TEST 5] Verifying Miss Distance Non-Negativity...")
    for offset_y in [0.0, 100.0, 5000.0, 20000.0]:
        sat_state, deb_state = create_close_approach_scenario(debris_offset_y=offset_y)
        r_rel, v_rel = calculate_relative_state(sat_state, deb_state)
        lin = calculate_linear_cpa(r_rel, v_rel)
        assert lin["d_cpa"] >= 0.0, f"Linear d_cpa negative: {lin['d_cpa']}"

        num = calculate_numerical_tca(sat_state, deb_state, duration=100.0, dt=1.0)
        assert num["miss_distance"] >= 0.0, f"Numerical miss distance negative: {num['miss_distance']}"

    print("  [PASS] Miss distance and d_CPA are strictly non-negative across all test scenarios.")


def test_linear_vs_numerical_comparison():
    print("\n[TEST 6] Verifying Linear vs Numerical Comparison & Orbital Curvature...")
    sat_state, deb_state = create_close_approach_scenario()
    duration = 1200.0

    report = screen_conjunction(
        initial_state1=sat_state,
        initial_state2=deb_state,
        duration=duration,
        dt=1.0,
    )

    comp = report["comparison"]
    delta_t = comp["delta_t_sec"]
    delta_d = comp["delta_distance_m"]

    print(f"  Delta TCA (|t_CPA - TCA|) : {delta_t:.2f} s")
    print(f"  Delta Distance (|d_CPA - Miss|) : {delta_d:.2f} m")
    print(f"  Physics explanation       : {comp['note']}")

    # The differences should be substantial because orbital mechanics curved the trajectory
    assert delta_t > 200.0, f"Expected significant delta_t, got {delta_t}"
    assert delta_d > 1500.0, f"Expected significant delta_d, got {delta_d}"
    assert "Linear CPA assumes constant relative velocity" in comp["note"]

    print("  [PASS] Linear vs. numerical distinction and physics effects properly captured.")


def test_batch_catalog_screening():
    print("\n[TEST 7] Verifying Batch Catalog Screening...")
    sat_state, deb1_state = create_close_approach_scenario(debris_offset_y=10000.0)
    _, deb2_state = create_close_approach_scenario(debris_offset_y=20000.0)

    # Safe pass object (100km higher orbit)
    v_safe = np.sqrt(MU_EARTH / 7_100_000.0)
    deb3_state = np.array([7_100_000.0, 0.0, 0.0, 0.0, v_safe, 0.0])

    catalog = [
        {"id": "DEBRIS_SAFE_100KM", "state": deb3_state},
        {"id": "DEBRIS_CLOSE_10KM", "state": deb1_state},
        {"id": "DEBRIS_MID_20KM", "state": deb2_state},
    ]

    candidates, all_reports = filter_conjunction_candidates(
        primary_state=sat_state,
        secondary_catalog=catalog,
        duration=1200.0,
        dt=1.0,
        threshold_m=25_000.0,
        primary_id="CARTOSAT_PRIMARY",
    )

    print(f"  Total catalog objects screened: {len(all_reports)}")
    print(f"  Conjunction candidates found  : {len(candidates)}")
    for i, c in enumerate(candidates, start=1):
        print(f"    Candidate {i}: {c['object2_id']} | Miss Distance: {c['numerical_tca']['miss_distance_m']:.2f} m | TCA: {c['numerical_tca']['tca_sec']:.2f} s")

    assert len(all_reports) == 3
    assert len(candidates) == 2  # DEBRIS_SAFE_100KM is filtered out (> 25 km threshold)
    # Sorted by miss distance in ascending order
    assert candidates[0]["object2_id"] == "DEBRIS_CLOSE_10KM"
    assert candidates[1]["object2_id"] == "DEBRIS_MID_20KM"
    assert candidates[0]["numerical_tca"]["miss_distance_m"] < candidates[1]["numerical_tca"]["miss_distance_m"]

    print("  [PASS] Batch catalog screening successfully executed.")


def run_all_tests():
    print("=" * 70)
    print("D2 CONJUNCTION ASSESSMENT VERIFICATION SUITE")
    print("=" * 70)

    test_controlled_close_approach()
    test_safe_pass()
    test_near_zero_relative_velocity()
    test_window_constraints()
    test_miss_distance_non_negativity()
    test_linear_vs_numerical_comparison()
    test_batch_catalog_screening()

    print("\n" + "=" * 70)
    print("ALL CONJUNCTION ASSESSMENT TESTS PASSED")
    print("=" * 70)


if __name__ == "__main__":
    run_all_tests()
