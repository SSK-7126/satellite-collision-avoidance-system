# Requirement Traceability Matrix

**Project:** Satellite Collision Avoidance System (ICPS)  
**Reference Document:** `Satellite_Anti_Collision_Unreal_Engine_Technical_Guide.docx` (12 pages, 18 Nov 2026)  
**Repository:** `C:\Users\Sriram Krovi\satellite-collision-avoidance-system`  
**Git Branch:** `main`  
**Classification Date:** 22 November 2026  

---

## 1. Traceability Matrix

| Section | Guide Requirement & Specification | Classification | Evidence: Existing Code & Tests | Gaps & Actions |
| :--- | :--- | :--- | :--- | :--- |
| **Preamble** | Educational/research prototype; not flight software. | **IMPLEMENTED** | `README.md`, `FINAL_QUALITY_REVIEW.md` | Preserve explicit disclaimers in all new files and interfaces. |
| **Outcomes.1** | Propagate protected satellite and secondary debris objects. | **IMPLEMENTED** | `D2/dynamics/two_body.py`, `orbit_propagator.py`; `D2/tests/test_orbit_propagation.py` | Validated for two-body Keplerian orbits. |
| **Outcomes.2** | Calculate TCA, miss distance, relative encounter velocity. | **IMPLEMENTED** | `D2/conjunction/tca.py`, `screening.py`; `D2/tests/test_conjunction.py` | Parabolic refinement and linear CPA validated. |
| **Outcomes.3** | Represent uncertainty & calculate Pc or clear risk proxy. | **IMPLEMENTED** | `D2/uncertainty/covariance.py`, `collision_probability.py`; `D2/tests/test_uncertainty.py` | Foster (1992) validated. Add standardized numerical quality flags. |
| **Outcomes.4** | Receive prediction/risk/decision from external ML service. | **MISSING** | No standalone inference service in repo. | Build versioned Python ML service with schema validation. |
| **Outcomes.5** | Apply physically constrained avoidance manoeuvre & re-screen. | **IMPLEMENTED** | `D2/manoeuvres/avoidance_pipeline.py`; `D2/tests/test_manoeuvres.py` | Impulsive verified. Extend to finite thrust & mass depletion. |
| **Outcomes.6** | Visualize and log events so scenarios can be repeated/compared. | **PARTIAL** | `unreal_simulation_payload.json`, UE5 HUD. | Build automated S0–S8 scenario runner and metrics logger. |
| **Sec 1** | Subsystem separation; scientific solver authoritative; no UE rigid-body for orbits. | **IMPLEMENTED** | `OrbitSimulationManager.cpp`, `CoordinateAdapter.cpp`; `test_visualization.py` | Preserved as invariant. Unreal only visualizes. |
| **Sec 2.1** | Declared ECI frame, SI units (m, m/s), single clock, double precision. | **IMPLEMENTED** | `coordinate_transform.py`, `two_body.py`; `test_visualization.py` | ECI J2000 standard. Float64 used everywhere in dynamics. |
| **Sec 2.1** | ECEF frame for Earth-fixed features with time-dependent transform. | **PARTIAL** | `EarthActor.cpp` has Earth rotation rate. | Implement explicit ECI <-> ECEF transform for ground stations. |
| **Sec 2.2** | Render scale definition (0.01 uu/m) and NOT TO SCALE indicator. | **IMPLEMENTED** | `coordinate_transform.py`, `AvoidanceInfoPanelWidget.cpp` | Visual scale 1 uu = 100 m verified. |
| **Sec 3.1** | Two-body point mass gravity: a = -mu * r / \|r\|^3. | **IMPLEMENTED** | `D2/dynamics/two_body.py`; `D2/tests/test_two_body.py` | Standard mu = 3.986004418e14 m^3/s^2. |
| **Sec 3.2** | Numerical RK4 ODE integrator with step convergence check. | **IMPLEMENTED** | `D2/dynamics/rk4.py`; `D2/tests/test_rk4.py` | Fixed-step RK4 verified. Add explicit h-halving convergence test. |
| **Sec 3.3** | J2 non-spherical gravity perturbation. | **MISSING** | None in `two_body.py`. | Implement J2 perturbation module with acceleration checks. |
| **Sec 3.3** | Atmospheric drag perturbation. | **MISSING** | None in `two_body.py`. | Implement exponential density drag model with area/Cd/mass. |
| **Sec 3.3** | Higher-order perturbations (SRP, third-body, eclipses). | **N/A** | Out of scope for LEO research prototype. | Document as future extension. |
| **Sec 4** | Satellite & debris object model (ID, epoch, frame, state, mass, HBR, cov). | **PARTIAL** | State dictionaries in D2. | Formalize `SpaceObject` dataclass. |
| **Sec 4.1** | Geometry: separate visual mesh size from physical hard-body radius (HBR). | **IMPLEMENTED** | HBR = 5.0m in scientific solver; visual meshes scaled in UE. | Invariant preserved. |
| **Sec 4.2** | Debris population: synthetic known states, orbital mechanics propagation. | **IMPLEMENTED** | LEO debris in `close_approach.py`; SGP4 in `propagator.py` | Extend to multi-debris catalog (S5). |
| **Sec 5.1** | Relative state: r_rel = r2 - r1, v_rel = v2 - v1. | **IMPLEMENTED** | `D2/conjunction/tca.py`; `D2/tests/test_conjunction.py` | Invariant preserved. |
| **Sec 5.2** | Linear CPA approximation with window and near-zero v_rel handling. | **IMPLEMENTED** | `D2/conjunction/tca.py`; `D2/tests/test_conjunction.py` | Invariant preserved. |
| **Sec 5.3** | Numerical TCA with separation minimization. | **IMPLEMENTED** | `D2/conjunction/tca.py`; `D2/tests/test_conjunction.py` | Parabolic refinement verified. |
| **Sec 5.4** | Screening volume as computational filter (25 km), distinct from Pc. | **IMPLEMENTED** | `D2/conjunction/screening.py`; `D2/tests/test_conjunction.py` | Invariant preserved. |
| **Sec 6.1** | Covariance representation (6x6 P), symmetry & PSD validation. | **IMPLEMENTED** | `D2/uncertainty/covariance.py`; `D2/tests/test_uncertainty.py` | Invariant preserved. |
| **Sec 6.1** | Relative covariance (P_rel = P1 + P2). | **IMPLEMENTED** | `D2/uncertainty/covariance.py`; `D2/tests/test_uncertainty.py` | Invariant preserved. |
| **Sec 6.1** | Covariance propagation: P(t) = Phi P(t0) Phi^T + Q. | **IMPLEMENTED** | `D2/dynamics/variational.py`, `covariance.py`; `test_orbital_covariance.py` | Variational 42-state STM integration verified. |
| **Sec 6.2** | Probability of collision (Pc): Foster (1992) 2D encounter-plane. | **IMPLEMENTED** | `D2/uncertainty/collision_probability.py`; `test_uncertainty.py` | Asymptotic underflow handling verified. |
| **Sec 6.2** | Missing covariance handling: Risk score / proxy label, never zero Pc. | **IMPLEMENTED** | `calculate_simplified_risk_proxy()`; `test_uncertainty.py` | Invariant preserved. |
| **Sec 6.3** | Risk vs probability: separate likelihood from consequences. | **PARTIAL** | Pc and miss distance separated. | Add relative kinetic energy & consequence index. |
| **Sec 7.1** | Delta-v and thrust: Impulsive baseline; finite burn. | **PARTIAL** | Impulsive implemented in `manoeuvre_model.py`. | Add finite thrust acceleration model. |
| **Sec 7.2** | Rocket equation: Delta-v = Isp * g0 * ln(m0 / mf), propellant mass. | **PARTIAL** | Formula cited in report; not in dynamic state. | Implement dynamic mass depletion in propulsion module. |
| **Sec 7.3** | Manoeuvre constraints: thrust, duration, fuel, attitude slew, error. | **PARTIAL** | Delta-v, lead time, deviation constrained. | Add propellant mass limit, slew limit, execution dispersion. |
| **Sec 7.4** | Manoeuvre evaluation loop: receive proposal, validate, apply, re-screen. | **IMPLEMENTED** | `D2/manoeuvres/avoidance_pipeline.py`; `test_manoeuvres.py` | Invariant preserved. |
| **Sec 8** | Sensor simulation: truth/observation separation, optical/radar, outages. | **MISSING** | No sensor subsystem exists. | Build `Sensors/` module with tracking models and outage injector. |
| **Sec 9** | Unreal actors: SimulationManager, Earth, Sat, Debris, Paths, Visualizers. | **IMPLEMENTED** | Unreal C++ classes in `UnrealProject/Source/SatelliteAvoidance/` | Invariant preserved. |
| **Sec 9** | Sensor visualizer component (`USensorVisualizerComponent`). | **MISSING** | None in UE source. | Add C++ component for sensor cone / tracking lines. |
| **Sec 9.1** | Rendering guidance: Local origin, sampled trails, visual differentiation. | **IMPLEMENTED** | Shader materials, trail actors, and HUD verified. | Invariant preserved. |
| **Sec 10** | Python–Unreal data contract: versioned JSON schema. | **PARTIAL** | Data bridge payload exists. | Formalize OpenAPI / Pydantic schemas for ML service. |
| **Sec 10.3** | Interface safeguards: Reject stale, malformed, wrong-frame messages. | **MISSING** | No API server middleware. | Implement validation middleware in ML service. |
| **Sec 11** | Scenarios S0–S8 definitions and reproducible execution. | **PARTIAL** | S2 and S4 implemented in D2 baseline; S0 and S8 in tests. | Build reproducible runnable scripts `Scenarios/s0_circular.py` to `s8_safe_pass.py`. |
| **Sec 12.1** | Physics validation: Units/frame checks, analytical checks, step convergence. | **IMPLEMENTED** | Extensive D2 tests; RK4 step test to add. | Add explicit step-size convergence test. |
| **Sec 12.2** | Metrics suite: TCA error, miss error, Pc calibration, FPR/FNR, lead time, fuel. | **PARTIAL** | D2 baseline evaluation CSVs exist. | Implement unified metrics computation script. |
| **Sec 13** | Development roadmap Phases 1–8. | **PARTIAL** | Phases 1–5 partially or fully complete. | Complete remaining phases sequentially. |
