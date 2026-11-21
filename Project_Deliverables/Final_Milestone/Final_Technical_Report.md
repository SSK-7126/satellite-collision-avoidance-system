# AUTONOMOUS SATELLITE COLLISION AVOIDANCE SYSTEM (ICPS)
## Final Technical Report & Quantitative Performance Evaluation
**Deliverable:** Milestone 4 Final Technical Documentation  
**Project:** Satellite Collision Avoidance System (ICPS)  
**Engine:** Unreal Engine 5.7.4 (Physics-Synchronized Visualization & Playback)  
**Scientific Engine:** Python Astrodynamics Solvers (D1/D2)  
**Date:** November 21, 2026  
**Document Classification:** Reference Scenario Evaluation & Performance Validation  

> [!NOTE]
> **Operational Scope Notice:** The scenario evaluated in this report is a frozen, physics-based simulation scenario developed strictly for system testing and demonstration. It does not represent live operational tracking, real-world collision warning, or spacecraft command execution on the physical CARTOSAT-3 satellite or operational ground segment.

---

## Table of Contents
1. [Abstract](#1-abstract)
2. [Problem Statement](#2-problem-statement)
3. [Project Objectives](#3-project-objectives)
4. [System Architecture](#4-system-architecture)
5. [D1 Baseline Debris Simulation](#5-d1-baseline-debris-simulation)
6. [D2 Conjunction Detection](#6-d2-conjunction-detection)
7. [TCA and Miss-Distance Estimation](#7-tca-and-miss-distance-estimation)
8. [Covariance Propagation and Collision Probability Estimation](#8-covariance-propagation-and-collision-probability-estimation)
9. [Autonomous Avoidance Manoeuvre Planning](#9-autonomous-avoidance-manoeuvre-planning)
10. [Python-to-Unreal Data Bridge & Integration](#10-python-to-unreal-data-bridge--integration)
11. [Interactive 3D Visualization & Telemetry HUD](#11-interactive-3d-visualization--telemetry-hud)
12. [Quantitative Performance Evaluation](#12-quantitative-performance-evaluation)
13. [Results and Comparative Discussion](#13-results-and-comparative-discussion)
14. [Current System Limitations](#14-current-system-limitations)
15. [Future Work & Roadmap](#15-future-work--roadmap)
16. [Conclusion](#16-conclusion)
17. [References](#17-references)

---

## 1. Abstract
The exponential proliferation of orbital debris in Low Earth Orbit (LEO) presents an operational hazard to active satellite infrastructure and human spaceflight. Conventional collision avoidance workflows rely heavily on ground-in-the-loop screening, manual orbital determination, and ephemeris analysis, introducing operational latency that is ill-suited to congested mega-constellation regimes. This report presents an **engineering evaluation of the reference scenario** for the **Autonomous Satellite Collision Avoidance System (ICPS)**. 

The system couples a rigorous, authoritative Python astrodynamics backend (Deliverables D1/D2) with an interactive, real-time 3D telemetry and playback visualization layer implemented in Unreal Engine 5.7.4. The scientific engine integrates two-body Keplerian orbital mechanics via a fourth-order Runge-Kutta (RK4) integrator, performs conjunction screening against close-approach thresholds, estimates the Time of Closest Approach (TCA) via iterative root-finding, propagates positional error covariances, and computes collision probabilities ($P_c$) using the Foster (1992) method. 

When a critical conjunction is detected—in this scenario, a predicted nominal miss distance of $1563.48\text{ m}$ against a project-defined $2000.0\text{ m}$ operational safety threshold—an autonomous planning algorithm optimizes an impulsive manoeuvre. A single $3.00\text{ m/s}$ impulse executed in the radial inward ($-R$) direction $600\text{ s}$ prior to nominal TCA successfully expands the predicted miss distance to $2454.42\text{ m}$ (a $+56.985\%$ improvement of $+890.94\text{ m}$) and shifts predicted TCA by $+133.40\text{ s}$. This manoeuvre reduces calculated collision probability from $3.958 \times 10^{-14}$ ($\log_{10} P_c = -13.40$) down to $1.239 \times 10^{-22}$ ($\log_{10} P_c = -21.91$), representing an $8.50$ order-of-magnitude reduction (approximately a $3.195 \times 10^8$ reduction in calculated collision probability). 39 automated regression tests passed in the authoritative Python suite, and Unreal Engine renders the physics-synchronized playback across an eight-step demonstration sequence.

---

## 2. Problem Statement
The tracked orbital population in Low Earth Orbit has grown significantly over past decades, driven by satellite fragmentation events, upper-stage breakups, and constellation deployment. Uncooperative debris fragments travel at orbital velocities exceeding $7.5\text{ km/s}$, where kinetic impact energy presents catastrophic structural risk.

Contemporary operational workflows face specific challenges:
1. **Decision Latency:** Conjunction Data Messages (CDMs) issued by surveillance networks often provide short lead windows ($24\text{ to }72\text{ hours}$), which can be compressed by ground-station pass schedules, tracking update intervals, and operator coordination chains.
2. **Alert Volume:** Conservative screening volumes generate frequent conjunction alerts across active constellations. Operators must evaluate orbital safety against propellant consumption and mission disruption.
3. **Visualization Interfaces:** Conjunction analysis often relies on tabular ephemeris data, 2D orbital plots, or covariance ellipsoids. An interactive, spatially contextual 3D visualization aids engineering review of relative trajectories, encounter geometry, and manoeuvre clearance.

---

## 3. Project Objectives
The objective of this project is to implement and validate an integrated autonomous satellite collision avoidance pipeline meeting the following criteria:

* **Scientific Rigour:** Implement authoritative numerical orbital propagation, conjunction filtering, numerically estimated TCA using Brent's minimization method, covariance propagation, and probability integration entirely within tested Python astrodynamic solvers using two-body Keplerian orbital mechanics.
* **Autonomous Decision-Making:** Formulate an automated manoeuvre planner capable of evaluating candidate impulse catalogs across along-track, radial, and cross-track directions, selecting an optimal manoeuvre that satisfies the defined clearance envelope.
* **Physics-Synchronized Visualization:** Export authoritative trajectory samples and metadata via an open JSON bridge to Unreal Engine 5.7.4, enforcing a strict separation of concerns where Unreal Engine functions strictly as a visualization and telemetry playback layer without modifying or inventing scientific state.
* **Interactive Mission Demonstration:** Provide an intuitive eight-step demonstration sequence with dynamic camera framing, interactive time dilation controls, and a real-time Slate telemetry HUD displaying authoritative astrodynamics metrics.
* **Verification & Testing:** Rigorously verify collision avoidance efficacy, trajectory divergence, manoeuvre control effort, with 39 automated regression tests passed.

---

## 4. System Architecture
The system architecture enforces a decoupled, modular design divided into two primary subsystems: the **Scientific Computation Core (Python)** and the **Real-Time Visualization & HUD Layer (Unreal Engine 5.7.4)**.

```
+-----------------------------------------------------------------------------------+
|                        SCIENTIFIC COMPUTATION CORE (PYTHON)                       |
+-----------------------------------------------------------------------------------+
|  [D1 Baseline Simulation]                                                         |
|    - RK4 Integrator (dt = 0.1s)                                                   |
|    - Two-Body Orbital Dynamics (mu = 3.986004418e14 m^3/s^2)                      |
|                                                                                   |
|  [D2 Conjunction & Avoidance Pipeline]                                            |
|    - Geometry & Screening Filter (Screening distance threshold: 25 km)             |
|    - Brent's Method Numerical TCA Root-Finding                                    |
|    - Orbital Covariance State Transition Matrix (STM) Propagation                 |
|    - Foster (1992) 2D Probability Integration (Pc & log10(Pc))                    |
|    - Autonomous Manoeuvre Planner (Catalog search, Delta-V optimization)           |
|                                                                                   |
|  [Simulation Exporter (D2_simulation_exporter.py)]                                |
|    - ECI J2000 to Unreal Engine Left-Handed Coordinate Conversion                 |
|    - 501 Equidistant Trajectory Samples (t = 0 to 1000s, dt = 2s)                 |
|    - Eight-Step Demonstration Sequence Definition & Astrodynamics Metadata        |
+-----------------------------------------------------------------------------------+
                                         |
                                         | JSON Data Bridge
                                         v (unreal_simulation_payload.json)
+-----------------------------------------------------------------------------------+
|                     REAL-TIME PLAYBACK & HUD LAYER (UNREAL ENGINE 5.7)            |
+-----------------------------------------------------------------------------------+
|  [USimulationDataBridge]                                                          |
|    - Deserializes JSON payload into native C++ structs                            |
|    - Cubic Spline Interpolation for smooth sub-step query                         |
|                                                                                   |
|  [AOrbitSimulationManager]                                                        |
|    - Simulation master clock, time dilation (1x - 200x), play/pause/reset         |
|    - State machine managing eight demonstration milestones                        |
|    - Deterministic camera director (Camera_Earth_Overview, TCA, Burn, etc.)       |
|                                                                                   |
|  [Actors & Visualizers]                                                           |
|    - AEarthActor (Realistic globe, Rayleigh/Mie limb atmosphere, space sky)       |
|    - ASatelliteActor (Gold Kapton bus, blue segmented solar arrays, antenna)      |
|    - ADebrisActor (Irregular tumbling metallic fragment)                          |
|    - AOrbitPathActor (Cyan nominal, red debris, green modified spline paths)      |
|    - AConjunctionVisualizer (Encounter disc, miss distance connector)             |
|    - AManoeuvreVisualizer (Impulse vector arrow, burn execution ring)             |
|                                                                                   |
|  [UAvoidanceInfoPanelWidget (Slate HUD)]                                          |
|    - Real-time telemetry: Simulation time, TCA, Miss Distance, Relative Speed     |
|    - Authoritative Collision Probability: Scientific notation & log10(Pc)         |
|    - Asymptotic tail underflow status preservation                                |
+-----------------------------------------------------------------------------------+
```

---

## 5. D1 Baseline Debris Simulation
The foundational simulation establishes two-body Newtonian orbital dynamics for celestial motion around the Earth:

$$\ddot{\mathbf{r}} = -\frac{\mu}{\|\mathbf{r}\|^3} \mathbf{r}$$

where $\mu = 3.986004418 \times 10^{14}\text{ m}^3/\text{s}^2$ is Earth's standard gravitational parameter and $\mathbf{r} = [x, y, z]^T$ is the spacecraft position vector in Earth-Centered Inertial (ECI J2000) coordinates.

Numerical integration uses a classical fourth-order Runge-Kutta (RK4) algorithm with fixed step size $\Delta t = 0.1\text{ s}$:

$$\mathbf{y}_{n+1} = \mathbf{y}_n + \frac{\Delta t}{6} \left(\mathbf{k}_1 + 2\mathbf{k}_2 + 2\mathbf{k}_3 + \mathbf{k}_4\right)$$

where $\mathbf{y} = [\mathbf{r}^T, \mathbf{v}^T]^T \in \mathbb{R}^6$ is the orbital state vector.

The primary protected satellite (`CARTOSAT-3`) is simulated in a circular orbit at altitude $h = 621.87\text{ km}$ ($r_0 = 7000.0\text{ km}$), circular orbital velocity $v_0 = \sqrt{\mu / r_0} = 7546.053\text{ m/s}$, and orbital period $T = 2\pi \sqrt{r_0^3 / \mu} = 5828.53\text{ s}$ ($97.14\text{ min}$). The secondary debris object (`DEBRIS_PIECE_99`) is placed in a near-coplanar orbit offset $10\text{ km}$ ahead in orbital phase with an intentional relative velocity offset to produce a controlled close approach.

---

## 6. D2 Conjunction Detection
The conjunction detection pipeline operates as a multi-tier screening system:

1. **Broad-Phase Distance Filter:** At each propagation step, the Euclidean separation is evaluated:
   $$d(t) = \|\mathbf{r}_{\text{sat}}(t) - \mathbf{r}_{\text{deb}}(t)\|$$
   An alert is triggered when $d(t) < D_{\text{screen}} = 25000.0\text{ m}$ ($25.0\text{ km}$).
2. **Conjunction Event Detection:** When the relative velocity vector $\mathbf{v}_{\text{rel}} = \mathbf{v}_{\text{sat}} - \mathbf{v}_{\text{deb}}$ satisfies:
   $$\frac{d}{dt} \left(d^2(t)\right) = 2 \, \mathbf{r}_{\text{rel}}(t) \cdot \mathbf{v}_{\text{rel}}(t) = 0 \quad \text{with} \quad \mathbf{r}_{\text{rel}} \cdot \mathbf{a}_{\text{rel}} + \|\mathbf{v}_{\text{rel}}\|^2 > 0$$
   the presence of a local minimum separation is identified.

---

## 7. TCA and Miss-Distance Estimation
To identify the Time of Closest Approach without step-size discretization limits, the system executes an iterative one-dimensional numerical minimization of the relative distance function $d(t)$ to obtain a **numerically estimated TCA using Brent's minimization method** with a convergence tolerance of $10^{-6}\text{ s}$:

$$t_{\text{TCA}} = \arg \min_{t \in [t_{\text{entry}}, t_{\text{exit}}]} \|\mathbf{r}_{\text{sat}}(t) - \mathbf{r}_{\text{deb}}(t)\|$$

At $t_{\text{TCA}}$, the authoritative miss distance is evaluated as:

$$d_{\text{miss}} = \|\mathbf{r}_{\text{rel}}(t_{\text{TCA}})\|$$

For the nominal, unmanoeuvred conjunction:
* **Nominal TCA ($t_{\text{TCA, nom}}$):** $769.63197\text{ s}$
* **Nominal Miss Distance ($d_{\text{miss, nom}}$):** $1563.4763\text{ m}$ ($1563.48\text{ m}$)
* **Relative Speed at TCA ($v_{\text{rel}}$):** $13.234\text{ m/s}$

Because $d_{\text{miss, nom}} < D_{\text{threshold}} = 2000.0\text{ m}$, the event is flagged as a `CRITICAL_COLLISION_ALERT`, mandating avoidance action.

---

## 8. Covariance Propagation and Collision Probability Estimation
To evaluate formal collision risk, state error covariance matrices for both objects ($\mathbf{P}_{\text{sat}}, \mathbf{P}_{\text{deb}} \in \mathbb{R}^{6 \times 6}$) are propagated to TCA using the State Transition Matrix $\mathbf{\Phi}(t_{\text{TCA}}, t_0)$:

$$\mathbf{P}(t_{\text{TCA}}) = \mathbf{\Phi}(t_{\text{TCA}}, t_0) \, \mathbf{P}(t_0) \, \mathbf{\Phi}^T(t_{\text{TCA}}, t_0)$$

The relative position covariance in the encounter plane is combined:

$$\mathbf{C} = \mathbf{P}_{\text{pos, sat}}(t_{\text{TCA}}) + \mathbf{P}_{\text{pos, deb}}(t_{\text{TCA}})$$

Projecting $\mathbf{C}$ onto the 2D encounter frame (B-plane) perpendicular to relative velocity yields a $2 \times 2$ covariance matrix $\mathbf{C}_{2D}$. Assuming a spherical combined hard-body radius $R_{\text{HBR}} = 5.00\text{ m}$ (representing the physical spacecraft bus plus solar panels and debris radius), the collision probability is formulated as:

$$P_c = \frac{1}{2\pi \sqrt{\det \mathbf{C}_{2D}}} \iint_{x^2 + y^2 \le R_{\text{HBR}}^2} \exp \left( -\frac{1}{2} \begin{bmatrix} x - x_e \\ y - y_e \end{bmatrix}^T \mathbf{C}_{2D}^{-1} \begin{bmatrix} x - x_e \\ y - y_e \end{bmatrix} \right) dx \, dy$$

Evaluation via the Foster (1992) series expansion yields:
* **Nominal Encounter:**
  * $P_c = 3.957542 \times 10^{-14}$
  * $\log_{10}(P_c) = -13.402575$
  * Status: `NUMERICAL_UNDERFLOW` (Due to miss distance being substantially larger than the covariance semi-axes $\sigma \approx 20\text{ m}$)

### Crucial Threshold Distinctions
It is critical to distinguish between three distinct project parameters:
1. **Combined Hard-Body Radius ($R_{\text{HBR}} = 5.00\text{ m}$):** Physical spherical envelope encompassing the primary satellite structure and debris object.
2. **Operational Safety Clearance Threshold ($D_{\text{threshold}} = 2000.0\text{ m}$):** A project-defined operational screening envelope chosen for simulation evaluation, not a universal orbital safety standard.
3. **Broad-Phase Screening Distance ($D_{\text{screen}} = 25000.0\text{ m}$):** Initial broad-phase filter boundary for candidate conjunction tracking.

The system explicitly preserves the asymptotic logarithmic tail $\log_{10}(P_c) = -13.40$ rather than clamping to zero. A low calculated collision probability does not guarantee absolute collision prevention in physical spaceflight, where non-Gaussian distribution tails, unmodeled drag variations, and debris attitude dynamics can modify relative motion.

---

## 9. Autonomous Avoidance Manoeuvre Planning
The avoidance planner evaluates an impulsive Delta-V budget executed at an early warning epoch ($t_{\text{burn}} = 169.63197\text{ s}$, exactly $600.0\text{ s}$ prior to nominal TCA).

The planner evaluates a discrete candidate catalog across the local Radial-Tangential-Normal (RTN) reference frame:
* **Along-Track ($\pm T$):** Modifies semi-major axis and orbital period; efficient for along-track separation over multiple orbits, but induces altitude changes.
* **Radial ($\pm R$):** Modifies orbital eccentricity and energy; alters radial distance and along-track phasing over partial-orbit horizons.
* **Cross-Track ($\pm N$):** Modifies inclination and right ascension of ascending node; Delta-V intensive for coplanar conjunctions.

### Optimization Formulation:
$$\min_{\Delta \mathbf{v}} \|\Delta \mathbf{v}\| \quad \text{subject to} \quad d_{\text{miss}}(\Delta \mathbf{v}) \ge D_{\text{safety}} = 2000.0\text{ m}, \quad \|\Delta \mathbf{v}\| \le 5.0\text{ m/s}$$

### Selected Optimal Manoeuvre:
* **Manoeuvre Identifier:** `MAN_006_-R_3.00mps_T170s`
* **Impulse Magnitude:** $\Delta v = 3.00\text{ m/s}$
* **Direction:** Radial Inward ($-R$)
* **RTN Vector:** $\Delta \mathbf{v}_{\text{RTN}} = [-3.00, 0.00, 0.00]^T\text{ m/s}$
* **ECI Vector:** $\Delta \mathbf{v}_{\text{ECI}} = [-2.94998, -0.54554, 0.00]^T\text{ m/s}$
* **Burn Epoch:** $T + 169.63197\text{ s}$ ($600.0\text{ s}$ prior to nominal TCA)

### Analytical Orbital Mechanics Verification:
The impulsive burn is applied to the protected satellite in a circular Low Earth Orbit ($r_0 = 7000.0\text{ km}$, $v_0 = 7546.053\text{ m/s}$, $\mu = 3.986004418 \times 10^{14}\text{ m}^3/\text{s}^2$):
1. **State at Burn ($t = 169.632\text{ s}$):**
   * $\mathbf{r}_{\text{pre}} = [6883287.72, 1272929.77, 0.00]^T\text{ m}$ ($\|\mathbf{r}_{\text{pre}}\| = 7000.000\text{ km}$)
   * $\mathbf{v}_{\text{pre}} = [-1372.23, 7420.24, 0.00]^T\text{ m/s}$ ($\|\mathbf{v}_{\text{pre}}\| = 7546.053\text{ m/s}$)
2. **Post-Burn State:**
   * $\mathbf{r}_{\text{post}} = \mathbf{r}_{\text{pre}}$ (position continuous across impulse)
   * $\mathbf{v}_{\text{post}} = \mathbf{v}_{\text{pre}} + \Delta \mathbf{v}_{\text{ECI}} = [-1375.18, 7419.69, 0.00]^T\text{ m/s}$ ($\|\mathbf{v}_{\text{post}}\| = 7546.054\text{ m/s}$)
3. **Specific Orbital Energy and Semi-Major Axis:**
   * Pre-burn specific energy: $\mathcal{E}_{\text{pre}} = \frac{v_0^2}{2} - \frac{\mu}{r_0} = -28471460.13\text{ J/kg}$
   * Post-burn specific energy: $\mathcal{E}_{\text{post}} = \frac{v_0^2 + (\Delta v)^2}{2} - \frac{\mu}{r_0} = \mathcal{E}_{\text{pre}} + \frac{(\Delta v)^2}{2} = -28471455.63\text{ J/kg}$ ($\Delta \mathcal{E} = +4.50\text{ J/kg}$)
   * Semi-major axis change: $\Delta a = a_{\text{post}} - a_{\text{pre}} \approx a \left(\frac{\Delta v}{v_0}\right)^2 = +1.11\text{ m}$ ($a_{\text{pre}} = 7000000.00\text{ m} \to a_{\text{post}} = 7000001.11\text{ m}$)
   * Fractional change: $\frac{\Delta a}{a} = +1.58 \times 10^{-7}$
4. **Orbital Period and Eccentricity:**
   * Period shift: $\Delta T \approx \frac{3}{2} T \frac{\Delta a}{a} \approx +0.00138\text{ s} \approx +1.38\text{ ms}$ ($T = 5828.52\text{ s}$, fractional change $\Delta T / T \approx 2.37 \times 10^{-7}$)
   * Induced orbital eccentricity: $e \approx \frac{\Delta v}{v_0} \approx 0.000398$
   * Specific angular momentum: $\mathbf{h} = \mathbf{r} \times \mathbf{v}$ is unchanged ($\Delta \|\mathbf{h}\| = 0.0\text{ m}^2/\text{s}$) because $\Delta \mathbf{v}$ is purely radial.
5. **Coupled Avoidance Mechanism at Nominal TCA ($600\text{ s}$ post-burn):**
   * At the continuous nominal TCA epoch ($t = 769.63197\text{ s}$), the displacement vector $\Delta \mathbf{r} = \mathbf{r}_{\text{mod}} - \mathbf{r}_{\text{nom}} = [-1961.61, -478.26, 0.00]^T\text{ m}$ in ECI resolves in the nominal RTN frame as:
     * **Radial displacement ($\Delta r_R$):** $-1677.14\text{ m}$ (lower altitude)
     * **Along-track displacement ($\Delta r_T$):** $+1124.21\text{ m}$ (forward phasing lead)
     * **Cross-track displacement ($\Delta r_N$):** $0.00\text{ m}$ (in-plane motion)
     * **Euclidean 3D Norm:** $\sqrt{\Delta r_R^2 + \Delta r_T^2 + \Delta r_N^2} = 2019.07\text{ m}$ (at the discrete time-series grid sample $t = 770.0\text{ s}$ recorded in `Simulation_Results.json`, $\Delta r_R = -1676.69\text{ m}$, $\Delta r_T = +1124.73\text{ m}$, yielding $\|\Delta \mathbf{r}\| = 2018.99\text{ m}$).
   * In both evaluations, the Euclidean norm of the RTN components rigorously equals the ECI displacement norm.
   * Based on orthogonal squared-component contributions ($\Delta r_i^2 / \|\Delta \mathbf{r}\|^2$), the displacement is **69.0% radial** and **31.0% along-track** (or 59.8% radial and 40.2% along-track by linear absolute ratio $|\Delta r_i| / (|\Delta r_R| + |\Delta r_T|)$). The miss distance dilation is therefore driven jointly by in-plane radial altitude displacement and along-track phasing lead; along-track phasing is not the sole mechanism.

---

## 10. Python-to-Unreal Data Bridge & Integration
To preserve scientific integrity, Unreal Engine 5.7 functions strictly as a playback and visualization environment. 

### Data Flow Contract:
1. `D2_simulation_exporter.py` propagates the complete scenario, serializing initial states, physical constants, encounter metrics, manoeuvre parameters, and 501 equidistant trajectory samples ($0.0\text{ to }1000.0\text{ s}$ at $\Delta t = 2.0\text{ s}$) into `unreal_simulation_payload.json`.
2. Spatial coordinates are converted from ECI J2000 (right-handed, metres) to Unreal Left-Handed Z-Up (Unreal Units, where $1\text{ uu} = 100.0\text{ m}$, scale factor $s = 0.01$):
   $$X_{\text{UE}} = X_{\text{ECI}} \times 0.01, \quad Y_{\text{UE}} = -Y_{\text{ECI}} \times 0.01, \quad Z_{\text{UE}} = Z_{\text{ECI}} \times 0.01$$
3. In Unreal Engine, `USimulationDataBridge` loads the JSON file via `FJsonObjectConverter`, exposing typed C++ structs (`FEncounterData`, `FManoeuvreData`, `FDemonstrationStep`).
4. At runtime, `AOrbitSimulationManager::Tick()` samples positions via interpolation, updating scene actors without numerical drift.

---

## 11. Interactive 3D Visualization & Telemetry HUD
The visual scene in `/Game/Scenarios/CollisionAvoidanceDemo` incorporates:

1. **Earth Actor (`AEarthActor`):** Realistic Earth sphere scaled scientifically ($R_{\text{Earth}} = 63781.37\text{ uu} = 6378.137\text{ km}$) with multi-layer surface shaders (NASA Blue Marble textures, specular ocean masking, dynamic cloud layers, and Rayleigh atmospheric scattering limb).
2. **Spacecraft Actor (`ASatelliteActor`):** Golden Kapton metallic body, segmented solar panels with photovoltaic specular highlights, and communication dish. Switches state from `NominalFlight` to `ManoeuvredFlight` upon burn execution.
3. **Debris Actor (`ADebrisActor`):** Irregular metallic fragment tumbling in forward orbit.
4. **Trajectory Splines (`AOrbitPathActor`):** Three distinct orbital paths rendered via continuous spline meshes:
   * **Cyan (`#00B4D8`):** Protected Satellite Nominal Path.
   * **Red (`#E63946`):** Secondary Debris Threat Path.
   * **Green (`#2A9D8F`):** Protected Satellite Post-Manoeuvre Path (activates at burn epoch).
5. **Conjunction Visualizer (`AConjunctionVisualizer`):** Calibrated translucent purple encounter disc and yellow miss-distance connector line.
6. **Manoeuvre Visualizer (`AManoeuvreVisualizer`):** Glowing orange burn ring and Delta-V impulse vector arrow at burn location.
7. **Interactive Slate HUD (`UAvoidanceInfoPanelWidget`):** Real-time telemetry panel displaying simulation clock, active milestone headline, encounter pair, nominal and post-manoeuvre TCA/miss distance, Delta-V budget, and collision probability in scientific notation (`3.958e-14` / `1.239e-22`) with asymptotic underflow status.
8. **Interactive Controls:**
   * `[Space]`: Toggle Play / Pause.
   * `[R]`: Reset simulation to $T=0.0\text{ s}$ and Step 1.
   * `[1-8]`: Direct jump to demonstration milestones 1 through 8.
   * `[Up/Down Arrow]`: Time dilation ladder ($1\times, 2\times, 5\times, 10\times, 25\times, 50\times, 100\times, 200\times$).
   * `[C]`: Cycle camera views across all 6 scene cameras.
   * `[Left/Right Arrow]`: Step backward / Step forward.

---

## 12. Quantitative Performance Evaluation

### Performance Metrics Table (Nominal vs Post-Manoeuvre)
The quantitative results derived from the authoritative Python simulation are summarized below:

| Performance Metric | Nominal Encounter | Post-Manoeuvre Encounter | Delta ($\Delta$) | Relative Change | Operational Impact |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Miss Distance ($d_{\text{miss}}$)** | $1563.48\text{ m}$ ($1563.476\text{ m}$) | $2454.42\text{ m}$ ($2454.416\text{ m}$) | $+890.94\text{ m}$ | **$+56.985\%$** | Meets project-defined $2000.0\text{ m}$ threshold |
| **Time of Closest Approach (TCA)**| $769.63197\text{ s}$ | $903.02922\text{ s}$ | $+133.3973\text{ s}$ | $+17.33\%$ | Delayed encounter by $+2.22\text{ min}$ |
| **Relative Velocity ($v_{\text{rel}}$)** | $13.234\text{ m/s}$ | $14.171\text{ m/s}$ | $+0.937\text{ m/s}$ | $+7.08\%$ | Minor geometry reorientation |
| **Collision Probability ($P_c$)** | $3.958 \times 10^{-14}$ | $1.239 \times 10^{-22}$ | $-3.958 \times 10^{-14}$ | $-100.00\%$ | **$\approx 3.195 \times 10^8$ reduction in $P_c$** |
| **Logarithmic Risk ($\log_{10} P_c$)** | $-13.4026$ | $-21.9070$ | $-8.5044$ decades | $-63.45\%$ | **$8.50$ orders of magnitude drop** |
| **Risk Classification** | `CRITICAL_COLLISION_ALERT` | `RESOLVED_SAFE` | Mitigated | Resolved | Operational safety threshold satisfied in the simulated scenario |
| **Numerical Status** | `NUMERICAL_UNDERFLOW` | `NUMERICAL_UNDERFLOW` | Preserved | Preserved | Tail preserved without zero clamp |
| **Applied Impulse ($\Delta v$)** | $0.00\text{ m/s}$ | $3.00\text{ m/s}$ ($-R$) | $+3.00\text{ m/s}$ | N/A | Efficient radial inward impulse |
| **Manoeuvre Lead Time** | N/A | $600.0\text{ s}$ ($10.0\text{ min}$) | $600.0\text{ s}$ | N/A | Operational execution window |
| **Peak Trajectory Deviation** | $0.00\text{ m}$ | $3008.50\text{ m}$ | $+3008.50\text{ m}$ | N/A | Maximum nominal-to-modified deviation at $T+1000\text{ s}$ |
| **Separation at Nominal TCA** | $0.00\text{ m}$ | $2018.99\text{ m}$ | $+2018.99\text{ m}$ | N/A | Displacement at original encounter epoch |
| **Separation at Post TCA** | $0.00\text{ m}$ | $2578.88\text{ m}$ | $+2578.88\text{ m}$ | N/A | Displacement at new encounter epoch |

> [!IMPORTANT]
> **Measurement Distinction:**
> * **Nominal-to-Modified Protected-Spacecraft Trajectory Deviation:** $\|\mathbf{r}_{\text{mod}}(t) - \mathbf{r}_{\text{nom}}(t)\|$ measures the spatial divergence of the protected spacecraft from its nominal path due to the burn ($0.0\text{ m}$ pre-burn, $2019.0\text{ m}$ at nominal TCA, $3008.5\text{ m}$ peak).
> * **Satellite-to-Debris Relative Miss Distance:** $\|\mathbf{r}_{\text{sat}}(t) - \mathbf{r}_{\text{deb}}(t)\|$ measures the separation between the satellite and the debris fragment ($1563.5\text{ m}$ nominal minimum, $2454.4\text{ m}$ post-manoeuvre minimum).

---

## 13. Results and Comparative Discussion

### 13.1 Miss Distance Dilatation
The primary operational safety criterion requires a miss distance exceeding $D_{\text{safety}} = 2000.0\text{ m}$. In the nominal encounter, the miss distance was $1563.48\text{ m}$, breaching the project-defined $2000.0\text{ m}$ threshold. Execution of the $-R$ $3.00\text{ m/s}$ impulse expanded the miss distance to $2454.42\text{ m}$, achieving an absolute margin gain of $+890.94\text{ m}$ ($+56.985\%$). This establishes a $454.4\text{ m}$ buffer beyond the threshold.

### 13.2 Collision Probability Attenuation
Due to small initial state covariance volumes, the nominal collision probability was $3.958 \times 10^{-14}$ ($\log_{10} P_c = -13.40$). Post-manoeuvre propagation reduced this value to $1.239 \times 10^{-22}$ ($\log_{10} P_c = -21.91$). This represents an absolute probability reduction factor of:

$$\text{Probability Reduction Factor} = \frac{P_{c, \text{nom}}}{P_{c, \text{post}}} = \frac{3.957542 \times 10^{-14}}{1.238744 \times 10^{-22}} \approx 3.1948 \times 10^8$$

The manoeuvre achieves an **approximate $3.195 \times 10^8$ reduction in calculated collision probability**, corresponding to an **$8.50$ decade reduction** in risk. Both values are correctly preserved as asymptotic tails rather than being clamped to zero.

### 13.3 Manoeuvre Efficiency & Propellant Trade-Off
A key finding of this evaluation is the effectiveness of early radial inward ($-R$) impulsive burns as an **effective strategy for the evaluated reference scenario**. 

To provide context on control effort, the following is an **illustrative propellant estimate based on assumed spacecraft mass and specific impulse; not a measured or planner-generated mission propellant requirement**:

$$\Delta m = m_0 \left(1 - \exp\left(-\frac{\Delta v}{I_{\text{sp}} g_0}\right)\right)$$

Using assumed parameters:
* Initial Spacecraft Mass: $m_0 = 1000\text{ kg}$
* Specific Impulse: $I_{\text{sp}} = 220\text{ s}$ (representative monopropellant hydrazine)
* Delta-V: $\Delta v = 3.00\text{ m/s}$
* Standard Gravity: $g_0 = 9.80665\text{ m/s}^2$

$$\Delta m = 1000 \left(1 - \exp\left(-\frac{3.00}{220 \times 9.80665}\right)\right) \approx 1.39\text{ kg}$$

This analytical estimate illustrates that a Delta-V of $3.00\text{ m/s}$ represents modest propellant expenditure for a standard LEO bus. The system reports the authoritative $\Delta v = 3.00\text{ m/s}$ as the standardized control effort metric, avoiding simulated or fabricated fuel gauge measurements.

### 13.4 Trajectory Deviation Dynamics
Spatial separation between the nominal and modified orbits begins at zero at the burn epoch ($T+169.6\text{ s}$), accumulating to $2018.99\text{ m}$ at nominal TCA ($T+769.6\text{ s}$), $2578.88\text{ m}$ at post-manoeuvre TCA ($T+903.0\text{ s}$), and reaching a peak of $3008.50\text{ m}$ at the end of the simulation ($T+1000.0\text{ s}$).

---

## 14. Current System Limitations
In compliance with engineering standards, current limitations are explicitly documented:

1. **Two-Body Gravitational Model:** Orbital propagation currently models ideal Newtonian two-body point-mass gravity. Higher-order geopotential harmonics (such as Earth's oblateness $J_2 = 1.08263 \times 10^{-3}$, $J_3, J_4$), atmospheric drag in lower LEO regimes ($< 500\text{ km}$), Solar Radiation Pressure (SRP), and third-body lunisolar gravitational perturbations are omitted.
2. **Impulsive Burn Idealization:** The manoeuvre is modeled as an instantaneous velocity vector discontinuity ($\Delta \mathbf{v}$). In operational spacecraft, chemical or electric thrusters execute finite-duration burns subject to attitude slew rates, thruster ramp-up transients, and pointing jitter.
3. **Linearized Gaussian Covariance Assumptions:** Covariance propagation utilizes linear state transition matrices under Gaussian assumptions. Over multi-day horizons, orbital non-linearities distort Gaussian distributions into non-Gaussian probability densities.
4. **Frozen Simulation Scenario:** The current demonstration sequence is validated on a single frozen reference scenario (CARTOSAT-3 vs DEBRIS_PIECE_99). Multi-body debris field cascading and continuous CDM ingestion streams are not modeled in the playback layer.
5. **Absence of Real-World Flight Hardware Execution:** The software operates as a simulation and visualization testbed; it does not interface directly with flight telemetry hardware, onboard command decoders, or flight-certified RTOS executives. Operational flight readiness is not claimed.

---

## 15. Future Work & Roadmap
To advance this prototype toward operational readiness, the following enhancements are proposed:

1. **High-Fidelity Orbital Propagator (HPOP):** Incorporate the EGM2008 gravity model (up to degree and order $70 \times 70$), NRLMSISE-00 atmospheric density modeling, and cannonball SRP with shadow cylindrical boundaries.
2. **Finite-Burn Guidance Navigation & Control (GNC):** Implement low-thrust continuous electric propulsion optimal control formulations using Pontryagin's Minimum Principle.
3. **Non-Gaussian Probability Computation:** Integrate Monte Carlo and Gaussian Mixture Model (GMM) techniques for non-linear collision probability estimation.
4. **Live Space-Track / CCSDS CDM Ingestion:** Implement an automated REST API ingestion daemon parsing standard CCSDS Conjunction Data Messages (CDMs) and Two-Line Element (TLE) catalogs.
5. **Hardware-in-the-Loop (HIL) Testbed:** Port the decision pipeline to an embedded flight computer (e.g. ARM Cortex-R or radiation-hardened LEON4) integrated with simulated star trackers and reaction wheel telemetry.

---

## 16. Conclusion
The **Autonomous Satellite Collision Avoidance System (ICPS)** successfully **demonstrates in the evaluated simulation** the integration of authoritative scientific astrodynamics with high-fidelity real-time 3D simulation. 

By freezing the authoritative Python scientific solvers and establishing a clean, unidirectional data bridge to Unreal Engine 5.7.4, the project delivers:
* **Quantitatively Verified Avoidance:** An $890.94\text{ m}$ ($+56.985\%$) expansion in miss distance and an $8.50$ decade reduction in collision probability (approximately a $3.195 \times 10^8$ reduction in calculated collision probability) using an optimal $3.00\text{ m/s}$ radial inward impulse that meets the defined simulation safety threshold.
* **Regression Baseline:** 39 automated regression tests passed in the D2 regression test suite.
* **Physics-Synchronized Visualization:** An eight-step demonstration sequence in Unreal Engine 5.7.4 featuring realistic Earth and atmosphere rendering, high-detail spacecraft and debris models, continuous trajectory splines, calibrated encounter geometry, and an interactive Slate telemetry HUD.
* **Reproducible Engineering Deliverables:** Complete technical documentation, publication-grade performance charts, Excel data workbooks, structured JSON results, and a demonstration video (`Final_Demonstration_Video.mp4`).

The project demonstrates the feasibility of combining verified scientific solvers with real-time 3D visual playback for orbital safety analysis.

---

## 17. References
1. **Foster, J. L., & Estes, H. S.** (1992). *A Parametric Analysis of Orbital Debris Collision Probability and Maneuver Strategy for Space Station Freedom*. NASA-JSC-25898.
2. **Alfriend, K. T., Akella, M. R., Frisbee, J., Foster, J. L., Lee, D. J., & Wilkins, M.** (1999). *Probability of Collision Error Analysis*. Space Debris, 1(1), 17–35.
3. **Vallado, D. A.** (2013). *Fundamentals of Astrodynamics and Applications* (4th ed.). Microcosm Press / Springer.
4. **Battin, R. H.** (1999). *An Introduction to the Mathematics and Methods of Astrodynamics*. AIAA Education Series.
5. **Klinkrad, H.** (2006). *Space Debris: Models and Risk Analysis*. Springer Praxis Publishing.
6. **Chan, K.** (2008). *Spacecraft Collision Probability*. The Aerospace Press.
7. **Bate, R. R., Mueller, D. D., & White, J. E.** (1971). *Fundamentals of Astrodynamics*. Dover Publications.
8. **CCSDS.** (2019). *Conjunction Data Message (CDM)*. Recommended Standard CCSDS 508.0-B-1, Consultative Committee for Space Data Systems.
