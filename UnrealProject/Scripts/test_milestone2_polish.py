"""
test_milestone2_polish.py
=========================
Visual Polish Pass for Milestone 2:
1. Earth overview: Complete Earth globe fully in frame, all 3 trajectories distinguishable.
2. Satellite detail: Rich PBR metallic materials (gold foil, glossy blue solar cells, silver deck), 3-point key/fill lighting with specular glints.
3. Conjunction TCA: Reduced compact encounter disc (radius 9.5 uu), crisp luminous miss distance connector, balanced framing of spacecraft and debris.
"""

import unreal
import json
import os
import math

payload_path = os.path.abspath(os.path.join(
    os.path.dirname(__file__),
    "../../D2/visualization/unreal_simulation_payload.json"
)).replace("\\", "/")

with open(payload_path, "r", encoding="utf-8") as f:
    payload = json.load(f)

level_path = "/Game/Scenarios/CollisionAvoidanceDemo"
unreal.EditorLevelLibrary.load_level(level_path)
world = unreal.EditorLevelLibrary.get_editor_world()
all_actors = unreal.EditorLevelLibrary.get_all_level_actors()

unreal.SystemLibrary.execute_console_command(None, "DisableAllScreenMessages")
unreal.SystemLibrary.execute_console_command(None, "r.TextureStreaming 0")
unreal.SystemLibrary.execute_console_command(None, "r.Streaming.PoolSize 0")
unreal.SystemLibrary.execute_console_command(None, "r.Streaming.FullyLoadUsedTextures 1")

# Clean terrestrial clutter
for a in list(all_actors):
    cname = a.get_class().get_name()
    if "Landscape" in cname or cname in ["VolumetricCloud", "ExponentialHeightFog", "SkyAtmosphere"]:
        a.set_actor_hidden_in_game(True)
    elif a.get_actor_label() == "SM_SkySphere":
        a.set_actor_hidden_in_game(True)

earth_actor = [a for a in all_actors if isinstance(a, unreal.EarthActor)][0]
sat_actor = [a for a in all_actors if isinstance(a, unreal.SatelliteActor)][0]
debris_actor = [a for a in all_actors if isinstance(a, unreal.DebrisActor)][0]
dir_light = [a for a in all_actors if isinstance(a, unreal.DirectionalLight)][0]
sky_light = [a for a in all_actors if isinstance(a, unreal.SkyLight)][0]
conj_viz = [a for a in all_actors if isinstance(a, unreal.ConjunctionVisualizer)][0]
man_viz = [a for a in all_actors if isinstance(a, unreal.ManoeuvreVisualizer)][0]

sat_nominal_path = None
debris_path = None
sat_modified_path = None
for a in all_actors:
    if isinstance(a, unreal.OrbitPathActor):
        if "Debris" in a.get_actor_label():
            debris_path = a
        elif "Modified" in a.get_actor_label():
            sat_modified_path = a
        else:
            sat_nominal_path = a

asset_tools = unreal.AssetToolsHelpers.get_asset_tools()
mat_factory = unreal.MaterialFactoryNew()

# 1. Earth Texture & Material
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

# 2. Solid Color PBR Material
unreal.EditorAssetLibrary.delete_asset("/Game/Common/M_SolidColor")
m_solid = asset_tools.create_asset("M_SolidColor", "/Game/Common", unreal.Material, mat_factory)
m_solid.set_editor_property("two_sided", True)
m_solid.set_editor_property("used_with_spline_meshes", True)

col_param = unreal.MaterialEditingLibrary.create_material_expression(m_solid, unreal.MaterialExpressionVectorParameter, -400, -100)
col_param.set_editor_property("parameter_name", "Color")
col_param.set_editor_property("default_value", unreal.LinearColor(1.0, 1.0, 1.0, 1.0))
unreal.MaterialEditingLibrary.connect_material_property(col_param, "", unreal.MaterialProperty.MP_BASE_COLOR)

met_param = unreal.MaterialEditingLibrary.create_material_expression(m_solid, unreal.MaterialExpressionScalarParameter, -400, 0)
met_param.set_editor_property("parameter_name", "Metallic")
met_param.set_editor_property("default_value", 0.0)
unreal.MaterialEditingLibrary.connect_material_property(met_param, "", unreal.MaterialProperty.MP_METALLIC)

rgh_param = unreal.MaterialEditingLibrary.create_material_expression(m_solid, unreal.MaterialExpressionScalarParameter, -400, 100)
rgh_param.set_editor_property("parameter_name", "Roughness")
rgh_param.set_editor_property("default_value", 0.5)
unreal.MaterialEditingLibrary.connect_material_property(rgh_param, "", unreal.MaterialProperty.MP_ROUGHNESS)

em_param = unreal.MaterialEditingLibrary.create_material_expression(m_solid, unreal.MaterialExpressionScalarParameter, -400, 200)
em_param.set_editor_property("parameter_name", "EmissiveMultiplier")
em_param.set_editor_property("default_value", 0.2)

mult_expr = unreal.MaterialEditingLibrary.create_material_expression(m_solid, unreal.MaterialExpressionMultiply, -200, 50)
unreal.MaterialEditingLibrary.connect_material_expressions(col_param, "", mult_expr, "A")
unreal.MaterialEditingLibrary.connect_material_expressions(em_param, "", mult_expr, "B")
unreal.MaterialEditingLibrary.connect_material_property(mult_expr, "", unreal.MaterialProperty.MP_EMISSIVE_COLOR)

unreal.MaterialEditingLibrary.recompile_material(m_solid)
unreal.EditorAssetLibrary.save_loaded_asset(m_solid)

# 3. Translucent Encounter Disc Material
unreal.EditorAssetLibrary.delete_asset("/Game/Common/M_TranslucentDisc")
m_disc = asset_tools.create_asset("M_TranslucentDisc", "/Game/Common", unreal.Material, mat_factory)
m_disc.set_editor_property("two_sided", True)
m_disc.set_editor_property("blend_mode", unreal.BlendMode.BLEND_TRANSLUCENT)
m_disc.set_editor_property("shading_model", unreal.MaterialShadingModel.MSM_UNLIT)

d_col = unreal.MaterialEditingLibrary.create_material_expression(m_disc, unreal.MaterialExpressionVectorParameter, -400, -100)
d_col.set_editor_property("parameter_name", "Color")
d_col.set_editor_property("default_value", unreal.LinearColor(0.75, 0.25, 1.0, 1.0))

d_mult = unreal.MaterialEditingLibrary.create_material_expression(m_disc, unreal.MaterialExpressionScalarParameter, -400, 0)
d_mult.set_editor_property("parameter_name", "Emissive")
d_mult.set_editor_property("default_value", 0.7)

d_mul_node = unreal.MaterialEditingLibrary.create_material_expression(m_disc, unreal.MaterialExpressionMultiply, -200, -50)
unreal.MaterialEditingLibrary.connect_material_expressions(d_col, "", d_mul_node, "A")
unreal.MaterialEditingLibrary.connect_material_expressions(d_mult, "", d_mul_node, "B")
unreal.MaterialEditingLibrary.connect_material_property(d_mul_node, "", unreal.MaterialProperty.MP_EMISSIVE_COLOR)

d_op = unreal.MaterialEditingLibrary.create_material_expression(m_disc, unreal.MaterialExpressionScalarParameter, -400, 150)
d_op.set_editor_property("parameter_name", "Opacity")
d_op.set_editor_property("default_value", 0.12)
unreal.MaterialEditingLibrary.connect_material_property(d_op, "", unreal.MaterialProperty.MP_OPACITY)

unreal.MaterialEditingLibrary.recompile_material(m_disc)
unreal.EditorAssetLibrary.save_loaded_asset(m_disc)

# 4. Earth Atmosphere
unreal.EditorAssetLibrary.delete_asset("/Game/Earth/M_Atmosphere")
m_atmo = asset_tools.create_asset("M_Atmosphere", "/Game/Earth", unreal.Material, mat_factory)
m_atmo.set_editor_property("two_sided", True)
m_atmo.set_editor_property("blend_mode", unreal.BlendMode.BLEND_TRANSLUCENT)
m_atmo.set_editor_property("shading_model", unreal.MaterialShadingModel.MSM_UNLIT)

fresnel = unreal.MaterialEditingLibrary.create_material_expression(m_atmo, unreal.MaterialExpressionFresnel, -400, 100)
fresnel.set_editor_property("exponent", 3.8)
fresnel.set_editor_property("base_reflect_fraction", 0.04)

atmo_col = unreal.MaterialEditingLibrary.create_material_expression(m_atmo, unreal.MaterialExpressionVectorParameter, -400, -100)
atmo_col.set_editor_property("parameter_name", "AtmosphereColor")
atmo_col.set_editor_property("default_value", unreal.LinearColor(0.25, 0.65, 1.0, 1.0))

atmo_mult = unreal.MaterialEditingLibrary.create_material_expression(m_atmo, unreal.MaterialExpressionMultiply, -150, -50)
unreal.MaterialEditingLibrary.connect_material_expressions(atmo_col, "", atmo_mult, "A")
unreal.MaterialEditingLibrary.connect_material_expressions(fresnel, "", atmo_mult, "B")
unreal.MaterialEditingLibrary.connect_material_property(atmo_mult, "", unreal.MaterialProperty.MP_EMISSIVE_COLOR)

op_mult = unreal.MaterialEditingLibrary.create_material_expression(m_atmo, unreal.MaterialExpressionScalarParameter, -400, 250)
op_mult.set_editor_property("parameter_name", "OpacityMultiplier")
op_mult.set_editor_property("default_value", 0.65)

atmo_op = unreal.MaterialEditingLibrary.create_material_expression(m_atmo, unreal.MaterialExpressionMultiply, -150, 150)
unreal.MaterialEditingLibrary.connect_material_expressions(fresnel, "", atmo_op, "A")
unreal.MaterialEditingLibrary.connect_material_expressions(op_mult, "", atmo_op, "B")
unreal.MaterialEditingLibrary.connect_material_property(atmo_op, "", unreal.MaterialProperty.MP_OPACITY)

unreal.MaterialEditingLibrary.recompile_material(m_atmo)
unreal.EditorAssetLibrary.save_loaded_asset(m_atmo)

def apply_earth_materials():
    emesh = earth_actor.get_editor_property("earth_mesh")
    if emesh:
        emesh.set_material(0, m_earth)
        emesh.set_relative_scale3d(unreal.Vector(1275.6274, 1275.6274, 1275.6274))
    atm = earth_actor.get_editor_property("atmosphere_mesh")
    if atm:
        atm.set_material(0, m_atmo)
        atm.set_relative_scale3d(unreal.Vector(1.015, 1.015, 1.015))
        atm.set_visibility(True)
        atm.set_hidden_in_game(False)

apply_earth_materials()

def apply_satellite_materials(sat, is_manoeuvred=False):
    # Gold Foil Bus
    body = sat.get_editor_property("satellite_body")
    if body:
        mat_b = body.create_dynamic_material_instance(0, m_solid)
        if is_manoeuvred:
            mat_b.set_vector_parameter_value("Color", unreal.LinearColor(0.1, 0.95, 0.45, 1.0))
            mat_b.set_scalar_parameter_value("Metallic", 0.95)
            mat_b.set_scalar_parameter_value("Roughness", 0.22)
            mat_b.set_scalar_parameter_value("EmissiveMultiplier", 0.25)
        else:
            mat_b.set_vector_parameter_value("Color", unreal.LinearColor(1.0, 0.84, 0.30, 1.0))
            mat_b.set_scalar_parameter_value("Metallic", 0.98)
            mat_b.set_scalar_parameter_value("Roughness", 0.16)
            mat_b.set_scalar_parameter_value("EmissiveMultiplier", 0.20)
        body.set_material(0, mat_b)

    # Segmented Solar Array Panels (Left, Left Outboard, Right, Right Outboard)
    # Give inner and outer panels slightly distinct micro-roughness for visible cell segmentation
    for i, p_name in enumerate(["solar_panel_left", "solar_panel_left_outboard", "solar_panel_right", "solar_panel_right_outboard"]):
        p_comp = sat.get_editor_property(p_name)
        if p_comp:
            mat_blue = p_comp.create_dynamic_material_instance(0, m_solid)
            # Subtle variation between inner and outer solar cells
            cell_blue = unreal.LinearColor(0.012, 0.055, 0.42, 1.0) if i in [0, 2] else unreal.LinearColor(0.010, 0.045, 0.36, 1.0)
            mat_blue.set_vector_parameter_value("Color", cell_blue)
            mat_blue.set_scalar_parameter_value("Metallic", 0.92)
            mat_blue.set_scalar_parameter_value("Roughness", 0.12)
            mat_blue.set_scalar_parameter_value("EmissiveMultiplier", 0.18)
            p_comp.set_material(0, mat_blue)

    # Aerospace Silver Metal (Payload deck, yokes, mast, thruster nozzle)
    for m_name in ["payload_deck", "solar_yoke_left", "solar_yoke_right", "antenna_mast", "thruster_nozzle"]:
        m_comp = sat.get_editor_property(m_name)
        if m_comp:
            mat_silver = m_comp.create_dynamic_material_instance(0, m_solid)
            mat_silver.set_vector_parameter_value("Color", unreal.LinearColor(0.85, 0.88, 0.92, 1.0))
            mat_silver.set_scalar_parameter_value("Metallic", 0.98)
            mat_silver.set_scalar_parameter_value("Roughness", 0.18)
            mat_silver.set_scalar_parameter_value("EmissiveMultiplier", 0.15)
            m_comp.set_material(0, mat_silver)

    # Gold Reflector Dish
    dish = sat.get_editor_property("antenna_dish")
    if dish:
        mat_dish = dish.create_dynamic_material_instance(0, m_solid)
        mat_dish.set_vector_parameter_value("Color", unreal.LinearColor(1.0, 0.88, 0.48, 1.0))
        mat_dish.set_scalar_parameter_value("Metallic", 0.98)
        mat_dish.set_scalar_parameter_value("Roughness", 0.14)
        mat_dish.set_scalar_parameter_value("EmissiveMultiplier", 0.25)
        dish.set_material(0, mat_dish)

    # Dark Optical Sensor Aperture
    sensor = sat.get_editor_property("earth_sensor")
    if sensor:
        mat_sensor = sensor.create_dynamic_material_instance(0, m_solid)
        mat_sensor.set_vector_parameter_value("Color", unreal.LinearColor(0.02, 0.025, 0.035, 1.0))
        mat_sensor.set_scalar_parameter_value("Metallic", 0.05)
        mat_sensor.set_scalar_parameter_value("Roughness", 0.08)
        mat_sensor.set_scalar_parameter_value("EmissiveMultiplier", 0.05)
        sensor.set_material(0, mat_sensor)

def apply_debris_materials(deb):
    for c_name in ["debris_mesh", "fragment_shard_a", "torn_strut"]:
        c_comp = deb.get_editor_property(c_name)
        if c_comp:
            mat_alloy = c_comp.create_dynamic_material_instance(0, m_solid)
            mat_alloy.set_vector_parameter_value("Color", unreal.LinearColor(0.70, 0.68, 0.66, 1.0))
            mat_alloy.set_scalar_parameter_value("Metallic", 0.88)
            mat_alloy.set_scalar_parameter_value("Roughness", 0.40)
            mat_alloy.set_scalar_parameter_value("EmissiveMultiplier", 0.20)
            c_comp.set_material(0, mat_alloy)

    shard_b = deb.get_editor_property("fragment_shard_b")
    if shard_b:
        mat_hazard = shard_b.create_dynamic_material_instance(0, m_solid)
        mat_hazard.set_vector_parameter_value("Color", unreal.LinearColor(1.0, 0.38, 0.02, 1.0))
        mat_hazard.set_scalar_parameter_value("Metallic", 0.45)
        mat_hazard.set_scalar_parameter_value("Roughness", 0.25)
        mat_hazard.set_scalar_parameter_value("EmissiveMultiplier", 0.40)
        shard_b.set_material(0, mat_hazard)

# Path trajectories setup
sat_nom_raw = payload["time_series"]["satellite_nominal_positions_ue"]
debris_raw = payload["time_series"]["debris_positions_ue"]
sat_mod_raw = payload["time_series"]["satellite_modified_positions_ue"]
sat_nom_pts = [unreal.Vector(p[0], p[1], p[2]) for p in sat_nom_raw]
debris_pts = [unreal.Vector(p[0], p[1], p[2]) for p in debris_raw]
sat_mod_pts = [unreal.Vector(p[0], p[1], p[2]) for p in sat_mod_raw]

def look_at(cam_pos, target_pos):
    dx = target_pos.x - cam_pos.x
    dy = target_pos.y - cam_pos.y
    dz = target_pos.z - cam_pos.z
    yaw = math.degrees(math.atan2(dy, dx))
    dist_xy = math.sqrt(dx*dx + dy*dy)
    pitch = math.degrees(math.atan2(dz, dist_xy))
    return unreal.Rotator(pitch=pitch, yaw=yaw, roll=0.0)

out_dir = (unreal.Paths.project_saved_dir() + "Screenshots/WindowsEditor").replace("\\", "/")

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
sun_earth_rot = unreal.Rotator(pitch=-22.0, yaw=148.0, roll=0.0)

# ==============================================================================
# POLISH SHOT 1: Milestone2_Earth_Overview
# Complete Earth globe fully in frame, all 3 trajectories distinguishable
# ==============================================================================
print(">>> Rendering Polished Earth Overview...")
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

# All 3 trajectories visible and distinguishable with crisp 28 uu geometry
if sat_nominal_path:
    sat_nominal_path.set_editor_property("path_thickness", 28.0)
    sat_nominal_path.set_trajectory_points(sat_nom_pts, unreal.LinearColor(0.0, 0.85, 1.0, 1.0)) # Cyan
    sat_nominal_path.set_actor_hidden_in_game(False)
if debris_path:
    debris_path.set_editor_property("path_thickness", 28.0)
    debris_path.set_trajectory_points(debris_pts, unreal.LinearColor(1.0, 0.15, 0.1, 1.0))        # Red
    debris_path.set_actor_hidden_in_game(False)
if sat_modified_path:
    sat_modified_path.set_editor_property("path_thickness", 28.0)
    sat_modified_path.set_trajectory_points(sat_mod_pts, unreal.LinearColor(0.15, 1.0, 0.35, 1.0)) # Green
    sat_modified_path.set_actor_hidden_in_game(False)

if conj_viz:
    conj_viz.set_actor_hidden_in_game(True)
if man_viz:
    man_viz.set_actor_hidden_in_game(True)

# Pulled back camera distance ~172,000 uu so the entire Earth sphere (127,562 uu diameter)
# is 100% visible with elegant space breathing margins around all borders
cam_overview_loc = unreal.Vector(155000.0, -60000.0, 42000.0)
cam_overview_rot = look_at(cam_overview_loc, unreal.Vector(0.0, 0.0, 0.0))
capture_view("Milestone2_Earth_Overview", cam_overview_loc, cam_overview_rot, fov=56.0, sun_rotation=sun_earth_rot, sun_intensity=14.0)

# ==============================================================================
# POLISH SHOT 2: Milestone2_Satellite_Detail
# Improved PBR specular lighting and panel segmentation
# ==============================================================================
print(">>> Rendering Polished Satellite Detail...")
if debris_actor:
    debris_actor.set_actor_location(FAR_AWAY, False, False)
    debris_actor.set_actor_hidden_in_game(True)

if sat_nominal_path:
    sat_nominal_path.set_actor_hidden_in_game(True)
if debris_path:
    debris_path.set_actor_hidden_in_game(True)
if sat_modified_path:
    sat_modified_path.set_actor_hidden_in_game(True)

if sat_actor:
    sat_actor.set_actor_scale3d(unreal.Vector(1.0, 1.0, 1.0))
    sat_actor.set_actor_location_and_rotation(sat_pos_0, unreal.Rotator(0.0, -90.0, 0.0), False, False)
    sat_actor.set_actor_hidden_in_game(False)
    apply_satellite_materials(sat_actor, is_manoeuvred=False)

# Camera positioned for dynamic 3/4 aerospace framing
sat_cam_loc = unreal.Vector(sat_pos_0.x - 1700.0, sat_pos_0.y - 1150.0, sat_pos_0.z + 550.0)
sat_cam_rot = look_at(sat_cam_loc, unreal.Vector(sat_pos_0.x, sat_pos_0.y, sat_pos_0.z + 30.0))

# 3-point key lighting at 35 deg offset to highlight metallic gleam and panel bevels
sun_sat_rot = unreal.Rotator(pitch=sat_cam_rot.pitch - 20.0, yaw=sat_cam_rot.yaw - 35.0, roll=0.0)
capture_view("Milestone2_Satellite_Detail", sat_cam_loc, sat_cam_rot, fov=46.0, sun_rotation=sun_sat_rot, sun_intensity=15.0)

# ==============================================================================
# POLISH SHOT 3: Milestone2_Conjunction_TCA
# Reduced compact encounter disc (radius 9.5 uu), crisp miss distance line, balanced framing
# ==============================================================================
print(">>> Rendering Polished Conjunction TCA...")
nom_tca_s = payload["nominal_encounter"]["tca_seconds"]
ts = payload["time_series"]["timestamps_sec"]
tca_idx = min(range(len(ts)), key=lambda i: abs(ts[i] - nom_tca_s))
sat_tca_pos = sat_nom_pts[tca_idx]
deb_tca_pos = debris_pts[tca_idx]
miss_dist_uu = payload["nominal_encounter"]["miss_distance_m"] * payload["scenario_metadata"]["scale_factor_uu_per_m"]

tca_mid = unreal.Vector((sat_tca_pos.x + deb_tca_pos.x) * 0.5, (sat_tca_pos.y + deb_tca_pos.y) * 0.5, (sat_tca_pos.z + deb_tca_pos.z) * 0.5)

if conj_viz:
    conj_viz.set_actor_location(sat_tca_pos, False, False)
    conj_viz.set_actor_hidden_in_game(False)

    # 1. TCA Marker Spheres (1.4 uu diameter)
    tca_sph = conj_viz.get_editor_property("tca_marker_sphere")
    if tca_sph:
        tca_sph.set_world_scale3d(unreal.Vector(0.014, 0.014, 0.014))
        mat_tca = tca_sph.create_dynamic_material_instance(0, m_solid)
        mat_tca.set_vector_parameter_value("Color", unreal.LinearColor(1.0, 0.85, 0.05, 1.0))
        mat_tca.set_scalar_parameter_value("EmissiveMultiplier", 2.5)
        tca_sph.set_material(0, mat_tca)

    deb_sph = conj_viz.get_editor_property("debris_tca_marker_sphere")
    if deb_sph:
        deb_sph.set_world_location(deb_tca_pos, False, False)
        deb_sph.set_world_scale3d(unreal.Vector(0.014, 0.014, 0.014))
        mat_deb = deb_sph.create_dynamic_material_instance(0, m_solid)
        mat_deb.set_vector_parameter_value("Color", unreal.LinearColor(1.0, 0.15, 0.1, 1.0))
        mat_deb.set_scalar_parameter_value("EmissiveMultiplier", 2.5)
        deb_sph.set_material(0, mat_deb)

    # 2. Miss Distance Connector Line (vibrant luminous magenta, 0.5 uu diameter)
    dx = deb_tca_pos.x - sat_tca_pos.x
    dy = deb_tca_pos.y - sat_tca_pos.y
    dz = deb_tca_pos.z - sat_tca_pos.z
    dist = math.sqrt(dx*dx + dy*dy + dz*dz)
    rot_line = look_at(sat_tca_pos, deb_tca_pos)
    rot_cyl = unreal.Rotator(pitch=rot_line.pitch - 90.0, yaw=rot_line.yaw, roll=0.0)

    line = conj_viz.get_editor_property("miss_distance_line")
    if line:
        line.set_world_location(tca_mid, False, False)
        line.set_world_rotation(rot_cyl, False, False)
        line.set_world_scale3d(unreal.Vector(0.005, 0.005, dist / 100.0))
        mat_line = line.create_dynamic_material_instance(0, m_solid)
        mat_line.set_vector_parameter_value("Color", unreal.LinearColor(1.0, 0.04, 0.72, 1.0))
        mat_line.set_scalar_parameter_value("EmissiveMultiplier", 2.8)
        line.set_material(0, mat_line)

    # 3. Compact Encounter Plane Disc (radius 9.5 uu, diameter 19 uu - neatly wraps the 15.63 uu separation)
    rot_disc = unreal.Rotator(pitch=rot_line.pitch - 45.0, yaw=rot_line.yaw + 35.0, roll=0.0)
    disc = conj_viz.get_editor_property("encounter_plane_disc")
    if disc and m_disc:
        disc.set_world_location(tca_mid, False, False)
        disc.set_world_rotation(rot_disc, False, False)
        disc.set_world_scale3d(unreal.Vector(9.5 / 50.0, 9.5 / 50.0, 0.0015))
        mat_disc = disc.create_dynamic_material_instance(0, m_disc)
        mat_disc.set_vector_parameter_value("Color", unreal.LinearColor(0.70, 0.22, 1.0, 1.0))
        mat_disc.set_scalar_parameter_value("Opacity", 0.12)
        disc.set_material(0, mat_disc)

# Dock small spacecraft and debris models with proportional scales
if sat_actor:
    sat_actor.set_actor_scale3d(unreal.Vector(0.014, 0.014, 0.014))
    sat_actor.set_actor_location(sat_tca_pos, False, False)
    sat_actor.set_actor_hidden_in_game(False)
    apply_satellite_materials(sat_actor)

if debris_actor:
    debris_actor.set_actor_scale3d(unreal.Vector(0.014, 0.014, 0.014))
    debris_actor.set_actor_location(deb_tca_pos, False, False)
    debris_actor.set_actor_hidden_in_game(False)
    apply_debris_materials(debris_actor)

# Balanced camera framing: 32 uu distance, elevated +12 uu, framing both objects diagonally
tca_cam_loc = unreal.Vector(tca_mid.x + 10.0, tca_mid.y + 31.0, tca_mid.z + 12.0)
tca_cam_rot = look_at(tca_cam_loc, tca_mid)
sun_tca_rot = unreal.Rotator(pitch=tca_cam_rot.pitch - 15.0, yaw=tca_cam_rot.yaw - 25.0, roll=0.0)
capture_view("Milestone2_Conjunction_TCA", tca_cam_loc, tca_cam_rot, fov=38.0, sun_rotation=sun_tca_rot, sun_intensity=14.0)

# Save the level
unreal.EditorLevelLibrary.save_current_level()
print("[LEVEL] Saved.")
print("Polish pass complete!")
unreal.SystemLibrary.execute_console_command(None, "QUIT_EDITOR")

