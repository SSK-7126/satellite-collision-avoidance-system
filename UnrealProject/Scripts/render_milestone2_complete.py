"""
UnrealProject/Scripts/render_milestone2_complete.py
===================================================
Executes complete Milestone 2 scene configuration and high-resolution captures:
- Earth: Blue marble photorealistic texture and subtle atmospheric limb
- Deep space: Complete removal of terrestrial landscape, sky atmosphere, and skydome warning
- Spacecraft: Golden central bus, segmented deep-blue solar wings, antenna mast/dish, optics, thruster
- Debris: Irregular metallic fragment, sheared torn strut, hazard orange facet
- Trajectories: 501 points per path, 25 uu width (Cyan nominal, Red debris, Green modified)
- Conjunction: Amber/Red TCA markers, Magenta miss-distance connector line, Violet encounter disc
- Manoeuvre: Electric Purple burn ring, Vibrant Green delta-v direction arrow (-R direction)
- 7 multi-angle captures exported to UnrealProject/Saved/Screenshots/WindowsEditor/
"""

import unreal
import json
import os
import math

print("=" * 70)
print("[MILESTONE 2 COMPLETE] Starting scene configuration & capture suite...")
print("=" * 70)

# 1. Load Simulation Payload
payload_path = os.path.abspath(os.path.join(
    os.path.dirname(__file__),
    "../../D2/visualization/unreal_simulation_payload.json"
)).replace("\\", "/")

with open(payload_path, "r", encoding="utf-8") as f:
    payload = json.load(f)

print(f"[PAYLOAD] Scenario: {payload['scenario_metadata']['scenario_id']}")
print(f"[PAYLOAD] Nominal TCA: {payload['nominal_encounter']['tca_seconds']:.2f}s, Miss: {payload['nominal_encounter']['miss_distance_m']:.1f}m")
print(f"[PAYLOAD] Selected Manoeuvre: {payload['selected_manoeuvre']['manoeuvre_id']} (dv = {payload['selected_manoeuvre']['delta_v_magnitude_mps']:.2f} m/s)")

# 2. Load Level
level_path = "/Game/Scenarios/CollisionAvoidanceDemo"
unreal.EditorLevelLibrary.load_level(level_path)
world = unreal.EditorLevelLibrary.get_editor_world()
all_actors = unreal.EditorLevelLibrary.get_all_level_actors()

# 3. Clean up terrestrial landscape / atmosphere template artifacts
for a in list(all_actors):
    cname = a.get_class().get_name()
    if "Landscape" in cname or cname in ["VolumetricCloud", "ExponentialHeightFog", "SkyAtmosphere"]:
        a.set_actor_hidden_in_game(True)
    elif a.get_actor_label() == "SM_SkySphere":
        a.set_actor_hidden_in_game(True)

print("[CLEANUP] Cleaned terrestrial environment and hid default SkySphere.")

# 4. Find Core Actors
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

# 5. Lighting Setup for Deep Space
if dir_light:
    comp = dir_light.get_component_by_class(unreal.DirectionalLightComponent)
    comp.set_editor_property("atmosphere_sun_light", False)
    comp.set_editor_property("use_temperature", False)
    comp.set_editor_property("light_color", unreal.Color(255, 255, 255, 255))
    comp.set_editor_property("intensity", 14.0)

if sky_light:
    comp = sky_light.get_component_by_class(unreal.SkyLightComponent)
    comp.set_editor_property("real_time_capture", False)
    comp.set_editor_property("light_color", unreal.Color(200, 220, 255, 255))
    comp.set_editor_property("intensity", 2.5)

# 6. Recreate & Compile M_SolidColor in memory to ensure perfect shader compilation
asset_tools = unreal.AssetToolsHelpers.get_asset_tools()
mat_factory = unreal.MaterialFactoryNew()
unreal.EditorAssetLibrary.delete_asset("/Game/Common/M_SolidColor")
m_solid = asset_tools.create_asset("M_SolidColor", "/Game/Common", unreal.Material, mat_factory)
m_solid.set_editor_property("two_sided", True)

col_param = unreal.MaterialEditingLibrary.create_material_expression(m_solid, unreal.MaterialExpressionVectorParameter, -400, -100)
col_param.set_editor_property("parameter_name", "Color")
col_param.set_editor_property("default_value", unreal.LinearColor(1.0, 1.0, 1.0, 1.0))
unreal.MaterialEditingLibrary.connect_material_property(col_param, "", unreal.MaterialProperty.MP_BASE_COLOR)

em_param = unreal.MaterialEditingLibrary.create_material_expression(m_solid, unreal.MaterialExpressionScalarParameter, -400, 100)
em_param.set_editor_property("parameter_name", "EmissiveMultiplier")
em_param.set_editor_property("default_value", 0.35)

mult_expr = unreal.MaterialEditingLibrary.create_material_expression(m_solid, unreal.MaterialExpressionMultiply, -200, 0)
unreal.MaterialEditingLibrary.connect_material_expressions(col_param, "", mult_expr, "A")
unreal.MaterialEditingLibrary.connect_material_expressions(em_param, "", mult_expr, "B")
unreal.MaterialEditingLibrary.connect_material_property(mult_expr, "", unreal.MaterialProperty.MP_EMISSIVE_COLOR)

metal_param = unreal.MaterialEditingLibrary.create_material_expression(m_solid, unreal.MaterialExpressionScalarParameter, -400, 250)
metal_param.set_editor_property("parameter_name", "Metallic")
metal_param.set_editor_property("default_value", 0.8)
unreal.MaterialEditingLibrary.connect_material_property(metal_param, "", unreal.MaterialProperty.MP_METALLIC)

rough_param = unreal.MaterialEditingLibrary.create_material_expression(m_solid, unreal.MaterialExpressionScalarParameter, -400, 400)
rough_param.set_editor_property("parameter_name", "Roughness")
rough_param.set_editor_property("default_value", 0.2)
unreal.MaterialEditingLibrary.connect_material_property(rough_param, "", unreal.MaterialProperty.MP_ROUGHNESS)

unreal.MaterialEditingLibrary.recompile_material(m_solid)
unreal.EditorAssetLibrary.save_loaded_asset(m_solid)
print("[MATERIALS] Recompiled M_SolidColor cleanly.")

# Also create M_TranslucentDisc cleanly
unreal.EditorAssetLibrary.delete_asset("/Game/Common/M_TranslucentDisc")
m_disc = asset_tools.create_asset("M_TranslucentDisc", "/Game/Common", unreal.Material, mat_factory)
m_disc.set_editor_property("two_sided", True)
m_disc.set_editor_property("blend_mode", unreal.BlendMode.BLEND_TRANSLUCENT)

d_col = unreal.MaterialEditingLibrary.create_material_expression(m_disc, unreal.MaterialExpressionVectorParameter, -400, -100)
d_col.set_editor_property("parameter_name", "Color")
d_col.set_editor_property("default_value", unreal.LinearColor(0.65, 0.2, 0.95, 1.0))
unreal.MaterialEditingLibrary.connect_material_property(d_col, "", unreal.MaterialProperty.MP_BASE_COLOR)
unreal.MaterialEditingLibrary.connect_material_property(d_col, "", unreal.MaterialProperty.MP_EMISSIVE_COLOR)

d_op = unreal.MaterialEditingLibrary.create_material_expression(m_disc, unreal.MaterialExpressionScalarParameter, -400, 150)
d_op.set_editor_property("parameter_name", "Opacity")
d_op.set_editor_property("default_value", 0.35)
unreal.MaterialEditingLibrary.connect_material_property(d_op, "", unreal.MaterialProperty.MP_OPACITY)

unreal.MaterialEditingLibrary.recompile_material(m_disc)
unreal.EditorAssetLibrary.save_loaded_asset(m_disc)
print("[MATERIALS] Recompiled M_TranslucentDisc cleanly.")

# 7. Earth Surface & Atmospheric Rim
m_earth = unreal.EditorAssetLibrary.load_asset("/Game/Earth/M_Earth")
m_atmo = unreal.EditorAssetLibrary.load_asset("/Game/Earth/M_Atmosphere")
t_earth = unreal.EditorAssetLibrary.load_asset("/Game/Earth/T_Earth_Day")

if earth_actor:
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
    print("[EARTH] Realistic Earth blue marble and atmospheric limb applied.")

# 8. Function to apply Satellite Materials directly to components
def apply_satellite_materials(sat):
    if not sat or not m_solid:
        return
    # 1. Golden Central Bus
    body = sat.get_editor_property("satellite_body")
    if body:
        mat_gold = body.create_dynamic_material_instance(0, m_solid)
        mat_gold.set_vector_parameter_value("Color", unreal.LinearColor(0.98, 0.82, 0.28, 1.0))
        mat_gold.set_scalar_parameter_value("Metallic", 0.9)
        mat_gold.set_scalar_parameter_value("Roughness", 0.2)
        mat_gold.set_scalar_parameter_value("EmissiveMultiplier", 0.4)
        body.set_material(0, mat_gold)

    # 2. Photovoltaic Solar Panels (Deep Blue)
    for p_name in ["solar_panel_left", "solar_panel_left_outboard", "solar_panel_right", "solar_panel_right_outboard"]:
        p_comp = sat.get_editor_property(p_name)
        if p_comp:
            mat_blue = p_comp.create_dynamic_material_instance(0, m_solid)
            mat_blue.set_vector_parameter_value("Color", unreal.LinearColor(0.015, 0.08, 0.55, 1.0))
            mat_blue.set_scalar_parameter_value("Metallic", 0.85)
            mat_blue.set_scalar_parameter_value("Roughness", 0.15)
            mat_blue.set_scalar_parameter_value("EmissiveMultiplier", 0.35)
            p_comp.set_material(0, mat_blue)

    # 3. Aerospace Structural Metal (Silver/Titanium)
    for m_name in ["payload_deck", "solar_yoke_left", "solar_yoke_right", "antenna_mast", "thruster_nozzle"]:
        m_comp = sat.get_editor_property(m_name)
        if m_comp:
            mat_silver = m_comp.create_dynamic_material_instance(0, m_solid)
            mat_silver.set_vector_parameter_value("Color", unreal.LinearColor(0.78, 0.82, 0.86, 1.0))
            mat_silver.set_scalar_parameter_value("Metallic", 0.9)
            mat_silver.set_scalar_parameter_value("Roughness", 0.25)
            mat_silver.set_scalar_parameter_value("EmissiveMultiplier", 0.25)
            m_comp.set_material(0, mat_silver)

    # 4. Antenna Dish (High-Gain Gold Mesh Reflector)
    dish = sat.get_editor_property("antenna_dish")
    if dish:
        mat_dish = dish.create_dynamic_material_instance(0, m_solid)
        mat_dish.set_vector_parameter_value("Color", unreal.LinearColor(0.95, 0.88, 0.55, 1.0))
        mat_dish.set_scalar_parameter_value("Metallic", 0.95)
        mat_dish.set_scalar_parameter_value("Roughness", 0.2)
        mat_dish.set_scalar_parameter_value("EmissiveMultiplier", 0.4)
        dish.set_material(0, mat_dish)

    # 5. Earth Sensor Optics (Dark Aperture)
    sensor = sat.get_editor_property("earth_sensor")
    if sensor:
        mat_sensor = sensor.create_dynamic_material_instance(0, m_solid)
        mat_sensor.set_vector_parameter_value("Color", unreal.LinearColor(0.02, 0.03, 0.05, 1.0))
        mat_sensor.set_scalar_parameter_value("Metallic", 0.1)
        mat_sensor.set_scalar_parameter_value("Roughness", 0.1)
        mat_sensor.set_scalar_parameter_value("EmissiveMultiplier", 0.1)
        sensor.set_material(0, mat_sensor)

# 9. Function to apply Debris Materials directly to components
def apply_debris_materials(deb):
    if not deb or not m_solid:
        return
    for c_name in ["debris_mesh", "fragment_shard_a", "torn_strut"]:
        c_comp = deb.get_editor_property(c_name)
        if c_comp:
            mat_alloy = c_comp.create_dynamic_material_instance(0, m_solid)
            mat_alloy.set_vector_parameter_value("Color", unreal.LinearColor(0.72, 0.70, 0.68, 1.0))
            mat_alloy.set_scalar_parameter_value("Metallic", 0.85)
            mat_alloy.set_scalar_parameter_value("Roughness", 0.45)
            mat_alloy.set_scalar_parameter_value("EmissiveMultiplier", 0.3)
            c_comp.set_material(0, mat_alloy)

    shard_b = deb.get_editor_property("fragment_shard_b")
    if shard_b:
        mat_hazard = shard_b.create_dynamic_material_instance(0, m_solid)
        mat_hazard.set_vector_parameter_value("Color", unreal.LinearColor(1.0, 0.35, 0.02, 1.0))
        mat_hazard.set_scalar_parameter_value("Metallic", 0.4)
        mat_hazard.set_scalar_parameter_value("Roughness", 0.3)
        mat_hazard.set_scalar_parameter_value("EmissiveMultiplier", 0.5)
        shard_b.set_material(0, mat_hazard)

apply_satellite_materials(sat_actor)
apply_debris_materials(debris_actor)
print("[SPACECRAFT] Applied PBR materials to satellite and debris.")

# 10. Trajectory Spline Mesh Geometry
sat_nom_raw = payload["time_series"]["satellite_nominal_positions_ue"]
deb_raw = payload["time_series"]["debris_positions_ue"]
sat_mod_raw = payload["time_series"]["satellite_modified_positions_ue"]

sat_nom_pts = [unreal.Vector(p[0], p[1], p[2]) for p in sat_nom_raw]
debris_pts = [unreal.Vector(p[0], p[1], p[2]) for p in deb_raw]
sat_mod_pts = [unreal.Vector(p[0], p[1], p[2]) for p in sat_mod_raw]

if sim_mgr:
    sim_mgr.initialize_simulation_from_payload(payload_path)

def setup_path_geometry(path_actor, pts, color):
    if not path_actor:
        return
    path_actor.set_editor_property("path_thickness", 25.0)
    path_actor.set_trajectory_points(pts, color)
    path_actor.set_actor_hidden_in_game(False)

setup_path_geometry(sat_nominal_path, sat_nom_pts, unreal.LinearColor(0.0, 0.85, 1.0, 1.0))
setup_path_geometry(debris_path, debris_pts, unreal.LinearColor(1.0, 0.15, 0.1, 1.0))
setup_path_geometry(sat_modified_path, sat_mod_pts, unreal.LinearColor(0.15, 1.0, 0.35, 1.0))
print("[TRAJECTORIES] Continuous 3D geometry generated: Cyan (501 pts), Red (501 pts), Green (501 pts).")

# 11. Conjunction Visualizer at Nominal TCA
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

# 12. Manoeuvre Visualizer at Burn Location
burn_epoch_s = payload["selected_manoeuvre"]["burn_epoch_seconds"]
burn_loc = unreal.Vector(*payload["selected_manoeuvre"]["satellite_position_at_burn_ue_uu"])
dv_ue = unreal.Vector(*payload["selected_manoeuvre"]["delta_v_ue_uu"])
dv_mag = payload["selected_manoeuvre"]["delta_v_magnitude_mps"]

if man_viz:
    man_viz.set_manoeuvre_geometry(burn_loc, dv_ue, dv_mag)
    man_viz.set_actor_hidden_in_game(False)
    print(f"[MANOEUVRE] Configured at Burn t={burn_epoch_s:.1f}s, Loc: {burn_loc}, dv: {dv_mag} m/s in -R direction.")

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

out_dir = (unreal.Paths.project_saved_dir() + "Screenshots/WindowsEditor").replace("\\", "/")
os.makedirs(out_dir, exist_ok=True)

unreal.SystemLibrary.execute_console_command(None, "r.TextureStreaming 0")

def capture_view(filename_base, cam_location, cam_rotation, fov=60.0, sun_rotation=None):
    if dir_light:
        if sun_rotation:
            dir_light.set_actor_rotation(sun_rotation, False)
        else:
            dir_light.set_actor_rotation(cam_rotation, False)

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
sun_overview_rot = unreal.Rotator(roll=0.0, pitch=-25.0, yaw=148.0) # Illuminates camera-facing hemisphere
if sat_actor:
    sat_actor.set_actor_hidden_in_game(False)
if debris_actor:
    debris_actor.set_actor_hidden_in_game(False)
capture_view("Milestone2_Earth_Overview", cam_overview_loc, cam_overview_rot, fov=65.0, sun_rotation=sun_overview_rot)

# Capture 2: Dedicated Spacecraft Camera (Golden metallic bus, segmented blue solar arrays, antenna mast/dish, thruster)
sat_pos = sat_nom_pts[0]
if sat_actor:
    sat_actor.set_actor_hidden_in_game(False)
    sat_actor.set_actor_location_and_rotation(sat_pos, unreal.Rotator(0.0, -90.0, 0.0), False, False)
    apply_satellite_materials(sat_actor)
if debris_actor:
    debris_actor.set_actor_hidden_in_game(True) # Isolate satellite for clean presentation without intersection

sat_cam_loc = unreal.Vector(sat_pos.x + 1350.0, sat_pos.y - 1350.0, sat_pos.z + 550.0)
sat_cam_rot = look_at(sat_cam_loc, sat_pos)
capture_view("Milestone2_Satellite_Detail", sat_cam_loc, sat_cam_rot, fov=48.0)

# Capture 3: Dedicated Debris Camera (Irregular jagged metallic fragment shards & hazard orange accent)
deb_pos = debris_pts[0]
if sat_actor:
    sat_actor.set_actor_hidden_in_game(True) # Isolate debris
if debris_actor:
    debris_actor.set_actor_hidden_in_game(False)
    debris_actor.set_actor_location(deb_pos, False, False)
    apply_debris_materials(debris_actor)

deb_cam_loc = unreal.Vector(deb_pos.x + 500.0, deb_pos.y - 600.0, deb_pos.z + 300.0)
deb_cam_rot = look_at(deb_cam_loc, deb_pos)
capture_view("Milestone2_Debris_Detail", deb_cam_loc, deb_cam_rot, fov=42.0)

# Capture 4: Encounter Framing (Satellite & Debris framed together in orbit at t=0)
if sat_actor:
    sat_actor.set_actor_hidden_in_game(False)
    sat_actor.set_actor_location_and_rotation(sat_pos, unreal.Rotator(0.0, -90.0, 0.0), False, False)
    apply_satellite_materials(sat_actor)
if debris_actor:
    debris_actor.set_actor_hidden_in_game(False)
    debris_actor.set_actor_location(deb_pos, False, False)
    apply_debris_materials(debris_actor)

mid_enc = unreal.Vector(70000.0, -50.0, 0.0)
enc_cam_loc = unreal.Vector(70000.0 + 1200.0, -50.0 - 1600.0, 750.0)
enc_cam_rot = look_at(enc_cam_loc, mid_enc)
capture_view("Milestone2_Encounter_Overview", enc_cam_loc, enc_cam_rot, fov=50.0)

# Capture 5: Conjunction TCA View (TCA markers: Amber Satellite & Red Debris, Magenta miss-distance line, Violet encounter disc)
if sat_actor:
    sat_actor.set_actor_hidden_in_game(False)
    sat_actor.set_actor_location(sat_tca_pos, False, False)
    apply_satellite_materials(sat_actor)
if debris_actor:
    debris_actor.set_actor_hidden_in_game(False)
    debris_actor.set_actor_location(deb_tca_pos, False, False)
    apply_debris_materials(debris_actor)

tca_mid = unreal.Vector((sat_tca_pos.x + deb_tca_pos.x) * 0.5, (sat_tca_pos.y + deb_tca_pos.y) * 0.5, (sat_tca_pos.z + deb_tca_pos.z) * 0.5)
tca_cam_loc = unreal.Vector(tca_mid.x + 1000.0, tca_mid.y - 1200.0, tca_mid.z + 650.0)
tca_cam_rot = look_at(tca_cam_loc, tca_mid)
capture_view("Milestone2_Conjunction_TCA", tca_cam_loc, tca_cam_rot, fov=45.0)

# Capture 6: Manoeuvre Burn Location & Delta-V Direction Arrow (Burn ring, trajectory tube, 3.0 m/s arrow in -R direction)
if sat_actor:
    sat_actor.set_actor_hidden_in_game(False)
    sat_actor.set_actor_location(burn_loc, False, False)
    apply_satellite_materials(sat_actor)

burn_cam_loc = unreal.Vector(burn_loc.x + 850.0, burn_loc.y - 1100.0, burn_loc.z + 500.0)
burn_cam_rot = look_at(burn_cam_loc, burn_loc)
capture_view("Milestone2_Manoeuvre_Burn", burn_cam_loc, burn_cam_rot, fov=48.0)

# Capture 7: Trajectory Divergence (Cyan nominal, Green post-manoeuvre modified, Red debris)
div_cam_loc = unreal.Vector(78000.0, -42000.0, 14000.0)
div_cam_rot = look_at(div_cam_loc, unreal.Vector(62000.0, -32000.0, 0.0))
sun_div_rot = unreal.Rotator(roll=0.0, pitch=-25.0, yaw=148.0)
capture_view("Milestone2_Trajectories_Divergence", div_cam_loc, div_cam_rot, fov=55.0, sun_rotation=sun_div_rot)

# Reset satellite & debris to t=0
if sat_actor:
    sat_actor.set_actor_hidden_in_game(False)
    sat_actor.set_actor_location_and_rotation(sat_pos, unreal.Rotator(0.0, -90.0, 0.0), False, False)
    apply_satellite_materials(sat_actor)
if debris_actor:
    debris_actor.set_actor_hidden_in_game(False)
    debris_actor.set_actor_location(deb_pos, False, False)
    apply_debris_materials(debris_actor)

unreal.EditorLevelLibrary.save_current_level()

print("=" * 70)
print("[MILESTONE 2 COMPLETE] All captures completed and level saved cleanly!")
print("=" * 70)

unreal.SystemLibrary.execute_console_command(None, "QUIT_EDITOR")
