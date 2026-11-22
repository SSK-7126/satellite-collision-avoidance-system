"""
Evaluation/metrics_suite.py
===========================
Comprehensive Astrodynamics & Conjunction Metrics Calculation Harness.
Strictly following Section 12.2 of the Technical Development Guide.

Metrics Evaluated:
1. TCA Error (s): Predicted versus reference time of closest approach.
2. Miss-Distance Error (m): Predicted versus reference separation at TCA.
3. Decision Lead Time (s): Time from actionable alert / manoeuvre decision to TCA.
4. Post-Manoeuvre Risk Reduction Factor: Ratio of pre- to post-manoeuvre collision probability (Pc_nom / Pc_post)
   or logarithmic decades (log10(Pc_nom) - log10(Pc_post)).
5. Delta-V & Propellant Expenditure: Required velocity impulse (m/s) and propellant mass consumed (kg).
6. Operational Clearance Margin (m): Distance clearance above the 2000 m threshold.
7. Classification Accuracy Metrics:
   - False-Positive Rate (FPR): Safe events falsely classified as dangerous.
   - False-Negative Rate (FNR): Dangerous events falsely classified as safe (safety-critical).
8. Computational Runtime (s): Total CPU time for numerical propagation, screening, and optimization.
"""

from typing import Dict, Any, List, Optional
import numpy as np

from D2.manoeuvres.propulsion import calculate_propellant_mass_ideal


def compute_conjunction_metrics(
    nominal_tca_s: float,
    reference_tca_s: float,
    nominal_miss_m: float,
    reference_miss_m: float,
    nominal_pc: Optional[float],
    post_pc: Optional[float],
    applied_delta_v_mps: float,
    burn_epoch_s: float,
    spacecraft_wet_mass_kg: float = 1000.0,
    isp_s: float = 300.0,
    operational_threshold_m: float = 2000.0,
    runtime_s: float = 0.0
) -> Dict[str, Any]:
    """
    Compute formal quantitative metrics for a conjunction and avoidance event.
    (Technical Guide Section 12.2)
    """
    # 1. Prediction Errors vs Reference Truth
    tca_err = float(abs(nominal_tca_s - reference_tca_s))
    miss_err = float(abs(nominal_miss_m - reference_miss_m))

    # 2. Decision Lead Time
    decision_lead_time_s = float(max(0.0, nominal_tca_s - burn_epoch_s))

    # 3. Collision Probability Reduction
    prob_reduction_ratio = None
    log10_reduction_decades = None
    if nominal_pc is not None and post_pc is not None and post_pc > 0.0:
        prob_reduction_ratio = float(nominal_pc / post_pc)
        log10_reduction_decades = float(np.log10(nominal_pc) - np.log10(post_pc))

    # 4. Resource Expenditure
    fuel_consumed_kg = calculate_propellant_mass_ideal(
        delta_v_mps=applied_delta_v_mps,
        initial_mass_kg=spacecraft_wet_mass_kg,
        isp_s=isp_s
    )

    return {
        "tca_error_seconds": tca_err,
        "miss_distance_error_m": miss_err,
        "decision_lead_time_seconds": decision_lead_time_s,
        "decision_lead_time_minutes": decision_lead_time_s / 60.0,
        "delta_v_magnitude_mps": float(applied_delta_v_mps),
        "fuel_consumed_kg": float(fuel_used_kg if 'fuel_used_kg' in locals() else fuel_consumed_kg),
        "collision_probability_reduction_ratio": prob_reduction_ratio,
        "collision_probability_reduction_decades": log10_reduction_decades,
        "computational_runtime_seconds": float(runtime_s),
    }


def compute_confusion_matrix_metrics(
    evaluations: List[Dict[str, Any]],
    threshold_m: float = 2000.0
) -> Dict[str, Any]:
    """
    Calculate classification metrics: FPR and FNR across evaluated encounters.
    - True Condition Positive: Actual miss distance < threshold_m (truly dangerous).
    - True Condition Negative: Actual miss distance >= threshold_m (truly safe).
    - Predicted Positive: System triggered avoidance alert.
    - Predicted Negative: System declared safe pass.
    """
    tp = 0
    fp = 0
    tn = 0
    fn = 0

    for ev in evaluations:
        actual_dangerous = bool(ev["actual_miss_m"] < threshold_m)
        predicted_dangerous = bool(ev["predicted_alert"] is True)

        if actual_dangerous and predicted_dangerous:
            tp += 1
        elif not actual_dangerous and predicted_dangerous:
            fp += 1
        elif not actual_dangerous and not predicted_dangerous:
            tn += 1
        elif actual_dangerous and not predicted_dangerous:
            fn += 1

    total = len(evaluations)
    fpr = float(fp / (fp + tn)) if (fp + tn) > 0 else 0.0
    fnr = float(fn / (fn + tp)) if (fn + tp) > 0 else 0.0

    return {
        "total_evaluations": total,
        "true_positives": tp,
        "false_positives": fp,
        "true_negatives": tn,
        "false_negatives": fn,
        "false_positive_rate": fpr,
        "false_negative_rate": fnr,
        "safety_critical_zero_fnr": bool(fn == 0),
    }
