"""
D2/manoeuvres/manoeuvre_evaluator.py
====================================
Candidate Collision-Avoidance Manoeuvre Simulation & Evaluation Module (D2).

Evaluates the physical and probabilistic consequences of applying a candidate
impulsive manoeuvre to the protected satellite:
1. Propagates the satellite to burn epoch t_burn.
2. Applies delta-v in ECI coordinates.
3. Propagates the modified satellite trajectory to the end of the assessment window.
4. Propagates the nominal secondary object trajectory over matching timestamps.
5. Recalculates post-manoeuvre numerical TCA, miss distance, and relative velocity.
6. Propagates state covariance along the modified trajectory to the new TCA epoch.
7. Re-evaluates post-manoeuvre collision probability (Pc) when covariance is available.
8. Calculates trajectory deviation from the nominal operational path.

Conventions & Units:
- Reference Frame : Earth-Centred Inertial (ECI)
- Distances       : Metres (m)
- Velocities      : Metres per second (m/s)
- Time            : Seconds (s)
- Precision       : Float64
"""

from typing import Dict, Any, Optional
import numpy as np

from D2.dynamics.two_body import MU_EARTH
from D2.dynamics.orbit_propagator import propagate_orbit
from D2.dynamics.variational import propagate_state_and_stm
from D2.uncertainty.covariance import (
    validate_covariance,
    combine_relative_covariance,
    propagate_covariance,
)
from D2.uncertainty.collision_probability import (
    calculate_collision_probability,
    calculate_simplified_risk_proxy,
)
from D2.manoeuvres.manoeuvre_model import ImpulsiveManoeuvre


def simulate_manoeuvre(
    initial_state_sat: np.ndarray,
    initial_state_sec: np.ndarray,
    manoeuvre: ImpulsiveManoeuvre,
    duration: float,
    dt: float = 1.0,
    initial_cov_sat: Optional[np.ndarray] = None,
    initial_cov_sec: Optional[np.ndarray] = None,
    hard_body_radius: float = 10.0,
    mu: float = MU_EARTH,
    nominal_sat_trajectory: Optional[Any] = None,
    nominal_sec_trajectory: Optional[Any] = None,
    skip_covariance_if_insufficient_miss: Optional[float] = None
) -> Dict[str, Any]:
    """
    Simulate a candidate impulsive manoeuvre and recalculate the post-manoeuvre
    encounter geometry, trajectory deviation, and collision probability.

    Parameters
    ----------
    initial_state_sat : array-like
        Initial 6D state of protected satellite at t = 0 [m, m/s].
    initial_state_sec : array-like
        Initial 6D state of secondary debris at t = 0 [m, m/s].
    manoeuvre : ImpulsiveManoeuvre
        Candidate manoeuvre to apply.
    duration : float
        Total assessment interval duration in seconds.
    dt : float, optional
        Integration time step in seconds (default 1.0 s).
    initial_cov_sat : array-like, optional
        Initial 6x6 covariance of protected satellite at t = 0.
    initial_cov_sec : array-like, optional
        Initial 6x6 covariance of secondary object at t = 0.
    hard_body_radius : float, optional
        Combined hard-body radius in metres (default 10.0 m).
    mu : float, optional
        Earth gravitational parameter.

    Returns
    -------
    eval_record : dict
        Comprehensive evaluation record for the candidate manoeuvre.
    """
    t_burn = float(manoeuvre.burn_time)
    dur = float(duration)
    if t_burn >= dur:
        raise ValueError(f"Burn time ({t_burn}s) must be less than simulation duration ({dur}s).")

    s1_0 = np.asarray(initial_state_sat, dtype=np.float64).copy()
    s2_0 = np.asarray(initial_state_sec, dtype=np.float64).copy()

    # -------------------------------------------------------------
    # 1. Propagate satellite to burn epoch t_burn
    # -------------------------------------------------------------
    if t_burn > 0.0:
        times_pre, states_pre = propagate_orbit(s1_0, duration=t_burn, dt=dt)
        state_at_burn = states_pre[-1].copy()
    else:
        times_pre = np.array([0.0])
        states_pre = np.array([s1_0.copy()])
        state_at_burn = s1_0.copy()

    r_burn = state_at_burn[:3]
    v_burn = state_at_burn[3:]

    # -------------------------------------------------------------
    # 2. Apply impulsive delta-v in ECI coordinates
    # -------------------------------------------------------------
    delta_v_eci = manoeuvre.resolve_eci(r_burn, v_burn)
    state_post_burn = state_at_burn.copy()
    state_post_burn[3:] += delta_v_eci

    # -------------------------------------------------------------
    # 3. Propagate modified satellite trajectory from t_burn to duration
    # -------------------------------------------------------------
    rem_duration = dur - t_burn
    times_post, states_post = propagate_orbit(state_post_burn, duration=rem_duration, dt=dt)

    # Stitch full modified satellite trajectory across [0, duration]
    if t_burn > 0.0:
        full_times_sat = np.concatenate((times_pre[:-1], times_post + t_burn))
        full_states_sat = np.vstack((states_pre[:-1], states_post))
    else:
        full_times_sat = times_post
        full_states_sat = states_post

    # -------------------------------------------------------------
    # 4. Propagate nominal trajectories (satellite and secondary)
    # -------------------------------------------------------------
    if nominal_sat_trajectory is not None:
        times_nom, states_sat_nom = nominal_sat_trajectory
    else:
        times_nom, states_sat_nom = propagate_orbit(s1_0, duration=dur, dt=dt)

    if nominal_sec_trajectory is not None:
        _, states_sec_nom = nominal_sec_trajectory
    else:
        _, states_sec_nom = propagate_orbit(s2_0, duration=dur, dt=dt)

    # -------------------------------------------------------------
    # 5. Calculate trajectory deviation: |r_mod(t) - r_nom(t)|
    # -------------------------------------------------------------
    # Truncate to matching length if minor step boundary difference
    n_pts = min(len(full_states_sat), len(states_sat_nom), len(states_sec_nom))
    t_eval = full_times_sat[:n_pts]
    states_sat_eval = full_states_sat[:n_pts]
    states_nom_eval = states_sat_nom[:n_pts]
    states_sec_eval = states_sec_nom[:n_pts]

    pos_dev_vec = states_sat_eval[:, :3] - states_nom_eval[:, :3]
    dev_norms = np.linalg.norm(pos_dev_vec, axis=1)
    max_traj_dev = float(np.max(dev_norms))
    final_traj_dev = float(dev_norms[-1])

    # -------------------------------------------------------------
    # 6. Recalculate post-manoeuvre encounter TCA and miss distance
    # -------------------------------------------------------------
    rel_pos_post = states_sec_eval[:, :3] - states_sat_eval[:, :3]
    rel_vel_post = states_sec_eval[:, 3:] - states_sat_eval[:, 3:]
    separations = np.linalg.norm(rel_pos_post, axis=1)

    min_idx = int(np.argmin(separations))
    t_discrete = float(t_eval[min_idx])
    d_discrete = float(separations[min_idx])

    # Quadratic sub-step refinement around discrete minimum
    tca_new = t_discrete
    miss_distance_new = d_discrete
    r_rel_tca_new = rel_pos_post[min_idx].copy()
    v_rel_tca_new = rel_vel_post[min_idx].copy()

    if 0 < min_idx < len(t_eval) - 1:
        y0 = float(separations[min_idx - 1]**2)
        y1 = float(separations[min_idx]**2)
        y2 = float(separations[min_idx + 1]**2)
        denom = y0 - 2.0 * y1 + y2
        if denom > 1e-14:
            h = float(t_eval[min_idx] - t_eval[min_idx - 1])
            delta = -0.5 * (y2 - y0) / denom * h
            if abs(delta) <= h:
                t_refined = t_discrete + delta
                # Interpolate states
                if 0.0 <= t_refined <= dur:
                    tca_new = float(t_refined)
                    # Linearly interpolate between adjacent states for smooth sub-second vector
                    alpha = delta / h
                    if alpha >= 0:
                        r_rel_tca_new = (1.0 - alpha) * rel_pos_post[min_idx] + alpha * rel_pos_post[min_idx + 1]
                        v_rel_tca_new = (1.0 - alpha) * rel_vel_post[min_idx] + alpha * rel_vel_post[min_idx + 1]
                    else:
                        r_rel_tca_new = (1.0 + alpha) * rel_pos_post[min_idx] - alpha * rel_pos_post[min_idx - 1]
                        v_rel_tca_new = (1.0 + alpha) * rel_vel_post[min_idx] - alpha * rel_vel_post[min_idx - 1]
                    miss_distance_new = float(np.linalg.norm(r_rel_tca_new))

    tca_new = float(np.clip(tca_new, 0.0, dur))
    miss_distance_new = max(0.0, float(miss_distance_new))
    rel_speed_new = float(np.linalg.norm(v_rel_tca_new))

    # Trajectory deviation at new TCA
    idx_tca = int(np.clip(min_idx, 0, len(dev_norms) - 1))
    tca_traj_dev = float(dev_norms[idx_tca])

    # -------------------------------------------------------------
    # 7. Covariance propagation to new TCA and collision probability
    # -------------------------------------------------------------
    cov_rel_tca_new = None
    pc_new = None
    log10_pc_new = None
    mahalanobis_new = None
    pc_status = "COVARIANCE_MISSING"

    should_eval_cov = (initial_cov_sat is not None and initial_cov_sec is not None)
    if should_eval_cov and (skip_covariance_if_insufficient_miss is not None):
        if miss_distance_new < skip_covariance_if_insufficient_miss:
            should_eval_cov = False
            pc_status = "SKIPPED_INSUFFICIENT_MISS_DISTANCE"

    if should_eval_cov:
        p1_0 = validate_covariance(initial_cov_sat, name="Sat Covariance")
        p2_0 = validate_covariance(initial_cov_sec, name="Sec Covariance")

        # A. Secondary object covariance propagated from 0 to tca_new
        _, phi2_tca = propagate_state_and_stm(s2_0, duration=tca_new, dt=dt, mu=mu)
        p2_cov_tca = propagate_covariance(p2_0, phi2_tca, q=None)

        # B. Manoeuvred satellite covariance propagated across burn
        if tca_new <= t_burn:
            # Conjunction occurs before or at burn
            _, phi1_tca = propagate_state_and_stm(s1_0, duration=tca_new, dt=dt, mu=mu)
            p1_cov_tca = propagate_covariance(p1_0, phi1_tca, q=None)
        else:
            # Propagate pre-burn (0 -> t_burn) along nominal trajectory
            if t_burn > 0.0:
                _, phi_pre = propagate_state_and_stm(s1_0, duration=t_burn, dt=dt, mu=mu)
                p1_burn = propagate_covariance(p1_0, phi_pre, q=None)
            else:
                p1_burn = p1_0.copy()

            # Propagate post-burn (t_burn -> tca_new) along modified trajectory
            rem_to_tca = tca_new - t_burn
            _, phi_post = propagate_state_and_stm(state_post_burn, duration=rem_to_tca, dt=dt, mu=mu)
            p1_cov_tca = propagate_covariance(p1_burn, phi_post, q=None)

        # C. Relative covariance at new TCA (independent-error assumption)
        cov_rel_tca_new = combine_relative_covariance(p1_cov_tca, p2_cov_tca)

        # D. Recalculate collision probability
        res_pc = calculate_collision_probability(
            r_rel_tca=r_rel_tca_new,
            v_rel_tca=v_rel_tca_new,
            cov_rel_tca=cov_rel_tca_new,
            hard_body_radius=hard_body_radius
        )
        pc_new = res_pc["pc"]
        log10_pc_new = res_pc.get("log10_pc")
        mahalanobis_new = res_pc.get("mahalanobis_distance")
        pc_status = res_pc["status"]
    else:
        # Covariance unavailable: clearly label risk proxy
        risk_proxy = calculate_simplified_risk_proxy(
            miss_distance=miss_distance_new,
            hard_body_radius=hard_body_radius,
            relative_speed=rel_speed_new
        )

    return {
        "manoeuvre_id": manoeuvre.manoeuvre_id,
        "burn_time_sec": t_burn,
        "delta_v_magnitude_mps": manoeuvre.delta_v_magnitude,
        "direction_label": manoeuvre.direction_label,
        "delta_v_rtn": manoeuvre.delta_v_rtn,
        "delta_v_eci": delta_v_eci,
        "post_manoeuvre_tca_sec": tca_new,
        "post_manoeuvre_miss_distance_m": miss_distance_new,
        "post_manoeuvre_relative_speed_mps": rel_speed_new,
        "post_manoeuvre_relative_position_m": r_rel_tca_new,
        "post_manoeuvre_relative_velocity_mps": v_rel_tca_new,
        "post_manoeuvre_pc": pc_new,
        "post_manoeuvre_log10_pc": log10_pc_new,
        "post_manoeuvre_mahalanobis_distance": mahalanobis_new,
        "pc_status": pc_status,
        "post_manoeuvre_cov_rel": cov_rel_tca_new,
        "max_trajectory_deviation_m": max_traj_dev,
        "tca_trajectory_deviation_m": tca_traj_dev,
        "final_trajectory_deviation_m": final_traj_dev,
    }
