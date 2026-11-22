"""
tests/test_scenarios.py
=======================
Verification test suite for Scenarios S0 through S8.
Follows Section 11 and Section 12 of the Technical Development Guide:
- S0: Circular orbit speed, period, and energy conservation
- S1: Elliptical orbit vis-viva, apogee/perigee return
- S2: Close approach TCA and miss distance
- S3: Uncertain conjunction covariance propagation and Foster Pc
- S4: Avoidance burn, Delta-v, and clearance satisfaction
- S5: Multiple debris population screening and multi-target clearance
- S6: Perturbed LEO (J2 nodal regression and drag secular decay)
- S7: Sensor tracking outage and uncertainty dilation
- S8: Safe pass disambiguation (proximity != collision risk)
"""

import pytest

from Scenarios.s0_circular_orbit import run_scenario_s0
from Scenarios.s1_elliptical_orbit import run_scenario_s1
from Scenarios.s2_close_approach import run_scenario_s2
from Scenarios.s3_uncertain_conjunction import run_scenario_s3
from Scenarios.s4_avoidance_burn import run_scenario_s4
from Scenarios.s5_multiple_debris import run_scenario_s5
from Scenarios.s6_perturbed_leo import run_scenario_s6
from Scenarios.s7_sensor_outage import run_scenario_s7
from Scenarios.s8_safe_pass import run_scenario_s8


def test_s0_circular_orbit():
    res = run_scenario_s0()
    assert res["status"] == "PASSED"
    assert res["relative_energy_error"] < 1e-6


def test_s1_elliptical_orbit():
    res = run_scenario_s1()
    assert res["status"] == "PASSED"
    assert res["perigee_error_m"] < 20.0
    assert res["apogee_error_m"] < 20.0


def test_s2_close_approach():
    res = run_scenario_s2()
    assert res["status"] == "PASSED"
    assert res["is_conjunction_candidate"] is True


def test_s3_uncertain_conjunction():
    res = run_scenario_s3()
    assert res["status"] == "PASSED"
    assert res["asymptotic_tail_underflow_preserved"] is True


def test_s4_avoidance_burn():
    res = run_scenario_s4()
    assert res["status"] == "PASSED"
    assert res["operational_threshold_satisfied"] is True
    assert res["delta_v_direction_rtn"] == "-R"
    assert abs(res["delta_v_magnitude_mps"] - 3.0) < 1e-3


def test_s5_multiple_debris():
    res = run_scenario_s5()
    assert res["status"] == "PASSED"
    assert res["all_debris_cleared_safely"] is True
    assert res["total_objects_screened"] == 10


def test_s6_perturbed_leo():
    res = run_scenario_s6(num_orbits=2.0)
    assert res["status"] == "PASSED"
    assert res["j2_trajectory_divergence_m"] > 500.0
    assert res["semi_major_axis_decay_from_drag_m"] < 0.0


def test_s7_sensor_outage():
    res = run_scenario_s7()
    assert res["status"] == "PASSED"
    assert res["variance_dilation_factor"] > 1.0


def test_s8_safe_pass():
    res = run_scenario_s8()
    assert res["status"] == "PASSED"
    assert res["delta_v_expended_mps"] == 0.0
    assert res["planning_status"] == "NO_MANOEUVRE_REQUIRED"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
