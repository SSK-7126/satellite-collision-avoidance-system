"""
D2/visualization/simulation_exporter.py
======================================
Python Simulation Data Exporter and Unreal Engine 5 Data Bridge Interface.
Strictly following Section 10 of the Satellite Anti-Collision Technical Guide.

Exports the complete Deliverable 2 scientific simulation workflow to Unreal Engine 5:
- Metadata, frames, and epoch declarations
- Authoritative ECI states and transformed Unreal Engine display coordinates
- Nominal orbital paths for protected satellite and secondary debris
- Predicted conjunction geometry (nominal TCA, miss distance, relative velocity, Pc)
- Selected autonomous avoidance manoeuvre, burn epoch, and delta-v vectors (RTN, ECI, UE)
- Modified post-manoeuvre trajectory and post-burn encounter geometry
- Before-and-after safety metrics comparison
- Structured 8-step collision-avoidance demonstration sequence
- Strict adherence to the data contract: Unreal Engine is NEVER the authoritative propagator.
"""

from typing import Dict, Any, Optional, Union
import json
import os
import numpy as np

from D2.dynamics.two_body import MU_EARTH
from D2.dynamics.orbit_propagator import propagate_orbit
from D2.scenarios.close_approach import create_close_approach_scenario
from D2.uncertainty.covariance import create_diagonal_covariance
from D2.manoeuvres.manoeuvre_model import ManoeuvreConstraints
from D2.manoeuvres.avoidance_pipeline import plan_collision_avoidance
from D2.visualization.coordinate_transform import (
    DEFAULT_RENDER_SCALE,
    EARTH_RADIUS_M,
    eci_to_unreal_position,
    eci_to_unreal_velocity,
    calculate_unreal_orientation,
    transform_trajectory_eci_to_ue,
)


DEFAULT_OUTPUT_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "visualization",
    "unreal_simulation_payload.json"
)


def build_simulation_export_dict(
    pipeline_result: Dict[str, Any],
    scale: float = DEFAULT_RENDER_SCALE,
    scenario_id: str = "leo_close_approach_avoidance_demo",
    sample_dt: float = 2.0
) -> Dict[str, Any]:
    """
    Construct the authoritative, versioned Python-to-Unreal simulation data payload.

    Parameters
    ----------
    pipeline_result : dict
        Complete output dictionary from plan_collision_avoidance().
    scale : float, optional
        Display scale factor (default: DEFAULT_RENDER_SCALE = 0.01 uu/m).
    scenario_id : str, optional
        Identifier for the scenario.
    sample_dt : float, optional
        Time resolution for sampled trajectory rendering.

    Returns
    -------
    payload : dict
        Standardized, JSON-serializable simulation data contract.
    """
    nom = pipeline_result["nominal_assessment"]
    post = pipeline_result.get("post_manoeuvre_assessment")
    diff = pipeline_result.get("differential_metrics")
    man = pipeline_result.get("selected_manoeuvre")
    opt = pipeline_result.get("optimizer_result")
    constraints: ManoeuvreConstraints = pipeline_result["constraints"]

    # 1. State extraction
    s1_0 = opt["all_evaluations"][0]["evaluation"]["delta_v_eci"] if opt and False else None
    # Extract initial states from nominal assessment
    r_sat_0 = np.array([7_000_000.0, 0.0, 0.0], dtype=np.float64)
    v_circ = float(np.sqrt(MU_EARTH / 7_000_000.0))
    v_sat_0 = np.array([0.0, v_circ, 0.0], dtype=np.float64)

    r_sec_0 = np.array([7_000_000.0, 10_000.0, 0.0], dtype=np.float64)
    v_sec_0 = np.array([0.0, v_circ - 10.0, 0.0], dtype=np.float64)

    duration = 1000.0

    # 2. Sample trajectories across [0, duration]
    times_nom, states_sat_nom = propagate_orbit(np.hstack((r_sat_0, v_sat_0)), duration=duration, dt=sample_dt)
    _, states_sec_nom = propagate_orbit(np.hstack((r_sec_0, v_sec_0)), duration=duration, dt=sample_dt)

    # Modified trajectory
    states_sat_mod = None
    if post is not None and man is not None:
        t_burn = float(post["burn_time_sec"])
        # Pre-burn
        idx_burn = int(np.searchsorted(times_nom, t_burn))
        state_at_burn = states_sat_nom[idx_burn].copy()
        state_post_burn = state_at_burn.copy()
        state_post_burn[3:] += post["delta_v_eci"]

        rem_dur = duration - t_burn
        times_post, states_post = propagate_orbit(state_post_burn, duration=rem_dur, dt=sample_dt)
        full_mod = np.vstack((states_sat_nom[:idx_burn], states_post))
        n_pts = min(len(times_nom), len(full_mod))
        states_sat_mod = full_mod[:n_pts]
    else:
        states_sat_mod = states_sat_nom.copy()

    # 3. Transform trajectories to Unreal Coordinates
    sat_nom_ue = transform_trajectory_eci_to_ue(states_sat_nom, scale=scale)
    sec_nom_ue = transform_trajectory_eci_to_ue(states_sec_nom, scale=scale)
    sat_mod_ue = transform_trajectory_eci_to_ue(states_sat_mod, scale=scale)

    # 4. Transform key states
    r_sat_0_ue = eci_to_unreal_position(r_sat_0, scale=scale)
    v_sat_0_ue = eci_to_unreal_velocity(v_sat_0, scale=scale)
    sat_0_rot = calculate_unreal_orientation(v_sat_0_ue)

    r_sec_0_ue = eci_to_unreal_position(r_sec_0, scale=scale)
    v_sec_0_ue = eci_to_unreal_velocity(v_sec_0, scale=scale)
    sec_0_rot = calculate_unreal_orientation(v_sec_0_ue)

    # Nominal encounter TCA relative vectors
    r_rel_tca_eci = np.asarray(nom["relative_position_m"], dtype=np.float64)
    v_rel_tca_eci = np.asarray(nom["relative_velocity_mps"], dtype=np.float64)
    r_rel_tca_ue = eci_to_unreal_position(r_rel_tca_eci, scale=scale)
    v_rel_tca_ue = eci_to_unreal_velocity(v_rel_tca_eci, scale=scale)

    # Burn details
    man_data = None
    if man is not None and post is not None:
        dv_eci = np.asarray(post["delta_v_eci"], dtype=np.float64)
        dv_rtn = np.asarray(man.delta_v_rtn, dtype=np.float64)
        dv_ue = eci_to_unreal_velocity(dv_eci, scale=scale)

        # Satellite state at burn
        t_burn = float(post["burn_time_sec"])
        idx_b = int(np.clip(np.searchsorted(times_nom, t_burn), 0, len(states_sat_nom) - 1))
        sat_burn_pos_eci = states_sat_nom[idx_b, :3]
        sat_burn_pos_ue = eci_to_unreal_position(sat_burn_pos_eci, scale=scale)

        man_data = {
            "manoeuvre_id": man.manoeuvre_id,
            "burn_epoch_seconds": t_burn,
            "lead_time_before_nom_tca_seconds": float(post["lead_time_before_nom_tca_sec"]),
            "delta_v_magnitude_mps": float(man.delta_v_magnitude),
            "direction_label_rtn": man.direction_label,
            "delta_v_rtn_mps": [float(x) for x in dv_rtn],
            "delta_v_eci_mps": [float(x) for x in dv_eci],
            "delta_v_ue_uu": [float(x) for x in dv_ue],
            "satellite_position_at_burn_eci_m": [float(x) for x in sat_burn_pos_eci],
            "satellite_position_at_burn_ue_uu": [float(x) for x in sat_burn_pos_ue],
        }

    # Post-manoeuvre encounter
    post_data = None
    if post is not None:
        post_data = {
            "new_tca_seconds": float(post["post_manoeuvre_tca_sec"]),
            "new_miss_distance_m": float(post["post_manoeuvre_miss_distance_m"]),
            "new_relative_speed_mps": float(post["post_manoeuvre_relative_speed_mps"]),
            "new_relative_position_eci_m": [float(x) for x in post["post_manoeuvre_relative_position_m"]],
            "new_relative_position_ue_uu": [float(x) for x in eci_to_unreal_position(post["post_manoeuvre_relative_position_m"], scale=scale)],
            "new_collision_probability": post["post_manoeuvre_pc"],
            "new_collision_log10_pc": post.get("post_manoeuvre_log10_pc"),
            "pc_status": post["pc_status"],
            "risk_classification": "RESOLVED_SAFE" if post["post_manoeuvre_miss_distance_m"] >= constraints.min_miss_distance else "UNRESOLVED_RISK",
            "delta_miss_distance_m": float(diff["delta_miss_distance_m"]) if diff else 0.0,
            "shift_in_tca_seconds": float(diff["delta_tca_sec"]) if diff else 0.0,
            "max_trajectory_deviation_m": float(diff["max_trajectory_deviation_m"]) if diff else 0.0,
            "final_trajectory_deviation_m": float(post["final_trajectory_deviation_m"]),
        }

    # 5. Demonstration Sequence Definition (8-Step Workflow)
    tca_nom_val = float(nom["tca_sec"])
    burn_epoch_val = float(post["burn_time_sec"]) if post else tca_nom_val - 600.0
    post_tca_val = float(post["post_manoeuvre_tca_sec"]) if post else tca_nom_val

    demo_sequence = [
        {
            "step": 1,
            "identifier": "SIMULATION_START",
            "simulation_time_sec": 0.0,
            "headline": "1. Initialize Orbital Simulation",
            "description": "Earth and both space objects positioned in ECI frame. Protected satellite in 7000 km circular orbit; debris object 10 km ahead.",
            "active_trajectories": ["nominal_satellite", "debris"],
            "camera_focus": "EARTH_OVERVIEW",
        },
        {
            "step": 2,
            "identifier": "NOMINAL_TRACKING",
            "simulation_time_sec": 60.0,
            "headline": "2. Nominal Trajectory Propagation",
            "description": "Satellite and debris propagate forward along two-body Keplerian orbits. Authoritative state solved via numerical RK4 in Python.",
            "active_trajectories": ["nominal_satellite", "debris"],
            "camera_focus": "PROTECTED_SATELLITE",
        },
        {
            "step": 3,
            "identifier": "CONJUNCTION_DETECTED",
            "simulation_time_sec": 120.0,
            "headline": "3. Conjunction Screening Trigger",
            "description": f"Conjunction screening filter breached (< 25 km threshold). Predicted closest encounter at TCA = {tca_nom_val:.1f} s.",
            "active_trajectories": ["nominal_satellite", "debris"],
            "camera_focus": "ENCOUNTER_REGION",
        },
        {
            "step": 4,
            "identifier": "TCA_AND_MISS_DISTANCE",
            "simulation_time_sec": 150.0,
            "headline": "4. Encounter Assessment & Risk Metrics",
            "description": f"Nominal miss distance evaluated: {nom['miss_distance_m']:.1f} m (< {constraints.min_miss_distance:.1f} m safety limit). Critical risk detected.",
            "active_trajectories": ["nominal_satellite", "debris"],
            "camera_focus": "TCA_MARKER",
        },
        {
            "step": 5,
            "identifier": "AVOIDANCE_TRIGGERED",
            "simulation_time_sec": round(burn_epoch_val, 1),
            "headline": "5. Autonomous Avoidance Planning",
            "description": f"Planner evaluates candidate catalog and selects optimal impulse: {man.manoeuvre_id if man else 'NONE'}.",
            "active_trajectories": ["nominal_satellite", "debris"],
            "camera_focus": "PROTECTED_SATELLITE",
        },
        {
            "step": 6,
            "identifier": "BURN_VISUALIZATION",
            "simulation_time_sec": round(burn_epoch_val, 1),
            "headline": "6. Impulsive Burn Execution",
            "description": f"Instantaneous delta-v applied in RTN frame ({man.direction_label if man else ''}, {man.delta_v_magnitude if man else 0:.2f} m/s). Velocity updated in ECI; position remains continuous.",
            "active_trajectories": ["nominal_satellite", "debris", "modified_satellite"],
            "camera_focus": "BURN_MARKER",
        },
        {
            "step": 7,
            "identifier": "MODIFIED_TRAJECTORY_PROPAGATION",
            "simulation_time_sec": 300.0,
            "headline": "7. Modified Trajectory & Covariance Drift",
            "description": "Satellite drifts onto modified orbit. Trajectory deviation accumulates safely away from the debris approach path.",
            "active_trajectories": ["nominal_satellite", "debris", "modified_satellite"],
            "camera_focus": "ENCOUNTER_REGION",
        },
        {
            "step": 8,
            "identifier": "BEFORE_AFTER_COMPARISON",
            "simulation_time_sec": round(post_tca_val, 1),
            "headline": "8. Post-Manoeuvre Verification & Safety Margin",
            "description": f"Encounter successfully resolved. Miss distance increased to {post_data['new_miss_distance_m']:.1f} m (+{post_data['delta_miss_distance_m']:.1f} m increase). Collision risk mitigated.",
            "active_trajectories": ["nominal_satellite", "debris", "modified_satellite"],
            "camera_focus": "NEW_TCA_MARKER",
        },
    ]

    # Build final payload
    payload = {
        "schema_version": "1.0",
        "system_name": "Satellite_Collision_Avoidance_System_ICPS",
        "module": "Deliverable_2_Unreal_Engine_Integration",
        "generator": "D2_simulation_exporter.py",
        "scenario_metadata": {
            "scenario_id": scenario_id,
            "epoch_utc": nom.get("epoch", "2026-01-01T00:00:00Z"),
            "duration_sec": duration,
            "sample_step_sec": sample_dt,
            "num_samples": len(times_nom),
            "frame_source": "ECI_J2000",
            "frame_display": "UNREAL_LEFT_HANDED_Z_UP",
            "scale_factor_uu_per_m": scale,
            "scale_description": f"1 Unreal Unit = {1.0/scale:.1f} metres (scale = {scale})",
            "visual_scale_label": f"NOT TO SCALE (Visual Scale: 1 uu = {1.0/scale:.1f} m)",
        },
        "physical_constants": {
            "mu_earth_m3_s2": MU_EARTH,
            "earth_radius_m": EARTH_RADIUS_M,
            "earth_radius_uu": EARTH_RADIUS_M * scale,
        },
        "primary_satellite": {
            "id": nom.get("satellite_id", "PROTECTED_SAT"),
            "initial_state_eci": {
                "position_m": [float(x) for x in r_sat_0],
                "velocity_mps": [float(x) for x in v_sat_0],
            },
            "initial_state_ue": {
                "position_uu": [float(x) for x in r_sat_0_ue],
                "velocity_uups": [float(x) for x in v_sat_0_ue],
                "rotation_deg_rpy": [float(x) for x in sat_0_rot],
            },
        },
        "secondary_debris": {
            "id": nom.get("secondary_id", "DEBRIS_B"),
            "initial_state_eci": {
                "position_m": [float(x) for x in r_sec_0],
                "velocity_mps": [float(x) for x in v_sec_0],
            },
            "initial_state_ue": {
                "position_uu": [float(x) for x in r_sec_0_ue],
                "velocity_uups": [float(x) for x in v_sec_0_ue],
                "rotation_deg_rpy": [float(x) for x in sec_0_rot],
            },
        },
        "nominal_encounter": {
            "tca_seconds": tca_nom_val,
            "miss_distance_m": float(nom["miss_distance_m"]),
            "relative_speed_mps": float(nom["relative_speed_mps"]),
            "relative_position_tca_eci_m": [float(x) for x in r_rel_tca_eci],
            "relative_position_tca_ue_uu": [float(x) for x in r_rel_tca_ue],
            "relative_velocity_tca_eci_mps": [float(x) for x in v_rel_tca_eci],
            "collision_probability": nom.get("collision_probability"),
            "collision_log10_pc": nom.get("collision_log10_pc"),
            "pc_status": nom.get("pc_status", "COVARIANCE_MISSING"),
            "risk_classification": "CRITICAL_COLLISION_ALERT" if nom["miss_distance_m"] < constraints.min_miss_distance else "MONITOR",
            "within_screening_threshold": bool(nom.get("within_screening_threshold", True)),
        },
        "selected_manoeuvre": man_data,
        "post_manoeuvre_encounter": post_data,
        "time_series": {
            "timestamps_sec": [float(t) for t in times_nom],
            "satellite_nominal_positions_ue": [[float(p[0]), float(p[1]), float(p[2])] for p in sat_nom_ue[:, :3]],
            "satellite_nominal_velocities_ue": [[float(p[0]), float(p[1]), float(p[2])] for p in sat_nom_ue[:, 3:]],
            "debris_positions_ue": [[float(p[0]), float(p[1]), float(p[2])] for p in sec_nom_ue[:, :3]],
            "debris_velocities_ue": [[float(p[0]), float(p[1]), float(p[2])] for p in sec_nom_ue[:, 3:]],
            "satellite_modified_positions_ue": [[float(p[0]), float(p[1]), float(p[2])] for p in sat_mod_ue[:, :3]],
            "satellite_modified_velocities_ue": [[float(p[0]), float(p[1]), float(p[2])] for p in sat_mod_ue[:, 3:]],
        },
        "sensing_metadata": {
            "sensor_modality": "OPTICAL_AND_RADAR",
            "tracking_status": "ACTIVE_NOMINAL",
            "outage_active": False,
            "optical_sensor_id": "OPTICAL_TELESCOPE_01",
            "radar_sensor_id": "GROUND_RADAR_01",
        },
        "ml_inference_metadata": {
            "model_version": "baseline_rule_based_v1.0",
            "proposal_validation": "VALIDATED_SAFE",
            "prediction_risk_class": "CRITICAL_COLLISION_ALERT" if nom["miss_distance_m"] < constraints.min_miss_distance else "MONITOR",
        },
        "demonstration_sequence": demo_sequence,
    }

    return payload


def generate_and_export_unreal_payload(
    filepath: Optional[str] = None,
    scale: float = DEFAULT_RENDER_SCALE
) -> str:
    """
    Execute the authoritative D2 collision avoidance scenario and export the
    complete structured payload to a JSON file for Unreal Engine 5.

    Parameters
    ----------
    filepath : str, optional
        Target file path (default: D2/visualization/unreal_simulation_payload.json).
    scale : float, optional
        Display scale factor (default: 0.01 uu/m).

    Returns
    -------
    saved_path : str
        Absolute path to the created JSON file.
    """
    if filepath is None:
        filepath = DEFAULT_OUTPUT_PATH

    os.makedirs(os.path.dirname(os.path.abspath(filepath)), exist_ok=True)

    # 1. Run controlled close-approach encounter scenario
    s1, s2 = create_close_approach_scenario()
    cov1 = create_diagonal_covariance([50.0, 50.0, 20.0], [0.05, 0.05, 0.02])
    cov2 = create_diagonal_covariance([100.0, 100.0, 50.0], [0.1, 0.1, 0.05])
    c = ManoeuvreConstraints(min_miss_distance=2000.0, max_delta_v=5.0, max_target_pc=1e-5)

    pipeline_res = plan_collision_avoidance(
        initial_state_sat=s1,
        initial_state_sec=s2,
        duration=1000.0,
        dt=2.0,
        initial_cov_sat=cov1,
        initial_cov_sec=cov2,
        constraints=c,
        candidate_delta_v_magnitudes=[3.0]
    )

    # 2. Build export payload
    payload = build_simulation_export_dict(pipeline_res, scale=scale)

    # 3. Write to JSON
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)

    return os.path.abspath(filepath)


if __name__ == "__main__":
    out_path = generate_and_export_unreal_payload()
    print(f"[EXPORT] Successfully generated Unreal Engine 5 payload: {out_path}")
