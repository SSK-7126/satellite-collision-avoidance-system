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
all_actors = unreal.EditorLevelLibrary.get_all_level_actors()

# Ensure payload is initialized so orbits and actors are positioned
mgrs = [a for a in all_actors if isinstance(a, unreal.OrbitSimulationManager)]
if mgrs:
    sim_mgr = mgrs[0]
    payload_path = (unreal.Paths.project_dir() + "../D2/visualization/unreal_simulation_payload.json").replace("\\\\", "/")
    sim_mgr.initialize_simulation_from_payload(payload_path)
    sim_mgr.jump_to_step(1)

# Ensure directional light is properly illuminating Earth from the encounter angle
for a in all_actors:
    if isinstance(a, unreal.DirectionalLight):
        comp = a.get_component_by_class(unreal.DirectionalLightComponent)
        comp.set_editor_property("intensity", 14.0)
        a.set_actor_rotation(unreal.Rotator(pitch=-30.0, yaw=-60.0, roll=0.0), False)
        print("Set DirectionalLight rotation and intensity.")
    elif isinstance(a, unreal.SkyLight):
        comp = a.get_component_by_class(unreal.SkyLightComponent)
        comp.set_editor_property("intensity", 2.0)

out_dir = (unreal.Paths.project_saved_dir() + "Screenshots/WindowsEditor").replace("\\\\", "/")
os.makedirs(out_dir, exist_ok=True)

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

# View 1: Earth Overview with Orbit Tracks in Space
cam_loc_1 = unreal.Vector(115000.0, -45000.0, 32000.0)
cam_rot_1 = unreal.Rotator(roll=0.0, pitch=-19.0, yaw=152.0)
capture("Earth_Realistic_Overview", cam_loc_1, cam_rot_1, fov=65.0)

# View 2: Orbital Encounter Vantage (Satellite distinct from Earth)
sat_pos = unreal.Vector(70000.0, 0.0, 0.0)
cam_loc_2 = unreal.Vector(70700.0, -700.0, 350.0)
cam_rot_2 = look_at(cam_loc_2, sat_pos)
capture("Earth_Orbital_SatelliteView", cam_loc_2, cam_rot_2, fov=48.0)

# View 3: Atmospheric Limb close-up
cam_loc_3 = unreal.Vector(68000.0, -15000.0, 8000.0)
cam_rot_3 = look_at(cam_loc_3, unreal.Vector(60000.0, -5000.0, 2000.0))
capture("Earth_Atmosphere_Limb", cam_loc_3, cam_rot_3, fov=50.0)

print("All visual verification captures completed.")
"""

res = remote.run_command(script)
for out in res.get("output", []):
    print(out.get("output"))

remote.stop()

