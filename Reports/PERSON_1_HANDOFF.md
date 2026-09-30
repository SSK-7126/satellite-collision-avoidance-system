# PERSON 1 → PERSON 2 HANDOFF
### Satellite Collision Avoidance System — D1
*Single technical handoff covering completed backend, interfaces, tests, limitations, and the remaining visualization/integration work.*

---

## 1. Purpose and Workflow

```
PERSON 1:
Real orbital data → TLE loading → SGP4 propagation
→ Relative motion → Closest approach → Encounter analysis
→ Simulation backend → HANDOFF → PERSON 2
→ 3D visualization → Dashboard → Controls → Final UI
```

---

## 2. Person 1 — Completed

- Real tracked orbital data loading
- TLE parsing
- SGP4 propagation
- Multi-time orbital propagation
- Position/velocity generation
- Relative motion and separation calculation
- Closest Approach Distance (CAD) and Time of Closest Approach (TCA)
- Relative speed, closing speed and approach angle
- Prototype proximity classification
- Live 2D real-data simulation
- Controlled synthetic close-approach test
- Persistent encounter-event detection
- Shared analysis engine

---

## 3. Project Files

```
satellite-collision-avoidance-system/
├── data/
│   └── orbital_data.txt
├── output/
│   ├── orbital_states.csv
│   └── encounter_analysis.csv
├── data_loader.py
├── propagator.py
├── relative_motion.py
├── analysis_engine.py
├── simulation.py
├── test_scenario.py
├── main.py
└── PERSON_1_HANDOFF.md
```

---

## 4. Orbital Data

- **Primary**: CARTOSAT-3 (NORAD 44804)
- **Secondary**: PSLV R/B (NORAD 44805)

TLEs are stored in `data/orbital_data.txt`. PSLV R/B is a rocket body, not fragmentation debris; it is used as the secondary tracked object for this prototype.

---

## 5. Backend Data Flow

```
data/orbital_data.txt
       ↓
data_loader.py → TLE records
       ↓
SGP4 → propagator.py
       ↓
position + velocity
       ↓
output/orbital_states.csv
       ↓
relative_motion.py
       ↓
output/encounter_analysis.csv
```

---

## 6. Orbital State Data

- **Position**: `x, y, z` in km.
- **Velocity**: `vx, vy, vz` in km/s.

Each orbital-state row contains `time`, `object`, `x/y/z`, and `vx/vy/vz`. Current propagation test: 60 minutes at 1-minute steps.

---

## 7. Relative Motion

$$\vec{r}_{\text{relative}} = \vec{r}_A - \vec{r}_B$$
$$\vec{v}_{\text{relative}} = \vec{v}_A - \vec{v}_B$$
$$\text{distance} = \|\vec{r}_{\text{relative}}\|$$
$$\text{relative\_speed} = \|\vec{v}_{\text{relative}}\|$$

The minimum separation gives **CAD (Closest Approach Distance)** and its timestamp gives **TCA (Time of Closest Approach)**.

---

## 8. Shared Analysis Engine

**File**: `analysis_engine.py`. Person 2 should use this interface rather than duplicating encounter mathematics.

```python
from analysis_engine import calculate_encounter_metrics

result = calculate_encounter_metrics(
    satellite_position,
    satellite_velocity,
    secondary_position,
    secondary_velocity
)

result["distance_km"]
result["relative_speed_km_s"]
result["closing_speed_km_s"]
result["approach_angle_deg"]
result["relative_position_km"]
result["relative_velocity_km_s"]
result["status"]
result["level"]
```

---

## 9. Metric Meanings

- **Distance**: Current 3D separation, km.
- **Relative speed**: Magnitude of relative velocity, km/s.
- **Closing speed**: Positive = approaching; negative = separating.
- **Approach angle**: Angle between relative position and relative velocity under the current implementation; 180° represents direct approach under this convention.

---

## 10. Prototype Status Logic

| Distance Threshold | Status | Level |
| :--- | :--- | :--- |
| $> 100\text{ km}$ | **SAFE** | LOW |
| $10\text{ km} < \text{distance} \le 100\text{ km}$ | **MONITOR** | MEDIUM |
| $\text{distance} \le 10\text{ km}$ | **CLOSE APPROACH** | HIGH |

> **Important**: These are prototype/demo thresholds, not official space-safety thresholds and not a probability-of-collision model. The current system is geometric proximity classification.

---

## 11. Real-Data Simulation

**File**: `simulation.py`. Run with `python simulation.py`.  
Uses CARTOSAT-3, PSLV R/B, real TLE data and SGP4. Displays simulation time, altitude, distance, relative speed, closing speed, approach angle, minimum observed distance and status.

---

## 12. 2D Visualization Limitation

The current display is an X-Y projection of 3D orbital coordinates. Apparent path crossing does not necessarily mean physical collision. The final visualization should use full X, Y, Z coordinates and be 3D.

---

## 13. Synthetic Close-Approach Test

**File**: `test_scenario.py`. Run with `python test_scenario.py`.  
This is a controlled synthetic scenario, not real orbital data. It validates alert/event logic and reaches approximately 5 km minimum separation.

- SAFE → MONITOR → CLOSE APPROACH
- Minimum distance $\approx 5\text{ km}$
- TCA $\approx 200\text{ s}$
- Encounter event remains recorded after separation
- *Never present this synthetic encounter as an actual CARTOSAT-3 collision prediction.*

---

## 14. Person 2 — Tasks

- **Task 1: 3D visualization**: Display Earth, CARTOSAT-3, secondary object, trajectories and current positions using x, y, z.
- **Task 2: Dashboard**: Show simulation time/speed, object altitude/velocity, distance, relative speed, closing speed, approach angle, CAD, TCA and status.
- **Task 3: Controls**: START, PAUSE, RESET, simulation speed; optionally REAL DATA MODE / SYNTHETIC TEST MODE.
- **Task 4: Encounter event**: Preserve a detected close-approach record after objects pass.

---

## 15. Integration Rule

*Do not rewrite `data_loader.py`, `propagator.py`, `relative_motion.py`, or `analysis_engine.py` unless a genuine integration issue requires it. The intended architecture is existing orbital-analysis backend → visualization layer.*

---

## 16. Recommended Architecture

```
TLE DATA
   ↓
SGP4 ENGINE
   ↓
Current State
   ↓
3D Position Velocity
   ↓
Analysis Engine
   ↓
3D Visualization Dashboard
   ↓
Final D1 UI
```

---

## 17. Integration Checklist

### 3D visualization
- [ ] Earth displayed
- [ ] CARTOSAT-3 displayed
- [ ] Secondary object displayed
- [ ] 3D trajectories displayed
- [ ] Objects animated
- [ ] X/Y/Z used

### Encounter display
- [ ] Distance
- [ ] Relative speed
- [ ] Closing speed
- [ ] Approach angle
- [ ] CAD
- [ ] TCA
- [ ] Current status

### Simulation
- [ ] Start
- [ ] Pause
- [ ] Reset
- [ ] Speed control

### Synthetic test
- [ ] Close approach detected
- [ ] Minimum distance shown
- [ ] TCA shown
- [ ] Event persists after separation

---

## 18. Units

- **Position**: km
- **Velocity**: km/s
- **Distance**: km
- **Relative speed**: km/s
- **Closing speed**: km/s
- **Approach angle**: degrees

*If the UI needs different units, convert only in the presentation layer.*

---

## 19. Verified Test Results

- **SGP4 — CARTOSAT-3**: position $(6104.885, -3207.665, \approx 0)\text{ km}$; velocity $(-0.468139, -0.862007, 7.536957)\text{ km/s}$.
- **SGP4 — PSLV R/B**: position $(4610.656, -4945.881, \approx 0)\text{ km}$; velocity $(-0.714407, -0.637282, 7.621605)\text{ km/s}$.
- **Synthetic analysis**: distance $5.00\text{ km}$; relative speed $10.00\text{ km/s}$; closing speed $10.00\text{ km/s}$; approach angle $180^\circ$; status **CLOSE APPROACH / HIGH**.
- **Synthetic simulation**: minimum distance $\approx 5.00\text{ km}$; TCA $\approx 200\text{ s}$; encounter remained recorded after separation.

---

## 20. Scientific Scope

- **Current D1**: TLE, SGP4, relative position/velocity, geometric separation and prototype proximity thresholds.
- **Not implemented**: covariance/uncertainty propagation, formal probability of collision (Pc), high-fidelity perturbations, atmospheric drag, solar radiation pressure, operational conjunction assessment, autonomous maneuver optimization, or real-time telemetry.

---

## 21. Real vs Synthetic

- **REAL**: CARTOSAT-3 TLE, PSLV R/B TLE, SGP4 propagation, orbital-state calculations and real-data simulation.
- **SYNTHETIC**: controlled close-approach trajectory, 5 km test encounter and threshold validation.
*The synthetic scenario validates software behavior; it is not an actual prediction.*

---

## 22. Person 2 Starting Point

Start with:
- `analysis_engine.py`
- `simulation.py`
- `output/orbital_states.csv`
- `output/encounter_analysis.csv`
- `data/orbital_data.txt`

1. Build the 3D visualization without changing the orbital-analysis backend.
2. Integrate live encounter metrics into the dashboard.
3. Integrate the synthetic close-approach test.

---

## 23. Final D1 Target

```
■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■
■ SATELLITE COLLISION AVOIDANCE SYSTEM                         ■
■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■
■ 3D EARTH               ■ SIMULATION                          ■
■                        ■ Time / Speed                        ■
■ ● CARTOSAT-3           ■ CARTOSAT-3 data                     ■
■   Secondary data       ■                                     ■
■ ● SECONDARY            ■ ENCOUNTER                           ■
■                        ■ Distance / Rel. Speed               ■
■ ORBITAL TRAJECTORIES   ■ Closing Speed / Angle               ■
■                        ■ CAD / TCA                           ■
■                        ■ STATUS                              ■
■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■
■ [START] [PAUSE] [RESET] [SPEED] [REAL DATA] [TEST MODE]      ■
■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■
```

---

## 24. Final Handoff

```
PERSON 1
   ↓
Orbital backend COMPLETE
   ↓
Analysis backend COMPLETE
   ↓
Simulation backend COMPLETE
   ↓
HANDOFF
   ↓
PERSON 2
   ↓
3D visualization
   ↓
Dashboard
   ↓
Controls
   ↓
Final integration
```

*Person 2 should begin with the 3D visualization and treat the existing orbital-analysis code as the backend.*
