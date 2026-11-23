"""
backend/conjunction/screener.py
===============================
Scalable coarse conjunction screening across multiple orbital objects.
Features:
- Apogee / Perigee orbital envelope pre-filtering ($O(1)$ shell culling).
- Time-sampled Euclidean screening over shared observation horizon.
- Local TCA refinement via parabolic interpolation.
- Rigorous Pc calculation: calls Foster 2D only if covariance is supplied;
  otherwise explicitly sets PROBABILITY_UNAVAILABLE (never fabricate 0.0).
"""

import math
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List, Optional, Tuple, Sequence
import numpy as np

from .models import (
    ConjunctionCandidate,
    AssessmentQuality,
)
from backend.catalogue.models import CatalogueObject
from backend.propagation.multi_object_manager import MultiObjectPropagator, TrajectorySample
from D2.uncertainty.collision_probability import (
    calculate_collision_probability,
    project_to_encounter_plane,
)
from D2.uncertainty.covariance import validate_covariance


class CoarseScreener:
    """
    Screens pairs of space objects for close approaches.
    """
    def __init__(
        self,
        screening_distance_m: float = 50_000.0,  # 50 km default coarse screening sphere
        time_step_sec: float = 10.0,
    ):
        self.screening_distance_m = screening_distance_m
        self.time_step_sec = time_step_sec

    @staticmethod
    def orbital_shells_overlap(
        obj_a: CatalogueObject,
        obj_b: CatalogueObject,
        radial_margin_km: float = 60.0
    ) -> bool:
        """
        O(1) apogee-perigee pre-filter:
        If perigee(A) - margin > apogee(B) or perigee(B) - margin > apogee(A),
        the orbits can never intersect.
        """
        if not obj_a.elements or not obj_b.elements:
            return True  # Cannot exclude without orbital elements

        peri_a = obj_a.elements.periapsis_km - radial_margin_km
        apo_a = obj_a.elements.apoapsis_km + radial_margin_km
        peri_b = obj_b.elements.periapsis_km - radial_margin_km
        apo_b = obj_b.elements.apoapsis_km + radial_margin_km

        if peri_a > apo_b or peri_b > apo_a:
            return False
        return True

    def screen_trajectories(
        self,
        obj_a: CatalogueObject,
        samples_a: List[TrajectorySample],
        obj_b: CatalogueObject,
        samples_b: List[TrajectorySample],
        epoch_start: datetime,
    ) -> List[ConjunctionCandidate]:
        """
        Screen two trajectory sample sets and find closest approach candidates.
        """
        candidates = []
        n_samples = min(len(samples_a), len(samples_b))
        if n_samples < 2:
            return candidates

        min_dist = float("inf")
        min_idx = -1

        for i in range(n_samples):
            r_a = np.array(samples_a[i].r_j2000_m, dtype=np.float64)
            r_b = np.array(samples_b[i].r_j2000_m, dtype=np.float64)
            dist = float(np.linalg.norm(r_b - r_a))

            if dist < min_dist:
                min_dist = dist
                min_idx = i

        # If closest approach is within coarse screening distance
        if min_dist <= self.screening_distance_m and min_idx != -1:
            # Refine TCA using 3-point parabolic interpolation around min_idx
            tca_offset = samples_a[min_idx].time_offset_sec
            refined_dist = min_dist

            if 0 < min_idx < n_samples - 1:
                d_prev = np.linalg.norm(np.array(samples_b[min_idx-1].r_j2000_m) - np.array(samples_a[min_idx-1].r_j2000_m))
                d_curr = min_dist
                d_next = np.linalg.norm(np.array(samples_b[min_idx+1].r_j2000_m) - np.array(samples_a[min_idx+1].r_j2000_m))

                # Parabolic peak/valley offset: delta_step = -0.5 * (d_next - d_prev) / (d_next - 2*d_curr + d_prev)
                denom = (d_next - 2.0 * d_curr + d_prev)
                if abs(denom) > 1e-12:
                    dt_step = -0.5 * (d_next - d_prev) / denom
                    dt_step = max(-1.0, min(1.0, dt_step))
                    tca_offset += dt_step * self.time_step_sec
                    refined_dist = max(0.0, d_curr - 0.25 * ((d_next - d_prev) ** 2) / denom)

            # Compute relative speed at min_idx
            v_a = np.array(samples_a[min_idx].v_j2000_mps, dtype=np.float64)
            v_b = np.array(samples_b[min_idx].v_j2000_mps, dtype=np.float64)
            rel_speed = float(np.linalg.norm(v_b - v_a))

            tca_epoch = epoch_start + timedelta(seconds=tca_offset)

            cand = ConjunctionCandidate(
                primary_id=str(obj_a.object_id),
                secondary_id=str(obj_b.object_id),
                primary_name=obj_a.name,
                secondary_name=obj_b.name,
                tca_seconds_from_epoch=round(tca_offset, 2),
                tca_epoch_utc=tca_epoch.isoformat(),
                miss_distance_m=round(refined_dist, 2),
                relative_speed_mps=round(rel_speed, 3),
                primary_r_j2000_m=samples_a[min_idx].r_j2000_m,
                primary_v_j2000_mps=samples_a[min_idx].v_j2000_mps,
                secondary_r_j2000_m=samples_b[min_idx].r_j2000_m,
                secondary_v_j2000_mps=samples_b[min_idx].v_j2000_mps,
                collision_probability=None,
                collision_log10_pc=None,
                pc_status="PROBABILITY_UNAVAILABLE_MISSING_COVARIANCE",
                assessment_quality=AssessmentQuality.REFINE_TCA,
                provenance={
                    "screened_at_utc": datetime.now(timezone.utc).isoformat(),
                    "screening_sphere_m": self.screening_distance_m,
                }
            )
            candidates.append(cand)

        return candidates


def calculate_conjunction_risk(
    candidate: ConjunctionCandidate,
    primary_cov_6x6: Optional[Sequence[Sequence[float]]] = None,
    secondary_cov_6x6: Optional[Sequence[Sequence[float]]] = None,
    hard_body_radius_m: float = 10.0,
) -> ConjunctionCandidate:
    """
    Evaluate collision probability (Pc) with strict uncertainty rules.
    If either covariance is missing, Pc is marked UNAVAILABLE (never fabricated).
    """
    if primary_cov_6x6 is None or secondary_cov_6x6 is None:
        candidate.collision_probability = None
        candidate.collision_log10_pc = None
        candidate.pc_status = "PROBABILITY_UNAVAILABLE_MISSING_COVARIANCE"
        candidate.assessment_quality = AssessmentQuality.PROBABILITY_UNAVAILABLE
        return candidate

    try:
        # Validate covariances
        p_cov = validate_covariance(primary_cov_6x6, "Primary Covariance")
        s_cov = validate_covariance(secondary_cov_6x6, "Secondary Covariance")

        # Combine under independent error assumption
        cov_combined_6x6 = p_cov + s_cov

        r_rel = np.array(candidate.secondary_r_j2000_m) - np.array(candidate.primary_r_j2000_m)
        v_rel = np.array(candidate.secondary_v_j2000_mps) - np.array(candidate.primary_v_j2000_mps)

        # Foster 2D encounter-plane integration
        res = calculate_collision_probability(
            r_rel_tca=r_rel,
            v_rel_tca=v_rel,
            cov_rel_tca=cov_combined_6x6,
            hard_body_radius=hard_body_radius_m,
        )

        if res.get("is_valid", False) and res.get("pc") is not None:
            pc_float = float(res["pc"])
            candidate.collision_probability = pc_float
            candidate.collision_log10_pc = res.get("log10_pc")
            candidate.pc_status = "NUMERICAL_OK" if pc_float > 1e-30 else "NUMERICAL_UNDERFLOW"
            candidate.assessment_quality = AssessmentQuality.VALIDATED_COVARIANCE
        else:
            candidate.collision_probability = None
            candidate.collision_log10_pc = None
            candidate.pc_status = res.get("status", "PROBABILITY_UNAVAILABLE")
            candidate.assessment_quality = AssessmentQuality.PROBABILITY_UNAVAILABLE

    except Exception as e:
        candidate.collision_probability = None
        candidate.collision_log10_pc = None
        candidate.pc_status = f"CALCULATION_ERROR: {str(e)}"
        candidate.assessment_quality = AssessmentQuality.PROBABILITY_UNAVAILABLE

    return candidate
