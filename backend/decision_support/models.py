"""
backend/decision_support/models.py
==================================
Data models for resource-aware manoeuvre proposals and human-in-the-loop approval.
Strictly disclaims operational flight command: all outputs are decision-support simulations.
"""

from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from enum import Enum
from typing import Dict, Any, List, Optional, Union


class ProposalApprovalState(str, Enum):
    PROPOSED = "PROPOSED_AWAITING_HUMAN_APPROVAL"
    APPROVED = "APPROVED_BY_OPERATOR"
    REJECTED = "REJECTED_BY_OPERATOR"
    EXECUTED = "SIMULATION_EXECUTED"


@dataclass
class SpacecraftConstraints:
    """Operational and hardware boundaries for avoidance manoeuvre execution."""
    max_delta_v_mps: float = 5.0            # Maximum allowable delta-v magnitude
    min_propellant_reserve_kg: float = 5.0  # Safe fuel reserve that cannot be depleted
    max_burn_duration_sec: float = 120.0    # Continuous engine burn limit
    min_lead_time_seconds: float = 600.0    # Minimum reaction time before TCA
    allowable_directions: List[str] = field(default_factory=lambda: ["+R", "-R", "+T", "-T", "+N", "-N"])


@dataclass
class ManoeuvreOption:
    """Individual candidate manoeuvre evaluation."""
    option_id: str
    direction_rtn: str                      # e.g. "-R (Radial Inward)"
    delta_v_magnitude_mps: float
    delta_v_vector_rtn_mps: List[float]
    delta_v_vector_j2000_mps: List[float]
    burn_epoch_utc: str
    burn_lead_time_sec: float

    # Resource Accounting
    estimated_propellant_used_kg: float
    remaining_propellant_kg: float
    burn_duration_sec: float
    is_fuel_feasible: bool

    # Post-Manoeuvre Encounter Geometry
    post_miss_distance_m: float
    post_relative_speed_mps: float
    post_collision_probability: Optional[float] = None
    post_collision_log10_pc: Optional[float] = None
    post_pc_status: str = "PROBABILITY_UNAVAILABLE_MISSING_COVARIANCE"

    # Evaluation Score
    is_safe: bool = False                   # Miss distance > safety threshold
    clearance_margin_m: float = 0.0         # post_miss_distance - threshold
    rank_score: float = 0.0


@dataclass
class ManoeuvreProposal:
    """Package of evaluated manoeuvre candidates requiring human flight-director signoff."""
    proposal_id: str
    conjunction_id: str
    primary_id: str
    secondary_id: str
    created_utc: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    nominal_miss_distance_m: float = 0.0
    nominal_collision_probability: Optional[float] = None
    safety_threshold_m: float = 2000.0

    candidate_options: List[ManoeuvreOption] = field(default_factory=list)
    selected_option_id: Optional[str] = None
    approval_state: ProposalApprovalState = ProposalApprovalState.PROPOSED
    approved_by: Optional[str] = None
    approval_timestamp_utc: Optional[str] = None
    operator_notes: Optional[str] = None

    operational_disclaimer: str = (
        "DECISION-SUPPORT SIMULATION ONLY. Human operator verification required. "
        "Updates local simulation manoeuvre proposals only. "
        "No real spacecraft command, control, uplink, or execution interface exists."
    )

    def approve(self, option_id: str, operator_id: str, notes: str = ""):
        self.selected_option_id = option_id
        self.approval_state = ProposalApprovalState.APPROVED
        self.approved_by = operator_id
        self.approval_timestamp_utc = datetime.now(timezone.utc).isoformat()
        self.operator_notes = notes

    def reject(self, operator_id: str, notes: str = ""):
        self.approval_state = ProposalApprovalState.REJECTED
        self.approved_by = operator_id
        self.approval_timestamp_utc = datetime.now(timezone.utc).isoformat()
        self.operator_notes = notes

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)
