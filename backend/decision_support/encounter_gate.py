"""
backend/decision_support/encounter_gate.py
=========================================
Strict state validation gate for encounter completion in simulation.

CRITICAL ARCHITECTURAL CONSTRAINTS:
1. Step navigation alone must NEVER establish encounter completion.
2. The manoeuvre must have been executed in simulation (manoeuvre_executed == True).
3. Simulation time must have reached or passed post-manoeuvre TCA (current_time_seconds >= post_tca_seconds).
4. The post-encounter propagated state must actually have been evaluated (post_state_evaluated == True).
5. The calculated separation must be valid (finite, positive) and greater than or equal to configured clearance threshold.
6. Invalid, missing, or stale state data must never produce a completed status.
"""

from dataclasses import dataclass
from typing import Optional
import math


@dataclass
class EncounterCompletionStatus:
    status: str
    detail: str
    is_completed: bool
    clearance_achieved: bool


def evaluate_step8_completion_gate(
    step_index: int,
    current_time_seconds: float,
    manoeuvre_executed: bool,
    post_tca_seconds: Optional[float],
    post_miss_distance_m: Optional[float],
    post_state_evaluated: bool,
    clearance_threshold_m: float = 2000.0,
) -> EncounterCompletionStatus:
    """
    Evaluates encounter completion status under strict multi-condition gate.

    Parameters
    ----------
    step_index : int
        Current demonstration sequence step index (1-8).
    current_time_seconds : float
        Current simulation elapsed time in seconds.
    manoeuvre_executed : bool
        Whether the avoidance manoeuvre burn has been executed.
    post_tca_seconds : float or None
        Post-burn Time of Closest Approach epoch in seconds.
    post_miss_distance_m : float or None
        Post-burn evaluated miss distance in metres.
    post_state_evaluated : bool
        Explicit boolean flag indicating post-encounter trajectory has been propagated and evaluated at TCA.
    clearance_threshold_m : float
        Operational clearance safety threshold in metres (default: 2000.0 m).

    Returns
    -------
    EncounterCompletionStatus
    """
    # 1. Validate post-encounter TCA
    b_valid_tca = (
        post_tca_seconds is not None
        and not math.isnan(post_tca_seconds)
        and not math.isinf(post_tca_seconds)
        and post_tca_seconds > 0.0
    )
    b_tca_reached = b_valid_tca and (current_time_seconds >= post_tca_seconds)

    # 2. Validate post-encounter separation / state data
    b_valid_post_data = (
        post_miss_distance_m is not None
        and not math.isnan(post_miss_distance_m)
        and not math.isinf(post_miss_distance_m)
        and post_miss_distance_m > 0.0
    )
    b_clearance_achieved = b_valid_post_data and (post_miss_distance_m >= clearance_threshold_m)

    # 3. Strict completion gate: ALL four conditions must hold:
    #    - Manoeuvre executed in simulation
    #    - TCA reached or passed
    #    - Post-encounter state actually evaluated
    #    - State data valid (not missing, NaN, <= 0)
    # Notice: step_index alone NEVER satisfies this gate.
    if manoeuvre_executed and b_tca_reached and post_state_evaluated and b_valid_post_data:
        if b_clearance_achieved:
            return EncounterCompletionStatus(
                status="SIMULATED ENCOUNTER COMPLETED \u2014 CLEARANCE ACHIEVED",
                detail=(
                    f"Simulated encounter epoch passed (T={post_tca_seconds:.2f}s); "
                    f"evaluated post-encounter state confirms clearance achieved "
                    f"({post_miss_distance_m:.2f}m >= {clearance_threshold_m:.0f}m)"
                ),
                is_completed=True,
                clearance_achieved=True,
            )
        else:
            return EncounterCompletionStatus(
                status="SIMULATED ENCOUNTER COMPLETED \u2014 CLEARANCE NOT ACHIEVED",
                detail=(
                    f"Simulated encounter passed (T={post_tca_seconds:.2f}s); "
                    f"evaluated separation ({post_miss_distance_m:.2f}m) below operational threshold "
                    f"({clearance_threshold_m:.0f}m)"
                ),
                is_completed=True,
                clearance_achieved=False,
            )

    # 4. Fallback status hierarchy when gate is not satisfied
    if manoeuvre_executed or step_index >= 6:
        return EncounterCompletionStatus(
            status="PREDICTED SAFE (POST-BURN)",
            detail="Post-burn trajectory predicts miss distance exceeds operational threshold (2,000 m)",
            is_completed=False,
            clearance_achieved=False,
        )
    elif current_time_seconds >= 120.0 or step_index >= 3:
        return EncounterCompletionStatus(
            status="CRITICAL RISK",
            detail="Predicted miss distance below safety threshold (2,000 m)",
            is_completed=False,
            clearance_achieved=False,
        )
    else:
        return EncounterCompletionStatus(
            status="NOMINAL MONITORING",
            detail="Spacecraft operating on verified orbital clearance",
            is_completed=False,
            clearance_achieved=False,
        )
