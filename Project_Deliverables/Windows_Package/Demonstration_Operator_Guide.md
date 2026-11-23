# ICPS — Satellite Collision Avoidance System: Operator Demonstration Guide

**Application:** ICPS Mission Control — Autonomous Conjunction Assessment & Avoidance  
**Platform:** Standalone Windows 64-bit Shipping Application (Unreal Engine 5.7.4 + KAN REST Microservice)  
**Classification:** Aerospace Operations & Real-Time Dual-Model Telemetry  

---

## 1. Quick Start (One-Click Launch)

To start the full demonstration with automatic KAN backend initialization:
1. Navigate to `Project_Deliverables/Windows_Package/`.
2. Double-click `Launch_ICPS_Demonstration.bat` (or run `powershell -ExecutionPolicy Bypass -File .\Launch_ICPS_Demonstration.ps1`).
3. The launcher will:
   - Detect or start the KAN microservice on `http://127.0.0.1:8000`.
   - Wait for `/api/v1/health` confirmation.
   - Launch `SatelliteAvoidance.exe` in 1080p windowed mode.
   - Automatically clean up background processes upon game exit.

---

## 2. Interactive Mission Control Dashboard Overview

The HUD interface presents two primary operational panels framing the 3D viewport:

```
+-------------------------------------------------------------------------------------------------------------+
|  [|| Pause] [Reset] [Step -] [Step +] [Speed: 10.0x v] [Camera: Free Camera v] [Free Camera: ON]           |
|                                                                                                             |
|  +--------------------+                                              +-----------------------------------+  |
|  | CAMERA CONTROLS    |                                              | MISSION TELEMETRY                 |  |
|  | Left Drag: Orbit   |                     (3D Earth)               | 1. Encounter Information          |  |
|  | Right Drag: Pan    |                                              | 2. Nominal Prediction             |  |
|  | Scroll: Zoom       |              (Satellite)     (Debris)        | 3. Planned Manoeuvre              |  |
|  | F: Frame Object    |                 [TCA Marker]                 | 4. Post-Manoeuvre Prediction      |  |
|  | R: Reset Camera    |                                              | 5. KAN ML Risk Assessment         |  |
|  +--------------------+                                              | 6. Dual-Model Verification Gate   |  |
|                                                                      | 7. OPERATIONAL STATUS             |  |
|                                                                      +-----------------------------------+  |
+-------------------------------------------------------------------------------------------------------------+
|  DEMONSTRATION TIMELINE (8 STEPS) : [1] [2] [3] [4] [5] [6: Active] [7] [8]    | Step 6 / 8: Impulsive Burn |
+-------------------------------------------------------------------------------------------------------------+
```

---

## 3. Eight-Step Demonstration Walkthrough

Use the bottom timeline chevrons or the **`[`** and **`]`** keys to step through the sequence:

| Step | Milestone | Key Astrodynamic Events | Dual-Model Telemetry |
| :---: | :--- | :--- | :--- |
| **1** | **Initial Orbital Configuration** | Primary satellite in 700 km circular LEO; initial state determination. | KAN: `[INSUFFICIENT_INPUT_DATA]`; Physics: `NOMINAL MONITORING` |
| **2** | **Conjunction Detection** | Catalog screening detects secondary object (`DEBRIS_PIECE_99`) approaching. | Nominal Miss Distance: $1,563.48\text{ m}$; TCA: $T + 769.63\text{ s}$ |
| **3** | **Risk Assessment** | Covariance propagation and Foster 2D/3D numerical evaluation. | Nominal $P_c = 3.9575 \times 10^{-14}$; collision threshold alert |
| **4** | **Manoeuvre Planning** | Optimization solver formulates impulsive $\Delta v = 3.00\text{ m/s}$ in Radial Inward ($-R$). | Manoeuvre Epoch: $T + 169.63\text{ s}$; KAN dual assessment active |
| **5** | **Pre-Burn Approach** | Spacecraft aligns thruster attitude; burn marker ring appears on trajectory. | Pre-burn tracking arc update; telemetry synchronization |
| **6** | **Impulsive Burn Execution** | Simulated burn applied; trajectory branches into green post-manoeuvre spline. | Physics $P_c = 1.2387 \times 10^{-22}$; KAN: $\log_{10} P_c = -21.7039$; Verdict: `[CONCORDANT (LOW RISK)]` |
| **7** | **Post-Burn Trajectory Evolution** | Spacecraft tracks onto altered orbit; separation distance continuously increases. | Miss distance expands to $2,454.42\text{ m}$ ($+890.94\text{ m}$ clearance) |
| **8** | **Final Encounter Assessment** | Spacecraft passes TCA with confirmed safe clearance exceeding $2,000\text{ m}$. | Status: `SIMULATED ENCOUNTER COMPLETED — CLEARANCE ACHIEVED`; Mission demonstration completed |

---

## 4. Camera Navigation & View Presets

### Free Camera Mouse Controls (Default Mode)
- **Left Mouse Drag:** Orbit / Rotate view around current focal point.
- **Right Mouse Drag:** Pan camera laterally and vertically.
- **Mouse Wheel Scroll:** Smooth zoom in / zoom out.
- **Middle Mouse Click:** Focus camera directly onto clicked actor.
- **`F` Key:** Frame and center the currently selected space object.
- **`R` Key:** Reset camera to the default orbital overview perspective.
- **`C` Key:** Cycle sequentially through all available preset cameras.

### Preset Camera Shortcuts
- **Key `1` / Overview:** Wide orbital vantage point showing Earth, primary satellite, debris, and full orbital paths.
- **Key `2` / Satellite Chase:** Elevated chase vantage closely tracking the primary spacecraft body and solar arrays.
- **Key `3` / Debris Relative:** Perspective centered on the incoming debris fragment.
- **Key `4` / Top-Down Orbital:** Plan-view orthogonal projection looking down onto the orbital plane.
- **Key `5` / Encounter Broadside:** Broadside perspective capturing the minimum separation vector.
- **Key `6` / Trajectory Plane:** Edge-on view visualizing orbital inclination and trajectory divergence.

---

## 5. Live Fallback Demonstration (How to Show the Panel)

To demonstrate the system's fault-tolerant aerospace architecture during a live presentation:

1. **Demonstrate Model Concordance (State 2):**
   - Click **Step 6** (`Impulsive Burn Execution`).
   - Point out **Card 5**: KAN predicts $\log_{10}(P_c) = -21.7039$ ($P_c = 1.9776 \times 10^{-22}$) in $42.2\text{ ms}$.
   - Point out **Card 6**: Concordance delta is $\Delta \log_{10} = 0.20$. Gate status shows `[CONCORDANT (LOW RISK)]`.
2. **Demonstrate Insufficient Input Fallback (State 3):**
   - Click **Step 1** (`Initial Orbital Configuration`).
   - Point out **Card 5**: Model status safely indicates `[INSUFFICIENT_INPUT_DATA]`.
   - Point out **Card 6**: Safety verdict indicates `[PHYSICS ONLY (FALLBACK)]`. The physics engine operates autonomously without error.
3. **Demonstrate Backend Disconnection Fallback (State 4):**
   - In a terminal, stop the KAN service (or launch with `-ForcePhysicsOnly`).
   - Advance steps in the dashboard.
   - Point out **Card 5**: Badge displays `[BACKEND UNAVAILABLE]`.
   - Point out **Card 6**: Displays `[PHYSICS ONLY (FALLBACK)]`.
   - Point out that Unreal Engine rendering remains at 60+ FPS with zero hitching or stalling.

---

## 6. Real Satellite Catalogue & SGP4 Multi-Object Monitoring

The ICPS pipeline supports operational space object tracking from CelesTrak and Space-Track data feeds:

### 6.1 Catalogue Search and Retrieval
- **NORAD Catalog Query:** Query payloads and debris by catalogue ID, international designator, or name:
  ```bash
  curl http://127.0.0.1:8000/api/v1/catalogue/search?query=CARTOSAT-3
  ```
- **Active Tracked Objects:** Inspect objects currently registered in the multi-object monitoring pipeline:
  ```bash
  curl http://127.0.0.1:8000/api/v1/catalogue/tracked
  ```
- **Format Support:** Full parsing for Two-Line Element (TLE) checksum verification and CCSDS Orbit Mean-Elements Message (OMM) JSON/CSV formats.

### 6.2 SGP4 Propagation & Frame Transformations
- SGP4 propagation calculates True Equator Mean Equinox (TEME) state vectors.
- Physical coordinates undergo explicit rotation from TEME into Earth-Centered Inertial (ECI J2000):
  $$\mathbf{r}_{\text{J2000}} = \mathbf{R}_{\text{prec}} \mathbf{R}_{\text{nut}} \mathbf{r}_{\text{TEME}}$$
- Preserves physical vector magnitudes with $< 10^{-9}$ relative error.
- Display transformation converts right-handed ECI J2000 (m, m/s) to left-handed Unreal Engine coordinates ($1\text{ uu} = 100\text{ m}$ at scale $0.01$ with $Y$ parity inverted):
  $$X_{\text{UE}} = X_{\text{J2000}} \times 0.01, \quad Y_{\text{UE}} = -Y_{\text{J2000}} \times 0.01, \quad Z_{\text{UE}} = Z_{\text{J2000}} \times 0.01$$

---

## 7. Custom Satellite & Debris Configuration

The Custom Object Configuration module empowers flight operators to define synthetic or uncatalogued objects for collision scenarios:

### 7.1 Creating a Custom Satellite
Satellites can be configured using Keplerian elements or Cartesian state vectors:
```json
POST /api/v1/custom-objects/satellite
{
  "name": "CUSTOM_SURVEILLANCE_SAT_1",
  "input_mode": "KEPLERIAN",
  "keplerian": {
    "semi_major_axis_km": 7078.137,
    "eccentricity": 0.001,
    "inclination_deg": 97.4,
    "raan_deg": 45.0,
    "arg_perigee_deg": 0.0,
    "mean_anomaly_deg": 180.0
  },
  "physical": {
    "dry_mass_kg": 750.0,
    "fuel_mass_kg": 40.0,
    "cross_section_m2": 4.5,
    "hard_body_radius_m": 2.5
  }
}
```

### 7.2 Creating Custom Debris with Unknown Properties
Aerospace-realistic debris often has uncharacterized properties. The system gracefully records provenance:
```json
POST /api/v1/custom-objects/debris
{
  "name": "FRAGMENT_UNKNOWN_DELTA",
  "input_mode": "CARTESIAN",
  "cartesian": {
    "r_j2000_km": [7075.0, 10.0, 5.0],
    "v_j2000_km_s": [0.0, 7.5, 0.5]
  },
  "physical": {
    "estimated_rcs_m2": 0.05,
    "area_to_mass_ratio": null,
    "hard_body_radius_m": 0.8
  }
}
```
*Missing physical parameters are explicitly tagged as `ESTIMATED` or `UNKNOWN` without defaulting unphysically.*

### 7.3 Scenario Isolation and Reset
Operator custom objects are isolated per scenario session. To instantly restore the baseline demonstration scenario (`CARTOSAT-3` vs `DEBRIS_PIECE_99`):
```bash
POST http://127.0.0.1:8000/api/v1/scenario/reset
```

---

## 8. Spacecraft Hardware & Resource-Aware Decision Support

### 8.1 Hardware Registry & Fuel Accounting
Each tracked active spacecraft maintains a detailed hardware record:
- Dry mass, initial propellant, and current propellant mass.
- Thruster specifications: thrust ($N$), specific impulse $I_{sp}$ ($s$), duty cycles, minimum controllable impulse bit.
- Propellant consumption calculation via the Tsiolkovsky rocket equation:
  $$\Delta m_{\text{prop}} = m_0 \left(1 - \exp\left(-\frac{\Delta v}{I_{sp} \cdot g_0}\right)\right)$$
- Delta-v capacity verification: ensures planned burns never exceed remaining propellant reserve.

### 8.2 Manoeuvre Planning and Human Approval Gate
- **RTN Triad Formulation:** Generates candidates across Radial ($\pm R$), Along-Track / Transverse ($\pm T$), and Cross-Track / Normal ($\pm N$).
- **Multi-Constraint Checking:** Evaluates $\Delta v_{\text{max}}$, minimum fuel reserve, and miss distance clearance.
- **Flight Director Workflow:** Manoeuvre proposals require explicit human approval (`PROPOSED` $\to$ `APPROVED` or `REJECTED`) to update the simulated mission proposal. The system functions strictly as a decision-support simulation; no real spacecraft command, control, uplink, or execution interface exists.

---

## 9. Performance Benchmarking Verification (Phase 10)

The system passes comprehensive latency and throughput benchmarks:

| Engine Component | Target Specification | Measured Performance | Margin |
| :--- | :--- | :--- | :--- |
| **SGP4 Propagation Speed** | $> 500\text{ states/sec}$ | **$27,951\text{ states/sec}$** | **$55\times$ target** |
| **Conjunction Shell Filtering** | $> 10,000\text{ checks/sec}$ | **$331,158\text{ checks/sec}$** | **$33\times$ target** |
| **Foster $P_c$ Evaluation** | $< 10\text{ ms/eval}$ | **$0.36\text{ ms/eval}$** | **$27\times$ faster** |
| **Decision Support Solver** | $< 50\text{ ms/candidate}$ | **$0.26\text{ ms}$** | **$190\times$ faster** |
| **Unreal Engine Shipping Frame Rate** | $\ge 60\text{ FPS}$ | **$60\text{ FPS (V-Sync locked)}$** | **Nominal** |
| **Full Repository Test Suite** | $100\%\text{ pass rate}$ | **$125 / 125\text{ tests passing}$** | **$100\%$ green** |
