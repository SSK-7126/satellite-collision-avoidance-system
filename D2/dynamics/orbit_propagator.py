
import numpy as np

from D2.dynamics.rk4 import rk4_step


def propagate_orbit(initial_state, duration, dt):
    """
    Propagate an orbital state over a specified duration.

    Parameters:
        initial_state : [x, y, z, vx, vy, vz]
        duration      : Total simulation time (seconds)
        dt            : Integration time step (seconds)

    Returns:
        times  : Simulation timestamps
        states : Position and velocity at each timestamp
    """

    if duration <= 0 or dt <= 0:
        raise ValueError("Duration and time step must be positive.")

    state = np.asarray(initial_state, dtype=np.float64).copy()

    if state.shape != (6,):
        raise ValueError("Initial state must contain 6 elements.")

    times = [0.0]
    states = [state.copy()]

    elapsed = 0.0

    while elapsed < duration:
        step = min(dt, duration - elapsed)

        state = rk4_step(state, step)

        elapsed += step

        times.append(elapsed)
        states.append(state.copy())

    return np.array(times), np.array(states)
