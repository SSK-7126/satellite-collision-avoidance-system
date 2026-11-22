"""
Scenarios/s4_avoidance_burn.py
==============================
Scenario S4: Avoidance Burn Execution and Post-Manoeuvre Re-Screening.
Strictly following Section 7, Section 11, and Section 12.1 of the Technical Guide.

Objectives:
- Full end-to-end autonomous avoidance manoeuvre planning on the baseline LEO encounter.
- Select optimal candidate from discrete RTN catalog: MAN_006_-R_3.00mps_T170s.
- Apply impulsive Delta-v (-3.00 m/s along -R at t_burn = 169.63 s).
- Re-propagate modified trajectory and synchronize covariance to the new TCA epoch.
- Re-screen conjunction to verify miss distance expansion beyond 2000 m threshold.
- Quantify Delta miss distance (+890.94 m), Delta TCA (+133.40 s), and Pc attenuation (8.5 decades).
"""

from typing import Dict, Any
import numpy as np

from D2.scenarios.close_approach import create_close_approach_scenario
from D2.uncertainty.covariance import create_diagonal_covariance
from D2.manoeuvres.manoeuvre_model import ManoeuvreConstraints
from D2.manoeuvres.avoidance_pipeline import plan_collision_avoidance
from D2.manoeuvres.propulsion import calculate_propellant_mass_ideal


def run_scenario_s4(duration: float = 1000.0, dt: float = 1.0) -> Dict[str, Any]:
    s1, s2 = create_close_approach_scenario()

    # Baseline 6x6 covariances
    c1 = create_diagonal_covariance(pos_std_m=[50.0, 100.0, 20.0], vel_std_mps=[0.05, 0.1, 0.02])
    c2 = create_diagonal_covariance(pos_std_m=[80.0, 150.0, 30.0], vel_std_mps=[0.08, 0.15, 0.03])

    constraints = ManoeuvreConstraints(
        max_delta_v=5.0,
        min_lead_time=120.0,
        max_trajectory_deviation=5000.0,
        min_miss_distance=2000.0,
        max_target_pc=1e-6
    )

    res = plan_collision_avoidance(
        initial_state_sat=s1,
        initial_state_sec=s2,
        duration=duration,
        dt=dt,
        initial_cov_sat=c1,
        initial_cov_sec=c2,
        hard_body_radius=5.0,
        constraints=constraints
    )

    nom = res["nominal_assessment"]
    post = res["post_manoeuvre_assessment"]
    diff = res["differential_metrics"]
    man = res["selected_manoeuvre"]

    # Compute propellant consumption for spacecraft mass = 1000 kg, Isp = 300 s
    fuel_used_kg = calculate_propellant_mass_ideal(
        delta_v_mps=man.delta_v_magnitude,
        initial_mass_kg=1000.0,
        isp_s=300.0
    )

    # Invariant checks: radial inward burn (-R, 3.0 m/s, T170s)
    assert res["status"] == "SUCCESS"
    assert res["avoidance_needed"] is True
    assert man.direction_label == "-R"
    assert np.isclose(man.delta_v_magnitude, 3.00, atol=1e-3)
    assert np.isclose(man.burn_time, 169.63, atol=1.0)
    assert np.isclose(nom["miss_distance_m"], 1563.48, atol=1.0)
    assert post["post_manoeuvre_miss_distance_m"] >= constraints.min_miss_distance
    assert diff["delta_miss_distance_m"] > 0.0

    passed = True

    return {
        "scenario_id": "S4_AVOIDANCE_BURN",
        "status": "PASSED" if passed else "FAILED",
        "selected_manoeuvre_id": man.manoeuvre_id,
        "delta_v_magnitude_mps": man.delta_v_magnitude,
        "delta_v_direction_rtn": man.direction_label,
        "burn_epoch_seconds": man.burn_time,
        "nominal_miss_distance_m": float(nom["miss_distance_m"]),
        "post_manoeuvre_miss_distance_m": float(post["post_manoeuvre_miss_distance_m"]),
        "miss_distance_gain_m": float(diff["delta_miss_distance_m"]),
        "tca_shift_seconds": float(diff["delta_tca_sec"]),
        "nominal_collision_probability": nom.get("collision_probability"),
        "post_collision_probability": post.get("post_manoeuvre_pc"),
        "estimated_fuel_consumed_kg": fuel_used_kg,
        "operational_threshold_satisfied": bool(post["post_manoeuvre_miss_distance_m"] >= constraints.min_miss_distance),
    }


if __name__ == "__main__":
    res = run_scenario_s4()
    print("S4 Result:", res)
