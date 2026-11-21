"""
D2/manoeuvres/avoidance_pipeline.py
===================================
Autonomous Collision-Avoidance Planning Pipeline for Deliverable 2 (D2).

Coordinates the end-to-end collision avoidance workflow:
1. Nominal Conjunction Assessment:
   - Propagates nominal two-body trajectories of protected satellite and secondary debris.
   - Calculates nominal numerical TCA, miss distance, and relative velocity.
   - Propagates covariance to nominal TCA and evaluates nominal collision probability Pc
     (when covariance matrices are available).
2. Avoidance Requirement Screening:
   - Checks whether collision risk exceeds mission safety criteria:
     miss distance < min_miss_distance OR Pc > max_target_pc.
   - If safe, returns status "NO_MANOEUVRE_REQUIRED" without fuel expenditure.
3. Candidate Manoeuvre Generation:
   - Generates candidate impulsive manoeuvres in the RTN local orbital frame across
     multiple burn epochs, delta-v magnitudes, and directional axes.
4. Manoeuvre Optimization & Verification:
   - Re-propagates the modified orbit post-manoeuvre.
   - Recalculates new TCA, post-manoeuvre miss distance, and new relative velocity.
   - Propagates covariance along the modified trajectory to the new TCA epoch.
   - Recalculates post-manoeuvre collision probability Pc (never reusing nominal Pc).
   - Verifies all constraints (delta-v limit, lead time, trajectory deviation, safety thresholds).
   - Selects the optimal manoeuvre minimizing delta-v and trajectory deviation.
5. Before-and-After Encounter Reporting:
   - Synthesizes comprehensive comparative metrics (Delta miss distance, Delta TCA, Delta Pc).
   - Explicitly reports when no acceptable manoeuvre can be found without claiming avoidance.

Conventions & Units:
- Reference Frame : Earth-Centred Inertial (ECI) for dynamics, RTN for manoeuvre specification
- Distances       : Metres (m)
- Velocities      : Metres per second (m/s)
- Time            : Seconds (s)
- Precision       : Float64
"""

from typing import Dict, Any, Optional, Sequence, List
import numpy as np

from D2.dynamics.two_body import MU_EARTH
from D2.conjunction.tca import calculate_numerical_tca
from D2.conjunction.screening import DEFAULT_SCREENING_THRESHOLD_M
from D2.uncertainty.covariance import (
    validate_covariance,
    propagate_covariance_to_tca,
)
from D2.uncertainty.collision_probability import (
    calculate_collision_probability,
    calculate_simplified_risk_proxy,
)
from D2.manoeuvres.manoeuvre_model import (
    ImpulsiveManoeuvre,
    ManoeuvreConstraints,
)
from D2.manoeuvres.candidate_generator import (
    generate_candidate_manoeuvres,
    DEFAULT_LEAD_TIMES,
    DEFAULT_DELTA_V_MAGNITUDES,
    DEFAULT_DIRECTIONS,
)
from D2.manoeuvres.manoeuvre_optimizer import evaluate_and_rank_candidates


def plan_collision_avoidance(
    initial_state_sat: np.ndarray,
    initial_state_sec: np.ndarray,
    duration: float,
    dt: float = 1.0,
    initial_cov_sat: Optional[np.ndarray] = None,
    initial_cov_sec: Optional[np.ndarray] = None,
    hard_body_radius: float = 10.0,
    constraints: Optional[ManoeuvreConstraints] = None,
    candidate_lead_times: Optional[Sequence[float]] = None,
    candidate_delta_v_magnitudes: Optional[Sequence[float]] = None,
    candidate_directions: Optional[Sequence[str]] = None,
    candidate_burn_times: Optional[Sequence[float]] = None,
    candidate_manoeuvres: Optional[Sequence[ImpulsiveManoeuvre]] = None,
    screening_threshold: float = DEFAULT_SCREENING_THRESHOLD_M,
    mu: float = MU_EARTH,
    satellite_id: str = "PROTECTED_SAT",
    secondary_id: str = "SECONDARY_OBJ",
    epoch: str = "2026-01-01T00:00:00Z"
) -> Dict[str, Any]:
    """
    Execute autonomous end-to-end collision avoidance manoeuvre planning.

    Parameters
    ----------
    initial_state_sat : array-like
        Initial 6D state of protected satellite at t = 0 [m, m/s].
    initial_state_sec : array-like
        Initial 6D state of secondary object at t = 0 [m, m/s].
    duration : float
        Conjunction assessment window duration in seconds.
    dt : float, optional
        Integration time step in seconds (default 1.0 s).
    initial_cov_sat : array-like, optional
        Initial 6x6 state covariance of protected satellite at t = 0.
    initial_cov_sec : array-like, optional
        Initial 6x6 state covariance of secondary object at t = 0.
    hard_body_radius : float, optional
        Combined hard-body collision radius in metres (default 10.0 m).
    constraints : ManoeuvreConstraints, optional
        Operational and safety constraints (default: ManoeuvreConstraints()).
    candidate_lead_times : sequence of float, optional
        Lead times before TCA for candidate generation.
    candidate_delta_v_magnitudes : sequence of float, optional
        Delta-v magnitude options for candidates in m/s.
    candidate_directions : sequence of str, optional
        RTN directions for candidate generation.
    candidate_burn_times : sequence of float, optional
        Explicit burn times for candidate generation.
    candidate_manoeuvres : sequence of ImpulsiveManoeuvre, optional
        Explicitly supplied candidates (skips automatic generation).
    screening_threshold : float, optional
        Computational screening filter distance in metres (default 25,000 m).
    mu : float, optional
        Earth gravitational parameter.
    satellite_id : str, optional
        Identifier for the protected satellite.
    secondary_id : str, optional
        Identifier for the secondary object.
    epoch : str, optional
        Epoch timestamp string.

    Returns
    -------
    report : dict
        Structured avoidance assessment report containing:
        - 'status': "SUCCESS", "NO_MANOEUVRE_REQUIRED", or "NO_ACCEPTABLE_MANOEUVRE_FOUND".
        - 'avoidance_needed': bool indicating if risk exceeded safety threshold.
        - 'nominal_assessment': Dict of pre-manoeuvre encounter conditions.
        - 'selected_manoeuvre': Selected ImpulsiveManoeuvre or None.
        - 'post_manoeuvre_assessment': Dict of post-manoeuvre encounter conditions or None.
        - 'differential_metrics': Dict of changes in miss distance, TCA, and Pc.
        - 'optimizer_result': Full candidate evaluation and ranking result.
        - 'constraints': ManoeuvreConstraints instance used.
    """
    if constraints is None:
        constraints = ManoeuvreConstraints()

    s1_0 = np.asarray(initial_state_sat, dtype=np.float64)
    s2_0 = np.asarray(initial_state_sec, dtype=np.float64)

    # =========================================================================
    # Step 1: Nominal Conjunction Assessment
    # =========================================================================
    nom_tca_res = calculate_numerical_tca(
        initial_state1=s1_0,
        initial_state2=s2_0,
        duration=duration,
        dt=dt,
        object1_id=satellite_id,
        object2_id=secondary_id,
        epoch=epoch
    )

    tca_nom = float(nom_tca_res["tca"])
    miss_dist_nom = float(nom_tca_res["miss_distance"])
    rel_speed_nom = float(nom_tca_res["relative_speed"])
    r_rel_nom = np.asarray(nom_tca_res["relative_position"], dtype=np.float64)
    v_rel_nom = np.asarray(nom_tca_res["relative_velocity"], dtype=np.float64)

    # Uncertainty & Collision Probability at nominal TCA
    pc_nom = None
    pc_nom_status = "COVARIANCE_MISSING"
    cov_rel_nom = None

    has_covariance = (initial_cov_sat is not None and initial_cov_sec is not None)
    if has_covariance:
        p1_0 = validate_covariance(initial_cov_sat, name="Sat Covariance")
        p2_0 = validate_covariance(initial_cov_sec, name="Sec Covariance")
        sync_nom = propagate_covariance_to_tca(
            state1_0=s1_0,
            cov1_0=p1_0,
            state2_0=s2_0,
            cov2_0=p2_0,
            tca=tca_nom,
            dt=dt,
            mu=mu,
            epoch_str=epoch
        )
        cov_rel_nom = sync_nom["cov_rel_tca"]
        pc_nom_eval = calculate_collision_probability(
            r_rel_tca=r_rel_nom,
            v_rel_tca=v_rel_nom,
            cov_rel_tca=cov_rel_nom,
            hard_body_radius=hard_body_radius
        )
        pc_nom = pc_nom_eval["pc"]
        pc_nom_log10 = pc_nom_eval.get("log10_pc")
        pc_nom_status = pc_nom_eval["status"]
    else:
        # Proxy risk description
        _ = calculate_simplified_risk_proxy(
            miss_distance=miss_dist_nom,
            hard_body_radius=hard_body_radius,
            relative_speed=rel_speed_nom
        )
        pc_nom_log10 = None

    nominal_assessment = {
        "satellite_id": satellite_id,
        "secondary_id": secondary_id,
        "epoch": epoch,
        "tca_sec": tca_nom,
        "miss_distance_m": miss_dist_nom,
        "relative_speed_mps": rel_speed_nom,
        "relative_position_m": r_rel_nom,
        "relative_velocity_mps": v_rel_nom,
        "collision_probability": pc_nom,
        "collision_log10_pc": pc_nom_log10,
        "pc_status": pc_nom_status,
        "covariance_present": has_covariance,
        "within_screening_threshold": (miss_dist_nom <= screening_threshold),
    }

    # =========================================================================
    # Step 2: Avoidance Requirement Screening
    # =========================================================================
    # Check if encounter violates safety thresholds:
    # 1. Miss distance is less than minimum required safety threshold.
    # 2. Or, if covariance is present, Pc exceeds maximum target threshold.
    risk_violates_miss_distance = (miss_dist_nom < constraints.min_miss_distance)
    risk_violates_pc = (has_covariance and pc_nom is not None and pc_nom > constraints.max_target_pc)
    avoidance_needed = risk_violates_miss_distance or risk_violates_pc

    if not avoidance_needed:
        # Encounter is already safe under nominal conditions
        return {
            "status": "NO_MANOEUVRE_REQUIRED",
            "avoidance_needed": False,
            "reason": (
                f"Nominal miss distance ({miss_dist_nom:.1f} m) meets or exceeds requirement "
                f"({constraints.min_miss_distance:.1f} m)"
                + (f" and nominal Pc ({pc_nom:.2e}) is within limit ({constraints.max_target_pc:.2e})."
                   if has_covariance and pc_nom is not None else ".")
            ),
            "nominal_assessment": nominal_assessment,
            "selected_manoeuvre": None,
            "post_manoeuvre_assessment": None,
            "differential_metrics": {
                "delta_miss_distance_m": 0.0,
                "delta_tca_sec": 0.0,
                "delta_pc": 0.0 if pc_nom is not None else None,
                "delta_v_expended_mps": 0.0,
                "max_trajectory_deviation_m": 0.0,
            },
            "optimizer_result": None,
            "constraints": constraints,
        }

    # =========================================================================
    # Step 3: Candidate Generation
    # =========================================================================
    if candidate_manoeuvres is not None:
        candidates = list(candidate_manoeuvres)
    else:
        # Ensure lead times do not violate nominal TCA
        candidates = generate_candidate_manoeuvres(
            tca_nominal=tca_nom,
            lead_times=candidate_lead_times,
            delta_v_magnitudes=candidate_delta_v_magnitudes,
            directions=candidate_directions,
            burn_times=candidate_burn_times,
            min_lead_time=constraints.min_lead_time
        )

    # =========================================================================
    # Step 4: Manoeuvre Optimization & Verification
    # =========================================================================
    opt_result = evaluate_and_rank_candidates(
        initial_state_sat=s1_0,
        initial_state_sec=s2_0,
        candidates=candidates,
        duration=duration,
        constraints=constraints,
        dt=dt,
        initial_cov_sat=initial_cov_sat,
        initial_cov_sec=initial_cov_sec,
        hard_body_radius=hard_body_radius,
        nominal_tca=tca_nom,
        mu=mu
    )

    # =========================================================================
    # Step 5: Before-and-After Encounter Reporting & Differentials
    # =========================================================================
    selected_man = opt_result["selected_manoeuvre"]
    selected_eval = opt_result["selected_evaluation"]

    if opt_result["status"] == "SUCCESS" and selected_man is not None and selected_eval is not None:
        status = "SUCCESS"
        tca_post = selected_eval["post_manoeuvre_tca_sec"]
        miss_dist_post = selected_eval["post_manoeuvre_miss_distance_m"]
        rel_speed_post = selected_eval["post_manoeuvre_relative_speed_mps"]
        pc_post = selected_eval["post_manoeuvre_pc"]

        delta_miss = miss_dist_post - miss_dist_nom
        delta_tca = tca_post - tca_nom
        delta_pc = (pc_post - pc_nom) if (pc_post is not None and pc_nom is not None) else None

        post_assessment = {
            "satellite_id": satellite_id,
            "secondary_id": secondary_id,
            "epoch": epoch,
            "manoeuvre_id": selected_man.manoeuvre_id,
            "burn_time_sec": selected_eval["burn_time_sec"],
            "lead_time_before_nom_tca_sec": tca_nom - selected_eval["burn_time_sec"],
            "delta_v_magnitude_mps": selected_man.delta_v_magnitude,
            "direction_label": selected_man.direction_label,
            "delta_v_rtn": selected_man.delta_v_rtn,
            "delta_v_eci": selected_eval["delta_v_eci"],
            "post_manoeuvre_tca_sec": tca_post,
            "post_manoeuvre_miss_distance_m": miss_dist_post,
            "post_manoeuvre_relative_speed_mps": rel_speed_post,
            "post_manoeuvre_relative_position_m": selected_eval["post_manoeuvre_relative_position_m"],
            "post_manoeuvre_relative_velocity_mps": selected_eval["post_manoeuvre_relative_velocity_mps"],
            "post_manoeuvre_pc": pc_post,
            "post_manoeuvre_log10_pc": selected_eval.get("post_manoeuvre_log10_pc"),
            "pc_status": selected_eval["pc_status"],
            "max_trajectory_deviation_m": selected_eval["max_trajectory_deviation_m"],
            "tca_trajectory_deviation_m": selected_eval["tca_trajectory_deviation_m"],
            "final_trajectory_deviation_m": selected_eval["final_trajectory_deviation_m"],
        }

        diff_metrics = {
            "delta_miss_distance_m": delta_miss,
            "delta_tca_sec": delta_tca,
            "delta_pc": delta_pc,
            "delta_v_expended_mps": selected_man.delta_v_magnitude,
            "max_trajectory_deviation_m": selected_eval["max_trajectory_deviation_m"],
        }
    else:
        status = "NO_ACCEPTABLE_MANOEUVRE_FOUND"
        post_assessment = None
        diff_metrics = {
            "delta_miss_distance_m": 0.0,
            "delta_tca_sec": 0.0,
            "delta_pc": None,
            "delta_v_expended_mps": 0.0,
            "max_trajectory_deviation_m": 0.0,
        }

    return {
        "status": status,
        "avoidance_needed": True,
        "nominal_assessment": nominal_assessment,
        "selected_manoeuvre": selected_man,
        "post_manoeuvre_assessment": post_assessment,
        "differential_metrics": diff_metrics,
        "optimizer_result": opt_result,
        "constraints": constraints,
    }


def format_avoidance_report(result: Dict[str, Any]) -> str:
    """
    Generate a formatted human-readable collision-avoidance assessment report.

    Parameters
    ----------
    result : dict
        Output from plan_collision_avoidance().

    Returns
    -------
    report_str : str
        Formatted markdown report.
    """
    lines = []
    lines.append("=" * 72)
    lines.append("        AUTONOMOUS COLLISION-AVOIDANCE ASSESSMENT REPORT (D2)")
    lines.append("=" * 72)

    status = result["status"]
    lines.append(f"Pipeline Status  : {status}")
    lines.append(f"Avoidance Needed : {result['avoidance_needed']}")

    nom = result["nominal_assessment"]
    lines.append("-" * 72)
    lines.append("1. NOMINAL ENCOUNTER (BEFORE MANOEUVRE)")
    lines.append("-" * 72)
    lines.append(f"  Nominal TCA            : {nom['tca_sec']:.2f} s from epoch")
    lines.append(f"  Nominal Miss Distance  : {nom['miss_distance_m']:.2f} m ({nom['miss_distance_m']/1000.0:.3f} km)")
    lines.append(f"  Relative Speed         : {nom['relative_speed_mps']:.3f} m/s")
    if nom["collision_probability"] is not None:
        log10_str = f" (log10 Pc: {nom['collision_log10_pc']:.2f})" if nom.get("collision_log10_pc") is not None else ""
        lines.append(f"  Collision Prob (Pc)    : {nom['collision_probability']:.3e}{log10_str} [{nom['pc_status']}]")
    else:
        lines.append(f"  Collision Prob (Pc)    : N/A [{nom['pc_status']}]")

    if status == "NO_MANOEUVRE_REQUIRED":
        lines.append("-" * 72)
        lines.append(f"DECISION: {result['reason']}")
        lines.append("=" * 72)
        return "\n".join(lines)

    if status == "NO_ACCEPTABLE_MANOEUVRE_FOUND":
        lines.append("-" * 72)
        lines.append("2. MANOEUVRE SELECTION: FAILED")
        lines.append("-" * 72)
        lines.append("  No candidate manoeuvre satisfied all mission constraints and safety targets.")
        lines.append("  Avoidance cannot be guaranteed with the current candidate set and constraints.")
        opt = result.get("optimizer_result")
        if opt:
            lines.append(f"  Candidates Evaluated   : {opt['total_candidates']}")
            lines.append(f"  Rejected Candidates    : {opt['num_rejected']}")
            lines.append("  Rejection Summary (first 5):")
            for rej in opt["rejected_candidates"][:5]:
                cand = rej["candidate"]
                reasons = "; ".join(rej["rejection_reasons"])
                lines.append(f"    - {cand.manoeuvre_id}: {reasons}")
        lines.append("=" * 72)
        return "\n".join(lines)

    # SUCCESS
    post = result["post_manoeuvre_assessment"]
    diff = result["differential_metrics"]
    man = result["selected_manoeuvre"]

    lines.append("-" * 72)
    lines.append("2. SELECTED AVOIDANCE MANOEUVRE")
    lines.append("-" * 72)
    lines.append(f"  Manoeuvre ID           : {man.manoeuvre_id}")
    lines.append(f"  Burn Time (t_burn)     : {post['burn_time_sec']:.1f} s (Lead Time: {post['lead_time_before_nom_tca_sec']:.1f} s)")
    lines.append(f"  Delta-v Magnitude      : {man.delta_v_magnitude:.3f} m/s")
    lines.append(f"  Direction (RTN)        : {man.direction_label}")
    lines.append(f"  Delta-v RTN Components : R={man.radial_component:+.3f}, T={man.along_track_component:+.3f}, N={man.cross_track_component:+.3f} m/s")
    lines.append(f"  Delta-v ECI Vector     : [{post['delta_v_eci'][0]:+.3f}, {post['delta_v_eci'][1]:+.3f}, {post['delta_v_eci'][2]:+.3f}] m/s")

    lines.append("-" * 72)
    lines.append("3. POST-MANOEUVRE ENCOUNTER (AFTER MANOEUVRE)")
    lines.append("-" * 72)
    lines.append(f"  New TCA                : {post['post_manoeuvre_tca_sec']:.2f} s")
    lines.append(f"  New Miss Distance      : {post['post_manoeuvre_miss_distance_m']:.2f} m ({post['post_manoeuvre_miss_distance_m']/1000.0:.3f} km)")
    lines.append(f"  New Relative Speed     : {post['post_manoeuvre_relative_speed_mps']:.3f} m/s")
    if post["post_manoeuvre_pc"] is not None:
        log10_str = f" (log10 Pc: {post['post_manoeuvre_log10_pc']:.2f})" if post.get("post_manoeuvre_log10_pc") is not None else ""
        lines.append(f"  New Collision Prob (Pc): {post['post_manoeuvre_pc']:.3e}{log10_str} [{post['pc_status']}]")
    else:
        lines.append(f"  New Collision Prob (Pc): N/A [{post['pc_status']}]")

    lines.append("-" * 72)
    lines.append("4. COMPARATIVE & SAFETY METRICS")
    lines.append("-" * 72)
    lines.append(f"  Miss Distance Increase : +{diff['delta_miss_distance_m']:.2f} m (+{diff['delta_miss_distance_m']/1000.0:.3f} km)")
    lines.append(f"  Shift in TCA           : {diff['delta_tca_sec']:+.2f} s")
    if diff["delta_pc"] is not None:
        lines.append(f"  Change in Pc           : {diff['delta_pc']:+.3e}")
    lines.append(f"  Max Trajectory Dev     : {diff['max_trajectory_deviation_m']:.2f} m")
    lines.append(f"  Total Delta-v Expended : {diff['delta_v_expended_mps']:.3f} m/s")
    lines.append("=" * 72)

    return "\n".join(lines)

