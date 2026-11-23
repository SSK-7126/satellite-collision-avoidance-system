"""
test_perfect_harmony.py
=======================
Test 4 master compositions combining:
- Broadside visibility of spacecraft & debris
- Photorealistic smooth Earth limb in background
- Distinguishable trajectories
- Crisp metallic and solar panel materials
"""
import unreal
import os
import math

out_dir = (unreal.Paths.project_saved_dir() + "Screenshots/WindowsEditor/Harmony").replace("\\", "/")
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

def capture_scene(tag, cam_loc, target_loc, fov=50.0):
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

# Exact scientific initial positions
sat.set_actor_location_and_rotation(unreal.Vector(70000.0, 0.0, 0.0), unreal.Rotator(0.0, -90.0, 0.0), False, False)
deb.set_actor_location_and_rotation(unreal.Vector(70000.0, -100.0, 0.0), unreal.Rotator(0.0, 0.0, 0.0), False, False)

# Set visual scale:
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

# Lighting: sun angled for crisp metallic shine
if sun:
    sun.set_actor_rotation(unreal.Rotator(pitch=-24.0, yaw=148.0, roll=0.0), False)
    comp = sun.get_component_by_class(unreal.DirectionalLightComponent)
    comp.set_editor_property("intensity", 15.0)

# 1. Harmony 1: (71100, 400, 600), target=(69980, -60, 20), FOV=48
capture_scene("Harmony_1", unreal.Vector(71100.0, 400.0, 600.0), unreal.Vector(69980.0, -60.0, 20.0), fov=48.0)

# 2. Harmony 2: (71300, 450, 700), target=(69980, -60, 20), FOV=50
capture_scene("Harmony_2", unreal.Vector(71300.0, 450.0, 700.0), unreal.Vector(69980.0, -60.0, 20.0), fov=50.0)

# 3. Harmony 3: (70900, 300, 500), target=(69980, -60, 30), FOV=46 (closer, larger subjects)
capture_scene("Harmony_3", unreal.Vector(70900.0, 300.0, 500.0), unreal.Vector(69980.0, -60.0, 30.0), fov=46.0)

# 4. Harmony 4: (71400, 200, 800), target=(69980, -60, 0), FOV=50 (elevated broadside with Earth limb)
capture_scene("Harmony_4", unreal.Vector(71400.0, 200.0, 800.0), unreal.Vector(69980.0, -60.0, 0.0), fov=50.0)

print("HARMONY_TESTS_DONE")
