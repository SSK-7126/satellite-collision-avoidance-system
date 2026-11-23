"""
verify_milestone_playback.py
============================
Simulate full milestone sequence in Unreal Engine:
- Set optimal Camera_Earth_Overview transform and FOV
- Set visual scales (0.38 sat, 0.48 debris) and materials
- Set trajectory path thickness (6.0 uu)
- Jump to each milestone step (1 through 8) via OrbitSimulationManager
- Capture the camera view for each step
"""
import unreal
import os

out_dir = (unreal.Paths.project_saved_dir() + "Screenshots/WindowsEditor/MilestoneSequence").replace("\\", "/")
os.makedirs(out_dir, exist_ok=True)

world = unreal.EditorLevelLibrary.get_editor_world()
actors = unreal.EditorLevelLibrary.get_all_level_actors()

sim_mgr = None
cam_overview = None
sat = None
deb = None
sun = None
sat_nom = None
deb_nom = None
sat_mod = None

for a in actors:
    lbl = a.get_actor_label()
    if lbl == "OrbitSimulationManager":
        sim_mgr = a
    elif lbl == "Camera_Earth_Overview":
        cam_overview = a
    elif lbl == "ProtectedSatellite_Payload01":
        sat = a
    elif lbl == "SecondaryDebris_Object99":
        deb = a
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

# 1. Update Camera_Earth_Overview transform and FOV
# Optimal elevated trailing quarter vantage:
opt_loc = unreal.Vector(70800.0, 600.0, 500.0)
opt_rot = unreal.Rotator(pitch=-25.87, yaw=-140.91, roll=0.0)
if cam_overview:
    cam_overview.set_actor_location_and_rotation(opt_loc, opt_rot, False, False)
    cam_comp = cam_overview.get_component_by_class(unreal.CameraComponent)
    if cam_comp:
        cam_comp.set_editor_property("field_of_view", 56.0)
    print("Updated Camera_Earth_Overview to optimal elevated vantage.")

# 2. Update visual scales
if sat:
    sat.set_actor_scale3d(unreal.Vector(0.38, 0.38, 0.38))
    apply_sat_mat(sat)
if deb:
    deb.set_actor_scale3d(unreal.Vector(0.48, 0.48, 0.48))
    apply_deb_mat(deb)

# 3. Trajectory path thickness
if sat_nom: sat_nom.set_editor_property("path_thickness", 6.0)
if deb_nom: deb_nom.set_editor_property("path_thickness", 6.0)
if sat_mod: sat_mod.set_editor_property("path_thickness", 6.0)

# 4. Sun lighting
if sun:
    sun.set_actor_rotation(unreal.Rotator(pitch=-24.0, yaw=150.0, roll=0.0), False)
    comp = sun.get_component_by_class(unreal.DirectionalLightComponent)
    comp.set_editor_property("intensity", 14.5)

def capture_active_camera(filename):
    # Find current active camera from sim_mgr or capture overview
    # Capture from cam_overview or step's target camera
    cam = cam_overview
    if sim_mgr:
        cam_idx = sim_mgr.get_editor_property("current_camera_index")
        cam_views = sim_mgr.get_editor_property("camera_views")
        if cam_idx < len(cam_views):
            cam = cam_views[cam_idx]

    loc = cam.get_actor_location()
    rot = cam.get_actor_rotation()
    cam_comp = cam.get_component_by_class(unreal.CameraComponent)
    fov = cam_comp.get_editor_property("field_of_view") if cam_comp else 56.0

    cap = unreal.EditorLevelLibrary.spawn_actor_from_class(unreal.SceneCapture2D, loc, rot)
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

    png = f"{filename}.png"
    unreal.RenderingLibrary.export_render_target(world, rt, out_dir, png)
    unreal.EditorLevelLibrary.destroy_actor(cap)
    print(f"Captured {filename} via {cam.get_actor_label()}")

# Jump to Step 1: Initial Setup
if sim_mgr:
    sim_mgr.jump_to_step(1)
    apply_sat_mat(sat, False)
capture_active_camera("Step1_InitialSetup_Overview")

# Jump to Step 2: Protected Satellite
if sim_mgr:
    sim_mgr.jump_to_step(2)
capture_active_camera("Step2_ProtectedSatellite")

# Jump to Step 4: Conjunction Alert (TCA)
if sim_mgr:
    sim_mgr.jump_to_step(4)
capture_active_camera("Step4_ConjunctionAlert_TCA")

# Jump to Step 6: Burn Execution
if sim_mgr:
    sim_mgr.jump_to_step(6)
    apply_sat_mat(sat, True)
capture_active_camera("Step6_BurnExecution")

# Jump to Step 8: Safe Clearance
if sim_mgr:
    sim_mgr.jump_to_step(8)
capture_active_camera("Step8_SafeClearance")

print("VERIFY_MILESTONES_COMPLETE")
