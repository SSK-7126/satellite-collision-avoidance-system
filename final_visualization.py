"""
final_visualization.py
======================
D1 Final Integration — 3D Orbital Visualization

Input:
    output/orbital_states.csv

Source of orbital states:
    Person 1 SGP4 propagation

This version:
    - Uses the propagated X/Y/Z coordinates directly
    - Displays Earth in 3D
    - Displays CARTOSAT-3 and PSLV R/B
    - Shows their 3D trajectories
    - Animates the propagated states
    - Supports pause, reset and playback speed control
"""

from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation

from analysis_engine import calculate_encounter_metrics


# ============================================================
# CONFIGURATION
# ============================================================

CSV_PATH = "output/orbital_states.csv"
ANALYSIS_PATH = "output/encounter_analysis.csv"

EARTH_RADIUS_KM = 6371.0


# ============================================================
# LOAD DATA
# ============================================================

def load_orbital_states(csv_path=CSV_PATH):
    """Load Person 1's propagated orbital states."""

    path = Path(csv_path)

    if not path.exists():
        raise FileNotFoundError(
            f"Orbital state file not found: {path.resolve()}\n"
            "Run 'python propagator.py' first."
        )

    df = pd.read_csv(path)

    required_columns = {
        "time",
        "object",
        "x_km",
        "y_km",
        "z_km",
        "vx_km_s",
        "vy_km_s",
        "vz_km_s",
    }

    missing = required_columns - set(df.columns)

    if missing:
        raise ValueError(
            f"Missing required columns: {sorted(missing)}"
        )

    df["time"] = pd.to_datetime(df["time"])

    objects = sorted(df["object"].unique())

    if "CARTOSAT-3" not in objects:
        raise ValueError("CARTOSAT-3 not found in orbital data.")

    if "PSLV R/B" not in objects:
        raise ValueError("PSLV R/B not found in orbital data.")

    cartosat = (
        df[df["object"] == "CARTOSAT-3"]
        .sort_values("time")
        .reset_index(drop=True)
    )

    pslv = (
        df[df["object"] == "PSLV R/B"]
        .sort_values("time")
        .reset_index(drop=True)
    )

    if len(cartosat) != len(pslv):
        raise ValueError(
            "CARTOSAT-3 and PSLV R/B have different numbers of time points."
        )

    if not np.array_equal(
        cartosat["time"].values,
        pslv["time"].values
    ):
        raise ValueError(
            "CARTOSAT-3 and PSLV R/B timestamps are not synchronized."
        )

    return cartosat, pslv


def load_encounter_analysis(csv_path=ANALYSIS_PATH):
    """Load Person 1's relative-motion analysis."""

    path = Path(csv_path)

    if not path.exists():
        print(
            f"[WARNING] Encounter analysis file not found: "
            f"{path.resolve()}"
        )
        return None

    df = pd.read_csv(path)

    required_columns = {
        "time",
        "distance_km"
    }

    missing = required_columns - set(df.columns)

    if missing:
        raise ValueError(
            f"Encounter analysis is missing columns: {sorted(missing)}"
        )

    df["time"] = pd.to_datetime(df["time"])

    return df


# ============================================================
# EARTH
# ============================================================

def create_earth(ax):
    """Draw a 3D spherical Earth."""

    u = np.linspace(0, 2 * np.pi, 60)
    v = np.linspace(0, np.pi, 30)

    x = EARTH_RADIUS_KM * np.outer(
        np.cos(u),
        np.sin(v)
    )

    y = EARTH_RADIUS_KM * np.outer(
        np.sin(u),
        np.sin(v)
    )

    z = EARTH_RADIUS_KM * np.outer(
        np.ones_like(u),
        np.cos(v)
    )

    ax.plot_surface(
        x,
        y,
        z,
        alpha=0.25,
        linewidth=0,
        color="steelblue"
    )


# ============================================================
# MAIN VISUALIZATION
# ============================================================

def run_visualization():

    cartosat, pslv = load_orbital_states()

    encounter_data = load_encounter_analysis()

    cad = None
    tca = None

    if encounter_data is not None and not encounter_data.empty:

        cad_row = encounter_data.loc[
            encounter_data["distance_km"].idxmin()
        ]

        cad = float(cad_row["distance_km"])
        tca = cad_row["time"]

    print("=" * 65)
    print("FINAL 3D ORBITAL VISUALIZATION")
    print("=" * 65)

    print(f"Input: {CSV_PATH}")
    print(f"Time points: {len(cartosat)}")
    print(f"Start: {cartosat['time'].iloc[0]}")
    print(f"End:   {cartosat['time'].iloc[-1]}")
    print()

    # --------------------------------------------------------
    # Create figure
    # --------------------------------------------------------

    fig = plt.figure(figsize=(11, 9))

    ax = fig.add_subplot(
        111,
        projection="3d"
    )

    try:
        fig.canvas.manager.set_window_title(
            "D1 Final Integration — 3D Orbital Visualization"
        )
    except Exception:
        pass

    # --------------------------------------------------------
    # Earth
    # --------------------------------------------------------

    create_earth(ax)

    # --------------------------------------------------------
    # Full orbital trajectories
    # --------------------------------------------------------

    ax.plot(
        cartosat["x_km"],
        cartosat["y_km"],
        cartosat["z_km"],
        linewidth=1.5,
        alpha=0.45,
        label="CARTOSAT-3 Trajectory"
    )

    ax.plot(
        pslv["x_km"],
        pslv["y_km"],
        pslv["z_km"],
        linewidth=1.5,
        alpha=0.45,
        label="PSLV R/B Trajectory"
    )

    # --------------------------------------------------------
    # Current object markers
    # --------------------------------------------------------

    sat_point, = ax.plot(
        [],
        [],
        [],
        marker="o",
        markersize=9,
        label="CARTOSAT-3"
    )

    pslv_point, = ax.plot(
        [],
        [],
        [],
        marker="s",
        markersize=8,
        label="PSLV R/B"
    )

    # --------------------------------------------------------
    # Moving trails
    # --------------------------------------------------------

    sat_trail, = ax.plot(
        [],
        [],
        [],
        linewidth=2
    )

    pslv_trail, = ax.plot(
        [],
        [],
        [],
        linewidth=2
    )

    # --------------------------------------------------------
    # Separation line
    # --------------------------------------------------------

    separation_line, = ax.plot(
        [],
        [],
        [],
        linestyle="--",
        linewidth=1.2,
        alpha=0.7
    )

    # --------------------------------------------------------
    # Information display
    # --------------------------------------------------------

    info = ax.text2D(
        0.02,
        0.96,
        "",
        transform=ax.transAxes,
        fontsize=9,
        verticalalignment="top",
        family="monospace",
        bbox=dict(
            boxstyle="round",
            alpha=0.8
        )
    )

    # --------------------------------------------------------
    # Axis limits
    # --------------------------------------------------------

    all_x = np.concatenate([
        cartosat["x_km"].values,
        pslv["x_km"].values
    ])

    all_y = np.concatenate([
        cartosat["y_km"].values,
        pslv["y_km"].values
    ])

    all_z = np.concatenate([
        cartosat["z_km"].values,
        pslv["z_km"].values
    ])

    max_range = max(
        np.max(np.abs(all_x)),
        np.max(np.abs(all_y)),
        np.max(np.abs(all_z)),
        EARTH_RADIUS_KM
    )

    limit = max_range * 1.10

    ax.set_xlim(-limit, limit)
    ax.set_ylim(-limit, limit)
    ax.set_zlim(-limit, limit)

    # --------------------------------------------------------
    # Labels
    # --------------------------------------------------------

    ax.set_xlabel("X Position (km)")
    ax.set_ylabel("Y Position (km)")
    ax.set_zlabel("Z Position (km)")

    ax.set_title(
        "D1 Final Integration — 3D Orbital Visualization\n"
        "SGP4 Propagated Data"
    )

    ax.legend(loc="upper right")

    ax.set_box_aspect([1, 1, 1])

    # ========================================================
    # SIMULATION STATE
    # ========================================================

    simulation_state = {
        "paused": False,
        "speed": 1.0,
        "current_frame": 0
    }

    # One frame is displayed every 100 ms at 1x.
    BASE_INTERVAL_MS = 100

    # ========================================================
    # UPDATE FUNCTION
    # ========================================================

    trail_length = 25

    def update(frame):

        frame = int(frame)

        # Keep frame inside valid range.
        frame = max(
            0,
            min(frame, len(cartosat) - 1)
        )

        simulation_state["current_frame"] = frame

        sat = cartosat.iloc[frame]
        obj = pslv.iloc[frame]

        # ----------------------------------------------------
        # Current positions
        # ----------------------------------------------------

        sat_point.set_data_3d(
            [sat["x_km"]],
            [sat["y_km"]],
            [sat["z_km"]]
        )

        pslv_point.set_data_3d(
            [obj["x_km"]],
            [obj["y_km"]],
            [obj["z_km"]]
        )

        # ----------------------------------------------------
        # Trails
        # ----------------------------------------------------

        start = max(
            0,
            frame - trail_length
        )

        sat_trail.set_data_3d(
            cartosat["x_km"].iloc[start:frame + 1],
            cartosat["y_km"].iloc[start:frame + 1],
            cartosat["z_km"].iloc[start:frame + 1]
        )

        pslv_trail.set_data_3d(
            pslv["x_km"].iloc[start:frame + 1],
            pslv["y_km"].iloc[start:frame + 1],
            pslv["z_km"].iloc[start:frame + 1]
        )

        # ----------------------------------------------------
        # Encounter analysis
        # ----------------------------------------------------

        sat_position = np.array([
            sat["x_km"],
            sat["y_km"],
            sat["z_km"]
        ])

        sat_velocity = np.array([
            sat["vx_km_s"],
            sat["vy_km_s"],
            sat["vz_km_s"]
        ])

        obj_position = np.array([
            obj["x_km"],
            obj["y_km"],
            obj["z_km"]
        ])

        obj_velocity = np.array([
            obj["vx_km_s"],
            obj["vy_km_s"],
            obj["vz_km_s"]
        ])

        metrics = calculate_encounter_metrics(
            sat_position,
            sat_velocity,
            obj_position,
            obj_velocity
        )

        distance = metrics["distance_km"]
        relative_speed = metrics["relative_speed_km_s"]
        closing_speed = metrics["closing_speed_km_s"]
        approach_angle = metrics["approach_angle_deg"]
        status = metrics["status"]
        level = metrics["level"]

        # ----------------------------------------------------
        # Separation line
        # ----------------------------------------------------

        separation_line.set_data_3d(
            [sat["x_km"], obj["x_km"]],
            [sat["y_km"], obj["y_km"]],
            [sat["z_km"], obj["z_km"]]
        )

        # ----------------------------------------------------
        # Speeds
        # ----------------------------------------------------

        sat_speed = np.sqrt(
            sat["vx_km_s"] ** 2 +
            sat["vy_km_s"] ** 2 +
            sat["vz_km_s"] ** 2
        )

        obj_speed = np.sqrt(
            obj["vx_km_s"] ** 2 +
            obj["vy_km_s"] ** 2 +
            obj["vz_km_s"] ** 2
        )

        # ----------------------------------------------------
        # Information display
        # ----------------------------------------------------

        info.set_text(
            f"TIME: {sat['time'].strftime('%Y-%m-%d %H:%M:%S UTC')}\n"
            f"STEP: {frame + 1}/{len(cartosat)}\n\n"
            f"SIMULATION SPEED: "
            f"{simulation_state['speed']:.2f}x\n\n"

            f"CARTOSAT-3\n"
            f"  Position: "
            f"[{sat['x_km']:.0f}, "
            f"{sat['y_km']:.0f}, "
            f"{sat['z_km']:.0f}] km\n"
            f"  Speed: {sat_speed:.2f} km/s\n\n"

            f"PSLV R/B (Rocket Body)\n"
            f"  Position: "
            f"[{obj['x_km']:.0f}, "
            f"{obj['y_km']:.0f}, "
            f"{obj['z_km']:.0f}] km\n"
            f"  Speed: {obj_speed:.2f} km/s\n\n"

            f"ENCOUNTER ANALYSIS\n"
            f"  Distance:       {distance:,.2f} km\n"
            f"  Relative Speed: {relative_speed:.3f} km/s\n"
            f"  Closing Speed:  {closing_speed:.3f} km/s\n"
            f"  Approach Angle: {approach_angle:.2f}°\n\n"

            f"STATUS: {status}\n"
            f"LEVEL:  {level}\n\n"

            f"60-MINUTE ENCOUNTER SUMMARY\n"
            f"  CAD: "
            f"{cad:,.2f} km"
            f"{'' if cad is not None else 'N/A'}\n"
            f"  TCA: "
            f"{tca.strftime('%H:%M:%S UTC') if tca is not None else 'N/A'}"
        )

        return (
            sat_point,
            pslv_point,
            sat_trail,
            pslv_trail,
            separation_line,
            info
        )

    # ========================================================
    # SPEED CONTROL
    # ========================================================

    def set_speed(new_speed):

        new_speed = max(
            0.25,
            min(new_speed, 16.0)
        )

        simulation_state["speed"] = new_speed

        # Change timer interval.
        #
        # 1x  = 100 ms
        # 2x  = 50 ms
        # 4x  = 25 ms
        # 0.5x = 200 ms
        #
        # This controls how frequently our custom frame
        # advancement function runs.

        interval = max(
            10,
            int(BASE_INTERVAL_MS / new_speed)
        )

        animation.event_source.interval = interval

        # If paused, redraw immediately so the speed display
        # changes without moving the satellites.

        if simulation_state["paused"]:

            update(
                simulation_state["current_frame"]
            )

            fig.canvas.draw_idle()

    # ========================================================
    # CUSTOM FRAME ADVANCEMENT
    # ========================================================

    # We use our own frame counter instead of relying on
    # FuncAnimation's automatic frame generator.

    def advance_frame():

        if simulation_state["paused"]:
            return

        current = simulation_state["current_frame"]

        # At 1x, move one frame per timer tick.
        #
        # At 2x, move two frames.
        #
        # At 4x, move four frames.
        #
        # At 0.5x, use an accumulator so the animation moves
        # one frame every two timer ticks.

        speed = simulation_state["speed"]

        simulation_state.setdefault(
            "frame_accumulator",
            0.0
        )

        simulation_state["frame_accumulator"] += speed

        frames_to_advance = int(
            simulation_state["frame_accumulator"]
        )

        simulation_state["frame_accumulator"] -= (
            frames_to_advance
        )

        if frames_to_advance <= 0:
            return

        next_frame = current + frames_to_advance

        # Loop back to beginning when the simulation reaches
        # the final frame.

        if next_frame >= len(cartosat):

            next_frame = 0

            simulation_state["frame_accumulator"] = 0.0

        update(next_frame)

        fig.canvas.draw_idle()

    # ========================================================
    # CREATE ANIMATION
    # ========================================================

    # Do not use FuncAnimation's automatic frame progression.
    #
    # We create the animation object only so Matplotlib owns
    # the figure's timer.

    animation = FuncAnimation(
        fig,
        lambda frame: update(
            simulation_state["current_frame"]
        ),
        frames=None,
        interval=BASE_INTERVAL_MS,
        blit=False,
        repeat=False
    )

    # Stop the automatic FuncAnimation timer.
    animation.event_source.stop()

    # Replace the timer callback with our own frame controller.

    animation.event_source.add_callback(
        advance_frame
    )

    animation.event_source.interval = BASE_INTERVAL_MS

    # Start the simulation.

    animation.event_source.start()

    # ========================================================
    # KEYBOARD CONTROLS
    # ========================================================

    def on_key(event):

        # ----------------------------------------------------
        # SPACE = Pause / Resume
        # ----------------------------------------------------

        if event.key == " ":

            if simulation_state["paused"]:

                simulation_state["paused"] = False

                animation.event_source.start()

            else:

                simulation_state["paused"] = True

                animation.event_source.stop()

        # ----------------------------------------------------
        # R = Reset
        # ----------------------------------------------------

        elif event.key.lower() == "r":

            animation.event_source.stop()

            simulation_state["current_frame"] = 0
            simulation_state["frame_accumulator"] = 0.0

            update(0)

            fig.canvas.draw_idle()

            simulation_state["paused"] = False

            animation.event_source.start()

        # ----------------------------------------------------
        # + = Increase speed
        # ----------------------------------------------------

        elif event.key in ["+", "="]:

            set_speed(
                simulation_state["speed"] * 2
            )

            if not simulation_state["paused"]:
                animation.event_source.stop()
                animation.event_source.start()

        # ----------------------------------------------------
        # - = Decrease speed
        # ----------------------------------------------------

        elif event.key == "-":

            set_speed(
                simulation_state["speed"] / 2
            )

            if not simulation_state["paused"]:
                animation.event_source.stop()
                animation.event_source.start()

    fig.canvas.mpl_connect(
        "key_press_event",
        on_key
    )

    # --------------------------------------------------------
    # Control instructions
    # --------------------------------------------------------

    fig.text(
        0.5,
        0.02,
        "SPACE: Pause/Resume   |   "
        "R: Reset   |   "
        "+/-: Change Playback Speed",
        ha="center",
        fontsize=9
    )

    # --------------------------------------------------------
    # Initial frame
    # --------------------------------------------------------

    simulation_state["frame_accumulator"] = 0.0

    update(0)

    plt.show()


# ============================================================
# PROGRAM ENTRY
# ============================================================

if __name__ == "__main__":
    run_visualization()