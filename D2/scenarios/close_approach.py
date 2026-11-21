"""
D2/scenarios/close_approach.py
==============================
Controlled Close-Approach Orbital Encounter Scenario for Deliverable 2 (D2).

Generates initial state vectors for a two-body close-approach encounter
between a protected primary satellite and a secondary space debris object
in Earth-centred inertial (ECI) coordinates using SI units.

Conventions & Units:
- Reference Frame : Earth-Centred Inertial (ECI)
- Distance / Pos  : Metres (m)
- Velocity        : Metres per second (m/s)
- Coordinates     : [x, y, z, vx, vy, vz]
"""

import numpy as np

from D2.dynamics.two_body import MU_EARTH


# Default scenario parameters (SI units: m, m/s)
DEFAULT_ORBITAL_RADIUS = 7_000_000.0       # 7,000 km orbital radius
DEFAULT_DEBRIS_OFFSET_Y = 10_000.0         # 10 km initial in-plane along-track offset
DEFAULT_DEBRIS_DELTA_VY = -10.0            # -10 m/s relative velocity offset


def calculate_relative_state(state1, state2):
    """
    Calculate initial relative position and velocity vectors between two objects.

    Relative quantities are defined as Object 2 relative to Object 1:
        r_rel = r2 - r1
        v_rel = v2 - v1

    Parameters
    ----------
    state1 : array-like
        Six-dimensional state vector of Object 1 (Protected Satellite)
        [x, y, z, vx, vy, vz] in SI units (m, m/s).
    state2 : array-like
        Six-dimensional state vector of Object 2 (Secondary Debris)
        [x, y, z, vx, vy, vz] in SI units (m, m/s).

    Returns
    -------
    r_rel : numpy.ndarray
        Relative position vector [rx, ry, rz] in metres.
    v_rel : numpy.ndarray
        Relative velocity vector [vx, vy, vz] in metres/second.
    """
    state1 = np.asarray(state1, dtype=np.float64)
    state2 = np.asarray(state2, dtype=np.float64)

    if state1.shape != (6,) or state2.shape != (6,):
        raise ValueError("Both state vectors must contain exactly 6 elements [x, y, z, vx, vy, vz].")

    r1 = state1[:3]
    v1 = state1[3:]
    r2 = state2[:3]
    v2 = state2[3:]

    r_rel = r2 - r1
    v_rel = v2 - v1

    return r_rel, v_rel


def create_close_approach_scenario(
    radius=DEFAULT_ORBITAL_RADIUS,
    debris_offset_y=DEFAULT_DEBRIS_OFFSET_Y,
    debris_delta_vy=DEFAULT_DEBRIS_DELTA_VY,
    return_relative=False
):
    """
    Generate a controlled two-object close-approach orbital encounter scenario.

    Object 1 (Protected Satellite):
        - Position : [radius, 0, 0] metres
        - Velocity : [0, v_circular, 0] metres/second

    Object 2 (Secondary Debris Object):
        - Position : [radius, debris_offset_y, 0] metres
        - Velocity : [0, v_circular + debris_delta_vy, 0] metres/second

    Calculations:
        1. Circular orbital velocity: v = sqrt(mu / r)
        2. Protected satellite initial state: [x1, y1, z1, vx1, vy1, vz1]
        3. Secondary debris initial state: [x2, y2, z2, vx2, vy2, vz2]
        4. Initial relative position: r_rel = r2 - r1
        5. Initial relative velocity: v_rel = v2 - v1

    Parameters
    ----------
    radius : float, optional
        Orbital radius in metres (default: 7,000,000.0 m).
    debris_offset_y : float, optional
        Initial Y-axis offset for debris in metres (default: 10,000.0 m).
    debris_delta_vy : float, optional
        Initial Y-axis velocity difference for debris in m/s (default: -10.0 m/s).
    return_relative : bool, optional
        If True, also returns (r_rel, v_rel). Default is False.

    Returns
    -------
    state_protected : numpy.ndarray
        6D state vector of the protected satellite [x, y, z, vx, vy, vz] in SI units.
    state_debris : numpy.ndarray
        6D state vector of the secondary debris [x, y, z, vx, vy, vz] in SI units.
    r_rel : numpy.ndarray (only if return_relative is True)
        Initial relative position vector (r2 - r1) in metres.
    v_rel : numpy.ndarray (only if return_relative is True)
        Initial relative velocity vector (v2 - v1) in metres/second.
    """
    if radius <= 0:
        raise ValueError("Orbital radius must be strictly positive.")

    # 1. Calculate circular orbital velocity using: v = sqrt(mu / r)
    v_circ = np.sqrt(MU_EARTH / radius)

    # 2. Generate protected satellite's initial state
    #    Position: [7000000, 0, 0] metres
    #    Velocity: [0, circular_velocity, 0] metres/second
    r_protected = np.array([radius, 0.0, 0.0], dtype=np.float64)
    v_protected = np.array([0.0, v_circ, 0.0], dtype=np.float64)
    state_protected = np.concatenate((r_protected, v_protected))

    # 3. Generate secondary debris object's initial state
    #    Position: [7000000, 10000, 0] metres
    #    Velocity: [0, circular_velocity - 10, 0] metres/second
    r_debris = np.array([radius, float(debris_offset_y), 0.0], dtype=np.float64)
    v_debris = np.array([0.0, v_circ + float(debris_delta_vy), 0.0], dtype=np.float64)
    state_debris = np.concatenate((r_debris, v_debris))

    # 4. Calculate initial relative position: r_rel = r2 - r1
    r_rel = r_debris - r_protected

    # 5. Calculate initial relative velocity: v_rel = v2 - v1
    v_rel = v_debris - v_protected

    # 6. Return state vectors
    if return_relative:
        return state_protected, state_debris, r_rel, v_rel

    return state_protected, state_debris


if __name__ == "__main__":
    sat_state, deb_state = create_close_approach_scenario()
    r_rel, v_rel = calculate_relative_state(sat_state, deb_state)

    print("=" * 65)
    print("D2 CLOSE-APPROACH SCENARIO GENERATION")
    print("=" * 65)
    print(f"Protected Satellite State (m, m/s):")
    print(f"  Position: {sat_state[:3]}")
    print(f"  Velocity: {sat_state[3:]}")
    print(f"  Radius  : {np.linalg.norm(sat_state[:3]):.3f} m")
    print(f"  Speed   : {np.linalg.norm(sat_state[3:]):.3f} m/s")
    print()
    print(f"Secondary Debris State (m, m/s):")
    print(f"  Position: {deb_state[:3]}")
    print(f"  Velocity: {deb_state[3:]}")
    print(f"  Radius  : {np.linalg.norm(deb_state[:3]):.3f} m")
    print(f"  Speed   : {np.linalg.norm(deb_state[3:]):.3f} m/s")
    print()
    print(f"Relative State (Debris - Satellite):")
    print(f"  Relative Position (r_rel) : {r_rel} m")
    print(f"  Initial Separation        : {np.linalg.norm(r_rel):.3f} m")
    print(f"  Relative Velocity (v_rel) : {v_rel} m/s")
    print(f"  Relative Speed            : {np.linalg.norm(v_rel):.3f} m/s")
    print("=" * 65)

