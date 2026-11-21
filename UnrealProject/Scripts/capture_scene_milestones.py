import sys
import time
import os

sys.path.append(r"C:\Program Files\Epic Games\UE_5.7\Engine\Plugins\Experimental\PythonScriptPlugin\Content\Python")
import remote_execution

remote = remote_execution.RemoteExecution()
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
if not mgrs:
    print("No OrbitSimulationManager found!")
sim_mgr = mgrs[0]

out_dir = (unreal.Paths.project_saved_dir() + "Screenshots/WindowsEditor").replace("\\\\", "/")
os.makedirs(out_dir, exist_ok=True)

# Overview camera placement
cam_loc = unreal.Vector(115000.0, -45000.0, 32000.0)
cam_rot = unreal.Rotator(roll=0.0, pitch=-19.0, yaw=152.0)
unreal.EditorLevelLibrary.set_level_viewport_camera_info(cam_loc, cam_rot)

def capture_frame(filename_base):
    capture_actor = unreal.EditorLevelLibrary.spawn_actor_from_class(unreal.SceneCapture2D, cam_loc, cam_rot)
    if capture_actor:
        comp = capture_actor.get_editor_property("capture_component2d")
        comp.set_editor_property("fov_angle", 65.0)
        rt = unreal.RenderingLibrary.create_render_target2d(world, 1920, 1080, unreal.TextureRenderTargetFormat.RTF_RGBA8)
        comp.set_editor_property("texture_target", rt)
        comp.capture_scene()
        png_name = f"{filename_base}.png"
        unreal.RenderingLibrary.export_render_target(world, rt, out_dir, png_name)
        unreal.EditorLevelLibrary.destroy_actor(capture_actor)
        print(f"Captured: {out_dir}/{png_name}")

# 1. Capture Step 1: Initial orbital setup (Earth, Sat, Debris, Cyan & Red paths)
sim_mgr.jump_to_step(1)
capture_frame("Step1_InitialOrbitSetup")

# 2. Capture Step 4: Conjunction encounter geometry (TCA marker, miss distance connector)
sim_mgr.jump_to_step(4)
capture_frame("Step4_ConjunctionEncounter")

# 3. Capture Step 7: Post-Manoeuvre avoidance trajectory (Green path, Burn ring, Delta-V arrow)
sim_mgr.jump_to_step(7)
capture_frame("Step7_AvoidanceManoeuvre")

# 4. Capture Step 8: Post-Manoeuvre Safe Clearance at TCA
sim_mgr.jump_to_step(8)
capture_frame("Step8_SafeClearance")

# Reset simulation
sim_mgr.reset_simulation()
print("All 4 milestone screenshots captured successfully.")
"""

res = remote.run_command(script)
print("Execution result:")
for out in res.get("output", []):
    print(" ", out.get("output"))

remote.stop()
