"""
D2/dynamics/variational.py
==========================
Variational Equations and Two-Body Orbital State-Transition Matrix (STM) Integrator
for Deliverable 2 (D2).

Formulation & Methodology:
1. Two-Body Equations of Motion:
      dr / dt = v
      dv / dt = a(r) = -mu * r / |r|^3

2. Orbital State-Transition Matrix (STM):
      Phi(t, t0) = d x(t) / d x(t0)
   Initial condition:
      Phi(t0, t0) = I_6

3. Variational Differential Equation:
      d Phi / dt = A(t) * Phi
   where:
      A(t) = [    0_3        I_3   ]
             [ da / dr(r)    0_3   ]

      da / dr = mu * (3 * r * r^T / |r|^5 - I_3 / |r|^3)

4. Coupled Numerical Integration:
   The 6D orbital state and 6x6 state-transition matrix (total 42 state elements)
   are integrated simultaneously using the standard 4th-order Runge-Kutta (RK4)
   algorithm, guaranteeing mathematical and temporal consistency with the RK4
   orbit propagator.

Conventions & Units:
- Reference Frame : Earth-Centred Inertial (ECI)
- Position Units  : Metres (m)
- Velocity Units  : Metres/second (m/s)
- Time Units      : Seconds (s)
- Precision       : Float64
"""

import numpy as np

from D2.dynamics.two_body import MU_EARTH, gravitational_acceleration, gravity_gradient
from D2.dynamics.orbit_propagator import propagate_orbit


def variational_matrix_a(position, mu=MU_EARTH):
    """
    Construct the 6x6 variational system matrix A(t) = df/dx for two-body orbital dynamics.

    Equation:
        A(t) = [    0_3        I_3 ]
               [ da / dr(r)    0_3 ]

    Properties:
        - Tr(A(t)) = 0 (traceless, ensuring det(Phi(t)) = 1 by Liouville's theorem)

    Parameters
    ----------
    position : array-like
        Position vector [x, y, z] in metres.
    mu : float, optional
        Earth gravitational parameter (m^3/s^2).

    Returns
    -------
    numpy.ndarray
        6x6 variational dynamics matrix A(t).
    """
    g_grad = gravity_gradient(position, mu=mu)

    a_mat = np.zeros((6, 6), dtype=np.float64)
    a_mat[:3, 3:] = np.eye(3, dtype=np.float64)
    a_mat[3:, :3] = g_grad

    return a_mat


def variational_derivative(state, phi, mu=MU_EARTH):
    """
    Evaluate time derivatives of coupled orbital state and state-transition matrix.

    Equations:
        d state / dt = [v, a(r)]
        d Phi / dt   = A(r) * Phi

    Parameters
    ----------
    state : array-like
        6D state vector [x, y, z, vx, vy, vz].
    phi : array-like
        6x6 state-transition matrix Phi.
    mu : float, optional
        Gravitational parameter.

    Returns
    -------
    state_dot : numpy.ndarray
        6D state derivative [vx, vy, vz, ax, ay, az].
    phi_dot : numpy.ndarray
        6x6 matrix derivative dPhi/dt.
    """
    pos = state[:3]
    vel = state[3:]

    acc = gravitational_acceleration(pos)
    a_mat = variational_matrix_a(pos, mu=mu)

    state_dot = np.concatenate((vel, acc))
    phi_dot = a_mat @ phi

    return state_dot, phi_dot


def propagate_state_and_stm(
    initial_state,
    duration,
    dt=1.0,
    initial_stm=None,
    mu=MU_EARTH,
    return_trajectory=False
):
    """
    Simultaneously propagate the orbital state and orbital state-transition matrix
    Phi(t, t0) over a specified duration using 4th-order Runge-Kutta (RK4).

    Parameters
    ----------
    initial_state : array-like
        Initial 6D orbital state [x, y, z, vx, vy, vz] in SI units.
    duration : float
        Total propagation time in seconds.
    dt : float, optional
        Integration time step in seconds (default 1.0 s).
    initial_stm : array-like, optional
        Initial 6x6 STM at t0. Default is the 6x6 identity matrix I_6.
    mu : float, optional
        Gravitational parameter (m^3/s^2).
    return_trajectory : bool, optional
        If True, returns full history (times, states, stms).
        If False (default), returns final state and final STM.

    Returns
    -------
    final_state : numpy.ndarray
        6D state vector at time t = duration.
    final_stm : numpy.ndarray
        6x6 orbital state-transition matrix Phi(duration, 0).
    (Optional if return_trajectory=True):
        times  : 1D array of timestamps.
        states : Nx6 array of orbital states.
        stms   : Nx6x6 array of state-transition matrices.
    """
    if duration < 0:
        raise ValueError("Propagation duration must be non-negative.")
    if dt <= 0:
        raise ValueError("Integration time step must be strictly positive.")

    state = np.asarray(initial_state, dtype=np.float64).copy()
    if state.shape != (6,):
        raise ValueError("Initial state must contain exactly 6 elements [x, y, z, vx, vy, vz].")

    if initial_stm is None:
        phi = np.eye(6, dtype=np.float64)
    else:
        phi = np.asarray(initial_stm, dtype=np.float64).copy()
        if phi.shape != (6, 6):
            raise ValueError("Initial STM must have shape (6, 6).")

    times = [0.0]
    states = [state.copy()]
    stms = [phi.copy()]

    elapsed = 0.0

    while elapsed < duration:
        h = min(dt, duration - elapsed)

        # Stage 1
        s_k1, p_k1 = variational_derivative(state, phi, mu=mu)

        # Stage 2
        s_mid1 = state + 0.5 * h * s_k1
        p_mid1 = phi + 0.5 * h * p_k1
        s_k2, p_k2 = variational_derivative(s_mid1, p_mid1, mu=mu)

        # Stage 3
        s_mid2 = state + 0.5 * h * s_k2
        p_mid2 = phi + 0.5 * h * p_k2
        s_k3, p_k3 = variational_derivative(s_mid2, p_mid2, mu=mu)

        # Stage 4
        s_end = state + h * s_k3
        p_end = phi + h * p_k3
        s_k4, p_k4 = variational_derivative(s_end, p_end, mu=mu)

        # RK4 update
        state += (h / 6.0) * (s_k1 + 2.0 * s_k2 + 2.0 * s_k3 + s_k4)
        phi += (h / 6.0) * (p_k1 + 2.0 * p_k2 + 2.0 * p_k3 + p_k4)
        elapsed += h

        if return_trajectory:
            times.append(elapsed)
            states.append(state.copy())
            stms.append(phi.copy())

    if return_trajectory:
        return np.array(times), np.array(states), np.array(stms)

    return state, phi


def compute_stm_finite_difference(
    initial_state,
    duration,
    dt=1.0,
    eps_pos=1.0,
    eps_vel=1e-3,
    mu=MU_EARTH
):
    """
    Calculate the two-body state-transition matrix using central finite-difference
    perturbations of the initial state propagated through the standard orbit propagator.

    Equation:
        Phi_FD[:, j] = [x(t; x0 + eps * e_j) - x(t; x0 - eps * e_j)] / (2 * eps)

    Parameters
    ----------
    initial_state : array-like
        Initial 6D orbital state.
    duration : float
        Propagation duration in seconds.
    dt : float, optional
        Integration time step in seconds (default 1.0 s).
    eps_pos : float, optional
        Position perturbation in metres (default 1.0 m).
    eps_vel : float, optional
        Velocity perturbation in m/s (default 1e-3 m/s).
    mu : float, optional
        Earth gravitational parameter.

    Returns
    -------
    phi_fd : numpy.ndarray
        6x6 finite-difference state-transition matrix.
    """
    state0 = np.asarray(initial_state, dtype=np.float64).copy()
    phi_fd = np.zeros((6, 6), dtype=np.float64)

    for j in range(6):
        eps = float(eps_pos if j < 3 else eps_vel)

        s_plus = state0.copy()
        s_minus = state0.copy()
        s_plus[j] += eps
        s_minus[j] -= eps

        _, states_plus = propagate_orbit(s_plus, duration=duration, dt=dt)
        _, states_minus = propagate_orbit(s_minus, duration=duration, dt=dt)

        phi_fd[:, j] = (states_plus[-1] - states_minus[-1]) / (2.0 * eps)

    return phi_fd


def compute_symplecticity_residual(phi):
    """
    Calculate the Hamiltonian symplecticity residual of a 6x6 state-transition matrix.

    Equation:
        J = [  0_3   I_3 ]
            [ -I_3   0_3 ]
        Residual = norm(Phi^T @ J @ Phi - J)

    For any Hamiltonian dynamical system (including two-body Keplerian motion),
    the state-transition matrix Phi is symplectic, satisfying Phi^T @ J @ Phi = J.

    Parameters
    ----------
    phi : array-like
        6x6 state-transition matrix to evaluate.

    Returns
    -------
    residual_norm : float
        Frobenius norm of the symplecticity error matrix ||Phi^T @ J @ Phi - J||.
    max_entry_error : float
        Maximum absolute element-wise error max |(Phi^T @ J @ Phi - J)_{ij}|.
    """
    phi_arr = np.asarray(phi, dtype=np.float64)
    if phi_arr.shape != (6, 6):
        raise ValueError(f"State-transition matrix must have shape (6, 6), got {phi_arr.shape}.")

    j_mat = np.zeros((6, 6), dtype=np.float64)
    j_mat[:3, 3:] = np.eye(3, dtype=np.float64)
    j_mat[3:, :3] = -np.eye(3, dtype=np.float64)

    symp_mat = phi_arr.T @ j_mat @ phi_arr - j_mat
    res_norm = float(np.linalg.norm(symp_mat))
    max_entry = float(np.max(np.abs(symp_mat)))

    return res_norm, max_entry


def validate_stm_accuracy(stm_analytical, stm_fd, rtol=1e-3, atol=1e-4, symp_tol=1e-9):
    """
    Validate the analytical variational STM against finite-difference STM and
    Hamiltonian symplecticity criteria.

    Parameters
    ----------
    stm_analytical : array-like
        6x6 analytically integrated STM.
    stm_fd : array-like
        6x6 finite-difference STM.
    rtol : float, optional
        Relative tolerance threshold (default 1e-3).
    atol : float, optional
        Absolute tolerance threshold (default 1e-4).
    symp_tol : float, optional
        Symplecticity residual tolerance threshold (default 1e-9).

    Returns
    -------
    validation : dict
        Dictionary containing max absolute error, max relative error,
        determinant, symplecticity residuals, and validation pass/fail flag.
    """
    phi_a = np.asarray(stm_analytical, dtype=np.float64)
    phi_num = np.asarray(stm_fd, dtype=np.float64)

    abs_diff = np.abs(phi_a - phi_num)
    max_abs_err = float(np.max(abs_diff))

    # Scale relative difference by element magnitude with 1.0 floor
    rel_diff = abs_diff / np.maximum(np.abs(phi_a), 1.0)
    max_rel_err = float(np.max(rel_diff))

    det_val = float(np.linalg.det(phi_a))
    det_err = float(abs(det_val - 1.0))

    symp_norm, symp_max_entry = compute_symplecticity_residual(phi_a)

    is_valid = bool(
        (max_rel_err <= rtol or max_abs_err <= atol)
        and symp_norm <= symp_tol
    )

    return {
        "max_abs_error": max_abs_err,
        "max_rel_error": max_rel_err,
        "determinant": det_val,
        "determinant_error": det_err,
        "symplecticity_residual_norm": symp_norm,
        "symplecticity_max_entry": symp_max_entry,
        "is_valid": is_valid,
    }

