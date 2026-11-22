"""
tests/test_sensors.py
=====================
Verification test suite for synthetic sensor simulation subsystem.
Follows Section 8 and Section 12 of the Technical Development Guide:
- Ground truth vs observed state separation
- Optical angular line-of-sight geometry and noise statistics
- Radar range and Doppler range-rate measurement consistency
- Ground station visibility pass and elevation mask
- Deterministic outage injection and dropout handling
"""

import numpy as np
import pytest

from Sensors.sensor_models import (
    GroundTruthState,
    OpticalSensor,
    RadarSensor,
    GroundStation,
    OnboardNavigationSimulator,
    OutageWindow,
)


def test_truth_vs_observation_separation():
    """Verify that truth states and observed state estimates are structurally distinct."""
    truth = GroundTruthState(
        object_id="SAT_A",
        time_s=100.0,
        position_m=np.array([7000000.0, 0.0, 0.0]),
        velocity_mps=np.array([0.0, 7546.0, 0.0])
    )

    nav = OnboardNavigationSimulator(pos_sigma_m=15.0, vel_sigma_mps=0.03, seed=42)
    obs = nav.estimate(truth)

    assert obs is not None
    assert obs.target_id == "SAT_A"
    assert obs.time_s == 100.0
    # Observed position must differ from truth due to simulated noise
    diff_pos = np.linalg.norm(obs.position_m - truth.position_m)
    assert diff_pos > 0.0
    assert diff_pos < 100.0  # Within ~3 sigma
    # Covariance must be 6x6 positive definite
    assert obs.covariance_6x6.shape == (6, 6)
    assert np.all(np.linalg.eigvalsh(obs.covariance_6x6) > 0.0)


def test_optical_sensor_geometry_and_noise():
    """Verify optical line-of-sight angles match geometric Right Ascension / Declination."""
    sensor = OpticalSensor(
        sensor_id="OPT_01",
        position_eci=np.array([0.0, 0.0, 0.0]),
        sigma_angle_rad=1e-5,
        seed=123
    )

    # Place target along +X, +Y at Z=0 -> RA = 45 deg, Dec = 0 deg
    r_target = np.array([5000000.0, 5000000.0, 0.0])
    truth = GroundTruthState(
        object_id="DEBRIS_01",
        time_s=50.0,
        position_m=r_target,
        velocity_mps=np.array([0.0, 0.0, 7500.0])
    )

    obs = sensor.measure(truth)
    assert obs is not None
    assert obs.sensor_type == "OPTICAL"
    ra = obs.measurements["right_ascension_rad"]
    dec = obs.measurements["declination_rad"]

    expected_ra = np.radians(45.0)
    assert np.isclose(ra, expected_ra, atol=1e-3)
    assert np.isclose(dec, 0.0, atol=1e-3)


def test_radar_sensor_range_and_doppler():
    """Verify radar range and range-rate measurements against exact relative velocity."""
    sensor = RadarSensor(
        sensor_id="RAD_01",
        position_eci=np.array([6378137.0, 0.0, 0.0]),  # At equator
        sigma_range_m=5.0,
        sigma_range_rate_mps=0.2,
        seed=999
    )

    # Target directly overhead (+X), moving along +Y
    r_target = np.array([7000000.0, 0.0, 0.0])
    v_target = np.array([0.0, 7500.0, 0.0])
    truth = GroundTruthState("DEBRIS_02", 0.0, r_target, v_target)

    obs = sensor.measure(truth)
    assert obs is not None
    assert obs.sensor_type == "RADAR"

    # Overhead geometry: r_rel = [621863, 0, 0], v_rel = [0, 7500, 0]
    # Dot product r_rel . v_rel = 0 -> range-rate should be close to 0
    expected_range = 7000000.0 - 6378137.0  # 621,863 m
    assert np.isclose(obs.measurements["slant_range_m"], expected_range, atol=25.0)
    assert np.isclose(obs.measurements["range_rate_mps"], 0.0, atol=1.0)


def test_ground_station_visibility_mask():
    """Verify topocentric elevation calculation and visibility mask (> 10 deg)."""
    # Station at equator, prime meridian
    station = GroundStation(station_id="KOUROU", lat_deg=5.2, lon_deg=-52.8, alt_m=0.0, min_elevation_deg=10.0)

    # Target directly above station at t=0
    r_sta_0, _ = station.get_eci_state(0.0)
    target_overhead = r_sta_0 * 1.1  # Directly overhead
    assert station.is_visible(target_overhead, time_s=0.0)

    # Target on opposite side of Earth
    target_opposite = -r_sta_0 * 1.1
    assert not station.is_visible(target_opposite, time_s=0.0)


def test_sensor_outage_injection():
    """Verify deterministic dropout window handling."""
    nav = OnboardNavigationSimulator(pos_sigma_m=10.0, vel_sigma_mps=0.01, seed=1)
    truth = GroundTruthState("SAT", 150.0, np.array([7e6, 0, 0]), np.array([0, 7500, 0]))

    outage = OutageWindow(start_time_s=100.0, end_time_s=200.0, outage_type="COMPLETE_DROPOUT")

    # Inside outage window: should return None
    obs_outage = nav.estimate(truth, outage_windows=[outage])
    assert obs_outage is None

    # Outside outage window: should return valid observation
    truth_outside = GroundTruthState("SAT", 250.0, np.array([7e6, 0, 0]), np.array([0, 7500, 0]))
    obs_valid = nav.estimate(truth_outside, outage_windows=[outage])
    assert obs_valid is not None
    assert obs_valid.time_s == 250.0


if __name__ == "__main__":
    test_truth_vs_observation_separation()
    test_optical_sensor_geometry_and_noise()
    test_radar_sensor_range_and_doppler()
    test_ground_station_visibility_mask()
    test_sensor_outage_injection()
    print("ALL SENSOR TESTS PASSED")
