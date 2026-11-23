"""
explore_camera_compositions.py
==============================
Test 6 distinct camera compositions for Camera_Earth_Overview.
Evaluates:
- Satellite model size and recognition (bus, wings, mast, dish)
- Debris model size and recognition (jagged shape, orange shard)
- Clear visual separation between satellite and debris
- Earth in background
- Trajectory line readability (Nominal cyan, Debris orange/red, Modified green)
"""
import unreal
import os
import math

out_dir = (unreal.Paths.project_saved_dir() + "Screenshots/WindowsEditor/Compositions").replace("\\", "/")
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

def apply_sat_mat(s, is_manoeuvred=False):
    if not s or not m_solid: return
    body = s.get_editor_property("satellite_body")
    if body:
        mat = body.create_dynamic_material_instance(0, m_solid)
        col = unreal.LinearColor(0.1, 0.95, 0.45, 1.0) if is_manoeuvred else unreal.LinearColor(0.98, 0.82, 0.28, 1.0)
        mat.set_vector_parameter_value("Color", col)
        mat.set_scalar_parameter_value("Metallic", 0.9)
        mat.set_scalar_parameter_value("Roughness", 0.2)
        mat.set_scalar_parameter_value("EmissiveMultiplier", 0.45)
        body.set_material(0, mat)
    for p in ["solar_panel_left", "solar_panel_left_outboard", "solar_panel_right", "solar_panel_right_outboard"]:
        comp = s.get_editor_property(p)
        if comp:
            mat = comp.create_dynamic_material_instance(0, m_solid)
            mat.set_vector_parameter_value("Color", unreal.LinearColor(0.015, 0.08, 0.55, 1.0))
            mat.set_scalar_parameter_value("Metallic", 0.85)
            mat.set_scalar_parameter_value("Roughness", 0.15)
            mat.set_scalar_parameter_value("EmissiveMultiplier", 0.4)
            comp.set_material(0, mat)
    for m in ["solar_yoke_left", "solar_yoke_right", "antenna_mast", "thruster_nozzle", "payload_deck"]:
        comp = s.get_editor_property(m)
        if comp:
            mat = comp.create_dynamic_material_instance(0, m_solid)
            mat.set_vector_parameter_value("Color", unreal.LinearColor(0.78, 0.82, 0.86, 1.0))
            mat.set_scalar_parameter_value("Metallic", 0.9)
            mat.set_scalar_parameter_value("Roughness", 0.25)
            mat.set_scalar_parameter_value("EmissiveMultiplier", 0.3)
            comp.set_material(0, mat)
    dish = s.get_editor_property("antenna_dish")
    if dish:
        mat = dish.create_dynamic_material_instance(0, m_solid)
        mat.set_vector_parameter_value("Color", unreal.LinearColor(0.95, 0.88, 0.55, 1.0))
        mat.set_scalar_parameter_value("Metallic", 0.95)
        mat.set_scalar_parameter_value("Roughness", 0.2)
        mat.set_scalar_parameter_value("EmissiveMultiplier", 0.45)
        dish.set_material(0, mat)

def apply_deb_mat(d):
    if not d or not m_solid: return
    for c in ["debris_mesh", "fragment_shard_a", "torn_strut"]:
        comp = d.get_editor_property(c)
        if comp:
            mat = comp.create_dynamic_material_instance(0, m_solid)
            mat.set_vector_parameter_value("Color", unreal.LinearColor(0.72, 0.70, 0.68, 1.0))
            mat.set_scalar_parameter_value("Metallic", 0.85)
            mat.set_scalar_parameter_value("Roughness", 0.45)
            mat.set_scalar_parameter_value("EmissiveMultiplier", 0.35)
            comp.set_material(0, mat)
    shard_b = d.get_editor_property("fragment_shard_b")
    if shard_b:
        mat = shard_b.create_dynamic_material_instance(0, m_solid)
        mat.set_vector_parameter_value("Color", unreal.LinearColor(1.0, 0.35, 0.02, 1.0))
        mat.set_scalar_parameter_value("Metallic", 0.4)
        mat.set_scalar_parameter_value("Roughness", 0.3)
        mat.set_scalar_parameter_value("EmissiveMultiplier", 0.55)
        shard_b.set_material(0, mat)

def look_at(from_pos, to_pos):
    dx = to_pos.x - from_pos.x
    dy = to_pos.y - from_pos.y
    dz = to_pos.z - from_pos.z
    yaw = math.degrees(math.atan2(dy, dx))
    pitch = math.degrees(math.atan2(dz, math.sqrt(dx*dx + dy*dy)))
    return unreal.Rotator(pitch=pitch, yaw=yaw, roll=0.0)

def capture_comp(tag, cam_loc, target_loc, fov=58.0):
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

# Set positions at t = 0
sat.set_actor_location_and_rotation(unreal.Vector(70000.0, 0.0, 0.0), unreal.Rotator(0.0, -90.0, 0.0), False, False)
deb.set_actor_location_and_rotation(unreal.Vector(70000.0, -100.0, 0.0), unreal.Rotator(0.0, 0.0, 0.0), False, False)

# Visual Scales:
# Satellite scale = 0.38 (bus: 76 uu, wingspan: 440 uu)
# Debris scale = 0.48 (cluster: 120 uu)
sat.set_actor_scale3d(unreal.Vector(0.38, 0.38, 0.38))
deb.set_actor_scale3d(unreal.Vector(0.48, 0.48, 0.48))

apply_sat_mat(sat)
apply_deb_mat(deb)

# Sleek trajectory thickness: 8.0 uu (clean line, no occlusion)
if sat_nom:
    sat_nom.set_editor_property("path_thickness", 8.0)
if deb_nom:
    deb_nom.set_editor_property("path_thickness", 8.0)
if sat_mod:
    sat_mod.set_editor_property("path_thickness", 8.0)
    sat_mod.set_actor_hidden_in_game(False)

# Sun rotation
if sun:
    sun.set_actor_rotation(unreal.Rotator(pitch=-24.0, yaw=150.0, roll=0.0), False)
    comp = sun.get_component_by_class(unreal.DirectionalLightComponent)
    comp.set_editor_property("intensity", 14.0)

# Midpoint between satellite (70000, 0, 0) and debris (70000, -100, 0)
mid = unreal.Vector(70000.0, -50.0, 0.0)

# 1. Broadside elevated: camera at (71200, 300, 450)
capture_comp("Comp1_Broadside_Elevated", unreal.Vector(71200.0, 300.0, 450.0), mid, fov=55.0)

# 2. Broadside side-view: camera at (71500, -50, 400)
capture_comp("Comp2_Broadside_Flank", unreal.Vector(71500.0, -50.0, 400.0), mid, fov=52.0)

# 3. Trailing quarter view: camera at (70800, 600, 500)
capture_comp("Comp3_Trailing_Quarter", unreal.Vector(70800.0, 600.0, 500.0), mid, fov=56.0)

# 4. Leading quarter view: camera at (70800, -700, 500)
capture_comp("Comp4_Leading_Quarter", unreal.Vector(70800.0, -700.0, 500.0), mid, fov=56.0)

# 5. Elevated high orbital view: camera at (72200, 100, 1200)
capture_comp("Comp5_Elevated_High", unreal.Vector(72200.0, 100.0, 1200.0), mid, fov=58.0)

# 6. Pulled back for wider Earth curvature: camera at (73000, -50, 1800)
capture_comp("Comp6_Earth_Curvature", unreal.Vector(73000.0, -50.0, 1800.0), mid, fov=58.0)

print("EXPLORE_COMPOSITIONS_DONE")
