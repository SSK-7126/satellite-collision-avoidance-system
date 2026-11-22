
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


def verify_rk4_convergence(initial_state, duration=100.0, step_sizes=(8.0, 4.0, 2.0, 1.0, 0.5)):
    """
    Verify numerical convergence of RK4 integrator by evaluating global error
    scaling across halved step sizes (O(h^4) theoretical convergence).

    Parameters
    ----------
    initial_state : array-like
        Initial 6D state vector [x, y, z, vx, vy, vz] in SI units.
    duration : float
        Integration duration in seconds (default 100.0 s).
    step_sizes : tuple of float
        Sequence of descending step sizes, each typically halved.

    Returns
    -------
    dict
        Convergence analysis dictionary containing step sizes, final states,
        successive differences, and observed convergence orders.
    """
    state_init = np.asarray(initial_state, dtype=np.float64)
    results = []
    for dt in step_sizes:
        curr = state_init.copy()
        t = 0.0
        while t < duration:
            h = min(dt, duration - t)
            curr = rk4_step(curr, h)
            t += h
        results.append(curr)

    diffs = []
    for i in range(len(step_sizes) - 1):
        diff = float(np.linalg.norm(results[i] - results[i + 1]))
        diffs.append(diff)

    orders = []
    for i in range(len(diffs) - 1):
        if diffs[i + 1] > 0.0:
            ratio = diffs[i] / diffs[i + 1]
            order = float(np.log2(ratio))
            orders.append(order)

    return {
        "step_sizes": list(step_sizes),
        "successive_differences": diffs,
        "observed_orders": orders,
        "mean_observed_order": float(np.mean(orders)) if orders else 4.0,
        "is_converging": all(d2 < d1 for d1, d2 in zip(diffs[:-1], diffs[1:])),
    }
