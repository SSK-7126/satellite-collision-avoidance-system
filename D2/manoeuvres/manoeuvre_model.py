"""
D2/manoeuvres/manoeuvre_model.py
================================
Impulsive Collision-Avoidance Manoeuvre Representation, Coordinate Frames,
and Mission Constraints for Deliverable 2 (D2).

Methodology & Standards:
1. Local Orbital Frame (RTN):
   - Radial (R)      : Unit vector along satellite position from Earth centre (r / |r|).
   - Normal (N)      : Unit vector along orbital angular momentum (r x v / |r x v|),
                       representing cross-track out-of-plane direction.
   - Transverse (T)  : Unit vector completing the right-handed triad (u_N x u_R),
                       representing along-track in-plane direction.
2. Frame Transformations:
   - Transform delta-v vectors between RTN and ECI using the rotation matrix
     R_{RTN->ECI} = [u_R, u_T, u_N].
3. Impulsive Manoeuvre Model:
   - Instantaneous velocity increment Delta_v applied at a specified burn epoch t_burn.
   - Spacecraft position remains continuous across the impulse.
4. Mission Constraints:
   - Configurable limits on delta-v magnitude, lead time, and trajectory deviation.

Conventions & Units:
- Reference Frame : Earth-Centred Inertial (ECI)
- Local Frame     : Radial-Transverse-Normal (RTN)
- Distances       : Metres (m)
- Velocities      : Metres per second (m/s)
- Time            : Seconds (s)
- Precision       : Float64
"""

from dataclasses import dataclass, field
from typing import Optional, Dict, Any
import numpy as np


# Standard unit direction vectors defined in the RTN frame
# [delta_v_R, delta_v_T, delta_v_N]
DIRECTION_VECTORS_RTN: Dict[str, np.ndarray] = {
    "+T": np.array([0.0, 1.0, 0.0], dtype=np.float64),      # Along-track prograde
    "-T": np.array([0.0, -1.0, 0.0], dtype=np.float64),     # Along-track retrograde
    "+N": np.array([0.0, 0.0, 1.0], dtype=np.float64),      # Cross-track (normal +)
    "-N": np.array([0.0, 0.0, -1.0], dtype=np.float64),     # Cross-track (normal -)
    "+R": np.array([1.0, 0.0, 0.0], dtype=np.float64),      # Radial outward
    "-R": np.array([-1.0, 0.0, 0.0], dtype=np.float64),     # Radial inward
    "+T+N": np.array([0.0, 1.0 / np.sqrt(2.0), 1.0 / np.sqrt(2.0)], dtype=np.float64),
    "+T-N": np.array([0.0, 1.0 / np.sqrt(2.0), -1.0 / np.sqrt(2.0)], dtype=np.float64),
    "-T+N": np.array([0.0, -1.0 / np.sqrt(2.0), 1.0 / np.sqrt(2.0)], dtype=np.float64),
    "-T-N": np.array([0.0, -1.0 / np.sqrt(2.0), -1.0 / np.sqrt(2.0)], dtype=np.float64),
    "+T+R": np.array([1.0 / np.sqrt(2.0), 1.0 / np.sqrt(2.0), 0.0], dtype=np.float64),
    "+T-R": np.array([-1.0 / np.sqrt(2.0), 1.0 / np.sqrt(2.0), 0.0], dtype=np.float64),
    "-T+R": np.array([1.0 / np.sqrt(2.0), -1.0 / np.sqrt(2.0), 0.0], dtype=np.float64),
    "-T-R": np.array([-1.0 / np.sqrt(2.0), -1.0 / np.sqrt(2.0), 0.0], dtype=np.float64),
}


def compute_rtn_basis(r_eci, v_eci):
    """
    Compute the orthonormal Radial-Transverse-Normal (RTN) basis vectors
    at a given orbital state in the Earth-Centred Inertial (ECI) frame.

    Equations:
        u_R = r / |r|
        u_N = (r x v) / |r x v|
        u_T = u_N x u_R

    Parameters
    ----------
    r_eci : array-like
        3D position vector in ECI [x, y, z] in metres.
    v_eci : array-like
        3D velocity vector in ECI [vx, vy, vz] in metres/second.

    Returns
    -------
    R_rtn_to_eci : numpy.ndarray
        3x3 rotation matrix whose columns are [u_R, u_T, u_N].
        Transforms a vector from RTN to ECI: v_eci = R_rtn_to_eci @ v_rtn.
    """
    r = np.asarray(r_eci, dtype=np.float64)
    v = np.asarray(v_eci, dtype=np.float64)

    if r.shape != (3,) or v.shape != (3,):
        raise ValueError("r_eci and v_eci must be 3-element vectors.")

    r_norm = float(np.linalg.norm(r))
    if r_norm <= 0.0:
        raise ValueError("Position vector norm must be strictly positive.")

    u_R = r / r_norm

    h_vec = np.cross(r, v)
    h_norm = float(np.linalg.norm(h_vec))
    if h_norm <= 0.0:
        raise ValueError("Angular momentum is zero (collinear position and velocity).")

    u_N = h_vec / h_norm
    u_T = np.cross(u_N, u_R)
    u_T = u_T / np.linalg.norm(u_T)

    # Columns are the unit vectors of RTN expressed in ECI coordinates
    return np.column_stack((u_R, u_T, u_N))


def rtn_to_eci(delta_v_rtn, r_eci, v_eci):
    """
    Transform a delta-v vector from the satellite's local RTN frame into the ECI frame.

    Parameters
    ----------
    delta_v_rtn : array-like
        Delta-v vector [dv_R, dv_T, dv_N] in m/s.
    r_eci : array-like
        Satellite position vector at burn epoch in metres.
    v_eci : array-like
        Satellite velocity vector at burn epoch in metres/second.

    Returns
    -------
    delta_v_eci : numpy.ndarray
        Delta-v vector [dv_x, dv_y, dv_z] in ECI in m/s.
    """
    dv_rtn = np.asarray(delta_v_rtn, dtype=np.float64)
    if dv_rtn.shape != (3,):
        raise ValueError("delta_v_rtn must contain 3 elements [dv_R, dv_T, dv_N].")

    R_mat = compute_rtn_basis(r_eci, v_eci)
    return R_mat @ dv_rtn


def eci_to_rtn(delta_v_eci, r_eci, v_eci):
    """
    Transform a delta-v vector from ECI into the satellite's local RTN frame.

    Parameters
    ----------
    delta_v_eci : array-like
        Delta-v vector [dv_x, dv_y, dv_z] in ECI in m/s.
    r_eci : array-like
        Satellite position vector in metres.
    v_eci : array-like
        Satellite velocity vector in metres/second.

    Returns
    -------
    delta_v_rtn : numpy.ndarray
        Delta-v vector [dv_R, dv_T, dv_N] in RTN in m/s.
    """
    dv_eci = np.asarray(delta_v_eci, dtype=np.float64)
    if dv_eci.shape != (3,):
        raise ValueError("delta_v_eci must contain 3 elements [dv_x, dv_y, dv_z].")

    R_mat = compute_rtn_basis(r_eci, v_eci)
    return R_mat.T @ dv_eci


@dataclass
class ImpulsiveManoeuvre:
    """
    Data model representing a candidate impulsive collision-avoidance manoeuvre.

    Attributes
    ----------
    burn_time : float
        Burn epoch in seconds from scenario start (t_burn >= 0).
    delta_v_magnitude : float
        Total velocity increment magnitude |Delta_v| in metres/second.
    direction_label : str
        Direction identifier in RTN frame (e.g. '+T', '-T', '+N', '-N', '+R', '-R').
    delta_v_rtn : numpy.ndarray
        Delta-v components in RTN [dv_R, dv_T, dv_N] in metres/second.
    delta_v_eci : Optional[numpy.ndarray]
        Delta-v vector in ECI [dv_x, dv_y, dv_z] in metres/second.
    manoeuvre_id : str
        Unique candidate identifier.
    """
    burn_time: float
    delta_v_magnitude: float
    direction_label: str
    delta_v_rtn: np.ndarray
    delta_v_eci: Optional[np.ndarray] = None
    manoeuvre_id: str = field(default="")

    def __post_init__(self):
        self.burn_time = float(self.burn_time)
        self.delta_v_magnitude = float(self.delta_v_magnitude)
        self.delta_v_rtn = np.asarray(self.delta_v_rtn, dtype=np.float64)

        if self.burn_time < 0.0:
            raise ValueError(f"Burn time must be non-negative, got {self.burn_time}.")
        if self.delta_v_magnitude <= 0.0:
            raise ValueError(f"Delta-v magnitude must be strictly positive, got {self.delta_v_magnitude}.")
        if self.delta_v_rtn.shape != (3,):
            raise ValueError("delta_v_rtn must have 3 elements.")

        if not self.manoeuvre_id:
            self.manoeuvre_id = f"MAN_{self.direction_label}_{self.delta_v_magnitude:.2f}mps_T{self.burn_time:.0f}s"

    @property
    def radial_component(self) -> float:
        return float(self.delta_v_rtn[0])

    @property
    def along_track_component(self) -> float:
        return float(self.delta_v_rtn[1])

    @property
    def cross_track_component(self) -> float:
        return float(self.delta_v_rtn[2])

    def resolve_eci(self, r_eci, v_eci):
        """Compute and cache delta_v_eci given the satellite's state at burn time."""
        self.delta_v_eci = rtn_to_eci(self.delta_v_rtn, r_eci, v_eci)
        return self.delta_v_eci


@dataclass
class ManoeuvreConstraints:
    """
    Configurable operational and safety mission constraints for manoeuvre selection.

    Attributes
    ----------
    max_delta_v : float
        Maximum permitted delta-v magnitude in m/s (default 5.0 m/s).
    min_miss_distance : float
        Minimum required separation distance threshold at TCA in metres (default 2,000.0 m).
    max_target_pc : float
        Maximum acceptable collision probability after manoeuvre (default 1e-5).
    max_trajectory_deviation : Optional[float]
        Maximum allowed orbital displacement from nominal path in metres (default None).
    min_lead_time : float
        Minimum advance lead time before burn epoch in seconds (default 30.0 s).
    """
    max_delta_v: float = 5.0
    min_miss_distance: float = 2000.0
    max_target_pc: float = 1e-5
    max_trajectory_deviation: Optional[float] = None
    min_lead_time: float = 30.0

    def __post_init__(self):
        if self.max_delta_v <= 0.0:
            raise ValueError("max_delta_v must be strictly positive.")
        if self.min_miss_distance <= 0.0:
            raise ValueError("min_miss_distance must be strictly positive.")
        if self.max_target_pc <= 0.0 or self.max_target_pc > 1.0:
            raise ValueError("max_target_pc must be in the open-closed interval (0, 1].")
        if self.min_lead_time < 0.0:
            raise ValueError("min_lead_time must be non-negative.")
        if self.max_trajectory_deviation is not None and self.max_trajectory_deviation <= 0.0:
            raise ValueError("max_trajectory_deviation must be strictly positive when set.")
