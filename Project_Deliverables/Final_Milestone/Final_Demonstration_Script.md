# Final Demonstration Script: Satellite Collision Avoidance System (ICPS)

**Project:** Autonomous Satellite Collision Avoidance System (ICPS)  
**Deliverable:** Milestone 4 Final Demonstration  
**Engine:** Unreal Engine 5.7.4 (Physics-Synchronized Visualization)  
**Scientific Source:** D1/D2 Python Astrodynamics Solvers  
**Video Asset:** `Project_Deliverables/Final_Milestone/Final_Demonstration_Video.mp4`  
**Video Specs:** 1280x720 (720p HD), 30.0 FPS, H.264 / AAC, 1320 frames, Runtime: 00:44 (44.00 s), File Size: ~5.76 MB  

---

## 1. Sequence Overview & Timeline

| Scene | Milestone Step | Timestamp (Video) | Simulation Time ($t$) | Camera Actor | Active Trajectories | Focus Target |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Opening** | Project Overview | 0:00 – 0:03.0 | Initial Epoch | Static Title Card | N/A | Project Header |
| **Scene 1** | Step 1 / 8 | 0:03.0 – 0:07.5 | $T + 0.0\text{ s}$ | `Camera_Earth_Overview` | Nominal Sat, Debris | Earth Globe & Orbital Plane |
| **Scene 2** | Step 2 / 8 | 0:07.5 – 0:11.5 | $T + 60.0\text{ s}$ | `Camera_Satellite_Detail` | Nominal Sat, Debris | Protected Satellite (CARTOSAT-3) |
| **Scene 3** | Step 3 / 8 | 0:11.5 – 0:15.5 | $T + 120.0\text{ s}$ | `Camera_Debris_Detail` | Nominal Sat, Debris | Secondary Debris (Object99) |
| **Scene 4** | Step 4 / 8 | 0:15.5 – 0:20.5 | $T + 150.0\text{ s} \rightarrow 769.6\text{ s}$ | `Camera_Conjunction_TCA` | Nominal Sat, Debris | Nominal TCA Marker & Miss Vector |
| **Scene 5** | Step 5 / 8 | 0:20.5 – 0:24.5 | $T + 169.6\text{ s}$ | `Camera_Encounter_Overview` | Nominal Sat, Debris | Encounter Region & Planner |
| **Scene 6** | Step 6 / 8 | 0:24.5 – 0:29.5 | $T + 169.6\text{ s}$ | `Camera_Manoeuvre_Burn` | Nominal Sat, Debris, Mod Sat | Impulse Vector & Burn Ring |
| **Scene 7** | Step 7 / 8 | 0:29.5 – 0:34.0 | $T + 300.0\text{ s}$ | `Camera_Trajectories_Divergence` | Nominal Sat, Debris, Mod Sat | Modified Green Orbit Divergence |
| **Scene 8** | Step 8 / 8 | 0:34.0 – 0:39.5 | $T + 903.0\text{ s}$ | `Camera_Earth_Overview` | Nominal Sat, Debris, Mod Sat | Post-Manoeuvre TCA & Clearance |
| **Closing** | Quantitative Summary | 0:39.5 – 0:44.0 | Post-Mission | Static Summary Card | N/A | Evaluation Metrics Table |

---

## 2. Detailed Scene-by-Scene Script & Narration

### Opening: Title & System Identification (0:00 – 0:03.0)
* **Visual Composition:** High-contrast deep space navy card with cyan border accents. Title: *Satellite Collision Avoidance System (ICPS) — Deliverable 4: Quantitative Performance Evaluation & Verification*.
* **On-Screen Metadata:**
  * Scenario: Low Earth Orbit (LEO, 7000 km semi-major axis, $h \approx 621.9\text{ km}$)
  * Primary Satellite: CARTOSAT-3 (`PROTECTED_SAT`, Payload01)
  * Secondary Threat: DEBRIS_PIECE_99 (`SECONDARY_OBJ`, Object99)
  * Solvers: Python RK4 Numerical Propagator, Foster (1992) Collision Probability
  * Visualization: Unreal Engine 5.7.4 (Physics-Synchronized Playback Bridge)
* **Narration / Voiceover:**
  > *"Welcome to the final technical demonstration of the Satellite Collision Avoidance System. This project demonstrates an autonomous conjunction assessment and impulsive avoidance manoeuvre workflow in Low Earth Orbit, combining authoritative Python astrodynamics with high-fidelity real-time visualization in Unreal Engine 5.7."*

---

### Scene 1: Step 1 / 8 — Initialize Orbital Simulation (0:03.0 – 0:07.5)
* **Camera Focus:** `Camera_Earth_Overview` (Location: $115000, -45000, 32000$, FOV: $65^\circ$).
* **Visual Elements:** Photorealistic Earth globe with high-resolution landmasses, oceans, atmospheric limb scattering, cyan nominal orbit path, and red debris trajectory ahead.
* **On-Screen Telemetry:**
  * `Sim Time`: $T + 000.0\text{ s}$
  * `Encounter Pair`: CARTOSAT-3 vs DEBRIS_PIECE_99
  * `Nominal Miss Distance`: $1563.5\text{ m}$ ($1.564\text{ km}$)
  * `Predicted TCA`: $769.63\text{ s}$
  * `Collision Prob (Pc)`: $3.958 \times 10^{-14}$ `[NUMERICAL_UNDERFLOW]`
  * `Status Badge`: `SCREENING TRIGGERED`
* **Narration / Voiceover:**
  > *"At epoch T zero, both space objects are placed in Earth-Centered Inertial coordinates. The primary satellite orbits in a 7000-kilometre circular orbit, with an uncooperative space debris fragment positioned 10 kilometres ahead in the orbital plane."*

---

### Scene 2: Step 2 / 8 — Nominal Trajectory Propagation (0:07.5 – 0:11.5)
* **Camera Focus:** `Camera_Satellite_Detail` (Location: $68250, -1100, 580$, Pitch: $-14.9^\circ$, Yaw: $32.2^\circ$, FOV: $48^\circ$).
* **Visual Elements:** High-detail spacecraft body with golden Kapton insulation, segmented photovoltaic solar arrays, and high-gain communication antenna propagating at $7.546\text{ km/s}$.
* **On-Screen Telemetry:**
  * `Sim Time`: $T + 060.0\text{ s}$
  * `Tracking Status`: ACTIVE KEPLERIAN PROPAGATION
  * `Orbital Altitude`: $621.87\text{ km}$ ($r = 7000.0\text{ km}$)
  * `Orbital Speed`: $7546.05\text{ m/s}$
  * `Status Badge`: `NOMINAL TRACKING`
* **Narration / Voiceover:**
  > *"At sixty seconds, nominal tracking is established. Satellite and debris propagate along two-body Keplerian orbits integrated via Python fourth-order Runge-Kutta numerical dynamics. The primary satellite maintains nominal flight orientation."*

---

### Scene 3: Step 3 / 8 — Conjunction Screening Trigger (0:11.5 – 0:15.5)
* **Camera Focus:** `Camera_Debris_Detail` (Location: $69250, -750, 400$, Pitch: $-22.0^\circ$, Yaw: $40.9^\circ$, FOV: $42^\circ$).
* **Visual Elements:** Irregular tumbling metallic debris fragment approaching the satellite path. The 25-kilometre screening sphere is breached.
* **On-Screen Telemetry:**
  * `Sim Time`: $T + 120.0\text{ s}$
  * `Secondary Threat`: DEBRIS_PIECE_99
  * `Relative Approach Speed`: $13.234\text{ m/s}$
  * `Screening Distance`: $18.42\text{ km}$ ($< 25.0\text{ km}$ threshold)
  * `Lead Time to TCA`: $649.6\text{ s}$ ($\sim 10.8\text{ min}$)
  * `Status Badge`: `CONJUNCTION ALERT`
* **Narration / Voiceover:**
  > *"At one hundred twenty seconds, the conjunction screening filter is breached as relative separation drops below twenty-five kilometres. The autonomous flight computer identifies a close approach candidate with an impending encounter."*

---

### Scene 4: Step 4 / 8 — Encounter Assessment & Risk Metrics (0:15.5 – 0:20.5)
* **Camera Focus:** `Camera_Conjunction_TCA` (Location: $47256.7, -51624.4, 14.0$, FOV: $40^\circ$).
* **Visual Elements:** Encounter plane geometry with calibrated translucent encounter disc, yellow-orange miss-distance connector line, and debris position at nominal TCA ($769.63\text{ s}$).
* **On-Screen Telemetry:**
  * `Sim Time`: $T + 150.0\text{ s}$ (Predicting TCA at $769.63\text{ s}$)
  * `Nominal Miss Distance`: $1563.5\text{ m}$ (CRITICAL $< 2000\text{ m}$ operational limit)
  * `Collision Prob (Pc)`: $3.958 \times 10^{-14}$ `[NUMERICAL_UNDERFLOW]`
  * `Hard-Body Radius`: $5.00\text{ m}$ (Combined spherical envelope)
  * `Status Badge`: `CRITICAL RISK DETECTED`
* **Narration / Voiceover:**
  > *"At one hundred fifty seconds, risk metrics are evaluated. The unmanoeuvred nominal encounter yields a miss distance of 1563.5 metres—violating the 2000-metre project-defined operational threshold. Although the formal probability of collision is 3.96 times ten to the minus fourteen due to the small hard-body radius of 5.0 metres relative to covariance dispersion, the geometric violation triggers mandatory avoidance planning."*

---

### Scene 5: Step 5 / 8 — Autonomous Avoidance Planning (0:20.5 – 0:24.5)
* **Camera Focus:** `Camera_Encounter_Overview` (Location: $68900, 170, 420$, FOV: $44^\circ$).
* **Visual Elements:** Wide orbital geometry showing the candidate manoeuvre trade space.
* **On-Screen Telemetry:**
  * `Sim Time`: $T + 169.6\text{ s}$
  * `Selected Impulse`: `MAN_006_-R_3.00mps_T170s`
  * `Delta-V Magnitude`: $3.00\text{ m/s}$ in Radial Inward ($-R$)
  * `Lead Time to Nominal TCA`: $600.0\text{ s}$ ($10.0\text{ minutes}$)
  * `Status Badge`: `MANOEUVRE PLANNED`
* **Narration / Voiceover:**
  > *"At 169.6 seconds, ten minutes prior to nominal TCA, the autonomous planner evaluates candidate impulses. It selects an optimal 3.0 metre-per-second burn in the negative radial direction. This inward impulse induces orbital eccentricity ($e \approx 0.0004$), creating coupled radial altitude displacement and along-track phasing to open clearance at closest approach, while leaving semi-major axis and orbital period essentially unchanged ($\Delta a \approx 1.11\text{ m}$, $\Delta T \approx 1.38\text{ ms}$)."*

---

### Scene 6: Step 6 / 8 — Impulsive Burn Execution (0:24.5 – 0:29.5)
* **Camera Focus:** `Camera_Manoeuvre_Burn` (Location: $69977.8, -14006.6, 650.0$, Pitch: $-20.9^\circ$, Yaw: $132.6^\circ$, FOV: $48^\circ$).
* **Visual Elements:** Spacecraft thruster plume visualization, glowing orange burn ring, and directional Delta-V vector pointing inward toward Earth center. Satellite state switches to `ManoeuvredFlight`.
* **On-Screen Telemetry:**
  * `Sim Time`: $T + 169.6\text{ s}$
  * `Applied Delta-V Vector`: $[-3.00, 0.00, 0.00]\text{ m/s}$ (RTN)
  * `ECI Delta-V Vector`: $[-2.95, -0.55, 0.00]\text{ m/s}$
  * `Velocity Shift`: Continuous position, discontinuous velocity
  * `Status Badge`: `BURN EXECUTED`
* **Narration / Voiceover:**
  > *"At exactly T plus 169.6 seconds, the impulsive burn executes. The velocity vector instantaneously rotates in inertial space, while orbital position remains continuous. The modified trajectory immediately activates."*

---

### Scene 7: Step 7 / 8 — Modified Trajectory & Covariance Drift (0:29.5 – 0:34.0)
* **Camera Focus:** `Camera_Trajectories_Divergence` (Location: $68900, 170, 420$, FOV: $62^\circ$).
* **Visual Elements:** Vibrant green modified trajectory spline splitting from the nominal cyan path. The spatial separation steadily grows as the spacecraft drifts ahead in orbit phase.
* **On-Screen Telemetry:**
  * `Sim Time`: $T + 300.0\text{ s}$
  * `Instant Trajectory Deviation`: $1386.4\text{ m}$ (Accumulating)
  * `Peak Trajectory Deviation`: $3008.5\text{ m}$ (at $T+1000\text{ s}$)
  * `Separation at Nom TCA`: $2019.0\text{ m}$
  * `Status Badge`: `TRAJECTORY DIVERGING`
* **Narration / Voiceover:**
  > *"At three hundred seconds, the satellite drifts along its modified orbit. The trajectory deviation accumulates safely away from the nominal path, reaching over two kilometres of separation at the nominal encounter epoch."*

---

### Scene 8: Step 8 / 8 — Post-Manoeuvre Verification & Safety Margin (0:34.0 – 0:39.5)
* **Camera Focus:** `Camera_Earth_Overview` (Location: $115000, -45000, 32000$, FOV: $65^\circ$).
* **Visual Elements:** Full Earth overview displaying the resolved encounter. The debris passes through the original nominal encounter zone while the protected satellite clears the point ahead of schedule.
* **On-Screen Telemetry:**
  * `Sim Time`: $T + 903.0\text{ s}$ (Post-Manoeuvre TCA)
  * `Post-Manoeuvre Miss Distance`: $2454.4\text{ m}$ ($+890.9\text{ m}$ / $+57.0\%$ increase)
  * `New TCA Epoch`: $903.03\text{ s}$ (Shift: $+133.40\text{ s}$)
  * `Post-Manoeuvre Pc`: $1.239 \times 10^{-22}$ ($\log_{10} P_c = -21.91$)
  * `Risk Reduction Factor`: $3.195 \times 10^8 \times$ reduction in calculated $P_c$
  * `Status Badge`: `RESOLVED SAFE`
* **Narration / Voiceover:**
  > *"At 903.0 seconds, the new time of closest approach is reached—delayed by 133.4 seconds. The miss distance has increased from 1563.5 to 2454.4 metres—an improvement of 890.9 metres or 57.0 percent, satisfying the operational safety threshold in this simulated scenario. The calculated collision probability drops to 1.24 times ten to the minus twenty-two: an attenuation of eight and a half orders of magnitude."*

---

### Closing: Performance Evaluation Summary & Conclusions (0:39.5 – 0:44.0)
* **Visual Composition:** Dark navy executive summary card displaying quantitative performance metrics, test suite verification status (39/39 passed), and project conclusions.
* **On-Screen Summary Table:**
  * Miss Distance Gain: $+890.94\text{ m}$ ($+56.985\%$)
  * TCA Delay Shift: $+133.40\text{ s}$
  * Probability Reduction: $8.50$ decades ($3.195 \times 10^8 \times$ reduction in calculated $P_c$)
  * Delta-V Investment: $3.00\text{ m/s}$ in $-R$
  * Software Verification: 39/39 Python Unit Tests Passed | UE 5.7.4 Engine Validated
* **Narration / Voiceover:**
  > *"In summary, the autonomous avoidance manoeuvre achieved an 890-metre clearance gain and an 8.5-decade reduction in calculated collision probability with a single 3-metre-per-second impulse. This concludes the Milestone 4 demonstration of the Satellite Collision Avoidance System."*

---

## 3. Camera Rigging & Unreal Engine Capture Settings

For automated re-recording or manual verification inside Unreal Editor, use the following scene camera parameters:

| Camera Name | World Location $(X, Y, Z)$ [uu] | Rotation $(\text{Pitch}, \text{Yaw}, \text{Roll})$ [deg] | Field of View [deg] | Target Purpose |
| :--- | :--- | :--- | :--- | :--- |
| `Camera_Earth_Overview` | `(115000.0, -45000.0, 32000.0)` | `(-14.5, 158.6, 0.0)` | $65.0^\circ$ | Global orbital context, Earth limb, full trajectory arcs |
| `Camera_Satellite_Detail` | `(68250.0, -1100.0, 580.0)` | `(-14.9, 32.2, 0.0)` | $48.0^\circ$ | Spacecraft bus, solar panel segmentation, antenna details |
| `Camera_Debris_Detail` | `(69250.0, -750.0, 400.0)` | `(-22.0, 40.9, 0.0)` | $42.0^\circ$ | Threat debris fragment inspection |
| `Camera_Encounter_Overview` | `(68900.0, 170.0, 420.0)` | `(-20.5, -11.3, 0.0)` | $44.0^\circ$ | Conjunction approach region and candidate planning space |
| `Camera_Conjunction_TCA` | `(47256.7, -51624.4, 14.0)` | `(-20.2, -107.3, 0.0)` | $40.0^\circ$ | Nominal encounter plane, miss distance connector, TCA marker |
| `Camera_Manoeuvre_Burn` | `(69977.8, -14006.6, 650.0)` | `(-20.9, 132.6, 0.0)` | $48.0^\circ$ | Impulse execution point, burn ring, Delta-V vector |
| `Camera_Trajectories_Divergence` | `(68900.0, 170.0, 420.0)` | `(-20.5, -11.3, 0.0)` | $62.0^\circ$ | Separation of nominal (cyan) and modified (green) trajectories |

### Reproducible Video Re-encoding Command
To re-generate `Final_Demonstration_Video.mp4` at any time from project source:
```bash
python build_demonstration_video.py
```
This script validates frame dimensions, blends cross-dissolves, renders on-screen HUD text, and writes an optimized H.264 MP4 file to `Project_Deliverables/Final_Milestone/Final_Demonstration_Video.mp4`.
