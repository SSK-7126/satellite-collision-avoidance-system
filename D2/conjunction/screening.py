"""
D2/conjunction/screening.py
===========================
Conjunction Screening and Candidate Filtering Module for Deliverable 2 (D2),
strictly following Section 5.4 of the Satellite Anti-Collision Technical Guide.

Key Concepts & Principles (Technical Guide Section 5.4):
- A screening volume or distance threshold is a computational filter to identify
  candidate conjunction pairs for further analysis.
- It is NOT a universal operational threshold or a collision warning.
- A conjunction is a predicted close approach; it is NOT automatically a collision
  warning or a probability-of-collision (Pc) result.
- Linear CPA estimates and numerically propagated TCA assessments are kept
  strictly distinguishable in data structures and reporting.

Conventions & Units:
- Reference Frame : Earth-Centred Inertial (ECI)
- Thresholds      : Metres (m)
- Velocities      : Metres per second (m/s)
- Time            : Seconds (s)
- Precision       : Float64
"""

import numpy as np

from D2.conjunction.tca import (
    calculate_relative_state,
    calculate_linear_cpa,
    calculate_numerical_tca,
)


# Default spherical screening threshold (SI units: metres)
DEFAULT_SCREENING_THRESHOLD_M = 25_000.0  # 25 km computational screening filter


def screen_conjunction(
    initial_state1,
    initial_state2,
    duration,
    dt=1.0,
    threshold_m=DEFAULT_SCREENING_THRESHOLD_M,
    object1_id="PROTECTED_SAT",
    object2_id="SECONDARY_OBJ",
    epoch="2026-01-01T00:00:00Z",
    refine_tca=True
):
    """
    Screen a candidate pair of space objects for conjunction within an assessment window.
    (Technical Guide Section 5.4)

    Executes:
    1. Initial relative state calculation: r_rel = r2 - r1, v_rel = v2 - v1.
    2. Local linear CPA approximation: t_CPA, d_CPA constrained to assessment window.
    3. Numerical trajectory propagation and separation minimization: actual TCA, miss distance.
    4. Explicit comparison between linear approximation and numerical result.
    5. Computational screening threshold evaluation (filtering candidate pairs).

    Parameters
    ----------
    initial_state1 : array-like
        Initial 6D state vector of Object 1 (Protected Satellite) in SI units.
    initial_state2 : array-like
        Initial 6D state vector of Object 2 (Secondary Object) in SI units.
    duration : float
        Assessment interval duration in seconds.
    dt : float, optional
        Integration time step in seconds (default 1.0 s).
    threshold_m : float, optional
        Screening volume radius / distance threshold in metres (default 25,000.0 m).
    object1_id : str, optional
        Identifier for Object 1.
    object2_id : str, optional
        Identifier for Object 2.
    epoch : str, optional
        Reference epoch string.
    refine_tca : bool, optional
        Whether to perform continuous sub-step refinement for numerical TCA (default True).

    Returns
    -------
    record : dict
        Standardized conjunction screening record:
        - 'object1_id': Primary object identifier.
        - 'object2_id': Secondary object identifier.
        - 'epoch': Epoch identifier.
        - 'duration': Assessment interval in seconds.
        - 'screening_threshold_m': Screening threshold applied in metres.
        - 'is_candidate': Boolean flag indicating if miss distance <= threshold.
        - 'classification': 'CONJUNCTION_CANDIDATE' or 'SAFE_PASS'.
        - 'linear_cpa': Dictionary of linear approximation metrics.
        - 'numerical_tca': Dictionary of numerically propagated metrics.
        - 'comparison': Comparison dictionary highlighting curvature differences.
        - 'uncertainty_assumptions': Explicit statement on uncertainty representation.
        - 'disclaimer': Explicit statement that this is a screening filter, not a Pc.
    """
    if threshold_m <= 0:
        raise ValueError("Screening threshold must be strictly positive.")

    # 1. Calculate initial relative state
    r_rel_0, v_rel_0 = calculate_relative_state(initial_state1, initial_state2)

    # 2. Local linear CPA approximation (constrained to [0, duration])
    linear_res = calculate_linear_cpa(
        r_rel_0,
        v_rel_0,
        window=(0.0, float(duration))
    )

    # 3. Numerical trajectory propagation & separation minimization
    num_res = calculate_numerical_tca(
        initial_state1=initial_state1,
        initial_state2=initial_state2,
        duration=duration,
        dt=dt,
        refine=refine_tca,
        object1_id=object1_id,
        object2_id=object2_id,
        epoch=epoch,
    )

    # 4. Compare linear CPA and numerical TCA
    delta_t = float(abs(linear_res["t_cpa"] - num_res["tca"]))
    delta_d = float(abs(linear_res["d_cpa"] - num_res["miss_distance"]))

    # 5. Screening threshold evaluation (computational filter)
    is_candidate = bool(num_res["miss_distance"] <= threshold_m)
    classification = "CONJUNCTION_CANDIDATE" if is_candidate else "SAFE_PASS"

    return {
        "object1_id": str(object1_id),
        "object2_id": str(object2_id),
        "epoch": str(epoch),
        "duration": float(duration),
        "screening_threshold_m": float(threshold_m),
        "is_candidate": is_candidate,
        "classification": classification,
        "linear_cpa": {
            "t_cpa_sec": linear_res["t_cpa"],
            "d_cpa_m": linear_res["d_cpa"],
            "t_cpa_unconstrained_sec": linear_res["t_cpa_unconstrained"],
            "relative_speed_mps": linear_res["relative_speed"],
            "is_constrained": linear_res["is_constrained"],
            "near_zero_velocity": linear_res["near_zero_velocity"],
        },
        "numerical_tca": {
            "tca_sec": num_res["tca"],
            "miss_distance_m": num_res["miss_distance"],
            "relative_speed_mps": num_res["relative_speed"],
            "relative_position_m": num_res["relative_position"],
            "relative_velocity_mps": num_res["relative_velocity"],
            "discrete_tca_sec": num_res["discrete_tca"],
            "discrete_miss_distance_m": num_res["discrete_miss_distance"],
        },
        "comparison": {
            "delta_t_sec": delta_t,
            "delta_distance_m": delta_d,
            "note": (
                "Linear CPA assumes constant relative velocity. "
                "Numerical TCA accounts for orbital curvature under Earth gravity."
            ),
        },
        "uncertainty_assumptions": num_res["uncertainty_assumptions"],
        "disclaimer": (
            "Screening threshold is a computational filter, not a universal collision-warning "
            "threshold. Conjunction is not a collision warning or probability-of-collision result."
        ),
    }


def filter_conjunction_candidates(
    primary_state,
    secondary_catalog,
    duration,
    dt=1.0,
    threshold_m=DEFAULT_SCREENING_THRESHOLD_M,
    primary_id="PROTECTED_SAT",
    epoch="2026-01-01T00:00:00Z"
):
    """
    Screen a catalog of secondary objects against a protected satellite.

    Parameters
    ----------
    primary_state : array-like
        6D initial state of the protected satellite.
    secondary_catalog : list of dict
        List of secondary objects, each containing:
        - 'id': str
        - 'state': array-like (6 elements)
    duration : float
        Assessment interval duration in seconds.
    dt : float, optional
        Integration time step in seconds (default 1.0 s).
    threshold_m : float, optional
        Screening distance threshold in metres.
    primary_id : str, optional
        Primary object identifier.
    epoch : str, optional
        Reference epoch string.

    Returns
    -------
    candidates : list of dict
        List of conjunction records that pass the screening threshold,
        sorted by miss distance in ascending order.
    all_reports : list of dict
        List of all conjunction assessment records evaluated.
    """
    candidates = []
    all_reports = []

    for sec in secondary_catalog:
        sec_id = sec.get("id", "UNKNOWN_SECONDARY")
        sec_state = sec["state"]

        report = screen_conjunction(
            initial_state1=primary_state,
            initial_state2=sec_state,
            duration=duration,
            dt=dt,
            threshold_m=threshold_m,
            object1_id=primary_id,
            object2_id=sec_id,
            epoch=epoch,
        )
        all_reports.append(report)

        if report["is_candidate"]:
            candidates.append(report)

    # Sort candidate encounters by minimum miss distance
    candidates.sort(key=lambda r: r["numerical_tca"]["miss_distance_m"])

    return candidates, all_reports
