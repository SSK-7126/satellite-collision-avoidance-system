"""
test_all_views_and_polish.py
============================
1. Test 3 fine-tuned variations of the elevated broadside overview camera (Plan1 refined):
   - Closer framing with scale 0.38 / 0.48
   - Balanced Earth curvature in lower half, space in upper half
   - Perfect sun lighting (bright, metallic reflections on bus and panels)
2. Test ALL other 5 milestone cameras with the new scales to verify framing, margins, and visibility:
   - Camera_Satellite_Detail (Step 2, Step 5)
   - Camera_Debris_Detail
   - Camera_Conjunction_TCA (Step 4)
   - Camera_Manoeuvre_Burn (Step 6)
   - Camera_Encounter_Overview (Step 3, Step 7)
"""
import unreal
import os
import math

out_dir = (unreal.Paths.project_saved_dir() + "Screenshots/WindowsEditor/AllViews").replace("\\", "/")
os.makedirs(out_dir, exist_ok=True)

world = unreal.EditorLevelLibrary.get_editor_world()
actors = unreal.EditorLevelLibrary.get_all_level_actors()

sat = None
deb = None
earth = None
sun = None
sat_nom = None
deb_nom = None
sat_mod = None
cams = {}

for a in actors:
    lbl = a.get_actor_label()
    if lbl == "ProtectedSatellite_Payload01":
        sat = a
    elif lbl == "SecondaryDebris_Object99":
        deb = a
    elif lbl == "Earth_CelestialBody":
        earth = a
    elif isinstance(a, unreal.DirectionalLight):
        sun = a
    elif lbl == "OrbitPath_SatelliteNominal":
        sat_nom = a
    elif lbl == "OrbitPath_DebrisNominal":
        deb_nom = a
    elif lbl == "OrbitPath_SatelliteModified":
        sat_mod = a
    elif isinstance(a, unreal.CameraActor):
        cams[lbl] = a

m_solid = unreal.EditorAssetLibrary.load_asset("/Game/Common/M_SolidColor")

def apply_sat_mat(s, is_manoeuvred=False):
    if not s or not m_solid: return
    body = s.get_editor_property("satellite_body")
    if body:
        mat = body.create_dynamic_material_instance(0, m_solid)
        col = unreal.LinearColor(0.1, 0.95, 0.45, 1.0) if is_manoeuvred else unreal.LinearColor(0.98, 0.82, 0.28, 1.0)
        mat.set_vector_parameter_value("Color", col)
        mat.set_scalar_parameter_value("Metallic", 0.92)
        mat.set_scalar_parameter_value("Roughness", 0.18)
        mat.set_scalar_parameter_value("EmissiveMultiplier", 0.5)
        body.set_material(0, mat)
    for p in ["solar_panel_left", "solar_panel_left_outboard", "solar_panel_right", "solar_panel_right_outboard"]:
        comp = s.get_editor_property(p)
        if comp:
            mat = comp.create_dynamic_material_instance(0, m_solid)
            mat.set_vector_parameter_value("Color", unreal.LinearColor(0.015, 0.08, 0.58, 1.0))
            mat.set_scalar_parameter_value("Metallic", 0.88)
            mat.set_scalar_parameter_value("Roughness", 0.12)
            mat.set_scalar_parameter_value("EmissiveMultiplier", 0.45)
            comp.set_material(0, mat)
    for m in ["solar_yoke_left", "solar_yoke_right", "antenna_mast", "thruster_nozzle", "payload_deck"]:
        comp = s.get_editor_property(m)
        if comp:
            mat = comp.create_dynamic_material_instance(0, m_solid)
            mat.set_vector_parameter_value("Color", unreal.LinearColor(0.82, 0.85, 0.88, 1.0))
            mat.set_scalar_parameter_value("Metallic", 0.92)
            mat.set_scalar_parameter_value("Roughness", 0.2)
            mat.set_scalar_parameter_value("EmissiveMultiplier", 0.35)
            comp.set_material(0, mat)
    dish = s.get_editor_property("antenna_dish")
    if dish:
        mat = dish.create_dynamic_material_instance(0, m_solid)
        mat.set_vector_parameter_value("Color", unreal.LinearColor(0.98, 0.90, 0.55, 1.0))
        mat.set_scalar_parameter_value("Metallic", 0.96)
        mat.set_scalar_parameter_value("Roughness", 0.18)
        mat.set_scalar_parameter_value("EmissiveMultiplier", 0.5)
        dish.set_material(0, mat)

def apply_deb_mat(d):
    if not d or not m_solid: return
    for c in ["debris_mesh", "fragment_shard_a", "torn_strut"]:
        comp = d.get_editor_property(c)
        if comp:
            mat = comp.create_dynamic_material_instance(0, m_solid)
            mat.set_vector_parameter_value("Color", unreal.LinearColor(0.72, 0.70, 0.68, 1.0))
            mat.set_scalar_parameter_value("Metallic", 0.88)
            mat.set_scalar_parameter_value("Roughness", 0.4)
            mat.set_scalar_parameter_value("EmissiveMultiplier", 0.4)
            comp.set_material(0, mat)
    shard_b = d.get_editor_property("fragment_shard_b")
    if shard_b:
        mat = shard_b.create_dynamic_material_instance(0, m_solid)
        mat.set_vector_parameter_value("Color", unreal.LinearColor(1.0, 0.38, 0.02, 1.0))
        mat.set_scalar_parameter_value("Metallic", 0.4)
        mat.set_scalar_parameter_value("Roughness", 0.25)
        mat.set_scalar_parameter_value("EmissiveMultiplier", 0.6)
        shard_b.set_material(0, mat)

def look_at(from_pos, to_pos):
    dx = to_pos.x - from_pos.x
    dy = to_pos.y - from_pos.y
    dz = to_pos.z - from_pos.z
    yaw = math.degrees(math.atan2(dy, dx))
    pitch = math.degrees(math.atan2(dz, math.sqrt(dx*dx + dy*dy)))
    return unreal.Rotator(pitch=pitch, yaw=yaw, roll=0.0)

def capture_scene(tag, cam_loc, cam_rot, fov=54.0):
    cap = unreal.EditorLevelLibrary.spawn_actor_from_class(unreal.SceneCapture2D, cam_loc, cam_rot)
    comp = cap.get_editor_property("capture_component2d")
    comp.set_editor_property("fov_angle", fov)
    comp.set_editor_property("capture_source", unreal.SceneCaptureSource.SCS_FINAL_COLOR_LDR)
    
    pps = comp.get_editor_property("post_process_settings")
    pps.set_editor_property("override_auto_exposure_bias", True)
    pps.set_editor_property("auto_exposure_bias", 0.0)
    comp.set_editor_property("post_process_settings", pps)

    rt = unreal.RenderingLibrary.create_render_target2d(world, 1920, 1080, unreal.TextureRenderTargetFormat.RTF_RGBA8)
    comp.set_editor_property("texture_target", rt)
    comp.capture_scene()

    png = f"{tag}.png"
    unreal.RenderingLibrary.export_render_target(world, rt, out_dir, png)
    unreal.EditorLevelLibrary.destroy_actor(cap)
    print(f"Captured {tag}")

# Ensure exact scientific initial positions
sat.set_actor_location_and_rotation(unreal.Vector(70000.0, 0.0, 0.0), unreal.Rotator(0.0, -90.0, 0.0), False, False)
deb.set_actor_location_and_rotation(unreal.Vector(70000.0, -100.0, 0.0), unreal.Rotator(0.0, 0.0, 0.0), False, False)

# Set visual scale:
# Satellite scale = 0.38 (wingspan ~440 uu, bus ~76 uu)
# Debris scale = 0.48 (cluster ~120 uu)
sat.set_actor_scale3d(unreal.Vector(0.38, 0.38, 0.38))
deb.set_actor_scale3d(unreal.Vector(0.48, 0.48, 0.48))

apply_sat_mat(sat)
apply_deb_mat(deb)

# Sleek trajectory thickness: 4.5 uu
if sat_nom: sat_nom.set_editor_property("path_thickness", 4.5)
if deb_nom: deb_nom.set_editor_property("path_thickness", 4.5)
if sat_mod:
    sat_mod.set_editor_property("path_thickness", 4.5)
    sat_mod.set_actor_hidden_in_game(True)

# Sun lighting: bright, angled to illuminate top, side, and front
if sun:
    sun.set_actor_rotation(unreal.Rotator(pitch=-26.0, yaw=148.0, roll=0.0), False)
    comp = sun.get_component_by_class(unreal.DirectionalLightComponent)
    comp.set_editor_property("intensity", 15.0)

midpoint = unreal.Vector(70000.0, -50.0, 0.0)

# ------------------------------------------------------------------------------
# 1. OVERVIEW CANDIDATES (Refined Plan1)
# ------------------------------------------------------------------------------
# Overview 1: X=70700, Y=-50, Z=1050, Target=(70000, -50, -50), FOV=50
cam1_loc = unreal.Vector(70700.0, -50.0, 1050.0)
cam1_rot = look_at(cam1_loc, unreal.Vector(70000.0, -50.0, -50.0))
capture_scene("Overview_Option_1", cam1_loc, cam1_rot, fov=50.0)

# Overview 2: X=70800, Y=-50, Z=1200, Target=(70000, -50, -30), FOV=52
cam2_loc = unreal.Vector(70800.0, -50.0, 1200.0)
cam2_rot = look_at(cam2_loc, unreal.Vector(70000.0, -50.0, -30.0))
capture_scene("Overview_Option_2", cam2_loc, cam2_rot, fov=52.0)

# Overview 3: X=70600, Y=-50, Z=900, Target=(70000, -50, -60), FOV=48 (closer, large crafts)
cam3_loc = unreal.Vector(70600.0, -50.0, 900.0)
cam3_rot = look_at(cam3_loc, unreal.Vector(70000.0, -50.0, -60.0))
capture_scene("Overview_Option_3", cam3_loc, cam3_rot, fov=48.0)

# ------------------------------------------------------------------------------
# 2. CHECK ALL OTHER LEVEL CAMERAS
# ------------------------------------------------------------------------------
# Detail Satellite: Camera_Satellite_Detail
cam_sat = cams.get("Camera_Satellite_Detail")
if cam_sat:
    loc = cam_sat.get_actor_location()
    rot = cam_sat.get_actor_rotation()
    cam_comp = cam_sat.get_component_by_class(unreal.CameraComponent)
    fov = cam_comp.get_editor_property("field_of_view") if cam_comp else 48.0
    capture_scene("Camera_Satellite_Detail_Eval", loc, rot, fov=fov)

# Detail Debris: Camera_Debris_Detail
cam_deb = cams.get("Camera_Debris_Detail")
if cam_deb:
    loc = cam_deb.get_actor_location()
    rot = cam_deb.get_actor_rotation()
    cam_comp = cam_deb.get_component_by_class(unreal.CameraComponent)
    fov = cam_comp.get_editor_property("field_of_view") if cam_comp else 42.0
    capture_scene("Camera_Debris_Detail_Eval", loc, rot, fov=fov)

# Encounter Overview: Camera_Encounter_Overview
cam_enc = cams.get("Camera_Encounter_Overview")
if cam_enc:
    loc = cam_enc.get_actor_location()
    rot = cam_enc.get_actor_rotation()
    cam_comp = cam_enc.get_component_by_class(unreal.CameraComponent)
    fov = cam_comp.get_editor_property("field_of_view") if cam_comp else 44.0
    capture_scene("Camera_Encounter_Overview_Eval", loc, rot, fov=fov)

print("ALL_VIEWS_AND_POLISH_TESTS_DONE")
