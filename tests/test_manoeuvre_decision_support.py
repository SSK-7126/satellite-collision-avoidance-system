"""
tests/test_manoeuvre_decision_support.py
========================================
Tests for Resource-Aware Manoeuvre Decision Support (Phase 8).
Verifies:
- RTN triad computation and orthonormality in ECI J2000
- Generation of candidate manoeuvres across RTN directions
- Propellant consumption accounting and remaining reserve validation
- Maximum delta-v and minimum fuel reserve constraint enforcement
- Post-burn orbital re-propagation and miss distance improvement
- Human flight director approval workflow (approve/reject transitions)
- Graceful handling of insufficient hardware/conjunction inputs
"""

import numpy as np
import pytest

from backend.conjunction.models import ConjunctionCandidate
from backend.resources.models import (
    SpacecraftHardwareRecord,
    ThrusterSpecification,
    ProvenanceType,
)
from backend.decision_support.models import (
    SpacecraftConstraints,
    ProposalApprovalState,
)
from backend.decision_support.planner import (
    ResourceAwareManoeuvrePlanner,
    compute_rtn_basis,
)


def test_rtn_basis_orthonormality():
    """Verify Radial-Transverse-Normal triad is orthonormal and right-handed."""
    r_vec = np.array([7_000_000.0, 0.0, 0.0])
    v_vec = np.array([0.0, 7500.0, 0.0])

    R_hat, T_hat, N_hat = compute_rtn_basis(r_vec, v_vec)

    # Unit lengths
    assert pytest.approx(np.linalg.norm(R_hat)) == 1.0
    assert pytest.approx(np.linalg.norm(T_hat)) == 1.0
    assert pytest.approx(np.linalg.norm(N_hat)) == 1.0

    # Mutual orthogonality
    assert pytest.approx(np.dot(R_hat, T_hat), abs=1e-12) == 0.0
    assert pytest.approx(np.dot(R_hat, N_hat), abs=1e-12) == 0.0
    assert pytest.approx(np.dot(T_hat, N_hat), abs=1e-12) == 0.0

    # Right-handedness: R x T == N
    assert np.allclose(np.cross(R_hat, T_hat), N_hat, atol=1e-12)


def test_manoeuvre_options_generation_and_clearance():
    """Verify autonomous generation of avoidance candidates and post-burn clearance."""
    planner = ResourceAwareManoeuvrePlanner(default_safety_threshold_m=2000.0)

    # Conjunction with 800m miss distance
    conj = ConjunctionCandidate(
        primary_id="44804",
        secondary_id="22285",
        primary_name="CARTOSAT-3",
        secondary_name="SL-16 R/B",
        tca_seconds_from_epoch=500.0,
        tca_epoch_utc="2026-11-23T12:08:20Z",
        miss_distance_m=800.0,
        relative_speed_mps=14.0,
        primary_r_j2000_m=[7_000_000.0, 0.0, 0.0],
        primary_v_j2000_mps=[0.0, 7546.0, 0.0],
        secondary_r_j2000_m=[7_000_000.0, 800.0, 0.0],
        secondary_v_j2000_mps=[0.0, 7546.0, 14.0],
    )

    hardware = SpacecraftHardwareRecord(
        object_id="44804",
        owner_operator="ISRO",
        dry_mass_kg=1100.0,
        initial_propellant_kg=50.0,
        current_propellant_kg=50.0,
        propellant_type="HYDRAZINE",
        thrusters=[ThrusterSpecification(thruster_type="RCS", thrust_n=10.0, isp_sec=220.0)],
    )

    constraints = SpacecraftConstraints(
        max_delta_v_mps=5.0,
        min_propellant_reserve_kg=10.0,
    )

    proposal = planner.plan_avoidance_options(
        conjunction=conj,
        hardware=hardware,
        constraints=constraints,
        delta_v_magnitudes=[1.0, 2.0, 3.0],
    )

    assert proposal.primary_id == "44804"
    assert len(proposal.candidate_options) > 0
    assert proposal.approval_state == ProposalApprovalState.PROPOSED

    # Find candidate options that achieve safety
    safe_options = [opt for opt in proposal.candidate_options if opt.is_safe]
    assert len(safe_options) > 0

    best_opt = safe_options[0]
    assert best_opt.post_miss_distance_m >= 2000.0
    assert best_opt.is_fuel_feasible is True
    assert best_opt.estimated_propellant_used_kg > 0.0
    assert best_opt.remaining_propellant_kg < 50.0
    assert best_opt.remaining_propellant_kg >= constraints.min_propellant_reserve_kg


def test_insufficient_hardware_graceful_handling():
    """Verify planner handles missing spacecraft hardware record cleanly without crashing."""
    planner = ResourceAwareManoeuvrePlanner()
    conj = ConjunctionCandidate(
        primary_id="UNKNOWN", secondary_id="DEB", primary_name="UNK", secondary_name="DEB",
        tca_seconds_from_epoch=300.0, tca_epoch_utc="", miss_distance_m=500.0, relative_speed_mps=10.0,
        primary_r_j2000_m=[7000000.0, 0, 0], primary_v_j2000_mps=[0, 7500, 0],
        secondary_r_j2000_m=[7000500.0, 0, 0], secondary_v_j2000_mps=[0, 7500, 10],
    )

    proposal = planner.plan_avoidance_options(conjunction=conj, hardware=None)
    assert len(proposal.candidate_options) == 0
    assert proposal.approval_state == ProposalApprovalState.PROPOSED


def test_human_approval_workflow():
    """Verify human flight director signoff transitions and audit metadata."""
    proposal = ResourceAwareManoeuvrePlanner().plan_avoidance_options(
        conjunction=ConjunctionCandidate(
            primary_id="SAT", secondary_id="DEB", primary_name="SAT", secondary_name="DEB",
            tca_seconds_from_epoch=500.0, tca_epoch_utc="", miss_distance_m=500.0, relative_speed_mps=10.0,
            primary_r_j2000_m=[7000000.0, 0, 0], primary_v_j2000_mps=[0, 7500, 0],
            secondary_r_j2000_m=[7000500.0, 0, 0], secondary_v_j2000_mps=[0, 7500, 10],
        ),
        hardware=SpacecraftHardwareRecord(object_id="SAT", dry_mass_kg=500.0, current_propellant_kg=20.0),
    )

    assert proposal.approval_state == ProposalApprovalState.PROPOSED

    # Operator approves option 1
    proposal.approve(
        option_id="OPT-01--R",
        operator_id="CHIEF_FLIGHT_DIRECTOR",
        notes="Approved 3.0 m/s radial inward burn",
    )

    assert proposal.approval_state == ProposalApprovalState.APPROVED
    assert proposal.approved_by == "CHIEF_FLIGHT_DIRECTOR"
    assert proposal.selected_option_id == "OPT-01--R"
    assert proposal.approval_timestamp_utc is not None
