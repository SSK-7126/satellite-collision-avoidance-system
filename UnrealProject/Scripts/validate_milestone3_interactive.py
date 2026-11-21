"""
validate_milestone3_interactive.py
==================================
READ-ONLY Validation of Milestone 3:
1. Timeline verification across all 8 milestones.
2. Collision probability verification (nominal, post-manoeuvre, underflow status).
3. Telemetry HUD data-source mapping.
4. Runtime interaction & camera view verification in UE 5.7.
"""

import unreal
import json
import os
import sys

out_file_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "../Saved/audit_report.txt"))
os.makedirs(os.path.dirname(out_file_path), exist_ok=True)
log_f = open(out_file_path, "w", encoding="utf-8")

def log(msg=""):
    print(msg)
    sys.stdout.flush()
    log_f.write(msg + "\n")
    log_f.flush()

log("=" * 85)
log("[READ-ONLY AUDIT] Milestone 3 Scientific & Interactive Validation")
log("=" * 85)

# 1. Load Level
level_path = "/Game/Scenarios/CollisionAvoidanceDemo"
unreal.EditorLevelLibrary.load_level(level_path)
world = unreal.EditorLevelLibrary.get_editor_world()
all_actors = unreal.EditorLevelLibrary.get_all_level_actors()

# 2. Load Simulation Payload
payload_path = os.path.abspath(os.path.join(
    os.path.dirname(__file__),
    "../../D2/visualization/unreal_simulation_payload.json"
)).replace("\\", "/")

with open(payload_path, "r", encoding="utf-8") as f:
    payload = json.load(f)

# Find Simulation Manager and Scene Actors
sim_mgrs = [a for a in all_actors if isinstance(a, unreal.OrbitSimulationManager)]
assert len(sim_mgrs) > 0, "OrbitSimulationManager not found in level!"
sim_mgr = sim_mgrs[0]

# Inspect Camera Actors
cameras = [a for a in all_actors if isinstance(a, unreal.CameraActor)]
log(f"\n--- 1. Camera Actors Discovery ({len(cameras)} found) ---")
for i, cam in enumerate(cameras):
    loc = cam.get_actor_location()
    rot = cam.get_actor_rotation()
    log(f"  Camera [{i+1}/{len(cameras)}]: '{cam.get_actor_label()}' | Loc: ({loc.x:.1f}, {loc.y:.1f}, {loc.z:.1f}) | Rot: (P={rot.pitch:.1f}, Y={rot.yaw:.1f}, R={rot.roll:.1f})")

# Initialize Simulation Manager with payload
init_ok = sim_mgr.initialize_simulation_from_payload(payload_path)
log(f"\nSimulation Manager Payload Init: {init_ok}")

# --- 2. Timeline and Step Verification ---
log("\n--- 2. Demonstration Sequence Timeline Audit ---")
steps = payload["demonstration_sequence"]
log(f"{'Step':<6} | {'Identifier':<26} | {'Sim Time (s)':<14} | {'Manoeuvre':<10} | {'Focus Camera':<18} | {'Headline'}")
log("-" * 110)
for s in steps:
    step_num = s["step"]
    sim_mgr.jump_to_step(step_num)
    t = sim_mgr.current_simulation_time
    b_man = sim_mgr.manoeuvre_executed
    cam_focus = s.get("camera_focus", "N/A")
    log(f"{step_num:<6} | {s['identifier']:<26} | {t:<14.1f} | {str(b_man):<10} | {cam_focus:<18} | {s['headline']}")

# Check nominal vs post-manoeuvre TCA and burn epoch
nom = payload["nominal_encounter"]
post = payload["post_manoeuvre_encounter"]
man = payload["selected_manoeuvre"]

log("\n--- 3. Key Astrodynamic Epochs Audit ---")
log(f"  Nominal TCA (unmanoeuvred)    : {nom['tca_seconds']:.4f} s (T+{nom['tca_seconds']:.1f}s)")
log(f"  Nominal Miss Distance         : {nom['miss_distance_m']:.2f} m")
log(f"  Manoeuvre Burn Epoch          : {man['burn_epoch_seconds']:.4f} s (T+{man['burn_epoch_seconds']:.1f}s)")
log(f"  Lead Time before Nominal TCA  : {man['lead_time_before_nom_tca_seconds']:.1f} s")
log(f"  Selected Impulse              : {man['manoeuvre_id']} | dV = {man['delta_v_magnitude_mps']:.2f} m/s in {man['direction_label_rtn']}")
log(f"  Post-Manoeuvre TCA (new)      : {post['new_tca_seconds']:.4f} s (T+{post['new_tca_seconds']:.1f}s)")
log(f"  Post-Manoeuvre Miss Distance  : {post['new_miss_distance_m']:.2f} m (+{post['delta_miss_distance_m']:.2f} m margin)")
log(f"  TCA Shift (delta-TCA)         : {post['shift_in_tca_seconds']:+.2f} s")

# --- 4. Collision Probability Audit ---
log("\n--- 4. Collision Probability Audit ---")
log(f"  Nominal Pc                    : {nom['collision_probability']:.6e}")
log(f"  Nominal log10(Pc)             : {nom['collision_log10_pc']:.4f}")
log(f"  Nominal Pc Status             : {nom['pc_status']}")
log(f"  Nominal Risk Classification   : {nom['risk_classification']}")
log(f"  Post-Manoeuvre Pc             : {post['new_collision_probability']:.6e}")
log(f"  Post-Manoeuvre log10(Pc)      : {post['new_collision_log10_pc']:.4f}")
log(f"  Post-Manoeuvre Pc Status      : {post['pc_status']}")
log(f"  Post-Manoeuvre Risk Class     : {post['risk_classification']}")

import math
nom_expected_pc = 10.0 ** nom['collision_log10_pc']
post_expected_pc = 10.0 ** post['new_collision_log10_pc']
log(f"\n  Consistency Check:")
log(f"    Nominal: 10^({nom['collision_log10_pc']:.4f}) = {nom_expected_pc:.6e} vs Pc = {nom['collision_probability']:.6e} (Ratio: {nom_expected_pc / nom['collision_probability']:.4f})")
log(f"    Post   : 10^({post['new_collision_log10_pc']:.4f}) = {post_expected_pc:.6e} vs Pc = {post['new_collision_probability']:.6e} (Ratio: {post_expected_pc / post['new_collision_probability']:.4f})")

# --- 5. Interactive Simulation Controls Verification ---
log("\n--- 5. Interactive Controls & State Machine Verification ---")

# Reset
sim_mgr.reset_simulation()
log(f"  ResetSimulation: t={sim_mgr.current_simulation_time:.1f}s, playing={sim_mgr.is_playing}, step={sim_mgr.current_step_index}, man_exec={sim_mgr.manoeuvre_executed}")

# Play/Pause
sim_mgr.toggle_play_pause()
log(f"  TogglePlayPause -> is_playing={sim_mgr.is_playing} (Expected: False)")
sim_mgr.toggle_play_pause()
log(f"  TogglePlayPause -> is_playing={sim_mgr.is_playing} (Expected: True)")

# Speed Tiers
speeds_tested = []
sim_mgr.set_time_dilation(1.0)
speeds_tested.append(sim_mgr.time_dilation)
for _ in range(7):
    sim_mgr.increase_speed()
    speeds_tested.append(sim_mgr.time_dilation)
log(f"  IncreaseSpeed ladder: {speeds_tested}")

speeds_decreased = []
for _ in range(7):
    sim_mgr.decrease_speed()
    speeds_decreased.append(sim_mgr.time_dilation)
log(f"  DecreaseSpeed ladder: {speeds_decreased}")

# Step navigation
sim_mgr.jump_to_step(1)
log(f"  JumpToStep(1) -> Step {sim_mgr.current_step_index}")
sim_mgr.step_forward()
log(f"  StepForward() -> Step {sim_mgr.current_step_index} (Expected: 2)")
sim_mgr.step_forward()
log(f"  StepForward() -> Step {sim_mgr.current_step_index} (Expected: 3)")
sim_mgr.step_backward()
log(f"  StepBackward() -> Step {sim_mgr.current_step_index} (Expected: 2)")

# Camera Switching
log(f"\n--- 6. Camera View Switching Test ---")
for i in range(len(cameras)):
    sim_mgr.cycle_camera_view()
    log(f"  CycleCameraView: Current Camera Index = {sim_mgr.current_camera_index} / {len(cameras)}")

for s_idx in range(1, 9):
    sim_mgr.set_camera_for_step(s_idx)
    log(f"  SetCameraForStep({s_idx}): Camera Index = {sim_mgr.current_camera_index}")

# Final Reset and Exit
sim_mgr.reset_simulation()
log("\n" + "=" * 85)
log("[READ-ONLY AUDIT] Validation complete! File written successfully.")
log("=" * 85)
log_f.close()
unreal.SystemLibrary.execute_console_command(None, "QUIT_EDITOR")
