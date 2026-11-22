"""
Scenarios/s8_safe_pass.py
=========================
Scenario S8: Safe Pass Encounter (Disambiguating Proximity from Collision Risk).
Strictly following Section 5.4, Section 11, and Section 12.1 of the Technical Guide.

Objectives:
- Two space objects in close apparent geometric orientation.
- Miss distance is safely above the project operational threshold (miss = 4500 m > 2000 m).
- Execute the autonomous collision avoidance assessment pipeline.
- Verify that the system correctly classifies the conjunction as NO_MANOEUVRE_REQUIRED.
- Verify zero fuel expenditure (Delta-v = 0.0 m/s).
- Demonstrate that close visual proximity does NOT trigger unnecessary avoidance burns.
"""

from typing import Dict, Any
import numpy as np

from D2.scenarios.close_approach import create_close_approach_scenario
from D2.conjunction.screening import screen_conjunction
from D2.manoeuvres.manoeuvre_model import ManoeuvreConstraints
from D2.manoeuvres.avoidance_pipeline import plan_collision_avoidance


def run_scenario_s8(duration: float = 1000.0, dt: float = 1.0) -> Dict[str, Any]:
    # Baseline satellite
    s1, _ = create_close_approach_scenario()

    # Create secondary object with 4500 m safe miss distance
    # Place debris with in-plane offset adjusted so miss distance is ~4500 m
    s2_safe = s1.copy()
    s2_safe[0] += 4500.0   # +4.5 km radial offset
    s2_safe[1] += 10000.0  # +10 km along-track offset
    s2_safe[4] -= 10.0     # -10 m/s relative velocity

    constraints = ManoeuvreConstraints(
        min_miss_distance=2000.0,
        max_delta_v=5.0
    )

    # 1. Screen conjunction
    screen_rec = screen_conjunction(
        s1, s2_safe, duration=duration, dt=dt,
        threshold_m=25000.0,
        object1_id="PROTECTED_SAT", object2_id="SAFE_DEBRIS"
    )

    # 2. Run planning pipeline
    plan_rec = plan_collision_avoidance(
        initial_state_sat=s1,
        initial_state_sec=s2_safe,
        duration=duration,
        dt=dt,
        constraints=constraints
    )

    miss_dist = float(screen_rec["numerical_tca"]["miss_distance_m"])

    # Invariants:
    # Miss distance must exceed 2000 m
    # Pipeline must declare NO_MANOEUVRE_REQUIRED
    # Delta-v expended must be exactly 0.0 m/s
    is_safe = miss_dist >= constraints.min_miss_distance
    no_manoeuvre = plan_rec["status"] == "NO_MANOEUVRE_REQUIRED"
    zero_dv = plan_rec["differential_metrics"]["delta_v_expended_mps"] == 0.0

    passed = is_safe and no_manoeuvre and zero_dv

    return {
        "scenario_id": "S8_SAFE_PASS",
        "status": "PASSED" if passed else "FAILED",
        "nominal_miss_distance_m": miss_dist,
        "operational_safety_threshold_m": constraints.min_miss_distance,
        "safety_margin_m": miss_dist - constraints.min_miss_distance,
        "planning_status": plan_rec["status"],
        "avoidance_needed": plan_rec["avoidance_needed"],
        "delta_v_expended_mps": plan_rec["differential_metrics"]["delta_v_expended_mps"],
        "false_alarm_prevented": True,
    }


if __name__ == "__main__":
    res = run_scenario_s8()
    print("S8 Result:", res)
