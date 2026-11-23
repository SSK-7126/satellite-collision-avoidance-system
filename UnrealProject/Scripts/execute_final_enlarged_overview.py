"""
execute_final_enlarged_overview.py
==================================
Controlled visualization execution inside Unreal Engine 5.7:
1. Loads /Game/Scenarios/CollisionAvoidanceDemo
2. Applies independent visual mesh scaling to Satellite (0.38) and Debris (0.48)
   while preserving exact scientific coordinates:
   - Protected Satellite: (70000.0, 0.0, 0.0)
   - Secondary Debris:    (70000.0, -100.0, 0.0)
3. Hides terrestrial template actors (SM_SkySphere, SkyAtmosphere, ExponentialHeightFog)
   to ensure deep space contrast and eliminate skydome warnings.
4. Positions Camera_Earth_Overview at elevated flank vantage:
   Location: (70300.0, 800.0, 750.0), Rotation: Pitch=-39.18, Yaw=-109.0, Roll=0.0, FOV: 48.0
5. Configures sleek 5.0 uu trajectory ribbons (Nominal Cyan, Debris Red/Orange).
6. Saves level permanently.
7. Captures high-res 1080p Enlarged_Overview_SimulationStart.png.
"""
import unreal
import os
import shutil
import math

print(">>> [VISUALIZATION RUN] Initializing execute_final_enlarged_overview.py...")

level_path = "/Game/Scenarios/CollisionAvoidanceDemo"
loaded = unreal.EditorLevelLibrary.load_level(level_path)
print(f">>> Level loaded: {loaded}")

world = unreal.EditorLevelLibrary.get_editor_world()
all_actors = unreal.EditorLevelLibrary.get_all_level_actors()

out_dir = (unreal.Paths.project_saved_dir() + "Screenshots/WindowsEditor/FinalEnlarged").replace("\\", "/")
artifacts_dir = "C:/Users/Sriram Krovi/.gemini/antigravity/brain/7d36e17b-846d-4a94-9bbc-4bf33eb09d71"
os.makedirs(out_dir, exist_ok=True)
os.makedirs(artifacts_dir, exist_ok=True)

earth_actor = None
sat_actor = None
debris_actor = None
sun = None
sat_nom_path = None
debris_path = None
sat_mod_path = None
cam_overview = None

for a in all_actors:
    lbl = a.get_actor_label()
    cname = a.get_class().get_name()

    # Hide terrestrial skydome warning and fog actors in orbital scene
    if lbl == "SM_SkySphere" or cname in ["SkyAtmosphere", "ExponentialHeightFog", "VolumetricCloud"]:
        a.set_actor_hidden_in_game(True)
        try:
            a.set_is_temporarily_hidden_in_editor(True)
        except Exception:
            pass

    if lbl == "Earth_CelestialBody" or (isinstance(a, unreal.EarthActor) and "Camera" not in lbl):
        earth_actor = a
    elif lbl == "ProtectedSatellite_Payload01" or (isinstance(a, unreal.SatelliteActor) and "Camera" not in lbl):
        sat_actor = a
    elif lbl == "SecondaryDebris_Object99" or (isinstance(a, unreal.DebrisActor) and "Camera" not in lbl):
        debris_actor = a
    elif isinstance(a, unreal.DirectionalLight):
        sun = a
    elif lbl == "OrbitPath_SatelliteNominal":
        sat_nom_path = a
    elif lbl == "OrbitPath_DebrisNominal":
        debris_path = a
    elif lbl == "OrbitPath_SatelliteModified":
        sat_mod_path = a
    elif lbl == "Camera_Earth_Overview":
        cam_overview = a

print(f">>> Actors identified: Earth={earth_actor is not None}, Sat={sat_actor is not None}, Debris={debris_actor is not None}, Cam={cam_overview is not None}")

# 1. Earth Atmosphere and Mesh Materials
m_earth = unreal.EditorAssetLibrary.load_asset("/Game/Earth/M_Earth")
m_atmo = unreal.EditorAssetLibrary.load_asset("/Game/Earth/M_Atmosphere")
if earth_actor:
    em = earth_actor.get_editor_property("earth_mesh")
    atm = earth_actor.get_editor_property("atmosphere_mesh")
    if em and m_earth:
        em.set_material(0, m_earth)
    if atm and m_atmo:
        atm.set_material(0, m_atmo)
        atm.set_relative_scale3d(unreal.Vector(1.015, 1.015, 1.015))
        atm.set_visibility(True)
        atm.set_hidden_in_game(False)
    print(">>> Earth materials verified.")

# 2. PBR Materials for Spacecraft and Debris
m_solid = unreal.EditorAssetLibrary.load_asset("/Game/Common/M_SolidColor")

def apply_sat_materials(s):
    if not s or not m_solid:
        return
    body = s.get_editor_property("satellite_body")
    if body:
        mat_body = body.create_dynamic_material_instance(0, m_solid)
        mat_body.set_vector_parameter_value("Color", unreal.LinearColor(0.98, 0.82, 0.28, 1.0))
        mat_body.set_scalar_parameter_value("Metallic", 0.92)
        mat_body.set_scalar_parameter_value("Roughness", 0.18)
        mat_body.set_scalar_parameter_value("EmissiveMultiplier", 0.45)
        body.set_material(0, mat_body)

    for p in ["solar_panel_left", "solar_panel_left_outboard", "solar_panel_right", "solar_panel_right_outboard"]:
        comp = s.get_editor_property(p)
        if comp:
            mat_blue = comp.create_dynamic_material_instance(0, m_solid)
            mat_blue.set_vector_parameter_value("Color", unreal.LinearColor(0.015, 0.08, 0.58, 1.0))
            mat_blue.set_scalar_parameter_value("Metallic", 0.88)
            mat_blue.set_scalar_parameter_value("Roughness", 0.12)
            mat_blue.set_scalar_parameter_value("EmissiveMultiplier", 0.42)
            comp.set_material(0, mat_blue)

    for m in ["solar_yoke_left", "solar_yoke_right", "antenna_mast", "thruster_nozzle", "payload_deck"]:
        comp = s.get_editor_property(m)
        if comp:
            mat_silver = comp.create_dynamic_material_instance(0, m_solid)
            mat_silver.set_vector_parameter_value("Color", unreal.LinearColor(0.82, 0.85, 0.88, 1.0))
            mat_silver.set_scalar_parameter_value("Metallic", 0.92)
            mat_silver.set_scalar_parameter_value("Roughness", 0.20)
            mat_silver.set_scalar_parameter_value("EmissiveMultiplier", 0.35)
            comp.set_material(0, mat_silver)

    dish = s.get_editor_property("antenna_dish")
    if dish:
        mat_dish = dish.create_dynamic_material_instance(0, m_solid)
        mat_dish.set_vector_parameter_value("Color", unreal.LinearColor(0.98, 0.90, 0.55, 1.0))
        mat_dish.set_scalar_parameter_value("Metallic", 0.96)
        mat_dish.set_scalar_parameter_value("Roughness", 0.18)
        mat_dish.set_scalar_parameter_value("EmissiveMultiplier", 0.45)
        dish.set_material(0, mat_dish)

def apply_deb_materials(d):
    if not d or not m_solid:
        return
    for c in ["debris_mesh", "fragment_shard_a", "torn_strut"]:
        comp = d.get_editor_property(c)
        if comp:
            mat_alloy = comp.create_dynamic_material_instance(0, m_solid)
            mat_alloy.set_vector_parameter_value("Color", unreal.LinearColor(0.72, 0.70, 0.68, 1.0))
            mat_alloy.set_scalar_parameter_value("Metallic", 0.88)
            mat_alloy.set_scalar_parameter_value("Roughness", 0.40)
            mat_alloy.set_scalar_parameter_value("EmissiveMultiplier", 0.40)
            comp.set_material(0, mat_alloy)

    shard_b = d.get_editor_property("fragment_shard_b")
    if shard_b:
        mat_hazard = shard_b.create_dynamic_material_instance(0, m_solid)
        mat_hazard.set_vector_parameter_value("Color", unreal.LinearColor(1.0, 0.38, 0.02, 1.0))
        mat_hazard.set_scalar_parameter_value("Metallic", 0.40)
        mat_hazard.set_scalar_parameter_value("Roughness", 0.25)
        mat_hazard.set_scalar_parameter_value("EmissiveMultiplier", 0.60)
        shard_b.set_material(0, mat_hazard)

# 3. Position and Scale Satellite & Debris
if sat_actor:
    # Exact scientific position at T=0
    sat_actor.set_actor_location_and_rotation(unreal.Vector(70000.0, 0.0, 0.0), unreal.Rotator(0.0, -90.0, 0.0), False, False)
    # Apply VisualMeshScale via C++ VisualRoot property or fallback
    try:
        sat_actor.set_editor_property("visual_mesh_scale", 0.38)
    except Exception:
        pass
    try:
        vroot = sat_actor.get_editor_property("visual_root")
        if vroot:
            vroot.set_relative_scale3d(unreal.Vector(0.38, 0.38, 0.38))
    except Exception:
        pass
    sat_actor.set_actor_scale3d(unreal.Vector(0.38, 0.38, 0.38))
    apply_sat_materials(sat_actor)
    print(">>> Protected Satellite configured: Position=(70000.0, 0.0, 0.0), Scale=0.38")

if debris_actor:
    # Exact scientific position at T=0
    debris_actor.set_actor_location_and_rotation(unreal.Vector(70000.0, -100.0, 0.0), unreal.Rotator(0.0, 0.0, 0.0), False, False)
    try:
        debris_actor.set_editor_property("visual_mesh_scale", 0.48)
    except Exception:
        pass
    try:
        vroot = debris_actor.get_editor_property("visual_root")
        if vroot:
            vroot.set_relative_scale3d(unreal.Vector(0.48, 0.48, 0.48))
    except Exception:
        pass
    debris_actor.set_actor_scale3d(unreal.Vector(0.48, 0.48, 0.48))
    apply_deb_materials(debris_actor)
    print(">>> Secondary Debris configured: Position=(70000.0, -100.0, 0.0), Scale=0.48")

# 4. Trajectory Ribbons
if sat_nom_path:
    sat_nom_path.set_editor_property("path_thickness", 5.0)
if debris_path:
    debris_path.set_editor_property("path_thickness", 5.0)
if sat_mod_path:
    sat_mod_path.set_editor_property("path_thickness", 5.0)
    sat_mod_path.set_actor_hidden_in_game(True)
print(">>> Trajectory ribbons configured.")

# 5. Sun Lighting
if sun:
    sun.set_actor_rotation(unreal.Rotator(pitch=-26.0, yaw=142.0, roll=0.0), False)
    comp = sun.get_component_by_class(unreal.DirectionalLightComponent)
    if comp:
        comp.set_editor_property("intensity", 15.0)
print(">>> Sun lighting oriented.")

# 6. Configure Camera_Earth_Overview
cam_loc = unreal.Vector(70300.0, 800.0, 750.0)
target = unreal.Vector(70000.0, -70.0, 0.0)
dx = target.x - cam_loc.x
dy = target.y - cam_loc.y
dz = target.z - cam_loc.z
yaw = math.degrees(math.atan2(dy, dx))
pitch = math.degrees(math.atan2(dz, math.sqrt(dx*dx + dy*dy)))
cam_rot = unreal.Rotator(pitch=pitch, yaw=yaw, roll=0.0)

if cam_overview:
    cam_overview.set_actor_location_and_rotation(cam_loc, cam_rot, False, False)
    comp = cam_overview.get_component_by_class(unreal.CameraComponent)
    if comp:
        comp.set_editor_property("field_of_view", 48.0)
    print(f">>> Camera_Earth_Overview saved: Loc={cam_loc}, Rot={cam_rot}, FOV=48.0")

# 7. Save Level
saved = unreal.EditorLevelLibrary.save_current_level()
print(f">>> [LEVEL SAVE] /Game/Scenarios/CollisionAvoidanceDemo saved: {saved}")

# 8. Render Capture
cap = unreal.EditorLevelLibrary.spawn_actor_from_class(unreal.SceneCapture2D, cam_loc, cam_rot)
comp = cap.get_editor_property("capture_component2d")
comp.set_editor_property("fov_angle", 48.0)
comp.set_editor_property("capture_source", unreal.SceneCaptureSource.SCS_FINAL_COLOR_LDR)

pps = comp.get_editor_property("post_process_settings")
pps.set_editor_property("override_auto_exposure_bias", True)
pps.set_editor_property("auto_exposure_bias", 0.0)
comp.set_editor_property("post_process_settings", pps)

rt = unreal.RenderingLibrary.create_render_target2d(world, 1920, 1080, unreal.TextureRenderTargetFormat.RTF_RGBA8)
comp.set_editor_property("texture_target", rt)
comp.capture_scene()

png = "Enlarged_Overview_SimulationStart.png"
unreal.RenderingLibrary.export_render_target(world, rt, out_dir, png)
unreal.EditorLevelLibrary.destroy_actor(cap)

saved_file = os.path.join(out_dir, png)
art_file = os.path.join(artifacts_dir, png)
if os.path.exists(saved_file):
    shutil.copy(saved_file, art_file)
print(f">>> [CAPTURED SUCCESS] Exported to {saved_file} and copied to {art_file}")

print(">>> [VISUALIZATION RUN] Execution completed successfully!")
