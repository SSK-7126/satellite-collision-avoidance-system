"""
tests/test_conjunction_screening.py
===================================
Tests for Multi-Object Conjunction Screening and Alerts (Phase 5).
Verifies:
- Apogee/perigee orbital envelope pre-filtering
- Coarse screening distance and time horizon filtering
- Local TCA refinement and relative encounter velocity calculation
- Strict uncertainty and Pc calculation rules:
  * Missing covariance -> PROBABILITY_UNAVAILABLE (never fabricated Pc=0)
  * Valid covariance -> 2D Foster encounter plane integration
- Alert severity grading (CRITICAL, WARNING, ADVISORY)
- Alert deduplication and lifecycle transitions (ACTIVE -> ACKNOWLEDGED -> RESOLVED)
- CCSDS Conjunction Data Message (CDM) parsing
"""

import numpy as np
import pytest
from datetime import datetime, timezone

from backend.catalogue.models import CatalogueObject, OrbitalElements
from backend.propagation.multi_object_manager import TrajectorySample
from backend.conjunction.models import (
    ConjunctionCandidate,
    AlertSeverity,
    AlertStatus,
    AssessmentQuality,
)
from backend.conjunction.screener import CoarseScreener, calculate_conjunction_risk
from backend.conjunction.alert_manager import AlertManager
from backend.conjunction.cdm_parser import parse_cdm_json
from D2.uncertainty.covariance import create_diagonal_covariance


def create_dummy_object(oid: str, name: str, peri_km: float, apo_km: float) -> CatalogueObject:
    elems = OrbitalElements(
        semi_major_axis_km=(peri_km + apo_km) / 2.0,
        eccentricity=(apo_km - peri_km) / (peri_km + apo_km),
        inclination_deg=51.6,
        raan_deg=100.0,
        arg_perigee_deg=45.0,
        mean_anomaly_deg=0.0,
        mean_motion_rev_per_day=15.0,
        period_minutes=90.0,
        apoapsis_km=apo_km,
        periapsis_km=peri_km,
    )
    return CatalogueObject(
        object_id=oid,
        name=name,
        epoch_utc="2026-11-23T12:00:00Z",
        source="TEST",
        format="TEST",
        retrieval_time_utc="2026-11-23T12:00:00Z",
        raw_record="",
        elements=elems,
    )


def test_orbital_shell_overlap_filter():
    """Verify O(1) apogee/perigee exclusion filter."""
    leo_obj = create_dummy_object("1", "LEO_SAT", 6700.0, 6900.0)
    meo_obj = create_dummy_object("2", "MEO_SAT", 12000.0, 13000.0)
    leo_overlapping = create_dummy_object("3", "LEO_NEAR", 6850.0, 7100.0)

    # LEO vs MEO cannot intersect
    assert CoarseScreener.orbital_shells_overlap(leo_obj, meo_obj) is False
    # LEO vs LEO overlapping can intersect
    assert CoarseScreener.orbital_shells_overlap(leo_obj, leo_overlapping) is True


def test_coarse_screening_and_tca_refinement():
    """Verify coarse time-series screening detects close approach and refines TCA."""
    screener = CoarseScreener(screening_distance_m=50_000.0, time_step_sec=10.0)
    obj_a = create_dummy_object("A", "SAT_A", 6800.0, 7000.0)
    obj_b = create_dummy_object("B", "SAT_B", 6800.0, 7000.0)

    start_dt = datetime(2026, 11, 23, 12, 0, 0, tzinfo=timezone.utc)

    # Create trajectory with a close pass at t = 100s:
    # SAT_A at [7000km, 0, 0] with vel [0, 7.5km/s, 0]
    # SAT_B passes at [7000km + 1500m, 0, 0]
    samples_a = []
    samples_b = []
    for step in range(21):  # 0 to 200s in 10s steps
        t = step * 10.0
        # Sat A moves along Y
        r_a = [7_000_000.0, (t - 100.0) * 7500.0, 0.0]
        v_a = [0.0, 7500.0, 0.0]
        # Sat B moves along Z with 1500m X-offset
        r_b = [7_000_000.0 + 1500.0, 0.0, (t - 100.0) * 7500.0]
        v_b = [0.0, 0.0, 7500.0]

        samples_a.append(TrajectorySample(t, "", r_a, v_a, [0, 0, 0]))
        samples_b.append(TrajectorySample(t, "", r_b, v_b, [0, 0, 0]))

    candidates = screener.screen_trajectories(obj_a, samples_a, obj_b, samples_b, start_dt)
    assert len(candidates) == 1
    cand = candidates[0]
    assert cand.primary_id == "A"
    assert cand.secondary_id == "B"
    assert pytest.approx(cand.tca_seconds_from_epoch, abs=1.0) == 100.0
    assert pytest.approx(cand.miss_distance_m, abs=50.0) == 1500.0
    assert cand.pc_status == "PROBABILITY_UNAVAILABLE_MISSING_COVARIANCE"


def test_strict_missing_covariance_rules():
    """Verify missing covariance never fabricates zero uncertainty or Pc."""
    cand = ConjunctionCandidate(
        primary_id="1", secondary_id="2", primary_name="SAT", secondary_name="DEB",
        tca_seconds_from_epoch=100.0, tca_epoch_utc="", miss_distance_m=1200.0, relative_speed_mps=12.0,
        primary_r_j2000_m=[7_000_000.0, 0.0, 0.0], primary_v_j2000_mps=[0.0, 7500.0, 0.0],
        secondary_r_j2000_m=[7_000_000.0, 1200.0, 0.0], secondary_v_j2000_mps=[0.0, 7500.0, 12.0],
    )

    # Missing covariance
    res = calculate_conjunction_risk(cand, primary_cov_6x6=None, secondary_cov_6x6=None)
    assert res.collision_probability is None
    assert res.collision_log10_pc is None
    assert res.pc_status == "PROBABILITY_UNAVAILABLE_MISSING_COVARIANCE"
    assert res.assessment_quality == AssessmentQuality.PROBABILITY_UNAVAILABLE


def test_validated_covariance_pc_calculation():
    """Verify that when 6x6 covariance is supplied, Foster 2D Pc is calculated."""
    cand = ConjunctionCandidate(
        primary_id="1", secondary_id="2", primary_name="SAT", secondary_name="DEB",
        tca_seconds_from_epoch=100.0, tca_epoch_utc="", miss_distance_m=50.0, relative_speed_mps=14.0,
        primary_r_j2000_m=[7_000_000.0, 0.0, 0.0], primary_v_j2000_mps=[0.0, 7500.0, 0.0],
        secondary_r_j2000_m=[7_000_050.0, 0.0, 0.0], secondary_v_j2000_mps=[0.0, 7500.0, 14.0],
    )

    # Provide valid 6x6 diagonal covariance (pos variance: (50m)^2, vel variance: (0.1m/s)^2)
    cov1 = create_diagonal_covariance(pos_std_m=[50.0, 50.0, 50.0], vel_std_mps=[0.1, 0.1, 0.1])
    cov2 = create_diagonal_covariance(pos_std_m=[50.0, 50.0, 50.0], vel_std_mps=[0.1, 0.1, 0.1])

    res = calculate_conjunction_risk(cand, primary_cov_6x6=cov1, secondary_cov_6x6=cov2, hard_body_radius_m=20.0)
    assert res.collision_probability is not None
    assert 0.0 < res.collision_probability <= 1.0
    assert res.collision_log10_pc is not None
    assert res.pc_status in ["NUMERICAL_OK", "NUMERICAL_UNDERFLOW"]
    assert res.assessment_quality == AssessmentQuality.VALIDATED_COVARIANCE


def test_alert_severity_and_lifecycle():
    """Verify alert severity grading, deduplication, and operator lifecycle."""
    mgr = AlertManager()
    cand_critical = ConjunctionCandidate(
        primary_id="SAT1", secondary_id="DEB1", primary_name="SAT1", secondary_name="DEB1",
        tca_seconds_from_epoch=500.0, tca_epoch_utc="", miss_distance_m=850.0, relative_speed_mps=10.0,
        primary_r_j2000_m=[0, 0, 0], primary_v_j2000_mps=[0, 0, 0],
        secondary_r_j2000_m=[0, 0, 0], secondary_v_j2000_mps=[0, 0, 0],
    )

    # 1. Critical alert creation
    alert = mgr.create_or_update_alert(cand_critical)
    assert alert.severity == AlertSeverity.CRITICAL
    assert alert.status == AlertStatus.ACTIVE

    # 2. Operator acknowledgement
    assert mgr.acknowledge_alert(alert.alert_id, operator="FLIGHT_DIRECTOR_01", notes="Reviewing avoidance burn")
    assert alert.status == AlertStatus.ACKNOWLEDGED
    assert alert.acknowledged_by == "FLIGHT_DIRECTOR_01"

    # 3. Deduplication: refined candidate with closer distance
    cand_refined = ConjunctionCandidate(
        primary_id="SAT1", secondary_id="DEB1", primary_name="SAT1", secondary_name="DEB1",
        tca_seconds_from_epoch=505.0, tca_epoch_utc="", miss_distance_m=810.0, relative_speed_mps=10.0,
        primary_r_j2000_m=[0, 0, 0], primary_v_j2000_mps=[0, 0, 0],
        secondary_r_j2000_m=[0, 0, 0], secondary_v_j2000_mps=[0, 0, 0],
    )
    alert2 = mgr.create_or_update_alert(cand_refined)
    assert alert2.alert_id == alert.alert_id  # Deduplicated into existing alert
    assert alert2.candidate.miss_distance_m == 810.0

    # 4. Operator resolution
    assert mgr.resolve_alert(alert.alert_id, operator="FLIGHT_DIRECTOR_01", notes="Manoeuvre approved and executed")
    assert alert.status == AlertStatus.RESOLVED


def test_cdm_parser_json():
    """Verify CCSDS Conjunction Data Message parsing."""
    cdm_sample = {
        "header": {"MESSAGE_ID": "CDM-2026-001", "ORIGINATOR": "18SDS", "CREATION_DATE": "2026-11-23T10:00:00Z"},
        "body": {
            "relative_metadata": {"TCA": "2026-11-23T15:30:00Z", "MISS_DISTANCE": 1420.5, "RELATIVE_SPEED": 13.8, "COLLISION_PROBABILITY": 2.5e-5},
            "segment1": {"metadata": {"OBJECT_DESIGNATOR": "44804", "OBJECT_NAME": "CARTOSAT-3"}},
            "segment2": {"metadata": {"OBJECT_DESIGNATOR": "22285", "OBJECT_NAME": "SL-16 R/B"}}
        }
    }
    cdm = parse_cdm_json(cdm_sample)
    assert cdm.message_id == "CDM-2026-001"
    assert cdm.originator == "18SDS"
    assert cdm.primary_id == "44804"
    assert cdm.primary_name == "CARTOSAT-3"
    assert cdm.secondary_id == "22285"
    assert cdm.miss_distance_m == 1420.5
    assert cdm.collision_probability == 2.5e-5
