
import numpy as np

from D2.dynamics.two_body import gravitational_acceleration


def state_derivative(state):
    """
    Calculate the derivative of the orbital state.

    State format:
    [x, y, z, vx, vy, vz]

    Returns:
    [vx, vy, vz, ax, ay, az]
    """

    position = state[:3]
    velocity = state[3:]

    acceleration = gravitational_acceleration(position)

    return np.concatenate((velocity, acceleration))


def rk4_step(state, dt):
    """
    Perform one Runge-Kutta 4 integration step.

    Parameters:
        state : Current position and velocity (SI units).
        dt    : Integration time step in seconds.

    Returns:
        Updated orbital state.
    """

    state = np.asarray(state, dtype=np.float64)

    if state.shape != (6,):
        raise ValueError("State must contain 6 elements.")

    if dt <= 0:
        raise ValueError("Time step must be positive.")

    k1 = state_derivative(state)
    k2 = state_derivative(state + 0.5 * dt * k1)
    k3 = state_derivative(state + 0.5 * dt * k2)
    k4 = state_derivative(state + dt * k3)

    new_state = state + (dt / 6.0) * (
        k1 + 2*k2 + 2*k3 + k4
    )

    return new_state
