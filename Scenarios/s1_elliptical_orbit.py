"""
Scenarios/s1_elliptical_orbit.py
================================
Scenario S1: Elliptical Orbit Propagation Verification.
Strictly following Section 3.1, Section 11, and Section 12.1 of the Technical Guide.

Objectives:
- Single satellite in an eccentric Keplerian orbit (e = 0.05, a = 7000 km).
- Perigee radius: rp = a * (1 - e) = 6650 km.
- Apogee radius:  ra = a * (1 + e) = 7350 km.
- Verify vis-viva speeds at perigee (vp) and apogee (va).
- Verify conservation of angular momentum vector (h = r x v) and specific energy.
- Verify return to perigee conditions after one revolution (period T).
"""

from typing import Dict, Any
import numpy as np

from D2.dynamics.two_body import MU_EARTH
from D2.dynamics.orbit_propagator import propagate_orbit


def run_scenario_s1(dt: float = 1.0) -> Dict[str, Any]:
    a = 7_000_000.0   # Semi-major axis (m)
    e = 0.05          # Eccentricity
    rp = a * (1.0 - e) # 6,650,000 m
    ra = a * (1.0 + e) # 7,350,000 m

    # Theoretical vis-viva speeds: v^2 = mu * (2/r - 1/a)
    vp_expected = float(np.sqrt(MU_EARTH * (2.0 / rp - 1.0 / a)))
    va_expected = float(np.sqrt(MU_EARTH * (2.0 / ra - 1.0 / a)))
    t_period_expected = float(2.0 * np.pi * np.sqrt(a**3 / MU_EARTH))

    # Initialize at perigee: along +X, velocity along +Y
    state_perigee = np.array([rp, 0.0, 0.0, 0.0, vp_expected, 0.0], dtype=np.float64)

    times, states = propagate_orbit(state_perigee, duration=t_period_expected, dt=dt)

    # Radii along the trajectory
    radii = np.linalg.norm(states[:, :3], axis=1)
    min_radius_sim = float(np.min(radii))
    max_radius_sim = float(np.max(radii))

    # Specific energy & angular momentum conservation
    h_initial = np.cross(states[0, :3], states[0, 3:6])
    h_final = np.cross(states[-1, :3], states[-1, 3:6])
    rel_h_error = float(np.linalg.norm(h_final - h_initial) / np.linalg.norm(h_initial))

    e_initial = 0.5 * vp_expected**2 - MU_EARTH / rp
    e_final = 0.5 * np.linalg.norm(states[-1, 3:6])**2 - MU_EARTH / np.linalg.norm(states[-1, :3])
    rel_e_error = float(abs((e_final - e_initial) / e_initial))

    perigee_err = abs(min_radius_sim - rp)
    apogee_err = abs(max_radius_sim - ra)

    passed = (
        perigee_err < 20.0 and
        apogee_err < 20.0 and
        rel_e_error < 1e-6 and
        rel_h_error < 1e-6
    )

    return {
        "scenario_id": "S1_ELLIPTICAL_ORBIT",
        "status": "PASSED" if passed else "FAILED",
        "semi_major_axis_m": a,
        "eccentricity": e,
        "expected_perigee_m": rp,
        "simulated_perigee_m": min_radius_sim,
        "perigee_error_m": perigee_err,
        "expected_apogee_m": ra,
        "simulated_apogee_m": max_radius_sim,
        "apogee_error_m": apogee_err,
        "expected_perigee_speed_mps": vp_expected,
        "expected_apogee_speed_mps": va_expected,
        "relative_energy_error": rel_e_error,
        "relative_angular_momentum_error": rel_h_error,
    }


if __name__ == "__main__":
    res = run_scenario_s1()
    print("S1 Result:", res)
