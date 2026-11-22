"""
Scenarios/s2_close_approach.py
==============================
Scenario S2: Controlled Two-Object Close Approach Conjunction.
Strictly following Section 5, Section 11, and Section 12.1 of the Technical Guide.

Objectives:
- Two objects in circular LEO (r0 = 7000 km) with controlled initial offset (10 km).
- Calculate linear Closest Point of Approach (CPA) approximation.
- Calculate numerically propagated Time of Closest Approach (TCA) and miss distance.
- Verify numerical TCA = 769.63 s and miss distance = 1563.48 m.
- Distinguish linear CPA approximation from curved numerical orbit trajectory.
"""

from typing import Dict, Any
import numpy as np

from D2.scenarios.close_approach import create_close_approach_scenario
from D2.conjunction.screening import screen_conjunction


def run_scenario_s2(duration: float = 1000.0, dt: float = 1.0) -> Dict[str, Any]:
    s1, s2 = create_close_approach_scenario()

    record = screen_conjunction(
        initial_state1=s1,
        initial_state2=s2,
        duration=duration,
        dt=dt,
        threshold_m=25000.0,
        object1_id="PROTECTED_SAT",
        object2_id="SECONDARY_OBJ",
        refine_tca=True
    )

    num_tca = record["numerical_tca"]["tca_sec"]
    num_miss = record["numerical_tca"]["miss_distance_m"]
    rel_speed = record["numerical_tca"]["relative_speed_mps"]
    linear_cpa = record["linear_cpa"]["d_cpa_m"]

    # Verify baseline invariants
    tca_match = np.isclose(num_tca, 769.631971, atol=0.05)
    miss_match = np.isclose(num_miss, 1563.476320, atol=0.1)

    passed = (
        tca_match and
        miss_match and
        record["is_candidate"] is True
    )

    return {
        "scenario_id": "S2_CLOSE_APPROACH",
        "status": "PASSED" if passed else "FAILED",
        "nominal_tca_seconds": num_tca,
        "nominal_miss_distance_m": num_miss,
        "linear_cpa_miss_distance_m": linear_cpa,
        "linear_vs_numerical_diff_m": abs(linear_cpa - num_miss),
        "relative_speed_at_tca_mps": rel_speed,
        "screening_classification": record["classification"],
        "is_conjunction_candidate": record["is_candidate"],
    }


if __name__ == "__main__":
    res = run_scenario_s2()
    print("S2 Result:", res)
