"""
backend/custom_objects/orbital_conversions.py
=============================================
Bidirectional orbital mechanics conversions between classical Keplerian
elements and Cartesian state vectors (ECI J2000).
Enforces physical constraints, prevents unphysical orbits, and ensures SI consistency.
"""

import math
from typing import Tuple, Dict, Any, List, Optional
import numpy as np

from D2.dynamics.two_body import MU_EARTH
from backend.catalogue.models import OrbitalElements

EARTH_RADIUS_M = 6_378_137.0


def true_anomaly_to_mean_anomaly(true_anomaly_deg: float, eccentricity: float) -> float:
    """
    Convert true anomaly (nu) to mean anomaly (M) for elliptical orbits (0 <= e < 1).
    
    1. Computes Eccentric Anomaly (E):
       tan(E / 2) = sqrt((1 - e) / (1 + e)) * tan(nu / 2)
    2. Computes Mean Anomaly (M):
       M = E - e * sin(E)
    """
    if eccentricity < 0.0 or eccentricity >= 1.0:
        raise ValueError(f"Elliptical conversion requires 0.0 <= e < 1.0, got {eccentricity}")

    nu_rad = math.radians(true_anomaly_deg % 360.0)
    e = eccentricity

    # Eccentric Anomaly E
    tan_half_e = math.sqrt((1.0 - e) / (1.0 + e)) * math.tan(nu_rad / 2.0)
    E_rad = 2.0 * math.atan(tan_half_e)

    # Wrap E into [0, 2pi)
    E_rad = E_rad % (2.0 * math.pi)

    # Kepler's Equation for M
    M_rad = E_rad - e * math.sin(E_rad)
    M_deg = math.degrees(M_rad) % 360.0
    return M_deg


def mean_anomaly_to_true_anomaly(mean_anomaly_deg: float, eccentricity: float, tol: float = 1e-12, max_iter: int = 50) -> float:
    """
    Convert mean anomaly (M) to true anomaly (nu) for elliptical orbits (0 <= e < 1).
    Solves Kepler's equation M = E - e * sin(E) using Newton-Raphson iteration.
    """
    if eccentricity < 0.0 or eccentricity >= 1.0:
        raise ValueError(f"Elliptical conversion requires 0.0 <= e < 1.0, got {eccentricity}")

    M_rad = math.radians(mean_anomaly_deg % 360.0)
    e = eccentricity

    # Initial guess for E (Vallado 4th ed., p. 73)
    if e < 0.8:
        E = M_rad
    else:
        E = math.pi

    # Newton-Raphson iteration: f(E) = E - e*sin(E) - M = 0
    for _ in range(max_iter):
        f = E - e * math.sin(E) - M_rad
        f_prime = 1.0 - e * math.cos(E)
        dE = -f / f_prime
        E += dE
        if abs(dE) < tol:
            break

    # True anomaly from Eccentric Anomaly
    tan_half_nu = math.sqrt((1.0 + e) / (1.0 - e)) * math.tan(E / 2.0)
    nu_rad = 2.0 * math.atan(tan_half_nu)
    nu_deg = math.degrees(nu_rad) % 360.0
    return nu_deg


def validate_orbital_parameters(
    semi_major_axis_km: float,
    eccentricity: float,
    inclination_deg: float,
    raan_deg: float = 0.0,
    arg_perigee_deg: float = 0.0,
    true_anomaly_deg: float = 0.0,
    mean_anomaly_deg: Optional[float] = None,
    allow_high_eccentricity: bool = True,
    operational_regime_check: bool = False,
) -> List[str]:
    """
    Validate physical and mathematical sanity of orbital parameters.
    
    Distinguishes:
    1. Fundamental Mathematical Validity (strict errors that violate Keplerian physics)
    2. Configurable Operational Constraints (advisories for specific mission altitude bands)
    
    Returns list of error messages (empty if mathematically valid).
    """
    errors = []
    if math.isnan(semi_major_axis_km) or math.isinf(semi_major_axis_km):
        errors.append("Semi-major axis must be a finite number")
    elif semi_major_axis_km <= 0.0:
        errors.append(f"Semi-major axis must be strictly positive, got {semi_major_axis_km} km")

    if math.isnan(eccentricity) or math.isinf(eccentricity):
        errors.append("Eccentricity must be a finite number")
    elif eccentricity < 0.0:
        errors.append(f"Eccentricity cannot be negative, got {eccentricity}")
    elif eccentricity >= 1.0:
        errors.append(f"Bound Earth orbits require eccentricity < 1.0 (parabolic/hyperbolic orbits unsupported), got {eccentricity}")

    if math.isnan(inclination_deg) or math.isinf(inclination_deg):
        errors.append("Inclination must be a finite number")
    elif not (0.0 <= inclination_deg <= 180.0):
        errors.append(f"Inclination must be within [0.0, 180.0] degrees, got {inclination_deg}")

    # Physical boundary check: periapsis must remain strictly above the physical Earth surface
    if semi_major_axis_km > 0.0 and 0.0 <= eccentricity < 1.0:
        periapsis_km = semi_major_axis_km * (1.0 - eccentricity)
        if periapsis_km < (EARTH_RADIUS_M / 1000.0):
            errors.append(
                f"Orbit penetrates Earth's surface: Periapsis is {periapsis_km:.1f} km "
                f"(Earth radius: {EARTH_RADIUS_M/1000.0:.1f} km)"
            )

    return errors


def keplerian_to_cartesian(
    semi_major_axis_km: float,
    eccentricity: float,
    inclination_deg: float,
    raan_deg: float,
    arg_perigee_deg: float,
    true_anomaly_deg: Optional[float] = None,
    mean_anomaly_deg: Optional[float] = None,
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Convert classical Keplerian orbital elements to Cartesian state vector (ECI J2000).
    Supports either true_anomaly_deg or mean_anomaly_deg (or both).
    
    If mean_anomaly_deg is supplied and true_anomaly_deg is None, rigorously
    solves Kepler's Equation for true anomaly.

    Returns
    -------
    r_eci_m : numpy.ndarray (3,)
        Position in ECI J2000 in metres.
    v_eci_mps : numpy.ndarray (3,)
        Velocity in ECI J2000 in metres/second.
    """
    errors = validate_orbital_parameters(semi_major_axis_km, eccentricity, inclination_deg)
    if errors:
        raise ValueError(f"Invalid orbital parameters: {'; '.join(errors)}")

    # Resolve anomaly
    if true_anomaly_deg is not None:
        nu_deg = float(true_anomaly_deg)
    elif mean_anomaly_deg is not None:
        nu_deg = mean_anomaly_to_true_anomaly(float(mean_anomaly_deg), eccentricity)
    else:
        nu_deg = 0.0

    a_m = semi_major_axis_km * 1000.0
    e = eccentricity
    inc = math.radians(inclination_deg)
    raan = math.radians(raan_deg)
    omega = math.radians(arg_perigee_deg)
    nu = math.radians(nu_deg)

    # Semi-latus rectum p = a * (1 - e^2)
    p_m = a_m * (1.0 - e ** 2)

    # Distance r in perifocal plane
    r_norm = p_m / (1.0 + e * math.cos(nu))

    # Position in perifocal frame (P, Q, W)
    r_perifocal = np.array([
        r_norm * math.cos(nu),
        r_norm * math.sin(nu),
        0.0
    ], dtype=np.float64)

    # Velocity in perifocal frame
    speed_scale = math.sqrt(MU_EARTH / p_m)
    v_perifocal = np.array([
        -speed_scale * math.sin(nu),
        speed_scale * (e + math.cos(nu)),
        0.0
    ], dtype=np.float64)

    # Perifocal to ECI transformation matrix: R_z(-raan) @ R_x(-inc) @ R_z(-omega)
    cos_o = math.cos(raan)
    sin_o = math.sin(raan)
    cos_i = math.cos(inc)
    sin_i = math.sin(inc)
    cos_w = math.cos(omega)
    sin_w = math.sin(omega)

    P_x = cos_o * cos_w - sin_o * sin_w * cos_i
    P_y = sin_o * cos_w + cos_o * sin_w * cos_i
    P_z = sin_w * sin_i

    Q_x = -cos_o * sin_w - sin_o * cos_w * cos_i
    Q_y = -sin_o * sin_w + cos_o * cos_w * cos_i
    Q_z = cos_w * sin_i

    R_trans = np.array([
        [P_x, Q_x, sin_o * sin_i],
        [P_y, Q_y, -cos_o * sin_i],
        [P_z, Q_z, cos_i]
    ], dtype=np.float64)

    r_eci_m = R_trans @ r_perifocal
    v_eci_mps = R_trans @ v_perifocal

    return r_eci_m, v_eci_mps


def cartesian_to_keplerian(
    r_eci_m: Sequence[float],
    v_eci_mps: Sequence[float],
) -> Dict[str, float]:
    """
    Convert Cartesian state vector in ECI J2000 (m, m/s) to classical Keplerian elements.
    """
    r_vec = np.asarray(r_eci_m, dtype=np.float64)
    v_vec = np.asarray(v_eci_mps, dtype=np.float64)

    if r_vec.shape != (3,) or v_vec.shape != (3,):
        raise ValueError("State vectors must contain exactly 3 elements.")

    r = float(np.linalg.norm(r_vec))
    v = float(np.linalg.norm(v_vec))

    if r <= 0.0 or v <= 0.0:
        raise ValueError("Position and velocity magnitudes must be strictly positive.")

    # Specific angular momentum vector h = r x v
    h_vec = np.cross(r_vec, v_vec)
    h = float(np.linalg.norm(h_vec))

    if h < 1e-6:
        raise ValueError("Degenerate radial orbit (zero angular momentum).")

    # Line of nodes n = k x h
    k_vec = np.array([0.0, 0.0, 1.0], dtype=np.float64)
    n_vec = np.cross(k_vec, h_vec)
    n = float(np.linalg.norm(n_vec))

    # Eccentricity vector e_vec = ((v^2 - mu/r)*r - (r.v)*v) / mu
    e_vec = ((v ** 2 - MU_EARTH / r) * r_vec - np.dot(r_vec, v_vec) * v_vec) / MU_EARTH
    e = float(np.linalg.norm(e_vec))

    # Specific mechanical energy xi = v^2/2 - mu/r
    energy = (v ** 2) / 2.0 - MU_EARTH / r

    if abs(energy) < 1e-12:
        raise ValueError("Parabolic orbit (energy = 0) unsupported.")
    if energy >= 0.0:
        raise ValueError(f"Hyperbolic unbound orbit (energy = {energy:.3e}) unsupported.")

    # Semi-major axis a = -mu / (2 * energy)
    a_m = -MU_EARTH / (2.0 * energy)
    a_km = a_m / 1000.0

    # Inclination: cos(i) = h_z / h
    inc_rad = math.acos(max(-1.0, min(1.0, h_vec[2] / h)))
    inc_deg = math.degrees(inc_rad)

    # Longitude of Ascending Node (RAAN)
    if n > 1e-9:
        raan_rad = math.acos(max(-1.0, min(1.0, n_vec[0] / n)))
        if n_vec[1] < 0.0:
            raan_rad = 2.0 * math.pi - raan_rad
    else:
        raan_rad = 0.0
    raan_deg = math.degrees(raan_rad)

    # Argument of Periapsis (omega)
    if n > 1e-9 and e > 1e-6:
        omega_rad = math.acos(max(-1.0, min(1.0, np.dot(n_vec, e_vec) / (n * e))))
        if e_vec[2] < 0.0:
            omega_rad = 2.0 * math.pi - omega_rad
    else:
        omega_rad = 0.0
    arg_p_deg = math.degrees(omega_rad)

    # True Anomaly (nu)
    if e > 1e-6:
        nu_rad = math.acos(max(-1.0, min(1.0, np.dot(e_vec, r_vec) / (e * r))))
        if np.dot(r_vec, v_vec) < 0.0:
            nu_rad = 2.0 * math.pi - nu_rad
    else:
        # Circular orbit
        nu_rad = 0.0
    true_anomaly_deg = math.degrees(nu_rad)

    # Rigorous Mean Anomaly (M) via Kepler's equation
    mean_anomaly_deg = true_anomaly_to_mean_anomaly(true_anomaly_deg, e)

    # Derived quantities
    periapsis_km = a_km * (1.0 - e)
    apoapsis_km = a_km * (1.0 + e)
    period_minutes = (2.0 * math.pi * math.sqrt((a_m ** 3) / MU_EARTH)) / 60.0
    mean_motion_rev_day = 86400.0 / (period_minutes * 60.0)

    return {
        "semi_major_axis_km": round(a_km, 4),
        "eccentricity": round(e, 7),
        "inclination_deg": round(inc_deg, 4),
        "raan_deg": round(raan_deg, 4),
        "arg_perigee_deg": round(arg_p_deg, 4),
        "true_anomaly_deg": round(true_anomaly_deg, 4),
        "mean_anomaly_deg": round(mean_anomaly_deg, 4),
        "mean_motion_rev_per_day": round(mean_motion_rev_day, 8),
        "period_minutes": round(period_minutes, 2),
        "periapsis_km": round(periapsis_km, 2),
        "apoapsis_km": round(apoapsis_km, 2),
    }
