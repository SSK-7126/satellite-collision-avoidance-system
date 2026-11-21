import sys
import time
import os
import math

sys.path.append(r"C:\Program Files\Epic Games\UE_5.7\Engine\Plugins\Experimental\PythonScriptPlugin\Content\Python")
import remote_execution

print("Connecting to Unreal Engine remote execution...")
remote = remote_execution.RemoteExecution()
remote.start()

# Retry connection until editor is ready
connected = False
for attempt in range(30):
    time.sleep(2.0)
    if remote.remote_nodes:
        node = remote.remote_nodes[0]
        remote.open_command_connection(node["node_id"])
        print(f"Connected to Unreal Engine node: {node['node_id']}")
        connected = True
        break
    print(f"Waiting for UnrealEditor... ({attempt+1}/30)")

if not connected:
    print("Could not connect to UnrealEditor.")
    sys.exit(1)

script = """
import unreal
import os
import math

world = unreal.EditorLevelLibrary.get_editor_world()
all_actors = unreal.EditorLevelLibrary.get_all_level_actors()

mgrs = [a for a in all_actors if isinstance(a, unreal.OrbitSimulationManager)]
if not mgrs:
    print("No OrbitSimulationManager found!")
sim_mgr = mgrs[0]

# Ensure payload is loaded
payload_path = (unreal.Paths.project_dir() + "../D2/visualization/unreal_simulation_payload.json").replace("\\\\", "/")
sim_mgr.initialize_simulation_from_payload(payload_path)

out_dir = (unreal.Paths.project_saved_dir() + "Screenshots/WindowsEditor").replace("\\\\", "/")
os.makedirs(out_dir, exist_ok=True)

# Lighting setup
for a in all_actors:
    if isinstance(a, unreal.DirectionalLight):
        comp = a.get_component_by_class(unreal.DirectionalLightComponent)
        comp.set_editor_property("intensity", 12.0)
        a.set_actor_rotation(unreal.Rotator(pitch=-35.0, yaw=-65.0, roll=0.0), False)
    elif isinstance(a, unreal.SkyLight):
        comp = a.get_component_by_class(unreal.SkyLightComponent)
        comp.set_editor_property("intensity", 4.0)

def look_at(cam_pos, target_pos):
    dx = target_pos.x - cam_pos.x
    dy = target_pos.y - cam_pos.y
    dz = target_pos.z - cam_pos.z
    yaw = math.degrees(math.atan2(dy, dx))
    dist_xy = math.sqrt(dx*dx + dy*dy)
    pitch = math.degrees(math.atan2(dz, dist_xy))
    return unreal.Rotator(pitch=pitch, yaw=yaw, roll=0.0)

def capture_scene(filename_base, cam_location, cam_rotation, fov=65.0):
    capture_actor = unreal.EditorLevelLibrary.spawn_actor_from_class(unreal.SceneCapture2D, cam_location, cam_rotation)
    comp = capture_actor.get_editor_property("capture_component2d")
    comp.set_editor_property("fov_angle", fov)
    comp.set_editor_property("capture_source", unreal.SceneCaptureSource.SCS_FINAL_COLOR_LDR)
    
    pps = comp.get_editor_property("post_process_settings")
    pps.set_editor_property("override_auto_exposure_bias", True)
    pps.set_editor_property("auto_exposure_bias", 0.0)
    comp.set_editor_property("post_process_settings", pps)

    rt = unreal.RenderingLibrary.create_render_target2d(world, 1920, 1080, unreal.TextureRenderTargetFormat.RTF_RGBA8)
    comp.set_editor_property("texture_target", rt)
    comp.capture_scene()

    png_name = f"{filename_base}.png"
    unreal.RenderingLibrary.export_render_target(world, rt, out_dir, png_name)
    unreal.EditorLevelLibrary.destroy_actor(capture_actor)
    print(f"Captured: {out_dir}/{png_name}")

# 1. Milestone 1: Earth Overview
sim_mgr.jump_to_step(1)
cam_loc_overview = unreal.Vector(115000.0, -45000.0, 32000.0)
cam_rot_overview = unreal.Rotator(roll=0.0, pitch=-19.0, yaw=152.0)
capture_scene("Step1_InitialOrbitSetup", cam_loc_overview, cam_rot_overview, fov=65.0)

# 2. Milestone 1: Satellite Close-Up
sat_pos_0 = unreal.Vector(70000.0, 0.0, 0.0)
cam_loc_sat = unreal.Vector(70600.0, -600.0, 350.0)
cam_rot_sat = look_at(cam_loc_sat, sat_pos_0)
capture_scene("Step1_SatelliteDetail", cam_loc_sat, cam_rot_sat, fov=45.0)

# 3. Milestone 4: Conjunction Encounter (TCA = 769.6s)
sim_mgr.jump_to_step(4)
tca_sat_pos = unreal.Vector(47237.9, -51658.3, 0.0)
cam_loc_tca = unreal.Vector(47237.9 + 50.0, -51658.3 - 50.0, 30.0)
cam_rot_tca = look_at(cam_loc_tca, tca_sat_pos)
capture_scene("Step4_ConjunctionEncounter", cam_loc_tca, cam_rot_tca, fov=50.0)

# 4. Milestone 6: Impulsive Burn Execution (t = 169.6s)
sim_mgr.jump_to_step(6)
burn_sat_pos = unreal.Vector(68827.8, -12756.6, 0.0)
cam_loc_burn = unreal.Vector(68827.8 + 60.0, -12756.6 - 60.0, 30.0)
cam_rot_burn = look_at(cam_loc_burn, burn_sat_pos)
capture_scene("Step6_BurnExecution", cam_loc_burn, cam_rot_burn, fov=50.0)

# 5. Milestone 7: Avoidance Trajectory Divergence (t = 300s)
sim_mgr.jump_to_step(7)
cam_loc_m7 = unreal.Vector(65000.0, -28000.0, 6000.0)
cam_rot_m7 = look_at(cam_loc_m7, unreal.Vector(62000.0, -32000.0, 0.0))
capture_scene("Step7_AvoidanceManoeuvre", cam_loc_m7, cam_rot_m7, fov=55.0)

# 6. Milestone 8: Safe Clearance Verification (t = 903s)
sim_mgr.jump_to_step(8)
cam_loc_m8 = unreal.Vector(42000.0, -58000.0, 8000.0)
cam_rot_m8 = look_at(cam_loc_m8, unreal.Vector(38000.0, -60000.0, 0.0))
capture_scene("Step8_SafeClearance", cam_loc_m8, cam_rot_m8, fov=55.0)

# Reset simulation
sim_mgr.reset_simulation()
print("Scene captures finished successfully.")
"""

res = remote.run_command(script)
for out in res.get("output", []):
    print(out.get("output"))

remote.stop()

