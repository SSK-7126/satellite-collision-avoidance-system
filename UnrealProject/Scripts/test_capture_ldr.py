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
out_dir = (unreal.Paths.project_saved_dir() + "Screenshots/WindowsEditor").replace("\\\\", "/")
os.makedirs(out_dir, exist_ok=True)

# Overview camera placement
cam_loc = unreal.Vector(115000.0, -45000.0, 32000.0)
cam_rot = unreal.Rotator(roll=0.0, pitch=-19.0, yaw=152.0)

capture_actor = unreal.EditorLevelLibrary.spawn_actor_from_class(unreal.SceneCapture2D, cam_loc, cam_rot)
comp = capture_actor.get_editor_property("capture_component2d")
comp.set_editor_property("fov_angle", 65.0)
comp.set_editor_property("capture_source", unreal.SceneCaptureSource.SCS_FINAL_COLOR_LDR)

# Enable post process auto exposure
pps = comp.get_editor_property("post_process_settings")
pps.set_editor_property("override_auto_exposure_bias", True)
pps.set_editor_property("auto_exposure_bias", 0.0)
comp.set_editor_property("post_process_settings", pps)

rt = unreal.RenderingLibrary.create_render_target2d(world, 1920, 1080, unreal.TextureRenderTargetFormat.RTF_RGBA8)
comp.set_editor_property("texture_target", rt)

comp.capture_scene()

png_name = "Test_LDR_Capture.png"
unreal.RenderingLibrary.export_render_target(world, rt, out_dir, png_name)
unreal.EditorLevelLibrary.destroy_actor(capture_actor)

print(f"Exported LDR capture: {out_dir}/{png_name}")
"""

res = remote.run_command(script)
for out in res.get("output", []):
    print(out.get("output"))

remote.stop()
