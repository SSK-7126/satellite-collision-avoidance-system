"""
D2/manoeuvres/manoeuvre_optimizer.py
====================================
Collision-Avoidance Manoeuvre Evaluation, Filtering, and Optimization Module (D2).

Selects an optimal collision-avoidance manoeuvre from candidate options by evaluating
them against operational mission constraints, safety thresholds, and optimization objectives:

1. Constraint Filtering:
   - Delta-v magnitude constraint (|Delta_v| <= max_delta_v).
   - Operational lead-time constraint (t_burn <= tca_nominal - min_lead_time).
   - Maximum allowable trajectory deviation (|r_man(t) - r_nom(t)| <= max_trajectory_deviation).
   - Safety thresholds:
       * Post-manoeuvre miss distance >= min_miss_distance.
       * Post-manoeuvre collision probability Pc <= max_target_pc (when covariance is present).

2. Multi-Criteria Ranking (for Feasible Candidates):
   - Primary: Minimize Delta-v magnitude |Delta_v| (propellant conservation).
   - Secondary: Minimize orbital trajectory deviation (operational path preservation).
   - Tertiary: Maximize miss distance / minimize Pc (safety margin maximization).

3. Fallback & Safe Reporting:
   - If no candidate satisfies all constraints, returns status "NO_ACCEPTABLE_MANOEUVRE_FOUND"
     with selected_manoeuvre = None. Avoidance is never falsely claimed.
   - When covariance is missing, uses geometric miss distance without fabricating artificial Pc.

Conventions & Units:
- Reference Frame : Earth-Centred Inertial (ECI) for dynamics, RTN for manoeuvre specification
- Distances       : Metres (m)
- Velocities      : Metres per second (m/s)
- Time            : Seconds (s)
- Precision       : Float64
"""

from typing import List, Dict, Any, Optional, Sequence
import numpy as np

from D2.dynamics.two_body import MU_EARTH
from D2.dynamics.orbit_propagator import propagate_orbit
from D2.conjunction.tca import calculate_numerical_tca
from D2.manoeuvres.manoeuvre_model import (
    ImpulsiveManoeuvre,
    ManoeuvreConstraints,
)
from D2.manoeuvres.manoeuvre_evaluator import simulate_manoeuvre


def evaluate_and_rank_candidates(
    initial_state_sat: np.ndarray,
    initial_state_sec: np.ndarray,
    candidates: Sequence[ImpulsiveManoeuvre],
    duration: float,
    constraints: Optional[ManoeuvreConstraints] = None,
    dt: float = 1.0,
    initial_cov_sat: Optional[np.ndarray] = None,
    initial_cov_sec: Optional[np.ndarray] = None,
    hard_body_radius: float = 10.0,
    nominal_tca: Optional[float] = None,
    mu: float = MU_EARTH
) -> Dict[str, Any]:
    """
    Evaluate, filter against constraints, and rank all candidate avoidance manoeuvres.

    Parameters
    ----------
    initial_state_sat : array-like
        Initial 6D state of protected satellite at t = 0 [m, m/s].
    initial_state_sec : array-like
        Initial 6D state of secondary object at t = 0 [m, m/s].
    candidates : sequence of ImpulsiveManoeuvre
        Candidate manoeuvres to evaluate.
    duration : float
        Assessment interval duration in seconds.
    constraints : ManoeuvreConstraints, optional
        Operational and safety constraints (default: ManoeuvreConstraints()).
    dt : float, optional
        Numerical integration time step in seconds (default 1.0 s).
    initial_cov_sat : array-like, optional
        Initial 6x6 state covariance of protected satellite at t = 0.
    initial_cov_sec : array-like, optional
        Initial 6x6 state covariance of secondary object at t = 0.
    hard_body_radius : float, optional
        Combined hard-body collision radius in metres (default 10.0 m).
    nominal_tca : float, optional
        Nominal TCA in seconds (calculated numerically if not provided).
    mu : float, optional
        Earth gravitational parameter in m^3/s^2.

    Returns
    -------
    result : dict
        Structured evaluation and ranking result:
        - 'status': "SUCCESS" if at least one feasible manoeuvre found, else "NO_ACCEPTABLE_MANOEUVRE_FOUND".
        - 'selected_manoeuvre': ImpulsiveManoeuvre or None.
        - 'selected_evaluation': Evaluation record dict or None.
        - 'feasible_candidates': List of candidate dicts passing all constraints, sorted by rank.
        - 'rejected_candidates': List of candidate dicts failing one or more constraints.
        - 'all_evaluations': List of all candidate evaluation dicts.
        - 'nominal_tca_sec': Nominal TCA used for lead-time constraints.
        - 'total_candidates': Total number of candidates evaluated.
        - 'num_feasible': Number of feasible candidates.
        - 'num_rejected': Number of rejected candidates.
    """
    if constraints is None:
        constraints = ManoeuvreConstraints()

    s1_0 = np.asarray(initial_state_sat, dtype=np.float64)
    s2_0 = np.asarray(initial_state_sec, dtype=np.float64)

    # 1. Determine nominal TCA if not provided
    if nominal_tca is None:
        nom_tca_res = calculate_numerical_tca(s1_0, s2_0, duration=duration, dt=dt)
        ref_tca = float(nom_tca_res["tca"])
    else:
        ref_tca = float(nominal_tca)

    # Pre-propagate nominal trajectories once for efficient reuse across candidates
    times_sat_nom, states_sat_nom = propagate_orbit(s1_0, duration=duration, dt=dt)
    times_sec_nom, states_sec_nom = propagate_orbit(s2_0, duration=duration, dt=dt)
    nom_sat_traj = (times_sat_nom, states_sat_nom)
    nom_sec_traj = (times_sec_nom, states_sec_nom)

    evaluated_candidates: List[Dict[str, Any]] = []

    for cand in candidates:
        rejection_reasons: List[str] = []

        # ---------------------------------------------------------
        # Check Pre-Simulation Constraints
        # ---------------------------------------------------------
        # 1. Delta-v budget limit
        if cand.delta_v_magnitude > (constraints.max_delta_v + 1e-9):
            rejection_reasons.append(
                f"EXCEEDS_MAX_DELTA_V: {cand.delta_v_magnitude:.3f} m/s > {constraints.max_delta_v:.3f} m/s"
            )

        # 2. Advance lead time before nominal TCA
        required_max_burn_time = ref_tca - constraints.min_lead_time
        if cand.burn_time > (required_max_burn_time + 1e-9):
            rejection_reasons.append(
                f"INSUFFICIENT_LEAD_TIME: burn_time={cand.burn_time:.1f}s > max allowed {required_max_burn_time:.1f}s "
                f"(nominal TCA {ref_tca:.1f}s - min lead {constraints.min_lead_time:.1f}s)"
            )

        # Check simulation validity (burn time must be within duration)
        if cand.burn_time >= duration:
            rejection_reasons.append(
                f"BURN_TIME_OUT_OF_WINDOW: burn_time={cand.burn_time:.1f}s >= duration={duration:.1f}s"
            )

        # ---------------------------------------------------------
        # Simulate Manoeuvre (only if pre-simulation constraints pass)
        # ---------------------------------------------------------
        eval_record: Optional[Dict[str, Any]] = None
        if not rejection_reasons:
            eval_record = simulate_manoeuvre(
                initial_state_sat=s1_0,
                initial_state_sec=s2_0,
                manoeuvre=cand,
                duration=duration,
                dt=dt,
                initial_cov_sat=initial_cov_sat,
                initial_cov_sec=initial_cov_sec,
                hard_body_radius=hard_body_radius,
                mu=mu,
                nominal_sat_trajectory=nom_sat_traj,
                nominal_sec_trajectory=nom_sec_traj,
                skip_covariance_if_insufficient_miss=constraints.min_miss_distance
            )

            # ---------------------------------------------------------
            # Check Post-Simulation Constraints
            # ---------------------------------------------------------
            # 3. Maximum trajectory deviation constraint
            if constraints.max_trajectory_deviation is not None:
                max_dev = eval_record["max_trajectory_deviation_m"]
                if max_dev > (constraints.max_trajectory_deviation + 1e-6):
                    rejection_reasons.append(
                        f"EXCEEDS_MAX_TRAJECTORY_DEVIATION: {max_dev:.1f} m > {constraints.max_trajectory_deviation:.1f} m"
                    )

            # 4. Minimum miss distance safety threshold
            post_miss = eval_record["post_manoeuvre_miss_distance_m"]
            if post_miss < (constraints.min_miss_distance - 1e-6):
                rejection_reasons.append(
                    f"INSUFFICIENT_MISS_DISTANCE: {post_miss:.1f} m < required {constraints.min_miss_distance:.1f} m"
                )

            # 5. Maximum acceptable collision probability Pc
            post_pc = eval_record["post_manoeuvre_pc"]
            if post_pc is not None:
                if post_pc > (constraints.max_target_pc + 1e-12):
                    rejection_reasons.append(
                        f"EXCEEDS_TARGET_PC: {post_pc:.2e} > allowed {constraints.max_target_pc:.2e}"
                    )
        elif cand.burn_time >= duration:
            rejection_reasons.append("SKIPPED_SIMULATION_BURN_PAST_DURATION")

        is_feasible = (len(rejection_reasons) == 0)

        evaluated_candidates.append({
            "candidate": cand,
            "evaluation": eval_record,
            "is_feasible": is_feasible,
            "rejection_reasons": rejection_reasons,
        })

    # Separate feasible and rejected
    feasible = [item for item in evaluated_candidates if item["is_feasible"]]
    rejected = [item for item in evaluated_candidates if not item["is_feasible"]]

    # ---------------------------------------------------------
    # Multi-Criteria Ranking of Feasible Candidates
    # ---------------------------------------------------------
    # Sorting hierarchy:
    # 1. Delta-v magnitude ascending (minimize propellant expenditure)
    # 2. Maximum trajectory deviation ascending (minimize operational orbital disruption)
    # 3. Miss distance descending (maximize separation)
    def ranking_key(item):
        cand: ImpulsiveManoeuvre = item["candidate"]
        ev = item["evaluation"]
        dv = cand.delta_v_magnitude
        traj_dev = ev["max_trajectory_deviation_m"] if ev is not None else 0.0
        # Negative miss distance for descending order
        miss_dist = ev["post_manoeuvre_miss_distance_m"] if ev is not None else 0.0
        return (round(dv, 4), round(traj_dev, 2), -round(miss_dist, 2))

    feasible.sort(key=ranking_key)

    if feasible:
        status = "SUCCESS"
        selected_manoeuvre = feasible[0]["candidate"]
        selected_evaluation = feasible[0]["evaluation"]
    else:
        status = "NO_ACCEPTABLE_MANOEUVRE_FOUND"
        selected_manoeuvre = None
        selected_evaluation = None

    return {
        "status": status,
        "selected_manoeuvre": selected_manoeuvre,
        "selected_evaluation": selected_evaluation,
        "feasible_candidates": feasible,
        "rejected_candidates": rejected,
        "all_evaluations": evaluated_candidates,
        "nominal_tca_sec": ref_tca,
        "total_candidates": len(evaluated_candidates),
        "num_feasible": len(feasible),
        "num_rejected": len(rejected),
    }
