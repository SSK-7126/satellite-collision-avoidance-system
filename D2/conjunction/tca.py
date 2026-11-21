"""
D2/conjunction/tca.py
=====================
Time of Closest Approach (TCA) and Closest Point of Approach (CPA) calculations
for Deliverable 2 (D2), following Sections 5.1–5.3 of the Satellite Anti-Collision
Technical Guide.

Methodologies Implemented:
1. Section 5.1: Relative State:
      r_rel(t) = r2(t) - r1(t)
      v_rel(t) = v2(t) - v1(t)
2. Section 5.2: Closest Point of Approach (local linear approximation):
      t_CPA = -(r_rel · v_rel) / (v_rel · v_rel)
      d_CPA = |r_rel + v_rel * t_CPA|
      - Safe handling for near-zero relative velocity.
      - Constraint of candidate CPA time to the assessment window.
3. Section 5.3: Time of Closest Approach (numerical propagation):
      - Propagate curved orbital trajectories using the two-body RK4 integrator.
      - Numerically minimize separation over the assessment interval.
      - High-precision continuous refinement using parabolic sub-step interpolation.
      - Record TCA, miss distance, relative speed, and encounter geometry.

Conventions & Units:
- Reference Frame : Earth-Centred Inertial (ECI)
- Positions       : Metres (m)
- Velocities      : Metres per second (m/s)
- Time            : Seconds (s)
- Precision       : Float64
"""

import numpy as np

from D2.dynamics.rk4 import rk4_step
from D2.dynamics.orbit_propagator import propagate_orbit


def calculate_relative_state(state1, state2):
    """
    Calculate relative position and velocity vectors between two objects.
    (Technical Guide Section 5.1)

    Relative state is defined as Object 2 relative to Object 1:
        r_rel = r2 - r1
        v_rel = v2 - v1

    Parameters
    ----------
    state1 : array-like
        6D state vector of Object 1 (Protected Satellite) [x, y, z, vx, vy, vz].
    state2 : array-like
        6D state vector of Object 2 (Secondary Object) [x, y, z, vx, vy, vz].

    Returns
    -------
    r_rel : numpy.ndarray
        Relative position vector [rx, ry, rz] in metres.
    v_rel : numpy.ndarray
        Relative velocity vector [vx, vy, vz] in metres/second.
    """
    s1 = np.asarray(state1, dtype=np.float64)
    s2 = np.asarray(state2, dtype=np.float64)

    if s1.shape != (6,) or s2.shape != (6,):
        raise ValueError("Both state vectors must contain exactly 6 elements [x, y, z, vx, vy, vz].")

    r_rel = s2[:3] - s1[:3]
    v_rel = s2[3:] - s1[3:]

    return r_rel, v_rel


def calculate_linear_cpa(r_rel, v_rel, window=None, tol=1e-12):
    """
    Calculate local linear Closest Point of Approach (CPA) time and distance.
    (Technical Guide Section 5.2)

    Equations:
        t_CPA = -(r_rel · v_rel) / (v_rel · v_rel)
        d_CPA = |r_rel + v_rel * t_CPA|

    Assumptions & Safeguards:
        - Assumes rectilinear motion with constant relative velocity over short intervals.
        - Safely handles near-zero relative velocity (|v_rel|^2 <= tol) without division by zero.
        - Constrains candidate closest-approach time to the assessment window [t_min, t_max].

    Parameters
    ----------
    r_rel : array-like
        Initial relative position vector (r2 - r1) in metres.
    v_rel : array-like
        Initial relative velocity vector (v2 - v1) in metres/second.
    window : tuple of (float, float), optional
        Assessment window (t_min, t_max) in seconds to constrain candidate CPA time.
        If None, the unconstrained linear CPA time is used.
    tol : float, optional
        Tolerance for near-zero relative velocity squared magnitude (default 1e-12).

    Returns
    -------
    result : dict
        Dictionary containing:
        - 't_cpa': Constrained CPA time in seconds.
        - 'd_cpa': CPA distance (miss distance) in metres (always non-negative).
        - 't_cpa_unconstrained': Unconstrained analytical CPA time in seconds.
        - 'r_cpa': Relative position vector at CPA in metres.
        - 'v_rel': Relative velocity vector in metres/second.
        - 'relative_speed': Magnitude of relative velocity in metres/second.
        - 'is_constrained': Boolean flag indicating if CPA time was clamped to the window.
        - 'near_zero_velocity': Boolean flag indicating if relative velocity was near-zero.
    """
    r_rel = np.asarray(r_rel, dtype=np.float64)
    v_rel = np.asarray(v_rel, dtype=np.float64)

    if r_rel.shape != (3,) or v_rel.shape != (3,):
        raise ValueError("r_rel and v_rel must each be 3-element vectors.")

    v_sq = float(np.dot(v_rel, v_rel))
    rel_speed = float(np.sqrt(v_sq))

    # Safe handling of near-zero relative velocity
    if v_sq <= tol:
        t_unconstrained = 0.0
        if window is not None:
            t_constrained = float(np.clip(t_unconstrained, window[0], window[1]))
            is_constrained = (t_constrained != t_unconstrained)
        else:
            t_constrained = t_unconstrained
            is_constrained = False

        r_cpa = r_rel.copy()
        d_cpa = float(np.linalg.norm(r_cpa))

        return {
            "t_cpa": t_constrained,
            "d_cpa": d_cpa,
            "t_cpa_unconstrained": t_unconstrained,
            "r_cpa": r_cpa,
            "v_rel": v_rel,
            "relative_speed": rel_speed,
            "is_constrained": is_constrained,
            "near_zero_velocity": True,
        }

    # Standard linear CPA time calculation: t_CPA = -(r_rel · v_rel) / (v_rel · v_rel)
    t_unconstrained = -float(np.dot(r_rel, v_rel)) / v_sq

    # Constrain candidate closest-approach time to the assessment window if provided
    if window is not None:
        t_min, t_max = window
        if t_min > t_max:
            raise ValueError(f"Invalid window: t_min ({t_min}) must be <= t_max ({t_max}).")
        t_constrained = float(np.clip(t_unconstrained, t_min, t_max))
        is_constrained = not np.isclose(t_constrained, t_unconstrained)
    else:
        t_constrained = t_unconstrained
        is_constrained = False

    # Closest approach distance: d_CPA = |r_rel + v_rel * t_CPA|
    r_cpa = r_rel + v_rel * t_constrained
    d_cpa = float(np.linalg.norm(r_cpa))

    return {
        "t_cpa": t_constrained,
        "d_cpa": d_cpa,
        "t_cpa_unconstrained": t_unconstrained,
        "r_cpa": r_cpa,
        "v_rel": v_rel,
        "relative_speed": rel_speed,
        "is_constrained": is_constrained,
        "near_zero_velocity": False,
    }


def calculate_numerical_tca(
    initial_state1,
    initial_state2,
    duration,
    dt=1.0,
    refine=True,
    object1_id="PROTECTED_SAT",
    object2_id="SECONDARY_OBJ",
    epoch="2026-01-01T00:00:00Z"
):
    """
    Determine actual Time of Closest Approach (TCA) and miss distance by
    numerically propagating both curved trajectories using the two-body RK4
    integrator and minimizing separation over the assessment window.
    (Technical Guide Section 5.3)

    Parameters
    ----------
    initial_state1 : array-like
        Initial 6D state [x, y, z, vx, vy, vz] of Object 1 in SI units.
    initial_state2 : array-like
        Initial 6D state [x, y, z, vx, vy, vz] of Object 2 in SI units.
    duration : float
        Total assessment interval duration in seconds.
    dt : float, optional
        Integration time step in seconds (default 1.0 s).
    refine : bool, optional
        If True, refines discrete minimum using quadratic sub-step interpolation (default True).
    object1_id : str, optional
        Identifier for Object 1.
    object2_id : str, optional
        Identifier for Object 2.
    epoch : str, optional
        Propagation epoch identifier or timestamp.

    Returns
    -------
    result : dict
        Comprehensive conjunction assessment record:
        - 'object1_id': ID of Object 1.
        - 'object2_id': ID of Object 2.
        - 'epoch': Epoch timestamp string.
        - 'assessment_duration': Assessment interval in seconds.
        - 'tca': Refined Time of Closest Approach in seconds from epoch.
        - 'miss_distance': Minimum separation distance at TCA in metres (>= 0).
        - 'relative_speed': Relative velocity magnitude at TCA in metres/second.
        - 'relative_position': Relative position vector [rx, ry, rz] at TCA in metres.
        - 'relative_velocity': Relative velocity vector [vx, vy, vz] at TCA in metres/second.
        - 'discrete_tca': Time of discrete grid minimum in seconds.
        - 'discrete_miss_distance': Discrete grid separation minimum in metres.
        - 'trajectory_times': Array of simulation timestamps.
        - 'trajectory_distances': Array of separation distances at each timestamp.
        - 'uncertainty_assumptions': Explicit note on uncertainty representation.
    """
    if duration <= 0:
        raise ValueError("Assessment duration must be strictly positive.")
    if dt <= 0:
        raise ValueError("Integration time step must be strictly positive.")

    s1 = np.asarray(initial_state1, dtype=np.float64)
    s2 = np.asarray(initial_state2, dtype=np.float64)

    # 1. Propagate both curved trajectories using existing two-body RK4 propagator
    times1, states1 = propagate_orbit(s1, duration=duration, dt=dt)
    times2, states2 = propagate_orbit(s2, duration=duration, dt=dt)

    # 2. Calculate relative states and separation across all timestamps
    rel_positions = states2[:, :3] - states1[:, :3]
    rel_velocities = states2[:, 3:] - states1[:, 3:]
    distances = np.linalg.norm(rel_positions, axis=1)

    # 3. Locate discrete minimum separation
    min_idx = int(np.argmin(distances))
    t_discrete = float(times1[min_idx])
    d_discrete = float(distances[min_idx])

    # 4. Continuous sub-step refinement using quadratic vertex interpolation on d^2(t)
    t_tca = t_discrete
    miss_distance = d_discrete
    r_tca = rel_positions[min_idx].copy()
    v_tca = rel_velocities[min_idx].copy()

    if refine and 0 < min_idx < len(times1) - 1:
        # Use squared distance for smooth, symmetric parabolic behaviour near vertex
        y0 = float(distances[min_idx - 1]**2)
        y1 = float(distances[min_idx]**2)
        y2 = float(distances[min_idx + 1]**2)

        denom = y0 - 2.0 * y1 + y2
        if denom > 1e-14:
            # Vertex offset delta relative to t_discrete
            h = float(times1[min_idx] - times1[min_idx - 1])
            delta = -0.5 * (y2 - y0) / denom * h

            # Constrain refinement within adjacent time steps [-h, +h]
            if abs(delta) <= h:
                t_candidate = t_discrete + delta

                # Safely integrate forward from t_{min_idx - 1} using a positive step
                step_from_prev = t_candidate - times1[min_idx - 1]
                if step_from_prev > 0:
                    st1_refined = rk4_step(states1[min_idx - 1], step_from_prev)
                    st2_refined = rk4_step(states2[min_idx - 1], step_from_prev)

                    r_cand = st2_refined[:3] - st1_refined[:3]
                    v_cand = st2_refined[3:] - st1_refined[3:]
                    d_cand = float(np.linalg.norm(r_cand))

                    # Accept refinement if it improves or matches discrete minimum
                    if d_cand <= d_discrete:
                        t_tca = float(t_candidate)
                        miss_distance = d_cand
                        r_tca = r_cand
                        v_tca = v_cand

    # Constrain TCA within assessment interval [0.0, duration]
    t_tca = float(np.clip(t_tca, 0.0, duration))
    miss_distance = max(0.0, float(miss_distance))
    rel_speed = float(np.linalg.norm(v_tca))

    return {
        "object1_id": str(object1_id),
        "object2_id": str(object2_id),
        "epoch": str(epoch),
        "assessment_duration": float(duration),
        "tca": t_tca,
        "miss_distance": miss_distance,
        "relative_speed": rel_speed,
        "relative_position": r_tca,
        "relative_velocity": v_tca,
        "discrete_tca": t_discrete,
        "discrete_miss_distance": d_discrete,
        "trajectory_times": times1,
        "trajectory_distances": distances,
        "uncertainty_assumptions": "Deterministic two-body RK4 (no covariance propagated)",
    }

