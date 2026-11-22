"""
D2/tests/test_propulsion.py
===========================
Verification test suite for D2 propulsion subsystem, finite-duration thrust,
Tsiolkovsky mass depletion, and manoeuvre execution uncertainty.
Follows Section 7 and Section 12.1 of the Technical Development Guide.
"""

import numpy as np
import pytest

from D2.dynamics.two_body import MU_EARTH
from D2.manoeuvres.propulsion import (
    PropulsionParameters,
    calculate_propellant_mass_ideal,
    calculate_delta_v_from_propellant,
    propagate_finite_burn,
    apply_execution_uncertainty,
    G0_STANDARD,
)


def test_propulsion_parameters_validation():
    """Verify initialization constraints of PropulsionParameters."""
    prop = PropulsionParameters(
        wet_mass_kg=1200.0,
        propellant_mass_kg=60.0,
        thrust_n=20.0,
        isp_s=310.0
    )
    assert prop.dry_mass_kg == 1140.0
    expected_m_dot = 20.0 / (310.0 * G0_STANDARD)
    assert np.isclose(prop.mass_flow_rate_kg_per_s, expected_m_dot)
    assert np.isclose(prop.effective_exhaust_velocity_mps, 310.0 * G0_STANDARD)

    with pytest.raises(ValueError):
        PropulsionParameters(wet_mass_kg=-100.0)

    with pytest.raises(ValueError):
        PropulsionParameters(wet_mass_kg=500.0, propellant_mass_kg=600.0)


def test_tsiolkovsky_hand_checkable_cases():
    """
    Verify Tsiolkovsky rocket equation against exact hand-checkable analytical calculations.
    (Technical Guide Section 7.2 & 12.1)
    """
    m0 = 1000.0   # kg
    isp = 300.0   # s
    g0 = 9.80665  # m/s^2
    c = isp * g0  # 2941.995 m/s

    # Case 1: Delta_v = 3.00 m/s (matching reference avoidance burn)
    dv = 3.00
    expected_mass = m0 * (1.0 - np.exp(-dv / c))  # ~ 1.01897 kg
    actual_mass = calculate_propellant_mass_ideal(dv, m0, isp, g0)
    assert np.isclose(actual_mass, expected_mass, rtol=1e-8)
    assert np.isclose(actual_mass, 1.01897, atol=1e-3)

    # Invert back to Delta-v
    recovered_dv = calculate_delta_v_from_propellant(actual_mass, m0, isp, g0)
    assert np.isclose(recovered_dv, dv, rtol=1e-8)


def test_finite_burn_propagation():
    """
    Verify finite-duration thrust propagation with dynamic mass depletion.
    (Technical Guide Section 7.1)
    """
    r0 = 7000000.0
    v0 = np.sqrt(MU_EARTH / r0)
    state0 = np.array([r0, 0.0, 0.0, 0.0, v0, 0.0], dtype=np.float64)

    # In-plane tangential burn (+Y in ECI)
    u_thrust = np.array([0.0, 1.0, 0.0], dtype=np.float64)
    prop = PropulsionParameters(
        wet_mass_kg=1000.0,
        propellant_mass_kg=50.0,
        thrust_n=20.0,
        isp_s=300.0
    )

    burn_duration = 50.0  # 50 seconds active burn
    res = propagate_finite_burn(
        initial_state_eci=state0,
        thrust_direction_eci=u_thrust,
        burn_duration_s=burn_duration,
        propulsion=prop,
        dt=0.5
    )

    expected_propellant = prop.mass_flow_rate_kg_per_s * burn_duration
    assert np.isclose(res["propellant_consumed_kg"], expected_propellant, rtol=1e-6)
    assert np.isclose(res["final_mass_kg"], prop.wet_mass_kg - expected_propellant, rtol=1e-6)

    # Spacecraft speed should have increased from prograde thrust
    final_speed = np.linalg.norm(res["final_state_eci"][3:6])
    assert final_speed > v0
    assert res["delta_v_effective_mps"] > 0.0


def test_propellant_exhaustion_rejection():
    """Verify that attempting a burn exceeding available propellant raises ValueError."""
    state0 = np.array([7000000.0, 0.0, 0.0, 0.0, 7500.0, 0.0])
    u_thrust = np.array([0.0, 1.0, 0.0])
    prop_low = PropulsionParameters(
        wet_mass_kg=1000.0,
        propellant_mass_kg=1.0,  # Only 1 kg available
        thrust_n=20.0,
        isp_s=300.0
    )

    with pytest.raises(ValueError, match="Insufficient propellant"):
        # 1000 s burn requires ~6.8 kg, only 1.0 kg available
        propagate_finite_burn(state0, u_thrust, burn_duration_s=1000.0, propulsion=prop_low)


def test_manoeuvre_execution_uncertainty():
    """
    Verify manoeuvre execution uncertainty dispersions and seed reproducibility.
    (Technical Guide Section 7.3)
    """
    dv_nom = np.array([0.0, 3.0, 0.0], dtype=np.float64)

    # 1. Deterministic repeatability with fixed seed
    res1 = apply_execution_uncertainty(dv_nom, sigma_magnitude_rel=0.02, sigma_pointing_deg=0.5, seed=42)
    res2 = apply_execution_uncertainty(dv_nom, sigma_magnitude_rel=0.02, sigma_pointing_deg=0.5, seed=42)

    assert np.allclose(res1["delta_v_actual_eci"], res2["delta_v_actual_eci"])
    assert res1["magnitude_actual_mps"] == res2["magnitude_actual_mps"]

    # 2. Statistical dispersion bounds over ensemble
    ensemble_mags = []
    for s in range(100):
        r = apply_execution_uncertainty(dv_nom, sigma_magnitude_rel=0.01, sigma_pointing_deg=0.5, seed=s)
        ensemble_mags.append(r["magnitude_actual_mps"])

    mean_mag = float(np.mean(ensemble_mags))
    std_mag = float(np.std(ensemble_mags))
    assert np.isclose(mean_mag, 3.0, atol=0.05)
    assert 0.015 <= std_mag <= 0.045  # Expected std ~ 0.03 m/s (1% of 3.0 m/s)


if __name__ == "__main__":
    test_propulsion_parameters_validation()
    test_tsiolkovsky_hand_checkable_cases()
    test_finite_burn_propagation()
    test_propellant_exhaustion_rejection()
    test_manoeuvre_execution_uncertainty()
    print("ALL PROPULSION TESTS PASSED")
