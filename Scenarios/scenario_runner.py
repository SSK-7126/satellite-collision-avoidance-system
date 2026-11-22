"""
Scenarios/scenario_runner.py
============================
Master Execution Harness for Scenarios S0–S8.
Strictly following Section 11 and Section 12 of the Technical Development Guide.

Executes:
  S0: Circular Orbit Verification
  S1: Elliptical Orbit Verification
  S2: Close Approach Conjunction
  S3: Uncertain Conjunction & Covariance Propagation
  S4: Avoidance Burn & Re-Screening
  S5: Multiple Debris Population Screening & Avoidance
  S6: Perturbed LEO (J2 Oblateness & Drag Decay)
  S7: Sensor Tracking Outage & Uncertainty Dilation
  S8: Safe Pass (Disambiguating Proximity from Risk)

Outputs:
  - Results/scenarios_s0_s8.json
  - Results/scenarios_summary.csv
"""

import time
import json
import csv
import os
import sys
from typing import Dict, Any, List

# Ensure project root is in sys.path
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from Scenarios.s0_circular_orbit import run_scenario_s0
from Scenarios.s1_elliptical_orbit import run_scenario_s1
from Scenarios.s2_close_approach import run_scenario_s2
from Scenarios.s3_uncertain_conjunction import run_scenario_s3
from Scenarios.s4_avoidance_burn import run_scenario_s4
from Scenarios.s5_multiple_debris import run_scenario_s5
from Scenarios.s6_perturbed_leo import run_scenario_s6
from Scenarios.s7_sensor_outage import run_scenario_s7
from Scenarios.s8_safe_pass import run_scenario_s8

RESULTS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "Results")
JSON_OUTPUT = os.path.join(RESULTS_DIR, "scenarios_s0_s8.json")
CSV_OUTPUT = os.path.join(RESULTS_DIR, "scenarios_summary.csv")


def run_all_scenarios() -> Dict[str, Any]:
    os.makedirs(RESULTS_DIR, exist_ok=True)
    print("=" * 75)
    print("EXECUTING SATELLITE ANTI-COLLISION SIMULATION SCENARIO SUITE (S0 - S8)")
    print("=" * 75)

    scenario_runners = [
        ("S0", "Circular Orbit", run_scenario_s0),
        ("S1", "Elliptical Orbit", run_scenario_s1),
        ("S2", "Close Approach", run_scenario_s2),
        ("S3", "Uncertain Conjunction", run_scenario_s3),
        ("S4", "Avoidance Burn", run_scenario_s4),
        ("S5", "Multiple Debris", run_scenario_s5),
        ("S6", "Perturbed LEO", run_scenario_s6),
        ("S7", "Sensor Outage", run_scenario_s7),
        ("S8", "Safe Pass", run_scenario_s8),
    ]

    results = {}
    summary_rows = []

    for sid, name, runner in scenario_runners:
        t0 = time.perf_counter()
        try:
            res = runner()
            runtime_s = time.perf_counter() - t0
            res["runtime_seconds"] = round(runtime_s, 4)
            status = res.get("status", "COMPLETED")
            results[sid] = res

            print(f"[{sid}] {name:<25} : {status:<8} (runtime: {runtime_s:.3f}s)")

            summary_rows.append({
                "scenario_id": sid,
                "name": name,
                "status": status,
                "runtime_seconds": f"{runtime_s:.4f}",
                "key_metric": str(list(res.items())[2] if len(res) > 2 else "N/A"),
            })
        except Exception as e:
            runtime_s = time.perf_counter() - t0
            results[sid] = {
                "scenario_id": sid,
                "name": name,
                "status": "ERROR",
                "error": str(e),
                "runtime_seconds": round(runtime_s, 4)
            }
            print(f"[{sid}] {name:<25} : ERROR ({e})")
            summary_rows.append({
                "scenario_id": sid,
                "name": name,
                "status": "ERROR",
                "runtime_seconds": f"{runtime_s:.4f}",
                "key_metric": f"ERROR: {str(e)}",
            })

    # Save JSON results
    with open(JSON_OUTPUT, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, default=str)
    print(f"\n[OUTPUT] Saved JSON scenario log: {JSON_OUTPUT}")

    # Save CSV summary
    with open(CSV_OUTPUT, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["scenario_id", "name", "status", "runtime_seconds", "key_metric"])
        writer.writeheader()
        writer.writerows(summary_rows)
    print(f"[OUTPUT] Saved CSV scenario summary: {CSV_OUTPUT}")

    all_passed = all(r.get("status") == "PASSED" for r in results.values())
    print("\n" + "=" * 75)
    print(f"OVERALL SCENARIO SUITE RESULT: {'ALL 9 SCENARIOS PASSED' if all_passed else 'SOME SCENARIOS FAILED'}")
    print("=" * 75)

    return results


if __name__ == "__main__":
    run_all_scenarios()
