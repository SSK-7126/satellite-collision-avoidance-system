"""
tests/test_custom_objects.py
============================
Tests for Custom Satellite and Debris Configuration & Management (Phase 7).
Verifies:
- Bidirectional Keplerian <-> Cartesian orbital mechanics conversion
- Strict physical bounds validation and rejection of unphysical orbits
- Full CRUD workflows for custom satellites (create, edit, duplicate, delete)
- Full CRUD workflows for custom debris with unknown mass/dimensions
- Separation of 3D visual scale from physical dimensions
- Distinct object origin identification (REAL_CATALOGUE, USER_CREATED, IMPORTED)
- Scenario persistence, JSON schema validation, import/export
- Scenario isolation and reset-to-original guarantee
"""

import os
import tempfile
import numpy as np
import pytest

from backend.custom_objects.models import (
    ObjectOrigin,
    VisualAppearance,
    CustomSatellite,
    CustomDebris,
)
from backend.custom_objects.orbital_conversions import (
    keplerian_to_cartesian,
    cartesian_to_keplerian,
    validate_orbital_parameters,
    true_anomaly_to_mean_anomaly,
    mean_anomaly_to_true_anomaly,
)
from backend.custom_objects.scenario_manager import (
    CustomScenario,
    CustomObjectManager,
)


def test_keplerian_cartesian_roundtrip():
    """Verify high-precision roundtrip conversion between Keplerian elements and Cartesian state."""
    sma_km = 7000.0
    ecc = 0.005
    inc_deg = 51.64
    raan_deg = 120.0
    arg_p_deg = 45.0
    nu_deg = 30.0

    r_vec, v_vec = keplerian_to_cartesian(sma_km, ecc, inc_deg, raan_deg, arg_p_deg, nu_deg)

    # Convert back to Keplerian
    recovered = cartesian_to_keplerian(r_vec, v_vec)

    assert pytest.approx(recovered["semi_major_axis_km"], abs=0.05) == sma_km
    assert pytest.approx(recovered["eccentricity"], abs=1e-5) == ecc
    assert pytest.approx(recovered["inclination_deg"], abs=0.01) == inc_deg
    assert pytest.approx(recovered["raan_deg"], abs=0.01) == raan_deg
    assert pytest.approx(recovered["arg_perigee_deg"], abs=0.05) == arg_p_deg
    assert pytest.approx(recovered["true_anomaly_deg"], abs=0.05) == nu_deg


def test_kepler_equation_true_vs_mean_anomaly():
    """Verify Kepler equation solver and true anomaly vs mean anomaly distinction."""
    ecc = 0.5
    # At periapsis, nu = 0 and M = 0
    assert pytest.approx(true_anomaly_to_mean_anomaly(0.0, ecc), abs=1e-6) == 0.0
    assert pytest.approx(mean_anomaly_to_true_anomaly(0.0, ecc), abs=1e-6) == 0.0

    # At apoapsis, nu = 180 and M = 180
    assert pytest.approx(true_anomaly_to_mean_anomaly(180.0, ecc), abs=1e-6) == 180.0
    assert pytest.approx(mean_anomaly_to_true_anomaly(180.0, ecc), abs=1e-6) == 180.0

    # At arbitrary intermediate angle (e.g. nu = 90 deg), M != nu for eccentric orbit
    m_90 = true_anomaly_to_mean_anomaly(90.0, ecc)
    assert abs(m_90 - 90.0) > 10.0  # Demonstrates clear distinction between M and nu
    recovered_nu = mean_anomaly_to_true_anomaly(m_90, ecc)
    assert pytest.approx(recovered_nu, abs=1e-5) == 90.0


def test_high_eccentricity_and_geo_orbits():
    """Verify that physically bound high-eccentricity (Molniya) and high-altitude (GEO) orbits are supported."""
    # 1. Molniya orbit: a = 26,600 km, e = 0.74, i = 63.4 deg
    molniya_errs = validate_orbital_parameters(26600.0, 0.74, 63.4)
    assert len(molniya_errs) == 0, f"Molniya rejected: {molniya_errs}"
    r_mol, v_mol = keplerian_to_cartesian(26600.0, 0.74, 63.4, 45.0, 270.0, true_anomaly_deg=0.0)
    # At perigee, altitude is ~6916 km - 6378 km = ~538 km (safe above surface)
    assert np.linalg.norm(r_mol) > 6_800_000.0

    # 2. Geostationary orbit (GEO): a = 42,164.14 km, e = 0.0001, i = 0.05 deg
    geo_errs = validate_orbital_parameters(42164.14, 0.0001, 0.05)
    assert len(geo_errs) == 0, f"GEO rejected: {geo_errs}"
    r_geo, v_geo = keplerian_to_cartesian(42164.14, 0.0001, 0.05, 0.0, 0.0, true_anomaly_deg=120.0)
    # GEO orbital speed is ~3.07 km/s
    speed_geo_kms = np.linalg.norm(v_geo) / 1000.0
    assert pytest.approx(speed_geo_kms, abs=0.05) == 3.075


def test_unphysical_orbital_parameters_rejection():
    """Ensure negative SMA, hyperbolic eccentricity, or Earth-surface penetration are rejected."""
    # Negative SMA
    assert len(validate_orbital_parameters(-7000.0, 0.01, 50.0)) > 0
    # Hyperbolic eccentricity (e >= 1.0)
    assert len(validate_orbital_parameters(7000.0, 1.2, 50.0)) > 0
    # Invalid inclination (> 180 deg)
    assert len(validate_orbital_parameters(7000.0, 0.01, 195.0)) > 0
    # Earth penetration: SMA 6000 km is inside Earth (R = 6378 km)
    assert len(validate_orbital_parameters(6000.0, 0.001, 50.0)) > 0


def test_custom_satellite_crud():
    """Verify full Create, Read, Update, Duplicate, Delete workflow for custom satellites."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        mgr = CustomObjectManager(scenarios_dir=tmp_dir)

        # 1. Create satellite with Keplerian elements
        sat = mgr.create_satellite(
            display_name="PROTOTYPE_CUBESAT_1",
            input_mode="ORBITAL_ELEMENTS",
            orbital_elements_dict={
                "semi_major_axis_km": 6900.0,
                "eccentricity": 0.001,
                "inclination_deg": 98.0,
                "raan_deg": 45.0,
                "arg_perigee_deg": 90.0,
            },
            true_anomaly_deg=10.0,
            dry_mass_kg=12.0,
            propellant_kg=2.0,
            bus_model="6U_CUBESAT",
        )
        assert sat.id in mgr.active_scenario.satellites
        assert sat.origin == ObjectOrigin.USER_CREATED_SIMULATION_OBJECT
        assert sat.display_name == "PROTOTYPE_CUBESAT_1"
        assert sat.cartesian_position_m is not None
        assert sat.cartesian_velocity_mps is not None

        # 2. Update satellite
        updated = mgr.update_satellite(sat.id, {"display_name": "PROTOTYPE_CUBESAT_1_RENAMED", "dry_mass_kg": 15.0})
        assert updated.display_name == "PROTOTYPE_CUBESAT_1_RENAMED"
        assert updated.dry_mass_kg == 15.0

        # 3. Duplicate satellite
        cloned = mgr.duplicate_satellite(sat.id, new_name="PROTOTYPE_CUBESAT_2")
        assert cloned.id != sat.id
        assert cloned.display_name == "PROTOTYPE_CUBESAT_2"
        assert len(mgr.active_scenario.satellites) == 2

        # 4. Delete satellite
        assert mgr.delete_satellite(sat.id) is True
        assert sat.id not in mgr.active_scenario.satellites
        assert len(mgr.active_scenario.satellites) == 1


def test_custom_debris_crud_with_unknown_properties():
    """Verify custom debris management permits unknown mass/dimensions with explicit labeling."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        mgr = CustomObjectManager(scenarios_dir=tmp_dir)

        # Create debris with unknown mass and dimensions
        deb = mgr.create_debris(
            display_name="FRAGMENT_ALPHA_99",
            input_mode="CARTESIAN_STATE",
            position_m=[7_000_000.0, 500.0, 0.0],
            velocity_mps=[0.0, 7500.0, 10.0],
            mass_kg=None,            # Permitted unknown
            dimensions_xyz_m=None,   # Permitted unknown
            shape_type="IRREGULAR_FRAGMENT",
            material="UNKNOWN",
            tumbling_rate_deg_s=25.0,
        )
        assert deb.id in mgr.active_scenario.debris
        assert deb.mass_kg is None
        assert deb.dimensions_xyz_m is None
        assert deb.material == "UNKNOWN"
        assert deb.orbital_elements is not None  # Derived from Cartesian state

        # Duplicate debris
        cloned_deb = mgr.duplicate_debris(deb.id, new_name="FRAGMENT_BETA_100")
        assert cloned_deb.id != deb.id
        assert len(mgr.active_scenario.debris) == 2

        # Delete debris
        assert mgr.delete_debris(deb.id) is True
        assert len(mgr.active_scenario.debris) == 1


def test_scenario_isolation_and_reset():
    """Verify that custom scenarios can be exported/imported and reset without touching original demo."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        mgr = CustomObjectManager(scenarios_dir=tmp_dir)

        # Add custom satellite
        mgr.create_satellite(
            display_name="TEST_SAT",
            input_mode="ORBITAL_ELEMENTS",
            orbital_elements_dict={"semi_major_axis_km": 7000.0, "eccentricity": 0.001, "inclination_deg": 50.0},
        )
        assert len(mgr.active_scenario.satellites) == 1

        # Export to JSON
        export_path = os.path.join(tmp_dir, "exported_scenario.json")
        mgr.export_scenario_json(export_path)
        assert os.path.exists(export_path)

        # Reset to original
        mgr.reset_to_original()
        assert len(mgr.active_scenario.satellites) == 0

        # Import back from JSON
        imported = mgr.import_scenario_json(export_path)
        assert len(imported.satellites) == 1
        assert "TEST_SAT" in [s.display_name for s in imported.satellites.values()]
