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

for a in all_actors:
    if isinstance(a, unreal.OrbitPathActor):
        a.set_actor_hidden_in_game(True)

conj_viz.set_actor_hidden_in_game(False)
man_viz.set_actor_hidden_in_game(True)

asset_tools = unreal.AssetToolsHelpers.get_asset_tools()
mat_factory = unreal.MaterialFactoryNew()

# Solid color material
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

# Translucent subtle glowing disc material
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
d_op.set_editor_property("default_value", 0.18)
unreal.MaterialEditingLibrary.connect_material_property(d_op, "", unreal.MaterialProperty.MP_OPACITY)

unreal.MaterialEditingLibrary.recompile_material(m_disc)
unreal.EditorAssetLibrary.save_loaded_asset(m_disc)

# Setup TCA geometry
nom_tca_s = payload["nominal_encounter"]["tca_seconds"]
ts = payload["time_series"]["timestamps_sec"]
tca_idx = min(range(len(ts)), key=lambda i: abs(ts[i] - nom_tca_s))
sat_nom_pts = [unreal.Vector(p[0], p[1], p[2]) for p in payload["time_series"]["satellite_nominal_positions_ue"]]
debris_pts = [unreal.Vector(p[0], p[1], p[2]) for p in payload["time_series"]["debris_positions_ue"]]
sat_tca_pos = sat_nom_pts[tca_idx]
deb_tca_pos = debris_pts[tca_idx]
miss_dist_uu = payload["nominal_encounter"]["miss_distance_m"] * payload["scenario_metadata"]["scale_factor_uu_per_m"]

conj_viz.update_conjunction_geometry(sat_tca_pos, deb_tca_pos, miss_dist_uu)
conj_viz.set_actor_location(sat_tca_pos, False, False)

# Component scaling and materials
tca_sph = conj_viz.get_editor_property("tca_marker_sphere")
if tca_sph:
    tca_sph.set_world_scale3d(unreal.Vector(2.0, 2.0, 2.0))
    mat_tca = tca_sph.create_dynamic_material_instance(0, m_solid)
    mat_tca.set_vector_parameter_value("Color", unreal.LinearColor(1.0, 0.82, 0.05, 1.0))
    mat_tca.set_scalar_parameter_value("EmissiveMultiplier", 2.2)
    tca_sph.set_material(0, mat_tca)

deb_sph = conj_viz.get_editor_property("debris_tca_marker_sphere")
if deb_sph:
    deb_sph.set_world_scale3d(unreal.Vector(2.0, 2.0, 2.0))
    mat_deb = deb_sph.create_dynamic_material_instance(0, m_solid)
    mat_deb.set_vector_parameter_value("Color", unreal.LinearColor(1.0, 0.15, 0.1, 1.0))
    mat_deb.set_scalar_parameter_value("EmissiveMultiplier", 2.2)
    deb_sph.set_material(0, mat_deb)

line = conj_viz.get_editor_property("miss_distance_line")
if line:
    line.set_world_scale3d(unreal.Vector(0.5, 0.5, miss_dist_uu / 100.0))
    mat_line = line.create_dynamic_material_instance(0, m_solid)
    mat_line.set_vector_parameter_value("Color", unreal.LinearColor(1.0, 0.05, 0.70, 1.0))
    mat_line.set_scalar_parameter_value("EmissiveMultiplier", 2.5)
    line.set_material(0, mat_line)

disc = conj_viz.get_editor_property("encounter_plane_disc")
if disc and m_disc:
    disc.set_world_scale3d(unreal.Vector(miss_dist_uu * 1.6 / 50.0, miss_dist_uu * 1.6 / 50.0, 0.005))
    mat_disc = disc.create_dynamic_material_instance(0, m_disc)
    disc.set_material(0, mat_disc)

# Dock small satellite and debris
sat_actor.set_actor_scale3d(unreal.Vector(0.04, 0.04, 0.04))
sat_actor.set_actor_location(sat_tca_pos, False, False)
sat_actor.set_actor_hidden_in_game(False)
body = sat_actor.get_editor_property("satellite_body")
if body:
    mat_b = body.create_dynamic_material_instance(0, m_solid)
    mat_b.set_vector_parameter_value("Color", unreal.LinearColor(0.98, 0.82, 0.28, 1.0))
    body.set_material(0, mat_b)

debris_actor.set_actor_scale3d(unreal.Vector(0.04, 0.04, 0.04))
debris_actor.set_actor_location(deb_tca_pos, False, False)
debris_actor.set_actor_hidden_in_game(False)
dmesh = debris_actor.get_editor_property("debris_mesh")
if dmesh:
    mat_d = dmesh.create_dynamic_material_instance(0, m_solid)
    mat_d.set_vector_parameter_value("Color", unreal.LinearColor(0.72, 0.70, 0.68, 1.0))
    dmesh.set_material(0, mat_d)

def look_at(cam_pos, target_pos):
    dx = target_pos.x - cam_pos.x
    dy = target_pos.y - cam_pos.y
    dz = target_pos.z - cam_pos.z
    yaw = math.degrees(math.atan2(dy, dx))
    dist_xy = math.sqrt(dx*dx + dy*dy)
    pitch = math.degrees(math.atan2(dz, dist_xy))
    return unreal.Rotator(pitch=pitch, yaw=yaw, roll=0.0)

tca_mid = unreal.Vector((sat_tca_pos.x + deb_tca_pos.x) * 0.5, (sat_tca_pos.y + deb_tca_pos.y) * 0.5, (sat_tca_pos.z + deb_tca_pos.z) * 0.5)

# Perpendicular vantage to miss distance vector:
# Dir = (14.9, -4.66, 0)
# Perp = (4.66, 14.9, 0) -> normalized: (0.298, 0.954, 0)
# Place camera perpendicular and elevated:
tca_cam_loc = unreal.Vector(tca_mid.x + 22.4, tca_mid.y + 71.6, tca_mid.z + 40.0)
tca_cam_rot = look_at(tca_cam_loc, tca_mid)

out_dir = (unreal.Paths.project_saved_dir() + "Screenshots/WindowsEditor").replace("\\", "/")

capture_actor = unreal.EditorLevelLibrary.spawn_actor_from_class(unreal.SceneCapture2D, tca_cam_loc, tca_cam_rot)
comp = capture_actor.get_editor_property("capture_component2d")
comp.set_editor_property("fov_angle", 42.0)
comp.set_editor_property("capture_source", unreal.SceneCaptureSource.SCS_FINAL_COLOR_LDR)
pps = comp.get_editor_property("post_process_settings")
pps.set_editor_property("override_auto_exposure_bias", True)
pps.set_editor_property("auto_exposure_bias", 0.0)
comp.set_editor_property("post_process_settings", pps)

rt = unreal.RenderingLibrary.create_render_target2d(world, 1920, 1080, unreal.TextureRenderTargetFormat.RTF_RGBA8)
comp.set_editor_property("texture_target", rt)

# Directional light along sightline
if dir_light:
    dir_light.set_actor_rotation(tca_cam_rot, False)
    comp_dl = dir_light.get_component_by_class(unreal.DirectionalLightComponent)
    comp_dl.set_editor_property("intensity", 12.0)

comp.capture_scene()

unreal.RenderingLibrary.export_render_target(world, rt, out_dir, "Test_TCA_Perpendicular.png")
unreal.EditorLevelLibrary.destroy_actor(capture_actor)
print("Saved Test_TCA_Perpendicular.png")

unreal.SystemLibrary.execute_console_command(None, "QUIT_EDITOR")
