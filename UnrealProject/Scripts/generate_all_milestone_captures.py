import sys
import time
import os

sys.path.append(r"C:\Program Files\Epic Games\UE_5.7\Engine\Plugins\Experimental\PythonScriptPlugin\Content\Python")
import remote_execution

class Config(remote_execution.RemoteExecutionConfig):
    def __init__(self):
        super().__init__()
        self.multicast_bind_address = '0.0.0.0'

remote = remote_execution.RemoteExecution(Config())
remote.start()
time.sleep(1.0)

if not remote.remote_nodes:
    print("No remote node found!")
    sys.exit(1)

node = remote.remote_nodes[0]
remote.open_command_connection(node["node_id"])

script = """
import unreal
import os

world = unreal.EditorLevelLibrary.get_editor_world()
all_actors = unreal.EditorLevelLibrary.get_all_level_actors()

mgrs = [a for a in all_actors if isinstance(a, unreal.OrbitSimulationManager)]
sim_mgr = mgrs[0]

# Initialize simulation payload to ensure all paths and visualizers are built
payload_path = (unreal.Paths.project_dir() + "../D2/visualization/unreal_simulation_payload.json").replace("\\\\", "/")
sim_mgr.initialize_simulation_from_payload(payload_path)

out_dir = (unreal.Paths.project_saved_dir() + "Screenshots/WindowsEditor").replace("\\\\", "/")
os.makedirs(out_dir, exist_ok=True)

# Overview camera vantage point
cam_loc = unreal.Vector(115000.0, -45000.0, 32000.0)
cam_rot = unreal.Rotator(roll=0.0, pitch=-19.0, yaw=152.0)

# Set sunlight rotation for optimal illumination
for a in all_actors:
    if isinstance(a, unreal.DirectionalLight):
        comp = a.get_component_by_class(unreal.DirectionalLightComponent)
        comp.set_editor_property("intensity", 12.0)
        a.set_actor_rotation(unreal.Rotator(pitch=-22.0, yaw=148.0, roll=0.0), False)
    elif isinstance(a, unreal.SkyLight):
        comp = a.get_component_by_class(unreal.SkyLightComponent)
        comp.set_editor_property("intensity", 2.0)

def capture_scene(filename_base, cam_location=cam_loc, cam_rotation=cam_rot, fov=65.0):
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

# Milestone 1: T+0s Initial Orbit
sim_mgr.jump_to_step(1)
capture_scene("Step1_InitialOrbitSetup")

# Close-up of Satellite & Debris at T+0s
sat_loc = unreal.Vector(70000.0, 0.0, 0.0)
sat_cam_loc = unreal.Vector(70800.0, -800.0, 400.0)
sat_cam_rot = unreal.Rotator(roll=0.0, pitch=-22.0, yaw=140.0)
capture_scene("Step1_SatelliteDetail", sat_cam_loc, sat_cam_rot, fov=50.0)

# Milestone 4: T+150s Conjunction Screening & Encounter Geometry
sim_mgr.jump_to_step(4)
capture_scene("Step4_ConjunctionEncounter")

# Milestone 6: T+169.6s Impulsive Burn Execution
sim_mgr.jump_to_step(6)
burn_cam_loc = unreal.Vector(71000.0, -13500.0, 1200.0)
burn_cam_rot = unreal.Rotator(roll=0.0, pitch=-25.0, yaw=150.0)
capture_scene("Step6_BurnExecution", burn_cam_loc, burn_cam_rot, fov=55.0)

# Milestone 7: T+300s Avoidance Trajectory Divergence (Green vs Red paths)
sim_mgr.jump_to_step(7)
capture_scene("Step7_AvoidanceManoeuvre")

# Milestone 8: T+903s Safe Clearance Verification
sim_mgr.jump_to_step(8)
capture_scene("Step8_SafeClearance")

# Reset simulation back to initial state
sim_mgr.reset_simulation()
unreal.EditorLevelLibrary.save_current_level()
print("All demonstration milestone captures completed and level saved.")
"""

res = remote.run_command(script)
for out in res.get("output", []):
    print(out.get("output"))

remote.stop()
