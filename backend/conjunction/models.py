"""
backend/conjunction/models.py
=============================
Data models for conjunction assessment, alerts, and CDMs.
Strictly distinguishes coarse screening from validated assessment, and
ensures missing covariance is never treated as zero uncertainty.
"""

from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from enum import Enum
from typing import Dict, Any, List, Optional, Union


class AlertSeverity(str, Enum):
    CRITICAL = "CRITICAL"    # Miss dist < 2,000 m OR Pc > 1e-4
    WARNING = "WARNING"      # Miss dist < 10,000 m OR Pc > 1e-6
    ADVISORY = "ADVISORY"    # Miss dist < 50,000 m (screening horizon)
    SAFE = "SAFE"            # Verified clear


class AlertStatus(str, Enum):
    ACTIVE = "ACTIVE"
    ACKNOWLEDGED = "ACKNOWLEDGED"
    RESOLVED = "RESOLVED"
    DISMISSED = "DISMISSED"


class AssessmentQuality(str, Enum):
    COARSE_SCREENING = "COARSE_SCREENING"             # Spherical/orbital geometry screening only
    REFINE_TCA = "REFINE_TCA"                         # Numerical TCA minimum found, no covariance
    VALIDATED_COVARIANCE = "VALIDATED_COVARIANCE"     # Validated 2D Foster Pc calculation
    PROBABILITY_UNAVAILABLE = "PROBABILITY_UNAVAILABLE" # Missing covariance; Pc NOT calculable


@dataclass
class ConjunctionCandidate:
    """Represents a potential conjunction detected during screening."""
    primary_id: str
    secondary_id: str
    primary_name: str
    secondary_name: str
    tca_seconds_from_epoch: float
    tca_epoch_utc: str
    miss_distance_m: float
    relative_speed_mps: float
    primary_r_j2000_m: List[float]
    primary_v_j2000_mps: List[float]
    secondary_r_j2000_m: List[float]
    secondary_v_j2000_mps: List[float]

    # Uncertainty & Probability (Never fabricated)
    collision_probability: Optional[float] = None
    collision_log10_pc: Optional[float] = None
    pc_status: str = "PROBABILITY_UNAVAILABLE_MISSING_COVARIANCE"
    assessment_quality: AssessmentQuality = AssessmentQuality.COARSE_SCREENING
    provenance: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ConjunctionAlert:
    """Managed operational alert with lifecycle history and audit trail."""
    alert_id: str
    candidate: ConjunctionCandidate
    severity: AlertSeverity
    status: AlertStatus = AlertStatus.ACTIVE
    created_utc: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_utc: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    acknowledged_by: Optional[str] = None
    acknowledgement_notes: Optional[str] = None
    history: List[Dict[str, Any]] = field(default_factory=list)

    def acknowledge(self, operator: str, notes: str = ""):
        self.status = AlertStatus.ACKNOWLEDGED
        self.acknowledged_by = operator
        self.acknowledgement_notes = notes
        now_iso = datetime.now(timezone.utc).isoformat()
        self.updated_utc = now_iso
        self.history.append({
            "action": "ACKNOWLEDGE",
            "operator": operator,
            "timestamp_utc": now_iso,
            "notes": notes,
        })

    def resolve(self, operator: str, notes: str = ""):
        self.status = AlertStatus.RESOLVED
        now_iso = datetime.now(timezone.utc).isoformat()
        self.updated_utc = now_iso
        self.history.append({
            "action": "RESOLVE",
            "operator": operator,
            "timestamp_utc": now_iso,
            "notes": notes,
        })

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        return d


@dataclass
class CDMRecord:
    """CCSDS Conjunction Data Message (CDM) standardized representation."""
    message_id: str
    originator: str
    creation_date: str
    tca_utc: str
    miss_distance_m: float
    relative_speed_mps: float
    primary_id: str
    primary_name: str
    secondary_id: str
    secondary_name: str
    collision_probability: Optional[float] = None
    hard_body_radius_m: Optional[float] = None
    primary_covariance_6x6: Optional[List[List[float]]] = None
    secondary_covariance_6x6: Optional[List[List[float]]] = None
    provenance: Dict[str, Any] = field(default_factory=dict)
