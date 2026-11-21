import sys
import time
import os
import math

sys.path.append(r"C:\Program Files\Epic Games\UE_5.7\Engine\Plugins\Experimental\PythonScriptPlugin\Content\Python")
import remote_execution

class Config(remote_execution.RemoteExecutionConfig):
    def __init__(self):
        super().__init__()
        self.multicast_bind_address = '0.0.0.0'

remote = remote_execution.RemoteExecution(Config())
remote.start()
time.sleep(1.0)
node = remote.remote_nodes[0]
remote.open_command_connection(node['node_id'])

script = """
import unreal
import os
import math

world = unreal.EditorLevelLibrary.get_editor_world()
out_dir = (unreal.Paths.project_saved_dir() + "Screenshots/WindowsEditor").replace("\\\\", "/")

def look_at(cam_pos, target_pos):
    dx = target_pos.x - cam_pos.x
    dy = target_pos.y - cam_pos.y
    dz = target_pos.z - cam_pos.z
    yaw = math.degrees(math.atan2(dy, dx))
    dist_xy = math.sqrt(dx*dx + dy*dy)
    pitch = math.degrees(math.atan2(dz, dist_xy))
    return unreal.Rotator(pitch=pitch, yaw=yaw, roll=0.0)

def capture(filename_base, cam_location, cam_rotation, fov=60.0):
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

# Camera at (72500, 300, 250), looking directly at satellite (70000, 0, 0) and Earth (0, 0, 0)
cam_loc = unreal.Vector(72200.0, 350.0, 250.0)
sat_pos = unreal.Vector(70000.0, 0.0, 0.0)
cam_rot = look_at(cam_loc, sat_pos)
capture("Earth_Orbital_SatelliteView", cam_loc, cam_rot, fov=65.0)

# Also let's re-save level
unreal.EditorLevelLibrary.save_current_level()
"""

res = remote.run_command(script)
for out in res.get("output", []):
    print(out.get("output"))

remote.stop()

