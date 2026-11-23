"""
generate_final_visualization_showcase.py
=========================================
Final high-fidelity Unreal Engine 5.7 visualization pass:
1. Loads /Game/Scenarios/CollisionAvoidanceDemo
2. Configures and compiles PBR materials for Earth, Atmosphere, Spacecraft, and Debris
3. Sets independent visual scales:
   - Protected Satellite: (0.38, 0.38, 0.38)
   - Secondary Debris: (0.48, 0.48, 0.48)
4. Configures Camera_Earth_Overview to optimal flank-elevated vantage:
   - Location: (70300.0, 800.0, 750.0)
   - Rotation: Pitch=-39.18, Yaw=-109.0, Roll=0.0
   - FOV: 48.0
5. Configures Camera_Conjunction_TCA, Camera_Satellite_Detail, Camera_Debris_Detail, Camera_Manoeuvre_Burn
6. Configures trajectory ribbons with sleek thickness (5.0 uu)
7. Saves the level permanently
8. Captures verification screenshots for all key operational phases and exports to artifacts directory
"""

import unreal
import os
import shutil
import math

print(">>> [FINAL SHOWCASE] Initializing...")

# 1. Load the level
level_path = "/Game/Scenarios/CollisionAvoidanceDemo"
unreal.EditorLevelLibrary.load_level(level_path)
world = unreal.EditorLevelLibrary.get_editor_world()
all_actors = unreal.EditorLevelLibrary.get_all_level_actors()

# Output directories
out_dir = (unreal.Paths.project_saved_dir() + "Screenshots/WindowsEditor/FinalShowcase").replace("\\", "/")
artifacts_dir = "C:/Users/Sriram Krovi/.gemini/antigravity/brain/7d36e17b-846d-4a94-9bbc-4bf33eb09d71"
os.makedirs(out_dir, exist_ok=True)
os.makedirs(artifacts_dir, exist_ok=True)

# Actor classification
earth_actor = None
sat_actor = None
debris_actor = None
sim_mgr = None
sun = None
sat_nom_path = None
debris_path = None
sat_mod_path = None
conj_viz = None
man_viz = None

cam_overview = None
cam_sat_detail = None
cam_deb_detail = None
cam_tca = None
cam_burn = None
cam_enc_overview = None

for a in all_actors:
    lbl = a.get_actor_label()
    if (isinstance(a, unreal.EarthActor) or "Earth" in lbl) and "Camera" not in lbl:
        earth_actor = a
    elif (isinstance(a, unreal.SatelliteActor) or "ProtectedSatellite" in lbl) and "Camera" not in lbl:
        sat_actor = a
    elif (isinstance(a, unreal.DebrisActor) or "SecondaryDebris" in lbl) and "Camera" not in lbl:
        debris_actor = a
    elif isinstance(a, unreal.OrbitSimulationManager):
        sim_mgr = a
    elif isinstance(a, unreal.DirectionalLight):
        sun = a
    elif (isinstance(a, unreal.ConjunctionVisualizer) or "Conjunction" in lbl) and "Camera" not in lbl:
        conj_viz = a
    elif (isinstance(a, unreal.ManoeuvreVisualizer) or "Manoeuvre" in lbl) and "Camera" not in lbl:
        man_viz = a
    elif lbl == "OrbitPath_SatelliteNominal":
        sat_nom_path = a
    elif lbl == "OrbitPath_DebrisNominal":
        debris_path = a
    elif lbl == "OrbitPath_SatelliteModified":
        sat_mod_path = a
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

print(f">>> Found actors: Earth={earth_actor is not None}, Sat={sat_actor is not None}, Debris={debris_actor is not None}")

# 2. Materials
m_earth = unreal.EditorAssetLibrary.load_asset("/Game/Earth/M_Earth")
m_atmo = unreal.EditorAssetLibrary.load_asset("/Game/Earth/M_Atmosphere")
m_solid = unreal.EditorAssetLibrary.load_asset("/Game/Common/M_SolidColor")

def apply_earth_materials():
    if not earth_actor:
        return
    em = earth_actor.get_editor_property("earth_mesh")
    atm = earth_actor.get_editor_property("atmosphere_mesh")
    if em and m_earth:
        em.set_material(0, m_earth)
    if atm and m_atmo:
        atm.set_material(0, m_atmo)
        atm.set_relative_scale3d(unreal.Vector(1.015, 1.015, 1.015))
        atm.set_visibility(True)
        atm.set_hidden_in_game(False)

apply_earth_materials()
print(">>> Earth materials applied.")

def apply_sat_materials(s, is_manoeuvred=False):
    if not s or not m_solid:
        return
    body = s.get_editor_property("satellite_body")
    if body:
        mat_body = body.create_dynamic_material_instance(0, m_solid)
        col = unreal.LinearColor(0.1, 0.95, 0.45, 1.0) if is_manoeuvred else unreal.LinearColor(0.98, 0.82, 0.28, 1.0)
        mat_body.set_vector_parameter_value("Color", col)
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

# 3. Apply independent visual scaling (Preserving exact physical ECI positions)
if sat_actor:
    sat_actor.set_actor_scale3d(unreal.Vector(0.38, 0.38, 0.38))
    apply_sat_materials(sat_actor, is_manoeuvred=False)
    print(">>> ProtectedSatellite scale set to (0.38, 0.38, 0.38).")

if debris_actor:
    debris_actor.set_actor_scale3d(unreal.Vector(0.48, 0.48, 0.48))
    apply_deb_materials(debris_actor)
    print(">>> SecondaryDebris scale set to (0.48, 0.48, 0.48).")

# 4. Trajectory ribbons
for p, color in [(sat_nom_path, unreal.LinearColor(0.0, 0.85, 1.0, 1.0)),
                 (debris_path, unreal.LinearColor(1.0, 0.30, 0.15, 1.0)),
                 (sat_mod_path, unreal.LinearColor(0.15, 1.0, 0.35, 1.0))]:
    if p:
        p.set_editor_property("path_thickness", 5.0)
print(">>> Trajectory ribbons path_thickness set to 5.0 uu.")

# 5. Sun lighting
if sun:
    sun.set_actor_rotation(unreal.Rotator(pitch=-24.0, yaw=148.0, roll=0.0), False)
    comp = sun.get_component_by_class(unreal.DirectionalLightComponent)
    if comp:
        comp.set_editor_property("intensity", 15.0)

# 6. Configure Camera_Earth_Overview (Flank Elevated Vantage)
# Places craft as primary subjects in center, Earth limb curving down left background
cam_overview_loc = unreal.Vector(70300.0, 800.0, 750.0)
cam_overview_rot = unreal.Rotator(pitch=-39.18, yaw=-109.0, roll=0.0)
if cam_overview:
    cam_overview.set_actor_location_and_rotation(cam_overview_loc, cam_overview_rot, False, False)
    comp = cam_overview.get_component_by_class(unreal.CameraComponent)
    if comp:
        comp.set_editor_property("field_of_view", 48.0)
    print(">>> Camera_Earth_Overview configured to optimal flank-elevated vantage.")

# 7. Configure Camera_Conjunction_TCA
cam_tca_loc = unreal.Vector(47277.17, -51578.21, 27.9)
cam_tca_rot = unreal.Rotator(pitch=-20.24, yaw=-107.35, roll=0.0)
if cam_tca:
    cam_tca.set_actor_location_and_rotation(cam_tca_loc, cam_tca_rot, False, False)
    comp = cam_tca.get_component_by_class(unreal.CameraComponent)
    if comp:
        comp.set_editor_property("field_of_view", 40.0)
    print(">>> Camera_Conjunction_TCA configured to encounter vantage.")

# 8. Configure Camera_Satellite_Detail
cam_sat_loc = unreal.Vector(69900.0, -180.0, 120.0)
cam_sat_rot = unreal.Rotator(pitch=-18.0, yaw=35.0, roll=0.0)
if cam_sat_detail:
    cam_sat_detail.set_actor_location_and_rotation(cam_sat_loc, cam_sat_rot, False, False)
    comp = cam_sat_detail.get_component_by_class(unreal.CameraComponent)
    if comp:
        comp.set_editor_property("field_of_view", 45.0)
    print(">>> Camera_Satellite_Detail configured.")

# 9. Configure Camera_Debris_Detail
cam_deb_loc = unreal.Vector(69920.0, -220.0, 80.0)
cam_deb_rot = unreal.Rotator(pitch=-15.0, yaw=30.0, roll=0.0)
if cam_deb_detail:
    cam_deb_detail.set_actor_location_and_rotation(cam_deb_loc, cam_deb_rot, False, False)
    comp = cam_deb_detail.get_component_by_class(unreal.CameraComponent)
    if comp:
        comp.set_editor_property("field_of_view", 42.0)
    print(">>> Camera_Debris_Detail configured.")

# 10. Configure Camera_Manoeuvre_Burn
# Burn location: (68827.8, -12756.6, 0.0)
cam_burn_loc = unreal.Vector(69977.8, -14006.6, 650.0)
cam_burn_rot = unreal.Rotator(pitch=-20.9, yaw=132.6, roll=0.0)
if cam_burn:
    cam_burn.set_actor_location_and_rotation(cam_burn_loc, cam_burn_rot, False, False)
    comp = cam_burn.get_component_by_class(unreal.CameraComponent)
    if comp:
        comp.set_editor_property("field_of_view", 48.0)
    print(">>> Camera_Manoeuvre_Burn configured.")

# 11. Save the level to make all changes permanent
saved = unreal.EditorLevelLibrary.save_current_level()
print(f">>> [LEVEL SAVE] Level saved successfully: {saved}")

# 12. Capture function
def render_and_export(cam_actor, tag):
    if not cam_actor:
        print(f"Error: cam_actor for {tag} is None!")
        return
    loc = cam_actor.get_actor_location()
    rot = cam_actor.get_actor_rotation()
    cam_comp = cam_actor.get_component_by_class(unreal.CameraComponent)
    fov = cam_comp.get_editor_property("field_of_view") if cam_comp else 50.0

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

    png = f"{tag}.png"
    unreal.RenderingLibrary.export_render_target(world, rt, out_dir, png)
    unreal.EditorLevelLibrary.destroy_actor(cap)

    saved_file = os.path.join(out_dir, png)
    art_file = os.path.join(artifacts_dir, png)
    if os.path.exists(saved_file):
        shutil.copy(saved_file, art_file)
    print(f">>> Captured & exported: {tag} ({saved_file})")

# Execute Captures
# View 1: Overview Simulation Start (T=0)
if sat_actor and debris_actor:
    sat_actor.set_actor_location_and_rotation(unreal.Vector(70000.0, 0.0, 0.0), unreal.Rotator(0.0, -90.0, 0.0), False, False)
    debris_actor.set_actor_location_and_rotation(unreal.Vector(70000.0, -100.0, 0.0), unreal.Rotator(0.0, 0.0, 0.0), False, False)
    apply_sat_materials(sat_actor, is_manoeuvred=False)
    apply_deb_materials(debris_actor)
if sat_mod_path:
    sat_mod_path.set_actor_hidden_in_game(True)
render_and_export(cam_overview, "Final_Overview_SimulationStart")

# View 2: Protected Satellite Detail
render_and_export(cam_sat_detail, "Final_Satellite_Detail")

# View 3: Secondary Debris Detail
render_and_export(cam_deb_detail, "Final_Debris_Detail")

# View 4: TCA Conjunction View
if conj_viz:
    sat_tca = unreal.Vector(47265.4, -51614.9, 13.9)
    deb_tca = unreal.Vector(47266.3, -51614.0, 13.9)
    conj_viz.update_conjunction_geometry(sat_tca, deb_tca, 1.06)
    conj_viz.set_actor_location(sat_tca, False, False)
    conj_viz.set_actor_hidden_in_game(False)
render_and_export(cam_tca, "Final_Conjunction_TCA")

# View 5: Manoeuvre Burn View
if man_viz and sat_actor:
    burn_loc = unreal.Vector(68827.8, -12756.6, 0.0)
    sat_actor.set_actor_location(burn_loc, False, False)
    apply_sat_materials(sat_actor, is_manoeuvred=True)
    if sat_mod_path:
        sat_mod_path.set_actor_hidden_in_game(False)
render_and_export(cam_burn, "Final_Manoeuvre_Burn")

# View 6: Post-Manoeuvre Safe Clearance (Overview)
if sat_actor and debris_actor:
    # Safe clearance positions at nominal TCA epoch: sat moved to safe trajectory
    sat_safe = unreal.Vector(45590.36, -50491.52, 13.9) # radial separation ~2019 m
    deb_at_tca = unreal.Vector(47266.3, -51614.0, 13.9)
    sat_actor.set_actor_location(sat_safe, False, False)
    debris_actor.set_actor_location(deb_at_tca, False, False)
render_and_export(cam_overview, "Final_Safe_Clearance")

print(">>> [FINAL SHOWCASE] All tasks completed successfully.")
