"""
D2/uncertainty/collision_probability.py
=======================================
Collision Probability (Pc) and Encounter Plane Projection Module for Deliverable 2 (D2),
strictly following Section 6 of the Satellite Anti-Collision Technical Guide.

Core Methodologies & Standards (Technical Guide Section 6.2 & 6.3):
1. Encounter-Plane (B-Plane) Projection:
   - Project 3D relative position and 3x3 position covariance onto a 2D plane
     perpendicular to the relative velocity vector at Time of Closest Approach (TCA).
2. Combined Hard-Body Collision Geometry:
   - Hard-body radius R = R1 + R2 represents the combined collision envelope.
3. 2D Gaussian Probability Integration (Foster 1992 / NASA CARA formulation):
   - Diagonalize 2D encounter covariance to principal uncertainty axes.
   - Analytical reduction of inner radial integral using error functions (erf),
     followed by 1D polar integration.
4. Safeguards & Interface Contracts:
   - Missing covariance does NOT assume zero uncertainty; Pc is marked UNAVAILABLE.
   - Simplified risk proxies are clearly distinguished from formal collision probability.
   - Non-positive-semidefinite or degenerate covariances are caught and flagged.

Conventions & Units:
- Reference Frame : Earth-Centred Inertial (ECI)
- Distances       : Metres (m)
- Velocities      : Metres per second (m/s)
- Covariance      : Metres squared (m^2)
- Probability     : Dimensionless ([0.0, 1.0])
"""

import numpy as np
from scipy import special

from D2.uncertainty.covariance import validate_covariance


def project_to_encounter_plane(r_rel, v_rel, cov_rel=None, tol=1e-12):
    """
    Project 3D relative state and position covariance onto the 2D encounter plane
    perpendicular to relative encounter velocity. (Technical Guide Section 6.2)

    Encounter Frame Definition:
        - z_axis (e_z) : Unit vector aligned with relative velocity (v_rel / |v_rel|).
        - x_axis (e_x) : Unit vector in the encounter plane along the in-plane relative position.
        - y_axis (e_y) : Completes the right-handed orthonormal triad (e_z x e_x).

    Parameters
    ----------
    r_rel : array-like
        3D relative position vector [rx, ry, rz] at TCA in metres.
    v_rel : array-like
        3D relative velocity vector [vx, vy, vz] at TCA in metres/second.
    cov_rel : array-like, optional
        6x6 relative covariance matrix. If provided, the 3x3 position submatrix
        is projected onto the 2D encounter plane.
    tol : float, optional
        Velocity squared magnitude tolerance to detect degenerate velocity.

    Returns
    -------
    result : dict
        Encounter plane projection dictionary containing:
        - 'mu_2d': 2D projected relative position [x_e, y_e] in metres.
        - 'miss_distance_2d': Magnitude of 2D relative position in metres.
        - 'cov_2d': 2x2 projected covariance matrix in m^2 (or None if cov_rel is None).
        - 'basis': Orthonormal triad dict {'e_x': e_x, 'e_y': e_y, 'e_z': e_z}.
        - 'projection_matrix': 2x3 projection matrix M.
        - 'is_degenerate': Boolean indicating if encounter velocity was degenerate.
    """
    r_vec = np.asarray(r_rel, dtype=np.float64)
    v_vec = np.asarray(v_rel, dtype=np.float64)

    if r_vec.shape != (3,) or v_vec.shape != (3,):
        raise ValueError("r_rel and v_rel must be 3-element vectors.")

    v_sq = float(np.dot(v_vec, v_vec))
    if v_sq <= tol:
        # Relative velocity is zero/degenerate; encounter plane is undefined
        return {
            "mu_2d": None,
            "miss_distance_2d": float(np.linalg.norm(r_vec)),
            "cov_2d": None,
            "basis": None,
            "projection_matrix": None,
            "is_degenerate": True,
        }

    # 1. Encounter normal unit vector along relative velocity
    e_z = v_vec / np.sqrt(v_sq)

    # 2. In-plane component of relative position
    r_in_plane = r_vec - np.dot(r_vec, e_z) * e_z
    norm_in_plane = float(np.linalg.norm(r_in_plane))

    if norm_in_plane > 1e-9:
        e_x = r_in_plane / norm_in_plane
    else:
        # Head-on collinear geometry: construct an arbitrary orthogonal vector
        if abs(e_z[0]) < 0.9:
            ref_vec = np.array([1.0, 0.0, 0.0], dtype=np.float64)
        else:
            ref_vec = np.array([0.0, 1.0, 0.0], dtype=np.float64)
        e_x = ref_vec - np.dot(ref_vec, e_z) * e_z
        e_x = e_x / np.linalg.norm(e_x)

    e_y = np.cross(e_z, e_x)
    e_y = e_y / np.linalg.norm(e_y)

    # 3. 2x3 projection matrix M: projects from 3D ECI to 2D encounter plane
    m_proj = np.vstack((e_x, e_y))  # Shape (2, 3)

    # 4. Project relative position onto encounter plane
    mu_2d = m_proj @ r_vec
    miss_2d = float(np.linalg.norm(mu_2d))

    # 5. Project 3x3 position covariance onto encounter plane (if provided)
    cov_2d = None
    if cov_rel is not None:
        cov_valid = validate_covariance(cov_rel, name="Relative Covariance")
        cov_pos_3d = cov_valid[:3, :3]  # Extract 3x3 position covariance block
        cov_2d = m_proj @ cov_pos_3d @ m_proj.T
        cov_2d = 0.5 * (cov_2d + cov_2d.T)

    return {
        "mu_2d": mu_2d,
        "miss_distance_2d": miss_2d,
        "cov_2d": cov_2d,
        "basis": {"e_x": e_x, "e_y": e_y, "e_z": e_z},
        "projection_matrix": m_proj,
        "is_degenerate": False,
    }


def _integrate_2d_gaussian_circle(x0, y0, sigma_x, sigma_y, radius, n_theta=360):
    r"""
    Integrate a 2D zero-correlation Gaussian distribution over a circular disc
    of radius R centered at the origin using Foster's analytical radial reduction.

    Equation:
        f(x, y) = 1/(2*pi*sigma_x*sigma_y) * exp(-(x - x0)^2/(2*sigma_x^2) - (y - y0)^2/(2*sigma_y^2))
        Pc = \iint_{x^2 + y^2 <= R^2} f(x, y) dx dy

    Parameters
    ----------
    x0, y0 : float
        Mean position coordinates in principal axis frame.
    sigma_x, sigma_y : float
        Principal standard deviations (must be strictly positive).
    radius : float
        Combined hard-body radius R in metres.
    n_theta : int, optional
        Number of angular integration steps in [0, 2*pi] (default 360).

    Returns
    -------
    pc : float
        Integrated collision probability in range [0.0, 1.0].
    """
    if radius <= 0.0:
        return 0.0

    theta = np.linspace(0, 2 * np.pi, n_theta, endpoint=False)
    cos_t = np.cos(theta)
    sin_t = np.sin(theta)

    a_coeff = (cos_t**2 / (2.0 * sigma_x**2)) + (sin_t**2 / (2.0 * sigma_y**2))
    b_coeff = (x0 * cos_t / sigma_x**2) + (y0 * sin_t / sigma_y**2)
    c_coeff = (x0**2 / (2.0 * sigma_x**2)) + (y0**2 / (2.0 * sigma_y**2))

    sqrt_a = np.sqrt(a_coeff)
    u0 = -b_coeff / (2.0 * sqrt_a)
    u1 = sqrt_a * radius - b_coeff / (2.0 * sqrt_a)

    # Exponent argument shift: B^2 / (4A) - C
    arg_exp = (b_coeff**2 / (4.0 * a_coeff)) - c_coeff
    exp_factor = np.exp(arg_exp)

    # Inner analytical radial integral
    term1 = -0.5 / a_coeff * (np.exp(-u1**2) - np.exp(-u0**2))
    term2 = (b_coeff * np.sqrt(np.pi) / (4.0 * a_coeff**1.5)) * (special.erf(u1) - special.erf(u0))

    inner_integrand = exp_factor * (term1 + term2)

    # 1D numerical quadrature over periodic interval [0, 2*pi)
    dtheta = 2.0 * np.pi / n_theta
    integral_sum = np.sum(inner_integrand) * dtheta

    pc = float(integral_sum / (2.0 * np.pi * sigma_x * sigma_y))
    return float(np.clip(pc, 0.0, 1.0))


def calculate_collision_probability(
    r_rel_tca,
    v_rel_tca,
    cov_rel_tca,
    hard_body_radius,
    method="foster_1d",
    n_theta=360
):
    """
    Calculate Probability of Collision (Pc) using the 2D encounter-plane method.
    (Technical Guide Section 6.2)

    Inputs (Technical Guide Section 6.2):
        - Relative state at TCA (r_rel, v_rel).
        - Relative covariance at TCA (cov_rel_tca).
        - Combined hard-body radius (hard_body_radius = R1 + R2).
        - Selected probability method.

    Outputs (Technical Guide Section 6.2):
        - Pc, method name, assumptions, numerical status and quality flags.

    Safeguards:
        - If cov_rel_tca is None, does NOT assume zero uncertainty.
          Sets Pc = None, status = 'COVARIANCE_MISSING', and provides a labeled risk proxy.
        - If relative velocity is near-zero, sets Pc = None, status = 'DEGENERATE_VELOCITY'.

    Parameters
    ----------
    r_rel_tca : array-like
        3D relative position vector at TCA in metres.
    v_rel_tca : array-like
        3D relative velocity vector at TCA in metres/second.
    cov_rel_tca : array-like or None
        6x6 relative covariance matrix at TCA in SI units.
    hard_body_radius : float
        Combined physical collision radius (R1 + R2) in metres.
    method : str, optional
        Computation method (default 'foster_1d').
    n_theta : int, optional
        Number of integration steps for 1D angular quadrature (default 360).

    Returns
    -------
    result : dict
        Standardized collision probability result dictionary.
    """
    hbr = float(hard_body_radius)
    if hbr < 0.0:
        raise ValueError("Combined hard-body radius must be non-negative.")

    # Compute consequence indicators (Technical Guide Section 6.3)
    v_norm = float(np.linalg.norm(v_rel_tca))
    rel_ke = 0.5 * v_norm**2
    if v_norm < 1000.0:
        conseq_cat = "LOW_VELOCITY"
    elif v_norm < 10000.0:
        conseq_cat = "HYPERVELOCITY"
    else:
        conseq_cat = "EXTREME_HYPERVELOCITY"
    consequence_indicators = {
        "relative_speed_mps": v_norm,
        "relative_kinetic_energy_J_per_kg": rel_ke,
        "consequence_category": conseq_cat,
    }

    # 1. Safeguard: Handle missing covariance explicitly without fabricating zero uncertainty
    if cov_rel_tca is None:
        risk_proxy = calculate_simplified_risk_proxy(
            miss_distance=float(np.linalg.norm(r_rel_tca)),
            hard_body_radius=hbr,
            relative_speed=v_norm,
        )
        return {
            "pc": None,
            "log10_pc": None,
            "ln_pc": None,
            "mahalanobis_distance": None,
            "method": "UNAVAILABLE",
            "status": "COVARIANCE_MISSING",
            "is_valid": False,
            "combined_hard_body_radius_m": hbr,
            "miss_distance_m": float(np.linalg.norm(r_rel_tca)),
            "encounter_plane_metrics": None,
            "risk_proxy": risk_proxy,
            "consequence_indicators": consequence_indicators,
            "quality_flags": ["COVARIANCE_MISSING", "PC_NOT_COMPUTABLE"],
            "assumptions": (
                "Covariance data was not provided. In accordance with Section 6.2 of the "
                "Technical Guide, missing covariance is NOT treated as zero uncertainty, "
                "and Pc is marked as unavailable."
            ),
        }

    # 2. Project relative state and covariance onto 2D encounter plane
    proj = project_to_encounter_plane(r_rel_tca, v_rel_tca, cov_rel=cov_rel_tca)

    if proj["is_degenerate"]:
        return {
            "pc": None,
            "log10_pc": None,
            "ln_pc": None,
            "mahalanobis_distance": None,
            "method": "UNAVAILABLE",
            "status": "DEGENERATE_VELOCITY",
            "is_valid": False,
            "combined_hard_body_radius_m": hbr,
            "miss_distance_m": proj["miss_distance_2d"],
            "encounter_plane_metrics": None,
            "quality_flags": ["DEGENERATE_VELOCITY", "ENCOUNTER_PLANE_UNDEFINED"],
            "assumptions": "Relative encounter velocity is zero; 2D encounter plane is undefined.",
        }

    mu_2d = proj["mu_2d"]
    cov_2d = proj["cov_2d"]
    miss_distance = proj["miss_distance_2d"]

    # 3. Trivial geometry check
    d_m2 = None
    mahalanobis_dist = None
    if cov_2d is not None and not proj["is_degenerate"]:
        # Pre-calculate Mahalanobis distance if covariance available
        pass

    if hbr == 0.0:
        return {
            "pc": 0.0,
            "log10_pc": -float("inf"),
            "ln_pc": -float("inf"),
            "mahalanobis_distance": 0.0,
            "method": "ANALYTICAL_ZERO_RADIUS",
            "status": "COMPUTED",
            "is_valid": True,
            "combined_hard_body_radius_m": 0.0,
            "miss_distance_m": miss_distance,
            "encounter_plane_metrics": {"mu_2d": mu_2d, "cov_2d": cov_2d},
            "quality_flags": ["ZERO_HARD_BODY_RADIUS"],
            "assumptions": "Combined hard body radius is zero; collision probability is identically zero.",
        }

    # 4. Diagonalize 2D encounter covariance to principal axes
    #    cov_2d = V @ diag(sigma_x^2, sigma_y^2) @ V^T
    eigvals, eigvecs = np.linalg.eigh(cov_2d)

    min_eig = float(np.min(eigvals))
    if min_eig < -1e-9:
        return {
            "pc": None,
            "log10_pc": None,
            "ln_pc": None,
            "mahalanobis_distance": None,
            "method": "UNAVAILABLE",
            "status": "NON_POSITIVE_DEFINITE_COVARIANCE",
            "is_valid": False,
            "combined_hard_body_radius_m": hbr,
            "miss_distance_m": miss_distance,
            "encounter_plane_metrics": {"cov_2d": cov_2d, "eigenvalues": eigvals},
            "quality_flags": ["NEGATIVE_COVARIANCE_EIGENVALUE"],
            "assumptions": "Encounter covariance matrix has significant negative eigenvalues.",
        }

    # Floor small numerical eigenvalues to positive machine precision
    eigvals = np.maximum(eigvals, 1e-12)
    sigma_x = float(np.sqrt(eigvals[1]))  # Major semi-axis
    sigma_y = float(np.sqrt(eigvals[0]))  # Minor semi-axis

    # Transform 2D mean to principal uncertainty frame: mu_principal = V^T @ mu_2d
    mu_principal = eigvecs.T @ mu_2d
    x0 = float(mu_principal[1])
    y0 = float(mu_principal[0])

    # 5. Mahalanobis distance and asymptotic small-body log probability
    d_m2 = (x0**2 / sigma_x**2) + (y0**2 / sigma_y**2)
    mahalanobis_dist = float(np.sqrt(d_m2))

    log_area_norm = np.log(hbr**2 / (2.0 * sigma_x * sigma_y))
    ln_pc_asymp = float(log_area_norm - 0.5 * d_m2)
    log10_pc = float(ln_pc_asymp / np.log(10.0))

    # 6. Integrate 2D Gaussian over collision circle via Foster 1D quadrature
    pc_foster = _integrate_2d_gaussian_circle(
        x0=x0,
        y0=y0,
        sigma_x=sigma_x,
        sigma_y=sigma_y,
        radius=hbr,
        n_theta=n_theta
    )

    # Detect numerical underflow / erf machine resolution limit:
    # Foster integration fails for |u| > ~5.5 (where erf(u) reaches +/-1 in float64)
    is_underflow = False
    if pc_foster <= 1e-16 or mahalanobis_dist > 5.5:
        is_underflow = True
        if ln_pc_asymp < -708.0:
            pc_val = 0.0  # Underflow below IEEE 754 subnormal range
        else:
            pc_val = float(np.exp(ln_pc_asymp))
    else:
        pc_val = pc_foster
        log10_pc = float(np.log10(max(pc_val, 1e-300)))

    quality_flags = ["VALID_COVARIANCE", "COVARIANCE_PROJECTED", "FOSTER_1D_INTEGRATION"]
    if miss_distance > 5.0 * max(sigma_x, sigma_y):
        quality_flags.append("LARGE_MISS_DISTANCE")

    if is_underflow:
        status = "NUMERICAL_UNDERFLOW"
        quality_flags.append("FLOAT64_INTEGRATION_UNDERFLOW")
        quality_flags.append("TAIL_ASYMPTOTIC_LOGPC")
        method_str = f"foster_1d_encounter_plane (tail_asymptotic, n_theta={n_theta})"
    else:
        status = "COMPUTED"
        quality_flags.append("PSD_VALID")
        method_str = f"foster_1d_encounter_plane (n_theta={n_theta})"

    return {
        "pc": pc_val,
        "log10_pc": log10_pc,
        "ln_pc": ln_pc_asymp,
        "mahalanobis_distance": mahalanobis_dist,
        "method": method_str,
        "status": status,
        "is_valid": True,
        "combined_hard_body_radius_m": hbr,
        "miss_distance_m": miss_distance,
        "encounter_plane_metrics": {
            "mu_2d": mu_2d,
            "cov_2d": cov_2d,
            "principal_sigmas": (sigma_x, sigma_y),
            "principal_mean": (x0, y0),
            "semi_major_axis_sigma_m": sigma_x,
            "semi_minor_axis_sigma_m": sigma_y,
            "mahalanobis_distance": mahalanobis_dist,
        },
        "consequence_indicators": consequence_indicators,
        "quality_flags": quality_flags,
        "assumptions": (
            "Encounter duration is short relative to orbital period; rectilinear relative motion; "
            "independent zero-mean Gaussian uncertainty; spherical hard-body collision geometry."
            + (" Tail asymptotic representation used due to float64 integration underflow." if is_underflow else "")
        ),
    }


def calculate_simplified_risk_proxy(miss_distance, hard_body_radius, relative_speed=None):
    """
    Calculate a simplified, clearly-labeled geometric proximity proxy when formal
    covariance is unavailable. (Technical Guide Section 6.2 & 6.3)

    Important Architectural Principle:
        This is a deterministic proximity ratio and screening metric, NOT a collision
        probability (Pc). It does not substitute for state uncertainty.

    Parameters
    ----------
    miss_distance : float
        Closest approach distance in metres.
    hard_body_radius : float
        Combined hard-body radius in metres.
    relative_speed : float, optional
        Relative encounter speed in metres/second.

    Returns
    -------
    proxy : dict
        Dictionary containing proximity metrics, clearly marked as non-probabilistic.
    """
    d = max(0.0, float(miss_distance))
    r = max(0.0, float(hard_body_radius))

    # Proximity ratio: R / d (infinite if d=0, bounded safely)
    denom = max(d, 1e-6)
    ratio = r / denom

    consequence_indicators = None
    if relative_speed is not None:
        v_s = float(relative_speed)
        consequence_indicators = {
            "relative_speed_mps": v_s,
            "relative_kinetic_energy_J_per_kg": 0.5 * v_s**2,
            "consequence_category": "LOW_VELOCITY" if v_s < 1000.0 else ("HYPERVELOCITY" if v_s < 10000.0 else "EXTREME_HYPERVELOCITY"),
        }

    return {
        "metric_type": "GEOMETRIC_PROXIMITY_PROXY",
        "is_probability": False,
        "proximity_ratio": float(ratio),
        "hard_body_overlap": bool(d <= r),
        "miss_distance_m": d,
        "hard_body_radius_m": r,
        "relative_speed_mps": float(relative_speed) if relative_speed is not None else None,
        "consequence_indicators": consequence_indicators,
        "quality_flags": ["GEOMETRIC_FALLBACK", "NO_COVARIANCE"],
        "disclaimer": (
            "This metric is a deterministic geometric proximity score, NOT a probability of "
            "collision (Pc). It cannot be interpreted as likelihood without state covariance."
        ),
    }


def calculate_max_collision_probability(miss_distance, hard_body_radius):
    """
    Calculate the analytical maximum possible collision probability (Max Pc)
    over all possible isotropic covariance scales. (Akella & Alfriend 2000)

    Equation:
        Pc_max = (R^2 / d^2) * exp(-1/2) for d >= R * sqrt(2)
        Pc_max = 1 - exp(-R^2 / (2 * sigma_opt^2))

    Useful as a conservative upper bound when uncertainty magnitude is unknown.

    Parameters
    ----------
    miss_distance : float
        Miss distance in metres.
    hard_body_radius : float
        Combined hard-body radius in metres.

    Returns
    -------
    max_pc : float
        Conservative upper bound on collision probability.
    """
    d = max(0.0, float(miss_distance))
    r = max(0.0, float(hard_body_radius))

    if r <= 0.0:
        return 0.0
    if d <= r:
        return 1.0

    # Optimal isotropic variance sigma^2 that maximizes Pc for a given d
    sigma_opt_sq = d**2 / 2.0
    max_pc = (r**2 / (2.0 * sigma_opt_sq)) * np.exp(-0.5)
    return float(np.clip(max_pc, 0.0, 1.0))
