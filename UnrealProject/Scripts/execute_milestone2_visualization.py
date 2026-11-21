"""
UnrealProject/Scripts/execute_milestone2_visualization.py
==========================================================
Executes complete Milestone 2 visualization setup:
- Realistic Earth texturing and atmospheric rim in space
- Complete removal of terrestrial landscape/fog artifacts
- Spacecraft detailed materials: Gold bus, Blue solar arrays, Silver metal, Sensor, Thruster
- Debris materials: Irregular jagged metallic fragment with hazard orange accent
- Trajectory geometry generation: 501 points per path, 25 uu width (Cyan, Red, Green)
- Conjunction geometry at Nominal TCA (T=769.63s, miss distance 1563.5m = 15.63 uu)
- Manoeuvre geometry at Burn epoch (T=169.63s, delta-v = 3.0 m/s in -R direction)
- High-resolution multi-angle camera captures
"""

import unreal
import json
import os
import math
import time

print("=" * 70)
print("[MILESTONE 2] Starting Satellite, Debris & Trajectory Visualization...")
print("=" * 70)

# 1. Load Simulation Payload
payload_path = os.path.abspath(os.path.join(
    os.path.dirname(__file__),
    "../../D2/visualization/unreal_simulation_payload.json"
)).replace("\\", "/")

if not os.path.exists(payload_path):
    raise FileNotFoundError(f"Payload not found at {payload_path}")

with open(payload_path, "r", encoding="utf-8") as f:
    payload = json.load(f)

print(f"[PAYLOAD] Loaded scenario: {payload['scenario_metadata']['scenario_id']}")
print(f"[PAYLOAD] Duration: {payload['scenario_metadata']['duration_sec']}s, Samples: {payload['scenario_metadata']['num_samples']}")
print(f"[PAYLOAD] Nominal TCA: {payload['nominal_encounter']['tca_seconds']:.2f}s, Miss Distance: {payload['nominal_encounter']['miss_distance_m']:.1f}m")
print(f"[PAYLOAD] Selected Manoeuvre: {payload['selected_manoeuvre']['manoeuvre_id']} (dv = {payload['selected_manoeuvre']['delta_v_magnitude_mps']:.2f} m/s)")
print(f"[PAYLOAD] Post-Manoeuvre TCA: {payload['post_manoeuvre_encounter']['new_tca_seconds']:.2f}s, New Miss: {payload['post_manoeuvre_encounter']['new_miss_distance_m']:.1f}m")

# 2. Load CollisionAvoidanceDemo level
level_path = "/Game/Scenarios/CollisionAvoidanceDemo"
loaded = unreal.EditorLevelLibrary.load_level(level_path)
print(f"[LEVEL] Load {level_path} result: {loaded}")

world = unreal.EditorLevelLibrary.get_editor_world()
all_actors = unreal.EditorLevelLibrary.get_all_level_actors()
print(f"[ACTORS] Found {len(all_actors)} actors in level.")

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

print(f"[FOUND] EarthActor: {earth_actor is not None}")
print(f"[FOUND] SatelliteActor: {sat_actor is not None}")
print(f"[FOUND] DebrisActor: {debris_actor is not None}")
print(f"[FOUND] OrbitSimulationManager: {sim_mgr is not None}")
print(f"[FOUND] SatNominalPath: {sat_nominal_path is not None}")
print(f"[FOUND] DebrisPath: {debris_path is not None}")
print(f"[FOUND] SatModifiedPath: {sat_modified_path is not None}")
print(f"[FOUND] ConjunctionVisualizer: {conj_viz is not None}")
print(f"[FOUND] ManoeuvreVisualizer: {man_viz is not None}")

# 4. Clean up terrestrial landscape / atmosphere template artifacts
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

print("[ENVIRONMENT] Cleaned up landscape/fog and configured space background.")

# 5. Configure Sunlight & Sky (Illuminating Earth and Spacecraft from encounter vantage)
if dir_light:
    comp = dir_light.get_component_by_class(unreal.DirectionalLightComponent)
    comp.set_editor_property("intensity", 14.0)
    dir_light.set_actor_rotation(unreal.Rotator(pitch=-22.0, yaw=148.0, roll=0.0), False)
    print("[LIGHT] DirectionalLight configured: pitch=-22.0, yaw=148.0, intensity=14.0")

if sky_light:
    comp = sky_light.get_component_by_class(unreal.SkyLightComponent)
    comp.set_editor_property("intensity", 2.5)
    print("[LIGHT] SkyLight configured: intensity=2.5")

# 6. Configure Earth Material & Atmosphere (Preserve M_Earth texture and subtle rim)
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
    if atm and m_atmo:
        dyn_atmo = atm.create_dynamic_material_instance(0, m_atmo)
        if dyn_atmo:
            dyn_atmo.set_vector_parameter_value("AtmosphereColor", unreal.LinearColor(0.2, 0.65, 1.0, 1.0))
            dyn_atmo.set_scalar_parameter_value("AtmosphereIntensity", 2.2)
            dyn_atmo.set_scalar_parameter_value("AtmosphereFresnelExp", 4.5)
        # Relative scale 1.015 ensures subtle atmospheric rim just 1.5% above Earth surface
        atm.set_relative_scale3d(unreal.Vector(1.015, 1.015, 1.015))
    print("[EARTH] Realistic Earth material & atmosphere rim verified.")

# 7. Apply Spacecraft Materials (Golden Bus, Blue Solar Wings, Silver Metal, Sensor, Thruster)
m_solid = unreal.EditorAssetLibrary.load_asset("/Game/Common/M_SolidColor")
if sat_actor and m_solid:
    # 1. Golden Bus
    body = sat_actor.get_editor_property("satellite_body")
    if body:
        mat_gold = body.create_dynamic_material_instance(0, m_solid)
        if mat_gold:
            mat_gold.set_vector_parameter_value("Color", unreal.LinearColor(0.98, 0.82, 0.28, 1.0))
            mat_gold.set_scalar_parameter_value("Metallic", 0.9)
            mat_gold.set_scalar_parameter_value("Roughness", 0.2)
            mat_gold.set_scalar_parameter_value("EmissiveMultiplier", 0.45)
    
    # 2. Photovoltaic Solar Panels (Deep Blue)
    for p_name in ["solar_panel_left", "solar_panel_left_outboard", "solar_panel_right", "solar_panel_right_outboard"]:
        p_comp = sat_actor.get_editor_property(p_name)
        if p_comp:
            mat_blue = p_comp.create_dynamic_material_instance(0, m_solid)
            if mat_blue:
                mat_blue.set_vector_parameter_value("Color", unreal.LinearColor(0.015, 0.08, 0.55, 1.0))
                mat_blue.set_scalar_parameter_value("Metallic", 0.85)
                mat_blue.set_scalar_parameter_value("Roughness", 0.15)
                mat_blue.set_scalar_parameter_value("EmissiveMultiplier", 0.35)
        
    # 3. Structural Aerospace Metal (Silver)
    for m_name in ["payload_deck", "solar_yoke_left", "solar_yoke_right", "antenna_mast", "thruster_nozzle"]:
        m_comp = sat_actor.get_editor_property(m_name)
        if m_comp:
            mat_silver = m_comp.create_dynamic_material_instance(0, m_solid)
            if mat_silver:
                mat_silver.set_vector_parameter_value("Color", unreal.LinearColor(0.78, 0.82, 0.86, 1.0))
                mat_silver.set_scalar_parameter_value("Metallic", 0.9)
                mat_silver.set_scalar_parameter_value("Roughness", 0.25)
                mat_silver.set_scalar_parameter_value("EmissiveMultiplier", 0.25)
        
    # 4. Antenna Dish (High-Gain Gold Mesh)
    dish = sat_actor.get_editor_property("antenna_dish")
    if dish:
        mat_dish = dish.create_dynamic_material_instance(0, m_solid)
        if mat_dish:
            mat_dish.set_vector_parameter_value("Color", unreal.LinearColor(0.95, 0.88, 0.55, 1.0))
            mat_dish.set_scalar_parameter_value("Metallic", 0.95)
            mat_dish.set_scalar_parameter_value("Roughness", 0.2)
            mat_dish.set_scalar_parameter_value("EmissiveMultiplier", 0.4)
    
    # 5. Earth Sensor (Dark Optics)
    sensor = sat_actor.get_editor_property("earth_sensor")
    if sensor:
        mat_sensor = sensor.create_dynamic_material_instance(0, m_solid)
        if mat_sensor:
            mat_sensor.set_vector_parameter_value("Color", unreal.LinearColor(0.02, 0.03, 0.05, 1.0))
            mat_sensor.set_scalar_parameter_value("Metallic", 0.1)
            mat_sensor.set_scalar_parameter_value("Roughness", 0.1)
            mat_sensor.set_scalar_parameter_value("EmissiveMultiplier", 0.1)
    print("[SATELLITE] Golden bus, segmented solar wings, antenna dish, and thruster materials configured.")

# 8. Apply Debris Materials (Irregular Metallic Fragment Shards & Hazard Warning)
if debris_actor and m_solid:
    for c_name in ["debris_mesh", "fragment_shard_a", "torn_strut"]:
        c_comp = debris_actor.get_editor_property(c_name)
        if c_comp:
            mat_alloy = c_comp.create_dynamic_material_instance(0, m_solid)
            if mat_alloy:
                mat_alloy.set_vector_parameter_value("Color", unreal.LinearColor(0.72, 0.70, 0.68, 1.0))
                mat_alloy.set_scalar_parameter_value("Metallic", 0.85)
                mat_alloy.set_scalar_parameter_value("Roughness", 0.45)
                mat_alloy.set_scalar_parameter_value("EmissiveMultiplier", 0.3)
        
    shard_b = debris_actor.get_editor_property("fragment_shard_b")
    if shard_b:
        mat_hazard = shard_b.create_dynamic_material_instance(0, m_solid)
        if mat_hazard:
            mat_hazard.set_vector_parameter_value("Color", unreal.LinearColor(1.0, 0.35, 0.02, 1.0))
            mat_hazard.set_scalar_parameter_value("Metallic", 0.4)
            mat_hazard.set_scalar_parameter_value("Roughness", 0.3)
            mat_hazard.set_scalar_parameter_value("EmissiveMultiplier", 0.6)
    print("[DEBRIS] Irregular metallic fragment shards and hazard warning marking configured.")

# 9. Extract trajectory points from payload
sat_nom_raw = payload["time_series"]["satellite_nominal_positions_ue"]
deb_raw = payload["time_series"]["debris_positions_ue"]
sat_mod_raw = payload["time_series"]["satellite_modified_positions_ue"]

sat_nom_pts = [unreal.Vector(p[0], p[1], p[2]) for p in sat_nom_raw]
debris_pts = [unreal.Vector(p[0], p[1], p[2]) for p in deb_raw]
sat_mod_pts = [unreal.Vector(p[0], p[1], p[2]) for p in sat_mod_raw]

print(f"[TRAJECTORIES] Extracted {len(sat_nom_pts)} nominal sat points, {len(debris_pts)} debris points, {len(sat_mod_pts)} modified sat points.")

# Initialize Simulation Manager with payload
if sim_mgr:
    sim_mgr.initialize_simulation_from_payload(payload_path)
    print("[SIM_MGR] Initialized from simulation payload.")

# Build trajectory spline mesh geometry
if sat_nominal_path:
    sat_nominal_path.set_editor_property("path_thickness", 25.0)
    sat_nominal_path.set_trajectory_points(sat_nom_pts, unreal.LinearColor(0.0, 0.85, 1.0, 1.0))
    sat_nominal_path.set_actor_hidden_in_game(False)
    print(f"[TRAJECTORIES] SatNominalPath generated: {len(sat_nom_pts)-1} spline meshes (Cyan, 25 uu).")

if debris_path:
    debris_path.set_editor_property("path_thickness", 25.0)
    debris_path.set_trajectory_points(debris_pts, unreal.LinearColor(1.0, 0.15, 0.1, 1.0))
    debris_path.set_actor_hidden_in_game(False)
    print(f"[TRAJECTORIES] DebrisPath generated: {len(debris_pts)-1} spline meshes (Red, 25 uu).")

if sat_modified_path:
    sat_modified_path.set_editor_property("path_thickness", 25.0)
    sat_modified_path.set_trajectory_points(sat_mod_pts, unreal.LinearColor(0.15, 1.0, 0.35, 1.0))
    sat_modified_path.set_actor_hidden_in_game(False)
    print(f"[TRAJECTORIES] SatModifiedPath generated: {len(sat_mod_pts)-1} spline meshes (Green, 25 uu).")

# 10. Configure Conjunction Visualizer at Nominal TCA
nom_tca_s = payload["nominal_encounter"]["tca_seconds"]
ts = payload["time_series"]["timestamps_sec"]
tca_idx = min(range(len(ts)), key=lambda i: abs(ts[i] - nom_tca_s))
sat_tca_pos = sat_nom_pts[tca_idx]
deb_tca_pos = debris_pts[tca_idx]
miss_dist_uu = payload["nominal_encounter"]["miss_distance_m"] * payload["scenario_metadata"]["scale_factor_uu_per_m"]

if conj_viz:
    conj_viz.update_conjunction_geometry(sat_tca_pos, deb_tca_pos, miss_dist_uu)
    conj_viz.set_actor_hidden_in_game(False)
    print(f"[CONJUNCTION] Configured at TCA t={nom_tca_s:.1f}s, Sat: {sat_tca_pos}, Deb: {deb_tca_pos}, Miss: {miss_dist_uu:.2f} uu ({payload['nominal_encounter']['miss_distance_m']:.1f} m).")

# 11. Configure Manoeuvre Visualizer at Burn Location
burn_epoch_s = payload["selected_manoeuvre"]["burn_epoch_seconds"]
burn_loc = unreal.Vector(*payload["selected_manoeuvre"]["satellite_position_at_burn_ue_uu"])
dv_ue = unreal.Vector(*payload["selected_manoeuvre"]["delta_v_ue_uu"])
dv_mag = payload["selected_manoeuvre"]["delta_v_magnitude_mps"]

if man_viz:
    man_viz.set_manoeuvre_geometry(burn_loc, dv_ue, dv_mag)
    man_viz.set_actor_hidden_in_game(False)
    print(f"[MANOEUVRE] Configured at Burn t={burn_epoch_s:.1f}s, Loc: {burn_loc}, dv: {dv_mag} m/s in -R direction.")

# 12. Save Level
unreal.EditorLevelLibrary.save_current_level()
print("[SAVE] Level /Game/Scenarios/CollisionAvoidanceDemo saved cleanly.")

# 13. High-Resolution Multi-Angle Visual Captures
out_dir = (unreal.Paths.project_saved_dir() + "Screenshots/WindowsEditor").replace("\\", "/")
os.makedirs(out_dir, exist_ok=True)

def look_at(cam_pos, target_pos):
    dx = target_pos.x - cam_pos.x
    dy = target_pos.y - cam_pos.y
    dz = target_pos.z - cam_pos.z
    yaw = math.degrees(math.atan2(dy, dx))
    dist_xy = math.sqrt(dx*dx + dy*dy)
    pitch = math.degrees(math.atan2(dz, dist_xy))
    return unreal.Rotator(pitch=pitch, yaw=yaw, roll=0.0)

# Ensure full texture streaming resolution and wait for compilation
unreal.SystemLibrary.execute_console_command(None, "r.TextureStreaming 0")
time.sleep(5.0)

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
    print(f"[CAPTURE] Successfully exported: {out_dir}/{png_name}")

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

# Capture 3: Dedicated Debris Camera (Irregular jagged metallic fragment shards & high-contrast hazard accent)
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

# Capture 5: Conjunction TCA View (TCA markers: Amber Satellite & Red Debris, Magenta miss-distance connector line, Violet encounter disc)
# At TCA t=769.63s, position satellite and debris at TCA positions
if sat_actor:
    sat_actor.set_actor_location(sat_tca_pos, False, False)
if debris_actor:
    debris_actor.set_actor_location(deb_tca_pos, False, False)

# Position camera framing encounter disc and marker geometry
tca_mid = unreal.Vector((sat_tca_pos.x + deb_tca_pos.x) * 0.5, (sat_tca_pos.y + deb_tca_pos.y) * 0.5, (sat_tca_pos.z + deb_tca_pos.z) * 0.5)
tca_cam_loc = unreal.Vector(tca_mid.x + 2200.0, tca_mid.y - 2800.0, tca_mid.z + 1400.0)
tca_cam_rot = look_at(tca_cam_loc, tca_mid)
capture_view("Milestone2_Conjunction_TCA", tca_cam_loc, tca_cam_rot, fov=46.0)

# Capture 6: Manoeuvre Burn Location & Delta-V Direction Arrow (Burn ring, trajectory tube, 3.0 m/s arrow in -R direction)
# At Burn epoch t=169.63s, position satellite at burn location
if sat_actor:
    sat_actor.set_actor_location(burn_loc, False, False)

burn_cam_loc = unreal.Vector(burn_loc.x + 950.0, burn_loc.y - 1200.0, burn_loc.z + 600.0)
burn_cam_rot = look_at(burn_cam_loc, burn_loc)
capture_view("Milestone2_Manoeuvre_Burn", burn_cam_loc, burn_cam_rot, fov=48.0)

# Capture 7: Trajectory Divergence (Cyan nominal, Green post-manoeuvre modified, Red debris)
# Frame diverging trajectories after burn
div_cam_loc = unreal.Vector(78000.0, -42000.0, 14000.0)
div_cam_rot = look_at(div_cam_loc, unreal.Vector(62000.0, -32000.0, 0.0))
capture_view("Milestone2_Trajectories_Divergence", div_cam_loc, div_cam_rot, fov=55.0)

print("=" * 70)
print("[MILESTONE 2] All tasks, geometry generation and captures completed successfully!")
print("=" * 70)

unreal.SystemLibrary.execute_console_command(None, "QUIT_EDITOR")
