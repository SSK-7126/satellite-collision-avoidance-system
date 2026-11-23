"""
test_overview_visualization.py
==============================
Test candidate scales and camera compositions for Overview view.
"""
import unreal
import os
import math
import sys

out_dir = (unreal.Paths.project_saved_dir() + "Screenshots/WindowsEditor").replace("\\", "/")
os.makedirs(out_dir, exist_ok=True)

log_file = (unreal.Paths.project_saved_dir() + "test_overview.log").replace("\\", "/")
lf = open(log_file, "w", encoding="utf-8")

def log(msg):
    print(msg)
    sys.stdout.flush()
    lf.write(msg + "\n")
    lf.flush()
    unreal.log(msg)

log("Starting test_overview_visualization.py...")

level_path = "/Game/Scenarios/CollisionAvoidanceDemo"
world = unreal.EditorLevelLibrary.get_editor_world()
all_actors = unreal.EditorLevelLibrary.get_all_level_actors()

def look_at(from_pos, to_pos):
    dx = to_pos.x - from_pos.x
    dy = to_pos.y - from_pos.y
    dz = to_pos.z - from_pos.z
    yaw = math.degrees(math.atan2(dy, dx))
    pitch = math.degrees(math.atan2(dz, math.sqrt(dx*dx + dy*dy)))
    return unreal.Rotator(pitch=pitch, yaw=yaw, roll=0.0)

# Find actors
sat_actor = None
debris_actor = None
earth_actor = None
dir_light = None
sat_nominal_path = None
debris_path = None
sat_modified_path = None

for a in all_actors:
    lbl = a.get_actor_label()
    if lbl == "ProtectedSatellite_Payload01":
        sat_actor = a
    elif lbl == "SecondaryDebris_Object99":
        debris_actor = a
    elif lbl == "Earth_CelestialBody":
        earth_actor = a
    elif isinstance(a, unreal.DirectionalLight):
        dir_light = a
    elif lbl == "OrbitPath_SatelliteNominal":
        sat_nominal_path = a
    elif lbl == "OrbitPath_DebrisNominal":
        debris_path = a
    elif lbl == "OrbitPath_SatelliteModified":
        sat_modified_path = a

# Load materials
m_solid = unreal.EditorAssetLibrary.load_asset("/Game/Common/M_SolidColor")
m_earth = unreal.EditorAssetLibrary.load_asset("/Game/Environment/M_Earth_Direct")
m_atmo = unreal.EditorAssetLibrary.load_asset("/Game/Environment/M_Atmosphere")

def apply_satellite_materials(sat, is_manoeuvred=False):
    if not sat or not m_solid:
        return
    body = sat.get_editor_property("satellite_body")
    if body:
        mat_body = body.create_dynamic_material_instance(0, m_solid)
        col = unreal.LinearColor(0.1, 0.95, 0.45, 1.0) if is_manoeuvred else unreal.LinearColor(0.98, 0.82, 0.28, 1.0)
        mat_body.set_vector_parameter_value("Color", col)
        mat_body.set_scalar_parameter_value("Metallic", 0.9)
        mat_body.set_scalar_parameter_value("Roughness", 0.2)
        mat_body.set_scalar_parameter_value("EmissiveMultiplier", 0.4)
        body.set_material(0, mat_body)

    for p_name in ["solar_panel_left", "solar_panel_left_outboard", "solar_panel_right", "solar_panel_right_outboard"]:
        p_comp = sat.get_editor_property(p_name)
        if p_comp:
            mat_blue = p_comp.create_dynamic_material_instance(0, m_solid)
            mat_blue.set_vector_parameter_value("Color", unreal.LinearColor(0.015, 0.08, 0.55, 1.0))
            mat_blue.set_scalar_parameter_value("Metallic", 0.85)
            mat_blue.set_scalar_parameter_value("Roughness", 0.15)
            mat_blue.set_scalar_parameter_value("EmissiveMultiplier", 0.35)
            p_comp.set_material(0, mat_blue)

    for m_name in ["solar_yoke_left", "solar_yoke_right", "antenna_mast", "thruster_nozzle", "payload_deck"]:
        m_comp = sat.get_editor_property(m_name)
        if m_comp:
            mat_silver = m_comp.create_dynamic_material_instance(0, m_solid)
            mat_silver.set_vector_parameter_value("Color", unreal.LinearColor(0.78, 0.82, 0.86, 1.0))
            mat_silver.set_scalar_parameter_value("Metallic", 0.9)
            mat_silver.set_scalar_parameter_value("Roughness", 0.25)
            mat_silver.set_scalar_parameter_value("EmissiveMultiplier", 0.25)
            m_comp.set_material(0, mat_silver)

    dish = sat.get_editor_property("antenna_dish")
    if dish:
        mat_dish = dish.create_dynamic_material_instance(0, m_solid)
        mat_dish.set_vector_parameter_value("Color", unreal.LinearColor(0.95, 0.88, 0.55, 1.0))
        mat_dish.set_scalar_parameter_value("Metallic", 0.95)
        mat_dish.set_scalar_parameter_value("Roughness", 0.2)
        mat_dish.set_scalar_parameter_value("EmissiveMultiplier", 0.4)
        dish.set_material(0, mat_dish)

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
    log(f"[CAPTURED] {out_dir}/{png_name}")

# Earth setup
if earth_actor and m_earth:
    emesh = earth_actor.get_editor_property("earth_mesh")
    if emesh:
        emesh.set_material(0, m_earth)
        emesh.set_relative_scale3d(unreal.Vector(1275.6274, 1275.6274, 1275.6274))
    atm = earth_actor.get_editor_property("atmosphere_mesh")
    if atm and m_atmo:
        atm.set_material(0, m_atmo)
        atm.set_relative_scale3d(unreal.Vector(1.015, 1.015, 1.015))
        atm.set_visibility(True)
        atm.set_hidden_in_game(False)

sat_pos_0 = unreal.Vector(70000.0, 0.0, 0.0)
deb_pos_0 = unreal.Vector(70000.0, -100.0, 0.0)
sat_rot_0 = unreal.Rotator(0.0, -90.0, 0.0)

if sat_actor:
    sat_actor.set_actor_location_and_rotation(sat_pos_0, sat_rot_0, False, False)
    sat_actor.set_actor_hidden_in_game(False)
    apply_satellite_materials(sat_actor)

if debris_actor:
    debris_actor.set_actor_location(deb_pos_0, False, False)
    debris_actor.set_actor_hidden_in_game(False)
    apply_debris_materials(debris_actor)

# Trajectories
if sat_nominal_path:
    sat_nominal_path.set_editor_property("path_thickness", 25.0)
    sat_nominal_path.set_actor_hidden_in_game(False)
if debris_path:
    debris_path.set_editor_property("path_thickness", 25.0)
    debris_path.set_actor_hidden_in_game(False)
if sat_modified_path:
    sat_modified_path.set_editor_property("path_thickness", 25.0)
    sat_modified_path.set_actor_hidden_in_game(False)

mid_pt = unreal.Vector(70000.0, -50.0, 0.0)
sun_rot = unreal.Rotator(pitch=-25.0, yaw=140.0, roll=0.0)

# ==============================================================================
# TEST CONFIGURATION 1: Scale 0.4
# ==============================================================================
sat_actor.set_actor_scale3d(unreal.Vector(0.4, 0.4, 0.4))
debris_actor.set_actor_scale3d(unreal.Vector(0.5, 0.5, 0.5))

cam_loc_1 = unreal.Vector(71400.0, 320.0, 580.0)
cam_rot_1 = look_at(cam_loc_1, mid_pt)
capture_view("Test_Overview_Cfg1", cam_loc_1, cam_rot_1, fov=58.0, sun_rotation=sun_rot, sun_intensity=14.0)

# ==============================================================================
# TEST CONFIGURATION 2: Scale 0.6
# ==============================================================================
sat_actor.set_actor_scale3d(unreal.Vector(0.6, 0.6, 0.6))
debris_actor.set_actor_scale3d(unreal.Vector(0.7, 0.7, 0.7))

cam_loc_2 = unreal.Vector(72200.0, 480.0, 920.0)
cam_rot_2 = look_at(cam_loc_2, mid_pt)
capture_view("Test_Overview_Cfg2", cam_loc_2, cam_rot_2, fov=62.0, sun_rotation=sun_rot, sun_intensity=14.0)

# ==============================================================================
# TEST CONFIGURATION 3: Scale 0.8
# ==============================================================================
sat_actor.set_actor_scale3d(unreal.Vector(0.8, 0.8, 0.8))
debris_actor.set_actor_scale3d(unreal.Vector(0.9, 0.9, 0.9))

cam_loc_3 = unreal.Vector(73000.0, 650.0, 1250.0)
cam_rot_3 = look_at(cam_loc_3, mid_pt)
capture_view("Test_Overview_Cfg3", cam_loc_3, cam_rot_3, fov=64.0, sun_rotation=sun_rot, sun_intensity=14.0)

log("ALL TEST CAPTURES COMPLETE SUCCESSFULLY!")
