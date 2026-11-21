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

# 1. Position camera overlooking the encounter and Earth
camera_loc = unreal.Vector(95000.0, -35000.0, 25000.0)
camera_rot = unreal.Rotator(roll=0.0, pitch=-18.0, yaw=148.0)
unreal.EditorLevelLibrary.set_level_viewport_camera_info(camera_loc, camera_rot)
unreal.EditorLevelLibrary.editor_invalidate_viewports()

# 2. Set up screenshot output path
out_dir = unreal.Paths.project_saved_dir() + "Screenshots/WindowsEditor/"
if not os.path.exists(out_dir):
    os.makedirs(out_dir, exist_ok=True)

shot_file = out_dir + "CollisionAvoidanceDemo_Viewport.png"
print(f"Target screenshot path: {shot_file}")

# 3. Take screenshot via AutomationLibrary or Console Command
world = unreal.EditorLevelLibrary.get_editor_world()
task = unreal.AutomationLibrary.take_high_res_screenshot(
    1280, 720,
    shot_file,
    camera=None,
    mask_enabled=False,
    capture_hdr=False,
    delay=0.0,
    force_game_view=False
)
print("Screenshot task submitted:", task)

# Also trigger HighResShot console command
unreal.SystemLibrary.execute_console_command(world, f"HighResShot 1280x720 filename=\\"{shot_file}\\"")
print("HighResShot command executed.")
"""

res = remote.run_command(script)
print("Execution result:")
for out in res.get("output", []):
    print(" ", out.get("output"))

remote.stop()

