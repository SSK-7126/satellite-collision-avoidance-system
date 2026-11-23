# ICPS Satellite Collision Avoidance System — Standalone Windows Application

**Autonomous Satellite Collision Avoidance & Dual-Model Mission Control**  
**Target Platform:** Windows 64-bit (x64)  
**Build Configuration:** Shipping  
**Engine:** Unreal Engine 5.7.4  
**ML Model:** Kolmogorov-Arnold Network (PyKAN B-Spline `[33, 8, 1]`)  

---

## 1. Quick Launch Instructions

### Option A: One-Click Demonstration Launcher (Recommended)
Double-click `Launch_ICPS_Demonstration.bat` (or run PowerShell):
```powershell
powershell -ExecutionPolicy Bypass -File .\Launch_ICPS_Demonstration.ps1
```
This launcher automatically verifies the local KAN microservice on port 8000, starts the daemon if offline, waits for `/api/v1/health`, opens the application, and manages clean shutdown.

### Option B: Direct Application Execution
Double-click `SatelliteAvoidance.exe` at the root of `SatelliteAvoidance_Windows_Shipping_x64`:
```cmd
SatelliteAvoidance.exe
```
*(If the KAN microservice is offline, the application seamlessly launches in autonomous physics-only mode)*.

---

## 2. Interactive Mission Control Dashboard

The interface provides an interactive aerospace mission-control experience:
- **Free Camera Navigation:** Left mouse drag (orbit), right mouse drag (pan), scroll wheel (smooth zoom), middle click (focus object), `F` key (frame object), `R` key (reset camera).
- **Preset Cameras:** Keys `1` through `6` cycle between Overview, Satellite Chase, Debris Relative, Top-Down Orbital, Encounter Broadside, and Trajectory Plane.
- **Timeline Progression:** 8-step clickable chevron timeline with play/pause (`Spacebar`), reset (`R`), step forward/back (`[` / `]`), and speed adjustments ($1.0\times$ to $200.0\times$).
- **Mission Telemetry Cards (Right Panel):**
  1. *Encounter Information:* Target pair, simulation time, and relative velocity.
  2. *Nominal Prediction:* Nominal TCA ($769.63\text{ s}$), miss distance ($1,563.48\text{ m}$), Foster $P_c$ ($3.9575 \times 10^{-14}$).
  3. *Planned Manoeuvre:* Delta-v ($3.00\text{ m/s}$ $-R$), burn epoch ($169.63\text{ s}$), burn marker.
  4. *Post-Manoeuvre Prediction:* Predicted TCA ($903.03\text{ s}$), miss distance ($2,454.42\text{ m}$), $P_c$ ($1.2387 \times 10^{-22}$).
  5. *KAN ML Risk Assessment:* Predicted $\log_{10}(P_c) = -21.7039$, Estimated $P_c = 1.9776 \times 10^{-22}$, inference latency ($42.2\text{ ms}$), status badge `[PREDICTED LOW]`.
  6. *Dual-Model Verification Gate:* Physics reference (`Foster 2D/3D`), physics $\log_{10}(P_c) = -21.91$, concordance delta $\Delta \log_{10} = 0.20$, verdict badge `[CONCORDANT (LOW RISK)]`.
  7. *Operational Status:* `PREDICTED SAFE` with clearance exceeding threshold.

---

## 3. Demonstration Documentation Index

- **[Demonstration Operator Guide](Demonstration_Operator_Guide.md):** Step-by-step presentation script, milestone descriptions, and fallback demonstration walkthrough.
- **[Backend Startup Instructions](Backend_Startup_Instructions.md):** Manual daemon launch commands, diagnostic endpoints, and REST schema specifications.
- **[Runtime Verification Report](Runtime_Verification_Report.md):** Packaging characteristics, binary sizes, test suite execution logs, and dual-model telemetry tables.

---

## 4. System Requirements

- **Operating System:** Windows 10 / Windows 11 64-bit
- **Graphics:** DirectX 12 compatible GPU (NVIDIA GTX 1060 / AMD Radeon RX 580 / Intel Iris Xe / Arc or newer)
- **DirectX:** Version 12
- **Memory:** 8 GB RAM
- **Storage:** ~500 MB uncompressed (ZIP distribution: 347.25 MB)
