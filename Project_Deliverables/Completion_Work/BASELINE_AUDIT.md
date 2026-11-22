# Baseline System Audit: D1 & D2 Health Check

**Project:** Satellite Collision Avoidance System (ICPS)  
**Audit Epoch:** 22 November 2026  
**Auditor:** Autonomous Orchestrator Agent  
**Environment:** Python 3.14.4 (Windows 11, x64) / Unreal Engine 5.7.4  

---

## 1. Test Suite Verification

Command executed:
```powershell
python -m pytest D2/tests
```

**Result:**
```text
============================= test session starts =============================
platform win32 -- Python 3.14.4, pytest-9.1.1, pluggy-1.7.0
rootdir: C:\Users\Sriram Krovi\satellite-collision-avoidance-system
collected 39 items

D2/tests/test_conjunction.py .......                                     [ 17%]
D2/tests/test_manoeuvres.py ............                                 [ 48%]
D2/tests/test_orbital_covariance.py ......                               [ 64%]
D2/tests/test_uncertainty.py ........                                    [ 84%]
D2/tests/test_visualization.py ......                                    [100%]

============================= 39 passed in 13.90s =============================
```

All 39 existing unit and regression tests pass with zero failures.

---

## 2. Protected Baseline Values (Authoritative Invariants)

These values represent the frozen, quality-controlled scientific baseline outputs established in Deliverable 2 and Milestone 4. Any modification causing deviation from these values constitutes a regression.

| Metric | Nominal State | Post-Manoeuvre State | Net Delta |
| :--- | :--- | :--- | :--- |
| **TCA (Seconds)** | $769.631971\text{ s}$ | $903.029223\text{ s}$ | $+133.397252\text{ s}$ |
| **Miss Distance (Metres)** | $1563.476320\text{ m}$ | $2454.416263\text{ m}$ | $+890.939943\text{ m}$ |
| **Operational Limit ($2000\text{ m}$)** | Violated ($436.52\text{ m}$ margin) | Cleared ($454.42\text{ m}$ margin) | Safe clearance |
| **Collision Probability ($P_c$)** | $3.957542 \times 10^{-14}$ | $1.238744 \times 10^{-22}$ | $-8.50\text{ orders of magnitude}$ |
| **Numerical Tail Status** | `NUMERICAL_UNDERFLOW` | `NUMERICAL_UNDERFLOW` | Preserved asymptotic tail |
| **Selected Manoeuvre** | N/A | `MAN_006_-R_3.00mps_T170s` | Optimal candidate |
| **Delta-V Magnitude & Axis** | $0.00\text{ m/s}$ | $3.00\text{ m/s}$ in $-\hat{\mathbf{R}}$ | Pure in-plane radial |
| **Burn Epoch** | N/A | $169.631971\text{ s}$ | $600.0\text{ s}$ lead time |
| **Trajectory Deviation at Nom TCA** | $0.00\text{ m}$ | $2018.989967\text{ m}$ | Coupled $R$ and $T$ components |
| **Peak Trajectory Deviation** | $0.00\text{ m}$ | $3008.502994\text{ m}$ | At $t = 1000.0\text{ s}$ |

---

## 3. Subsystem Architecture Map

```
satellite-collision-avoidance-system/
├── D1 (Historical Baseline)
│   ├── data_loader.py (TLE ingestion)
│   ├── propagator.py (SGP4 propagation)
│   └── day1_pipeline.py (End-to-end SGP4 pipeline)
├── D2 (Scientific Core)
│   ├── dynamics/
│   │   ├── two_body.py (Point-mass gravity & gravity gradient)
│   │   ├── rk4.py (Fixed-step Runge-Kutta 4 integrator)
│   │   ├── variational.py (42-state STM & variational equations)
│   │   └── orbit_propagator.py (State time-series propagator)
│   ├── conjunction/
│   │   ├── tca.py (Linear CPA & numerical parabolic-refined TCA)
│   │   └── screening.py (25 km broad-phase filter)
│   ├── uncertainty/
│   │   ├── covariance.py (6x6 covariance representation, validation & STM mapping)
│   │   └── collision_probability.py (Foster 1992 encounter plane solver)
│   ├── manoeuvres/
│   │   ├── manoeuvre_model.py (RTN frame, RTN <-> ECI rotations, ImpulsiveManoeuvre)
│   │   ├── candidate_generator.py (Discrete RTN candidate grid)
│   │   ├── manoeuvre_evaluator.py (Post-burn re-propagation and re-screening)
│   │   ├── manoeuvre_optimizer.py (Multi-criteria ranking & constraint filtering)
│   │   └── avoidance_pipeline.py (End-to-end autonomous avoidance pipeline)
│   ├── scenarios/
│   │   └── close_approach.py (7000 km circular LEO reference scenario)
│   └── visualization/
│       ├── coordinate_transform.py (ECI -> Unreal left-handed Z-up transformation)
│       └── simulation_exporter.py (unreal_simulation_payload.json generator)
├── UnrealProject/ (Unreal Engine 5.7.4 Client)
│   └── Source/SatelliteAvoidance/
│       ├── Actors/ (EarthActor, SatelliteActor, DebrisActor)
│       ├── DataBridge/ (CoordinateAdapter, SimulationDataBridge)
│       ├── Simulation/ (OrbitSimulationManager)
│       ├── UI/ (AvoidanceInfoPanelWidget)
│       └── Visualization/ (OrbitPathActor, ConjunctionVisualizer, ManoeuvreVisualizer)
└── Project_Deliverables/Final_Milestone/
    ├── Simulation_Results.json
    ├── Performance_Evaluation.csv
    └── Final_Technical_Report.pdf
```
