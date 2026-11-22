"""
Sensors/sensor_models.py
========================
Synthetic Space Surveillance & Onboard Sensor Simulation Subsystem.
Strictly following Section 8 of the Satellite Anti-Collision Technical Guide.

Core Principles:
1. Strict Truth vs Observation Separation:
   - Ground truth trajectories remain pristine.
   - Downstream consumers (screening, estimation, ML features) consume ONLY
     timestamped noisy observations and estimated state structures.
2. Simulated Tracking Modalities:
   - Optical Tracking: Line-of-sight Right Ascension (RA) and Declination (Dec)
     with angular noise and optional centroiding bias.
   - Radar Tracking: Range and Range-rate measurements with measurement noise,
     range bias, and maximum detection range limits.
   - Ground Station Tracking Pass: Earth-rotation-dependent topocentric elevation
     mask (> 10 deg) defining periodic visibility windows.
   - Onboard Navigation / GNSS: Spacecraft state estimate with position/velocity
     noise, measurement drift, and estimated 6x6 state covariance.
3. Outage & Degradation Injection:
   - Configurable dropout windows, communication blackouts, or sensor noise inflation.
   - Fully deterministic and reproducible using fixed random seeds.

Conventions & Units:
- Reference Frame : Earth-Centred Inertial (ECI J2000) / Topocentric
- Angles          : Radians (rad) or Degrees (deg)
- Ranges          : Metres (m), Velocities: Metres per second (m/s)
- Time            : Seconds from epoch (s)
- Precision       : Float64
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Tuple
import numpy as np

# WGS84 Constants
WGS84_A = 6378137.0            # Semi-major axis in metres
WGS84_F = 1.0 / 298.257223563   # Flattening
EARTH_ROTATION_RATE_RAD_S = 7.292115e-5  # Earth angular speed (rad/s)


@dataclass
class GroundTruthState:
    """True physical orbital state (never directly exposed to realistic ML inference)."""
    object_id: str
    time_s: float
    position_m: np.ndarray       # Shape (3,)
    velocity_mps: np.ndarray     # Shape (3,)
    epoch_utc: str = "2026-01-01T00:00:00Z"
    frame: str = "ECI_J2000"


@dataclass
class SensorObservation:
    """
    Standardized noisy measurement record. (Technical Guide Section 8)
    """
    observation_id: str
    sensor_id: str
    sensor_type: str            # 'OPTICAL', 'RADAR', 'ONBOARD_GNSS'
    target_id: str
    time_s: float
    epoch_utc: str
    frame: str
    measurements: Dict[str, float]
    noise_sigma: Dict[str, float]
    quality_flags: List[str]
    is_valid: bool = True
    outage_flag: bool = False


@dataclass
class ObservedStateEstimate:
    """
    Estimated orbital state derived strictly from observations.
    (Technical Guide Section 8 & 10)
    """
    target_id: str
    time_s: float
    position_m: np.ndarray       # Shape (3,)
    velocity_mps: np.ndarray     # Shape (3,)
    covariance_6x6: np.ndarray   # Shape (6, 6)
    epoch_utc: str = "2026-01-01T00:00:00Z"
    frame: str = "ECI_J2000"
    quality_flags: List[str] = field(default_factory=list)
    source: str = "simulated_sensor_pipeline"


@dataclass
class OutageWindow:
    """Time window defining simulated observation outage or data corruption."""
    start_time_s: float
    end_time_s: float
    outage_type: str = "COMPLETE_DROPOUT"   # 'COMPLETE_DROPOUT' or 'NOISE_INFLATION'
    noise_multiplier: float = 10.0


# =============================================================================
# SENSOR MODELS
# =============================================================================

class OpticalSensor:
    """
    Simulates optical angular line-of-sight tracking (Right Ascension & Declination).
    """
    def __init__(
        self,
        sensor_id: str = "OPTICAL_TELESCOPE_01",
        position_eci: Optional[np.ndarray] = None,
        sigma_angle_rad: float = 5.0e-6,   # ~1.0 arcsecond noise
        bias_angle_rad: float = 0.0,
        max_range_m: float = 50_000_000.0,
        seed: Optional[int] = None
    ):
        self.sensor_id = sensor_id
        self.position_eci = np.zeros(3) if position_eci is None else np.asarray(position_eci, dtype=np.float64)
        self.sigma_angle_rad = sigma_angle_rad
        self.bias_angle_rad = bias_angle_rad
        self.max_range_m = max_range_m
        self.rng = np.random.default_rng(seed)

    def measure(
        self,
        target_truth: GroundTruthState,
        sensor_pos_eci: Optional[np.ndarray] = None
    ) -> Optional[SensorObservation]:
        pos_obs = self.position_eci if sensor_pos_eci is None else sensor_pos_eci
        r_los = target_truth.position_m - pos_obs
        dist = np.linalg.norm(r_los)

        if dist > self.max_range_m or dist <= 0.0:
            return None

        # True angles: Right Ascension (alpha), Declination (delta)
        alpha_true = float(np.arctan2(r_los[1], r_los[0]))
        delta_true = float(np.arcsin(np.clip(r_los[2] / dist, -1.0, 1.0)))

        # Add Gaussian noise and bias
        noise_alpha = self.rng.normal(0.0, self.sigma_angle_rad)
        noise_delta = self.rng.normal(0.0, self.sigma_angle_rad)

        alpha_meas = float(alpha_true + self.bias_angle_rad + noise_alpha)
        delta_meas = float(delta_true + self.bias_angle_rad + noise_delta)

        return SensorObservation(
            observation_id=f"OBS_OPT_{self.sensor_id}_{target_truth.time_s:.1f}",
            sensor_id=self.sensor_id,
            sensor_type="OPTICAL",
            target_id=target_truth.object_id,
            time_s=target_truth.time_s,
            epoch_utc=target_truth.epoch_utc,
            frame="ECI_J2000",
            measurements={
                "right_ascension_rad": alpha_meas,
                "declination_rad": delta_meas,
                "apparent_range_m": float(dist),
            },
            noise_sigma={
                "sigma_angle_rad": self.sigma_angle_rad,
            },
            quality_flags=["OPTICAL_LOS", "GAUSSIAN_NOISE"],
            is_valid=True
        )


class RadarSensor:
    """
    Simulates radar-like tracking: Range and Range-Rate (Doppler) measurements.
    (Technical Guide Section 8)
    """
    def __init__(
        self,
        sensor_id: str = "GROUND_RADAR_01",
        position_eci: Optional[np.ndarray] = None,
        sigma_range_m: float = 10.0,       # 10 m range noise
        sigma_range_rate_mps: float = 0.5, # 0.5 m/s Doppler noise
        range_bias_m: float = 0.0,
        max_range_m: float = 3_000_000.0,  # 3000 km radar detection horizon
        seed: Optional[int] = None
    ):
        self.sensor_id = sensor_id
        self.position_eci = np.zeros(3) if position_eci is None else np.asarray(position_eci, dtype=np.float64)
        self.sigma_range_m = sigma_range_m
        self.sigma_range_rate_mps = sigma_range_rate_mps
        self.range_bias_m = range_bias_m
        self.max_range_m = max_range_m
        self.rng = np.random.default_rng(seed)

    def measure(
        self,
        target_truth: GroundTruthState,
        sensor_pos_eci: Optional[np.ndarray] = None,
        sensor_vel_eci: Optional[np.ndarray] = None
    ) -> Optional[SensorObservation]:
        r_sen = self.position_eci if sensor_pos_eci is None else sensor_pos_eci
        v_sen = np.zeros(3) if sensor_vel_eci is None else sensor_vel_eci

        r_rel = target_truth.position_m - r_sen
        v_rel = target_truth.velocity_mps - v_sen
        range_true = float(np.linalg.norm(r_rel))

        if range_true > self.max_range_m or range_true <= 0.0:
            return None

        # Range-rate: d(range)/dt = (r_rel . v_rel) / range
        range_rate_true = float(np.dot(r_rel, v_rel) / range_true)

        # Apply noise and bias
        noise_r = self.rng.normal(0.0, self.sigma_range_m)
        noise_rr = self.rng.normal(0.0, self.sigma_range_rate_mps)

        range_meas = float(range_true + self.range_bias_m + noise_r)
        range_rate_meas = float(range_rate_true + noise_rr)

        return SensorObservation(
            observation_id=f"OBS_RAD_{self.sensor_id}_{target_truth.time_s:.1f}",
            sensor_id=self.sensor_id,
            sensor_type="RADAR",
            target_id=target_truth.object_id,
            time_s=target_truth.time_s,
            epoch_utc=target_truth.epoch_utc,
            frame="ECI_J2000",
            measurements={
                "slant_range_m": max(0.0, range_meas),
                "range_rate_mps": range_rate_meas,
            },
            noise_sigma={
                "sigma_range_m": self.sigma_range_m,
                "sigma_range_rate_mps": self.sigma_range_rate_mps,
            },
            quality_flags=["RADAR_RANGE_DOPPLER", "GAUSSIAN_NOISE"],
            is_valid=True
        )


class GroundStation:
    """
    Ground tracking station with geodetic coordinates, topocentric elevation mask,
    and Earth-rotation coordinate mapping. (Technical Guide Section 8)
    """
    def __init__(
        self,
        station_id: str,
        lat_deg: float,
        lon_deg: float,
        alt_m: float = 0.0,
        min_elevation_deg: float = 10.0
    ):
        self.station_id = station_id
        self.lat_rad = np.radians(lat_deg)
        self.lon_rad = np.radians(lon_deg)
        self.alt_m = alt_m
        self.min_elevation_rad = np.radians(min_elevation_deg)

        # Geodetic to ECEF
        sin_phi = np.sin(self.lat_rad)
        cos_phi = np.cos(self.lat_rad)
        sin_lam = np.sin(self.lon_rad)
        cos_lam = np.cos(self.lon_rad)
        e2 = 2.0 * WGS84_F - WGS84_F**2
        n_rad = WGS84_A / np.sqrt(1.0 - e2 * sin_phi**2)

        self.r_ecef = np.array([
            (n_rad + alt_m) * cos_phi * cos_lam,
            (n_rad + alt_m) * cos_phi * sin_lam,
            (n_rad * (1.0 - e2) + alt_m) * sin_phi
        ], dtype=np.float64)

    def get_eci_state(self, time_s: float) -> Tuple[np.ndarray, np.ndarray]:
        """Convert station ECEF position to ECI at given elapsed seconds."""
        theta = EARTH_ROTATION_RATE_RAD_S * time_s
        c_th, s_th = np.cos(theta), np.sin(theta)
        r_eci = np.array([
            c_th * self.r_ecef[0] - s_th * self.r_ecef[1],
            s_th * self.r_ecef[0] + c_th * self.r_ecef[1],
            self.r_ecef[2]
        ])
        v_eci = np.array([
            -EARTH_ROTATION_RATE_RAD_S * r_eci[1],
            EARTH_ROTATION_RATE_RAD_S * r_eci[0],
            0.0
        ])
        return r_eci, v_eci

    def is_visible(self, target_pos_eci: np.ndarray, time_s: float) -> bool:
        """Evaluate if target is above the station's minimum elevation mask."""
        r_sta_eci, _ = self.get_eci_state(time_s)
        rho_vec = target_pos_eci - r_sta_eci
        rho_norm = np.linalg.norm(rho_vec)
        if rho_norm <= 0.0:
            return False

        # Zenith unit vector in ECI
        r_norm = np.linalg.norm(r_sta_eci)
        zenith = r_sta_eci / r_norm

        # Elevation angle = 90 deg - angle(zenith, rho)
        cos_zenith = np.dot(zenith, rho_vec / rho_norm)
        elevation = np.arcsin(np.clip(cos_zenith, -1.0, 1.0))
        return bool(elevation >= self.min_elevation_rad)


class OnboardNavigationSimulator:
    """
    Simulates onboard GNSS / orbit determination estimation with realistic noise,
    measurement bias, and estimated covariance.
    """
    def __init__(
        self,
        pos_sigma_m: float = 20.0,
        vel_sigma_mps: float = 0.02,
        seed: Optional[int] = None
    ):
        self.pos_sigma_m = pos_sigma_m
        self.vel_sigma_mps = vel_sigma_mps
        self.rng = np.random.default_rng(seed)

    def estimate(
        self,
        truth: GroundTruthState,
        outage_windows: Optional[List[OutageWindow]] = None
    ) -> Optional[ObservedStateEstimate]:
        t = truth.time_s

        # Check for outage
        is_outage = False
        noise_mult = 1.0
        if outage_windows:
            for w in outage_windows:
                if w.start_time_s <= t <= w.end_time_s:
                    if w.outage_type == "COMPLETE_DROPOUT":
                        return None
                    elif w.outage_type == "NOISE_INFLATION":
                        is_outage = True
                        noise_mult = w.noise_multiplier

        sig_r = self.pos_sigma_m * noise_mult
        sig_v = self.vel_sigma_mps * noise_mult

        noise_pos = self.rng.normal(0.0, sig_r, size=3)
        noise_vel = self.rng.normal(0.0, sig_v, size=3)

        est_pos = truth.position_m + noise_pos
        est_vel = truth.velocity_mps + noise_vel

        # Construct 6x6 covariance
        cov_6x6 = np.zeros((6, 6), dtype=np.float64)
        for i in range(3):
            cov_6x6[i, i] = sig_r**2
            cov_6x6[i + 3, i + 3] = sig_v**2

        flags = ["ONBOARD_ESTIMATE", "VALID_OBSERVATION"]
        if is_outage:
            flags.append("DEGRADED_OUTAGE")

        return ObservedStateEstimate(
            target_id=truth.object_id,
            time_s=t,
            position_m=est_pos,
            velocity_mps=est_vel,
            covariance_6x6=cov_6x6,
            epoch_utc=truth.epoch_utc,
            frame=truth.frame,
            quality_flags=flags,
            source="onboard_navigation"
        )
