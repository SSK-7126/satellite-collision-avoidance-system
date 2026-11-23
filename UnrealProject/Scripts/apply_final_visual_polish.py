"""
apply_final_visual_polish.py
============================
Master script for Unreal Engine 5.7:
1. Loads /Game/Scenarios/CollisionAvoidanceDemo
2. Applies visual scaling:
   - Protected Satellite: scale (0.38, 0.38, 0.38)
   - Secondary Debris: scale (0.48, 0.48, 0.48)
3. Configures camera vantage points:
   - Camera_Earth_Overview: (70800.0, 600.0, 500.0), rot=(-25.87, -140.91, 0.0), FOV=56.0
   - Camera_Conjunction_TCA: (47277.17, -51578.21, 27.9), rot=(-20.24, -107.35, 0.0), FOV=40.0
4. Sets trajectory path thickness to 6.0 uu
5. Applies PBR materials to spacecraft and debris components
6. Saves the level package permanently
7. Steps through all 8 simulation milestones and captures high-resolution screenshots
8. Exits cleanly
"""

import unreal
import os
import shutil

print(">>> [VISUAL POLISH] Starting apply_final_visual_polish.py...")

# 1. Load the level
level_path = "/Game/Scenarios/CollisionAvoidanceDemo"
unreal.EditorLevelLibrary.load_level(level_path)
world = unreal.EditorLevelLibrary.get_editor_world()
actors = unreal.EditorLevelLibrary.get_all_level_actors()

# Output directories
out_dir = (unreal.Paths.project_saved_dir() + "Screenshots/WindowsEditor/MilestoneSequence").replace("\\", "/")
artifacts_dir = "C:/Users/Sriram Krovi/.gemini/antigravity/brain/7d36e17b-846d-4a94-9bbc-4bf33eb09d71"
os.makedirs(out_dir, exist_ok=True)
os.makedirs(artifacts_dir, exist_ok=True)

# Actor references
sim_mgr = None
cam_overview = None
cam_sat_detail = None
cam_deb_detail = None
cam_tca = None
cam_burn = None
cam_enc_overview = None
sat = None
deb = None
sun = None
sat_nom = None
deb_nom = None
sat_mod = None
conj_viz = None
man_viz = None

for a in actors:
    lbl = a.get_actor_label()
    if lbl == "OrbitSimulationManager":
        sim_mgr = a
    elif lbl == "Camera_Earth_Overview":
        cam_overview = a
    elif lbl == "Camera_Satellite_Detail":
        cam_sat_detail = a
    elif lbl == "Camera_Debris_Detail":
        cam_deb_detail = a
    elif lbl == "Camera_Conjunction_TCA":
        cam_tca = a
    elif lbl == "Camera_Manoeuvre_Burn":
        cam_burn = a
    elif lbl == "Camera_Encounter_Overview":
        cam_enc_overview = a
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
    elif lbl == "Conjunction_Visualizer":
        conj_viz = a
    elif lbl == "Manoeuvre_Visualizer":
        man_viz = a

m_solid = unreal.EditorAssetLibrary.load_asset("/Game/Common/M_SolidColor")

def apply_sat_mat(s, is_manoeuvred=False):
    if not s or not m_solid:
        return
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
    if not d or not m_solid:
        return
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

# 2. Configure Camera_Earth_Overview
opt_overview_loc = unreal.Vector(70800.0, 600.0, 500.0)
opt_overview_rot = unreal.Rotator(pitch=-25.87, yaw=-140.91, roll=0.0)
if cam_overview:
    cam_overview.set_actor_location_and_rotation(opt_overview_loc, opt_overview_rot, False, False)
    comp = cam_overview.get_component_by_class(unreal.CameraComponent)
    if comp:
        comp.set_editor_property("field_of_view", 56.0)
    print(">>> Updated Camera_Earth_Overview to optimal elevated vantage.")

# 3. Configure Camera_Conjunction_TCA
opt_tca_loc = unreal.Vector(47277.17, -51578.21, 27.9)
opt_tca_rot = unreal.Rotator(pitch=-20.24, yaw=-107.35, roll=0.0)
if cam_tca:
    cam_tca.set_actor_location_and_rotation(opt_tca_loc, opt_tca_rot, False, False)
    comp = cam_tca.get_component_by_class(unreal.CameraComponent)
    if comp:
        comp.set_editor_property("field_of_view", 40.0)
    print(">>> Updated Camera_Conjunction_TCA to correct encounter vantage.")

# 4. Configure visual scales
if sat:
    sat.set_actor_scale3d(unreal.Vector(0.38, 0.38, 0.38))
    apply_sat_mat(sat, is_manoeuvred=False)
    print(">>> Set ProtectedSatellite scale to (0.38, 0.38, 0.38).")

if deb:
    deb.set_actor_scale3d(unreal.Vector(0.48, 0.48, 0.48))
    apply_deb_mat(deb)
    print(">>> Set SecondaryDebris scale to (0.48, 0.48, 0.48).")

# 5. Set Trajectory ribbon thickness
for p in [sat_nom, deb_nom, sat_mod]:
    if p:
        p.set_editor_property("path_thickness", 6.0)
print(">>> Set Trajectory ribbons path_thickness to 6.0 uu.")

# 6. Directional Light
if sun:
    sun.set_actor_rotation(unreal.Rotator(pitch=-24.0, yaw=150.0, roll=0.0), False)
    comp = sun.get_component_by_class(unreal.DirectionalLightComponent)
    if comp:
        comp.set_editor_property("intensity", 14.5)
    print(">>> Set Sun lighting orientation and intensity.")

# 7. Save the level to persist all actor scales, transforms, and properties
saved = unreal.EditorLevelLibrary.save_current_level()
print(f">>> [LEVEL SAVE] save_current_level result: {saved}")

# 8. Milestone Playback Capture Function
def capture_camera_view(cam, filename):
    if not cam:
        print(f"Warning: Camera for {filename} is None!")
        return
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

    saved_path = os.path.join(out_dir, png)
    art_path = os.path.join(artifacts_dir, png)
    if os.path.exists(saved_path):
        shutil.copy(saved_path, art_path)
    print(f">>> [CAPTURED] {filename} via {cam.get_actor_label()} (saved {saved_path})")

# Step 1: Initialize Orbital Simulation (Camera_Earth_Overview)
print(">>> Executing Step 1...")
if sim_mgr:
    sim_mgr.jump_to_step(1)
    apply_sat_mat(sat, is_manoeuvred=False)
capture_camera_view(cam_overview, "Step1_InitialSetup_Overview")

# Step 2: Protected Satellite Detail (Camera_Satellite_Detail)
print(">>> Executing Step 2...")
if sim_mgr:
    sim_mgr.jump_to_step(2)
capture_camera_view(cam_sat_detail, "Step2_ProtectedSatellite")

# Step 3: Conjunction Screening Trigger (Camera_Encounter_Overview)
print(">>> Executing Step 3...")
if sim_mgr:
    sim_mgr.jump_to_step(3)
capture_camera_view(cam_enc_overview, "Step3_EncounterOverview")

# Step 4: Encounter Assessment & Risk Metrics (Camera_Conjunction_TCA)
print(">>> Executing Step 4...")
if sim_mgr:
    sim_mgr.jump_to_step(4)
capture_camera_view(cam_tca, "Step4_ConjunctionAlert_TCA")

# Step 5: Autonomous Avoidance Planning (Camera_Satellite_Detail)
print(">>> Executing Step 5...")
if sim_mgr:
    sim_mgr.jump_to_step(5)
capture_camera_view(cam_sat_detail, "Step5_AutonomousPlanning")

# Step 6: Impulsive Burn Execution (Camera_Manoeuvre_Burn)
print(">>> Executing Step 6...")
if sim_mgr:
    sim_mgr.jump_to_step(6)
    apply_sat_mat(sat, is_manoeuvred=True)
capture_camera_view(cam_burn, "Step6_BurnExecution")

# Step 7: Modified Trajectory Divergence (Camera_Encounter_Overview)
print(">>> Executing Step 7...")
if sim_mgr:
    sim_mgr.jump_to_step(7)
capture_camera_view(cam_enc_overview, "Step7_ModifiedTrajectory")

# Step 8: Post-Manoeuvre Verification & Safe Clearance (Camera_Earth_Overview)
print(">>> Executing Step 8...")
if sim_mgr:
    sim_mgr.jump_to_step(8)
capture_camera_view(cam_overview, "Step8_SafeClearance")

# Also capture Debris Detail for complete visual inspection
capture_camera_view(cam_deb_detail, "Camera_Debris_Detail_Eval")

print(">>> [VISUAL POLISH] All captures completed successfully.")
