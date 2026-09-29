import numpy as np


# =========================================================
# PROTOTYPE THRESHOLDS
# =========================================================

SAFE_DISTANCE_KM = 100.0
CLOSE_APPROACH_KM = 10.0


def calculate_encounter_metrics(
    position_a,
    velocity_a,
    position_b,
    velocity_b
):
    """
    Calculate relative-motion and encounter parameters.

    Parameters
    ----------
    position_a : array-like
        Position of object A in km.

    velocity_a : array-like
        Velocity of object A in km/s.

    position_b : array-like
        Position of object B in km.

    velocity_b : array-like
        Velocity of object B in km/s.

    Returns
    -------
    dict
        Encounter metrics.
    """

    position_a = np.asarray(position_a, dtype=float)
    velocity_a = np.asarray(velocity_a, dtype=float)

    position_b = np.asarray(position_b, dtype=float)
    velocity_b = np.asarray(velocity_b, dtype=float)

    # -----------------------------------------------------
    # Relative vectors
    # -----------------------------------------------------

    relative_position = position_a - position_b
    relative_velocity = velocity_a - velocity_b

    # -----------------------------------------------------
    # Distance
    # -----------------------------------------------------

    distance_km = np.linalg.norm(relative_position)

    # -----------------------------------------------------
    # Relative speed
    # -----------------------------------------------------

    relative_speed_km_s = np.linalg.norm(
        relative_velocity
    )

    # -----------------------------------------------------
    # Closing speed
    # -----------------------------------------------------

    if distance_km > 0:

        closing_speed_km_s = -np.dot(
            relative_position,
            relative_velocity
        ) / distance_km

    else:

        closing_speed_km_s = 0.0

    # -----------------------------------------------------
    # Approach angle
    # -----------------------------------------------------

    if (
        distance_km > 0
        and relative_speed_km_s > 0
    ):

        cosine_angle = np.dot(
            relative_position,
            relative_velocity
        ) / (
            distance_km
            * relative_speed_km_s
        )

        cosine_angle = np.clip(
            cosine_angle,
            -1.0,
            1.0
        )

        approach_angle_deg = np.degrees(
            np.arccos(cosine_angle)
        )

    else:

        approach_angle_deg = 0.0

    # -----------------------------------------------------
    # Prototype status
    # -----------------------------------------------------

    if distance_km < CLOSE_APPROACH_KM:

        status = "CLOSE APPROACH"
        level = "HIGH"

    elif distance_km < SAFE_DISTANCE_KM:

        status = "MONITOR"
        level = "MEDIUM"

    else:

        status = "SAFE"
        level = "LOW"

    return {
        "distance_km": distance_km,
        "relative_speed_km_s": relative_speed_km_s,
        "closing_speed_km_s": closing_speed_km_s,
        "approach_angle_deg": approach_angle_deg,
        "relative_position_km": relative_position,
        "relative_velocity_km_s": relative_velocity,
        "status": status,
        "level": level
    }


# =========================================================
# TEST
# =========================================================

if __name__ == "__main__":

    # Simple controlled test
    position_a = np.array([1000.0, 7000.0, 0.0])
    position_b = np.array([1005.0, 7000.0, 0.0])

    velocity_a = np.array([5.0, 0.0, 0.0])
    velocity_b = np.array([-5.0, 0.0, 0.0])

    result = calculate_encounter_metrics(
        position_a,
        velocity_a,
        position_b,
        velocity_b
    )

    print("\nANALYSIS ENGINE TEST")
    print("=" * 50)

    print(
        f"Distance: "
        f"{result['distance_km']:.2f} km"
    )

    print(
        f"Relative speed: "
        f"{result['relative_speed_km_s']:.2f} km/s"
    )

    print(
        f"Closing speed: "
        f"{result['closing_speed_km_s']:.2f} km/s"
    )

    print(
        f"Approach angle: "
        f"{result['approach_angle_deg']:.2f} degrees"
    )

    print(
        f"Status: "
        f"{result['status']} [{result['level']}]"
    )