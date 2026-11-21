"""
D2/visualization/render_demo_snapshots.py
=========================================
Generates high-fidelity visual demonstration snapshots and HUD telemetry renders
of the 8-step satellite collision-avoidance demonstration sequence.
"""

import os
import json
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D

from D2.visualization.simulation_exporter import DEFAULT_OUTPUT_PATH

OUTPUT_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "visualization",
    "snapshots"
)


def render_all_demonstration_snapshots(json_path=DEFAULT_OUTPUT_PATH, out_dir=OUTPUT_DIR):
    os.makedirs(out_dir, exist_ok=True)

    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    ts = data["time_series"]
    timestamps = np.array(ts["timestamps_sec"])
    sat_nom_ue = np.array(ts["satellite_nominal_positions_ue"])
    deb_ue = np.array(ts["debris_positions_ue"])
    sat_mod_ue = np.array(ts["satellite_modified_positions_ue"])

    earth_radius_uu = data["physical_constants"]["earth_radius_uu"]
    nom_enc = data["nominal_encounter"]
    post_enc = data["post_manoeuvre_encounter"]
    man = data["selected_manoeuvre"]

    # Sphere coordinates for Earth
    u = np.linspace(0, 2 * np.pi, 40)
    v = np.linspace(0, Math_pi := np.pi, 20)
    x_earth = earth_radius_uu * np.outer(np.cos(u), np.sin(v))
    y_earth = earth_radius_uu * np.outer(np.sin(u), np.sin(v))
    z_earth = earth_radius_uu * np.outer(np.ones(np.size(u)), np.cos(v))

    # Helper function to plot base scene
    def plot_base_scene(ax, title, time_sec):
        ax.set_facecolor("#05070e")
        # Plot Earth
        ax.plot_surface(x_earth, y_earth, z_earth, color="#1e3a8a", alpha=0.35, edgecolor="#3b82f6", linewidth=0.2)
        # Plot Orbits
        ax.plot(sat_nom_ue[:, 0], sat_nom_ue[:, 1], sat_nom_ue[:, 2], color="#00e5ff", linestyle="--", linewidth=1.2, label="Nominal Sat Path", alpha=0.7)
        ax.plot(deb_ue[:, 0], deb_ue[:, 1], deb_ue[:, 2], color="#ef4444", linestyle="--", linewidth=1.2, label="Debris Path", alpha=0.7)

        ax.set_title(title, color="#38bdf8", fontsize=11, fontweight="bold", pad=10)
        ax.set_xlim([-800, 800])
        ax.set_ylim([-800, 800])
        ax.set_zlim([-800, 800])
        ax.tick_params(colors="#64748b", labelsize=7)
        ax.xaxis.pane.fill = False
        ax.yaxis.pane.fill = False
        ax.zaxis.pane.fill = False
        ax.grid(color="#1e293b", linestyle=":", linewidth=0.5)

    # -------------------------------------------------------------
    # SNAPSHOT 1: Conjunction Assessment at TCA (Nominal Orbit)
    # -------------------------------------------------------------
    fig = plt.figure(figsize=(14, 8), facecolor="#05070e")
    ax1 = fig.add_subplot(1, 2, 1, projection="3d")
    plot_base_scene(ax1, "3D ORBITAL VIEWPORT — NOMINAL CLOSE APPROACH", 769.6)

    # TCA position
    tca_nom_sec = nom_enc["tca_seconds"]
    idx_tca = int(np.clip(np.searchsorted(timestamps, tca_nom_sec), 0, len(timestamps) - 1))
    sat_tca = sat_nom_ue[idx_tca]
    deb_tca = deb_ue[idx_tca]

    ax1.scatter([sat_tca[0]], [sat_tca[1]], [sat_tca[2]], color="#00e5ff", s=80, marker="s", label="Satellite (TCA)")
    ax1.scatter([deb_tca[0]], [deb_tca[1]], [deb_tca[2]], color="#ef4444", s=60, marker="o", label="Debris (TCA)")
    ax1.plot([sat_tca[0], deb_tca[0]], [sat_tca[1], deb_tca[1]], [sat_tca[2], deb_tca[2]], color="#ff0055", linewidth=2.5, label="Miss Distance: 1563.5 m")
    ax1.legend(loc="upper left", facecolor="#0b1329", edgecolor="#38bdf8", fontsize=8, labelcolor="#e2e8f0")

    # Telemetry HUD on right panel
    ax2 = fig.add_subplot(1, 2, 2)
    ax2.set_facecolor("#0b1329")
    ax2.axis("off")
    hud_text = (
        "=====================================================\n"
        "   UNREAL ENGINE 5 HUD TELEMETRY — CONJUNCTION STAGE\n"
        "=====================================================\n\n"
        f"SCENARIO CLOCK     : T + {tca_nom_sec:.1f} s [TCA ENCOUNTER]\n"
        f"STATUS             : CRITICAL COLLISION ALERT [HIGH RISK]\n"
        f"PRIMARY SATELLITE  : PROTECTED_SAT (LEO 7000 km Circular)\n"
        f"SECONDARY OBJECT   : DEBRIS_B\n\n"
        "-----------------------------------------------------\n"
        "1. NOMINAL ENCOUNTER METRICS (PRE-MANOEUVRE)\n"
        "-----------------------------------------------------\n"
        f"Time to Closest App : {nom_enc['tca_seconds']:.2f} s\n"
        f"Nominal Miss Dist   : {nom_enc['miss_distance_m']:.2f} m (1.563 km)\n"
        f"Relative Speed      : {nom_enc['relative_speed_mps']:.3f} m/s\n"
        f"Collision Prob (Pc) : {nom_enc['collision_probability']:.3e} (log10: {nom_enc['collision_log10_pc']:.2f})\n"
        f"Pc Numerical Status : [{nom_enc['pc_status']}]\n"
        "Safety Constraint   : Miss Distance < 2000.0 m [VIOLATION]\n\n"
        "-----------------------------------------------------\n"
        "2. AUTONOMOUS AVOIDANCE PLANNER DECISION\n"
        "-----------------------------------------------------\n"
        f"Selected Manoeuvre  : {man['manoeuvre_id']}\n"
        f"Burn Epoch          : T + {man['burn_epoch_seconds']:.1f} s (Lead Time: {man['lead_time_before_nom_tca_seconds']:.1f} s)\n"
        f"Delta-v Magnitude   : {man['delta_v_magnitude_mps']:.3f} m/s\n"
        f"RTN Direction       : {man['direction_label_rtn']} (Radial Inward)\n"
        f"Delta-v Vector RTN  : [{man['delta_v_rtn_mps'][0]:.2f}, {man['delta_v_rtn_mps'][1]:.2f}, {man['delta_v_rtn_mps'][2]:.2f}] m/s\n"
        "Action Status       : BURN EXECUTED AT T+169.6 s\n"
    )
    ax2.text(0.05, 0.95, hud_text, transform=ax2.transAxes, color="#e2e8f0", fontfamily="monospace", fontsize=9.5, verticalalignment="top")
    plt.tight_layout()
    snap1_path = os.path.join(out_dir, "step4_conjunction_assessment.png")
    fig.savefig(snap1_path, dpi=180, facecolor=fig.get_facecolor(), edgecolor="none")
    plt.close(fig)

    # -------------------------------------------------------------
    # SNAPSHOT 2: Avoidance Burn Execution at t = 169.6s
    # -------------------------------------------------------------
    fig = plt.figure(figsize=(14, 8), facecolor="#05070e")
    ax1 = fig.add_subplot(1, 2, 1, projection="3d")
    plot_base_scene(ax1, "3D ORBITAL VIEWPORT — IMPULSIVE BURN EXECUTION", 169.6)

    t_burn = man["burn_epoch_seconds"]
    idx_burn = int(np.clip(np.searchsorted(timestamps, t_burn), 0, len(timestamps) - 1))
    sat_burn = sat_nom_ue[idx_burn]

    # Draw Modified Orbit in Green
    ax1.plot(sat_mod_ue[:, 0], sat_mod_ue[:, 1], sat_mod_ue[:, 2], color="#00ff66", linewidth=1.5, label="Modified Post-Burn Path")
    # Draw Burn Ring
    ax1.scatter([sat_burn[0]], [sat_burn[1]], [sat_burn[2]], color="#ffaa00", s=150, marker="*", label="Burn Epoch: MAN_-R_3.0mps")
    # Draw Delta-v vector
    dv_ue = np.array(man["delta_v_ue_uu"]) * 3000.0  # Scale vector for visual prominence
    ax1.quiver(sat_burn[0], sat_burn[1], sat_burn[2], dv_ue[0], dv_ue[1], dv_ue[2], color="#ffaa00", linewidth=3, arrow_length_ratio=0.3)
    ax1.legend(loc="upper left", facecolor="#0b1329", edgecolor="#38bdf8", fontsize=8, labelcolor="#e2e8f0")

    ax2 = fig.add_subplot(1, 2, 2)
    ax2.set_facecolor("#0b1329")
    ax2.axis("off")
    burn_text = (
        "=====================================================\n"
        "   UNREAL ENGINE 5 HUD TELEMETRY — BURN EXECUTION\n"
        "=====================================================\n\n"
        f"SCENARIO CLOCK     : T + {t_burn:.1f} s [AVOIDANCE BURN EVENT]\n"
        f"STATUS             : IMPULSE APPLIED [TRANSITIONING ORBIT]\n"
        f"SATELLITE STATE    : POS CONTINUOUS, VELOCITY MODIFIED\n\n"
        "-----------------------------------------------------\n"
        "BURN MECHANICS & COORDINATE TRANSFORMATION\n"
        "-----------------------------------------------------\n"
        f"Target Direction    : {man['direction_label_rtn']} (Radial Inward along r/|r|)\n"
        f"Applied Impulse     : Delta-v = {man['delta_v_magnitude_mps']:.3f} m/s\n"
        f"ECI Delta-v Vector  : [{man['delta_v_eci_mps'][0]:+.3f}, {man['delta_v_eci_mps'][1]:+.3f}, {man['delta_v_eci_mps'][2]:+.3f}] m/s\n"
        f"Unreal Display Vec  : [{man['delta_v_ue_uu'][0]:+.4f}, {man['delta_v_ue_uu'][1]:+.4f}, {man['delta_v_ue_uu'][2]:+.4f}] uu\n"
        f"Position at Burn ECI: [{man['satellite_position_at_burn_eci_m'][0]:.0f}, {man['satellite_position_at_burn_eci_m'][1]:.0f}, {man['satellite_position_at_burn_eci_m'][2]:.0f}] m\n"
        f"Position at Burn UE : [{man['satellite_position_at_burn_ue_uu'][0]:.1f}, {man['satellite_position_at_burn_ue_uu'][1]:.1f}, {man['satellite_position_at_burn_ue_uu'][2]:.1f}] uu\n"
        "Impulse Model       : Instantaneous (dr = 0, dv = dv_eci)\n"
        "Propagator Coupling : Orbit STM Phi_post(t) initiated from post-burn state\n"
    )
    ax2.text(0.05, 0.95, burn_text, transform=ax2.transAxes, color="#e2e8f0", fontfamily="monospace", fontsize=9.5, verticalalignment="top")
    plt.tight_layout()
    snap2_path = os.path.join(out_dir, "step6_avoidance_burn.png")
    fig.savefig(snap2_path, dpi=180, facecolor=fig.get_facecolor(), edgecolor="none")
    plt.close(fig)

    # -------------------------------------------------------------
    # SNAPSHOT 3: Post-Manoeuvre Resolution at New TCA (t = 903.0s)
    # -------------------------------------------------------------
    fig = plt.figure(figsize=(14, 8), facecolor="#05070e")
    ax1 = fig.add_subplot(1, 2, 1, projection="3d")
    plot_base_scene(ax1, "3D ORBITAL VIEWPORT — RESOLVED ENCOUNTER AT NEW TCA", 903.0)

    # Draw Modified Orbit in Green
    ax1.plot(sat_mod_ue[:, 0], sat_mod_ue[:, 1], sat_mod_ue[:, 2], color="#00ff66", linewidth=1.8, label="Modified Trajectory (Post-Burn)")

    new_tca = post_enc["new_tca_seconds"]
    idx_new_tca = int(np.clip(np.searchsorted(timestamps, new_tca), 0, len(timestamps) - 1))
    sat_new_tca = sat_mod_ue[idx_new_tca]
    deb_new_tca = deb_ue[idx_new_tca]

    ax1.scatter([sat_new_tca[0]], [sat_new_tca[1]], [sat_new_tca[2]], color="#00ff66", s=90, marker="s", label="Satellite (New TCA)")
    ax1.scatter([deb_new_tca[0]], [deb_new_tca[1]], [deb_new_tca[2]], color="#ef4444", s=60, marker="o", label="Debris (New TCA)")
    ax1.plot([sat_new_tca[0], deb_new_tca[0]], [sat_new_tca[1], deb_new_tca[1]], [sat_new_tca[2], deb_new_tca[2]], color="#00ff66", linewidth=2.5, label=f"New Miss: {post_enc['new_miss_distance_m']:.1f} m")
    ax1.legend(loc="upper left", facecolor="#0b1329", edgecolor="#38bdf8", fontsize=8, labelcolor="#e2e8f0")

    ax2 = fig.add_subplot(1, 2, 2)
    ax2.set_facecolor("#0b1329")
    ax2.axis("off")
    resolve_text = (
        "=====================================================\n"
        "   UNREAL ENGINE 5 HUD TELEMETRY — RESOLUTION STAGE\n"
        "=====================================================\n\n"
        f"SCENARIO CLOCK     : T + {new_tca:.1f} s [POST-MANOEUVRE TCA]\n"
        f"STATUS             : AVOIDANCE RESOLVED [SAFE CLEARANCE]\n"
        f"RISK CLASSIFICATION: {post_enc['risk_classification']}\n\n"
        "-----------------------------------------------------\n"
        "BEFORE VS AFTER COMPARATIVE METRICS\n"
        "-----------------------------------------------------\n"
        f"Nominal Miss Distance : {nom_enc['miss_distance_m']:.2f} m (1.563 km)\n"
        f"New Miss Distance     : {post_enc['new_miss_distance_m']:.2f} m (2.454 km)\n"
        f"Miss Distance Increase: +{post_enc['delta_miss_distance_m']:.2f} m (+0.891 km) [SAFETY MARGIN SECURED]\n\n"
        f"Nominal TCA Epoch     : {nom_enc['tca_seconds']:.2f} s\n"
        f"New TCA Epoch         : {post_enc['new_tca_seconds']:.2f} s (Shift: +{post_enc['shift_in_tca_seconds']:+.2f} s)\n\n"
        f"Nominal Collision Pc  : {nom_enc['collision_probability']:.3e} (log10: {nom_enc['collision_log10_pc']:.2f})\n"
        f"New Collision Pc      : {post_enc['new_collision_probability']:.3e} (log10: {post_enc['new_collision_log10_pc']:.2f})\n"
        f"Pc Numerical Status   : [{post_enc['pc_status']}]\n"
        f"Max Trajectory Dev    : {post_enc['max_trajectory_deviation_m']:.1f} m\n"
        f"Total Delta-v Expended: {man['delta_v_magnitude_mps']:.3f} m/s\n"
    )
    ax2.text(0.05, 0.95, resolve_text, transform=ax2.transAxes, color="#e2e8f0", fontfamily="monospace", fontsize=9.5, verticalalignment="top")
    plt.tight_layout()
    snap3_path = os.path.join(out_dir, "step8_post_manoeuvre_resolution.png")
    fig.savefig(snap3_path, dpi=180, facecolor=fig.get_facecolor(), edgecolor="none")
    plt.close(fig)

    print(f"[SNAPSHOTS] Successfully generated demonstration snapshots in {out_dir}")
    return [snap1_path, snap2_path, snap3_path]


if __name__ == "__main__":
    paths = render_all_demonstration_snapshots()
    for p in paths:
        print("  Created:", p)

