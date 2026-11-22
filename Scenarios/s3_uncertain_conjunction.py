"""
Scenarios/s3_uncertain_conjunction.py
=====================================
Scenario S3: Uncertain Conjunction Assessment with Covariance Propagation.
Strictly following Section 6, Section 11, and Section 12.1 of the Technical Guide.

Objectives:
- Ingest state uncertainty via 6x6 covariance matrices for both space objects.
- Combine covariances under independent-error assumption (P_rel = P1 + P2).
- Propagate combined covariance along orbital path using 42-state Variational STM.
- Project 3D covariance onto the 2D encounter plane perpendicular to relative velocity.
- Compute formal collision probability (Pc) via Foster (1992) integration.
- Verify asymptotic numerical underflow handling without reporting zero.
"""

from typing import Dict, Any
import numpy as np

from D2.scenarios.close_approach import create_close_approach_scenario
from D2.conjunction.tca import calculate_numerical_tca
from D2.uncertainty.covariance import (
    create_diagonal_covariance,
    combine_relative_covariance as combine_covariances,
    propagate_covariance_to_tca,
)
from D2.uncertainty.collision_probability import calculate_collision_probability


def run_scenario_s3(hard_body_radius: float = 5.0, duration: float = 1000.0, dt: float = 1.0) -> Dict[str, Any]:
    s1, s2 = create_close_approach_scenario()

    # Define realistic 6x6 covariances (position 1-sigma: 50-150 m, velocity 1-sigma: 0.05-0.15 m/s)
    c1 = create_diagonal_covariance(pos_std_m=[50.0, 100.0, 20.0], vel_std_mps=[0.05, 0.1, 0.02])
    c2 = create_diagonal_covariance(pos_std_m=[80.0, 150.0, 30.0], vel_std_mps=[0.08, 0.15, 0.03])

    # 1. Numerical TCA
    tca_res = calculate_numerical_tca(s1, s2, duration=duration, dt=dt)
    tca = float(tca_res["tca"])
    miss_dist = float(tca_res["miss_distance"])

    # 2. Propagate covariances to TCA using synchronized two-body STM
    sync_res = propagate_covariance_to_tca(
        state1_0=s1,
        cov1_0=c1,
        state2_0=s2,
        cov2_0=c2,
        tca=tca,
        dt=dt
    )
    cov_rel_tca = sync_res["cov_rel_tca"]
    r_rel_tca = sync_res["r_rel_tca"]
    v_rel_tca = sync_res["v_rel_tca"]

    # 3. Calculate Foster Pc
    pc_res = calculate_collision_probability(
        r_rel_tca=r_rel_tca,
        v_rel_tca=v_rel_tca,
        cov_rel_tca=cov_rel_tca,
        hard_body_radius=hard_body_radius
    )

    pc_val = pc_res["pc"]
    log10_pc = pc_res["log10_pc"]
    status = pc_res["status"]

    # Invariants: Pc is small (between 10^-18 and 10^-10) due to 5m HBR relative to 1563m miss distance
    pc_match = (pc_val is not None and 1e-18 <= pc_val <= 1e-10)
    underflow_preserved = (status == "NUMERICAL_UNDERFLOW")

    passed = (
        pc_match and
        underflow_preserved and
        pc_res["is_valid"] is True
    )

    return {
        "scenario_id": "S3_UNCERTAIN_CONJUNCTION",
        "status": "PASSED" if passed else "FAILED",
        "tca_seconds": tca,
        "miss_distance_m": miss_dist,
        "hard_body_radius_m": hard_body_radius,
        "collision_probability": pc_val,
        "log10_pc": log10_pc,
        "pc_status": status,
        "asymptotic_tail_underflow_preserved": underflow_preserved,
        "quality_flags": pc_res["quality_flags"],
        "consequence_indicators": pc_res.get("consequence_indicators"),
    }


if __name__ == "__main__":
    res = run_scenario_s3()
    print("S3 Result:", res)
