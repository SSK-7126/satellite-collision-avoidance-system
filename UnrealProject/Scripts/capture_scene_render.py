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
out_dir = unreal.Paths.project_saved_dir() + "Screenshots/WindowsEditor"
if not os.path.exists(out_dir):
    os.makedirs(out_dir, exist_ok=True)

# 1. Camera location overlooking Earth and the satellite encounter
# Earth is at (0,0,0) with radius 63781 uu. Sat is at (70000, 0, 0).
# Vantage point at (95000, -35000, 25000) looking towards (65000, -10000, 0)
cam_loc = unreal.Vector(95000.0, -35000.0, 25000.0)
cam_rot = unreal.Rotator(roll=0.0, pitch=-22.0, yaw=145.0)

# Set viewport camera as well
unreal.EditorLevelLibrary.set_level_viewport_camera_info(cam_loc, cam_rot)

# Spawn a transient SceneCapture2D actor
capture_actor = unreal.EditorLevelLibrary.spawn_actor_from_class(unreal.SceneCapture2D, cam_loc, cam_rot)
if capture_actor:
    capture_comp = capture_actor.get_editor_property("capture_component2d")
    rt = unreal.RenderingLibrary.create_render_target2d(world, 1920, 1080, unreal.TextureRenderTargetFormat.RTF_RGBA8)
    capture_comp.set_editor_property("texture_target", rt)
    capture_comp.capture_scene()
    
    png_path = os.path.join(out_dir, "CollisionAvoidanceDemo_Viewport.png").replace("\\\\", "/")
    unreal.RenderingLibrary.export_render_target(world, rt, out_dir, "CollisionAvoidanceDemo_Viewport.png")
    print(f"Exported scene capture to: {png_path}")
    
    unreal.EditorLevelLibrary.destroy_actor(capture_actor)
    print("Transient capture actor destroyed.")
"""

res = remote.run_command(script)
print("Execution result:")
for out in res.get("output", []):
    print(" ", out.get("output"))

remote.stop()

