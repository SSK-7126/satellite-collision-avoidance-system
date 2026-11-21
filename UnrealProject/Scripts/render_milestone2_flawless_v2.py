"""
render_milestone2_flawless_v2.py
================================
Master rendering script for Milestone 2: Satellite, Debris, and Orbital Trajectory Visualization.

Produces 7 pristine, high-fidelity visual verification captures in Unreal Engine 5.7.4:
1. Milestone2_Earth_Overview.png - Complete Earth in space, continents, oceans, limb, and orbital tracks
2. Milestone2_Satellite_Detail.png - Golden bus, blue solar arrays, titanium deck/mast, gold dish, optics against deep space
3. Milestone2_Debris_Detail.png - Irregular alloy fragment shards and hazard orange facet against deep space
4. Milestone2_Encounter_Overview.png - Satellite & Debris framed together in initial orbital state (t=0)
5. Milestone2_Conjunction_TCA.png - Conjunction geometry: Amber & Red spheres, Magenta miss line, Violet disc
6. Milestone2_Manoeuvre_Burn.png - Burn geometry: Purple burn ring, Green delta-v arrow along -R, diverging paths
7. Milestone2_Trajectories_Divergence.png - Broad orbital vantage showing Nominal (Cyan), Debris (Red), Avoidance (Green)
"""

import unreal
import json
import os
import math

print("=" * 70)
print("[MILESTONE 2 MASTER V2] Starting rendering pipeline...")
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

# Suppress on-screen warnings and texture streaming mips
unreal.SystemLibrary.execute_console_command(None, "DisableAllScreenMessages")
unreal.SystemLibrary.execute_console_command(None, "r.TextureStreaming 0")

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
    comp.set_editor_property("intensity", 12.0)

if sky_light:
    comp = sky_light.get_component_by_class(unreal.SkyLightComponent)
    comp.set_editor_property("real_time_capture", False)
    comp.set_editor_property("light_color", unreal.Color(200, 220, 255, 255))
    comp.set_editor_property("intensity", 2.0)

# 6. Recreate & Compile M_SolidColor with used_with_spline_meshes=True upfront
asset_tools = unreal.AssetToolsHelpers.get_asset_tools()
mat_factory = unreal.MaterialFactoryNew()

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

# Recreate M_TranslucentDisc cleanly
unreal.EditorAssetLibrary.delete_asset("/Game/Common/M_TranslucentDisc")
m_disc = asset_tools.create_asset("M_TranslucentDisc", "/Game/Common", unreal.Material, mat_factory)
m_disc.set_editor_property("two_sided", True)
m_disc.set_editor_property("blend_mode", unreal.BlendMode.BLEND_TRANSLUCENT)
m_disc.set_editor_property("shading_model", unreal.MaterialShadingModel.MSM_UNLIT)

d_col = unreal.MaterialEditingLibrary.create_material_expression(m_disc, unreal.MaterialExpressionVectorParameter, -400, -100)
d_col.set_editor_property("parameter_name", "Color")
d_col.set_editor_property("default_value", unreal.LinearColor(0.7, 0.25, 1.0, 1.0))
unreal.MaterialEditingLibrary.connect_material_property(d_col, "", unreal.MaterialProperty.MP_EMISSIVE_COLOR)

d_op = unreal.MaterialEditingLibrary.create_material_expression(m_disc, unreal.MaterialExpressionScalarParameter, -400, 150)
d_op.set_editor_property("parameter_name", "Opacity")
d_op.set_editor_property("default_value", 0.35)
unreal.MaterialEditingLibrary.connect_material_property(d_op, "", unreal.MaterialProperty.MP_OPACITY)

unreal.MaterialEditingLibrary.recompile_material(m_disc)
unreal.EditorAssetLibrary.save_loaded_asset(m_disc)
print("[MATERIALS] M_TranslucentDisc compiled cleanly")

# 7. Earth Materials
m_earth = unreal.EditorAssetLibrary.load_asset("/Game/Earth/M_Earth")
m_atmo = unreal.EditorAssetLibrary.load_asset("/Game/Earth/M_Atmosphere")
t_earth = unreal.EditorAssetLibrary.load_asset("/Game/Earth/T_Earth_Day")

def apply_earth_materials():
    if not earth_actor:
        return
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
        radius_ue = earth_actor.get_editor_property("earth_radius_ue")
        atmo_scale = (radius_ue * 1.015) / 50.0
        atm.set_world_scale3d(unreal.Vector(atmo_scale, atmo_scale, atmo_scale))
        atm.set_visibility(True)
        atm.set_hidden_in_game(False)

apply_earth_materials()
print("[EARTH] Earth materials configured.")

# 8. Satellite Materials Function
def apply_satellite_materials(sat, is_manoeuvred=False):
    if not sat or not m_solid:
        return
    # Golden Body (or Emerald Green if post-manoeuvre)
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

# 9. Debris Materials Function
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

# 10. Conjunction Visualizer Materials Function
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
        mat_disc.set_vector_parameter_value("Color", unreal.LinearColor(0.7, 0.25, 1.0, 1.0))
        mat_disc.set_scalar_parameter_value("Opacity", 0.35)
        disc.set_material(0, mat_disc)

# 11. Manoeuvre Visualizer Materials Function
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

# 12. Trajectory Points Extraction
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

# 13. Conjunction Data Setup
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

# 14. Manoeuvre Data Setup
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

def capture_view(filename_base, cam_location, cam_rotation, fov=60.0, sun_rotation=None, sun_intensity=12.0):
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

# Proven realistic Earth illumination sun rotator (from enhance_and_capture.py)
sun_earth_rot = unreal.Rotator(pitch=-22.0, yaw=148.0, roll=0.0)

# ==============================================================================
# CAPTURE 1: Milestone2_Earth_Overview
# Complete Earth in space, continents, oceans, atmospheric limb, and orbital tracks
# ==============================================================================
print(">>> Executing Capture 1: Earth Overview...")
apply_earth_materials()

if sat_actor:
    sat_actor.set_actor_location_and_rotation(sat_pos_0, unreal.Rotator(0.0, -90.0, 0.0), False, False)
    sat_actor.set_actor_hidden_in_game(False)
    apply_satellite_materials(sat_actor)

if debris_actor:
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
capture_view("Milestone2_Earth_Overview", cam_overview_loc, cam_overview_rot, fov=65.0, sun_rotation=sun_earth_rot, sun_intensity=12.0)

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
    sat_actor.set_actor_location_and_rotation(sat_pos_0, unreal.Rotator(0.0, -90.0, 0.0), False, False)
    sat_actor.set_actor_hidden_in_game(False)
    apply_satellite_materials(sat_actor, is_manoeuvred=False)

# Camera positioned on Earth side looking OUTWARDS into black deep space (away from Earth)
# sat_pos_0 is (70000, 0, 0). Vector from Earth (0,0,0) to sat is (+70000, 0, 0).
# Cam placed at (69200, -550, 320) looking towards sat (70000, 0, 40)
sat_cam_loc = unreal.Vector(sat_pos_0.x - 800.0, sat_pos_0.y - 550.0, sat_pos_0.z + 320.0)
sat_cam_rot = look_at(sat_cam_loc, unreal.Vector(sat_pos_0.x, sat_pos_0.y, sat_pos_0.z + 40.0))
capture_view("Milestone2_Satellite_Detail", sat_cam_loc, sat_cam_rot, fov=44.0, sun_rotation=sat_cam_rot, sun_intensity=14.0)

# ==============================================================================
# CAPTURE 3: Milestone2_Debris_Detail
# Isolated Debris Fragment with metallic shards and hazard orange plate against space
# ==============================================================================
print(">>> Executing Capture 3: Debris Detail...")
if sat_actor:
    sat_actor.set_actor_location(FAR_AWAY, False, False)
    sat_actor.set_actor_hidden_in_game(True)

if debris_actor:
    debris_actor.set_actor_location(deb_pos_0, False, False)
    debris_actor.set_actor_hidden_in_game(False)
    apply_debris_materials(debris_actor)

# Camera looking OUTWARDS from Earth side into deep space
deb_cam_loc = unreal.Vector(deb_pos_0.x - 350.0, deb_pos_0.y - 320.0, deb_pos_0.z + 180.0)
deb_cam_rot = look_at(deb_cam_loc, deb_pos_0)
capture_view("Milestone2_Debris_Detail", deb_cam_loc, deb_cam_rot, fov=38.0, sun_rotation=deb_cam_rot, sun_intensity=14.0)

# ==============================================================================
# CAPTURE 4: Milestone2_Encounter_Overview
# Satellite & Debris framed together in initial orbital state (t=0) with orbital tracks
# ==============================================================================
print(">>> Executing Capture 4: Encounter Overview...")
if sat_actor:
    sat_actor.set_actor_location_and_rotation(sat_pos_0, unreal.Rotator(0.0, -90.0, 0.0), False, False)
    sat_actor.set_actor_hidden_in_game(False)
    apply_satellite_materials(sat_actor)

if debris_actor:
    debris_actor.set_actor_location(deb_pos_0, False, False)
    debris_actor.set_actor_hidden_in_game(False)
    apply_debris_materials(debris_actor)

if sat_nominal_path:
    sat_nominal_path.set_actor_hidden_in_game(False)
if debris_path:
    debris_path.set_actor_hidden_in_game(False)
if sat_modified_path:
    sat_modified_path.set_actor_hidden_in_game(True)

mid_enc = unreal.Vector((sat_pos_0.x + deb_pos_0.x) * 0.5, (sat_pos_0.y + deb_pos_0.y) * 0.5, (sat_pos_0.z + deb_pos_0.z) * 0.5)
# Camera positioned to view both along orbit with Earth in background
enc_cam_loc = unreal.Vector(mid_enc.x + 950.0, mid_enc.y - 1200.0, mid_enc.z + 550.0)
enc_cam_rot = look_at(enc_cam_loc, mid_enc)
capture_view("Milestone2_Encounter_Overview", enc_cam_loc, enc_cam_rot, fov=48.0, sun_rotation=sun_earth_rot, sun_intensity=12.0)

# ==============================================================================
# CAPTURE 5: Milestone2_Conjunction_TCA
# Conjunction geometry at nominal TCA: Amber & Red spheres, Magenta miss line, Violet disc
# ==============================================================================
print(">>> Executing Capture 5: Conjunction TCA...")
# Hide trajectories to keep close-up markers crisp and unobstructed
if sat_nominal_path:
    sat_nominal_path.set_actor_hidden_in_game(True)
if debris_path:
    debris_path.set_actor_hidden_in_game(True)
if sat_modified_path:
    sat_modified_path.set_actor_hidden_in_game(True)

if sat_actor:
    sat_actor.set_actor_location(sat_tca_pos, False, False)
    sat_actor.set_actor_hidden_in_game(False)
    apply_satellite_materials(sat_actor)

if debris_actor:
    debris_actor.set_actor_location(deb_tca_pos, False, False)
    debris_actor.set_actor_hidden_in_game(False)
    apply_debris_materials(debris_actor)

if conj_viz:
    conj_viz.update_conjunction_geometry(sat_tca_pos, deb_tca_pos, miss_dist_uu)
    conj_viz.set_actor_location(sat_tca_pos, False, False)
    conj_viz.set_actor_hidden_in_game(False)
    apply_conjunction_materials(conj_viz)

tca_mid = unreal.Vector((sat_tca_pos.x + deb_tca_pos.x) * 0.5, (sat_tca_pos.y + deb_tca_pos.y) * 0.5, (sat_tca_pos.z + deb_tca_pos.z) * 0.5)
tca_cam_loc = unreal.Vector(tca_mid.x + 750.0, tca_mid.y - 850.0, tca_mid.z + 450.0)
tca_cam_rot = look_at(tca_cam_loc, tca_mid)
capture_view("Milestone2_Conjunction_TCA", tca_cam_loc, tca_cam_rot, fov=42.0, sun_rotation=tca_cam_rot, sun_intensity=14.0)

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
    sat_nominal_path.set_actor_hidden_in_game(False)
if sat_modified_path:
    sat_modified_path.set_actor_hidden_in_game(False)
if debris_path:
    debris_path.set_actor_hidden_in_game(True)

burn_cam_loc = unreal.Vector(burn_loc.x + 650.0, burn_loc.y - 750.0, burn_loc.z + 420.0)
burn_cam_rot = look_at(burn_cam_loc, burn_loc)
capture_view("Milestone2_Manoeuvre_Burn", burn_cam_loc, burn_cam_rot, fov=46.0, sun_rotation=burn_cam_rot, sun_intensity=14.0)

# ==============================================================================
# CAPTURE 7: Milestone2_Trajectories_Divergence
# Global orbital vantage: Earth, Nominal (Cyan), Avoidance (Green), Debris (Red), divergence
# ==============================================================================
print(">>> Executing Capture 7: Trajectories Divergence...")
apply_earth_materials()

if sat_nominal_path:
    sat_nominal_path.set_actor_hidden_in_game(False)
if debris_path:
    debris_path.set_actor_hidden_in_game(False)
if sat_modified_path:
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

if sat_actor:
    sat_actor.set_actor_location_and_rotation(sat_pos_0, unreal.Rotator(0.0, -90.0, 0.0), False, False)
    sat_actor.set_actor_hidden_in_game(False)
    apply_satellite_materials(sat_actor, is_manoeuvred=False)

if debris_actor:
    debris_actor.set_actor_location(deb_pos_0, False, False)
    debris_actor.set_actor_hidden_in_game(False)
    apply_debris_materials(debris_actor)

# Vantage showing both paths diverging after burn and debris intersecting near TCA
div_cam_loc = unreal.Vector(105000.0, -48000.0, 26000.0)
div_target = unreal.Vector(68000.0, -18000.0, 2000.0)
div_cam_rot = look_at(div_cam_loc, div_target)
capture_view("Milestone2_Trajectories_Divergence", div_cam_loc, div_cam_rot, fov=62.0, sun_rotation=sun_earth_rot, sun_intensity=12.0)

print("=" * 70)
print("[MILESTONE 2 MASTER V2] All 7 captures completed successfully!")
print("=" * 70)

unreal.SystemLibrary.execute_console_command(None, "QUIT_EDITOR")
