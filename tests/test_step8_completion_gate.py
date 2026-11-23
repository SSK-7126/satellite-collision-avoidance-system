"""
tests/test_step8_completion_gate.py
===================================
Regression tests for the Step 8 completion gate.

Strict requirements verified:
1. Navigating directly to Step 8 before TCA does not show completion.
2. Reaching TCA without evaluating the post-encounter state does not show completion.
3. A valid evaluated separation above the threshold shows completion.
4. An evaluated separation below the threshold does not show completion.
5. Missing or invalid post-encounter data does not show completion.
"""

import math
import pytest
from backend.decision_support.encounter_gate import (
    evaluate_step8_completion_gate,
    EncounterCompletionStatus,
)


class TestStep8CompletionGate:
    """Verifies all 5 formal requirements for simulated encounter completion gate."""

    def test_requirement_1_navigating_directly_to_step8_before_tca_does_not_show_completion(self):
        """
        Requirement 1: Navigating directly to Step 8 before TCA must never show completion.
        Even if StepIndex == 8, if simulation time has not reached TCA, completion must be false.
        """
        # Case A: Jump to step 8 at T = 0.0s (no burn, before TCA)
        res_t0 = evaluate_step8_completion_gate(
            step_index=8,
            current_time_seconds=0.0,
            manoeuvre_executed=False,
            post_tca_seconds=903.03,
            post_miss_distance_m=2454.42,
            post_state_evaluated=False,
            clearance_threshold_m=2000.0,
        )
        assert not res_t0.is_completed, "Completion must be false before TCA"
        assert not res_t0.clearance_achieved
        assert res_t0.status != "SIMULATED ENCOUNTER COMPLETED — CLEARANCE ACHIEVED"
        assert res_t0.status == "PREDICTED SAFE (POST-BURN)"

        # Case B: In step 8 at T = 500.0s (post-burn, but still before TCA of 903.03s)
        res_t500 = evaluate_step8_completion_gate(
            step_index=8,
            current_time_seconds=500.0,
            manoeuvre_executed=True,
            post_tca_seconds=903.03,
            post_miss_distance_m=2454.42,
            post_state_evaluated=False,
            clearance_threshold_m=2000.0,
        )
        assert not res_t500.is_completed, "Step 8 before TCA must remain PREDICTED SAFE, not completed"
        assert res_t500.status == "PREDICTED SAFE (POST-BURN)"
        assert not res_t500.clearance_achieved

    def test_requirement_2_reaching_tca_without_evaluating_state_does_not_show_completion(self):
        """
        Requirement 2: Reaching or passing TCA without evaluating the post-encounter state
        (bPostEncounterStateEvaluated == False) must not show completion.
        """
        res = evaluate_step8_completion_gate(
            step_index=8,
            current_time_seconds=905.0,  # Passed TCA (903.03s)
            manoeuvre_executed=True,
            post_tca_seconds=903.03,
            post_miss_distance_m=2454.42,
            post_state_evaluated=False,  # Propagation / evaluation flag NOT yet set
            clearance_threshold_m=2000.0,
        )
        assert not res.is_completed, "Must not show completion without explicit state evaluation"
        assert not res.clearance_achieved
        assert res.status == "PREDICTED SAFE (POST-BURN)"
        assert "CLEARANCE ACHIEVED" not in res.status

    def test_requirement_3_valid_evaluated_separation_above_threshold_shows_completion(self):
        """
        Requirement 3: A valid evaluated separation above threshold (e.g. 2,454.42 m >= 2,000 m)
        shows 'SIMULATED ENCOUNTER COMPLETED — CLEARANCE ACHIEVED'.
        """
        res = evaluate_step8_completion_gate(
            step_index=8,
            current_time_seconds=905.0,  # Reached and passed TCA
            manoeuvre_executed=True,     # Burn applied
            post_tca_seconds=903.03,
            post_miss_distance_m=2454.42, # Valid evaluated miss > 2000 m
            post_state_evaluated=True,   # Evaluated flag set
            clearance_threshold_m=2000.0,
        )
        assert res.is_completed, "Must confirm completion when all conditions are satisfied"
        assert res.clearance_achieved, "Must confirm clearance achieved"
        assert res.status == "SIMULATED ENCOUNTER COMPLETED — CLEARANCE ACHIEVED"
        assert "2454.42m >= 2000m" in res.detail

    def test_requirement_4_evaluated_separation_below_threshold_does_not_show_clearance_achieved(self):
        """
        Requirement 4: An evaluated separation below threshold (e.g. 1,500 m < 2,000 m)
        does NOT show clearance achieved, but reports clearance failure / hazard status.
        """
        res = evaluate_step8_completion_gate(
            step_index=8,
            current_time_seconds=905.0,
            manoeuvre_executed=True,
            post_tca_seconds=903.03,
            post_miss_distance_m=1500.0,  # Below safety threshold of 2000 m
            post_state_evaluated=True,
            clearance_threshold_m=2000.0,
        )
        assert res.is_completed, "Encounter is completed"
        assert not res.clearance_achieved, "Clearance must NOT be achieved"
        assert res.status == "SIMULATED ENCOUNTER COMPLETED — CLEARANCE NOT ACHIEVED"
        assert "below operational threshold" in res.detail

    @pytest.mark.parametrize("invalid_miss", [None, float("nan"), float("inf"), -500.0, 0.0])
    def test_requirement_5_missing_or_invalid_miss_distance_does_not_show_completion(self, invalid_miss):
        """
        Requirement 5A: Missing, NaN, infinite, or non-positive miss distance data
        must never produce a completed status.
        """
        res = evaluate_step8_completion_gate(
            step_index=8,
            current_time_seconds=905.0,
            manoeuvre_executed=True,
            post_tca_seconds=903.03,
            post_miss_distance_m=invalid_miss,
            post_state_evaluated=True,
            clearance_threshold_m=2000.0,
        )
        assert not res.is_completed, f"Invalid miss distance ({invalid_miss}) must not produce completion"
        assert not res.clearance_achieved
        assert "CLEARANCE ACHIEVED" not in res.status

    @pytest.mark.parametrize("invalid_tca", [None, float("nan"), float("inf"), -1.0, 0.0])
    def test_requirement_5_missing_or_invalid_tca_does_not_show_completion(self, invalid_tca):
        """
        Requirement 5B: Missing, NaN, infinite, or non-positive TCA
        must never produce a completed status.
        """
        res = evaluate_step8_completion_gate(
            step_index=8,
            current_time_seconds=905.0,
            manoeuvre_executed=True,
            post_tca_seconds=invalid_tca,
            post_miss_distance_m=2454.42,
            post_state_evaluated=True,
            clearance_threshold_m=2000.0,
        )
        assert not res.is_completed, f"Invalid TCA ({invalid_tca}) must not produce completion"
        assert not res.clearance_achieved
        assert "CLEARANCE ACHIEVED" not in res.status
