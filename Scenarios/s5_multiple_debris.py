"""
Scenarios/s5_multiple_debris.py
===============================
Scenario S5: Multiple Debris Population Screening and Re-Screening.
Strictly following Section 4.2, Section 5.4, Section 7.4, and Section 11 of the Technical Guide.

Objectives:
- 1 protected primary satellite in LEO (7000 km circular orbit).
- Population of 10 uncooperative space debris objects distributed in orbit.
- Broad-phase screening (25 km filter) identifies candidates.
- Plan avoidance manoeuvre for the primary critical threat.
- Multi-target re-screening: verify post-manoeuvre trajectory against ALL 10 debris objects
  to guarantee the manoeuvre does not create a new collision hazard.
"""

from typing import Dict, Any, List
import numpy as np

from D2.dynamics.two_body import MU_EARTH
from D2.dynamics.orbit_propagator import propagate_orbit
from D2.conjunction.tca import calculate_numerical_tca
from D2.conjunction.screening import screen_conjunction
from D2.manoeuvres.manoeuvre_model import ImpulsiveManoeuvre, rtn_to_eci, DIRECTION_VECTORS_RTN


def run_scenario_s5(duration: float = 1200.0, dt: float = 1.0) -> Dict[str, Any]:
    r0 = 7_000_000.0
    v_circ = float(np.sqrt(MU_EARTH / r0))

    # Protected Primary Satellite
    sat_state = np.array([r0, 0.0, 0.0, 0.0, v_circ, 0.0], dtype=np.float64)

    # 10 Debris objects with varied initial geometry
    # Object 0 is the critical threat (10 km offset, -10 m/s vy)
    debris_catalog = [
        {"id": "DEBRIS_01_CRITICAL", "offset": [0.0, 10000.0, 0.0], "vel_offset": [0.0, -10.0, 0.0]},
        {"id": "DEBRIS_02_IN_PLANE_FAR", "offset": [0.0, 50000.0, 0.0], "vel_offset": [0.0, -5.0, 0.0]},
        {"id": "DEBRIS_03_RADIAL_HIGH", "offset": [15000.0, 0.0, 0.0], "vel_offset": [-5.0, 0.0, 0.0]},
        {"id": "DEBRIS_04_OUT_OF_PLANE", "offset": [0.0, 5000.0, 20000.0], "vel_offset": [0.0, 0.0, -15.0]},
        {"id": "DEBRIS_05_CO_ORBITAL", "offset": [0.0, -30000.0, 0.0], "vel_offset": [0.0, 2.0, 0.0]},
        {"id": "DEBRIS_06_RETROGRADE_FAST", "offset": [25000.0, 10000.0, 0.0], "vel_offset": [-2.0, -20.0, 0.0]},
        {"id": "DEBRIS_07_INCLINED", "offset": [0.0, 12000.0, -15000.0], "vel_offset": [0.0, -8.0, 10.0]},
        {"id": "DEBRIS_08_POLAR_CROSS", "offset": [5000.0, 0.0, 35000.0], "vel_offset": [-1.0, 0.0, -25.0]},
        {"id": "DEBRIS_09_SAFE_PASS", "offset": [0.0, 8000.0, 0.0], "vel_offset": [0.0, -3.0, 0.0]},
        {"id": "DEBRIS_10_DISTANT", "offset": [-40000.0, 100000.0, 0.0], "vel_offset": [10.0, -10.0, 0.0]},
    ]

    debris_states = []
    for d in debris_catalog:
        pos = sat_state[:3] + np.array(d["offset"])
        vel = sat_state[3:] + np.array(d["vel_offset"])
        debris_states.append(np.concatenate((pos, vel)))

    # Step 1: Pre-manoeuvre screening against all 10 debris objects
    initial_screen_results = []
    candidates = []
    for i, d_state in enumerate(debris_states):
        res = screen_conjunction(
            sat_state, d_state, duration=duration, dt=dt,
            object1_id="PROTECTED_SAT", object2_id=debris_catalog[i]["id"],
            threshold_m=25000.0
        )
        initial_screen_results.append(res)
        if res["is_candidate"]:
            candidates.append({
                "id": debris_catalog[i]["id"],
                "miss_distance_m": res["numerical_tca"]["miss_distance_m"],
                "tca_s": res["numerical_tca"]["tca_sec"]
            })

    # Sort candidates by miss distance
    candidates.sort(key=lambda x: x["miss_distance_m"])
    primary_threat = candidates[0] if candidates else None

    # Step 2: Apply avoidance manoeuvre (-3.0 m/s along -R at t = 170 s)
    t_burn = 170.0
    dv_rtn = np.array([-3.0, 0.0, 0.0])  # -R radial burn
    times_pre, states_pre = propagate_orbit(sat_state, duration=t_burn, dt=dt)
    sat_at_burn = states_pre[-1].copy()
    dv_eci = rtn_to_eci(dv_rtn, sat_at_burn[:3], sat_at_burn[3:])
    sat_post_burn = sat_at_burn.copy()
    sat_post_burn[3:] += dv_eci

    # Propagate modified trajectory from t_burn to duration
    times_post, states_post = propagate_orbit(sat_post_burn, duration=duration - t_burn, dt=dt)
    full_mod_states = np.vstack((states_pre[:-1], states_post))

    # Step 3: Multi-target re-screening against ALL 10 debris objects post-manoeuvre
    post_screen_results = []
    for i, d_state in enumerate(debris_states):
        # Propagate debris to t_burn to align epochs
        t_d, s_d = propagate_orbit(d_state, duration=t_burn, dt=dt)
        d_at_burn = s_d[-1]

        tca_post = calculate_numerical_tca(
            sat_post_burn, d_at_burn,
            duration=duration - t_burn, dt=dt
        )
        post_screen_results.append({
            "debris_id": debris_catalog[i]["id"],
            "post_miss_distance_m": tca_post["miss_distance"],
            "post_tca_s": tca_post["tca"] + t_burn,
        })

    # Verify primary threat clearance expanded
    orig_threat_post = [r for r in post_screen_results if r["debris_id"] == "DEBRIS_01_CRITICAL"][0]
    threat_cleared = orig_threat_post["post_miss_distance_m"] > 2000.0

    # Verify no new secondary object was put into critical hazard (< 2000 m)
    min_post_miss = min(r["post_miss_distance_m"] for r in post_screen_results)
    no_secondary_hazard = min_post_miss >= 2000.0

    passed = (
        len(candidates) >= 1 and
        threat_cleared and
        no_secondary_hazard
    )

    return {
        "scenario_id": "S5_MULTIPLE_DEBRIS",
        "status": "PASSED" if passed else "FAILED",
        "total_objects_screened": len(debris_catalog),
        "conjunction_candidates_detected": len(candidates),
        "primary_threat_id": primary_threat["id"] if primary_threat else None,
        "primary_nominal_miss_m": primary_threat["miss_distance_m"] if primary_threat else None,
        "primary_post_miss_m": orig_threat_post["post_miss_distance_m"],
        "minimum_post_manoeuvre_clearance_m": min_post_miss,
        "all_debris_cleared_safely": no_secondary_hazard,
    }


if __name__ == "__main__":
    res = run_scenario_s5()
    print("S5 Result:", res)
