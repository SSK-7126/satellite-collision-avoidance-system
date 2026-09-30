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
"""

from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation


# ============================================================
# CONFIGURATION
# ============================================================

CSV_PATH = "output/orbital_states.csv"
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


# ============================================================
# EARTH
# ============================================================

def create_earth(ax):
    """Draw a 3D spherical Earth."""

    u = np.linspace(0, 2 * np.pi, 60)
    v = np.linspace(0, np.pi, 30)

    x = EARTH_RADIUS_KM * np.outer(np.cos(u), np.sin(v))
    y = EARTH_RADIUS_KM * np.outer(np.sin(u), np.sin(v))
    z = EARTH_RADIUS_KM * np.outer(np.ones_like(u), np.cos(v))

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

    ax = fig.add_subplot(111, projection="3d")

    fig.canvas.manager.set_window_title(
        "D1 Final Integration — 3D Orbital Visualization"
    )

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

    # Determine scale dynamically from actual propagated data.

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

    # Small margin around the actual data.

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

    # --------------------------------------------------------
    # Equal aspect ratio
    # --------------------------------------------------------

    ax.set_box_aspect([1, 1, 1])

    # --------------------------------------------------------
    # Animation
    # --------------------------------------------------------

    trail_length = 25

    def update(frame):

        sat = cartosat.iloc[frame]
        obj = pslv.iloc[frame]

        # Current positions

        sat_position = (
            sat["x_km"],
            sat["y_km"],
            sat["z_km"]
        )

        obj_position = (
            obj["x_km"],
            obj["y_km"],
            obj["z_km"]
        )

        sat_point.set_data_3d(
            [sat_position[0]],
            [sat_position[1]],
            [sat_position[2]]
        )

        pslv_point.set_data_3d(
            [obj_position[0]],
            [obj_position[1]],
            [obj_position[2]]
        )

        # ----------------------------------------------------
        # Trails
        # ----------------------------------------------------

        start = max(0, frame - trail_length)

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
        # 3D separation
        # ----------------------------------------------------

        dx = sat["x_km"] - obj["x_km"]
        dy = sat["y_km"] - obj["y_km"]
        dz = sat["z_km"] - obj["z_km"]

        distance = np.sqrt(
            dx ** 2 +
            dy ** 2 +
            dz ** 2
        )

        separation_line.set_data_3d(
            [sat["x_km"], obj["x_km"]],
            [sat["y_km"], obj["y_km"]],
            [sat["z_km"], obj["z_km"]]
        )

        # ----------------------------------------------------
        # Telemetry
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

        info.set_text(
            f"TIME: {sat['time'].strftime('%Y-%m-%d %H:%M:%S UTC')}\n"
            f"STEP: {frame + 1}/{len(cartosat)}\n\n"
            f"CARTOSAT-3\n"
            f"  Position: "
            f"[{sat['x_km']:.0f}, "
            f"{sat['y_km']:.0f}, "
            f"{sat['z_km']:.0f}] km\n"
            f"  Speed: {sat_speed:.2f} km/s\n\n"
            f"PSLV R/B\n"
            f"  Position: "
            f"[{obj['x_km']:.0f}, "
            f"{obj['y_km']:.0f}, "
            f"{obj['z_km']:.0f}] km\n"
            f"  Speed: {obj_speed:.2f} km/s\n\n"
            f"3D SEPARATION: {distance:,.2f} km"
        )

        return (
            sat_point,
            pslv_point,
            sat_trail,
            pslv_trail,
            separation_line,
            info
        )

    animation = FuncAnimation(
        fig,
        update,
        frames=len(cartosat),
        interval=100,
        blit=False,
        repeat=True
    )

    plt.show()


# ============================================================
# PROGRAM ENTRY
# ============================================================

if __name__ == "__main__":
    run_visualization()