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

# Hide terrestrial clutter
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

# Materials
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
em_param.set_editor_property("default_value", 0.5)

mult_expr = unreal.MaterialEditingLibrary.create_material_expression(m_solid, unreal.MaterialExpressionMultiply, -200, 0)
unreal.MaterialEditingLibrary.connect_material_expressions(col_param, "", mult_expr, "A")
unreal.MaterialEditingLibrary.connect_material_expressions(em_param, "", mult_expr, "B")
unreal.MaterialEditingLibrary.connect_material_property(mult_expr, "", unreal.MaterialProperty.MP_EMISSIVE_COLOR)

unreal.MaterialEditingLibrary.recompile_material(m_solid)
unreal.EditorAssetLibrary.save_loaded_asset(m_solid)

# Translucent disc
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
d_mult.set_editor_property("default_value", 0.8)

d_mul_node = unreal.MaterialEditingLibrary.create_material_expression(m_disc, unreal.MaterialExpressionMultiply, -200, -50)
unreal.MaterialEditingLibrary.connect_material_expressions(d_col, "", d_mul_node, "A")
unreal.MaterialEditingLibrary.connect_material_expressions(d_mult, "", d_mul_node, "B")
unreal.MaterialEditingLibrary.connect_material_property(d_mul_node, "", unreal.MaterialProperty.MP_EMISSIVE_COLOR)

d_op = unreal.MaterialEditingLibrary.create_material_expression(m_disc, unreal.MaterialExpressionScalarParameter, -400, 150)
d_op.set_editor_property("parameter_name", "Opacity")
d_op.set_editor_property("default_value", 0.15)
unreal.MaterialEditingLibrary.connect_material_property(d_op, "", unreal.MaterialProperty.MP_OPACITY)

unreal.MaterialEditingLibrary.recompile_material(m_disc)
unreal.EditorAssetLibrary.save_loaded_asset(m_disc)

def apply_satellite_materials(sat):
    body = sat.get_editor_property("satellite_body")
    if body:
        mat_b = body.create_dynamic_material_instance(0, m_solid)
        mat_b.set_vector_parameter_value("Color", unreal.LinearColor(0.98, 0.82, 0.28, 1.0))
        mat_b.set_scalar_parameter_value("EmissiveMultiplier", 0.4)
        body.set_material(0, mat_b)
    for p_name in ["solar_panel_left", "solar_panel_left_outboard", "solar_panel_right", "solar_panel_right_outboard"]:
        p_comp = sat.get_editor_property(p_name)
        if p_comp:
            mat_blue = p_comp.create_dynamic_material_instance(0, m_solid)
            mat_blue.set_vector_parameter_value("Color", unreal.LinearColor(0.015, 0.08, 0.55, 1.0))
            mat_blue.set_scalar_parameter_value("EmissiveMultiplier", 0.35)
            p_comp.set_material(0, mat_blue)
    for m_name in ["payload_deck", "solar_yoke_left", "solar_yoke_right", "antenna_mast", "thruster_nozzle"]:
        m_comp = sat.get_editor_property(m_name)
        if m_comp:
            mat_silver = m_comp.create_dynamic_material_instance(0, m_solid)
            mat_silver.set_vector_parameter_value("Color", unreal.LinearColor(0.78, 0.82, 0.86, 1.0))
            mat_silver.set_scalar_parameter_value("EmissiveMultiplier", 0.25)
            m_comp.set_material(0, mat_silver)
    dish = sat.get_editor_property("antenna_dish")
    if dish:
        mat_dish = dish.create_dynamic_material_instance(0, m_solid)
        mat_dish.set_vector_parameter_value("Color", unreal.LinearColor(0.95, 0.88, 0.55, 1.0))
        mat_dish.set_scalar_parameter_value("EmissiveMultiplier", 0.4)
        dish.set_material(0, mat_dish)
    sensor = sat.get_editor_property("earth_sensor")
    if sensor:
        mat_sensor = sensor.create_dynamic_material_instance(0, m_solid)
        mat_sensor.set_vector_parameter_value("Color", unreal.LinearColor(0.02, 0.03, 0.05, 1.0))
        sensor.set_material(0, mat_sensor)

def apply_debris_materials(deb):
    for c_name in ["debris_mesh", "fragment_shard_a", "torn_strut"]:
        c_comp = deb.get_editor_property(c_name)
        if c_comp:
            mat_alloy = c_comp.create_dynamic_material_instance(0, m_solid)
            mat_alloy.set_vector_parameter_value("Color", unreal.LinearColor(0.72, 0.70, 0.68, 1.0))
            mat_alloy.set_scalar_parameter_value("EmissiveMultiplier", 0.3)
            c_comp.set_material(0, mat_alloy)
    shard_b = deb.get_editor_property("fragment_shard_b")
    if shard_b:
        mat_hazard = shard_b.create_dynamic_material_instance(0, m_solid)
        mat_hazard.set_vector_parameter_value("Color", unreal.LinearColor(1.0, 0.35, 0.02, 1.0))
        mat_hazard.set_scalar_parameter_value("EmissiveMultiplier", 0.5)
        shard_b.set_material(0, mat_hazard)

# Path trajectories setup
sat_nom_raw = payload["time_series"]["satellite_nominal_positions_ue"]
debris_raw = payload["time_series"]["debris_positions_ue"]
sat_nom_pts = [unreal.Vector(p[0], p[1], p[2]) for p in sat_nom_raw]
debris_pts = [unreal.Vector(p[0], p[1], p[2]) for p in debris_raw]

def setup_path_geometry(path_actor, pts, color, thickness=8.0):
    if not path_actor:
        return
    path_actor.set_editor_property("path_thickness", thickness)
    path_actor.set_trajectory_points(pts, color)
    path_actor.set_actor_hidden_in_game(False)

setup_path_geometry(sat_nominal_path, sat_nom_pts, unreal.LinearColor(0.0, 0.85, 1.0, 1.0), 8.0)
setup_path_geometry(debris_path, debris_pts, unreal.LinearColor(1.0, 0.15, 0.1, 1.0), 8.0)
if sat_modified_path:
    sat_modified_path.set_actor_hidden_in_game(True)

def look_at(cam_pos, target_pos):
    dx = target_pos.x - cam_pos.x
    dy = target_pos.y - cam_pos.y
    dz = target_pos.z - cam_pos.z
    yaw = math.degrees(math.atan2(dy, dx))
    dist_xy = math.sqrt(dx*dx + dy*dy)
    pitch = math.degrees(math.atan2(dz, dist_xy))
    return unreal.Rotator(pitch=pitch, yaw=yaw, roll=0.0)

out_dir = (unreal.Paths.project_saved_dir() + "Screenshots/WindowsEditor").replace("\\", "/")

def capture_view(filename_base, cam_location, cam_rotation, fov=60.0):
    if dir_light:
        dir_light.set_actor_rotation(cam_rotation, False)
        comp = dir_light.get_component_by_class(unreal.DirectionalLightComponent)
        comp.set_editor_property("intensity", 14.0)

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

# ==============================================================================
# TEST 1: Calibrated Encounter Overview (t = 0)
# Framed from X = 68800, Y = +180, Z = +380 looking down-track towards (70000, -50, 0)
# ==============================================================================
sat_pos_0 = sat_nom_pts[0] # (70000, 0, 0)
deb_pos_0 = debris_pts[0]   # (70000, -100, 0)

sat_actor.set_actor_scale3d(unreal.Vector(0.35, 0.35, 0.35))
sat_actor.set_actor_location_and_rotation(sat_pos_0, unreal.Rotator(0.0, -90.0, 0.0), False, False)
sat_actor.set_actor_hidden_in_game(False)
apply_satellite_materials(sat_actor)

debris_actor.set_actor_scale3d(unreal.Vector(0.35, 0.35, 0.35))
debris_actor.set_actor_location(deb_pos_0, False, False)
debris_actor.set_actor_hidden_in_game(False)
apply_debris_materials(debris_actor)

sat_nominal_path.set_actor_hidden_in_game(False)
debris_path.set_actor_hidden_in_game(False)
conj_viz.set_actor_hidden_in_game(True)
man_viz.set_actor_hidden_in_game(True)

mid_enc = unreal.Vector(70000.0, -50.0, 0.0)
# 3/4 elevated vantage looking down-track and outboard into space:
enc_cam_loc = unreal.Vector(mid_enc.x - 1100.0, mid_enc.y + 220.0, mid_enc.z + 420.0)
enc_cam_rot = look_at(enc_cam_loc, mid_enc)
capture_view("Test_Encounter_Calibrated", enc_cam_loc, enc_cam_rot, fov=44.0)

# ==============================================================================
# TEST 2: Calibrated Conjunction TCA
# ==============================================================================
sat_nominal_path.set_actor_hidden_in_game(True)
debris_path.set_actor_hidden_in_game(True)

nom_tca_s = payload["nominal_encounter"]["tca_seconds"]
ts = payload["time_series"]["timestamps_sec"]
tca_idx = min(range(len(ts)), key=lambda i: abs(ts[i] - nom_tca_s))
sat_tca_pos = sat_nom_pts[tca_idx]
deb_tca_pos = debris_pts[tca_idx]
miss_dist_uu = payload["nominal_encounter"]["miss_distance_m"] * payload["scenario_metadata"]["scale_factor_uu_per_m"]

tca_mid = unreal.Vector((sat_tca_pos.x + deb_tca_pos.x) * 0.5, (sat_tca_pos.y + deb_tca_pos.y) * 0.5, (sat_tca_pos.z + deb_tca_pos.z) * 0.5)

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
dist = math.sqrt(dx*dx + dy*dy + dz*dz) # 15.635 uu
rot_line = look_at(sat_tca_pos, deb_tca_pos)
rot_cyl = unreal.Rotator(pitch=rot_line.pitch - 90.0, yaw=rot_line.yaw, roll=0.0)

line = conj_viz.get_editor_property("miss_distance_line")
if line:
    line.set_world_location(tca_mid, False, False)
    line.set_world_rotation(rot_cyl, False, False)
    line.set_world_scale3d(unreal.Vector(0.006, 0.006, dist / 100.0))
    mat_line = line.create_dynamic_material_instance(0, m_solid)
    mat_line.set_vector_parameter_value("Color", unreal.LinearColor(1.0, 0.05, 0.70, 1.0))
    mat_line.set_scalar_parameter_value("EmissiveMultiplier", 2.5)
    line.set_material(0, mat_line)

# Center encounter disc at tca_mid so it frames both objects symmetrically
disc = conj_viz.get_editor_property("encounter_plane_disc")
if disc and m_disc:
    disc.set_world_location(tca_mid, False, False)
    disc.set_world_rotation(rot_cyl, False, False)
    # Radius 12 uu (diameter 24 uu)
    disc.set_world_scale3d(unreal.Vector(12.0 / 50.0, 12.0 / 50.0, 0.002))
    mat_disc = disc.create_dynamic_material_instance(0, m_disc)
    disc.set_material(0, mat_disc)

# Dock small satellite and debris models
sat_actor.set_actor_scale3d(unreal.Vector(0.012, 0.012, 0.012))
sat_actor.set_actor_location(sat_tca_pos, False, False)
sat_actor.set_actor_hidden_in_game(False)
apply_satellite_materials(sat_actor)

debris_actor.set_actor_scale3d(unreal.Vector(0.012, 0.012, 0.012))
debris_actor.set_actor_location(deb_tca_pos, False, False)
debris_actor.set_actor_hidden_in_game(False)
apply_debris_materials(debris_actor)

# Camera: perpendicular to miss distance vector looking outward away from Earth into space
tca_cam_loc = unreal.Vector(tca_mid.x + 11.32, tca_mid.y + 36.24, tca_mid.z + 14.0)
tca_cam_rot = look_at(tca_cam_loc, tca_mid)
capture_view("Test_TCA_Calibrated", tca_cam_loc, tca_cam_rot, fov=40.0)

print("Tests completed successfully!")
unreal.SystemLibrary.execute_console_command(None, "QUIT_EDITOR")
