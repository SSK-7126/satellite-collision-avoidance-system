
import numpy as np

# Earth's standard gravitational parameter (m^3/s^2)
MU_EARTH = 3.986004418e14


def gravitational_acceleration(position):
    """
    Calculate Earth's gravitational acceleration.

    Parameters
    ----------
    position : array-like
        Position vector [x, y, z] in metres.

    Returns
    -------
    numpy.ndarray
        Gravitational acceleration [ax, ay, az] in m/s^2.
    """

    position = np.asarray(position, dtype=np.float64)

    radius = np.linalg.norm(position)

    if radius == 0:
        raise ValueError("Position cannot be at Earth's centre.")

    acceleration = -MU_EARTH * position / radius**3

    return acceleration


def gravity_gradient(position, mu=MU_EARTH):
    """
    Calculate the gravity gradient tensor (partial derivative of gravitational acceleration
    with respect to position) for two-body orbital dynamics.

    Equation:
        da / dr = mu * (3 * r * r^T / |r|^5 - I / |r|^3)

    Properties:
        - Symmetric: (da / dr)^T = da / dr
        - Traceless: Tr(da / dr) = 0 (Laplace's equation: nabla^2 U = 0)

    Parameters
    ----------
    position : array-like
        Position vector [x, y, z] in metres.
    mu : float, optional
        Gravitational parameter in m^3/s^2 (default Earth: 3.986004418e14).

    Returns
    -------
    numpy.ndarray
        3x3 symmetric gravity gradient matrix da/dr in s^-2.
    """
    position = np.asarray(position, dtype=np.float64)

    if position.shape != (3,):
        raise ValueError("Position must contain exactly 3 elements [x, y, z].")

    radius = np.linalg.norm(position)

    if radius == 0:
        raise ValueError("Position cannot be at Earth's centre.")

    r3 = radius**3
    r5 = radius**5

    gradient = mu * (
        3.0 * np.outer(position, position) / r5
        - np.eye(3, dtype=np.float64) / r3
    )

    return gradient
