"""
D2/manoeuvres/candidate_generator.py
====================================
Candidate Collision-Avoidance Manoeuvre Generation Module for Deliverable 2 (D2).

Generates a structured, configurable catalog of candidate impulsive avoidance
manoeuvres defined in the protected satellite's local Radial-Transverse-Normal
(RTN) orbital frame across multiple burn epochs and delta-v magnitudes.

Key Principles:
- Direction diversity: Along-track (+T, -T), Cross-track (+N, -N), Radial (+R, -R),
  and combination vectors.
- Timing diversity: Configurable advance lead times before nominal TCA.
- Parameterized magnitude options: Configurable delta-v levels.
- Physical validity: Enforces strictly positive delta-v and 0 <= t_burn < TCA.
"""

from typing import List, Optional, Sequence
import numpy as np

from D2.manoeuvres.manoeuvre_model import (
    ImpulsiveManoeuvre,
    DIRECTION_VECTORS_RTN,
)


# Default candidate generation grids (SI units: s, m/s)
DEFAULT_LEAD_TIMES = [120.0, 300.0, 600.0]                 # Seconds before TCA
DEFAULT_DELTA_V_MAGNITUDES = [0.2, 0.5, 1.0, 2.0, 3.0, 5.0]  # m/s (up to standard budget limit)
DEFAULT_DIRECTIONS = ["+T", "-T", "+N", "-N", "+R", "-R", "+T+N", "-T+N"]


def generate_candidate_manoeuvres(
    tca_nominal: float,
    lead_times: Optional[Sequence[float]] = None,
    delta_v_magnitudes: Optional[Sequence[float]] = None,
    directions: Optional[Sequence[str]] = None,
    burn_times: Optional[Sequence[float]] = None,
    min_lead_time: float = 30.0
) -> List[ImpulsiveManoeuvre]:
    """
    Generate a discrete catalog of candidate impulsive avoidance manoeuvres in RTN.

    Parameters
    ----------
    tca_nominal : float
        Nominal predicted Time of Closest Approach (TCA) in seconds from epoch.
    lead_times : sequence of float, optional
        Lead times before nominal TCA (t_burn = tca_nominal - lead_time).
        Default: [120.0, 300.0, 600.0] seconds.
    delta_v_magnitudes : sequence of float, optional
        Candidate delta-v magnitudes in metres/second.
        Default: [0.2, 0.5, 1.0, 2.0] m/s.
    directions : sequence of str, optional
        List of direction keys from DIRECTION_VECTORS_RTN.
        Default: ['+T', '-T', '+N', '-N', '+R', '-R', '+T+N', '-T+N'].
    burn_times : sequence of float, optional
        Explicit burn epochs to use instead of lead times.
    min_lead_time : float, optional
        Minimum acceptable advance lead time before TCA (default 30.0 s).

    Returns
    -------
    candidates : list of ImpulsiveManoeuvre
        List of generated candidate manoeuvres.
    """
    if tca_nominal <= min_lead_time:
        raise ValueError(
            f"Nominal TCA ({tca_nominal:.1f}s) must exceed minimum lead time ({min_lead_time:.1f}s)."
        )

    # 1. Determine valid candidate burn times
    candidate_burn_times: List[float] = []

    if burn_times is not None:
        for bt in burn_times:
            bt_float = float(bt)
            if 0.0 <= bt_float <= (tca_nominal - min_lead_time):
                candidate_burn_times.append(bt_float)
    else:
        leads = lead_times if lead_times is not None else DEFAULT_LEAD_TIMES
        for lt in leads:
            bt = float(tca_nominal - lt)
            if bt >= 0.0:
                candidate_burn_times.append(bt)

        # Fallback if lead times were all too large for short TCA
        if not candidate_burn_times:
            candidate_burn_times = [
                float(0.25 * tca_nominal),
                float(0.50 * tca_nominal),
            ]

    # Deduplicate and sort burn times
    candidate_burn_times = sorted(list(set(candidate_burn_times)))

    # 2. Determine magnitudes and directions
    mags = [float(m) for m in (delta_v_magnitudes if delta_v_magnitudes is not None else DEFAULT_DELTA_V_MAGNITUDES)]
    mags = [m for m in mags if m > 0.0]
    if not mags:
        raise ValueError("At least one strictly positive delta-v magnitude must be provided.")

    dirs = list(directions if directions is not None else DEFAULT_DIRECTIONS)
    for d in dirs:
        if d not in DIRECTION_VECTORS_RTN:
            raise ValueError(f"Unknown direction label '{d}'. Valid options are: {list(DIRECTION_VECTORS_RTN.keys())}")

    # 3. Permute combinations into ImpulsiveManoeuvre candidates
    candidates: List[ImpulsiveManoeuvre] = []
    idx = 1

    for bt in candidate_burn_times:
        for mag in mags:
            for d in dirs:
                u_dir = DIRECTION_VECTORS_RTN[d]
                dv_rtn = mag * u_dir
                cid = f"MAN_{idx:03d}_{d}_{mag:.2f}mps_T{bt:.0f}s"

                cand = ImpulsiveManoeuvre(
                    burn_time=bt,
                    delta_v_magnitude=mag,
                    direction_label=d,
                    delta_v_rtn=dv_rtn,
                    manoeuvre_id=cid
                )
                candidates.append(cand)
                idx += 1

    return candidates
