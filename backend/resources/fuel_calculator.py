"""
backend/resources/fuel_calculator.py
====================================
Analytical rocket propellant consumption and delta-v capacity calculator.
Strictly relies on the classical Tsiolkovsky Rocket Equation:
  Delta-v = Isp * g0 * ln(m0 / m1)
  Delta-m = m0 * (1 - exp(-Delta-v / (Isp * g0)))
"""

import math

# Standard standard gravitational acceleration at Earth's surface (m/s^2)
G0_STANDARD = 9.80665


def estimate_propellant_consumption(
    initial_mass_kg: float,
    delta_v_mps: float,
    isp_sec: float,
) -> float:
    """
    Calculate estimated propellant mass consumed for an impulsive delta-v burn.
    
    Parameters
    ----------
    initial_mass_kg : float
        Total wet mass of spacecraft before burn in kilograms.
    delta_v_mps : float
        Manoeuvre impulsive velocity increment in m/s.
    isp_sec : float
        Effective specific impulse in seconds.

    Returns
    -------
    propellant_consumed_kg : float
        Estimated propellant consumed in kilograms.

    Raises
    ------
    ValueError
        If inputs are unphysical or non-positive.
    """
    if initial_mass_kg <= 0.0:
        raise ValueError(f"Initial mass must be strictly positive, got {initial_mass_kg}")
    if delta_v_mps < 0.0:
        raise ValueError(f"Delta-v magnitude cannot be negative, got {delta_v_mps}")
    if isp_sec <= 0.0:
        raise ValueError(f"Specific impulse (Isp) must be strictly positive, got {isp_sec}")

    if delta_v_mps == 0.0:
        return 0.0

    # Exhaust velocity c = Isp * g0
    exhaust_velocity = isp_sec * G0_STANDARD

    # Fraction of mass remaining: m1 / m0 = exp(-dv / c)
    mass_ratio = math.exp(-delta_v_mps / exhaust_velocity)

    # Propellant consumed: dm = m0 * (1 - mass_ratio)
    propellant_consumed = initial_mass_kg * (1.0 - mass_ratio)

    return propellant_consumed


def estimate_delta_v_capacity(
    dry_mass_kg: float,
    propellant_kg: float,
    isp_sec: float,
) -> float:
    """
    Calculate maximum delta-v achievable with available propellant.
    """
    if dry_mass_kg <= 0.0 or propellant_kg < 0.0 or isp_sec <= 0.0:
        return 0.0

    m0 = dry_mass_kg + propellant_kg
    m1 = dry_mass_kg

    exhaust_velocity = isp_sec * G0_STANDARD
    delta_v_max = exhaust_velocity * math.log(m0 / m1)

    return delta_v_max
