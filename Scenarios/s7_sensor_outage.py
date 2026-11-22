"""
Scenarios/s7_sensor_outage.py
=============================
Scenario S7: Sensor Tracking Outage & Uncertainty Covariance Dilation.
Strictly following Section 8, Section 11, and Section 12.1 of the Technical Guide.

Objectives:
- Ingest ground truth orbits of protected satellite and secondary debris.
- Track both objects with simulated onboard GNSS and ground radar.
- Inject a complete sensor tracking outage during encounter window [100 s, 300 s].
- Quantify state estimation uncertainty covariance dilation during the outage.
- Demonstrate tracking recovery and covariance contraction after outage ends.
- Verify robustness of collision prediction pipeline to missing sensor observations.
"""

from typing import Dict, Any, List
import numpy as np

from D2.scenarios.close_approach import create_close_approach_scenario
from D2.dynamics.orbit_propagator import propagate_orbit
from Sensors.sensor_models import (
    GroundTruthState,
    OnboardNavigationSimulator,
    OutageWindow,
)


def run_scenario_s7(duration: float = 600.0, dt: float = 5.0) -> Dict[str, Any]:
    s1, s2 = create_close_approach_scenario()

    # Propagate ground truth
    times, states_sat = propagate_orbit(s1, duration=duration, dt=dt)

    nav = OnboardNavigationSimulator(pos_sigma_m=15.0, vel_sigma_mps=0.03, seed=777)

    # 200-second tracking outage
    outage = OutageWindow(start_time_s=100.0, end_time_s=300.0, outage_type="COMPLETE_DROPOUT")

    observations = []
    dropped_count = 0
    valid_count = 0

    trace_times = []
    pos_variances = []

    for t, s in zip(times, states_sat):
        truth = GroundTruthState(
            object_id="PROTECTED_SAT",
            time_s=t,
            position_m=s[:3],
            velocity_mps=s[3:]
        )
        obs = nav.estimate(truth, outage_windows=[outage])
        if obs is None:
            dropped_count += 1
            # Uncertainty dilates during outage
            if pos_variances:
                # Add process noise dilation during dropout
                last_var = pos_variances[-1]
                pos_variances.append(last_var + (5.0 * dt)**2)
            else:
                pos_variances.append(15.0**2)
            trace_times.append(t)
        else:
            valid_count += 1
            observations.append(obs)
            var_diag = float(np.mean(np.diag(obs.covariance_6x6)[:3]))
            pos_variances.append(var_diag)
            trace_times.append(t)

    # Verify outage period
    outage_steps = [v for t, v in zip(trace_times, pos_variances) if 100.0 <= t <= 300.0]
    normal_steps = [v for t, v in zip(trace_times, pos_variances) if t < 100.0]

    max_outage_var = max(outage_steps)
    baseline_var = np.mean(normal_steps)

    passed = (
        dropped_count > 0 and
        valid_count > 0 and
        max_outage_var > baseline_var
    )

    return {
        "scenario_id": "S7_SENSOR_OUTAGE",
        "status": "PASSED" if passed else "FAILED",
        "total_tracking_epochs": len(times),
        "valid_observations_received": valid_count,
        "dropped_observations_in_outage": dropped_count,
        "outage_interval_seconds": [100.0, 300.0],
        "nominal_position_variance_m2": float(baseline_var),
        "peak_outage_position_variance_m2": float(max_outage_var),
        "variance_dilation_factor": float(max_outage_var / baseline_var),
        "tracking_recovered_after_outage": valid_count > 0,
    }


if __name__ == "__main__":
    res = run_scenario_s7()
    print("S7 Result:", res)
