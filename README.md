# Autonomous Satellite Collision Avoidance System (ICPS)

[![Regression Tests](https://img.shields.io/badge/D2%20Pytest-39%2F39%20Passed-brightgreen)](file:///c:/Users/Sriram%20Krovi/satellite-collision-avoidance-system/D2/tests)
[![Unreal Engine](https://img.shields.io/badge/Unreal%20Engine-5.7.4-blue)](https://www.unrealengine.com/)
[![Astrodynamics Solvers](https://img.shields.io/badge/Backend-Python%20RK4%20%7C%20Foster%20(1992)-orange)](file:///c:/Users/Sriram%20Krovi/satellite-collision-avoidance-system/D2/)
[![Milestone](https://img.shields.io/badge/Milestone-4%20Final%20QC%20Approved-success)](file:///c:/Users/Sriram%20Krovi/satellite-collision-avoidance-system/Project_Deliverables/Final_Milestone/)

A research-grade software system and physics-synchronized 3D visualization platform for autonomous conjunction assessment, risk screening, collision probability evaluation, and impulsive avoidance manoeuvre planning in Low Earth Orbit (LEO).

Developed under the Autonomous Satellite Collision Avoidance System project (ICPS), pairing authoritative Python astrodynamics backends with real-time, telemetry-driven Unreal Engine 5.7.4 visualization.

---

## 1. System Architecture

The project decouples astrodynamic computation from real-time visualization:

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

## 2. Key Scenario Parameters & Evaluation Results

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

## 3. Project Deliverables

All authoritative final deliverables for Milestone 4 and the Quality Control pass are archived in `Project_Deliverables/Final_Milestone/`:

| Deliverable Asset | Description | Format / Path |
| :--- | :--- | :--- |
| **Final Technical Report (PDF)** | Formal 17-section aerospace systems engineering report | [Final_Technical_Report.pdf](file:///c:/Users/Sriram%20Krovi/satellite-collision-avoidance-system/Project_Deliverables/Final_Milestone/Final_Technical_Report.pdf) |
| **Final Technical Report (Markdown)** | Markdown master source for the technical report | [Final_Technical_Report.md](file:///c:/Users/Sriram%20Krovi/satellite-collision-avoidance-system/Project_Deliverables/Final_Milestone/Final_Technical_Report.md) |
| **Demonstration Video** | Physics-synchronized 8-milestone 720p HD video | [Final_Demonstration_Video.mp4](file:///c:/Users/Sriram%20Krovi/satellite-collision-avoidance-system/Project_Deliverables/Final_Milestone/Final_Demonstration_Video.mp4) |
| **Demonstration Script** | Narration script, scene breakdown, camera rigging specs | [Final_Demonstration_Script.md](file:///c:/Users/Sriram%20Krovi/satellite-collision-avoidance-system/Project_Deliverables/Final_Milestone/Final_Demonstration_Script.md) |
| **Simulation Results JSON** | Machine-readable quantitative evaluation metrics | [Simulation_Results.json](file:///c:/Users/Sriram%20Krovi/satellite-collision-avoidance-system/Project_Deliverables/Final_Milestone/Simulation_Results.json) |
| **Quality Review Report** | Detailed QC audit report, phrase corrections, and limitations | [FINAL_QUALITY_REVIEW.md](file:///c:/Users/Sriram%20Krovi/satellite-collision-avoidance-system/Project_Deliverables/Final_Milestone/FINAL_QUALITY_REVIEW.md) |
| **Performance Charts** | High-resolution publication plots (6 figures) | [Performance_Charts/](file:///c:/Users/Sriram%20Krovi/satellite-collision-avoidance-system/Project_Deliverables/Final_Milestone/Performance_Charts/) |

### Demonstration Video Specifications
- **File**: `Project_Deliverables/Final_Milestone/Final_Demonstration_Video.mp4`
- **Resolution**: 1280x720 (720p HD)
- **Frame Rate**: 30.0 FPS (1320 frames total)
- **Exact Duration**: **00:44** (44.00 seconds)
- **Codec**: H.264 / AAC
- **File Size**: ~5.76 MB (6,044,828 bytes)

---

## 4. Verification & Regression Testing

The D2 scientific test suite verifies numerical propagation, coordinate transformations, covariance mapping, collision probability solvers, and payload generation.

To run the regression suite in headless mode:

```powershell
$env:MPLBACKEND="Agg"
python -m pytest D2/tests -v --tb=short
```

**Verification Status**: **39 passed** in ~30 seconds (100% pass rate, zero failures, zero regressions).

### Deliverable Recompilation
- **Technical Report PDF**: `python build_technical_report_pdf.py`
- **Demonstration Video**: `python build_demonstration_video.py`

---

## 5. Scope & Limitations (Non-Flight-Readiness Statement)

> [!CAUTION]
> **Research and Simulation Prototype Disclaimer**:
> This software is an academic and engineering prototype designed for concept demonstration, numerical analysis, and simulation visualization. It is **not** certified flight software, nor is it intended for real-time operational collision-avoidance decision making without qualification.

Key simplifications and assumptions:
1. **Orbital Dynamics**: Dynamics are modeled using two-body Keplerian gravity ($\mu = 3.986004418 \times 10^{14}\text{ m}^3/\text{s}^2$). Perturbations such as Earth oblateness ($J_2$), atmospheric drag, solar radiation pressure, and third-body lunisolar gravity are omitted.
2. **Impulsive Burn Approximation**: The manoeuvre is applied instantaneously as an impulsive velocity increment ($\Delta \mathbf{v}$). Finite-thrust burn transients, attitude slew settling, thruster warm-up, and pointing jitter are not simulated.
3. **Collision Probability Bounds**: Collision probability ($P_c$) is computed using the Foster (1992) 2D encounter plane integration. Due to the high nominal miss distance ($1563.48\text{ m}$) relative to the combined hard-body radius ($5.00\text{ m}$), evaluated values ($10^{-14}$ to $10^{-22}$) inhabit the asymptotic tail of the Gaussian distribution.
4. **Propellant Estimation**: Fuel consumption estimates presented in documentation ($1.39\text{ kg}$) are illustrative analytical figures based on an assumed $1000\text{ kg}$ spacecraft with $I_{\text{sp}} = 220\text{ s}$ hydrazine propulsion, not physical sensor measurements.
