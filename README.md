# Satellite Anti-Collision System (ICPS)
### Autonomous Satellite Collision Avoidance System

[![Pytest Test Suite](https://img.shields.io/badge/Pytest%20Suite-70%2F70%20Passed-brightgreen)](file:///c:/Users/Sriram%20Krovi/satellite-collision-avoidance-system/tests)
[![Scenario Suite](https://img.shields.io/badge/Scenarios%20S0--S8-9%2F9%20Passed-brightgreen)](file:///c:/Users/Sriram%20Krovi/satellite-collision-avoidance-system/Scenarios)
[![Unreal Engine](https://img.shields.io/badge/Unreal%20Engine-5.7.4-blue)](https://www.unrealengine.com/)
[![Astrodynamics Solvers](https://img.shields.io/badge/Backend-Python%20RK4%20%7C%20Foster%20(1992)-orange)](file:///c:/Users/Sriram%20Krovi/satellite-collision-avoidance-system/D2/)
[![Milestone](https://img.shields.io/badge/Milestone-4%20Final%20QC%20Approved-success)](file:///c:/Users/Sriram%20Krovi/satellite-collision-avoidance-system/Project_Deliverables/Final_Milestone/)

A computational simulation and physics-synchronized 3D visualization platform designed to model orbital debris, detect potential satellite close approaches, evaluate collision risk, and simulate autonomous collision-avoidance manoeuvres in Low Earth Orbit (LEO).

Developed under the Autonomous Satellite Collision Avoidance System project (ICPS), pairing authoritative Python astrodynamics backends with real-time, telemetry-driven Unreal Engine 5.7.4 visualization.

---

## 1. Project Deliverables

### D1 — Orbital Environment Simulation & Conjunction Assessment
- Model a protected primary satellite (CARTOSAT-3) and uncooperative space debris objects.
- Simulate orbital motion using two-body gravitational dynamics and SGP4 TLE propagation.
- Generate and visualize synchronized orbital trajectories.
- Calculate relative position, relative velocity, separation distance, and closest approach.
- Provide 2D/3D visualization and interactive telemetry dashboards.

### D2 — Autonomous Collision Avoidance & Manoeuvre Planning
- Detect potential close approaches between satellites and debris using broad-phase screening ($25.0\text{ km}$).
- Calculate Time of Closest Approach (TCA) and minimum miss distance.
- Estimate collision risk and collision probability ($P_c$) via 2D encounter plane integration (Foster, 1992) and state covariance propagation.
- Autonomous candidate manoeuvre generation and multi-criteria optimization in the local orbital RTN frame.
- Apply impulsive $\Delta \mathbf{v}$ and simulate the post-manoeuvre modified trajectory.
- Quantitatively evaluate miss distance improvement, TCA shift, collision risk attenuation, trajectory deviation, and control effort.

---

## 2. System Architecture

| Component | Technology | Responsibility |
| :--- | :--- | :--- |
| **Scientific Astrodynamics** | Python (NumPy, SciPy) | Numerical RK4 propagation, two-body equations of motion, covariance propagation |
| **Conjunction & Collision Risk** | Python D1/D2 Solvers | Numerical TCA detection, Foster (1992) probability solver, screening filters |
| **Manoeuvre & Propulsion** | Python Optimization Engine | Discrete RTN candidate generation, Tsiolkovsky propellant calculation, finite-burn 7D propagation, execution dispersion |
| **Sensor Simulation** | Python Sensor Subsystem | Ground truth vs. observation separation, optical LOS & angular noise, radar range & Doppler, WGS84 ground stations, outage injection |
| **ML Inference Service** | Python Service (JSON Schema v1.0) | Standardized request/response interface, frame & timestamp validation, heuristic risk estimation, physics-based safety gate |
| **Advanced Orbital Dynamics** | Python Perturbation Engine | Optional WGS84 $J_2$ geopotential harmonic and exponential atmospheric drag with atmospheric co-rotation |
| **Scenario Suite (S0–S8)** | Python Automated Test Suite | Standardized evaluation benchmarks (circular, elliptical, close approach, multiple debris, perturbed LEO, outages, safe pass) |
| **Evaluation & Metrics** | Python Analytics Engine | Automated calculation of TCA error, miss distance error, decision lead time, risk reduction factor, propellant consumed |
| **Data Bridge** | JSON Contract (`unreal_simulation_payload.json`) | Versioned data contract serializing 8 milestone epochs, full trajectories, sensing metadata, and ML telemetry |
| **Visualization & Telemetry** | Unreal Engine 5.7.4 (C++ / UMG) | Physics-synchronized 3D rendering, interactive HUD telemetry, 8 milestone cameras, sensor visualizer actor component |

```
+---------------------------------------------------------------------------------+
|                        AUTHORITATIVE SCIENTIFIC BACKEND                         |
|                                                                                 |
|  +------------------------+      +-------------------------+                    |
|  | D1 Conjunction Engine  | ---> | D2 Avoidance Manoeuvre  |                    |
|  | SGP4 TLE / Numerical   |      | RK4 Integrator, RTN/ECI |                    |
|  | Relative Motion (TCA)  |      | Foster (1992) Pc Solver |                    |
|  +------------------------+      +-------------------------+                    |
|                                               |                                 |
|                                               v                                 |
|                             +-----------------------------------+               |
|                             | unreal_simulation_payload.json    |               |
|                             | 8 Milestone Epochs & Trajectories |               |
|                             +-----------------------------------+               |
+-----------------------------------------------|---------------------------------+
                                                | JSON Bridge
                                                v
+---------------------------------------------------------------------------------+
|                       UNREAL ENGINE 5.7.4 VISUALIZATION                         |
|                                                                                 |
|  +---------------------------+       +------------------------------------+     |
|  | OrbitSimulationManager    | <---> | AvoidanceInfoPanelWidget (HUD)     |     |
|  | Trajectory Spline Visuals |       | 8 Milestones, Cameras, Telemetry   |     |
|  +---------------------------+       +------------------------------------+     |
+---------------------------------------------------------------------------------+
```

- **Authoritative Astrodynamics**: All physical trajectories, orbital states, covariance ellipsoids, and collision probabilities are computed exclusively by Python scientific solvers.
- **Unreal Engine Playback**: Unreal Engine functions strictly as a high-fidelity visual rendering and telemetry presentation client. The engine consumes `unreal_simulation_payload.json` and performs no independent physical simulation.

---

## 3. Mathematical Model

The authoritative astrodynamic backends implement the following equations of motion:

1. **Two-Body Gravitational Acceleration**
   $$\mathbf{a} = -\frac{\mu \mathbf{r}}{\|\mathbf{r}\|^3}$$
   where $\mu = 3.986004418 \times 10^{14}\text{ m}^3/\text{s}^2$ (standard Earth gravitational parameter).

2. **Circular Orbital Velocity & Period**
   $$v = \sqrt{\frac{\mu}{r}}, \qquad T = 2\pi \sqrt{\frac{r^3}{\mu}}$$

3. **Relative Encounter State & Closest Approach (TCA)**
   $$\mathbf{r}_{\text{rel}}(t) = \mathbf{r}_{\text{sec}}(t) - \mathbf{r}_{\text{sat}}(t), \qquad \mathbf{v}_{\text{rel}}(t) = \mathbf{v}_{\text{sec}}(t) - \mathbf{v}_{\text{sat}}(t)$$
   At the epoch of closest approach, the range rate vanishes:
   $$\dot{d}(t_{\text{TCA}}) = \frac{\mathbf{r}_{\text{rel}}(t_{\text{TCA}}) \cdot \mathbf{v}_{\text{rel}}(t_{\text{TCA}})}{\|\mathbf{r}_{\text{rel}}(t_{\text{TCA}})\|} = 0$$

4. **Collision Probability ($P_c$) Evaluation (Foster, 1992)**
   Projecting the relative covariance $\mathbf{C}_{\text{enc}}$ onto the 2D encounter plane normal to $\mathbf{v}_{\text{rel}}$:
   $$P_c = \frac{1}{2\pi \sigma_x \sigma_y \sqrt{1 - \rho_{xy}^2}} \iint_{\|\mathbf{r}\| \le R_{\text{HBR}}} \exp\left( -\frac{1}{2(1-\rho_{xy}^2)} \left[ \frac{(x-x_0)^2}{\sigma_x^2} - \frac{2\rho_{xy}(x-x_0)(y-y_0)}{\sigma_x \sigma_y} + \frac{(y-y_0)^2}{\sigma_y^2} \right] \right) dx\,dy$$

5. **Impulsive Avoidance Velocity Increment**
   $$\Delta \mathbf{v} = \mathbf{v}(t_{\text{burn}}^+) - \mathbf{v}(t_{\text{burn}}^-)$$
   Numerical orbit propagation utilizes a fourth-order Runge-Kutta (RK4) integrator.

---

## 4. Key Scenario Parameters & Evaluation Results

The reference scenario models a close approach in a circular Low Earth Orbit ($r_0 = 7000.0\text{ km}$, altitude $h \approx 621.9\text{ km}$, speed $v_0 = 7546.05\text{ m/s}$):
- **Protected Primary Satellite**: CARTOSAT-3 (`PROTECTED_SAT`, Payload01 bus)
- **Secondary Threat Object**: DEBRIS_PIECE_99 (`SECONDARY_OBJ`, Object99 fragment)
- **Operational Safety Threshold**: $2000.0\text{ m}$ ($2.0\text{ km}$, project-defined operational clearance limit)
- **Hard-Body Radius (HBR)**: $5.00\text{ m}$ (combined physical collision radius)
- **Screening Distance**: $25000.0\text{ m}$ ($25.0\text{ km}$ broad-phase detection sphere)

### Quantitative Evaluation Summary

| Parameter | Nominal (Unmanoeuvred) | Post-Manoeuvre | Net Change / Improvement |
| :--- | :--- | :--- | :--- |
| **Miss Distance at TCA** | $1563.48\text{ m}$ | $2454.42\text{ m}$ | **$+890.94\text{ m}$** ($+56.985\%$ gain) |
| **Time of Closest Approach (TCA)** | $769.63\text{ s}$ | $903.03\text{ s}$ | **$+133.40\text{ s}$** temporal delay |
| **Operational Threshold ($2000\text{ m}$)** | Violated (by $436.52\text{ m}$) | **Satisfied** (by $454.42\text{ m}$) | Conjunction cleared |
| **Calculated Collision Probability ($P_c$)** | $3.958 \times 10^{-14}$ | $1.239 \times 10^{-22}$ | **$8.50$ decades** ($3.195 \times 10^8 \times$ reduction) |
| **Selected Avoidance Manoeuvre** | N/A | `MAN_006_-R_3.00mps_T170s` | Optimal candidate |
| **Delta-V Magnitude & Direction** | $0.00\text{ m/s}$ | $3.00\text{ m/s}$ in $-\hat{\mathbf{R}}$ | Pure in-plane radial impulse |
| **Burn Epoch ($t_{\text{burn}}$)** | N/A | $169.63\text{ s}$ | $600.0\text{ s}$ ($10\text{ min}$) lead time |
| **Max Trajectory Deviation** | $0.00\text{ m}$ | $3008.50\text{ m}$ (at $t=1000\text{ s}$) | Spatial divergence |

### Orbital Mechanics Clarification

The applied avoidance manoeuvre is an impulsive burn of $\Delta v = 3.00\text{ m/s}$ along the negative radial direction ($-\hat{\mathbf{R}}$). In a circular orbit:
- The radial burn preserves tangential velocity ($v_{\theta} = 7546.05\text{ m/s}$) and introduces a radial velocity component ($v_r = -3.00\text{ m/s}$).
- This induces a small orbital eccentricity:
  $$e \approx \frac{\Delta v}{v_0} \approx \frac{3.00}{7546.05} \approx 0.000398$$
- Specific orbital energy increases by $\Delta \mathcal{E} = \frac{(\Delta v)^2}{2} = +4.50\text{ J/kg}$, resulting in a semi-major axis increase of $\Delta a \approx a \left(\frac{\Delta v}{v_0}\right)^2 \approx \mathbf{+1.11\text{ m}}$ ($\Delta a / a \approx 1.58 \times 10^{-7}$).
- The orbital period shift is negligible: $\Delta T \approx \frac{3}{2} T \frac{\Delta a}{a} \approx \mathbf{+1.38\text{ ms}}$ out of a $5828.52\text{ s}$ orbit.
- At nominal TCA ($600\text{ s}$ post-burn), the trajectory deviation resolves into a **$-1677.1\text{ m}$ radial displacement** (lower altitude) and a **$+1124.2\text{ m}$ along-track forward lead** (Euclidean norm $2019.1\text{ m}$; $2018.99\text{ m}$ at the discrete $770.0\text{ s}$ grid sample), with squared-component contributions of 69.0% radial and 31.0% along-track. The miss distance dilation is driven jointly by coupled radial and along-track in-plane separation, **not** by along-track phasing alone or an out-of-plane inclination change.

---

## 5. Data Sources & Simulation Outputs

### Reference Astrodynamics & Data Sources
- **Synthetic Orbital Objects**: Controlled encounter baseline scenario in circular LEO.
- **TLE Records**: Space object tracking data (`data/orbital_data.txt`, CARTOSAT-3 NORAD ID 44804, PSLV R/B NORAD ID 44805).
- **NASA CARA**: Conjunction assessment, 2D encounter plane integration standards, and safety clearance thresholds.
- **ESA Space Debris Office / IADC**: Space debris environment modeling conventions and operational screening guidelines.
- **NASA/JPL**: Physical constants (WGS84 Earth equatorial radius $R_E = 6378137.0\text{ m}$, $\mu = 398600.4418\text{ km}^3/\text{s}^2$).

### Primary Simulation Outputs
- Complete 3D satellite and debris trajectory states (nominal and modified).
- Time of Closest Approach (TCA) and relative separation distance series.
- 2D encounter plane geometry and Mahalanobis distance.
- Pre- and post-manoeuvre collision probabilities ($P_c$) with asymptotic underflow preservation.
- Optimal impulsive $\Delta \mathbf{v}$ vector in RTN and ECI frames.
- Quantitative collision avoidance evaluation metrics and trajectory deviation profiles.

---

## 6. Project Deliverables & Reproduction Guide

All authoritative final deliverables for Milestone 4 and the Quality Control pass are archived in `Project_Deliverables/Final_Milestone/`:

| Deliverable Asset | Description | Format / Path |
| :--- | :--- | :--- |
| **Final Technical Report (PDF)** | Formal 17-section aerospace systems engineering report | [Final_Technical_Report.pdf](file:///c:/Users/Sriram%20Krovi/satellite-collision-avoidance-system/Project_Deliverables/Final_Milestone/Final_Technical_Report.pdf) |
| **Final Technical Report (Markdown)** | Markdown master source for the technical report | [Final_Technical_Report.md](file:///c:/Users/Sriram%20Krovi/satellite-collision-avoidance-system/Project_Deliverables/Final_Milestone/Final_Technical_Report.md) |
| **Demonstration Video** | Physics-synchronized 8-milestone 720p HD video | [Final_Demonstration_Video.mp4](file:///c:/Users/Sriram%20Krovi/satellite-collision-avoidance-system/Project_Deliverables/Final_Milestone/Final_Demonstration_Video.mp4) |
| **Demonstration Script** | Narration script, scene breakdown, camera rigging specs | [Final_Demonstration_Script.md](file:///c:/Users/Sriram%20Krovi/satellite-collision-avoidance-system/Project_Deliverables/Final_Milestone/Final_Demonstration_Script.md) |
| **Simulation Results JSON** | Machine-readable quantitative evaluation metrics | [Simulation_Results.json](file:///c:/Users/Sriram%20Krovi/satellite-collision-avoidance-system/Project_Deliverables/Final_Milestone/Simulation_Results.json) |
| **Quality Review Report** | Detailed QC audit report, phrase corrections, and limitations | [FINAL_QUALITY_REVIEW.md](file:///c:/Users/Sriram%20Krovi/satellite-collision-avoidance-system/Project_Deliverables/Final_Milestone/FINAL_QUALITY_REVIEW.md) |
| **Performance Evaluation (Excel)** | Multi-sheet workbook with trajectory time-series | [Performance_Evaluation.xlsx](file:///c:/Users/Sriram%20Krovi/satellite-collision-avoidance-system/Project_Deliverables/Final_Milestone/Performance_Evaluation.xlsx) |
| **Performance Charts** | High-resolution publication plots (6 figures) | [Performance_Charts/](file:///c:/Users/Sriram%20Krovi/satellite-collision-avoidance-system/Project_Deliverables/Final_Milestone/Performance_Charts/) |

### Demonstration Video Specifications
- **File**: `Project_Deliverables/Final_Milestone/Final_Demonstration_Video.mp4`
- **Resolution**: 1280x720 (720p HD)
- **Frame Rate**: 30.0 FPS (1320 frames total)
- **Exact Duration**: **00:44** (44.00 seconds)
- **Codec**: H.264 / AAC
- **File Size**: ~5.76 MB (6,044,828 bytes)

### Reproduction Instructions

#### A. Run Complete Unit & Integration Test Suite (70 Tests)
Verify that all 70 tests across astrodynamics, propulsion, sensors, ML service, and scenarios pass:
```powershell
$env:MPLBACKEND="Agg"
python -m pytest tests D2/tests -v --tb=short
```

#### B. Run Standardized S0–S8 Scenario Suite
Execute the nine benchmark scenarios defined in the technical specification:
```powershell
python Scenarios/scenario_runner.py
```
This generates `Results/scenarios_s0_s8.json` and `Results/scenarios_summary.csv`.

#### C. Run D2 Scientific Regression Test Suite (Baseline 39 Tests)
Verify the historical baseline astrodynamics unit tests pass:
```powershell
$env:MPLBACKEND="Agg"
python -m pytest D2/tests -v --tb=short
```

#### D. Re-generate Performance Charts, Excel & CSV Tables
```powershell
python generate_milestone4_evaluation.py
```

#### E. Re-compile Technical Report PDF
```powershell
python build_technical_report_pdf.py
```

#### F. Re-render Demonstration Video
```powershell
python build_demonstration_video.py
```

#### G. Run In-Engine Interactive Validation in Unreal Engine 5.7
```powershell
& "C:\Program Files\Epic Games\UE_5.7\Engine\Binaries\Win64\UnrealEditor-Cmd.exe" "c:\Users\Sriram Krovi\satellite-collision-avoidance-system\UnrealProject\SatelliteAvoidance.uproject" -ExecutePythonScript="c:\Users\Sriram Krovi\satellite-collision-avoidance-system\UnrealProject\Scripts\verify_milestone3_fixes.py" -stdout -unattended -nopause -nosplash
```

---

## 7. Repository Structure

```text
satellite-collision-avoidance-system/
├── README.md                                    # Master repository documentation
├── .gitignore                                   # Git ignore rules for Unreal & Python
├── test_scenario.py                             # Controlled scenario runner
├── build_technical_report_pdf.py                # Deliverable PDF report compiler
├── build_demonstration_video.py                 # 44-second demonstration video generator
├── generate_milestone4_evaluation.py            # Evaluation metrics and chart generator
├── D1/                                          # Deliverable 1: Conjunction assessment prototype
│   ├── day1_pipeline.py                         # D1 pipeline execution
│   ├── propagator.py                            # SGP4 orbit propagation
│   └── relative_motion.py                       # Relative distance and closest approach
├── D2/                                          # Deliverable 2: Autonomous avoidance manoeuvre planning
│   ├── conjunction/                             # TCA and screening modules
│   ├── dynamics/                                # Two-body gravity, RK4 integrator, variational STM, J2 & drag
│   │   ├── perturbations.py                     # Optional WGS84 J2 harmonic and atmospheric drag
│   │   └── rk4.py                               # RK4 integrator with convergence scaling verification
│   ├── manoeuvres/                              # Avoidance pipeline, candidate generator, optimizer
│   │   └── propulsion.py                        # Tsiolkovsky equation, 7D finite burn, execution dispersion
│   ├── uncertainty/                             # Covariance propagation, Foster (1992) Pc solver
│   ├── visualization/                           # Unreal coordinate transform, JSON simulation payload
│   └── tests/                                   # Astrodynamics unit test suite (45 tests)
├── Sensors/                                     # Sensor & observation simulation subsystem
│   ├── __init__.py
│   └── sensor_models.py                         # Optical, radar, ground station passes, outage injection
├── MLService/                                   # Machine learning inference service & contracts
│   ├── __init__.py
│   ├── schemas.py                               # Versioned JSON schema (v1.0) definitions
│   └── inference_service.py                     # Inference service with frame, freshness & safety gates
├── Scenarios/                                   # Standardized S0–S8 scenario test suite
│   ├── __init__.py
│   ├── s0_circular_orbit.py                     # S0: Circular LEO baseline
│   ├── s1_elliptical_orbit.py                   # S1: Elliptical orbit conservation
│   ├── s2_close_approach.py                     # S2: Close approach conjunction
│   ├── s3_uncertain_conjunction.py               # S3: Covariance & encounter-plane Pc
│   ├── s4_avoidance_burn.py                     # S4: Avoidance burn execution and clearance
│   ├── s5_multiple_debris.py                    # S5: Multiple debris cloud screening
│   ├── s6_perturbed_leo.py                      # S6: Perturbed LEO orbit propagation
│   ├── s7_sensor_outage.py                      # S7: Sensor tracking outage injection
│   ├── s8_safe_pass.py                          # S8: Safe passage non-conjunction
│   └── scenario_runner.py                       # Master scenario runner
├── Evaluation/                                  # Evaluation metrics suite
│   ├── __init__.py
│   └── metrics_suite.py                         # TCA error, miss distance error, fuel, risk reduction
├── tests/                                       # Integration test suite (25 tests)
│   ├── test_sensors.py                          # Sensor subsystem unit tests (5 tests)
│   ├── test_ml_service.py                       # ML inference service unit tests (5 tests)
│   └── test_scenarios.py                        # S0–S8 integration tests (9 tests)
├── Results/                                     # Reproducible benchmark output data
│   ├── scenarios_s0_s8.json                     # Structured JSON results for S0–S8
│   └── scenarios_summary.csv                    # Summary metrics table for S0–S8
├── Project_Deliverables/                        # Authoritative milestone deliverables
│   ├── Final_Milestone/                         # Milestone 4 reports, video, charts, and datasets
│   └── Completion_Work/                         # Technical guide alignment documentation & reports
│       ├── REQUIREMENT_TRACEABILITY.md          # 16-section requirement traceability matrix
│       ├── IMPLEMENTATION_PLAN.md               # Phase-by-phase execution plan
│       ├── BASELINE_AUDIT.md                    # Initial baseline audit document
│       ├── PROGRESS.md & PROGRESS.json          # Live tracking logs
│       ├── FINAL_COMPLETION_REPORT.md           # Comprehensive completion engineering report
│       └── FINAL_COMPLETION_AUDIT.md            # Independent verification audit report
└── UnrealProject/                               # Unreal Engine 5.7.4 visualization project
    ├── Config/                                  # Project engine and game configuration
    ├── Content/                                 # Materials, textures, Earth assets, scenario maps
    ├── Source/SatelliteAvoidance/               # C++ actors, data bridge, HUD widget, visualizers
    │   └── Visualization/                       # USensorVisualizerComponent, orbit actors
    └── Scripts/                                 # Headless Python automation & verification scripts
```

---

## 8. Scope & Limitations (Non-Flight-Readiness Statement)

> [!CAUTION]
> **Research and Simulation Prototype Disclaimer**:
> This software is an academic and engineering prototype designed for concept demonstration, numerical analysis, and simulation visualization. It is **not** certified flight software, nor is it intended for real-time operational collision-avoidance decision making without qualification.

Key simplifications and assumptions:
1. **Orbital Dynamics**: The baseline dynamics model employs two-body Keplerian gravity ($\mu = 3.986004418 \times 10^{14}\text{ m}^3/\text{s}^2$). Advanced perturbations including Earth oblateness ($J_2$) and atmospheric drag with atmospheric co-rotation are available as opt-in force models in `D2/dynamics/perturbations.py`. Higher-degree spherical harmonics ($J_3, J_{2,2}, \dots$) and lunisolar third-body gravity are not included.
2. **Propulsion Modeling**: The reference scenario evaluates an impulsive velocity increment ($\Delta \mathbf{v} = 3.0\text{ m/s}$). Finite-duration thrusting and execution pointing/magnitude uncertainties are modeled in `D2/manoeuvres/propulsion.py` for comparative analysis.
3. **Collision Probability Bounds**: Collision probability ($P_c$) is computed using the Foster (1992) 2D encounter plane integration. Due to the high nominal miss distance ($1563.48\text{ m}$) relative to the combined hard-body radius ($5.00\text{ m}$), evaluated values ($10^{-14}$ to $10^{-22}$) inhabit the asymptotic tail of the Gaussian distribution.
4. **Sensor Simulation**: Ground station tracking, optical line-of-sight, radar range-Doppler, and outage intervals are simulated with parameterized Gaussian measurement noise to decouple ground truth from observation estimates.
5. **Machine Learning Service**: The ML inference service implements the complete versioned JSON schema (v1.0), input sanitization, and physical safety validation gate. In accordance with ethical simulation standards, the inference engine executes an explicit rule-based heuristic baseline rather than fabricated deep learning weights.
