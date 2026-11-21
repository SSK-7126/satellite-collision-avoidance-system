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
if not remote.remote_nodes:
    print("ERROR: No remote execution nodes discovered!")
    sys.exit(1)

node = remote.remote_nodes[0]
print(f"Connecting to node: {node['node_id']} ({node['engine_version']})")
remote.open_command_connection(node['node_id'])

script = """
import unreal
import os
import math

world = unreal.EditorLevelLibrary.get_editor_world()
all_actors = unreal.EditorLevelLibrary.get_all_level_actors()

# 1. Update Directional Light to illuminate Earth from the camera view
for a in all_actors:
    if isinstance(a, unreal.DirectionalLight):
        comp = a.get_component_by_class(unreal.DirectionalLightComponent)
        comp.set_editor_property("intensity", 12.0)
        # Point towards Earth from the encounter/camera hemisphere
        a.set_actor_rotation(unreal.Rotator(pitch=-22.0, yaw=148.0, roll=0.0), False)
        print("DirectionalLight adjusted: pitch=-22.0, yaw=148.0, intensity=12.0")
    elif isinstance(a, unreal.SkyLight):
        comp = a.get_component_by_class(unreal.SkyLightComponent)
        comp.set_editor_property("intensity", 1.8)
        print("SkyLight adjusted: intensity=1.8")

# 2. Check EarthActor materials
earth_actors = [a for a in all_actors if isinstance(a, unreal.EarthActor)]
if earth_actors:
    ea = earth_actors[0]
    mat_earth = unreal.EditorAssetLibrary.load_asset("/Game/Earth/M_Earth")
    mat_atmo = unreal.EditorAssetLibrary.load_asset("/Game/Earth/M_Atmosphere")
    em = ea.get_editor_property("earth_mesh")
    atm = ea.get_editor_property("atmosphere_mesh")
    if em and mat_earth:
        em.set_material(0, mat_earth)
        print("EarthMesh material confirmed: /Game/Earth/M_Earth")
    if atm and mat_atmo:
        atm.set_material(0, mat_atmo)
        # Ensure scale is 1.015
        atm.set_relative_scale3d(unreal.Vector(1.015, 1.015, 1.015))
        print("AtmosphereMesh material confirmed: /Game/Earth/M_Atmosphere, scale 1.015")

# 3. Initialize simulation manager to Step 1
mgrs = [a for a in all_actors if isinstance(a, unreal.OrbitSimulationManager)]
if mgrs:
    sim_mgr = mgrs[0]
    payload_path = (unreal.Paths.project_dir() + "../D2/visualization/unreal_simulation_payload.json").replace("\\\\", "/")
    sim_mgr.initialize_simulation_from_payload(payload_path)
    sim_mgr.jump_to_step(1)
    print("Simulation manager set to Step 1")

# Helper for look-at rotator
def look_at(cam_pos, target_pos):
    dx = target_pos.x - cam_pos.x
    dy = target_pos.y - cam_pos.y
    dz = target_pos.z - cam_pos.z
    yaw = math.degrees(math.atan2(dy, dx))
    dist_xy = math.sqrt(dx*dx + dy*dy)
    pitch = math.degrees(math.atan2(dz, dist_xy))
    return unreal.Rotator(pitch=pitch, yaw=yaw, roll=0.0)

out_dir = (unreal.Paths.project_saved_dir() + "Screenshots/WindowsEditor").replace("\\\\", "/")
os.makedirs(out_dir, exist_ok=True)

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

# View 1: Earth Realistic Overview
# Cam at (115000, -45000, 32000), looking at Earth center (0,0,0)
cam_loc_1 = unreal.Vector(115000.0, -45000.0, 32000.0)
cam_rot_1 = look_at(cam_loc_1, unreal.Vector(0.0, 0.0, 0.0))
capture("Earth_Realistic_Overview", cam_loc_1, cam_rot_1, fov=65.0)

# View 2: Orbital Satellite View with Earth in Background
# Find satellite position
sat_actors = [a for a in all_actors if isinstance(a, unreal.SatelliteActor)]
if sat_actors:
    sat_loc = sat_actors[0].get_actor_location()
    print(f"Satellite location: {sat_loc}")
    # Place camera offset looking towards satellite and Earth behind it
    # Earth is at (0,0,0). Direction from Earth to Sat is sat_loc / sat_dist
    sat_dist = math.sqrt(sat_loc.x**2 + sat_loc.y**2 + sat_loc.z**2)
    radial_u = unreal.Vector(sat_loc.x / sat_dist, sat_loc.y / sat_dist, sat_loc.z / sat_dist)
    
    # Camera placed outside orbit looking back towards satellite and Earth
    cam_loc_2 = unreal.Vector(sat_loc.x + radial_u.x * 2800.0 + 800.0, sat_loc.y + radial_u.y * 2800.0 - 1200.0, sat_loc.z + radial_u.z * 2800.0 + 600.0)
    cam_rot_2 = look_at(cam_loc_2, sat_loc)
    capture("Earth_Orbital_SatelliteView", cam_loc_2, cam_rot_2, fov=50.0)

# View 3: Atmospheric Limb close-up
cam_loc_3 = unreal.Vector(68000.0, -15000.0, 9000.0)
cam_rot_3 = look_at(cam_loc_3, unreal.Vector(60000.0, -4000.0, 1500.0))
capture("Earth_Atmosphere_Limb", cam_loc_3, cam_rot_3, fov=48.0)

# Save the level
unreal.EditorLevelLibrary.save_current_level()
print("Saved CollisionAvoidanceDemo level successfully.")
"""

res = remote.run_command(script)
for out in res.get("output", []):
    print(out.get("output"))

remote.stop()

