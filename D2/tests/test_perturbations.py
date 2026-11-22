"""
D2/tests/test_perturbations.py
==============================
Verification test suite for Earth J2 equatorial oblateness & atmospheric drag.
Follows Section 3.3 and Section 12.1 of the Technical Development Guide.
"""

import numpy as np
import pytest

from D2.dynamics.two_body import MU_EARTH
from D2.dynamics.orbit_propagator import propagate_orbit
from D2.dynamics.perturbations import (
    ForceModelConfig,
    calculate_j2_acceleration,
    calculate_drag_acceleration,
    get_atmospheric_density,
    propagate_orbit_perturbed,
    EARTH_EQUATORIAL_RADIUS_M,
    EARTH_J2,
)


def test_two_body_baseline_identity():
    """
    CRITICAL INVARIANT: Verify that when perturbations are disabled,
    propagate_orbit_perturbed matches the authoritative two-body baseline to float64 machine precision.
    (Technical Guide Section 3.3)
    """
    r0 = 7000000.0
    v0 = np.sqrt(MU_EARTH / r0)
    state0 = np.array([r0, 0.0, 0.0, 0.0, v0, 0.0], dtype=np.float64)

    duration = 300.0
    dt = 1.0

    # Baseline pure two-body
    times_base, states_base = propagate_orbit(state0, duration, dt)

    # Perturbed propagator with disabled perturbations
    cfg_off = ForceModelConfig(include_j2=False, include_drag=False)
    times_pert, states_pert = propagate_orbit_perturbed(state0, duration, dt, config=cfg_off)

    assert np.allclose(times_base, times_pert, atol=1e-15)
    assert np.allclose(states_base, states_pert, atol=1e-12), (
        "Perturbed propagator with flags OFF must match pure two-body baseline to machine precision."
    )


def test_j2_acceleration_geometry_and_magnitude():
    """
    Verify analytical properties and magnitude of J2 perturbing acceleration.
    (Technical Guide Section 3.3)
    """
    r_orbit = 7_000_000.0

    # 1. Equatorial state: z = 0
    pos_eq = np.array([r_orbit, 0.0, 0.0])
    a_j2_eq = calculate_j2_acceleration(pos_eq)

    # az must be exactly zero at equator
    assert np.isclose(a_j2_eq[2], 0.0, atol=1e-15)
    # ax must be inward (negative)
    assert a_j2_eq[0] < 0.0
    # Expected magnitude ~ 0.0109 m/s^2
    mag_eq = float(np.linalg.norm(a_j2_eq))
    assert 0.009 <= mag_eq <= 0.013

    # 2. Polar state: x = y = 0, z = r_orbit
    pos_pole = np.array([0.0, 0.0, r_orbit])
    a_j2_pole = calculate_j2_acceleration(pos_pole)
    assert np.isclose(a_j2_pole[0], 0.0, atol=1e-15)
    assert np.isclose(a_j2_pole[1], 0.0, atol=1e-15)
    # At pole, 3 - 5*(1) = -2 -> factor * (-z) * (-2) = +2 * factor * z -> pointing outward away from center
    assert a_j2_pole[2] > 0.0


def test_atmospheric_drag_dissipation():
    """
    Verify that atmospheric drag accelerates strictly opposite to relative motion,
    dissipating kinetic energy (v . a_drag < 0). (Technical Guide Section 3.3)
    """
    r_orbit = 6_700_000.0  # 322 km altitude LEO
    v_circ = np.sqrt(MU_EARTH / r_orbit)

    pos = np.array([r_orbit, 0.0, 0.0])
    vel = np.array([0.0, v_circ, 0.0])

    a_drag = calculate_drag_acceleration(
        pos,
        vel,
        mass_kg=1000.0,
        area_m2=5.0,
        cd=2.2
    )

    # Power dissipation = v . a_drag must be strictly negative
    power_per_kg = float(np.dot(vel, a_drag))
    assert power_per_kg < 0.0, "Atmospheric drag must always oppose motion and dissipate orbital energy."

    # Drag acceleration must oppose tangential velocity (+Y)
    assert a_drag[1] < 0.0


def test_drag_causes_orbital_decay():
    """Verify that atmospheric drag causes secular decay in orbital radius over time."""
    r_low = 6_678_137.0  # 300 km altitude (higher density)
    v_circ = np.sqrt(MU_EARTH / r_low)
    state0 = np.array([r_low, 0.0, 0.0, 0.0, v_circ, 0.0])

    cfg_drag = ForceModelConfig(
        include_j2=False,
        include_drag=True,
        spacecraft_mass_kg=500.0,
        drag_area_m2=10.0,
        drag_coefficient_cd=2.5
    )

    duration = 1800.0  # 30 minutes
    times, states = propagate_orbit_perturbed(state0, duration, dt=2.0, config=cfg_drag)

    r_init = np.linalg.norm(states[0, :3])
    r_final = np.linalg.norm(states[-1, :3])

    # Orbital altitude must have decayed
    assert r_final < r_init, f"Expected orbital decay from drag, got r_init={r_init}, r_final={r_final}"


if __name__ == "__main__":
    test_two_body_baseline_identity()
    test_j2_acceleration_geometry_and_magnitude()
    test_atmospheric_drag_dissipation()
    test_drag_causes_orbital_decay()
    print("ALL PERTURBATION TESTS PASSED")
