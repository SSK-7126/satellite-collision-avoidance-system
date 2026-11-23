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
| **8** | **Final Encounter Assessment** | Spacecraft passes TCA with confirmed safe clearance exceeding $2,000\text{ m}$. | Status: `PREDICTED SAFE`; Mission completed |

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
