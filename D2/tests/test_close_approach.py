"""
D2/tests/test_close_approach.py
===============================
Verification test suite for D2 close-approach scenario generation.

Tests:
1. Both objects have six-dimensional state vectors.
2. All values are finite.
3. Both objects have the expected initial orbital radius.
4. Initial separation is 10,000 metres.
5. Initial relative velocity magnitude is 10 metres/second.
6. Relative position and velocity calculations are correct.
7. Verification with orbit propagator and two-body dynamics.

Run:
    python -m D2.tests.test_close_approach
"""

import numpy as np

from D2.dynamics.two_body import MU_EARTH
from D2.dynamics.orbit_propagator import propagate_orbit
from D2.scenarios.close_approach import (
    create_close_approach_scenario,
    calculate_relative_state,
    DEFAULT_ORBITAL_RADIUS,
    DEFAULT_DEBRIS_OFFSET_Y,
    DEFAULT_DEBRIS_DELTA_VY,
)


def run_tests():
    print("=" * 65)
    print("D2 CLOSE-APPROACH SCENARIO VERIFICATION SUITE")
    print("=" * 65)

    # Generate the scenario
    sat_state, deb_state = create_close_approach_scenario()

    print("\nProtected satellite initial state:")
    print(f"  Position (m) : {sat_state[:3]}")
    print(f"  Velocity (m/s): {sat_state[3:]}")

    print("\nSecondary debris initial state:")
    print(f"  Position (m) : {deb_state[:3]}")
    print(f"  Velocity (m/s): {deb_state[3:]}")

    # -------------------------------------------------------------
    # 1. Both objects have six-dimensional state vectors
    # -------------------------------------------------------------
    print("\n[CHECK 1] Verifying six-dimensional state vector dimensions...")
    assert isinstance(sat_state, np.ndarray), "Protected satellite state must be a numpy ndarray"
    assert isinstance(deb_state, np.ndarray), "Secondary debris state must be a numpy ndarray"
    assert sat_state.shape == (6,), f"Satellite state shape must be (6,), got {sat_state.shape}"
    assert deb_state.shape == (6,), f"Debris state shape must be (6,), got {deb_state.shape}"
    assert sat_state.dtype == np.float64, f"Satellite dtype must be float64, got {sat_state.dtype}"
    assert deb_state.dtype == np.float64, f"Debris dtype must be float64, got {deb_state.dtype}"
    print("  [PASS] Both state vectors are 6-dimensional float64 arrays.")

    # -------------------------------------------------------------
    # 2. All values are finite
    # -------------------------------------------------------------
    print("\n[CHECK 2] Verifying all values are finite (no NaN or Inf)...")
    assert np.all(np.isfinite(sat_state)), "Protected satellite state contains non-finite values."
    assert np.all(np.isfinite(deb_state)), "Secondary debris state contains non-finite values."
    print("  [PASS] All state vector values are strictly finite.")

    # -------------------------------------------------------------
    # 3. Both objects have expected initial orbital radius
    # -------------------------------------------------------------
    print("\n[CHECK 3] Verifying initial orbital radii...")
    r_sat = np.linalg.norm(sat_state[:3])
    r_deb = np.linalg.norm(deb_state[:3])

    expected_sat_r = DEFAULT_ORBITAL_RADIUS  # 7,000,000.0 m
    expected_deb_r = np.sqrt(DEFAULT_ORBITAL_RADIUS**2 + DEFAULT_DEBRIS_OFFSET_Y**2)

    print(f"  Protected satellite radius : {r_sat:.3f} m (Expected: {expected_sat_r:.3f} m)")
    print(f"  Secondary debris radius    : {r_deb:.3f} m (Expected: {expected_deb_r:.3f} m)")

    assert np.isclose(r_sat, expected_sat_r), f"Satellite radius mismatch: {r_sat} != {expected_sat_r}"
    assert np.isclose(r_deb, expected_deb_r), f"Debris radius mismatch: {r_deb} != {expected_deb_r}"
    # Both objects are at nominal ~7,000 km orbital radius (within 10 m)
    assert abs(r_sat - 7_000_000.0) < 1e-6, "Satellite radius is not 7,000,000 m"
    assert abs(r_deb - 7_000_000.0) < 10.0, "Debris radius deviates beyond expected in-plane geometry"
    print("  [PASS] Both objects have the expected initial orbital radius.")

    # -------------------------------------------------------------
    # 4. Initial separation is 10,000 metres
    # -------------------------------------------------------------
    print("\n[CHECK 4] Verifying initial separation distance...")
    r_rel = deb_state[:3] - sat_state[:3]
    initial_separation = float(np.linalg.norm(r_rel))
    expected_separation = 10_000.0

    print(f"  Calculated initial separation: {initial_separation:.3f} m (Expected: {expected_separation:.3f} m)")
    assert np.isclose(initial_separation, expected_separation), (
        f"Initial separation mismatch: {initial_separation} != {expected_separation}"
    )
    print("  [PASS] Initial separation is exactly 10,000 metres.")

    # -------------------------------------------------------------
    # 5. Initial relative velocity magnitude is 10 metres/second
    # -------------------------------------------------------------
    print("\n[CHECK 5] Verifying initial relative velocity magnitude...")
    v_rel = deb_state[3:] - sat_state[3:]
    initial_relative_speed = float(np.linalg.norm(v_rel))
    expected_rel_speed = 10.0

    print(f"  Calculated relative speed: {initial_relative_speed:.3f} m/s (Expected: {expected_rel_speed:.3f} m/s)")
    assert np.isclose(initial_relative_speed, expected_rel_speed), (
        f"Relative speed mismatch: {initial_relative_speed} != {expected_rel_speed}"
    )
    print("  [PASS] Initial relative velocity magnitude is exactly 10 metres/second.")

    # -------------------------------------------------------------
    # 6. Relative position and velocity calculations are correct
    # -------------------------------------------------------------
    print("\n[CHECK 6] Verifying relative position and velocity vector calculations...")
    expected_r_rel = np.array([0.0, 10_000.0, 0.0])
    expected_v_rel = np.array([0.0, -10.0, 0.0])

    print(f"  r_rel: {r_rel} (Expected: {expected_r_rel})")
    print(f"  v_rel: {v_rel} (Expected: {expected_v_rel})")

    assert np.allclose(r_rel, expected_r_rel), f"r_rel incorrect: {r_rel} != {expected_r_rel}"
    assert np.allclose(v_rel, expected_v_rel), f"v_rel incorrect: {v_rel} != {expected_v_rel}"

    # Verify calculate_relative_state function
    r_rel_calc, v_rel_calc = calculate_relative_state(sat_state, deb_state)
    assert np.allclose(r_rel_calc, expected_r_rel), "calculate_relative_state returned wrong r_rel"
    assert np.allclose(v_rel_calc, expected_v_rel), "calculate_relative_state returned wrong v_rel"

    # Verify return_relative=True keyword argument
    _, _, r_rel_kw, v_rel_kw = create_close_approach_scenario(return_relative=True)
    assert np.allclose(r_rel_kw, expected_r_rel), "return_relative=True returned wrong r_rel"
    assert np.allclose(v_rel_kw, expected_v_rel), "return_relative=True returned wrong v_rel"

    # Verify circular velocity formula v = sqrt(mu / r)
    expected_v_circ = np.sqrt(MU_EARTH / 7_000_000.0)
    assert np.isclose(sat_state[4], expected_v_circ), (
        f"Circular velocity calculation incorrect: {sat_state[4]} != {expected_v_circ}"
    )
    assert np.isclose(deb_state[4], expected_v_circ - 10.0), (
        f"Debris velocity calculation incorrect: {deb_state[4]} != {expected_v_circ - 10.0}"
    )
    print("  [PASS] Relative position and velocity calculations are fully validated.")

    # -------------------------------------------------------------
    # 7. Dynamic propagation check with D2 orbit propagator
    # -------------------------------------------------------------
    print("\n[CHECK 7] Verifying dynamic propagation compatibility (D2 RK4 two-body)...")
    duration = 60.0
    dt = 1.0

    times1, states1 = propagate_orbit(sat_state, duration=duration, dt=dt)
    times2, states2 = propagate_orbit(deb_state, duration=duration, dt=dt)

    assert states1.shape == (61, 6), f"Propagated states1 shape mismatch: {states1.shape}"
    assert states2.shape == (61, 6), f"Propagated states2 shape mismatch: {states2.shape}"
    assert np.all(np.isfinite(states1)), "Propagated satellite states contain non-finite values."
    assert np.all(np.isfinite(states2)), "Propagated debris states contain non-finite values."

    print(f"  Propagated 60s (61 steps): Sat position={states1[-1, :3]}, Debris position={states2[-1, :3]}")
    print("  [PASS] Both states propagate cleanly through D2 two-body RK4 integrator.")

    print("\n" + "=" * 65)
    print("CLOSE-APPROACH SCENARIO TEST PASSED")
    print("=" * 65)


if __name__ == "__main__":
    run_tests()

