"""
D2/visualization/coordinate_transform.py
========================================
Earth-Centred Inertial (ECI) to Unreal Engine 5 Coordinate Adapter Module.
Strictly following Section 2 of the Satellite Anti-Collision Technical Guide.

Coordinate Conventions & Methodological Principles:
1. Source Frame (Scientific Solver):
   - Reference Frame : Earth-Centred Inertial (ECI, J2000 / GCRF)
   - Coordinate System: Right-handed Cartesian triad
       * +X_ECI : Points towards the Vernal Equinox (First Point of Aries)
       * +Z_ECI : Aligned with Earth's rotational north celestial pole
       * +Y_ECI : Completes right-handed triad in equatorial plane (+Z x +X)
   - Units           : SI Units (metres, metres/second, seconds)
   - Precision       : Float64 (double precision)

2. Target Frame (Unreal Engine 5 Display):
   - Coordinate System: Left-handed Cartesian triad, Z-up
       * +X_UE  : Forward
       * +Y_UE  : Right
       * +Z_UE  : Up (aligned with Earth North pole)
   - Standard Unit   : Centimetres (1 Unreal Unit [uu] = 1 cm)

3. Handedness & Axes Mapping:
   - To convert from right-handed ECI to left-handed Unreal Engine while preserving
     the physical Earth rotational axis (+Z pointing Up):
       X_UE = +X_ECI * scale
       Y_UE = -Y_ECI * scale    (handedness parity reflection)
       Z_UE = +Z_ECI * scale

   - Transformation Matrix M:
       M = scale * [  1   0   0 ]
                   [  0  -1   0 ]
                   [  0   0   1 ]
       det(M / scale) = -1.0 (exact parity inversion for handedness transition)
       M / scale is orthogonal and self-inverse: (M/scale)^T @ (M/scale) = I_3.

4. Display Scale Factor (Technical Guide Section 2.2):
   - Literal 1:1 scale (1 uu = 1 cm, scale = 100.0) yields Earth radius = 637,813,700 uu.
   - For optimal viewport rendering, camera stability, and legibility, a macro display scale
     is defined:
       DEFAULT_RENDER_SCALE = 0.01  (1 uu = 100 metres; 1 km = 10 uu)
       Earth Radius in UE   = 63,781.37 uu (~637.8 m world size)
       LEO Orbit Radius     = 70,000.00 uu (~700.0 m world size)
   - Architectural Principle: Display coordinates are NEVER fed back into the scientific solver.
"""

from typing import Tuple, Union, Sequence, Optional
import numpy as np

# Standard Earth physical constants
EARTH_RADIUS_M = 6_378_137.0  # WGS-84 equatorial radius in metres

# Supported visualization display scales (Unreal Units per metre)
DEFAULT_RENDER_SCALE = 0.01   # Macro scale: 1 uu = 100 m (Earth radius = 63,781.37 uu)
LWC_RENDER_SCALE = 100.0      # Literal scale: 1 uu = 1 cm (Large World Coordinates)


def get_transformation_matrix(scale: float = DEFAULT_RENDER_SCALE) -> np.ndarray:
    """
    Return the 3x3 transformation matrix converting ECI vectors to Unreal Engine coordinates.

    Parameters
    ----------
    scale : float, optional
        Display scale factor in Unreal Units per metre (default: 0.01 uu/m).

    Returns
    -------
    M : numpy.ndarray
        3x3 linear transformation matrix.
    """
    scale_float = float(scale)
    return np.diag([scale_float, -scale_float, scale_float]).astype(np.float64)


def eci_to_unreal_position(
    r_eci: Union[Sequence[float], np.ndarray],
    scale: float = DEFAULT_RENDER_SCALE
) -> np.ndarray:
    """
    Transform a 3D position vector from ECI (metres, right-handed) into
    Unreal Engine coordinates (Unreal Units, left-handed, Z-up).

    Equations:
        X_ue = +X_eci * scale
        Y_ue = -Y_eci * scale
        Z_ue = +Z_eci * scale

    Parameters
    ----------
    r_eci : array-like
        3-element position vector [x, y, z] in ECI in metres.
    scale : float, optional
        Scale factor in uu/m (default 0.01).

    Returns
    -------
    r_ue : numpy.ndarray
        3-element position vector [x, y, z] in Unreal Engine coordinates (uu).
    """
    r = np.asarray(r_eci, dtype=np.float64)
    if r.shape != (3,):
        raise ValueError(f"r_eci must be a 3-element vector, got shape {r.shape}.")

    scale_f = float(scale)
    return np.array([r[0] * scale_f, -r[1] * scale_f, r[2] * scale_f], dtype=np.float64)


def unreal_to_eci_position(
    r_ue: Union[Sequence[float], np.ndarray],
    scale: float = DEFAULT_RENDER_SCALE
) -> np.ndarray:
    """
    Inverse transform: convert an Unreal Engine coordinate vector back into ECI metres.

    Equations:
        X_eci = +X_ue / scale
        Y_eci = -Y_ue / scale
        Z_eci = +Z_ue / scale

    Parameters
    ----------
    r_ue : array-like
        3-element position vector [x, y, z] in Unreal Engine coordinates (uu).
    scale : float, optional
        Scale factor in uu/m (default 0.01).

    Returns
    -------
    r_eci : numpy.ndarray
        3-element position vector in ECI metres.
    """
    r = np.asarray(r_ue, dtype=np.float64)
    if r.shape != (3,):
        raise ValueError(f"r_ue must be a 3-element vector, got shape {r.shape}.")

    scale_f = float(scale)
    if scale_f <= 0.0:
        raise ValueError("Display scale factor must be strictly positive.")

    return np.array([r[0] / scale_f, -r[1] / scale_f, r[2] / scale_f], dtype=np.float64)


def eci_to_unreal_velocity(
    v_eci: Union[Sequence[float], np.ndarray],
    scale: float = DEFAULT_RENDER_SCALE
) -> np.ndarray:
    """
    Transform a velocity vector from ECI (m/s) into Unreal Engine coordinates (uu/s).

    Parameters
    ----------
    v_eci : array-like
        Velocity vector [vx, vy, vz] in ECI in m/s.
    scale : float, optional
        Scale factor in uu/m (default 0.01).

    Returns
    -------
    v_ue : numpy.ndarray
        Velocity vector in Unreal Engine coordinates (uu/s).
    """
    v = np.asarray(v_eci, dtype=np.float64)
    if v.shape != (3,):
        raise ValueError(f"v_eci must be a 3-element vector, got shape {v.shape}.")

    scale_f = float(scale)
    return np.array([v[0] * scale_f, -v[1] * scale_f, v[2] * scale_f], dtype=np.float64)


def unreal_to_eci_velocity(
    v_ue: Union[Sequence[float], np.ndarray],
    scale: float = DEFAULT_RENDER_SCALE
) -> np.ndarray:
    """
    Inverse transform for velocity: convert Unreal Engine velocity (uu/s) back to ECI (m/s).
    """
    v = np.asarray(v_ue, dtype=np.float64)
    if v.shape != (3,):
        raise ValueError(f"v_ue must be a 3-element vector, got shape {v.shape}.")

    scale_f = float(scale)
    if scale_f <= 0.0:
        raise ValueError("Display scale factor must be strictly positive.")

    return np.array([v[0] / scale_f, -v[1] / scale_f, v[2] / scale_f], dtype=np.float64)


def calculate_unreal_orientation(
    v_ue: Union[Sequence[float], np.ndarray]
) -> Tuple[float, float, float]:
    """
    Calculate satellite visual orientation (Roll, Pitch, Yaw in degrees) in Unreal Engine
    aligned with the instantaneous velocity vector (along-track flight orientation).

    Unreal Rotator Conventions:
        - Pitch : Rotation around Y_UE axis (elevation from horizontal plane)
        - Yaw   : Rotation around Z_UE axis (azimuth in X-Y plane)
        - Roll  : Rotation around X_UE axis (bank angle, default 0.0 deg)

    Parameters
    ----------
    v_ue : array-like
        3-element velocity vector in Unreal Engine coordinates [vx, vy, vz].

    Returns
    -------
    rotator : tuple of (roll, pitch, yaw) in degrees
        Euler angles in Unreal Engine format.
    """
    v = np.asarray(v_ue, dtype=np.float64)
    vx, vy, vz = float(v[0]), float(v[1]), float(v[2])

    horiz_speed = np.sqrt(vx * vx + vy * vy)

    # Yaw: angle in X-Y plane
    yaw_deg = float(np.degrees(np.arctan2(vy, vx)))

    # Pitch: angle out of X-Y plane
    pitch_deg = float(np.degrees(np.arctan2(vz, max(horiz_speed, 1e-12))))

    roll_deg = 0.0  # Zero bank angle baseline

    return (round(roll_deg, 3), round(pitch_deg, 3), round(yaw_deg, 3))


def transform_trajectory_eci_to_ue(
    trajectory_eci: np.ndarray,
    scale: float = DEFAULT_RENDER_SCALE
) -> np.ndarray:
    """
    Vectorized transformation of an Nx3 (positions) or Nx6 (positions + velocities)
    trajectory array from ECI into Unreal Engine coordinates.

    Parameters
    ----------
    trajectory_eci : numpy.ndarray
        Array of shape (N, 3) or (N, 6).
    scale : float, optional
        Scale factor in uu/m.

    Returns
    -------
    trajectory_ue : numpy.ndarray
        Transformed array of matching shape in Unreal Engine units.
    """
    arr = np.asarray(trajectory_eci, dtype=np.float64)
    if arr.ndim != 2 or arr.shape[1] not in (3, 6):
        raise ValueError(f"trajectory_eci must have shape (N, 3) or (N, 6), got {arr.shape}.")

    scale_f = float(scale)
    result = np.zeros_like(arr)

    # Transform positions [x, -y, z] * scale
    result[:, 0] = arr[:, 0] * scale_f
    result[:, 1] = -arr[:, 1] * scale_f
    result[:, 2] = arr[:, 2] * scale_f

    # Transform velocities if 6D state array
    if arr.shape[1] == 6:
        result[:, 3] = arr[:, 3] * scale_f
        result[:, 4] = -arr[:, 4] * scale_f
        result[:, 5] = arr[:, 5] * scale_f

    return result

