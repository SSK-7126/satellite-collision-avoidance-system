import numpy as np
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation


# =========================================================
# SYNTHETIC TEST SCENARIO
# =========================================================

SIMULATION_SPEED = 5
UPDATE_INTERVAL = 100

SAFE_DISTANCE_KM = 100.0
CLOSE_APPROACH_KM = 10.0


# =========================================================
# INITIAL CONDITIONS
# =========================================================

satellite_initial = np.array([
    -1000.0,
    7000.0
])

debris_initial = np.array([
    1000.0,
    7005.0
])

satellite_velocity = np.array([
    5.0,
    0.0
])

debris_velocity = np.array([
    -5.0,
    0.0
])


# =========================================================
# SIMULATION STATE
# =========================================================

simulation_seconds = 0.0

minimum_distance = float("inf")
minimum_time = 0.0

close_approach_detected = False
close_approach_time = None


# =========================================================
# FIGURE
# =========================================================

fig, ax = plt.subplots(figsize=(10, 8))

fig.canvas.manager.set_window_title(
    "Satellite Collision Avoidance — Synthetic Test"
)

ax.set_title(
    "Satellite Collision Avoidance — CONTROLLED TEST",
    fontsize=14
)

ax.set_xlabel("X Position (km)")
ax.set_ylabel("Y Position (km)")

ax.set_aspect("equal")


# =========================================================
# EARTH
# =========================================================

earth = plt.Circle(
    (0, 0),
    6371,
    fill=True,
    alpha=0.15
)

ax.add_patch(earth)


# =========================================================
# OBJECTS
# =========================================================

satellite_point, = ax.plot(
    [],
    [],
    marker="o",
    markersize=9,
    label="TEST SATELLITE"
)

debris_point, = ax.plot(
    [],
    [],
    marker="o",
    markersize=9,
    label="TEST DEBRIS"
)

satellite_trail, = ax.plot(
    [],
    [],
    linewidth=1
)

debris_trail, = ax.plot(
    [],
    [],
    linewidth=1
)

ax.legend(loc="upper right")


# =========================================================
# INFORMATION
# =========================================================

info_text = ax.text(
    0.02,
    0.98,
    "",
    transform=ax.transAxes,
    verticalalignment="top",
    fontsize=10
)

status_text = ax.text(
    0.5,
    0.03,
    "",
    transform=ax.transAxes,
    horizontalalignment="center",
    fontsize=14,
    fontweight="bold"
)


# =========================================================
# TRAILS
# =========================================================

satellite_x = []
satellite_y = []

debris_x = []
debris_y = []


# =========================================================
# VIEW
# =========================================================

ax.set_xlim(-8000, 8000)
ax.set_ylim(-8000, 8000)


# =========================================================
# UPDATE
# =========================================================

def update(frame):

    global simulation_seconds
    global minimum_distance
    global minimum_time
    global close_approach_detected
    global close_approach_time

    # Advance simulation
    simulation_seconds += SIMULATION_SPEED

    # -----------------------------------------------------
    # OBJECT POSITIONS
    # -----------------------------------------------------

    satellite_position = (
        satellite_initial
        + satellite_velocity * simulation_seconds
    )

    debris_position = (
        debris_initial
        + debris_velocity * simulation_seconds
    )

    # -----------------------------------------------------
    # TRAILS
    # -----------------------------------------------------

    satellite_x.append(satellite_position[0])
    satellite_y.append(satellite_position[1])

    debris_x.append(debris_position[0])
    debris_y.append(debris_position[1])

    max_trail = 250

    if len(satellite_x) > max_trail:
        satellite_x.pop(0)
        satellite_y.pop(0)

    if len(debris_x) > max_trail:
        debris_x.pop(0)
        debris_y.pop(0)

    # -----------------------------------------------------
    # UPDATE OBJECTS
    # -----------------------------------------------------

    satellite_point.set_data(
        [satellite_position[0]],
        [satellite_position[1]]
    )

    debris_point.set_data(
        [debris_position[0]],
        [debris_position[1]]
    )

    satellite_trail.set_data(
        satellite_x,
        satellite_y
    )

    debris_trail.set_data(
        debris_x,
        debris_y
    )

    # -----------------------------------------------------
    # RELATIVE MOTION
    # -----------------------------------------------------

    relative_position = (
        satellite_position - debris_position
    )

    relative_velocity = (
        satellite_velocity - debris_velocity
    )

    distance = np.linalg.norm(
        relative_position
    )

    relative_speed = np.linalg.norm(
        relative_velocity
    )

    closing_speed = -np.dot(
        relative_position,
        relative_velocity
    ) / distance

    # -----------------------------------------------------
    # MINIMUM DISTANCE
    # -----------------------------------------------------

    if distance < minimum_distance:

        minimum_distance = distance
        minimum_time = simulation_seconds

    # -----------------------------------------------------
    # DETECT CLOSE APPROACH
    # -----------------------------------------------------

    if (
        distance <= CLOSE_APPROACH_KM
        and not close_approach_detected
    ):

        close_approach_detected = True
        close_approach_time = simulation_seconds

    # -----------------------------------------------------
    # CURRENT STATUS
    # -----------------------------------------------------

    if distance < CLOSE_APPROACH_KM:

        current_status = "CLOSE APPROACH"
        current_level = "HIGH"

    elif distance < SAFE_DISTANCE_KM:

        current_status = "MONITOR"
        current_level = "MEDIUM"

    else:

        current_status = "SAFE"
        current_level = "LOW"

    # -----------------------------------------------------
    # EVENT MESSAGE
    # -----------------------------------------------------

    if close_approach_detected:

        event_message = (
            "\n⚠ CLOSE APPROACH DETECTED"
            f"\nMinimum distance: {minimum_distance:.2f} km"
            f"\nTime of closest approach: "
            f"{minimum_time:.0f} s"
        )

    else:

        event_message = (
            "\nNo close approach detected yet."
        )

    # -----------------------------------------------------
    # INFORMATION PANEL
    # -----------------------------------------------------

    info_text.set_text(
        f"TEST MODE — SYNTHETIC SCENARIO\n\n"

        f"Simulation Time:\n"
        f"{simulation_seconds:.0f} s\n\n"

        f"ENCOUNTER\n"
        f"Distance: {distance:.2f} km\n"
        f"Relative speed: {relative_speed:.2f} km/s\n"
        f"Closing speed: {closing_speed:.2f} km/s\n\n"

        f"MINIMUM OBSERVED\n"
        f"{minimum_distance:.2f} km\n"
        f"At: {minimum_time:.0f} s\n\n"

        f"THRESHOLDS\n"
        f"Safe: > {SAFE_DISTANCE_KM:.0f} km\n"
        f"Monitor: {CLOSE_APPROACH_KM:.0f}–"
        f"{SAFE_DISTANCE_KM:.0f} km\n"
        f"Close: < {CLOSE_APPROACH_KM:.0f} km"
        f"{event_message}"
    )

    # -----------------------------------------------------
    # STATUS
    # -----------------------------------------------------

    if close_approach_detected:

        status_text.set_text(
            f"STATUS: {current_status} [{current_level}]"
            "\n⚠ ENCOUNTER EVENT RECORDED"
        )

    else:

        status_text.set_text(
            f"STATUS: {current_status} [{current_level}]"
        )

    return (
        satellite_point,
        debris_point,
        satellite_trail,
        debris_trail,
        info_text,
        status_text
    )


# =========================================================
# START
# =========================================================

if __name__ == "__main__":
    animation = FuncAnimation(
        fig,
        update,
        interval=UPDATE_INTERVAL,
        blit=False
    )

    plt.show()
