"""
D2/manoeuvres/propulsion.py
===========================
Propulsion Subsystem, Finite-Duration Thrust Modeling, Dynamic Mass Depletion,
and Manoeuvre Execution Uncertainty for Deliverable 2 (D2).
Strictly following Section 7 of the Satellite Anti-Collision Technical Guide.

Key Capabilities:
1. Spacecraft Propulsion Properties:
   - Specific impulse (Isp in seconds), standard gravity (g0 = 9.80665 m/s^2).
   - Thrust level (T in Newtons), mass flow rate dm/dt = T / (Isp * g0).
   - Spacecraft wet mass and remaining propellant budget.
   - Physical constraints: maximum burn duration, minimum impulse bit, slew limits.
2. Tsiolkovsky Rocket Equation & Propellant Consumption:
   - Delta-v = Isp * g0 * ln(m0 / mf).
   - Propellant mass consumed: Delta_m = m0 * (1 - exp(-Delta_v / (Isp * g0))).
3. Finite-Duration Thrust Propagation:
   - State derivative includes gravitational acceleration and continuous thrust:
     dr/dt = v
     dv/dt = a_gravity(r) + (T / m(t)) * u_thrust
     dm/dt = -T / (Isp * g0)
   - Integrated using Runge-Kutta 4 (RK4).
4. Execution Uncertainty Model:
   - Magnitude dispersion: Delta_v_actual = Delta_v_nominal * (1 + N(0, sigma_mag^2)).
   - Pointing dispersion: Spherical deflection angle theta_err ~ N(0, sigma_pointing^2).
   - Fully deterministic and reproducible using configurable random seeds.
5. Invariant Preservation:
   - Impulsive delta-v model remains the primary validated baseline.
   - Illustrative mass/Isp values are clearly noted as non-operational defaults.

Conventions & Units:
- Reference Frame : Earth-Centred Inertial (ECI) / local RTN
- Thrust          : Newtons (N)
- Mass            : Kilograms (kg)
- Velocities      : Metres per second (m/s)
- Time            : Seconds (s)
- Precision       : Float64
"""

from dataclasses import dataclass, field
from typing import Tuple, Dict, Any, Optional
import numpy as np

from D2.dynamics.two_body import MU_EARTH, gravitational_acceleration
from D2.dynamics.rk4 import rk4_step
from D2.manoeuvres.manoeuvre_model import compute_rtn_basis, rtn_to_eci, DIRECTION_VECTORS_RTN

# Standard terrestrial acceleration of gravity (SI: m/s^2)
G0_STANDARD = 9.80665


@dataclass
class PropulsionParameters:
    """
    Physical spacecraft propulsion and mass parameters.
    (Technical Guide Section 7.2 & 7.3)
    """
    wet_mass_kg: float = 1000.0              # Initial wet mass in kg (satellite bus + fuel)
    propellant_mass_kg: float = 50.0          # Usable propellant mass in kg
    thrust_n: float = 10.0                    # Available continuous thrust in Newtons
    isp_s: float = 300.0                      # Specific impulse in seconds
    min_impulse_bit_ns: float = 0.05          # Minimum controllable impulse bit (N*s)
    max_burn_duration_s: float = 600.0        # Thermal/operational continuous burn limit
    slew_rate_deg_per_s: float = 1.0          # Attitude slew rate limit in deg/s

    def __post_init__(self):
        if self.wet_mass_kg <= 0.0:
            raise ValueError("Wet mass must be strictly positive.")
        if self.propellant_mass_kg < 0.0 or self.propellant_mass_kg > self.wet_mass_kg:
            raise ValueError("Propellant mass must be between 0 and wet mass.")
        if self.thrust_n <= 0.0:
            raise ValueError("Thrust must be strictly positive.")
        if self.isp_s <= 0.0:
            raise ValueError("Specific impulse must be strictly positive.")

    @property
    def dry_mass_kg(self) -> float:
        """Dry mass of the spacecraft without propellant."""
        return self.wet_mass_kg - self.propellant_mass_kg

    @property
    def mass_flow_rate_kg_per_s(self) -> float:
        """Mass flow rate dm/dt = T / (Isp * g0) in kg/s."""
        return self.thrust_n / (self.isp_s * G0_STANDARD)

    @property
    def effective_exhaust_velocity_mps(self) -> float:
        """Effective exhaust velocity c = Isp * g0 in m/s."""
        return self.isp_s * G0_STANDARD


def calculate_propellant_mass_ideal(
    delta_v_mps: float,
    initial_mass_kg: float,
    isp_s: float = 300.0,
    g0: float = G0_STANDARD
) -> float:
    """
    Calculate propellant consumed for a given Delta-v using Tsiolkovsky's rocket equation.
    (Technical Guide Section 7.2)

    Formula:
        Delta_m = m0 * (1 - exp(-Delta_v / (Isp * g0)))

    Parameters
    ----------
    delta_v_mps : float
        Velocity increment magnitude in m/s.
    initial_mass_kg : float
        Initial spacecraft mass m0 in kg.
    isp_s : float, optional
        Specific impulse in seconds (default: 300.0 s).
    g0 : float, optional
        Standard gravitational acceleration (default: 9.80665 m/s^2).

    Returns
    -------
    propellant_kg : float
        Required propellant mass in kg.
    """
    dv = float(abs(delta_v_mps))
    m0 = float(initial_mass_kg)
    if m0 <= 0.0:
        raise ValueError("Initial mass must be positive.")
    if isp_s <= 0.0:
        raise ValueError("Specific impulse must be positive.")

    c = isp_s * g0
    fraction = 1.0 - np.exp(-dv / c)
    return float(m0 * fraction)


def calculate_delta_v_from_propellant(
    propellant_mass_kg: float,
    initial_mass_kg: float,
    isp_s: float = 300.0,
    g0: float = G0_STANDARD
) -> float:
    """
    Calculate Delta-v capability from a given propellant mass consumption.

    Formula:
        Delta_v = Isp * g0 * ln(m0 / (m0 - Delta_m))
    """
    mp = float(propellant_mass_kg)
    m0 = float(initial_mass_kg)
    if mp < 0.0 or mp >= m0:
        raise ValueError("Propellant mass must be non-negative and less than initial mass.")
    c = isp_s * g0
    return float(c * np.log(m0 / (m0 - mp)))


def finite_thrust_state_derivative(
    state_and_mass: np.ndarray,
    thrust_eci: np.ndarray,
    mass_flow_rate: float
) -> np.ndarray:
    """
    Calculate the 7D state derivative [vx, vy, vz, ax, ay, az, dm/dt]
    during active continuous thrust.

    Parameters
    ----------
    state_and_mass : array-like
        7-element array: [x, y, z, vx, vy, vz, mass].
    thrust_eci : array-like
        3D thrust vector in ECI frame [Tx, Ty, Tz] in Newtons.
    mass_flow_rate : float
        dm/dt in kg/s (positive scalar).

    Returns
    -------
    derivative : numpy.ndarray
        7-element state derivative array.
    """
    pos = state_and_mass[:3]
    vel = state_and_mass[3:6]
    mass = state_and_mass[6]

    if mass <= 0.0:
        raise ValueError("Spacecraft mass must be strictly positive.")

    # Gravitational acceleration
    a_grav = gravitational_acceleration(pos)

    # Thrust acceleration: a_thrust = T / m
    a_thrust = thrust_eci / mass

    a_total = a_grav + a_thrust
    dm_dt = -abs(mass_flow_rate)

    return np.concatenate((vel, a_total, [dm_dt]))


def rk4_step_finite_thrust(
    state_and_mass: np.ndarray,
    thrust_eci: np.ndarray,
    mass_flow_rate: float,
    dt: float
) -> np.ndarray:
    """
    Perform a single 4th-order Runge-Kutta step for the 7D state-mass vector.
    """
    y = np.asarray(state_and_mass, dtype=np.float64)
    f = lambda s: finite_thrust_state_derivative(s, thrust_eci, mass_flow_rate)

    k1 = f(y)
    k2 = f(y + 0.5 * dt * k1)
    k3 = f(y + 0.5 * dt * k2)
    k4 = f(y + dt * k3)

    return y + (dt / 6.0) * (k1 + 2.0 * k2 + 2.0 * k3 + k4)


def propagate_finite_burn(
    initial_state_eci: np.ndarray,
    thrust_direction_eci: np.ndarray,
    burn_duration_s: float,
    propulsion: PropulsionParameters,
    dt: float = 0.5
) -> Dict[str, Any]:
    """
    Propagate orbital state and mass depletion during a finite-duration thrust event.
    (Technical Guide Section 7.1 & 7.3)

    Parameters
    ----------
    initial_state_eci : array-like
        Initial 6D orbital state [x, y, z, vx, vy, vz] in SI units.
    thrust_direction_eci : array-like
        Unit vector of thrust pointing direction in ECI.
    burn_duration_s : float
        Duration of active burn in seconds.
    propulsion : PropulsionParameters
        Spacecraft propulsion system properties.
    dt : float, optional
        Integration time step in seconds (default: 0.5 s).

    Returns
    -------
    result : dict
        Propagation result containing final state, final mass, propellant consumed,
        effective Delta-v achieved, and trajectory time series.
    """
    s0 = np.asarray(initial_state_eci, dtype=np.float64)
    u_thrust = np.asarray(thrust_direction_eci, dtype=np.float64)
    u_norm = np.linalg.norm(u_thrust)
    if u_norm <= 0.0:
        raise ValueError("Thrust direction norm must be strictly positive.")
    u_thrust = u_thrust / u_norm

    duration = float(burn_duration_s)
    if duration <= 0.0:
        raise ValueError("Burn duration must be positive.")

    # Check propellant availability
    m_flow = propulsion.mass_flow_rate_kg_per_s
    req_propellant = m_flow * duration

    if req_propellant > propulsion.propellant_mass_kg:
        raise ValueError(
            f"Insufficient propellant: burn requires {req_propellant:.2f} kg, "
            f"available {propulsion.propellant_mass_kg:.2f} kg."
        )

    thrust_vec = propulsion.thrust_n * u_thrust

    # 7D state: [x, y, z, vx, vy, vz, m]
    state_7d = np.concatenate((s0, [propulsion.wet_mass_kg]))

    times = [0.0]
    states = [state_7d.copy()]
    elapsed = 0.0

    while elapsed < duration:
        step = min(dt, duration - elapsed)
        state_7d = rk4_step_finite_thrust(state_7d, thrust_vec, m_flow, step)
        elapsed += step
        times.append(elapsed)
        states.append(state_7d.copy())

    states_arr = np.array(states)
    times_arr = np.array(times)

    final_state_6d = states_arr[-1, :6]
    final_mass = float(states_arr[-1, 6])
    propellant_consumed = float(propulsion.wet_mass_kg - final_mass)

    # Compute effective delta-v achieved by integrating thrust acceleration:
    # Delta-v_effective = c * ln(m0 / mf)
    dv_ideal = propulsion.effective_exhaust_velocity_mps * np.log(propulsion.wet_mass_kg / final_mass)

    return {
        "final_state_eci": final_state_6d,
        "final_mass_kg": final_mass,
        "propellant_consumed_kg": propellant_consumed,
        "delta_v_effective_mps": float(dv_ideal),
        "burn_duration_s": duration,
        "thrust_magnitude_n": propulsion.thrust_n,
        "mass_flow_rate_kg_s": m_flow,
        "times_s": times_arr,
        "states_7d": states_arr,
    }


def apply_execution_uncertainty(
    delta_v_nominal_eci: np.ndarray,
    sigma_magnitude_rel: float = 0.01,
    sigma_pointing_deg: float = 0.5,
    seed: Optional[int] = None
) -> Dict[str, Any]:
    """
    Apply physical execution uncertainty (magnitude dispersion and pointing error)
    to a nominal Delta-v vector. (Technical Guide Section 7.3)

    Dispersions:
        - Magnitude error: delta_v_dispersed = |dv| * (1 + delta_mag), delta_mag ~ N(0, sigma_mag^2)
        - Pointing error: rotation of thrust axis by angle theta_err ~ N(0, sigma_pointing^2)
          around a randomly oriented transverse axis.

    Parameters
    ----------
    delta_v_nominal_eci : array-like
        Nominal Delta-v vector in ECI frame [dv_x, dv_y, dv_z] in m/s.
    sigma_magnitude_rel : float, optional
        Relative 1-sigma magnitude error (default: 0.01 = 1%).
    sigma_pointing_deg : float, optional
        1-sigma pointing error in degrees (default: 0.5 deg).
    seed : int, optional
        Deterministic random seed for reproducibility.

    Returns
    -------
    result : dict
        Dictionary containing dispersed Delta-v vector, magnitude, error offsets, and seed.
    """
    rng = np.random.default_rng(seed)
    dv_nom = np.asarray(delta_v_nominal_eci, dtype=np.float64)
    nom_mag = float(np.linalg.norm(dv_nom))

    if nom_mag <= 1e-12:
        return {
            "delta_v_actual_eci": dv_nom.copy(),
            "magnitude_actual_mps": 0.0,
            "magnitude_error_mps": 0.0,
            "pointing_error_deg": 0.0,
            "seed": seed,
        }

    u_nom = dv_nom / nom_mag

    # 1. Magnitude dispersion
    delta_mag_rel = rng.normal(0.0, sigma_magnitude_rel)
    actual_mag = max(0.0, nom_mag * (1.0 + delta_mag_rel))

    # 2. Pointing dispersion (Rodrigues' rotation formula around a random perpendicular axis)
    sigma_rad = np.radians(sigma_pointing_deg)
    pointing_err_rad = float(abs(rng.normal(0.0, sigma_rad)))
    pointing_err_deg = float(np.degrees(pointing_err_rad))

    # Construct an arbitrary orthogonal axis to u_nom
    if abs(u_nom[0]) < 0.9:
        ref = np.array([1.0, 0.0, 0.0])
    else:
        ref = np.array([0.0, 1.0, 0.0])
    perp1 = np.cross(u_nom, ref)
    perp1 = perp1 / np.linalg.norm(perp1)
    perp2 = np.cross(u_nom, perp1)

    # Random azimuthal deflection angle
    psi = rng.uniform(0.0, 2.0 * np.pi)
    rot_axis = np.cos(psi) * perp1 + np.sin(psi) * perp2

    # Rotate nominal unit vector by pointing_err_rad around rot_axis
    # Rodrigues' formula: v_rot = v*cos(th) + (k x v)*sin(th) + k*(k.v)*(1 - cos(th))
    u_actual = (
        u_nom * np.cos(pointing_err_rad)
        + np.cross(rot_axis, u_nom) * np.sin(pointing_err_rad)
        + rot_axis * np.dot(rot_axis, u_nom) * (1.0 - np.cos(pointing_err_rad))
    )
    u_actual = u_actual / np.linalg.norm(u_actual)

    dv_actual = actual_mag * u_actual

    return {
        "delta_v_actual_eci": dv_actual,
        "magnitude_actual_mps": actual_mag,
        "magnitude_error_mps": float(actual_mag - nom_mag),
        "pointing_error_deg": pointing_err_deg,
        "seed": seed,
    }
