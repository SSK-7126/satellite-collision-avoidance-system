# Satellite Collision Avoidance System

A prototype system for satellite conjunction assessment and collision-risk monitoring using real orbital data, SGP4 propagation, relative-motion analysis, and 3D visualization.

## Overview

The system takes orbital data for tracked space objects, propagates their positions and velocities, calculates relative motion, identifies the closest approach, and classifies the encounter using configurable prototype distance thresholds.

The project currently uses:

- **CARTOSAT-3** — NORAD ID 44804
- **PSLV R/B (Rocket Body)** — NORAD ID 44805

> PSLV R/B is a rocket body and is not classified as fragmentation debris.

## Deliverables

### D1 — Conjunction Assessment Prototype

D1 implements the complete analysis pipeline:

1. Load orbital data from TLE records.
2. Propagate satellite states using **SGP4**.
3. Generate synchronized position and velocity data.
4. Calculate relative position, relative velocity, separation distance, and closest approach.
5. Classify proximity risk.
6. Provide 2D and 3D visualization.
7. Provide an interactive web dashboard.
8. Validate close-approach detection using a controlled synthetic scenario.

### D2 — Autonomous Maneuver Planning

D2 is the planned extension of the system toward autonomous collision-avoidance maneuver planning.

The D1 outputs provide the orbital state and encounter information required as inputs for future maneuver analysis.

## Data Sources

Orbital data is stored in:

```text
data/orbital_data.txt