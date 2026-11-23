"""
capture_mission_control_preview.py
===================================
Executes within Unreal Editor via UnrealEditor-Cmd.exe (hardware rendering enabled).
Renders the 3D scene from the approved Mission Control Overview camera.
"""
import unreal
import math
import os
import shutil

print(">>> [MISSION CONTROL CAPTURE] Loading CollisionAvoidanceDemo level...")
level_path = "/Game/Scenarios/CollisionAvoidanceDemo"
loaded = unreal.EditorLevelLibrary.load_level(level_path)
print(f">>> Level loaded: {loaded}")

world = unreal.EditorLevelLibrary.get_editor_world()
all_actors = unreal.EditorLevelLibrary.get_all_level_actors()

sat = None
deb = None
earth = None
sim = None
sun = None
sat_nom_path = None
deb_path = None
sat_mod_path = None
conj_viz = None
man_viz = None

for a in all_actors:
    lbl = a.get_actor_label()
    cname = a.get_class().get_name()
    if isinstance(a, unreal.SatelliteActor):
        sat = a
    elif isinstance(a, unreal.DebrisActor):
        deb = a
    elif isinstance(a, unreal.EarthActor):
        earth = a
    elif isinstance(a, unreal.OrbitSimulationManager):
        sim = a
    elif isinstance(a, unreal.DirectionalLight):
        sun = a
    elif lbl == "OrbitPath_SatelliteNominal":
        sat_nom_path = a
    elif lbl == "OrbitPath_DebrisNominal":
        deb_path = a
    elif lbl == "OrbitPath_SatelliteModified":
        sat_mod_path = a
    elif lbl == "Conjunction_Visualizer" or isinstance(a, unreal.ConjunctionVisualizer):
        conj_viz = a
    elif lbl == "Manoeuvre_Visualizer" or isinstance(a, unreal.ManoeuvreVisualizer):
        man_viz = a

print(f">>> Actors found: sat={sat is not None}, deb={deb is not None}, earth={earth is not None}")

# 1. Earth Setup: Center background, visual radius 16000 uu
if earth:
    earth.set_actor_location(unreal.Vector(0.0, 0.0, 0.0), False, False)
    em = earth.get_editor_property("earth_mesh")
    m_earth = unreal.EditorAssetLibrary.load_asset("/Game/Earth/M_Earth")
    if em and m_earth:
        em.set_material(0, m_earth)
        em.set_relative_scale3d(unreal.Vector(160.0, 160.0, 160.0))
    atm = earth.get_editor_property("atmosphere_mesh")
    m_atmo = unreal.EditorAssetLibrary.load_asset("/Game/Earth/M_Atmosphere")
    if atm and m_atmo:
        atm.set_material(0, m_atmo)
        atm.set_relative_scale3d(unreal.Vector(163.0, 163.0, 163.0))
        atm.set_visibility(True)
        atm.set_hidden_in_game(False)
    print(">>> Earth configured: realistic marble scaled to 16,000 uu in background.")

# 2. Materials
m_solid = unreal.EditorAssetLibrary.load_asset("/Game/Common/M_SolidColor")

# 3. Position and scale Satellite in foreground left
# In Mission Control framing
sat_pos = unreal.Vector(50000.0, -22000.0, 1200.0)
if sat:
    sat.set_actor_location_and_rotation(sat_pos, unreal.Rotator(12.0, -60.0, 5.0), False, False)
    vroot = sat.get_editor_property("visual_root")
    if vroot:
        vroot.set_relative_scale3d(unreal.Vector(2.4, 2.4, 2.4))
    sat_body = sat.get_editor_property("satellite_body")
    if sat_body and m_solid:
        mb = sat_body.create_dynamic_material_instance(0, m_solid)
        mb.set_vector_parameter_value("Color", unreal.LinearColor(0.98, 0.82, 0.28, 1.0))
        mb.set_scalar_parameter_value("Metallic", 0.92)
        mb.set_scalar_parameter_value("Roughness", 0.18)
        mb.set_scalar_parameter_value("EmissiveMultiplier", 0.45)
    print(">>> Satellite configured: foreground left, scaled 2.4x.")

# 4. Position and scale Debris in mid-right
deb_pos = unreal.Vector(56000.0, -15000.0, 1400.0)
if deb:
    deb.set_actor_location_and_rotation(deb_pos, unreal.Rotator(20.0, 35.0, 10.0), False, False)
    vroot = deb.get_editor_property("visual_root")
    if vroot:
        vroot.set_relative_scale3d(unreal.Vector(2.2, 2.2, 2.2))
    deb_mesh = deb.get_editor_property("debris_mesh")
    if deb_mesh and m_solid:
        mdb = deb_mesh.create_dynamic_material_instance(0, m_solid)
        mdb.set_vector_parameter_value("Color", unreal.LinearColor(0.85, 0.85, 0.88, 1.0))
        mdb.set_scalar_parameter_value("Metallic", 0.80)
        mdb.set_scalar_parameter_value("Roughness", 0.35)
        mdb.set_scalar_parameter_value("EmissiveMultiplier", 0.25)
    print(">>> Debris configured: mid-right foreground, scaled 2.2x.")

# 5. Enable modified trajectory
if sat_mod_path:
    sat_mod_path.set_actor_hidden_in_game(False)

# 6. Overview Camera framing matching IMAGE A
# Looking from (32000, -38000, 12000) towards (20000, -8000, 0)
cam_pos = unreal.Vector(34000.0, -36000.0, 11000.0)
target = unreal.Vector(18000.0, -6000.0, 0.0)
to_tgt = target - cam_pos
yaw = math.degrees(math.atan2(to_tgt.y, to_tgt.x))
pitch = math.degrees(math.atan2(to_tgt.z, math.sqrt(to_tgt.x**2 + to_tgt.y**2)))
cam_rot = unreal.Rotator(pitch=pitch, yaw=yaw, roll=0.0)
fov = 46.0

print(f">>> Viewport Camera: Pos={cam_pos}, Rot={cam_rot}, FOV={fov}")

# 7. SceneCapture2D with normal hardware rendering
cap = unreal.EditorLevelLibrary.spawn_actor_from_class(unreal.SceneCapture2D, cam_pos, cam_rot)
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

out_dir = "C:/Users/Sriram Krovi/satellite-collision-avoidance-system/Project_Deliverables/Windows_Package/Reports/Screenshots"
os.makedirs(out_dir, exist_ok=True)
png_name = "MissionControl_3D_Scene_Render.png"
unreal.RenderingLibrary.export_render_target(world, rt, out_dir, png_name)
unreal.EditorLevelLibrary.destroy_actor(cap)

raw_file = os.path.join(out_dir, png_name)
print(f">>> [CAPTURE SUCCESS] 3D Scene rendered to: {raw_file} (exists: {os.path.exists(raw_file)})")

# Copy to conversation artifacts
art_dir = "C:/Users/Sriram Krovi/.gemini/antigravity/brain/cdd0c206-fcf3-4310-8916-ebe32a293b35"
os.makedirs(art_dir, exist_ok=True)
shutil.copy(raw_file, os.path.join(art_dir, png_name))

# Clean exit
print(">>> [MISSION CONTROL CAPTURE] Complete! Calling quit_editor...")
unreal.SystemLibrary.quit_editor()
