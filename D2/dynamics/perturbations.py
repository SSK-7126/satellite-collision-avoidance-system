"""
D2/dynamics/perturbations.py
===========================
Orbital Perturbations Module: Earth J2 Oblateness & Atmospheric Drag.
Strictly following Section 3.3 and Section 12.1 of the Technical Development Guide.

Architectural Guarantees:
1. Strict Opt-In Design:
   - Two-body Keplerian point-mass gravity remains the authoritative default.
   - Perturbations are applied ONLY when explicitly enabled by configuration flags.
   - When perturbations are disabled, solver output matches two-body baseline to float64 machine precision.
2. Earth J2 Zonal Harmonic Perturbation:
   - Models Earth's equatorial bulge (equatorial radius Re = 6378137.0 m, J2 = 1.08262668e-3).
   - Analytical formulation:
     a_J2,x = -(3/2) * J2 * mu * Re^2 * x / r^5 * (1 - 5 * z^2 / r^2)
     a_J2,y = -(3/2) * J2 * mu * Re^2 * y / r^5 * (1 - 5 * z^2 / r^2)
     a_J2,z = -(3/2) * J2 * mu * Re^2 * z / r^5 * (3 - 5 * z^2 / r^2)
3. Atmospheric Drag Perturbation:
   - Models aerodynamic friction in Low Earth Orbit:
     a_drag = -0.5 * rho(h) * (Cd * A / m) * |v_rel| * v_rel
   - Relative velocity v_rel accounts for Earth atmospheric co-rotation:
     v_rel = v - omega_Earth x r
   - Exponential atmospheric density model with altitude scale height.

Conventions & Units:
- Reference Frame : Earth-Centred Inertial (ECI J2000)
- Position / Altitude : Metres (m)
- Velocity            : Metres per second (m/s)
- Density             : kg/m^3
- Acceleration        : m/s^2
- Precision           : Float64
"""

from dataclasses import dataclass
from typing import Tuple, Optional, Dict, Any
import numpy as np

from D2.dynamics.two_body import MU_EARTH, gravitational_acceleration

# WGS84 Physical Geopotential Constants
EARTH_EQUATORIAL_RADIUS_M = 6378137.0     # WGS84 Earth semi-major axis (m)
EARTH_J2 = 1.08262668e-3                  # WGS84 J2 oblateness parameter (dimensionless)
EARTH_ROTATION_RATE_RAD_S = 7.292115e-5   # Earth angular rotation rate (rad/s)

# Standard Atmospheric LEO Reference Parameters (~600 km nominal altitude)
ATMOSPHERE_REF_H0_M = 600000.0             # 600 km reference altitude
ATMOSPHERE_REF_RHO0_KG_M3 = 1.454e-13      # kg/m^3 at 600 km
ATMOSPHERE_SCALE_HEIGHT_H_M = 71835.0      # Scale height in metres (~71.8 km)


@dataclass
class ForceModelConfig:
    """
    Configuration flags and physical parameters for orbital force modeling.
    (Technical Guide Section 3.3)
    """
    include_j2: bool = False
    include_drag: bool = False
    spacecraft_mass_kg: float = 1000.0
    drag_area_m2: float = 5.0
    drag_coefficient_cd: float = 2.2
    j2_value: float = EARTH_J2
    earth_radius_m: float = EARTH_EQUATORIAL_RADIUS_M


def calculate_j2_acceleration(
    position_eci: np.ndarray,
    mu: float = MU_EARTH,
    j2: float = EARTH_J2,
    re: float = EARTH_EQUATORIAL_RADIUS_M
) -> np.ndarray:
    """
    Calculate Earth J2 equatorial bulge perturbing acceleration in ECI coordinates.
    (Technical Guide Section 3.3)

    Parameters
    ----------
    position_eci : array-like
        Position vector [x, y, z] in metres.
    mu : float, optional
        Gravitational parameter (m^3/s^2).
    j2 : float, optional
        J2 zonal harmonic coefficient.
    re : float, optional
        Earth equatorial radius (metres).

    Returns
    -------
    a_j2 : numpy.ndarray
        Perturbing acceleration vector [ax, ay, az] in m/s^2.
    """
    r_vec = np.asarray(position_eci, dtype=np.float64)
    r = float(np.linalg.norm(r_vec))

    if r <= 0.0:
        raise ValueError("Position vector norm must be strictly positive.")

    x, y, z = r_vec[0], r_vec[1], r_vec[2]
    r2 = r * r
    r5 = r2 * r2 * r
    z2_over_r2 = (z * z) / r2

    factor = 1.5 * j2 * mu * (re * re) / r5

    ax = -factor * x * (1.0 - 5.0 * z2_over_r2)
    ay = -factor * y * (1.0 - 5.0 * z2_over_r2)
    az = -factor * z * (3.0 - 5.0 * z2_over_r2)

    return np.array([ax, ay, az], dtype=np.float64)


def get_atmospheric_density(altitude_m: float) -> float:
    """
    Calculate atmospheric density using an exponential density model in LEO.
    rho(h) = rho0 * exp(-(h - h0) / H)
    """
    h = max(0.0, float(altitude_m))
    delta_h = h - ATMOSPHERE_REF_H0_M
    rho = ATMOSPHERE_REF_RHO0_KG_M3 * np.exp(-delta_h / ATMOSPHERE_SCALE_HEIGHT_H_M)
    return float(np.clip(rho, 0.0, 1.0))


def calculate_drag_acceleration(
    position_eci: np.ndarray,
    velocity_eci: np.ndarray,
    mass_kg: float = 1000.0,
    area_m2: float = 5.0,
    cd: float = 2.2,
    re: float = EARTH_EQUATORIAL_RADIUS_M
) -> np.ndarray:
    """
    Calculate atmospheric drag perturbing acceleration in ECI coordinates.
    (Technical Guide Section 3.3)

    Parameters
    ----------
    position_eci : array-like
        Position vector in metres.
    velocity_eci : array-like
        Inertial velocity vector in m/s.
    mass_kg : float, optional
        Spacecraft mass in kg.
    area_m2 : float, optional
        Cross-sectional drag area in m^2.
    cd : float, optional
        Aerodynamic drag coefficient (typically 2.0 - 2.2 for LEO).
    re : float, optional
        Earth equatorial radius in metres.

    Returns
    -------
    a_drag : numpy.ndarray
        Drag acceleration vector [ax, ay, az] in m/s^2.
    """
    r_vec = np.asarray(position_eci, dtype=np.float64)
    v_vec = np.asarray(velocity_eci, dtype=np.float64)
    r = float(np.linalg.norm(r_vec))

    if mass_kg <= 0.0 or area_m2 <= 0.0 or cd <= 0.0:
        raise ValueError("Mass, area, and Cd must be strictly positive.")

    altitude = r - re
    if altitude < 0.0:
        # Beneath Earth surface
        altitude = 0.0

    rho = get_atmospheric_density(altitude)

    # Relative velocity accounting for Earth atmospheric co-rotation:
    # v_rel = v - omega_Earth x r
    # omega_Earth = [0, 0, omega]
    v_atm = np.array([
        -EARTH_ROTATION_RATE_RAD_S * r_vec[1],
        EARTH_ROTATION_RATE_RAD_S * r_vec[0],
        0.0
    ], dtype=np.float64)

    v_rel = v_vec - v_atm
    v_rel_mag = float(np.linalg.norm(v_rel))

    if v_rel_mag <= 1e-9 or rho <= 0.0:
        return np.zeros(3, dtype=np.float64)

    # a_drag = -0.5 * rho * (Cd * A / m) * |v_rel| * v_rel
    bc_inv = (cd * area_m2) / mass_kg  # Inverse ballistic coefficient (m^2/kg)
    a_drag = -0.5 * rho * bc_inv * v_rel_mag * v_rel

    return a_drag


def total_orbital_acceleration(
    position_eci: np.ndarray,
    velocity_eci: np.ndarray,
    config: Optional[ForceModelConfig] = None
) -> np.ndarray:
    """
    Compute total orbital acceleration with modular, opt-in force models.
    """
    # 1. Base point-mass two-body gravity (authoritative baseline)
    a_total = gravitational_acceleration(position_eci)

    if config is None:
        return a_total

    # 2. Opt-in Earth J2 oblateness
    if config.include_j2:
        a_j2 = calculate_j2_acceleration(
            position_eci,
            j2=config.j2_value,
            re=config.earth_radius_m
        )
        a_total = a_total + a_j2

    # 3. Opt-in Atmospheric Drag
    if config.include_drag:
        a_drag = calculate_drag_acceleration(
            position_eci,
            velocity_eci,
            mass_kg=config.spacecraft_mass_kg,
            area_m2=config.drag_area_m2,
            cd=config.drag_coefficient_cd,
            re=config.earth_radius_m
        )
        a_total = a_total + a_drag

    return a_total


def rk4_step_perturbed(
    state: np.ndarray,
    dt: float,
    config: Optional[ForceModelConfig] = None
) -> np.ndarray:
    """
    Perform one Runge-Kutta 4 step including opt-in perturbations.
    """
    y = np.asarray(state, dtype=np.float64)

    def deriv(s):
        pos = s[:3]
        vel = s[3:]
        acc = total_orbital_acceleration(pos, vel, config=config)
        return np.concatenate((vel, acc))

    k1 = deriv(y)
    k2 = deriv(y + 0.5 * dt * k1)
    k3 = deriv(y + 0.5 * dt * k2)
    k4 = deriv(y + dt * k3)

    return y + (dt / 6.0) * (k1 + 2.0 * k2 + 2.0 * k3 + k4)


def propagate_orbit_perturbed(
    initial_state: np.ndarray,
    duration: float,
    dt: float = 1.0,
    config: Optional[ForceModelConfig] = None
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Propagate an orbital state over a specified duration with optional force models.
    (Technical Guide Section 3.3)

    Parameters
    ----------
    initial_state : array-like
        Initial 6D state [x, y, z, vx, vy, vz] in SI units.
    duration : float
        Total duration in seconds.
    dt : float, optional
        Integration time step in seconds (default: 1.0 s).
    config : ForceModelConfig, optional
        Perturbing force model configuration (default: None, pure two-body).

    Returns
    -------
    times : numpy.ndarray
        Array of simulation timestamps.
    states : numpy.ndarray
        Array of propagated 6D states at each timestamp.
    """
    if duration <= 0.0 or dt <= 0.0:
        raise ValueError("Duration and dt must be strictly positive.")

    curr_state = np.asarray(initial_state, dtype=np.float64).copy()
    times = [0.0]
    states = [curr_state.copy()]
    elapsed = 0.0

    while elapsed < duration:
        step = min(dt, duration - elapsed)
        curr_state = rk4_step_perturbed(curr_state, step, config=config)
        elapsed += step
        times.append(elapsed)
        states.append(curr_state.copy())

    return np.array(times, dtype=np.float64), np.array(states, dtype=np.float64)
