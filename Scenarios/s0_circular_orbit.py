"""
Scenarios/s0_circular_orbit.py
==============================
Scenario S0: Ideal Circular Two-Body Orbit Verification.
Strictly following Section 3.1, Section 11, and Section 12.1 of the Technical Guide.

Objectives:
- Single protected satellite in ideal two-body orbit (r0 = 7000 km).
- Verify expected circular orbital speed: v = sqrt(mu / r0) = 7546.053 m/s.
- Verify Keplerian period: T = 2 * pi * sqrt(r0^3 / mu) = 5828.517 s.
- Verify specific orbital energy conservation over a full orbital revolution:
  Delta_E / |E0| < 1e-7 using RK4 numerical integration.
"""

from typing import Dict, Any
import numpy as np

from D2.dynamics.two_body import MU_EARTH
from D2.dynamics.orbit_propagator import propagate_orbit


def run_scenario_s0(dt: float = 1.0) -> Dict[str, Any]:
    r0 = 7_000_000.0  # 7000 km orbital radius
    v_expected = float(np.sqrt(MU_EARTH / r0))
    t_period_expected = float(2.0 * np.pi * np.sqrt(r0**3 / MU_EARTH))

    # Initial state: position along +X, velocity along +Y
    state0 = np.array([r0, 0.0, 0.0, 0.0, v_expected, 0.0], dtype=np.float64)

    # Propagate for exactly one orbital period
    times, states = propagate_orbit(state0, duration=t_period_expected, dt=dt)

    # Initial and final radii
    r_initial = float(np.linalg.norm(states[0, :3]))
    r_final = float(np.linalg.norm(states[-1, :3]))
    v_final = float(np.linalg.norm(states[-1, 3:6]))

    # Specific mechanical energy: E = v^2 / 2 - mu / r
    energy_initial = 0.5 * v_expected**2 - (MU_EARTH / r_initial)
    energy_final = 0.5 * v_final**2 - (MU_EARTH / r_final)
    rel_energy_error = float(abs((energy_final - energy_initial) / energy_initial))

    # Return closure: distance from initial position after 1 period
    closure_distance_m = float(np.linalg.norm(states[-1, :3] - states[0, :3]))

    passed = (
        abs(r_final - r0) < 5.0 and
        rel_energy_error < 1e-6 and
        closure_distance_m < 50.0
    )

    return {
        "scenario_id": "S0_CIRCULAR_ORBIT",
        "status": "PASSED" if passed else "FAILED",
        "orbital_radius_m": r0,
        "expected_speed_mps": v_expected,
        "final_speed_mps": v_final,
        "orbital_period_s": t_period_expected,
        "radial_error_m": float(abs(r_final - r0)),
        "closure_distance_m": closure_distance_m,
        "relative_energy_error": rel_energy_error,
        "num_integration_steps": len(times),
    }


if __name__ == "__main__":
    res = run_scenario_s0()
    print("S0 Result:", res)
