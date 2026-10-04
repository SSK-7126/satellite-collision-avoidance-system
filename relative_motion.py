import pandas as pd
import numpy as np


INPUT_FILE = "output/orbital_states.csv"
OUTPUT_FILE = "output/encounter_analysis.csv"
SUMMARY_FILE = "output/encounter_summary.csv"


def calculate_relative_motion(primary_name="CARTOSAT-3"):
    """
    Calculate relative motion between the primary satellite (CARTOSAT-3)
    and all other tracked space objects in the dataset.
    """
    df = pd.read_csv(INPUT_FILE)

    if primary_name not in df["object"].values:
        raise ValueError(f"Primary object '{primary_name}' not found in orbital data.")

    primary_df = df[df["object"] == primary_name].sort_values("time").reset_index(drop=True)
    all_objects = sorted(df["object"].unique())
    secondary_objects = [obj for obj in all_objects if obj != primary_name]

    print("\n" + "=" * 65)
    print(f"MULTI-OBJECT RELATIVE MOTION & CONJUNCTION ASSESSMENT")
    print(f"Primary Asset: {primary_name}")
    print(f"Tracked Catalog: {len(secondary_objects)} secondary objects")
    print("=" * 65)

    summary_records = []
    all_encounter_rows = []

    # If PSLV R/B is present, compute its baseline first for backward compatibility
    ordered_secondaries = (
        ["PSLV R/B"] + [o for o in secondary_objects if o != "PSLV R/B"]
        if "PSLV R/B" in secondary_objects
        else secondary_objects
    )

    for sec_name in ordered_secondaries:
        sec_df = df[df["object"] == sec_name].sort_values("time").reset_index(drop=True)

        if len(primary_df) != len(sec_df):
            print(f"[WARN] Time length mismatch for {sec_name}, skipping.")
            continue

        pairwise_results = []
        for i in range(len(primary_df)):
            r_pri = np.array([
                primary_df.loc[i, "x_km"],
                primary_df.loc[i, "y_km"],
                primary_df.loc[i, "z_km"]
            ])
            r_sec = np.array([
                sec_df.loc[i, "x_km"],
                sec_df.loc[i, "y_km"],
                sec_df.loc[i, "z_km"]
            ])
            v_pri = np.array([
                primary_df.loc[i, "vx_km_s"],
                primary_df.loc[i, "vy_km_s"],
                primary_df.loc[i, "vz_km_s"]
            ])
            v_sec = np.array([
                sec_df.loc[i, "vx_km_s"],
                sec_df.loc[i, "vy_km_s"],
                sec_df.loc[i, "vz_km_s"]
            ])

            r_rel = r_pri - r_sec
            v_rel = v_pri - v_sec
            dist_km = float(np.linalg.norm(r_rel))
            rel_spd = float(np.linalg.norm(v_rel))

            row_data = {
                "time": primary_df.loc[i, "time"],
                "secondary_object": sec_name,
                "distance_km": dist_km,
                "relative_speed_km_s": rel_spd,
                "relative_x_km": r_rel[0],
                "relative_y_km": r_rel[1],
                "relative_z_km": r_rel[2],
                "relative_vx_km_s": v_rel[0],
                "relative_vy_km_s": v_rel[1],
                "relative_vz_km_s": v_rel[2]
            }
            pairwise_results.append(row_data)

        sec_res_df = pd.DataFrame(pairwise_results)
        closest_idx = sec_res_df["distance_km"].idxmin()
        closest_row = sec_res_df.loc[closest_idx]

        summary_records.append({
            "secondary_object": sec_name,
            "closest_approach_distance_km": closest_row["distance_km"],
            "time_of_closest_approach": closest_row["time"],
            "relative_speed_at_tca_km_s": closest_row["relative_speed_km_s"]
        })

        if sec_name == "PSLV R/B" or len(all_encounter_rows) == 0:
            # Baseline encounter file maintains PSLV R/B structure for existing consumers
            primary_baseline_df = sec_res_df

        all_encounter_rows.extend(pairwise_results)

    # Save primary baseline encounter file (compatible with stage2 & test scripts)
    primary_baseline_df.to_csv(OUTPUT_FILE, index=False)
    print(f"[OK] Primary baseline encounter analysis saved to: {OUTPUT_FILE}")

    # Save catalog summary
    summary_df = pd.DataFrame(summary_records).sort_values("closest_approach_distance_km").reset_index(drop=True)
    summary_df.to_csv(SUMMARY_FILE, index=False)
    print(f"[OK] Catalog conjunction summary saved to: {SUMMARY_FILE}\n")

    print(f"{'OBJECT':<25} {'MIN DIST (km)':<16} {'TCA (UTC)':<24} {'REL SPEED (km/s)':<16}")
    print("-" * 81)
    for _, r in summary_df.iterrows():
        print(f"{r['secondary_object']:<25} {r['closest_approach_distance_km']:<16.2f} {str(r['time_of_closest_approach'])[:19]:<24} {r['relative_speed_at_tca_km_s']:<16.3f}")


if __name__ == "__main__":
    calculate_relative_motion()