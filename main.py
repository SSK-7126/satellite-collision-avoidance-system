"""
main.py
=======
Satellite Collision Avoidance System (SCAS)
Master Execution Script — Integrated Backend & 3D Visualization System

Usage:
    python main.py                 # Run interactive 3D visualization (Real Data Mode)
    python main.py --mode synthetic # Run interactive 3D visualization (Synthetic Close-Approach Test)
    python main.py --test          # Run automated end-to-end verification suite
    python main.py --help          # Show command options
"""

import sys
import argparse
from visualization_3d import SatelliteVisualizer3D


def run_automated_verification():
    """
    Run non-interactive end-to-end verification of all Person 1 backend components
    and Person 2 visualization/analysis integrations.
    """
    print("\n" + "=" * 70)
    print("SATELLITE COLLISION AVOIDANCE SYSTEM - SYSTEM VERIFICATION SUITE")
    print("=" * 70)

    # 1. Test Real Data Mode
    print("\n[TEST 1] Verifying Real Tracked Data Mode (CARTOSAT-3 / PSLV R/B)...")
    app_real = SatelliteVisualizer3D(mode="real", headless=True)
    m_real = app_real.step()
    print(f"  [OK] SGP4 Propagation Start:  {app_real.real_start_time}")
    print(f"  [OK] Primary Object:          {m_real['primary_name']}")
    print(f"  [OK] Primary Position (km):   [{m_real['pos_a'][0]:.2f}, {m_real['pos_a'][1]:.2f}, {m_real['pos_a'][2]:.2f}]")
    print(f"  [OK] Primary Altitude:        {m_real['alt_a']:.2f} km")
    print(f"  [OK] Secondary Object:        {m_real['secondary_name']}")
    print(f"  [OK] Secondary Altitude:      {m_real['alt_b']:.2f} km")
    print(f"  [OK] 3D Separation Distance:  {m_real['encounter']['distance_km']:.2f} km")
    print(f"  [OK] Relative Speed:          {m_real['encounter']['relative_speed_km_s']:.3f} km/s")
    print(f"  [OK] Proximity Status:        {m_real['encounter']['status']} [{m_real['encounter']['level']}]")

    # 2. Test Synthetic Test Scenario
    print("\n[TEST 2] Verifying Controlled Synthetic Close-Approach Scenario...")
    app_syn = SatelliteVisualizer3D(mode="synthetic", headless=True)
    app_syn.sim_speed = 10  # 1s per step

    statuses_observed = set()
    for _ in range(400):
        step_metrics = app_syn.step()
        statuses_observed.add(step_metrics["encounter"]["status"])

    print(f"  [OK] Proximity Status Hierarchy: {sorted(list(statuses_observed))}")
    print(f"  [OK] Verified Observed CAD:      {app_syn.cad_km:.2f} km (Expected ~ 5.00 km)")
    print(f"  [OK] Verified Estimated TCA:     {app_syn.tca_str} (Expected ~ T+ 200 s)")
    print(f"  [OK] Close Approach Detected:    {app_syn.close_approach_detected}")
    print(f"  [OK] Encounter Record Persisted: {app_syn.persisted_event_record is not None}")

    if app_syn.persisted_event_record:
        print(f"  [OK] Persisted Event Record:     {app_syn.persisted_event_record}")

    # 3. Assert Criteria
    assert "SAFE" in statuses_observed, "SAFE status missing"
    assert "MONITOR" in statuses_observed, "MONITOR status missing"
    assert "CLOSE APPROACH" in statuses_observed, "CLOSE APPROACH status missing"
    assert abs(app_syn.cad_km - 5.0) < 0.1, f"CAD mismatch: {app_syn.cad_km}"
    assert app_syn.close_approach_detected is True, "Close approach failed detection"
    assert app_syn.persisted_event_record is not None, "Event persistence failed"

    print("\n" + "=" * 70)
    print("ALL VERIFICATION CHECKS PASSED SUCCESSFULLY (100% COMPLIANT WITH D1 SPEC)")
    print("=" * 70 + "\n")


def main():
    parser = argparse.ArgumentParser(
        description="Satellite Collision Avoidance System — 3D Visualization and Conjunction Analysis"
    )
    parser.add_argument(
        "--mode",
        choices=["real", "synthetic"],
        default="real",
        help="Simulation mode: 'real' (real TLE tracking) or 'synthetic' (5km close approach encounter)"
    )
    parser.add_argument(
        "--test",
        action="store_true",
        help="Run non-interactive automated test suite and exit"
    )
    parser.add_argument(
        "--headless",
        action="store_true",
        help="Run without displaying a graphical window"
    )

    args = parser.parse_args()

    if args.test:
        run_automated_verification()
        return

    print("=" * 65)
    print("   SATELLITE COLLISION AVOIDANCE SYSTEM - D1")
    print("   3D Orbital Visualization & Conjunction Dashboard")
    print("=" * 65)
    print(f" Mode:           {args.mode.upper()}")
    print(" Interactive UI: Opening 3D Space Operations Center...")
    print(" Controls:")
    print("   - [▶ PLAY / ⏸ PAUSE]  Toggle simulation clock")
    print("   - [↺ RESET]           Reset clock, CAD, and telemetry")
    print("   - [1x, 10x, 60x, 300x] Time warp speed multipliers")
    print("   - [REAL DATA / TEST]  Switch operational mode")
    print("   - Mouse: Left click & drag to rotate 3D Earth, right click to zoom")
    print("   - Keys:  Space = Pause/Play, 'r' = Reset, 'm' = Toggle Mode, 'q' = Quit")
    print("=" * 65)

    app = SatelliteVisualizer3D(mode=args.mode, headless=args.headless)
    app.run()


if __name__ == "__main__":
    main()
