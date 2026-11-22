"""
MLService/inference_service.py
==============================
Machine Learning / Decision Support Inference Service for Collision Avoidance.
Strictly following Section 10 of the Satellite Anti-Collision Technical Guide.

Core Design:
1. Versioned Request/Response Interface:
   - Ingests validated observations or estimated features.
   - Outputs structured predictions and manoeuvre proposals.
2. Interface Safeguards (Section 10.3):
   - Rejects stale messages (monotonic timestamp enforcement).
   - Rejects wrong-frame payloads (ECEF or unrecognized frames).
   - Rejects malformed or NaN/infinite inputs.
3. Transparent Baseline Model:
   - When no trained weights or empirical datasets exist, implements a clearly
     labeled deterministic rule-based BASELINE model (`baseline_rule_based_v1.0`).
   - Zero fabrication of trained model metrics or false AI claims.
4. Untrusted Proposal Validation Gate:
   - All proposed manoeuvres are marked UNVALIDATED upon generation.
   - Proposals MUST pass deterministic astrodynamic validation and physical
     constraint filtering before simulated execution.
"""

from typing import Dict, Any, Optional, Tuple
import numpy as np

from MLService.schemas import (
    MLInferenceRequest,
    MLInferenceResponse,
    PredictionOutput,
    RecommendedAction,
    CURRENT_SCHEMA_VERSION,
)
from D2.conjunction.tca import calculate_relative_state, calculate_linear_cpa
from D2.uncertainty.collision_probability import calculate_collision_probability
from D2.manoeuvres.manoeuvre_model import ManoeuvreConstraints


class MLInferenceService:
    """
    Python ML inference and risk classification service.
    """
    def __init__(
        self,
        model_version: str = "baseline_rule_based_v1.0",
        critical_miss_distance_m: float = 2000.0,
        critical_pc_threshold: float = 1e-6
    ):
        self.model_version = model_version
        self.critical_miss_distance_m = critical_miss_distance_m
        self.critical_pc_threshold = critical_pc_threshold
        # Track last processed timestamp per scenario for stale message detection
        self.last_seen_timestamps: Dict[str, float] = {}

    def process_request(self, raw_payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process an incoming ML inference request with strict interface safeguards.
        (Technical Guide Section 10.3)
        """
        # 1. Parse and validate schema
        try:
            req = MLInferenceRequest.from_dict(raw_payload)
            req.validate()
        except Exception as e:
            return {
                "schema_version": CURRENT_SCHEMA_VERSION,
                "error": "MALFORMED_PAYLOAD",
                "message": str(e),
                "is_valid": False,
            }

        # 2. Check for finite numbers
        r1 = np.asarray(req.primary.position_m, dtype=np.float64)
        v1 = np.asarray(req.primary.velocity_mps, dtype=np.float64)
        r2 = np.asarray(req.secondary.position_m, dtype=np.float64)
        v2 = np.asarray(req.secondary.velocity_mps, dtype=np.float64)

        if not (np.all(np.isfinite(r1)) and np.all(np.isfinite(v1)) and
                np.all(np.isfinite(r2)) and np.all(np.isfinite(v2))):
            return {
                "schema_version": CURRENT_SCHEMA_VERSION,
                "error": "UNPHYSICAL_INPUT",
                "message": "State vectors contain non-finite numbers (NaN or Inf)",
                "is_valid": False,
            }

        # 3. Stale timestamp check
        scen = req.scenario_id
        t = req.timestamp_s
        if scen in self.last_seen_timestamps:
            if t < self.last_seen_timestamps[scen] - 1e-4:
                return {
                    "schema_version": CURRENT_SCHEMA_VERSION,
                    "error": "STALE_TIMESTAMP",
                    "message": f"Received timestamp {t:.2f}s is earlier than last seen {self.last_seen_timestamps[scen]:.2f}s",
                    "is_valid": False,
                }
        self.last_seen_timestamps[scen] = t

        # 4. Generate Baseline Prediction & Risk Classification
        # Relative state
        r_rel, v_rel = calculate_relative_state(np.hstack((r1, v1)), np.hstack((r2, v2)))
        cpa_res = calculate_linear_cpa(r_rel, v_rel, window=(0.0, 3600.0))

        pred_tca = float(cpa_res["t_cpa"])
        pred_miss = float(cpa_res["d_cpa"])

        # Probability calculation if covariances exist
        pc_val = None
        if req.primary.covariance_6x6 is not None and req.secondary.covariance_6x6 is not None:
            c1 = np.asarray(req.primary.covariance_6x6, dtype=np.float64)
            c2 = np.asarray(req.secondary.covariance_6x6, dtype=np.float64)
            cov_rel = c1 + c2
            try:
                pc_res = calculate_collision_probability(r_rel, v_rel, cov_rel, hard_body_radius=5.0)
                pc_val = pc_res.get("pc")
            except Exception:
                pc_val = None

        # Risk Classification
        if pred_miss < 500.0 or (pc_val is not None and pc_val > 1e-4):
            risk_class = "CRITICAL"
        elif pred_miss < self.critical_miss_distance_m or (pc_val is not None and pc_val > self.critical_pc_threshold):
            risk_class = "HIGH"
        elif pred_miss < 10000.0:
            risk_class = "MEDIUM"
        else:
            risk_class = "LOW"

        # Recommended Action
        if risk_class in ["HIGH", "CRITICAL"]:
            # Propose an in-plane radial avoidance impulse (-R) with advance lead time
            action = RecommendedAction(
                type="PROPOSE_MANEUVER",
                epoch_offset_seconds=max(60.0, pred_tca - 600.0),
                delta_v_mps=[-3.0, 0.0, 0.0],  # 3.0 m/s along -R
                frame="RTN"
            )
        else:
            action = RecommendedAction(
                type="MONITOR",
                epoch_offset_seconds=0.0,
                delta_v_mps=[0.0, 0.0, 0.0],
                frame="RTN"
            )

        resp = MLInferenceResponse(
            schema_version=CURRENT_SCHEMA_VERSION,
            scenario_id=scen,
            prediction=PredictionOutput(
                tca_seconds=pred_tca,
                miss_distance_m=pred_miss,
                collision_probability=pc_val,
                risk_class=risk_class
            ),
            recommended_action=action,
            model_version=self.model_version,
            is_validated=False,
            validation_status="UNVALIDATED_PROPOSAL"
        )

        return resp.to_dict()

    @staticmethod
    def validate_proposal_physics(
        proposal: Dict[str, Any],
        constraints: Optional[ManoeuvreConstraints] = None
    ) -> Tuple[bool, str]:
        """
        Safety Gate: Deterministically validate an ML manoeuvre proposal against
        astrodynamic physical constraints before simulated execution.
        (Technical Guide Section 10.3)
        """
        if constraints is None:
            constraints = ManoeuvreConstraints()

        action = proposal.get("recommended_action", {})
        if action.get("type") != "PROPOSE_MANEUVER":
            return True, "No manoeuvre proposed; monitoring only."

        dv = np.asarray(action.get("delta_v_mps", []), dtype=np.float64)
        if dv.shape != (3,):
            return False, f"Invalid delta_v dimension: expected 3, got {dv.shape}"

        dv_mag = float(np.linalg.norm(dv))
        if dv_mag > constraints.max_delta_v + 1e-6:
            return False, f"Delta-V {dv_mag:.2f} m/s exceeds max allowed {constraints.max_delta_v:.2f} m/s"

        lead_time = float(action.get("epoch_offset_seconds", 0.0))
        if lead_time < 0.0:
            return False, f"Negative lead time: {lead_time:.1f} s"

        frame = action.get("frame")
        if frame != "RTN":
            return False, f"Invalid action frame: expected 'RTN', got '{frame}'"

        return True, "PASSED_PHYSICAL_VALIDATION"
