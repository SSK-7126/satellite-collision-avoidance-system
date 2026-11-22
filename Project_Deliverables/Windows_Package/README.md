# ICPS Satellite Collision Avoidance System — Standalone Windows Application

Autonomous Satellite Collision Avoidance Demonstration
**Target Platform:** Windows 64-bit (x64)
**Build Configuration:** Shipping
**Engine:** Unreal Engine 5.7.4

---

## 1. Quick Launch Instructions

1. **Extract the ZIP Archive:**
   Extract `SatelliteAvoidance_Windows_Shipping_x64.zip` to any local directory on your Windows computer (e.g. `C:\ICPS_App\` or `D:\SatelliteAvoidance\`).
2. **Launch the Application:**
   Double-click `SatelliteAvoidance.exe` located at the root of the extracted folder:
   ```
   [Extracted Folder]\SatelliteAvoidance.exe
   ```
   *(Alternatively, run `SatelliteAvoidance\Binaries\Win64\SatelliteAvoidance-Win64-Shipping.exe`)*
3. **No Unreal Editor or Python Required:**
   The application is fully compiled and packaged as a standalone native Windows 64-bit application. It runs directly on the target machine without Unreal Editor or Python installed.

---

## 2. Interactive Demonstration Controls

The simulation automatically starts in Play mode at 5.0x real-time speed. You can interact with the simulation, timeline, and cameras using the following keyboard shortcuts:

| Key | Action | Description |
|:---|:---|:---|
| **Spacebar** | **Play / Pause** | Toggle playback clock between active progression and paused state |
| **R** | **Reset Simulation** | Reset clock to initial epoch ($T=0.0\text{ s}$) and re-initialize nominal trajectory |
| **C** | **Cycle Camera View** | Smoothly blend across all 6 cinematic and scientific camera perspectives |
| **Up Arrow** | **Increase Speed** | Accelerate playback through tiers: $1\times \rightarrow 2\times \rightarrow 5\times \rightarrow 10\times \rightarrow 25\times \rightarrow 50\times \rightarrow 100\times \rightarrow 200\times$ |
| **Down Arrow** | **Decrease Speed** | Decelerate playback speed |
| **Right Arrow** | **Step Forward** | Advance to next milestone demonstration step |
| **Left Arrow** | **Step Backward** | Step backward to previous milestone demonstration step |
| **Keys 1 – 8** | **Direct Milestone Jump** | Instantly jump to Step 1 through Step 8 with synchronized camera framing |
| **Numpad 1 – 8** | **Direct Milestone Jump** | Numpad equivalents for direct milestone navigation |
| **Alt + Enter** | **Toggle Fullscreen** | Toggle between windowed and borderless fullscreen mode |
| **Alt + F4** | **Exit Application** | Close and cleanly shut down the application |

---

## 3. Eight-Step Demonstration Sequence

| Step | Epoch | Headline | Assigned Camera | Key Telemetry & Astrodynamic Event |
|:---:|:---:|:---|:---|:---|
| **1** | $T+0.0\text{ s}$ | Initialize Orbital Simulation | `Camera_Earth_Overview` | Nominal orbit monitoring; Instantaneous separation: $10,000\text{ m}$; Predicted nominal TCA miss: $1,563.48\text{ m}$ |
| **2** | $T+60.0\text{ s}$ | Nominal Tracking & Observation | `Camera_Satellite_Detail` | Optical LOS sensor lock; Instantaneous separation: $9,379.6\text{ m}$ |
| **3** | $T+120.0\text{ s}$ | Conjunction Detection | `Camera_Encounter_Overview` | Critical risk threshold exceeded ($P_c = 3.958 \times 10^{-14}$); Planned burn announced |
| **4** | $T+150.0\text{ s}$ | Conjunction Geometry Assessment | `Camera_Conjunction_TCA` | Focus on closest-approach point; Predicted nominal miss: $1,563.48\text{ m}$ |
| **5** | $T+169.6\text{ s}$ | Manoeuvre Readiness | `Camera_Satellite_Detail` | Satellite pre-burn posture; Instantaneous separation: $8,149.4\text{ m}$ |
| **6** | $T+169.6\text{ s}$ | Manoeuvre Execution | `Camera_Manoeuvre_Burn` | Radial inward burn applied ($\Delta v = 3.00\text{ m/s}$, $-R$); Modified orbit initiated |
| **7** | $T+300.0\text{ s}$ | Post-Manoeuvre Divergence | `Camera_Encounter_Overview` | Trajectory divergence in progress; Instantaneous separation: $6,648.5\text{ m}$ |
| **8** | $T+903.0\text{ s}$ | Safe Clearance Achieved | `Camera_Earth_Overview` | Post-manoeuvre TCA achieved; Instantaneous separation: $4,525.72\text{ m}$; Post-burn miss distance: $2,454.42\text{ m}$ (Clearance resolved $> 2,000\text{ m}$ threshold) |

---

## 4. Telemetry HUD Display Guide

The telemetry panel (top-left) displays synchronized flight data derived from the authoritative scientific payload:
- **Simulation Time:** Elapsed scenario seconds from initial epoch.
- **Encounter Pair:** Protected Satellite (`CARTOSAT-3` / `ProtectedSatellite_Payload01`) vs. Tracked Debris (`DEBRIS_PIECE_99` / `SecondaryDebris_Object99`).
- **Nominal TCA & Miss Distance:** Nominal time of closest approach ($769.63\text{ s}$) and nominal miss distance ($1,563.48\text{ m}$).
- **Instantaneous Separation vs. Predicted TCA Miss Distance:**
  *Note:* Instantaneous separation is the current distance between satellite and debris. Predicted TCA miss distance is the minimum clearance predicted at the conjunction epoch ($T=903.03\text{ s}$). At Step 8, instantaneous separation is $\approx 4,525.72\text{ m}$, while the post-manoeuvre TCA miss distance is $2,454.42\text{ m}$.
- **Collision Probability ($P_c$):** Calculated via Foster (1992) 2D probability solver. Reduced from $3.958 \times 10^{-14}$ (nominal) to $1.239 \times 10^{-22}$ (post-manoeuvre).
- **Safety Status:** Clearly displays risk status transition from *CRITICAL RISK* to *AVOIDANCE RESOLVED*.

---

## 5. System Requirements

### Minimum Requirements:
- **Operating System:** Windows 10 64-bit (Version 1909 or higher) or Windows 11 64-bit
- **Processor:** Intel Core i5 / AMD Ryzen 5 (4 physical cores or higher)
- **Memory:** 8 GB RAM
- **Graphics:** DirectX 12 compatible GPU (NVIDIA GTX 1060 / AMD Radeon RX 580 / Intel Iris Xe / Arc or newer)
- **DirectX:** Version 12 (DirectX 12 feature level 11_0 or 12_0)
- **Storage:** 1.0 GB available disk space (Uncompressed package size: $\approx 468\text{ MB}$)

### Runtime Dependencies:
- **Microsoft Visual C++ 2015–2022/2026 Redistributable (x64)**
  If not already installed on the target computer, download and install the official Microsoft VC++ Redistributable:
  `https://aka.ms/vs/17/release/vc_redist.x64.exe`
- **DirectX 12 Runtime:** Standard with Windows 10 / Windows 11 updates.
- **Bundled Libraries:** `D3D12Core.dll`, `DirectML.dll`, `tbb12.dll`, and `tbbmalloc.dll` are included within the packaged directory.

---

## 6. Known Characteristics & Notes

- **Initial Load Time:** The first launch initializes the D3D12 shader pipeline and pre-caches GPU assets; subsequent launches start faster.
- **Data Integrity:** Simulation trajectory and conjunction values are loaded directly from `SatelliteAvoidance/Content/Data/unreal_simulation_payload.json`.
- **Standalone Execution:** No internet connection, Python environment, or development SDK is required.
