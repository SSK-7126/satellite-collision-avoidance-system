"""
render_milestone2_final.py
==========================
Definitive Master Rendering Script for Milestone 2: Satellite, Debris, and Orbital Trajectory Visualization.

Deliverables:
1. Milestone2_Earth_Overview.png: Complete Earth in space, continents, oceans, atmospheric rim, and orbital tracks.
2. Milestone2_Satellite_Detail.png: Spacecraft model with golden bus, blue solar wings, silver deck, gold dish, optical sensor.
3. Milestone2_Debris_Detail.png: Irregular metallic fragment shards and hazard orange accent plate.
4. Milestone2_Encounter_Overview.png: Satellite and debris framed together in initial orbital state (t=0) with orbital tracks.
5. Milestone2_Conjunction_TCA.png: Conjunction markers at nominal TCA (t=769.63s, miss distance 15.63 uu / 1563.5m).
6. Milestone2_Manoeuvre_Burn.png: Burn location ring (Purple), Green Delta-V arrow along -R (3.0 m/s), diverging paths.
7. Milestone2_Trajectories_Divergence.png: Orbital vantage showing Earth, Nominal (Cyan), Avoidance (Green), and Debris (Red) paths.
"""

import unreal
import json
import os
import math

print("=" * 70)
print("[MILESTONE 2 FINAL] Initializing rendering pipeline...")
print("=" * 70)

# 1. Load Simulation Payload
payload_path = os.path.abspath(os.path.join(
    os.path.dirname(__file__),
    "../../D2/visualization/unreal_simulation_payload.json"
)).replace("\\", "/")

with open(payload_path, "r", encoding="utf-8") as f:
    payload = json.load(f)

# 2. Load Level
level_path = "/Game/Scenarios/CollisionAvoidanceDemo"
unreal.EditorLevelLibrary.load_level(level_path)
world = unreal.EditorLevelLibrary.get_editor_world()
all_actors = unreal.EditorLevelLibrary.get_all_level_actors()

# Suppress on-screen warnings and force max texture streaming quality
unreal.SystemLibrary.execute_console_command(None, "DisableAllScreenMessages")
unreal.SystemLibrary.execute_console_command(None, "r.TextureStreaming 0")
unreal.SystemLibrary.execute_console_command(None, "r.Streaming.PoolSize 0")
unreal.SystemLibrary.execute_console_command(None, "r.Streaming.FullyLoadUsedTextures 1")

# 3. Clean up terrestrial environment
for a in list(all_actors):
    cname = a.get_class().get_name()
    if "Landscape" in cname or cname in ["VolumetricCloud", "ExponentialHeightFog", "SkyAtmosphere"]:
        a.set_actor_hidden_in_game(True)
    elif a.get_actor_label() == "SM_SkySphere":
        a.set_actor_hidden_in_game(True)

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

# 5. Base Lighting Defaults
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
    comp.set_editor_property("intensity", 2.0)

asset_tools = unreal.AssetToolsHelpers.get_asset_tools()
mat_factory = unreal.MaterialFactoryNew()

# 6. Configure T_Earth_Day & M_Earth
t_earth = unreal.EditorAssetLibrary.load_asset("/Game/Earth/T_Earth_Day")
if t_earth:
    t_earth.set_editor_property("never_stream", True)
    unreal.EditorAssetLibrary.save_loaded_asset(t_earth)

unreal.EditorAssetLibrary.delete_asset("/Game/Earth/M_Earth")
m_earth = asset_tools.create_asset("M_Earth", "/Game/Earth", unreal.Material, mat_factory)
m_earth.set_editor_property("two_sided", False)

tex_expr = unreal.MaterialEditingLibrary.create_material_expression(m_earth, unreal.MaterialExpressionTextureSampleParameter2D, -300, 0)
tex_expr.set_editor_property("parameter_name", "EarthTexture")
if t_earth:
    tex_expr.set_editor_property("texture", t_earth)
unreal.MaterialEditingLibrary.connect_material_property(tex_expr, "RGB", unreal.MaterialProperty.MP_BASE_COLOR)

rough_expr = unreal.MaterialEditingLibrary.create_material_expression(m_earth, unreal.MaterialExpressionConstant, -150, 150)
rough_expr.set_editor_property("r", 0.65)
unreal.MaterialEditingLibrary.connect_material_property(rough_expr, "", unreal.MaterialProperty.MP_ROUGHNESS)

unreal.MaterialEditingLibrary.recompile_material(m_earth)
unreal.EditorAssetLibrary.save_loaded_asset(m_earth)
print("[MATERIALS] M_Earth compiled and saved with high-res T_Earth_Day.")

# 7. Recreate & Compile M_SolidColor with used_with_spline_meshes=True upfront
unreal.EditorAssetLibrary.delete_asset("/Game/Common/M_SolidColor")
m_solid = asset_tools.create_asset("M_SolidColor", "/Game/Common", unreal.Material, mat_factory)
m_solid.set_editor_property("two_sided", True)
m_solid.set_editor_property("used_with_spline_meshes", True)

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
print("[MATERIALS] M_SolidColor compiled cleanly with used_with_spline_meshes=True")

# 8. Recreate M_TranslucentDisc cleanly (Subtle, highly translucent violet encounter plane)
unreal.EditorAssetLibrary.delete_asset("/Game/Common/M_TranslucentDisc")
m_disc = asset_tools.create_asset("M_TranslucentDisc", "/Game/Common", unreal.Material, mat_factory)
m_disc.set_editor_property("two_sided", True)
m_disc.set_editor_property("blend_mode", unreal.BlendMode.BLEND_TRANSLUCENT)
m_disc.set_editor_property("shading_model", unreal.MaterialShadingModel.MSM_UNLIT)

d_col = unreal.MaterialEditingLibrary.create_material_expression(m_disc, unreal.MaterialExpressionVectorParameter, -400, -100)
d_col.set_editor_property("parameter_name", "Color")
d_col.set_editor_property("default_value", unreal.LinearColor(0.65, 0.2, 0.95, 1.0))
unreal.MaterialEditingLibrary.connect_material_property(d_col, "", unreal.MaterialProperty.MP_EMISSIVE_COLOR)

d_op = unreal.MaterialEditingLibrary.create_material_expression(m_disc, unreal.MaterialExpressionScalarParameter, -400, 150)
d_op.set_editor_property("parameter_name", "Opacity")
d_op.set_editor_property("default_value", 0.12)
unreal.MaterialEditingLibrary.connect_material_property(d_op, "", unreal.MaterialProperty.MP_OPACITY)

unreal.MaterialEditingLibrary.recompile_material(m_disc)
unreal.EditorAssetLibrary.save_loaded_asset(m_disc)
print("[MATERIALS] M_TranslucentDisc compiled cleanly.")

# 9. Configure Earth Actor
m_atmo = unreal.EditorAssetLibrary.load_asset("/Game/Earth/M_Atmosphere")

def apply_earth_materials():
    if not earth_actor:
        return
    em = earth_actor.get_editor_property("earth_mesh")
    atm = earth_actor.get_editor_property("atmosphere_mesh")
    if em and m_earth:
        em.set_material(0, m_earth)
    if atm and m_atmo:
        atm.set_material(0, m_atmo)
        atm.set_relative_scale3d(unreal.Vector(1.015, 1.015, 1.015))
        atm.set_visibility(True)
        atm.set_hidden_in_game(False)

apply_earth_materials()
print("[EARTH] Earth materials configured.")

# 10. Satellite Materials Function
def apply_satellite_materials(sat, is_manoeuvred=False):
    if not sat or not m_solid:
        return
    # Golden Bus (or Emerald Green if post-manoeuvre)
    body = sat.get_editor_property("satellite_body")
    if body:
        mat_body = body.create_dynamic_material_instance(0, m_solid)
        if is_manoeuvred:
            mat_body.set_vector_parameter_value("Color", unreal.LinearColor(0.1, 0.95, 0.45, 1.0))
            mat_body.set_scalar_parameter_value("Metallic", 0.85)
            mat_body.set_scalar_parameter_value("Roughness", 0.25)
            mat_body.set_scalar_parameter_value("EmissiveMultiplier", 0.4)
        else:
            mat_body.set_vector_parameter_value("Color", unreal.LinearColor(0.98, 0.82, 0.28, 1.0))
            mat_body.set_scalar_parameter_value("Metallic", 0.9)
            mat_body.set_scalar_parameter_value("Roughness", 0.2)
            mat_body.set_scalar_parameter_value("EmissiveMultiplier", 0.4)
        body.set_material(0, mat_body)

    # Blue Solar Panels
    for p_name in ["solar_panel_left", "solar_panel_left_outboard", "solar_panel_right", "solar_panel_right_outboard"]:
        p_comp = sat.get_editor_property(p_name)
        if p_comp:
            mat_blue = p_comp.create_dynamic_material_instance(0, m_solid)
            mat_blue.set_vector_parameter_value("Color", unreal.LinearColor(0.015, 0.08, 0.55, 1.0))
            mat_blue.set_scalar_parameter_value("Metallic", 0.85)
            mat_blue.set_scalar_parameter_value("Roughness", 0.15)
            mat_blue.set_scalar_parameter_value("EmissiveMultiplier", 0.35)
            p_comp.set_material(0, mat_blue)

    # Aerospace Silver Metal
    for m_name in ["payload_deck", "solar_yoke_left", "solar_yoke_right", "antenna_mast", "thruster_nozzle"]:
        m_comp = sat.get_editor_property(m_name)
        if m_comp:
            mat_silver = m_comp.create_dynamic_material_instance(0, m_solid)
            mat_silver.set_vector_parameter_value("Color", unreal.LinearColor(0.78, 0.82, 0.86, 1.0))
            mat_silver.set_scalar_parameter_value("Metallic", 0.9)
            mat_silver.set_scalar_parameter_value("Roughness", 0.25)
            mat_silver.set_scalar_parameter_value("EmissiveMultiplier", 0.25)
            m_comp.set_material(0, mat_silver)

    # Gold Reflector Dish
    dish = sat.get_editor_property("antenna_dish")
    if dish:
        mat_dish = dish.create_dynamic_material_instance(0, m_solid)
        mat_dish.set_vector_parameter_value("Color", unreal.LinearColor(0.95, 0.88, 0.55, 1.0))
        mat_dish.set_scalar_parameter_value("Metallic", 0.95)
        mat_dish.set_scalar_parameter_value("Roughness", 0.2)
        mat_dish.set_scalar_parameter_value("EmissiveMultiplier", 0.4)
        dish.set_material(0, mat_dish)

    # Dark Optical Sensor Aperture
    sensor = sat.get_editor_property("earth_sensor")
    if sensor:
        mat_sensor = sensor.create_dynamic_material_instance(0, m_solid)
        mat_sensor.set_vector_parameter_value("Color", unreal.LinearColor(0.02, 0.03, 0.05, 1.0))
        mat_sensor.set_scalar_parameter_value("Metallic", 0.1)
        mat_sensor.set_scalar_parameter_value("Roughness", 0.1)
        mat_sensor.set_scalar_parameter_value("EmissiveMultiplier", 0.1)
        sensor.set_material(0, mat_sensor)

# 11. Debris Materials Function
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

# 12. Conjunction Visualizer Materials Function
def apply_conjunction_materials(cv):
    if not cv or not m_solid:
        return
    tca_sph = cv.get_editor_property("tca_marker_sphere")
    if tca_sph:
        mat_tca = tca_sph.create_dynamic_material_instance(0, m_solid)
        mat_tca.set_vector_parameter_value("Color", unreal.LinearColor(1.0, 0.82, 0.05, 1.0))
        mat_tca.set_scalar_parameter_value("EmissiveMultiplier", 2.2)
        tca_sph.set_material(0, mat_tca)

    deb_sph = cv.get_editor_property("debris_tca_marker_sphere")
    if deb_sph:
        mat_deb = deb_sph.create_dynamic_material_instance(0, m_solid)
        mat_deb.set_vector_parameter_value("Color", unreal.LinearColor(1.0, 0.15, 0.1, 1.0))
        mat_deb.set_scalar_parameter_value("EmissiveMultiplier", 2.2)
        deb_sph.set_material(0, mat_deb)

    line = cv.get_editor_property("miss_distance_line")
    if line:
        mat_line = line.create_dynamic_material_instance(0, m_solid)
        mat_line.set_vector_parameter_value("Color", unreal.LinearColor(1.0, 0.05, 0.70, 1.0))
        mat_line.set_scalar_parameter_value("EmissiveMultiplier", 2.5)
        line.set_material(0, mat_line)

    disc = cv.get_editor_property("encounter_plane_disc")
    if disc and m_disc:
        mat_disc = disc.create_dynamic_material_instance(0, m_disc)
        mat_disc.set_vector_parameter_value("Color", unreal.LinearColor(0.65, 0.2, 0.95, 1.0))
        mat_disc.set_scalar_parameter_value("Opacity", 0.12)
        disc.set_material(0, mat_disc)

# 13. Manoeuvre Visualizer Materials Function
def apply_manoeuvre_materials(mv):
    if not mv or not m_solid:
        return
    ring = mv.get_editor_property("burn_marker_ring")
    if ring:
        mat_ring = ring.create_dynamic_material_instance(0, m_solid)
        mat_ring.set_vector_parameter_value("Color", unreal.LinearColor(0.85, 0.3, 1.0, 1.0))
        mat_ring.set_scalar_parameter_value("EmissiveMultiplier", 2.0)
        ring.set_material(0, mat_ring)

    for a_name in ["delta_v_arrow_shaft", "delta_v_arrow"]:
        comp = mv.get_editor_property(a_name)
        if comp:
            mat_arrow = comp.create_dynamic_material_instance(0, m_solid)
            mat_arrow.set_vector_parameter_value("Color", unreal.LinearColor(0.1, 1.0, 0.35, 1.0))
            mat_arrow.set_scalar_parameter_value("EmissiveMultiplier", 2.2)
            comp.set_material(0, mat_arrow)

# 14. Trajectory Points Extraction
sat_nom_raw = payload["time_series"]["satellite_nominal_positions_ue"]
debris_raw = payload["time_series"]["debris_positions_ue"]
sat_mod_raw = payload["time_series"]["satellite_modified_positions_ue"]

sat_nom_pts = [unreal.Vector(p[0], p[1], p[2]) for p in sat_nom_raw]
debris_pts = [unreal.Vector(p[0], p[1], p[2]) for p in debris_raw]
sat_mod_pts = [unreal.Vector(p[0], p[1], p[2]) for p in sat_mod_raw]

def setup_path_geometry(path_actor, pts, color):
    if not path_actor:
        return
    path_actor.set_editor_property("path_thickness", 25.0)
    path_actor.set_trajectory_points(pts, color)
    path_actor.set_actor_hidden_in_game(False)

setup_path_geometry(sat_nominal_path, sat_nom_pts, unreal.LinearColor(0.0, 0.85, 1.0, 1.0)) # Cyan
setup_path_geometry(debris_path, debris_pts, unreal.LinearColor(1.0, 0.15, 0.1, 1.0))        # Red
setup_path_geometry(sat_modified_path, sat_mod_pts, unreal.LinearColor(0.15, 1.0, 0.35, 1.0)) # Green
print("[TRAJECTORIES] 3 continuous orbital splines generated.")

# 15. Conjunction Data Setup
nom_tca_s = payload["nominal_encounter"]["tca_seconds"]
ts = payload["time_series"]["timestamps_sec"]
tca_idx = min(range(len(ts)), key=lambda i: abs(ts[i] - nom_tca_s))
sat_tca_pos = sat_nom_pts[tca_idx]
deb_tca_pos = debris_pts[tca_idx]
miss_dist_uu = payload["nominal_encounter"]["miss_distance_m"] * payload["scenario_metadata"]["scale_factor_uu_per_m"]

if conj_viz:
    conj_viz.update_conjunction_geometry(sat_tca_pos, deb_tca_pos, miss_dist_uu)
    conj_viz.set_actor_location(sat_tca_pos, False, False)
    conj_viz.set_actor_hidden_in_game(False)
    apply_conjunction_materials(conj_viz)

# 16. Manoeuvre Data Setup
burn_epoch_s = payload["selected_manoeuvre"]["burn_epoch_seconds"]
burn_loc = unreal.Vector(*payload["selected_manoeuvre"]["satellite_position_at_burn_ue_uu"])
dv_ue = unreal.Vector(*payload["selected_manoeuvre"]["delta_v_ue_uu"])
dv_mag = payload["selected_manoeuvre"]["delta_v_magnitude_mps"]

if man_viz:
    man_viz.set_manoeuvre_geometry(burn_loc, dv_ue, dv_mag)
    man_viz.set_actor_hidden_in_game(False)
    apply_manoeuvre_materials(man_viz)

# Helper look-at
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

def capture_view(filename_base, cam_location, cam_rotation, fov=60.0, sun_rotation=None, sun_intensity=14.0):
    if dir_light:
        if sun_rotation:
            dir_light.set_actor_rotation(sun_rotation, False)
        else:
            dir_light.set_actor_rotation(cam_rotation, False)
        comp = dir_light.get_component_by_class(unreal.DirectionalLightComponent)
        comp.set_editor_property("intensity", sun_intensity)

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

FAR_AWAY = unreal.Vector(-999999.0, -999999.0, -999999.0)
sat_pos_0 = sat_nom_pts[0]
deb_pos_0 = debris_pts[0]

# Proven Earth daylight illumination angle: points from (+X, -Y, +Z) towards Earth
sun_earth_rot = unreal.Rotator(pitch=-22.0, yaw=148.0, roll=0.0)

# ==============================================================================
# CAPTURE 1: Milestone2_Earth_Overview
# Complete Earth in space, continents, oceans, atmospheric limb, and orbital tracks
# ==============================================================================
print(">>> Executing Capture 1: Earth Overview...")
apply_earth_materials()

if sat_actor:
    sat_actor.set_actor_scale3d(unreal.Vector(1.0, 1.0, 1.0))
    sat_actor.set_actor_location_and_rotation(sat_pos_0, unreal.Rotator(0.0, -90.0, 0.0), False, False)
    sat_actor.set_actor_hidden_in_game(False)
    apply_satellite_materials(sat_actor)

if debris_actor:
    debris_actor.set_actor_scale3d(unreal.Vector(1.0, 1.0, 1.0))
    debris_actor.set_actor_location(deb_pos_0, False, False)
    debris_actor.set_actor_hidden_in_game(False)
    apply_debris_materials(debris_actor)

if sat_nominal_path:
    sat_nominal_path.set_actor_hidden_in_game(False)
if debris_path:
    debris_path.set_actor_hidden_in_game(False)
if sat_modified_path:
    sat_modified_path.set_actor_hidden_in_game(False)

if conj_viz:
    conj_viz.set_actor_hidden_in_game(True)
if man_viz:
    man_viz.set_actor_hidden_in_game(True)

cam_overview_loc = unreal.Vector(115000.0, -45000.0, 32000.0)
cam_overview_rot = look_at(cam_overview_loc, unreal.Vector(0.0, 0.0, 0.0))
capture_view("Milestone2_Earth_Overview", cam_overview_loc, cam_overview_rot, fov=65.0, sun_rotation=sun_earth_rot, sun_intensity=14.0)

# ==============================================================================
# CAPTURE 2: Milestone2_Satellite_Detail
# Isolated Spacecraft Model with golden bus, blue solar wings, silver deck, gold dish against space
# ==============================================================================
print(">>> Executing Capture 2: Satellite Detail...")
if debris_actor:
    debris_actor.set_actor_location(FAR_AWAY, False, False)
    debris_actor.set_actor_hidden_in_game(True)

# Hide trajectories so tubes don't intersect the satellite
if sat_nominal_path:
    sat_nominal_path.set_actor_hidden_in_game(True)
if debris_path:
    debris_path.set_actor_hidden_in_game(True)
if sat_modified_path:
    sat_modified_path.set_actor_hidden_in_game(True)

if conj_viz:
    conj_viz.set_actor_hidden_in_game(True)
if man_viz:
    man_viz.set_actor_hidden_in_game(True)

if sat_actor:
    sat_actor.set_actor_scale3d(unreal.Vector(1.0, 1.0, 1.0))
    sat_actor.set_actor_location_and_rotation(sat_pos_0, unreal.Rotator(0.0, -90.0, 0.0), False, False)
    sat_actor.set_actor_hidden_in_game(False)
    apply_satellite_materials(sat_actor, is_manoeuvred=False)

# Camera positioned to frame entire satellite wingspan against deep space with breathing margins
sat_cam_loc = unreal.Vector(sat_pos_0.x - 1750.0, sat_pos_0.y - 1100.0, sat_pos_0.z + 580.0)
sat_cam_rot = look_at(sat_cam_loc, unreal.Vector(sat_pos_0.x, sat_pos_0.y, sat_pos_0.z + 30.0))
capture_view("Milestone2_Satellite_Detail", sat_cam_loc, sat_cam_rot, fov=48.0, sun_rotation=sat_cam_rot, sun_intensity=14.0)

# ==============================================================================
# CAPTURE 3: Milestone2_Debris_Detail
# Isolated Debris Fragment with metallic shards and hazard orange plate against space
# ==============================================================================
print(">>> Executing Capture 3: Debris Detail...")
if sat_actor:
    sat_actor.set_actor_location(FAR_AWAY, False, False)
    sat_actor.set_actor_hidden_in_game(True)

if debris_actor:
    debris_actor.set_actor_scale3d(unreal.Vector(1.0, 1.0, 1.0))
    debris_actor.set_actor_location(deb_pos_0, False, False)
    debris_actor.set_actor_hidden_in_game(False)
    apply_debris_materials(debris_actor)

# Camera positioned to frame full irregular debris geometry cleanly against deep space
deb_cam_loc = unreal.Vector(deb_pos_0.x - 750.0, deb_pos_0.y - 650.0, deb_pos_0.z + 400.0)
deb_cam_rot = look_at(deb_cam_loc, deb_pos_0)
capture_view("Milestone2_Debris_Detail", deb_cam_loc, deb_cam_rot, fov=42.0, sun_rotation=deb_cam_rot, sun_intensity=14.0)

# ==============================================================================
# CAPTURE 4: Milestone2_Encounter_Overview
# Satellite & Debris framed together in initial orbital state (t=0) with orbital tracks
# ==============================================================================
print(">>> Executing Capture 4: Encounter Overview...")
# Scale actors to 0.35 so their visual bodies do not intersect across the 100 uu gap along Y
if sat_actor:
    sat_actor.set_actor_scale3d(unreal.Vector(0.35, 0.35, 0.35))
    sat_actor.set_actor_location_and_rotation(sat_pos_0, unreal.Rotator(0.0, -90.0, 0.0), False, False)
    sat_actor.set_actor_hidden_in_game(False)
    apply_satellite_materials(sat_actor)

if debris_actor:
    debris_actor.set_actor_scale3d(unreal.Vector(0.35, 0.35, 0.35))
    debris_actor.set_actor_location(deb_pos_0, False, False)
    debris_actor.set_actor_hidden_in_game(False)
    apply_debris_materials(debris_actor)

# Sleek 8.0 uu trajectories for crisp close-up framing
if sat_nominal_path:
    sat_nominal_path.set_editor_property("path_thickness", 8.0)
    sat_nominal_path.set_trajectory_points(sat_nom_pts, unreal.LinearColor(0.0, 0.85, 1.0, 1.0))
    sat_nominal_path.set_actor_hidden_in_game(False)
if debris_path:
    debris_path.set_editor_property("path_thickness", 8.0)
    debris_path.set_trajectory_points(debris_pts, unreal.LinearColor(1.0, 0.15, 0.1, 1.0))
    debris_path.set_actor_hidden_in_game(False)
if sat_modified_path:
    sat_modified_path.set_actor_hidden_in_game(True)

if conj_viz:
    conj_viz.set_actor_hidden_in_game(True)
if man_viz:
    man_viz.set_actor_hidden_in_game(True)

mid_enc = unreal.Vector((sat_pos_0.x + deb_pos_0.x) * 0.5, (sat_pos_0.y + deb_pos_0.y) * 0.5, (sat_pos_0.z + deb_pos_0.z) * 0.5)
# 3/4 elevated vantage looking down-track and outboard into deep space
enc_cam_loc = unreal.Vector(mid_enc.x - 1100.0, mid_enc.y + 220.0, mid_enc.z + 420.0)
enc_cam_rot = look_at(enc_cam_loc, mid_enc)
capture_view("Milestone2_Encounter_Overview", enc_cam_loc, enc_cam_rot, fov=44.0, sun_rotation=enc_cam_rot, sun_intensity=14.0)

# ==============================================================================
# CAPTURE 5: Milestone2_Conjunction_TCA
# Conjunction geometry at nominal TCA: Amber & Red spheres, Magenta miss line, Violet disc
# ==============================================================================
print(">>> Executing Capture 5: Conjunction TCA...")
# Hide trajectories to keep close-up encounter markers crisp and unobstructed
if sat_nominal_path:
    sat_nominal_path.set_actor_hidden_in_game(True)
if debris_path:
    debris_path.set_actor_hidden_in_game(True)
if sat_modified_path:
    sat_modified_path.set_actor_hidden_in_game(True)

tca_mid = unreal.Vector((sat_tca_pos.x + deb_tca_pos.x) * 0.5, (sat_tca_pos.y + deb_tca_pos.y) * 0.5, (sat_tca_pos.z + deb_tca_pos.z) * 0.5)

if conj_viz:
    conj_viz.set_actor_location(sat_tca_pos, False, False)
    conj_viz.set_actor_hidden_in_game(False)

    tca_sph = conj_viz.get_editor_property("tca_marker_sphere")
    if tca_sph:
        tca_sph.set_world_scale3d(unreal.Vector(0.018, 0.018, 0.018))
        mat_tca = tca_sph.create_dynamic_material_instance(0, m_solid)
        mat_tca.set_vector_parameter_value("Color", unreal.LinearColor(1.0, 0.82, 0.05, 1.0))
        mat_tca.set_scalar_parameter_value("EmissiveMultiplier", 2.2)
        tca_sph.set_material(0, mat_tca)

    deb_sph = conj_viz.get_editor_property("debris_tca_marker_sphere")
    if deb_sph:
        deb_sph.set_world_location(deb_tca_pos, False, False)
        deb_sph.set_world_scale3d(unreal.Vector(0.018, 0.018, 0.018))
        mat_deb = deb_sph.create_dynamic_material_instance(0, m_solid)
        mat_deb.set_vector_parameter_value("Color", unreal.LinearColor(1.0, 0.15, 0.1, 1.0))
        mat_deb.set_scalar_parameter_value("EmissiveMultiplier", 2.2)
        deb_sph.set_material(0, mat_deb)

    dx = deb_tca_pos.x - sat_tca_pos.x
    dy = deb_tca_pos.y - sat_tca_pos.y
    dz = deb_tca_pos.z - sat_tca_pos.z
    dist = math.sqrt(dx*dx + dy*dy + dz*dz)
    rot_line = look_at(sat_tca_pos, deb_tca_pos)
    rot_cyl = unreal.Rotator(pitch=rot_line.pitch - 90.0, yaw=rot_line.yaw, roll=0.0)
    rot_disc = unreal.Rotator(pitch=rot_line.pitch - 45.0, yaw=rot_line.yaw + 35.0, roll=0.0)

    line = conj_viz.get_editor_property("miss_distance_line")
    if line:
        line.set_world_location(tca_mid, False, False)
        line.set_world_rotation(rot_cyl, False, False)
        line.set_world_scale3d(unreal.Vector(0.006, 0.006, dist / 100.0))
        mat_line = line.create_dynamic_material_instance(0, m_solid)
        mat_line.set_vector_parameter_value("Color", unreal.LinearColor(1.0, 0.05, 0.70, 1.0))
        mat_line.set_scalar_parameter_value("EmissiveMultiplier", 2.5)
        line.set_material(0, mat_line)

    disc = conj_viz.get_editor_property("encounter_plane_disc")
    if disc and m_disc:
        disc.set_world_location(tca_mid, False, False)
        disc.set_world_rotation(rot_disc, False, False)
        disc.set_world_scale3d(unreal.Vector(14.0 / 50.0, 14.0 / 50.0, 0.002))
        mat_disc = disc.create_dynamic_material_instance(0, m_disc)
        disc.set_material(0, mat_disc)

# Dock small satellite and debris models
if sat_actor:
    sat_actor.set_actor_scale3d(unreal.Vector(0.012, 0.012, 0.012))
    sat_actor.set_actor_location(sat_tca_pos, False, False)
    sat_actor.set_actor_hidden_in_game(False)
    apply_satellite_materials(sat_actor)

if debris_actor:
    debris_actor.set_actor_scale3d(unreal.Vector(0.012, 0.012, 0.012))
    debris_actor.set_actor_location(deb_tca_pos, False, False)
    debris_actor.set_actor_hidden_in_game(False)
    apply_debris_materials(debris_actor)

# Camera: perpendicular and elevated, looking outward into deep space
tca_cam_loc = unreal.Vector(tca_mid.x + 11.32, tca_mid.y + 36.24, tca_mid.z + 14.0)
tca_cam_rot = look_at(tca_cam_loc, tca_mid)
capture_view("Milestone2_Conjunction_TCA", tca_cam_loc, tca_cam_rot, fov=40.0, sun_rotation=tca_cam_rot, sun_intensity=14.0)

# ==============================================================================
# CAPTURE 6: Milestone2_Manoeuvre_Burn
# Burn location, Electric Purple ring, Green Delta-V arrow along -R, diverging paths
# ==============================================================================
print(">>> Executing Capture 6: Manoeuvre Burn...")
if conj_viz:
    conj_viz.set_actor_hidden_in_game(True)
if debris_actor:
    debris_actor.set_actor_location(FAR_AWAY, False, False)
    debris_actor.set_actor_hidden_in_game(True)

if sat_actor:
    sat_actor.set_actor_scale3d(unreal.Vector(1.0, 1.0, 1.0))
    sat_actor.set_actor_location(burn_loc, False, False)
    sat_actor.set_actor_hidden_in_game(False)
    apply_satellite_materials(sat_actor, is_manoeuvred=True)

if man_viz:
    man_viz.set_manoeuvre_geometry(burn_loc, dv_ue, dv_mag)
    man_viz.set_actor_location(burn_loc, False, False)
    man_viz.set_actor_hidden_in_game(False)
    apply_manoeuvre_materials(man_viz)

# Show Nominal and Modified paths to illustrate divergence at burn
if sat_nominal_path:
    sat_nominal_path.set_editor_property("path_thickness", 25.0)
    sat_nominal_path.set_trajectory_points(sat_nom_pts, unreal.LinearColor(0.0, 0.85, 1.0, 1.0))
    sat_nominal_path.set_actor_hidden_in_game(False)
if sat_modified_path:
    sat_modified_path.set_editor_property("path_thickness", 25.0)
    sat_modified_path.set_trajectory_points(sat_mod_pts, unreal.LinearColor(0.15, 1.0, 0.35, 1.0))
    sat_modified_path.set_actor_hidden_in_game(False)
if debris_path:
    debris_path.set_actor_hidden_in_game(True)

burn_cam_loc = unreal.Vector(burn_loc.x + 1150.0, burn_loc.y - 1250.0, burn_loc.z + 650.0)
burn_cam_rot = look_at(burn_cam_loc, burn_loc)
capture_view("Milestone2_Manoeuvre_Burn", burn_cam_loc, burn_cam_rot, fov=48.0, sun_rotation=burn_cam_rot, sun_intensity=14.0)

# ==============================================================================
# CAPTURE 7: Milestone2_Trajectories_Divergence
# Global orbital vantage: Earth, Nominal (Cyan), Avoidance (Green), Debris (Red), divergence
# ==============================================================================
print(">>> Executing Capture 7: Trajectories Divergence...")
apply_earth_materials()

if sat_actor:
    sat_actor.set_actor_scale3d(unreal.Vector(1.0, 1.0, 1.0))
    sat_actor.set_actor_location_and_rotation(sat_pos_0, unreal.Rotator(0.0, -90.0, 0.0), False, False)
    sat_actor.set_actor_hidden_in_game(False)
    apply_satellite_materials(sat_actor, is_manoeuvred=False)

if debris_actor:
    debris_actor.set_actor_scale3d(unreal.Vector(1.0, 1.0, 1.0))
    debris_actor.set_actor_location(deb_pos_0, False, False)
    debris_actor.set_actor_hidden_in_game(False)
    apply_debris_materials(debris_actor)

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

if man_viz:
    man_viz.set_manoeuvre_geometry(burn_loc, dv_ue, dv_mag)
    man_viz.set_actor_location(burn_loc, False, False)
    man_viz.set_actor_hidden_in_game(False)
    apply_manoeuvre_materials(man_viz)

if conj_viz:
    conj_viz.update_conjunction_geometry(sat_tca_pos, deb_tca_pos, miss_dist_uu)
    conj_viz.set_actor_location(sat_tca_pos, False, False)
    conj_viz.set_actor_hidden_in_game(False)
    apply_conjunction_materials(conj_viz)

# Vantage showing both paths diverging after burn and debris intersecting near TCA
div_cam_loc = unreal.Vector(105000.0, -48000.0, 26000.0)
div_target = unreal.Vector(68000.0, -18000.0, 2000.0)
div_cam_rot = look_at(div_cam_loc, div_target)
capture_view("Milestone2_Trajectories_Divergence", div_cam_loc, div_cam_rot, fov=62.0, sun_rotation=sun_earth_rot, sun_intensity=14.0)

# ==============================================================================
# 8. PERSISTENT LEVEL CAMERAS & LEVEL SAVE
# ==============================================================================
print(">>> Configuring persistent level cameras...")
cameras_to_create = [
    ("Camera_Earth_Overview", cam_overview_loc, cam_overview_rot, 65.0),
    ("Camera_Satellite_Detail", sat_cam_loc, sat_cam_rot, 48.0),
    ("Camera_Debris_Detail", deb_cam_loc, deb_cam_rot, 42.0),
    ("Camera_Encounter_Overview", enc_cam_loc, enc_cam_rot, 44.0),
    ("Camera_Conjunction_TCA", tca_cam_loc, tca_cam_rot, 40.0),
    ("Camera_Manoeuvre_Burn", burn_cam_loc, burn_cam_rot, 48.0),
    ("Camera_Trajectories_Divergence", div_cam_loc, div_cam_rot, 62.0),
]

all_actors = unreal.EditorLevelLibrary.get_all_level_actors()
created_cams = {}
for cam_label, loc, rot, fov in cameras_to_create:
    cam_actor = None
    for a in all_actors:
        if a.get_actor_label() == cam_label:
            cam_actor = a
            break
    if not cam_actor:
        cam_actor = unreal.EditorLevelLibrary.spawn_actor_from_class(unreal.CameraActor, loc, rot)
        cam_actor.set_actor_label(cam_label)
    else:
        cam_actor.set_actor_location_and_rotation(loc, rot, False, False)
    ccomp = cam_actor.get_component_by_class(unreal.CameraComponent)
    if ccomp:
        ccomp.set_editor_property("field_of_view", fov)
    created_cams[cam_label] = cam_actor

if sim_mgr and "Camera_Earth_Overview" in created_cams:
    sim_mgr.set_editor_property("overview_camera", created_cams["Camera_Earth_Overview"])

# Restore nominal initial scene state before saving
if sat_actor:
    sat_actor.set_actor_scale3d(unreal.Vector(1.0, 1.0, 1.0))
    sat_actor.set_actor_location_and_rotation(sat_pos_0, unreal.Rotator(0.0, -90.0, 0.0), False, False)
    sat_actor.set_actor_hidden_in_game(False)
    apply_satellite_materials(sat_actor, is_manoeuvred=False)

if debris_actor:
    debris_actor.set_actor_scale3d(unreal.Vector(1.0, 1.0, 1.0))
    debris_actor.set_actor_location(deb_pos_0, False, False)
    debris_actor.set_actor_hidden_in_game(False)
    apply_debris_materials(debris_actor)

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
    sat_modified_path.set_actor_hidden_in_game(True)

if man_viz:
    man_viz.set_actor_hidden_in_game(True)
if conj_viz:
    conj_viz.set_actor_hidden_in_game(False)

# Save the level
unreal.EditorLevelLibrary.save_current_level()
print("[LEVEL] /Game/Scenarios/CollisionAvoidanceDemo level saved successfully.")

print("=" * 70)
print("[MILESTONE 2 FINAL] All 7 captures and level save completed successfully!")
print("=" * 70)

unreal.SystemLibrary.execute_console_command(None, "QUIT_EDITOR")
