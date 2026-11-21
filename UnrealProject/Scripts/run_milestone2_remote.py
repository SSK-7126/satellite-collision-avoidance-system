import sys
import time
import os
import shutil

sys.path.append(r"C:\Program Files\Epic Games\UE_5.7\Engine\Plugins\Experimental\PythonScriptPlugin\Content\Python")
import remote_execution

class Config(remote_execution.RemoteExecutionConfig):
    def __init__(self):
        super().__init__()
        self.multicast_bind_address = '0.0.0.0'

print("Connecting to live Unreal Engine 5.7.4 GUI instance...")
remote = remote_execution.RemoteExecution(Config())
remote.start()
time.sleep(1.0)

if not remote.remote_nodes:
    print("ERROR: No remote execution nodes discovered!")
    sys.exit(1)

node = remote.remote_nodes[0]
print(f"Connected to node: {node['node_id']} ({node['engine_version']})")
remote.open_command_connection(node['node_id'])

remote_script = """
import unreal
import json
import os
import math
import time

print("=" * 70)
print("[REMOTE MILESTONE 2] Starting live execution inside UE5 GUI...")
print("=" * 70)

# 1. Load Simulation Payload
payload_path = (unreal.Paths.project_dir() + "../D2/visualization/unreal_simulation_payload.json").replace("\\\\", "/")
with open(payload_path, "r", encoding="utf-8") as f:
    payload = json.load(f)

print(f"[PAYLOAD] Loaded scenario: {payload['scenario_metadata']['scenario_id']}")
print(f"[PAYLOAD] Duration: {payload['scenario_metadata']['duration_sec']}s, Samples: {payload['scenario_metadata']['num_samples']}")
print(f"[PAYLOAD] Nominal TCA: {payload['nominal_encounter']['tca_seconds']:.2f}s, Miss: {payload['nominal_encounter']['miss_distance_m']:.1f}m")
print(f"[PAYLOAD] Selected Manoeuvre: {payload['selected_manoeuvre']['manoeuvre_id']} (dv = {payload['selected_manoeuvre']['delta_v_magnitude_mps']:.2f} m/s)")

# 2. Ensure level is loaded
level_path = "/Game/Scenarios/CollisionAvoidanceDemo"
unreal.EditorLevelLibrary.load_level(level_path)
world = unreal.EditorLevelLibrary.get_editor_world()
all_actors = unreal.EditorLevelLibrary.get_all_level_actors()

# 3. Find Core Actors
earth_actor = None
sat_actor = None
debris_actor = None
sim_mgr = None
dir_light = None
sky_light = None
sat_nominal_path = None
debris_path = None
sat_modified_path = None
conj_viz = None
man_viz = None

for a in all_actors:
    aname = a.get_actor_label()
    if isinstance(a, unreal.EarthActor):
        earth_actor = a
    elif isinstance(a, unreal.SatelliteActor):
        sat_actor = a
    elif isinstance(a, unreal.DebrisActor):
        debris_actor = a
    elif isinstance(a, unreal.OrbitSimulationManager):
        sim_mgr = a
    elif isinstance(a, unreal.DirectionalLight):
        dir_light = a
    elif isinstance(a, unreal.SkyLight):
        sky_light = a
    elif isinstance(a, unreal.ConjunctionVisualizer):
        conj_viz = a
    elif isinstance(a, unreal.ManoeuvreVisualizer):
        man_viz = a
    elif isinstance(a, unreal.OrbitPathActor):
        if "Debris" in aname:
            debris_path = a
        elif "Modified" in aname:
            sat_modified_path = a
        else:
            sat_nominal_path = a

print(f"[ACTORS] Earth: {earth_actor is not None}, Sat: {sat_actor is not None}, Debris: {debris_actor is not None}")
print(f"[ACTORS] ConjViz: {conj_viz is not None}, ManViz: {man_viz is not None}")
print(f"[ACTORS] Paths: Nom={sat_nominal_path is not None}, Deb={debris_path is not None}, Mod={sat_modified_path is not None}")

# 4. Clean up terrestrial landscape / fog artifacts
for a in list(all_actors):
    cname = a.get_class().get_name()
    if "Landscape" in cname or cname in ["VolumetricCloud", "ExponentialHeightFog"]:
        a.set_actor_hidden_in_game(True)
    elif isinstance(a, unreal.SkyAtmosphere):
        a.set_actor_hidden_in_game(True)
    elif a.get_actor_label() == "SM_SkySphere":
        m_space = unreal.EditorAssetLibrary.load_asset("/Game/Earth/M_SpaceSky")
        sm_comp = a.get_component_by_class(unreal.StaticMeshComponent)
        if sm_comp and m_space:
            sm_comp.set_material(0, m_space)

# 5. Configure Lighting
if dir_light:
    comp = dir_light.get_component_by_class(unreal.DirectionalLightComponent)
    comp.set_editor_property("intensity", 14.0)
    dir_light.set_actor_rotation(unreal.Rotator(pitch=-22.0, yaw=148.0, roll=0.0), False)

if sky_light:
    comp = sky_light.get_component_by_class(unreal.SkyLightComponent)
    comp.set_editor_property("intensity", 2.2)

# 6. Apply Materials to Earth
if earth_actor:
    m_earth = unreal.EditorAssetLibrary.load_asset("/Game/Earth/M_Earth")
    m_atmo = unreal.EditorAssetLibrary.load_asset("/Game/Earth/M_Atmosphere")
    t_earth = unreal.EditorAssetLibrary.load_asset("/Game/Earth/T_Earth_Day")
    em = earth_actor.get_editor_property("earth_mesh")
    atm = earth_actor.get_editor_property("atmosphere_mesh")
    if em and m_earth:
        dyn_earth = em.create_dynamic_material_instance(0, m_earth)
        if dyn_earth and t_earth:
            dyn_earth.set_texture_parameter_value("EarthTexture", t_earth)
        em.set_material(0, dyn_earth)
    if atm and m_atmo:
        dyn_atmo = atm.create_dynamic_material_instance(0, m_atmo)
        if dyn_atmo:
            dyn_atmo.set_vector_parameter_value("AtmosphereColor", unreal.LinearColor(0.2, 0.65, 1.0, 1.0))
            dyn_atmo.set_scalar_parameter_value("AtmosphereIntensity", 2.2)
            dyn_atmo.set_scalar_parameter_value("AtmosphereFresnelExp", 4.5)
        atm.set_material(0, dyn_atmo)
        atm.set_relative_scale3d(unreal.Vector(1.015, 1.015, 1.015))
        atm.set_visibility(True)
        atm.set_hidden_in_game(False)
    print("[EARTH] Configured realistic Earth & atmosphere rim.")

# 7. Apply Satellite C++ Materials
if sat_actor:
    sat_actor.apply_satellite_materials()
    print("[SATELLITE] Applied C++ spacecraft materials (Gold bus, Blue panels, Silver metal, Sensor, Thruster).")

# 8. Apply Debris C++ Materials
if debris_actor:
    debris_actor.apply_debris_materials()
    print("[DEBRIS] Applied C++ debris materials (Metallic fragment shards & Hazard orange facet).")

# 9. Extract & Build Trajectories
sat_nom_raw = payload["time_series"]["satellite_nominal_positions_ue"]
deb_raw = payload["time_series"]["debris_positions_ue"]
sat_mod_raw = payload["time_series"]["satellite_modified_positions_ue"]

sat_nom_pts = [unreal.Vector(p[0], p[1], p[2]) for p in sat_nom_raw]
debris_pts = [unreal.Vector(p[0], p[1], p[2]) for p in deb_raw]
sat_mod_pts = [unreal.Vector(p[0], p[1], p[2]) for p in sat_mod_raw]

if sim_mgr:
    sim_mgr.initialize_simulation_from_payload(payload_path)

if sat_nominal_path:
    sat_nominal_path.set_editor_property("path_thickness", 25.0)
    sat_nominal_path.set_trajectory_points(sat_nom_pts, unreal.LinearColor(0.0, 0.85, 1.0, 1.0))
    sat_nominal_path.set_actor_hidden_in_game(False)

if debris_path:
    debris_path.set_editor_property("path_thickness", 25.0)
    debris_path.set_trajectory_points(debris_pts, unreal.LinearColor(1.0, 0.15, 0.1, 1.0))
    debris_path.set_actor_hidden_in_game(False)

if sat_modified_path:
    sat_modified_path.set_editor_property("path_thickness", 25.0)
    sat_modified_path.set_trajectory_points(sat_mod_pts, unreal.LinearColor(0.15, 1.0, 0.35, 1.0))
    sat_modified_path.set_actor_hidden_in_game(False)

print(f"[TRAJECTORIES] Built Cyan ({len(sat_nom_pts)} pts), Red ({len(debris_pts)} pts), Green ({len(sat_mod_pts)} pts) spline meshes.")

# 10. Configure Conjunction Geometry
nom_tca_s = payload["nominal_encounter"]["tca_seconds"]
ts = payload["time_series"]["timestamps_sec"]
tca_idx = min(range(len(ts)), key=lambda i: abs(ts[i] - nom_tca_s))
sat_tca_pos = sat_nom_pts[tca_idx]
deb_tca_pos = debris_pts[tca_idx]
miss_dist_uu = payload["nominal_encounter"]["miss_distance_m"] * payload["scenario_metadata"]["scale_factor_uu_per_m"]

if conj_viz:
    conj_viz.update_conjunction_geometry(sat_tca_pos, deb_tca_pos, miss_dist_uu)
    conj_viz.set_actor_hidden_in_game(False)
    print(f"[CONJUNCTION] Configured at TCA t={nom_tca_s:.1f}s, Miss={miss_dist_uu:.2f} uu ({payload['nominal_encounter']['miss_distance_m']:.1f} m).")

# 11. Configure Manoeuvre Geometry
burn_epoch_s = payload["selected_manoeuvre"]["burn_epoch_seconds"]
burn_loc = unreal.Vector(*payload["selected_manoeuvre"]["satellite_position_at_burn_ue_uu"])
dv_ue = unreal.Vector(*payload["selected_manoeuvre"]["delta_v_ue_uu"])
dv_mag = payload["selected_manoeuvre"]["delta_v_magnitude_mps"]

if man_viz:
    man_viz.set_manoeuvre_geometry(burn_loc, dv_ue, dv_mag)
    man_viz.set_actor_hidden_in_game(False)
    print(f"[MANOEUVRE] Configured at Burn t={burn_epoch_s:.1f}s, dv={dv_mag} m/s in -R direction.")

unreal.EditorLevelLibrary.save_current_level()

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

unreal.SystemLibrary.execute_console_command(None, "r.TextureStreaming 0")

def capture_view(filename_base, cam_location, cam_rotation, fov=60.0):
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
    print(f"[CAPTURED] {out_dir}/{png_name}")

# Capture 1: Pulled-back Earth Overview showing complete globe in space, atmospheric limb & orbital trajectories
cam_overview_loc = unreal.Vector(115000.0, -45000.0, 32000.0)
cam_overview_rot = unreal.Rotator(roll=0.0, pitch=-19.0, yaw=152.0)
capture_view("Milestone2_Earth_Overview", cam_overview_loc, cam_overview_rot, fov=65.0)

# Capture 2: Dedicated Spacecraft Camera (Golden metallic bus, segmented blue solar arrays, antenna mast/dish, thruster)
sat_pos = sat_nom_pts[0]
if sat_actor:
    sat_actor.set_actor_location_and_rotation(sat_pos, unreal.Rotator(0.0, -90.0, 0.0), False, False)
sat_cam_loc = unreal.Vector(sat_pos.x + 650.0, sat_pos.y - 850.0, sat_pos.z + 450.0)
sat_cam_rot = look_at(sat_cam_loc, sat_pos)
capture_view("Milestone2_Satellite_Detail", sat_cam_loc, sat_cam_rot, fov=42.0)

# Capture 3: Dedicated Debris Camera (Irregular jagged metallic fragment shards & hazard orange accent)
deb_pos = debris_pts[0]
if debris_actor:
    debris_actor.set_actor_location(deb_pos, False, False)
deb_cam_loc = unreal.Vector(deb_pos.x + 450.0, deb_pos.y - 550.0, deb_pos.z + 300.0)
deb_cam_rot = look_at(deb_cam_loc, deb_pos)
capture_view("Milestone2_Debris_Detail", deb_cam_loc, deb_cam_rot, fov=38.0)

# Capture 4: Encounter Framing (Satellite & Debris framed together in orbit at t=0)
mid_enc = unreal.Vector(70000.0, -50.0, 0.0)
enc_cam_loc = unreal.Vector(70000.0 + 1800.0, -50.0 - 2400.0, 1100.0)
enc_cam_rot = look_at(enc_cam_loc, mid_enc)
capture_view("Milestone2_Encounter_Overview", enc_cam_loc, enc_cam_rot, fov=50.0)

# Capture 5: Conjunction TCA View (TCA markers: Amber Satellite & Red Debris, Magenta miss-distance line, Violet encounter disc)
if sat_actor:
    sat_actor.set_actor_location(sat_tca_pos, False, False)
if debris_actor:
    debris_actor.set_actor_location(deb_tca_pos, False, False)

tca_mid = unreal.Vector((sat_tca_pos.x + deb_tca_pos.x) * 0.5, (sat_tca_pos.y + deb_tca_pos.y) * 0.5, (sat_tca_pos.z + deb_tca_pos.z) * 0.5)
tca_cam_loc = unreal.Vector(tca_mid.x + 1400.0, tca_mid.y - 1800.0, tca_mid.z + 900.0)
tca_cam_rot = look_at(tca_cam_loc, tca_mid)
capture_view("Milestone2_Conjunction_TCA", tca_cam_loc, tca_cam_rot, fov=45.0)

# Capture 6: Manoeuvre Burn Location & Delta-V Direction Arrow (Burn ring, trajectory tube, 3.0 m/s arrow in -R direction)
if sat_actor:
    sat_actor.set_actor_location(burn_loc, False, False)

burn_cam_loc = unreal.Vector(burn_loc.x + 850.0, burn_loc.y - 1100.0, burn_loc.z + 550.0)
burn_cam_rot = look_at(burn_cam_loc, burn_loc)
capture_view("Milestone2_Manoeuvre_Burn", burn_cam_loc, burn_cam_rot, fov=48.0)

# Capture 7: Trajectory Divergence (Cyan nominal, Green post-manoeuvre modified, Red debris)
div_cam_loc = unreal.Vector(78000.0, -42000.0, 14000.0)
div_cam_rot = look_at(div_cam_loc, unreal.Vector(62000.0, -32000.0, 0.0))
capture_view("Milestone2_Trajectories_Divergence", div_cam_loc, div_cam_rot, fov=55.0)

# Reset satellite & debris to t=0
if sat_actor:
    sat_actor.set_actor_location_and_rotation(sat_pos, unreal.Rotator(0.0, -90.0, 0.0), False, False)
if debris_actor:
    debris_actor.set_actor_location(deb_pos, False, False)

unreal.EditorLevelLibrary.save_current_level()
print("=" * 70)
print("[REMOTE MILESTONE 2] Successfully finished all tasks, geometry and captures!")
print("=" * 70)
"""

res = remote.run_command(remote_script)
for out in res.get("output", []):
    print(out.get("output"))

remote.stop()
print("Finished remote execution.")
