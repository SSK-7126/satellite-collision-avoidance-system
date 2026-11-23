"""
test_overview_candidates.py
===========================
Systematically test camera positions for Camera_Earth_Overview to find the perfect framing:
- Satellite & Debris as primary subjects
- Both recognizable immediately without zooming
- Solar panels and debris geometry clearly distinguishable
- Earth in background
- Trajectories distinguishable (cyan, red, green)
"""
import unreal
import os
import math

out_dir = (unreal.Paths.project_saved_dir() + "Screenshots/WindowsEditor/OverviewCandidates").replace("\\", "/")
os.makedirs(out_dir, exist_ok=True)

world = unreal.EditorLevelLibrary.get_editor_world()
actors = unreal.EditorLevelLibrary.get_all_level_actors()

sat_actor = None
debris_actor = None
earth_actor = None
dir_light = None
sat_nominal_path = None
debris_path = None
sat_modified_path = None

for a in actors:
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

m_solid = unreal.EditorAssetLibrary.load_asset("/Game/Common/M_SolidColor")

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
        mat_body.set_scalar_parameter_value("EmissiveMultiplier", 0.45)
        body.set_material(0, mat_body)

    for p_name in ["solar_panel_left", "solar_panel_left_outboard", "solar_panel_right", "solar_panel_right_outboard"]:
        p_comp = sat.get_editor_property(p_name)
        if p_comp:
            mat_blue = p_comp.create_dynamic_material_instance(0, m_solid)
            mat_blue.set_vector_parameter_value("Color", unreal.LinearColor(0.015, 0.08, 0.55, 1.0))
            mat_blue.set_scalar_parameter_value("Metallic", 0.85)
            mat_blue.set_scalar_parameter_value("Roughness", 0.15)
            mat_blue.set_scalar_parameter_value("EmissiveMultiplier", 0.4)
            p_comp.set_material(0, mat_blue)

    for m_name in ["solar_yoke_left", "solar_yoke_right", "antenna_mast", "thruster_nozzle", "payload_deck"]:
        m_comp = sat.get_editor_property(m_name)
        if m_comp:
            mat_silver = m_comp.create_dynamic_material_instance(0, m_solid)
            mat_silver.set_vector_parameter_value("Color", unreal.LinearColor(0.78, 0.82, 0.86, 1.0))
            mat_silver.set_scalar_parameter_value("Metallic", 0.9)
            mat_silver.set_scalar_parameter_value("Roughness", 0.25)
            mat_silver.set_scalar_parameter_value("EmissiveMultiplier", 0.3)
            m_comp.set_material(0, mat_silver)

    dish = sat.get_editor_property("antenna_dish")
    if dish:
        mat_dish = dish.create_dynamic_material_instance(0, m_solid)
        mat_dish.set_vector_parameter_value("Color", unreal.LinearColor(0.95, 0.88, 0.55, 1.0))
        mat_dish.set_scalar_parameter_value("Metallic", 0.95)
        mat_dish.set_scalar_parameter_value("Roughness", 0.2)
        mat_dish.set_scalar_parameter_value("EmissiveMultiplier", 0.45)
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
            mat_alloy.set_scalar_parameter_value("EmissiveMultiplier", 0.35)
            c_comp.set_material(0, mat_alloy)

    shard_b = deb.get_editor_property("fragment_shard_b")
    if shard_b:
        mat_hazard = shard_b.create_dynamic_material_instance(0, m_solid)
        mat_hazard.set_vector_parameter_value("Color", unreal.LinearColor(1.0, 0.35, 0.02, 1.0))
        mat_hazard.set_scalar_parameter_value("Metallic", 0.4)
        mat_hazard.set_scalar_parameter_value("Roughness", 0.3)
        mat_hazard.set_scalar_parameter_value("EmissiveMultiplier", 0.55)
        shard_b.set_material(0, mat_hazard)

def look_at(from_pos, to_pos):
    dx = to_pos.x - from_pos.x
    dy = to_pos.y - from_pos.y
    dz = to_pos.z - from_pos.z
    yaw = math.degrees(math.atan2(dy, dx))
    pitch = math.degrees(math.atan2(dz, math.sqrt(dx*dx + dy*dy)))
    return unreal.Rotator(pitch=pitch, yaw=yaw, roll=0.0)

def capture(tag, cam_loc, target_loc, fov=60.0):
    cam_rot = look_at(cam_loc, target_loc)
    capture_actor = unreal.EditorLevelLibrary.spawn_actor_from_class(unreal.SceneCapture2D, cam_loc, cam_rot)
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

    png_name = f"{tag}.png"
    unreal.RenderingLibrary.export_render_target(world, rt, out_dir, png_name)
    unreal.EditorLevelLibrary.destroy_actor(capture_actor)
    print(f"Captured {tag}")

# Set positions at t = 0
sat_actor.set_actor_location_and_rotation(unreal.Vector(70000.0, 0.0, 0.0), unreal.Rotator(0.0, -90.0, 0.0), False, False)
debris_actor.set_actor_location_and_rotation(unreal.Vector(70000.0, -100.0, 0.0), unreal.Rotator(0.0, 0.0, 0.0), False, False)

apply_satellite_materials(sat_actor)
apply_debris_materials(debris_actor)

# Trajectory thicknesses: 10 uu
sat_nominal_path.set_editor_property("path_thickness", 10.0)
debris_path.set_editor_property("path_thickness", 10.0)
sat_modified_path.set_editor_property("path_thickness", 10.0)
sat_modified_path.set_actor_hidden_in_game(False) # show so we can evaluate all 3 distinguishable paths

# Sun lighting
if dir_light:
    dir_light.set_actor_rotation(unreal.Rotator(pitch=-22.0, yaw=148.0, roll=0.0), False)
    comp = dir_light.get_component_by_class(unreal.DirectionalLightComponent)
    comp.set_editor_property("intensity", 14.0)

# Target midpoint between sat and debris
midpoint = unreal.Vector(70000.0, -50.0, 0.0)

# Test 1: Broadside 3/4 elevated view
# Sat scale 0.35, Debris scale 0.45
sat_actor.set_actor_scale3d(unreal.Vector(0.35, 0.35, 0.35))
debris_actor.set_actor_scale3d(unreal.Vector(0.45, 0.45, 0.45))

# Candidate A: Cam at (71200, 200, 500), looking at midpoint
capture("Candidate_A", unreal.Vector(71200.0, 200.0, 500.0), midpoint, fov=58.0)

# Candidate B: Broadside flank - Cam at (71400, -50, 450), looking directly at midpoint
capture("Candidate_B", unreal.Vector(71400.0, -50.0, 450.0), midpoint, fov=55.0)

# Candidate C: Slightly wider context - Cam at (71800, 100, 700), looking at midpoint
capture("Candidate_C", unreal.Vector(71800.0, 100.0, 700.0), midpoint, fov=55.0)

# Candidate D: Satellite scale 0.45, Debris scale 0.55 - Cam at (71600, 250, 600)
sat_actor.set_actor_scale3d(unreal.Vector(0.45, 0.45, 0.45))
debris_actor.set_actor_scale3d(unreal.Vector(0.55, 0.55, 0.55))
capture("Candidate_D", unreal.Vector(71600.0, 250.0, 600.0), midpoint, fov=58.0)

# Candidate E: Flank angle showing Earth curve below and space above
# Cam at (71000, -350, 400), looking towards (70000, 20, -50)
capture("Candidate_E", unreal.Vector(71000.0, -350.0, 400.0), unreal.Vector(70000.0, 20.0, -50.0), fov=56.0)

print("ALL_OVERVIEW_CANDIDATES_TESTED")
