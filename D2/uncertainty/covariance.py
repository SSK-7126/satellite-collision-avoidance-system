"""
D2/uncertainty/covariance.py
============================
Orbital State Uncertainty & Covariance Management Module for Deliverable 2 (D2),
strictly following Section 6.1 of the Satellite Anti-Collision Technical Guide.

Core Methodologies:
1. 6x6 Covariance Representation:
   - Position and velocity uncertainty represented by a 6x6 matrix P.
   - Diagonal elements describe variances (m^2 for position, m^2/s^2 for velocity).
   - Off-diagonal elements describe cross-correlations.
2. Covariance Validation:
   - Shape verification (must be exactly 6x6).
   - Symmetry verification: P = P^T within numerical tolerance.
   - Positive-semidefinite (PSD) verification: all eigenvalues >= -tol.
3. Relative Covariance Calculation (Independent-Error Assumption):
   - P_rel = P1 + P2 (valid only when P1 and P2 refer to the same frame and epoch).
4. Covariance Propagation:
   - P(t) = Phi(t, t0) * P(t0) * Phi(t, t0)^T + Q
   - Accepts state-transition matrix Phi and process-noise matrix Q.

Conventions & Units:
- Reference Frame : Earth-Centred Inertial (ECI)
- Position Units  : Metres (m), Variance in m^2
- Velocity Units  : Metres/second (m/s), Variance in m^2/s^2
- Precision       : Float64
"""

import numpy as np

from D2.dynamics.two_body import MU_EARTH
from D2.dynamics.variational import propagate_state_and_stm


def validate_covariance(cov, name="Covariance", rtol=1e-5, atol=1e-8):
    """
    Validate that a given matrix is a valid 6x6 symmetric positive-semidefinite
    covariance matrix.

    Parameters
    ----------
    cov : array-like
        Matrix to validate.
    name : str, optional
        Descriptive name of the covariance matrix for error reporting.
    rtol : float, optional
        Relative tolerance for symmetry check (default 1e-5).
    atol : float, optional
        Absolute tolerance for symmetry and eigenvalue non-negativity (default 1e-8).

    Returns
    -------
    cov_valid : numpy.ndarray
        Validated 6x6 covariance matrix as float64.

    Raises
    ------
    ValueError
        If the matrix is None, has incorrect shape, contains non-finite entries,
        is asymmetric, or has negative eigenvalues beyond numerical tolerance.
    """
    if cov is None:
        raise ValueError(f"{name} cannot be None.")

    cov_arr = np.asarray(cov, dtype=np.float64)

    # 1. Dimension validation
    if cov_arr.shape != (6, 6):
        raise ValueError(f"{name} must have dimensions (6, 6), got shape {cov_arr.shape}.")

    # 2. Finiteness validation
    if not np.all(np.isfinite(cov_arr)):
        raise ValueError(f"{name} contains non-finite values (NaN or Inf).")

    # 3. Symmetry validation: P == P^T
    if not np.allclose(cov_arr, cov_arr.T, rtol=rtol, atol=atol):
        max_asym = np.max(np.abs(cov_arr - cov_arr.T))
        raise ValueError(
            f"{name} is not symmetric. Maximum asymmetry |P - P^T| = {max_asym:.3e} "
            f"(exceeds tolerance atol={atol:.1e})."
        )

    # Enforce exact numerical symmetry to eliminate minuscule floating-point asymmetries
    cov_sym = 0.5 * (cov_arr + cov_arr.T)

    # 4. Positive-semidefinite validation: all eigenvalues >= -atol
    eigenvalues = np.linalg.eigvalsh(cov_sym)
    min_eigenval = float(np.min(eigenvalues))

    if min_eigenval < -atol:
        raise ValueError(
            f"{name} is not positive-semidefinite. Minimum eigenvalue = {min_eigenval:.3e} "
            f"(negative beyond numerical tolerance atol={atol:.1e})."
        )

    # Minor numerical projection: clip negligible negative eigenvalues (e.g. -1e-15) to zero
    if min_eigenval < 0.0:
        eigvals, eigvecs = np.linalg.eigh(cov_sym)
        eigvals = np.maximum(eigvals, 0.0)
        cov_sym = eigvecs @ np.diag(eigvals) @ eigvecs.T
        cov_sym = 0.5 * (cov_sym + cov_sym.T)

    return cov_sym


def is_valid_covariance(cov, rtol=1e-5, atol=1e-8):
    """
    Check if a matrix is a valid 6x6 covariance matrix without raising exceptions.

    Parameters
    ----------
    cov : array-like
        Matrix to inspect.

    Returns
    -------
    is_valid : bool
        True if the matrix is a valid 6x6 symmetric positive-semidefinite matrix.
    reason : str
        Explanation if invalid, or 'Valid' if successful.
    """
    try:
        validate_covariance(cov, rtol=rtol, atol=atol)
        return True, "Valid 6x6 symmetric positive-semidefinite covariance matrix."
    except (ValueError, TypeError) as exc:
        return False, str(exc)


def combine_relative_covariance(
    cov1,
    cov2,
    frame1="ECI",
    frame2="ECI",
    epoch1=None,
    epoch2=None,
    rtol=1e-5,
    atol=1e-8
):
    """
    Calculate relative covariance between two space objects under the
    independent-error assumption. (Technical Guide Section 6.1)

    Equation:
        P_rel = P1 + P2

    Assumptions & Safeguards:
        - The errors in state estimates for Object 1 and Object 2 are statistically independent.
        - Both covariances must be expressed in the identical coordinate frame and epoch.
        - Cross-covariances between objects are assumed to be zero (P12 = P21^T = 0).

    Parameters
    ----------
    cov1 : array-like
        6x6 covariance matrix of Object 1 (Protected Satellite).
    cov2 : array-like
        6x6 covariance matrix of Object 2 (Secondary Object).
    frame1 : str, optional
        Coordinate frame of cov1 (default 'ECI').
    frame2 : str, optional
        Coordinate frame of cov2 (default 'ECI').
    epoch1 : str or float, optional
        Reference epoch for cov1.
    epoch2 : str or float, optional
        Reference epoch for cov2.

    Returns
    -------
    cov_rel : numpy.ndarray
        Combined 6x6 relative covariance matrix in SI units.

    Raises
    ------
    ValueError
        If frames or epochs mismatch, or either covariance matrix is invalid.
    """
    if frame1 != frame2:
        raise ValueError(
            f"Frame mismatch in covariance combination: Frame 1 is '{frame1}', "
            f"Frame 2 is '{frame2}'. Both must refer to the same coordinate frame."
        )

    if epoch1 is not None and epoch2 is not None and epoch1 != epoch2:
        raise ValueError(
            f"Epoch mismatch in covariance combination: Epoch 1 is '{epoch1}', "
            f"Epoch 2 is '{epoch2}'. Covariances must be propagated to the same epoch."
        )

    c1 = validate_covariance(cov1, name="Object 1 Covariance (P1)", rtol=rtol, atol=atol)
    c2 = validate_covariance(cov2, name="Object 2 Covariance (P2)", rtol=rtol, atol=atol)

    # Independent-error assumption: P_rel = P1 + P2
    cov_rel = c1 + c2
    cov_rel = 0.5 * (cov_rel + cov_rel.T)

    return validate_covariance(cov_rel, name="Relative Covariance (P_rel)", rtol=rtol, atol=atol)


def propagate_covariance(cov_0, phi, q=None, rtol=1e-5, atol=1e-8):
    """
    Propagate state covariance using a linear state-transition matrix and process noise.
    (Technical Guide Section 6.1)

    Equation:
        P(t) = Phi(t, t0) * P(t0) * Phi(t, t0)^T + Q

    Where:
        P(t0) : Initial 6x6 covariance matrix.
        Phi   : 6x6 State-Transition Matrix (STM).
        Q     : 6x6 Process-noise / model-error contribution.

    Documented Assumptions:
        1. Linear state-space perturbation dynamics: delta_x(t) = Phi(t, t0) * delta_x(t0) + w(t).
        2. Process noise w(t) has zero mean and covariance Q.
        3. Higher-order nonlinear uncertainty deformation is neglected over the propagation interval.
        4. The caller is responsible for providing a validated STM Phi corresponding to the
           underlying force models.

    Parameters
    ----------
    cov_0 : array-like
        Initial 6x6 covariance matrix at t0.
    phi : array-like
        6x6 State-Transition Matrix (STM) from t0 to t.
    q : array-like, optional
        6x6 process noise covariance matrix Q. If None, Q is assumed zero (6x6 zeros).

    Returns
    -------
    cov_t : numpy.ndarray
        Propagated 6x6 covariance matrix at time t.
    """
    p0 = validate_covariance(cov_0, name="Initial Covariance P(t0)", rtol=rtol, atol=atol)

    phi_arr = np.asarray(phi, dtype=np.float64)
    if phi_arr.shape != (6, 6):
        raise ValueError(f"State-transition matrix (Phi) must be shape (6, 6), got {phi_arr.shape}.")
    if not np.all(np.isfinite(phi_arr)):
        raise ValueError("State-transition matrix (Phi) contains non-finite values.")

    if q is None:
        q_mat = np.zeros((6, 6), dtype=np.float64)
    else:
        q_mat = validate_covariance(q, name="Process Noise Matrix Q", rtol=rtol, atol=atol)

    # Simplified propagation equation: P(t) = Phi * P(t0) * Phi^T + Q
    p_t = phi_arr @ p0 @ phi_arr.T + q_mat
    p_t = 0.5 * (p_t + p_t.T)

    return validate_covariance(p_t, name="Propagated Covariance P(t)", rtol=rtol, atol=atol)


def compute_linear_stm(dt):
    """
    Compute an unperturbed constant-velocity (rectilinear) 6x6 State-Transition Matrix (STM).

    Equation:
        Phi_linear(dt) = [ I_3   dt * I_3 ]
                         [ 0_3     I_3    ]

    CRITICAL APPROXIMATION NOTICE & METHODOLOGY BOUNDARY:
        - This matrix is an idealized, rectilinear (constant-velocity) kinematic approximation.
        - It assumes zero gravitational acceleration gradients (da / dr = 0).
        - It MUST NOT be treated as the general orbital state-transition matrix.
        - For two-body orbital dynamics under Earth gravity, the orbital STM must be obtained
          by integrating the variational equations (dPhi/dt = A(t)*Phi).
          Use 'propagate_orbital_covariance()' or 'propagate_state_and_stm()'.

    Parameters
    ----------
    dt : float
        Time step in seconds.

    Returns
    -------
    phi : numpy.ndarray
        6x6 rectilinear constant-velocity state-transition matrix.
    """
    dt_float = float(dt)
    phi = np.eye(6, dtype=np.float64)
    phi[0, 3] = dt_float
    phi[1, 4] = dt_float
    phi[2, 5] = dt_float
    return phi


def propagate_orbital_covariance(
    initial_state,
    initial_cov,
    duration,
    dt=1.0,
    q=None,
    mu=MU_EARTH,
    rtol=1e-5,
    atol=1e-8
):
    """
    Propagate state covariance consistently with two-body orbital dynamics
    by integrating the variational equations coupled with the RK4 orbit propagator.

    Methodology:
        1. Numerically integrate orbital state x(t) and variational STM Phi(t, t0):
              d Phi / dt = A(t) * Phi,   Phi(t0, t0) = I_6
           where:
              A(t) = [ 0_3   I_3 ]
                     [ G(r)  0_3 ]
              G(r) = mu * (3 * r * r^T / |r|^5 - I_3 / |r|^3)
        2. Propagate state covariance:
              P(t) = Phi(t, t0) * P(t0) * Phi(t, t0)^T + Q

    Process-Noise Handling:
        - If Q is None, it defaults to a 6x6 zeros matrix (Q = 0_{6x6}).
        - If Q is provided, it is validated as a symmetric positive-semidefinite 6x6 matrix.
        - No unmodelled process noise is fabricated.

    Parameters
    ----------
    initial_state : array-like
        Initial 6D orbital state [x, y, z, vx, vy, vz] in SI units.
    initial_cov : array-like
        Initial 6x6 covariance matrix P(t0).
    duration : float
        Propagation duration in seconds.
    dt : float, optional
        Integration time step in seconds (default 1.0 s).
    q : array-like, optional
        6x6 process noise covariance matrix Q (default None -> zero matrix).
    mu : float, optional
        Gravitational parameter (m^3/s^2).

    Returns
    -------
    final_state : numpy.ndarray
        6D orbital state at time t.
    final_cov : numpy.ndarray
        6x6 propagated covariance matrix P(t).
    final_stm : numpy.ndarray
        6x6 orbital state-transition matrix Phi(t, t0).
    """
    # 1. Validate initial covariance
    p0 = validate_covariance(initial_cov, name="Initial Covariance P(t0)", rtol=rtol, atol=atol)

    # 2. Integrate orbital state and STM simultaneously via variational RK4
    final_state, final_stm = propagate_state_and_stm(
        initial_state=initial_state,
        duration=duration,
        dt=dt,
        mu=mu
    )

    # 3. Propagate covariance: P(t) = Phi * P(t0) * Phi^T + Q
    final_cov = propagate_covariance(p0, final_stm, q=q, rtol=rtol, atol=atol)

    return final_state, final_cov, final_stm


def propagate_covariance_to_tca(
    state1_0,
    cov1_0,
    state2_0,
    cov2_0,
    tca,
    dt=1.0,
    q1=None,
    q2=None,
    mu=MU_EARTH,
    frame="ECI",
    epoch_str="2026-01-01T00:00:00Z"
):
    """
    Propagate both space objects' orbital states and covariance matrices to the
    Time of Closest Approach (TCA) using the two-body orbital STM, and compute
    their relative covariance.

    Ensures that the covariance used for subsequent collision probability (Pc)
    assessment is evaluated at the exact same epoch (TCA) and in the exact same
    coordinate frame (ECI) as the relative encounter state.

    Parameters
    ----------
    state1_0 : array-like
        Initial 6D state of Object 1 (Protected Satellite) at t = 0.
    cov1_0 : array-like
        Initial 6x6 covariance of Object 1 at t = 0.
    state2_0 : array-like
        Initial 6D state of Object 2 (Secondary Debris) at t = 0.
    cov2_0 : array-like
        Initial 6x6 covariance of Object 2 at t = 0.
    tca : float
        Time of closest approach in seconds from epoch.
    dt : float, optional
        Integration time step in seconds (default 1.0 s).
    q1 : array-like, optional
        Process noise for Object 1.
    q2 : array-like, optional
        Process noise for Object 2.
    mu : float, optional
        Gravitational parameter.
    frame : str, optional
        Coordinate reference frame (default 'ECI').
    epoch_str : str, optional
        Initial epoch timestamp string.

    Returns
    -------
    result : dict
        Synchronized conjunction encounter uncertainty record containing:
        - 'state1_tca', 'state2_tca': 6D state vectors at TCA.
        - 'cov1_tca', 'cov2_tca': 6x6 individual covariances at TCA.
        - 'cov_rel_tca': 6x6 combined relative covariance at TCA.
        - 'r_rel_tca': 3D relative position vector at TCA.
        - 'v_rel_tca': 3D relative velocity vector at TCA.
        - 'miss_distance': Miss distance in metres.
        - 'relative_speed': Relative encounter speed in m/s.
        - 'phi1', 'phi2': 6x6 orbital STMs for both objects.
        - 'tca': Time of closest approach in seconds.
        - 'frame': Reference frame ('ECI').
        - 'epoch': Reference epoch string.
    """
    tca_float = float(tca)
    if tca_float < 0:
        raise ValueError("TCA must be non-negative.")

    # 1. Propagate Object 1 to TCA
    state1_tca, cov1_tca, phi1 = propagate_orbital_covariance(
        initial_state=state1_0,
        initial_cov=cov1_0,
        duration=tca_float,
        dt=dt,
        q=q1,
        mu=mu
    )

    # 2. Propagate Object 2 to TCA
    state2_tca, cov2_tca, phi2 = propagate_orbital_covariance(
        initial_state=state2_0,
        initial_cov=cov2_0,
        duration=tca_float,
        dt=dt,
        q=q2,
        mu=mu
    )

    # 3. Combine relative covariance at TCA (under independent-error assumption)
    cov_rel_tca = combine_relative_covariance(
        cov1=cov1_tca,
        cov2=cov2_tca,
        frame1=frame,
        frame2=frame
    )

    # 4. Synchronized relative state at TCA
    r_rel_tca = state2_tca[:3] - state1_tca[:3]
    v_rel_tca = state2_tca[3:] - state1_tca[3:]
    miss_dist = float(np.linalg.norm(r_rel_tca))
    rel_spd = float(np.linalg.norm(v_rel_tca))

    return {
        "state1_tca": state1_tca,
        "state2_tca": state2_tca,
        "cov1_tca": cov1_tca,
        "cov2_tca": cov2_tca,
        "cov_rel_tca": cov_rel_tca,
        "r_rel_tca": r_rel_tca,
        "v_rel_tca": v_rel_tca,
        "miss_distance": miss_dist,
        "relative_speed": rel_spd,
        "phi1": phi1,
        "phi2": phi2,
        "tca": tca_float,
        "frame": str(frame),
        "epoch": str(epoch_str),
    }


def create_diagonal_covariance(pos_std_m, vel_std_mps):
    """
    Create a diagonal 6x6 covariance matrix from position and velocity standard deviations.

    Parameters
    ----------
    pos_std_m : float or array-like of 3 floats
        Standard deviation in position (metres). Scalar applies equally to x, y, z.
    vel_std_mps : float or array-like of 3 floats
        Standard deviation in velocity (metres/second). Scalar applies equally to vx, vy, vz.

    Returns
    -------
    cov : numpy.ndarray
        Valid 6x6 diagonal covariance matrix.
    """
    if np.isscalar(pos_std_m):
        sigma_pos = np.full(3, float(pos_std_m), dtype=np.float64)
    else:
        sigma_pos = np.asarray(pos_std_m, dtype=np.float64)
        if sigma_pos.shape != (3,):
            raise ValueError("Position std must have 3 elements [sigma_x, sigma_y, sigma_z].")

    if np.isscalar(vel_std_mps):
        sigma_vel = np.full(3, float(vel_std_mps), dtype=np.float64)
    else:
        sigma_vel = np.asarray(vel_std_mps, dtype=np.float64)
        if sigma_vel.shape != (3,):
            raise ValueError("Velocity std must have 3 elements [sigma_vx, sigma_vy, sigma_vz].")

    if np.any(sigma_pos < 0.0) or np.any(sigma_vel < 0.0):
        raise ValueError("Standard deviations must be strictly non-negative.")

    diag_elements = np.concatenate((sigma_pos**2, sigma_vel**2))
    return np.diag(diag_elements)

