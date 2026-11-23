# ICPS — Custom Satellite and Debris Configuration Schema Guide

**System:** ICPS Autonomous Satellite Collision Avoidance System  
**Module:** Custom Satellite & Debris Management (Phase 7)  
**Standard:** ISO 24113 Space Systems / CCSDS Orbit Data Messages  
**Specification Version:** 1.0.0 (FINAL)

---

## 1. Overview & Purpose

The Custom Object Configuration Module enables mission directors, aerospace researchers, and demonstration operators to dynamically inject custom satellites and uncatalogued space debris into the ICPS collision assessment pipeline.

The module provides:
1. Dual representation input: **Classical Keplerian Elements** and **Inertial Cartesian Vectors (ECI J2000)**.
2. Rigorous physical parameter validation rejecting unphysical or colliding orbits.
3. Realistic characterization of unknown debris properties with explicit field-level provenance.
4. Per-session scenario isolation with instant one-click reset to the authoritative demonstration baseline.
5. Bidirectional JSON schema import/export and comprehensive REST API endpoints.

---

## 2. Orbital State Vector Representations

### 2.1 Classical Keplerian Elements Schema

Classical orbital elements describe the geometry of the orbit in the central two-body gravitational field of Earth ($\mu = 3.986004418 \times 10^{14}\text{ m}^3/\text{s}^2$):

| Field | Type | Units | Valid Range | Physical Definition |
| :--- | :--- | :--- | :--- | :--- |
| `semi_major_axis_km` | `float` | $\text{km}$ | $a(1-e) > R_\oplus$ ($6,378.137\text{ km}$) | Half of the major axis of the orbital ellipse (LEO to GEO and beyond) |
| `eccentricity` | `float` | dimensionless | $0.0 \le e < 1.0$ | Shape parameter ($0$ = circular, $0 < e < 1$ = bound elliptical, e.g. Molniya $e \approx 0.74$) |
| `inclination_deg` | `float` | degrees | $0.0^\circ \le i \le 180.0^\circ$ | Angle between orbital plane and equatorial plane |
| `raan_deg` | `float` | degrees | $0.0^\circ \le \Omega < 360.0^\circ$ | Right Ascension of the Ascending Node |
| `arg_perigee_deg` | `float` | degrees | $0.0^\circ \le \omega < 360.0^\circ$ | Argument of Perigee measured from ascending node |
| `true_anomaly_deg` | `float` | degrees | $0.0^\circ \le \nu < 360.0^\circ$ | True geometric angle from perigee to position vector |
| `mean_anomaly_deg` | `float` | degrees | $0.0^\circ \le M < 360.0^\circ$ | Fictitious uniform angular fraction of orbital period |

### 2.2 Mathematical Validity vs Configurable Operational Constraints

The system strictly decouples **fundamental mathematical validity** from **mission operational envelopes**:

1. **Fundamental Mathematical Validity (Hard Rejection Gate):**
   - Semi-major axis $a > 0$ strictly finite and non-zero.
   - Closed bound orbits require $0.0 \le e < 1.0$ (hyperbolic $e \ge 1.0$ rejected for closed Earth monitoring).
   - Periapsis radius $r_p = a(1 - e) > R_\oplus$ ($6,378.137\text{ km}$), preventing subterranean collision with the physical Earth surface.
   - Specific mechanical energy $\mathcal{E} = \frac{v^2}{2} - \frac{\mu}{r} < 0$. Velocity magnitude is mathematically bounded above by local parabolic escape speed $v < \sqrt{2\mu/r}$, which varies from $11.18\text{ km/s}$ at surface to $4.35\text{ km/s}$ at GEO.
2. **Configurable Mission Operational Constraints (Advisory Warnings):**
   - **Low Earth Orbit (LEO):** $h \in [150, 2,000]\text{ km}$; typical speeds $v \in [6.9, 7.8]\text{ km/s}$.
   - **Medium Earth Orbit (MEO):** $h \in [2,000, 35,786]\text{ km}$; e.g., GNSS constellations ($a \approx 26,560\text{ km}$).
   - **Geostationary Orbit (GEO):** $a \approx 42,164.14\text{ km}$, $e \approx 0.0$, circular orbital speed $v \approx 3.075\text{ km/s}$.
   - **Highly Elliptical Orbit (HEO):** Molniya ($a \approx 26,600\text{ km}, e \approx 0.74, i \approx 63.4^\circ$), where apogee velocity drops to $\sim 1.5\text{ km/s}$.
   *The system accepts any mathematically bound Earth orbit without rejecting valid high-altitude or high-eccentricity missions.*

### 2.3 Mean Anomaly vs True Anomaly Resolution

For non-circular orbits ($e > 0$), Mean Anomaly $M$ is **not** equal to True Anomaly $\nu$. The system solves the non-linear relationship rigorously using Kepler's Equation:

$$\tan\left(\frac{E}{2}\right) = \sqrt{\frac{1 - e}{1 + e}} \tan\left(\frac{\nu}{2}\right)$$
$$M = E - e \sin(E)$$

Conversely, given $M$, the system performs Newton-Raphson iteration on $f(E) = E - e \sin(E) - M = 0$ to machine convergence ($|\Delta E| < 10^{-12}$), then determines $\nu$:
$$\tan\left(\frac{\nu}{2}\right) = \sqrt{\frac{1 + e}{1 - e}} \tan\left(\frac{E}{2}\right)$$

### 2.4 Inertial Cartesian State Schema (ECI J2000)

Cartesian state vectors describe position and velocity in Earth-Centered Inertial J2000 coordinates:

```json
{
  "r_j2000_km": [7000.0, 0.0, 1000.0],
  "v_j2000_km_s": [0.0, 7.546, 0.500],
  "epoch_utc": "2026-11-23T12:00:00Z"
}
```

| Field | Type | Units | Mathematical Validity Criteria |
| :--- | :--- | :--- | :--- |
| `r_j2000_km` | `[float, float, float]` | $\text{km}$ | $\|\mathbf{r}\| > 6,378.137\text{ km}$ ($h > 0\text{ km}$) |
| `v_j2000_km_s` | `[float, float, float]` | $\text{km/s}$ | $\|\mathbf{v}\| < \sqrt{2\mu / \|\mathbf{r}\|}$ (strictly bound sub-escape velocity) |
| `epoch_utc` | `string (ISO-8601)` | UTC | Valid ISO-8601 timestamp with UTC designator `Z` |

---

## 3. Custom Satellite Schema

Custom satellites represent controlled, active spacecraft with telemetry, propulsion, and mass properties:

```json
{
  "object_id": "CUSTOM_SAT_101",
  "name": "HYPERSPECTRAL_EARTH_OBSERVER",
  "input_mode": "KEPLERIAN",
  "keplerian": {
    "semi_major_axis_km": 7078.137,
    "eccentricity": 0.0012,
    "inclination_deg": 97.5,
    "raan_deg": 125.4,
    "arg_perigee_deg": 45.0,
    "mean_anomaly_deg": 180.0
  },
  "physical_properties": {
    "dry_mass_kg": 850.0,
    "fuel_mass_kg": 65.0,
    "cross_section_m2": 5.2,
    "hard_body_radius_m": 2.8,
    "drag_coefficient_cd": 2.2,
    "reflectivity_cr": 1.3
  },
  "propulsion": {
    "thruster_type": "HYDRAZINE_MONOPROPELLANT",
    "thrust_n": 22.0,
    "isp_sec": 225.0,
    "min_impulse_bit_ns": 0.05
  },
  "owner_operator": "COMMERCIAL_OPERATOR_EU",
  "status": "ACTIVE_PROPULSIVE"
}
```

---

## 4. Custom Debris Schema & Handling Unknown Properties

Aerospace debris tracking frequently involves fragments whose mass, shape, area, and ballistic characteristics are unknown. The schema explicitly avoids fabricating default values and tracks confidence provenance:

```json
{
  "object_id": "DEBRIS_UNKNOWN_2026_01",
  "name": "FRAGMENT_COSMOS_DEBRIS",
  "input_mode": "CARTESIAN",
  "cartesian": {
    "r_j2000_km": [7075.250, 15.420, 2.100],
    "v_j2000_km_s": [0.012, 7.548, 0.495]
  },
  "physical_properties": {
    "estimated_rcs_m2": 0.12,
    "hard_body_radius_m": 1.2,
    "area_to_mass_ratio": null,
    "dry_mass_kg": null,
    "drag_coefficient_cd": null
  },
  "provenance_metadata": {
    "estimated_rcs_m2": {"source": "RADAR_ESTIMATE", "confidence": "APPROXIMATE"},
    "hard_body_radius_m": {"source": "OPERATOR_BOUND", "confidence": "CONSERVATIVE"},
    "area_to_mass_ratio": {"source": "UNAVAILABLE", "confidence": "UNKNOWN"}
  },
  "status": "PASSIVE_TUMBLING"
}
```

### 4.1 Provenance Types
- `OPERATOR_SUPPLIED`: Manual operator parameter entry or simulation configuration.
- `PUBLIC_DATABASE`: ESA DISCOS or UCS Satellite Database records.
- `RADAR_ESTIMATE`: Ground-based radar cross-section (RCS) observation.
- `CONSERVATIVE_ENVELOPE`: Worst-case collision bounding sphere.
- `UNKNOWN`: Parameter is unmeasured; downstream models apply strict fallback logic.

---

## 5. Scenario Isolation and Persistence

1. **Isolation Boundary:**
   - User-created satellites and debris reside in the active `ScenarioManager` runtime layer.
   - Authoritative D1/D2 scenario files (`D2/scenarios/`) and baseline demonstration data (`CARTOSAT-3` vs `DEBRIS_PIECE_99`) are strictly read-only and immutable.
2. **Scenario Reset Contract:**
   - Issuing `POST /api/v1/scenario/reset` purges all custom objects and restores the baseline eight-step demonstration configuration immediately.
3. **Session Import / Export:**
   - Full scenario configurations (including custom objects, hardware records, and planned manoeuvres) can be exported to a single portable JSON manifest via `GET /api/v1/scenario/export` and re-imported via `POST /api/v1/scenario/import`.

---

## 6. REST API Endpoint Reference

| Endpoint | Method | Description |
| :--- | :--- | :--- |
| `/api/v1/custom-objects/satellite` | `POST` | Register a new custom satellite |
| `/api/v1/custom-objects/debris` | `POST` | Register a new custom debris object |
| `/api/v1/custom-objects/{object_id}` | `GET` | Retrieve custom object record by ID |
| `/api/v1/custom-objects/{object_id}` | `PUT` | Update orbital or physical parameters |
| `/api/v1/custom-objects/{object_id}` | `DELETE` | Remove custom object from active scenario |
| `/api/v1/custom-objects` | `GET` | List all active custom objects |
| `/api/v1/scenario/reset` | `POST` | Purge custom objects and reset to baseline demonstration |
| `/api/v1/scenario/export` | `GET` | Export entire scenario configuration to JSON |
| `/api/v1/scenario/import` | `POST` | Import scenario configuration from JSON |
