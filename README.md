# Satellite Anti-Collision System (ICPS)

A computational simulation designed to model orbital debris, detect potential satellite collisions, and simulate autonomous collision-avoidance manoeuvres.

## Project Deliverables

### D1 — Orbital Environment Simulation
- Model a protected satellite and surrounding debris objects.
- Simulate orbital motion using gravitational dynamics.
- Generate and visualize orbital trajectories.
- Study the relative motion of space objects.

### D2 — Autonomous Collision Avoidance
- Detect potential close approaches between satellites and debris.
- Calculate Time of Closest Approach (TCA) and miss distance.
- Estimate collision risk using orbital uncertainty.
- Determine a suitable avoidance manoeuvre.
- Apply Δv and simulate the modified trajectory.
- Evaluate collision avoidance success, trajectory deviation and manoeuvre effort.

## System Architecture

| Component | Responsibility |
|---|---|
| Unreal Engine 5 | 3D orbital environment and visualization |
| Orbital Dynamics | Orbit propagation and physical calculations |
| Python / ML | Risk prediction and manoeuvre decision-making |
| Data Bridge | Communication between simulation and ML service |

## Mathematical Model

**1. Gravitational Acceleration**

\[
a=-\frac{\mu r}{|r|^3}
\]

**2. Orbital Velocity**

\[
v=\sqrt{\frac{\mu}{r}}
\]

**3. Orbital Period**

\[
T=2\pi\sqrt{\frac{r^3}{\mu}}
\]

**4. Relative Position and Velocity**

\[
r_{rel}=r_2-r_1
\]

\[
v_{rel}=v_2-v_1
\]

**5. Closest Approach Time**

\[
t_{CPA}=-\frac{r_{rel}\cdot v_{rel}}{v_{rel}\cdot v_{rel}}
\]

**6. Manoeuvre Velocity Change**

\[
\Delta v=\int a_{thrust}(t)\,dt
\]

Numerical orbit propagation uses the Runge-Kutta 4 (RK4) method as the initial integration approach.

## Data Sources

- **Synthetic orbital objects:** Initial controlled simulation scenarios.
- **NASA CARA:** Conjunction assessment and collision avoidance references.
- **ESA Space Debris Office:** Potential supplementary debris environment data.
- **Orekit:** Astrodynamics reference for orbital propagation and force models.
- **NASA/JPL:** Orbital and Earth-related reference constants.

Specific external datasets will be documented when incorporated into the implementation.

## Simulation Outputs

- Satellite and debris trajectories.
- Time of Closest Approach (TCA).
- Minimum miss distance.
- Relative encounter velocity.
- Collision-risk assessment.
- Pre- and post-manoeuvre trajectories.
- Δv and manoeuvre effort.
- Collision avoidance performance metrics.

## Repository Structure

```text
SatelliteAntiCollision/
├── README.md
├── UnrealProject/
├── DynamicsService/
├── MLService/
├── Scenarios/
├── Datasets/
└── Results/
```

## Scope

This is an educational and research prototype. It is not operational spacecraft flight software. Orbital calculations, collision-risk methods and manoeuvre models require independent validation.
