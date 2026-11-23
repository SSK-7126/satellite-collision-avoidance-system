"""
backend/decision_support/planner.py
===================================
Resource-Aware Autonomous Manoeuvre Planner.
Evaluates candidate avoidance manoeuvres for protected satellites:
- Enforces thrust, mass, Isp, and propellant reserve limits.
- Evaluates RTN directions: Radial (+R/-R), In-Track (+T/-T), and Normal (+N/-N).
- Re-propagates orbital motion to Time of Closest Approach.
- Computes propellant consumption via the Tsiolkovsky rocket equation.
- Generates ranked decision support proposals requiring human flight director approval.
"""

import math
import uuid
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List, Optional, Tuple, Sequence
import numpy as np

from .models import (
    ManoeuvreOption,
    ManoeuvreProposal,
    ProposalApprovalState,
    SpacecraftConstraints,
)
from backend.conjunction.models import ConjunctionCandidate
from backend.resources.models import SpacecraftHardwareRecord
from backend.resources.fuel_calculator import estimate_propellant_consumption
from D2.dynamics.orbit_propagator import propagate_orbit


def compute_rtn_basis(r_vec: np.ndarray, v_vec: np.ndarray) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """
    Compute orthonormal Radial-Transverse-Normal (RTN / RIC) unit vectors in ECI J2000.
    - Radial (R): along position vector r / |r|
    - Normal (N): along orbital angular momentum (r x v) / |r x v|
    - Transverse (T): completes right-handed triad (N x R), in-track direction
    """
    r_norm = float(np.linalg.norm(r_vec))
    if r_norm < 1e-6:
        raise ValueError("Degenerate position vector")
    R_hat = r_vec / r_norm

    h_vec = np.cross(r_vec, v_vec)
    h_norm = float(np.linalg.norm(h_vec))
    if h_norm < 1e-6:
        raise ValueError("Degenerate angular momentum vector")
    N_hat = h_vec / h_norm

    T_hat = np.cross(N_hat, R_hat)
    T_hat = T_hat / float(np.linalg.norm(T_hat))

    return R_hat, T_hat, N_hat


class ResourceAwareManoeuvrePlanner:
    """
    Autonomous decision-support planner evaluating resource-bounded avoidance manoeuvres.
    """
    def __init__(
        self,
        default_safety_threshold_m: float = 2000.0,
        default_lead_time_sec: float = 600.0, # 10 minutes prior to TCA
    ):
        self.default_safety_threshold_m = default_safety_threshold_m
        self.default_lead_time_sec = default_lead_time_sec

    def plan_avoidance_options(
        self,
        conjunction: ConjunctionCandidate,
        hardware: Optional[SpacecraftHardwareRecord] = None,
        constraints: Optional[SpacecraftConstraints] = None,
        delta_v_magnitudes: Optional[List[float]] = None,
    ) -> ManoeuvreProposal:
        """
        Generate and rank candidate avoidance manoeuvres subject to spacecraft constraints.
        """
        cons = constraints or SpacecraftConstraints()
        dv_list = delta_v_magnitudes or [1.0, 2.0, 3.0, 5.0]

        proposal_id = f"PROP-{uuid.uuid4().hex[:8].upper()}"
        proposal = ManoeuvreProposal(
            proposal_id=proposal_id,
            conjunction_id=f"CONJ-{conjunction.primary_id}-{conjunction.secondary_id}",
            primary_id=conjunction.primary_id,
            secondary_id=conjunction.secondary_id,
            nominal_miss_distance_m=conjunction.miss_distance_m,
            nominal_collision_probability=conjunction.collision_probability,
            safety_threshold_m=self.default_safety_threshold_m,
            approval_state=ProposalApprovalState.PROPOSED,
        )

        # Handle insufficient hardware data
        if hardware is None:
            # Cannot plan without physical spacecraft constraints
            return proposal

        r_sat = np.array(conjunction.primary_r_j2000_m, dtype=np.float64)
        v_sat = np.array(conjunction.primary_v_j2000_mps, dtype=np.float64)
        r_deb = np.array(conjunction.secondary_r_j2000_m, dtype=np.float64)
        v_deb = np.array(conjunction.secondary_v_j2000_mps, dtype=np.float64)

        try:
            R_hat, T_hat, N_hat = compute_rtn_basis(r_sat, v_sat)
        except Exception:
            return proposal

        # Spacecraft mass and propulsion specs
        m_wet = hardware.total_mass_kg
        prop_avail = hardware.current_propellant_kg
        isp = hardware.thrusters[0].isp_sec if hardware.thrusters else 220.0
        thrust_total = sum(t.thrust_n for t in hardware.thrusters) if hardware.thrusters else 10.0

        direction_map = {
            "-R": ("-R (Radial Inward)", -R_hat, [-1.0, 0.0, 0.0]),
            "+R": ("+R (Radial Outward)", R_hat, [1.0, 0.0, 0.0]),
            "+T": ("+T (In-Track Prograde)", T_hat, [0.0, 1.0, 0.0]),
            "-T": ("-T (In-Track Retrograde)", -T_hat, [0.0, -1.0, 0.0]),
            "+N": ("+N (Normal / Out-of-Plane)", N_hat, [0.0, 0.0, 1.0]),
            "-N": ("-N (Normal / Out-of-Plane)", -N_hat, [0.0, 0.0, -1.0]),
        }

        lead_time = min(self.default_lead_time_sec, max(60.0, conjunction.tca_seconds_from_epoch * 0.5))
        now_dt = datetime.now(timezone.utc)
        burn_epoch = now_dt + timedelta(seconds=max(0.0, conjunction.tca_seconds_from_epoch - lead_time))

        candidates: List[ManoeuvreOption] = []
        option_idx = 1

        for dir_key, (dir_label, unit_vec, vec_rtn) in direction_map.items():
            if dir_key not in cons.allowable_directions:
                continue

            for dv_mag in dv_list:
                if dv_mag > cons.max_delta_v_mps:
                    continue

                dv_eci = unit_vec * dv_mag

                # Propellant estimation via Tsiolkovsky equation
                prop_consumed = estimate_propellant_consumption(m_wet, dv_mag, isp)
                remaining_prop = max(0.0, prop_avail - prop_consumed)
                is_fuel_ok = (remaining_prop >= cons.min_propellant_reserve_kg) and (prop_consumed <= prop_avail)

                # Burn duration estimate: t_burn = (m_avg * dv) / thrust
                burn_dur = (m_wet * dv_mag) / max(0.1, thrust_total)

                # Numerical re-propagation to TCA
                # Initial post-burn state at burn lead time
                state_post_burn = np.hstack((r_sat, v_sat + dv_eci))
                prop_duration = lead_time
                _, states_mod = propagate_orbit(state_post_burn, duration=prop_duration, dt=min(10.0, prop_duration/10.0))
                r_sat_post_tca = states_mod[-1][:3]

                # Propagate debris unperturbed to TCA
                state_deb_0 = np.hstack((r_deb, v_deb))
                _, states_deb = propagate_orbit(state_deb_0, duration=prop_duration, dt=min(10.0, prop_duration/10.0))
                r_deb_post_tca = states_deb[-1][:3]
                v_deb_post_tca = states_deb[-1][3:]

                # Post-manoeuvre encounter geometry
                post_miss = float(np.linalg.norm(r_deb_post_tca - r_sat_post_tca))
                post_rel_speed = float(np.linalg.norm(v_deb_post_tca - (states_mod[-1][3:])))

                is_safe = (post_miss >= self.default_safety_threshold_m) and is_fuel_ok
                margin = post_miss - self.default_safety_threshold_m

                # Rank score: higher margin per fuel used
                rank_score = (margin / max(1.0, prop_consumed)) if is_safe else -1000.0

                opt = ManoeuvreOption(
                    option_id=f"OPT-{option_idx:02d}-{dir_key}",
                    direction_rtn=dir_label,
                    delta_v_magnitude_mps=round(dv_mag, 2),
                    delta_v_vector_rtn_mps=[round(c * dv_mag, 3) for c in vec_rtn],
                    delta_v_vector_j2000_mps=[round(c, 3) for c in dv_eci],
                    burn_epoch_utc=burn_epoch.isoformat(),
                    burn_lead_time_sec=round(lead_time, 1),
                    estimated_propellant_used_kg=round(prop_consumed, 3),
                    remaining_propellant_kg=round(remaining_prop, 2),
                    burn_duration_sec=round(burn_dur, 1),
                    is_fuel_feasible=is_fuel_ok,
                    post_miss_distance_m=round(post_miss, 2),
                    post_relative_speed_mps=round(post_rel_speed, 3),
                    is_safe=is_safe,
                    clearance_margin_m=round(margin, 2),
                    rank_score=round(rank_score, 2),
                )
                candidates.append(opt)
                option_idx += 1

        # Sort candidate options by rank score descending
        candidates.sort(key=lambda x: x.rank_score, reverse=True)
        proposal.candidate_options = candidates

        return proposal
