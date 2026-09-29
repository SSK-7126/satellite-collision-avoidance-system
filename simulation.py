import numpy as np
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
from sgp4.api import Satrec, jday, days2mdhms
from datetime import datetime, timedelta, timezone

from data_loader import load_tle_data


# =========================================================
# SIMULATION SETTINGS
# =========================================================

SIMULATION_SPEED = 60
UPDATE_INTERVAL = 100

# Demonstration thresholds
SAFE_DISTANCE_KM = 100.0
CLOSE_APPROACH_KM = 10.0


# =========================================================
# LOAD ORBITAL DATA
# =========================================================

objects = load_tle_data("data/orbital_data.txt")

satellites = {}

for obj in objects:
    satellites[obj["name"]] = Satrec.twoline2rv(
        obj["line1"],
        obj["line2"]
    )


# =========================================================
# START TIME
# =========================================================

cartosat = satellites["CARTOSAT-3"]

month, day, hour, minute, second = days2mdhms(
    cartosat.epochyr + 2000,
    cartosat.epochdays
)

start_time = datetime(
    cartosat.epochyr + 2000,
    month,
    day,
    hour,
    minute,
    int(second),
    tzinfo=timezone.utc
)

simulation_time = start_time


# =========================================================
# SGP4
# =========================================================

def get_state(satellite, time):

    jd, fr = jday(
        time.year,
        time.month,
        time.day,
        time.hour,
        time.minute,
        time.second +
        time.microsecond / 1_000_000
    )

    error, position, velocity = satellite.sgp4(jd, fr)

    if error != 0:
        raise RuntimeError(
            f"SGP4 error code: {error}"
        )

    return np.array(position), np.array(velocity)


# =========================================================
# FIGURE
# =========================================================

fig, ax = plt.subplots(figsize=(10, 8))

fig.canvas.manager.set_window_title(
    "Satellite Collision Avoidance System"
)

ax.set_title(
    "Satellite Collision Avoidance — Live Simulation",
    fontsize=15
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
    alpha=0.25
)

ax.add_patch(earth)


# =========================================================
# OBJECTS
# =========================================================

cartosat_point, = ax.plot(
    [],
    [],
    marker="o",
    markersize=9,
    label="CARTOSAT-3"
)

pslv_point, = ax.plot(
    [],
    [],
    marker="o",
    markersize=9,
    label="PSLV R/B"
)


cartosat_trail, = ax.plot(
    [],
    [],
    linewidth=1
)

pslv_trail, = ax.plot(
    [],
    [],
    linewidth=1
)


ax.legend(loc="upper right")


# =========================================================
# INFORMATION PANEL
# =========================================================

info_text = ax.text(
    0.02,
    0.98,
    "",
    transform=ax.transAxes,
    verticalalignment="top",
    fontsize=10
)


# =========================================================
# STATUS DISPLAY
# =========================================================

status_text = ax.text(
    0.5,
    0.03,
    "",
    transform=ax.transAxes,
    horizontalalignment="center",
    fontsize=13,
    fontweight="bold"
)


# =========================================================
# TRAILS
# =========================================================

cartosat_x = []
cartosat_y = []

pslv_x = []
pslv_y = []

MAX_TRAIL = 300


# =========================================================
# MINIMUM DISTANCE
# =========================================================

minimum_distance = float("inf")
minimum_distance_time = None


# =========================================================
# UPDATE
# =========================================================

def update(frame):

    global simulation_time
    global minimum_distance
    global minimum_distance_time

    # Advance simulation clock
    simulation_time += timedelta(
        seconds=SIMULATION_SPEED
    )

    # Get CARTOSAT state
    cartosat_position, cartosat_velocity = get_state(
        satellites["CARTOSAT-3"],
        simulation_time
    )

    # Get PSLV R/B state
    pslv_position, pslv_velocity = get_state(
        satellites["PSLV R/B"],
        simulation_time
    )

    # -----------------------------------------------------
    # TRAILS
    # -----------------------------------------------------

    cartosat_x.append(cartosat_position[0])
    cartosat_y.append(cartosat_position[1])

    pslv_x.append(pslv_position[0])
    pslv_y.append(pslv_position[1])

    if len(cartosat_x) > MAX_TRAIL:
        cartosat_x.pop(0)
        cartosat_y.pop(0)

    if len(pslv_x) > MAX_TRAIL:
        pslv_x.pop(0)
        pslv_y.pop(0)

    cartosat_point.set_data(
        [cartosat_position[0]],
        [cartosat_position[1]]
    )

    pslv_point.set_data(
        [pslv_position[0]],
        [pslv_position[1]]
    )

    cartosat_trail.set_data(
        cartosat_x,
        cartosat_y
    )

    pslv_trail.set_data(
        pslv_x,
        pslv_y
    )

    # -----------------------------------------------------
    # RELATIVE MOTION
    # -----------------------------------------------------

    relative_position = (
        cartosat_position - pslv_position
    )

    relative_velocity = (
        cartosat_velocity - pslv_velocity
    )

    distance = np.linalg.norm(
        relative_position
    )

    relative_speed = np.linalg.norm(
        relative_velocity
    )

    # -----------------------------------------------------
    # CLOSING SPEED
    # -----------------------------------------------------

    closing_speed = -np.dot(
        relative_position,
        relative_velocity
    ) / distance

    # -----------------------------------------------------
    # APPROACH ANGLE
    # -----------------------------------------------------

    cosine_angle = np.dot(
        relative_position,
        relative_velocity
    ) / (
        np.linalg.norm(relative_position)
        *
        np.linalg.norm(relative_velocity)
    )

    cosine_angle = np.clip(
        cosine_angle,
        -1.0,
        1.0
    )

    approach_angle = np.degrees(
        np.arccos(cosine_angle)
    )

    # -----------------------------------------------------
    # MINIMUM DISTANCE OBSERVED
    # -----------------------------------------------------

    if distance < minimum_distance:

        minimum_distance = distance
        minimum_distance_time = simulation_time

    # -----------------------------------------------------
    # RISK STATUS
    # -----------------------------------------------------

    if distance < CLOSE_APPROACH_KM:

        status = "CLOSE APPROACH"
        status_level = "HIGH"

    elif distance < SAFE_DISTANCE_KM:

        status = "MONITOR"
        status_level = "MEDIUM"

    else:

        status = "SAFE"
        status_level = "LOW"

    # -----------------------------------------------------
    # ALTITUDE
    # -----------------------------------------------------

    cartosat_altitude = (
        np.linalg.norm(cartosat_position)
        - 6371
    )

    pslv_altitude = (
        np.linalg.norm(pslv_position)
        - 6371
    )

    # -----------------------------------------------------
    # INFORMATION PANEL
    # -----------------------------------------------------

    info_text.set_text(
        f"SIMULATION TIME\n"
        f"{simulation_time.strftime('%Y-%m-%d %H:%M:%S UTC')}\n\n"

        f"CARTOSAT-3\n"
        f"Altitude: {cartosat_altitude:.1f} km\n\n"

        f"PSLV R/B\n"
        f"Altitude: {pslv_altitude:.1f} km\n\n"

        f"ENCOUNTER\n"
        f"Distance: {distance:,.2f} km\n"
        f"Relative speed: {relative_speed:.3f} km/s\n"
        f"Closing speed: {closing_speed:.3f} km/s\n"
        f"Approach angle: {approach_angle:.1f}°\n\n"

        f"MINIMUM OBSERVED\n"
        f"{minimum_distance:,.2f} km"
    )

    # -----------------------------------------------------
    # STATUS
    # -----------------------------------------------------

    status_text.set_text(
        f"STATUS: {status}   [{status_level}]"
    )

    return (
        cartosat_point,
        pslv_point,
        cartosat_trail,
        pslv_trail,
        info_text,
        status_text
    )


# =========================================================
# START
# =========================================================

animation = FuncAnimation(
    fig,
    update,
    interval=UPDATE_INTERVAL,
    blit=False
)

plt.show()