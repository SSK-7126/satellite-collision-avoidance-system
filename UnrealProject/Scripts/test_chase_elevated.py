"""
test_chase_elevated.py
======================
Test elevated chase/flank vantages where:
- Camera is at X ≈ 70000 - 70300, Y ≈ 600 - 900, Z ≈ 650 - 900
- Looking forward along -Y towards (70000, -60, 0)
- Left wing extends to +X, Right wing extends to -X -> perfectly visible broadside!
- Debris is ahead at Y = -100
- Earth is below in the background
"""
import unreal
import os
import math

out_dir = (unreal.Paths.project_saved_dir() + "Screenshots/WindowsEditor/ChaseViews").replace("\\", "/")
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

m_solid = unreal.EditorAssetLibrary.load_asset("/Game/Common/M_SolidColor")

def apply_sat_mat(s):
    if not s or not m_solid: return
    body = s.get_editor_property("satellite_body")
    if body:
        mat = body.create_dynamic_material_instance(0, m_solid)
        mat.set_vector_parameter_value("Color", unreal.LinearColor(0.98, 0.82, 0.28, 1.0))
        mat.set_scalar_parameter_value("Metallic", 0.92)
        mat.set_scalar_parameter_value("Roughness", 0.18)
        mat.set_scalar_parameter_value("EmissiveMultiplier", 0.45)
        body.set_material(0, mat)
    for p in ["solar_panel_left", "solar_panel_left_outboard", "solar_panel_right", "solar_panel_right_outboard"]:
        comp = s.get_editor_property(p)
        if comp:
            mat = comp.create_dynamic_material_instance(0, m_solid)
            mat.set_vector_parameter_value("Color", unreal.LinearColor(0.015, 0.08, 0.58, 1.0))
            mat.set_scalar_parameter_value("Metallic", 0.88)
            mat.set_scalar_parameter_value("Roughness", 0.12)
            mat.set_scalar_parameter_value("EmissiveMultiplier", 0.42)
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
        mat.set_scalar_parameter_value("EmissiveMultiplier", 0.45)
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

def capture_scene(tag, cam_loc, target_loc, fov=52.0):
    cam_rot = look_at(cam_loc, target_loc)
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

# Visual scale:
sat.set_actor_scale3d(unreal.Vector(0.38, 0.38, 0.38))
deb.set_actor_scale3d(unreal.Vector(0.48, 0.48, 0.48))

apply_sat_mat(sat)
apply_deb_mat(deb)

# Sleek trajectory thickness: 4.0 uu
if sat_nom: sat_nom.set_editor_property("path_thickness", 4.0)
if deb_nom: deb_nom.set_editor_property("path_thickness", 4.0)
if sat_mod:
    sat_mod.set_editor_property("path_thickness", 4.0)
    sat_mod.set_actor_hidden_in_game(True)

# Sun lighting
if sun:
    sun.set_actor_rotation(unreal.Rotator(pitch=-28.0, yaw=140.0, roll=0.0), False)
    comp = sun.get_component_by_class(unreal.DirectionalLightComponent)
    comp.set_editor_property("intensity", 15.0)

target = unreal.Vector(70000.0, -70.0, 0.0)

# Chase 1: X=70150, Y=700, Z=650, FOV=50
capture_scene("Chase1_Direct_Elevated", unreal.Vector(70150.0, 700.0, 650.0), target, fov=50.0)

# Chase 2: X=70300, Y=800, Z=750, FOV=48
capture_scene("Chase2_Flank_Elevated", unreal.Vector(70300.0, 800.0, 750.0), target, fov=48.0)

# Chase 3: X=70500, Y=750, Z=850, FOV=52
capture_scene("Chase3_Higher_Angle", unreal.Vector(70500.0, 750.0, 850.0), target, fov=52.0)

# Chase 4: X=69800, Y=700, Z=650, FOV=50 (slightly on the Earth side of the orbit track)
capture_scene("Chase4_Inboard_Elevated", unreal.Vector(69800.0, 700.0, 650.0), target, fov=50.0)

print("CHASE_TESTS_DONE")
