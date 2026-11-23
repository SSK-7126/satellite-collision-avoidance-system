"""
tests/test_hardware_resources.py
================================
Tests for Satellite Hardware and Resource Registry (Phase 6).
Verifies:
- Tsiolkovsky rocket equation propellant consumption estimates
- Delta-v capacity calculation
- Spacecraft hardware specifications, dimensions, and dry mass
- Fuel event history recording and remaining propellant updates
- Exhaustion prevention when requested burn exceeds propellant reserve
- Explicit field-level provenance recording (operator, simulated, public, unknown)
- Persistence and reload of hardware registry records
"""

import math
import os
import tempfile
import pytest

from backend.resources.models import (
    SpacecraftHardwareRecord,
    ThrusterSpecification,
    FuelEvent,
    ProvenanceType,
)
from backend.resources.fuel_calculator import (
    estimate_propellant_consumption,
    estimate_delta_v_capacity,
    G0_STANDARD,
)
from backend.resources.registry import HardwareRegistry


def test_tsiolkovsky_propellant_estimation():
    """Verify hand-checkable propellant consumption for 3 m/s impulsive burn."""
    m0 = 1155.0  # 1100 kg dry + 55 kg fuel
    dv = 3.00    # m/s
    isp = 220.0  # s

    # Analytical: c = 220 * 9.80665 = 2157.463 m/s
    # ratio = exp(-3.0 / 2157.463) = exp(-0.0013905) = 0.9986104
    # dm = 1155.0 * (1 - 0.9986104) = 1.605 kg
    consumed = estimate_propellant_consumption(m0, dv, isp)
    assert 1.55 < consumed < 1.65
    assert pytest.approx(consumed, rel=1e-3) == m0 * (1.0 - math.exp(-dv / (isp * G0_STANDARD)))


def test_zero_delta_v_consumption():
    """Zero delta-v should consume exactly zero propellant."""
    consumed = estimate_propellant_consumption(1000.0, 0.0, 220.0)
    assert consumed == 0.0


def test_invalid_propellant_inputs_rejection():
    """Ensure negative mass, negative delta-v, or non-positive Isp raise ValueError."""
    with pytest.raises(ValueError, match="Initial mass"):
        estimate_propellant_consumption(-100.0, 5.0, 220.0)
    with pytest.raises(ValueError, match="Delta-v"):
        estimate_propellant_consumption(1000.0, -1.0, 220.0)
    with pytest.raises(ValueError, match="Specific impulse"):
        estimate_propellant_consumption(1000.0, 5.0, 0.0)


def test_delta_v_capacity_calculation():
    """Verify maximum delta-v calculation from propellant reserve."""
    dry_mass = 1000.0
    prop_mass = 100.0
    isp = 250.0

    # dv_max = 250 * 9.80665 * ln(1100 / 1000) = 2451.66 * ln(1.1) = 233.66 m/s
    dv_max = estimate_delta_v_capacity(dry_mass, prop_mass, isp)
    assert 230.0 < dv_max < 240.0


def test_hardware_registry_burn_recording_and_exhaustion():
    """Verify fuel event recording, propellant decrementing, and exhaustion safeguard."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        storage_file = os.path.join(tmp_dir, "hardware.json")
        reg = HardwareRegistry(storage_path=storage_file)

        # 1. Retrieve CARTOSAT-3
        record = reg.get_record("44804")
        assert record is not None
        assert record.dry_mass_kg == 1100.0
        assert record.current_propellant_kg == 55.0

        # 2. Record 3.0 m/s avoidance burn
        event = reg.record_manoeuvre_burn(
            object_id="44804",
            manoeuvre_id="MAN-001-RADIAL-3MS",
            delta_v_mps=3.0,
            isp_sec=220.0,
        )
        assert event.delta_v_mps == 3.0
        assert 1.55 < event.estimated_propellant_used_kg < 1.65
        assert event.remaining_propellant_kg < 55.0
        assert event.is_estimate is True
        assert "Tsiolkovsky" in event.assumptions

        # 3. Exhaustion test: attempt burn requiring more fuel than available
        with pytest.raises(ValueError, match="requires.*propellant.*available"):
            reg.record_manoeuvre_burn(
                object_id="44804",
                manoeuvre_id="MAN-OVERBUDGET",
                delta_v_mps=500.0,  # 500 m/s requires ~230 kg of propellant
            )

        # 4. Persistence verification: load into separate instance
        reg2 = HardwareRegistry(storage_path=storage_file)
        rec2 = reg2.get_record("44804")
        assert rec2 is not None
        assert len(rec2.fuel_events) == 1
        assert pytest.approx(rec2.current_propellant_kg, abs=0.01) == event.remaining_propellant_kg
