"""
backend/conjunction/alert_manager.py
====================================
Alert lifecycle management, deduplication, severity grading, and audit log.
"""

from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
import uuid

from .models import ConjunctionCandidate, ConjunctionAlert, AlertSeverity, AlertStatus


class AlertManager:
    """
    Manages active and historical conjunction alerts.
    """
    def __init__(
        self,
        critical_miss_distance_m: float = 2_000.0,
        warning_miss_distance_m: float = 10_000.0,
        critical_pc_threshold: float = 1e-4,
        warning_pc_threshold: float = 1e-6,
    ):
        self.critical_miss_distance_m = critical_miss_distance_m
        self.warning_miss_distance_m = warning_miss_distance_m
        self.critical_pc_threshold = critical_pc_threshold
        self.warning_pc_threshold = warning_pc_threshold

        self._alerts_by_id: Dict[str, ConjunctionAlert] = {}

    def classify_severity(self, cand: ConjunctionCandidate) -> AlertSeverity:
        """Classify severity using miss distance and Pc (if available)."""
        # Pc-based severity overrides distance if available
        if cand.collision_probability is not None:
            if cand.collision_probability >= self.critical_pc_threshold:
                return AlertSeverity.CRITICAL
            if cand.collision_probability >= self.warning_pc_threshold:
                return AlertSeverity.WARNING

        # Distance-based classification
        if cand.miss_distance_m <= self.critical_miss_distance_m:
            return AlertSeverity.CRITICAL
        elif cand.miss_distance_m <= self.warning_miss_distance_m:
            return AlertSeverity.WARNING
        else:
            return AlertSeverity.ADVISORY

    def create_or_update_alert(self, candidate: ConjunctionCandidate) -> ConjunctionAlert:
        """
        Create alert for candidate or update existing duplicate encounter alert.
        Deduplication key: pair (idA, idB) within 120s TCA window.
        """
        pair_key = tuple(sorted([candidate.primary_id, candidate.secondary_id]))
        severity = self.classify_severity(candidate)

        # Check existing alerts for deduplication
        for alert in self._alerts_by_id.values():
            if alert.status in [AlertStatus.ACTIVE, AlertStatus.ACKNOWLEDGED]:
                other_pair = tuple(sorted([alert.candidate.primary_id, alert.candidate.secondary_id]))
                if pair_key == other_pair:
                    # Same pair: check if TCA within 120 seconds
                    tca_diff = abs(alert.candidate.tca_seconds_from_epoch - candidate.tca_seconds_from_epoch)
                    if tca_diff <= 120.0:
                        # Update existing alert with closer approach
                        alert.candidate = candidate
                        alert.severity = severity
                        alert.updated_utc = datetime.now(timezone.utc).isoformat()
                        alert.history.append({
                            "action": "UPDATE_REFINED_STATE",
                            "miss_distance_m": candidate.miss_distance_m,
                            "timestamp_utc": alert.updated_utc,
                        })
                        return alert

        # Create new alert
        alert_id = f"ALT-{uuid.uuid4().hex[:8].upper()}"
        alert = ConjunctionAlert(
            alert_id=alert_id,
            candidate=candidate,
            severity=severity,
            status=AlertStatus.ACTIVE,
            history=[{
                "action": "CREATED",
                "severity": severity.value,
                "timestamp_utc": datetime.now(timezone.utc).isoformat(),
            }]
        )
        self._alerts_by_id[alert_id] = alert
        return alert

    def get_alert(self, alert_id: str) -> Optional[ConjunctionAlert]:
        return self._alerts_by_id.get(alert_id)

    def list_alerts(
        self,
        severity: Optional[AlertSeverity] = None,
        status: Optional[AlertStatus] = None
    ) -> List[ConjunctionAlert]:
        alerts = list(self._alerts_by_id.values())
        if severity:
            alerts = [a for a in alerts if a.severity == severity]
        if status:
            alerts = [a for a in alerts if a.status == status]
        return alerts

    def acknowledge_alert(self, alert_id: str, operator: str, notes: str = "") -> bool:
        alert = self.get_alert(alert_id)
        if alert:
            alert.acknowledge(operator=operator, notes=notes)
            return True
        return False

    def resolve_alert(self, alert_id: str, operator: str, notes: str = "") -> bool:
        alert = self.get_alert(alert_id)
        if alert:
            alert.resolve(operator=operator, notes=notes)
            return True
        return False
