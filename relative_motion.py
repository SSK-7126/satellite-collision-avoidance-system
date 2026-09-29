import pandas as pd
import numpy as np


INPUT_FILE = "output/orbital_states.csv"
OUTPUT_FILE = "output/encounter_analysis.csv"


def calculate_relative_motion():
    # Load propagated orbital states
    df = pd.read_csv(INPUT_FILE)

    # Separate the two objects
    cartosat = df[df["object"] == "CARTOSAT-3"].copy()
    pslv = df[df["object"] == "PSLV R/B"].copy()

    # Make sure rows are matched by time
    cartosat = cartosat.sort_values("time").reset_index(drop=True)
    pslv = pslv.sort_values("time").reset_index(drop=True)

    if len(cartosat) != len(pslv):
        raise ValueError("The two objects do not have the same number of time points.")

    if not np.array_equal(
        cartosat["time"].values,
        pslv["time"].values
    ):
        raise ValueError("Time points do not match between the two objects.")

    results = []

    for i in range(len(cartosat)):

        # Position vectors
        r_cartosat = np.array([
            cartosat.loc[i, "x_km"],
            cartosat.loc[i, "y_km"],
            cartosat.loc[i, "z_km"]
        ])

        r_pslv = np.array([
            pslv.loc[i, "x_km"],
            pslv.loc[i, "y_km"],
            pslv.loc[i, "z_km"]
        ])

        # Velocity vectors
        v_cartosat = np.array([
            cartosat.loc[i, "vx_km_s"],
            cartosat.loc[i, "vy_km_s"],
            cartosat.loc[i, "vz_km_s"]
        ])

        v_pslv = np.array([
            pslv.loc[i, "vx_km_s"],
            pslv.loc[i, "vy_km_s"],
            pslv.loc[i, "vz_km_s"]
        ])

        # Relative position
        relative_position = r_cartosat - r_pslv

        # Relative velocity
        relative_velocity = v_cartosat - v_pslv

        # Separation distance
        distance_km = np.linalg.norm(relative_position)

        # Relative speed
        relative_speed_km_s = np.linalg.norm(relative_velocity)

        results.append({
            "time": cartosat.loc[i, "time"],
            "distance_km": distance_km,
            "relative_speed_km_s": relative_speed_km_s,
            "relative_x_km": relative_position[0],
            "relative_y_km": relative_position[1],
            "relative_z_km": relative_position[2],
            "relative_vx_km_s": relative_velocity[0],
            "relative_vy_km_s": relative_velocity[1],
            "relative_vz_km_s": relative_velocity[2]
        })

    # Create analysis DataFrame
    result_df = pd.DataFrame(results)

    # Find closest approach
    closest_index = result_df["distance_km"].idxmin()
    closest = result_df.loc[closest_index]

    # Save complete analysis
    result_df.to_csv(OUTPUT_FILE, index=False)

    print("\nRELATIVE MOTION ANALYSIS")
    print("=" * 60)

    print(f"Time points analyzed: {len(result_df)}")

    print("\nClosest Approach")
    print("-" * 60)

    print(f"Time: {closest['time']}")
    print(f"Distance: {closest['distance_km']:.3f} km")
    print(
        f"Relative speed: "
        f"{closest['relative_speed_km_s']:.6f} km/s"
    )

    print("\nAnalysis saved to:")
    print(OUTPUT_FILE)


if __name__ == "__main__":
    calculate_relative_motion()