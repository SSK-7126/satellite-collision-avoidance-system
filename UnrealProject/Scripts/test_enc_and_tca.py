import unreal
import json
import os
import math

payload_path = os.path.abspath(os.path.join(
    os.path.dirname(__file__),
    "../../D2/visualization/unreal_simulation_payload.json"
)).replace("\\", "/")

with open(payload_path, "r", encoding="utf-8") as f:
    payload = json.load(f)

level_path = "/Game/Scenarios/CollisionAvoidanceDemo"
unreal.EditorLevelLibrary.load_level(level_path)
world = unreal.EditorLevelLibrary.get_editor_world()
all_actors = unreal.EditorLevelLibrary.get_all_level_actors()

unreal.SystemLibrary.execute_console_command(None, "DisableAllScreenMessages")
unreal.SystemLibrary.execute_console_command(None, "r.TextureStreaming 0")

for a in list(all_actors):
    cname = a.get_class().get_name()
    if "Landscape" in cname or cname in ["VolumetricCloud", "ExponentialHeightFog", "SkyAtmosphere"]:
        a.set_actor_hidden_in_game(True)
    elif a.get_actor_label() == "SM_SkySphere":
        a.set_actor_hidden_in_game(True)

earth_actor = [a for a in all_actors if isinstance(a, unreal.EarthActor)][0]
sat_actor = [a for a in all_actors if isinstance(a, unreal.SatelliteActor)][0]
debris_actor = [a for a in all_actors if isinstance(a, unreal.DebrisActor)][0]
dir_light = [a for a in all_actors if isinstance(a, unreal.DirectionalLight)][0]
sky_light = [a for a in all_actors if isinstance(a, unreal.SkyLight)][0]
conj_viz = [a for a in all_actors if isinstance(a, unreal.ConjunctionVisualizer)][0]
man_viz = [a for a in all_actors if isinstance(a, unreal.ManoeuvreVisualizer)][0]

sat_nominal_path = None
debris_path = None
sat_modified_path = None
for a in all_actors:
    if isinstance(a, unreal.OrbitPathActor):
        if "Debris" in a.get_actor_label():
            debris_path = a
        elif "Modified" in a.get_actor_label():
            sat_modified_path = a
        else:
            sat_nominal_path = a

m_solid = unreal.EditorAssetLibrary.load_asset("/Game/Common/M_SolidColor")
m_disc = unreal.EditorAssetLibrary.load_asset("/Game/Common/M_TranslucentDisc")
m_earth = unreal.EditorAssetLibrary.load_asset("/Game/Earth/M_Earth")
m_atmo = unreal.EditorAssetLibrary.load_asset("/Game/Earth/M_Atmosphere")

# Apply earth
em = earth_actor.get_editor_property("earth_mesh")
atm = earth_actor.get_editor_property("atmosphere_mesh")
if em and m_earth:
    em.set_material(0, m_earth)
if atm and m_atmo:
    atm.set_material(0, m_atmo)
    atm.set_relative_scale3d(unreal.Vector(1.015, 1.015, 1.015))

# Trajectories
sat_nom_pts = [unreal.Vector(p[0], p[1], p[2]) for p in payload["time_series"]["satellite_nominal_positions_ue"]]
debris_pts = [unreal.Vector(p[0], p[1], p[2]) for p in payload["time_series"]["debris_positions_ue"]]
sat_mod_pts = [unreal.Vector(p[0], p[1], p[2]) for p in payload["time_series"]["satellite_modified_positions_ue"]]

sat_nominal_path.set_editor_property("path_thickness", 25.0)
sat_nominal_path.set_trajectory_points(sat_nom_pts, unreal.LinearColor(0.0, 0.85, 1.0, 1.0))

debris_path.set_editor_property("path_thickness", 25.0)
debris_path.set_trajectory_points(debris_pts, unreal.LinearColor(1.0, 0.15, 0.1, 1.0))

def apply_satellite_materials(sat):
    body = sat.get_editor_property("satellite_body")
    if body:
        mat = body.create_dynamic_material_instance(0, m_solid)
        mat.set_vector_parameter_value("Color", unreal.LinearColor(0.98, 0.82, 0.28, 1.0))
        mat.set_scalar_parameter_value("Metallic", 0.9)
        mat.set_scalar_parameter_value("Roughness", 0.2)
        body.set_material(0, mat)
    for p_name in ["solar_panel_left", "solar_panel_left_outboard", "solar_panel_right", "solar_panel_right_outboard"]:
        p = sat.get_editor_property(p_name)
        if p:
            mat_b = p.create_dynamic_material_instance(0, m_solid)
            mat_b.set_vector_parameter_value("Color", unreal.LinearColor(0.015, 0.08, 0.55, 1.0))
            p.set_material(0, mat_b)
    for m_name in ["payload_deck", "solar_yoke_left", "solar_yoke_right", "antenna_mast", "thruster_nozzle"]:
        m = sat.get_editor_property(m_name)
        if m:
            mat_s = m.create_dynamic_material_instance(0, m_solid)
            mat_s.set_vector_parameter_value("Color", unreal.LinearColor(0.78, 0.82, 0.86, 1.0))
            m.set_material(0, mat_s)
    dish = sat.get_editor_property("antenna_dish")
    if dish:
        mat_d = dish.create_dynamic_material_instance(0, m_solid)
        mat_d.set_vector_parameter_value("Color", unreal.LinearColor(0.95, 0.88, 0.55, 1.0))
        dish.set_material(0, mat_d)

def apply_debris_materials(deb):
    for c_name in ["debris_mesh", "fragment_shard_a", "torn_strut"]:
        c = deb.get_editor_property(c_name)
        if c:
            mat = c.create_dynamic_material_instance(0, m_solid)
            mat.set_vector_parameter_value("Color", unreal.LinearColor(0.72, 0.70, 0.68, 1.0))
            c.set_material(0, mat)
    b = deb.get_editor_property("fragment_shard_b")
    if b:
        mat = b.create_dynamic_material_instance(0, m_solid)
        mat.set_vector_parameter_value("Color", unreal.LinearColor(1.0, 0.35, 0.02, 1.0))
        b.set_material(0, mat)

def look_at(cam_pos, target_pos):
    dx = target_pos.x - cam_pos.x
    dy = target_pos.y - cam_pos.y
    dz = target_pos.z - cam_pos.z
    yaw = math.degrees(math.atan2(dy, dx))
    dist_xy = math.sqrt(dx*dx + dy*dy)
    pitch = math.degrees(math.atan2(dz, dist_xy))
    return unreal.Rotator(pitch=pitch, yaw=yaw, roll=0.0)

out_dir = (unreal.Paths.project_saved_dir() + "Screenshots/WindowsEditor").replace("\\", "/")

def capture_view(filename_base, cam_location, cam_rotation, fov=60.0, sun_rotation=None, sun_intensity=14.0):
    if dir_light:
        if sun_rotation:
            dir_light.set_actor_rotation(sun_rotation, False)
        else:
            dir_light.set_actor_rotation(cam_rotation, False)
        comp = dir_light.get_component_by_class(unreal.DirectionalLightComponent)
        comp.set_editor_property("intensity", sun_intensity)

    capture_actor = unreal.EditorLevelLibrary.spawn_actor_from_class(unreal.SceneCapture2D, cam_location, cam_rotation)
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

    png_name = f"{filename_base}.png"
    unreal.RenderingLibrary.export_render_target(world, rt, out_dir, png_name)
    unreal.EditorLevelLibrary.destroy_actor(capture_actor)
    print(f"[CAPTURED] {out_dir}/{png_name}")

# TEST 1: ENCOUNTER OVERVIEW (Perpendicular to line of separation)
sat_pos_0 = sat_nom_pts[0]
deb_pos_0 = debris_pts[0]

sat_actor.set_actor_scale3d(unreal.Vector(0.35, 0.35, 0.35))
sat_actor.set_actor_location_and_rotation(sat_pos_0, unreal.Rotator(0.0, -90.0, 0.0), False, False)
sat_actor.set_actor_hidden_in_game(False)
apply_satellite_materials(sat_actor)

debris_actor.set_actor_scale3d(unreal.Vector(0.35, 0.35, 0.35))
debris_actor.set_actor_location(deb_pos_0, False, False)
debris_actor.set_actor_hidden_in_game(False)
apply_debris_materials(debris_actor)

sat_nominal_path.set_actor_hidden_in_game(False)
debris_path.set_actor_hidden_in_game(False)
sat_modified_path.set_actor_hidden_in_game(True)
conj_viz.set_actor_hidden_in_game(True)
man_viz.set_actor_hidden_in_game(True)

mid_enc = unreal.Vector((sat_pos_0.x + deb_pos_0.x) * 0.5, (sat_pos_0.y + deb_pos_0.y) * 0.5, (sat_pos_0.z + deb_pos_0.z) * 0.5)
enc_cam_loc = unreal.Vector(mid_enc.x + 950.0, mid_enc.y, mid_enc.z + 420.0)
enc_cam_rot = look_at(enc_cam_loc, mid_enc)
sun_enc_rot = unreal.Rotator(pitch=-30.0, yaw=140.0, roll=0.0)
capture_view("Test_Encounter_Separated", enc_cam_loc, enc_cam_rot, fov=44.0, sun_rotation=sun_enc_rot, sun_intensity=14.0)

# TEST 2: CONJUNCTION TCA (Looking OUTWARDS away from Earth into Deep Space)
nom_tca_s = payload["nominal_encounter"]["tca_seconds"]
ts = payload["time_series"]["timestamps_sec"]
tca_idx = min(range(len(ts)), key=lambda i: abs(ts[i] - nom_tca_s))
sat_tca_pos = sat_nom_pts[tca_idx]
deb_tca_pos = debris_pts[tca_idx]
miss_dist_uu = payload["nominal_encounter"]["miss_distance_m"] * payload["scenario_metadata"]["scale_factor_uu_per_m"]

sat_actor.set_actor_scale3d(unreal.Vector(0.05, 0.05, 0.05))
sat_actor.set_actor_location(sat_tca_pos, False, False)
apply_satellite_materials(sat_actor)

debris_actor.set_actor_scale3d(unreal.Vector(0.05, 0.05, 0.05))
debris_actor.set_actor_location(deb_tca_pos, False, False)
apply_debris_materials(debris_actor)

sat_nominal_path.set_actor_hidden_in_game(True)
debris_path.set_actor_hidden_in_game(True)
sat_modified_path.set_actor_hidden_in_game(True)

conj_viz.update_conjunction_geometry(sat_tca_pos, deb_tca_pos, miss_dist_uu)
conj_viz.set_actor_location(sat_tca_pos, False, False)
conj_viz.set_actor_hidden_in_game(False)

# Conjunction materials: Amber, Red, Magenta, Violet disc
tca_sph = conj_viz.get_editor_property("tca_marker_sphere")
if tca_sph:
    mat_tca = tca_sph.create_dynamic_material_instance(0, m_solid)
    mat_tca.set_vector_parameter_value("Color", unreal.LinearColor(1.0, 0.82, 0.05, 1.0))
    mat_tca.set_scalar_parameter_value("EmissiveMultiplier", 1.8)
    tca_sph.set_material(0, mat_tca)

deb_sph = conj_viz.get_editor_property("debris_tca_marker_sphere")
if deb_sph:
    mat_deb = deb_sph.create_dynamic_material_instance(0, m_solid)
    mat_deb.set_vector_parameter_value("Color", unreal.LinearColor(1.0, 0.15, 0.1, 1.0))
    mat_deb.set_scalar_parameter_value("EmissiveMultiplier", 1.8)
    deb_sph.set_material(0, mat_deb)

line = conj_viz.get_editor_property("miss_distance_line")
if line:
    mat_line = line.create_dynamic_material_instance(0, m_solid)
    mat_line.set_vector_parameter_value("Color", unreal.LinearColor(1.0, 0.05, 0.70, 1.0))
    mat_line.set_scalar_parameter_value("EmissiveMultiplier", 2.0)
    line.set_material(0, mat_line)

disc = conj_viz.get_editor_property("encounter_plane_disc")
if disc and m_disc:
    mat_disc = disc.create_dynamic_material_instance(0, m_disc)
    mat_disc.set_vector_parameter_value("Color", unreal.LinearColor(0.65, 0.2, 0.95, 1.0))
    mat_disc.set_scalar_parameter_value("Opacity", 0.12)
    disc.set_material(0, mat_disc)

tca_mid = unreal.Vector((sat_tca_pos.x + deb_tca_pos.x) * 0.5, (sat_tca_pos.y + deb_tca_pos.y) * 0.5, (sat_tca_pos.z + deb_tca_pos.z) * 0.5)

# Camera positioned on the Earth side looking OUTWARDS into deep black space
tca_cam_loc = unreal.Vector(tca_mid.x - 120.0, tca_mid.y + 130.0, tca_mid.z + 85.0)
tca_cam_rot = look_at(tca_cam_loc, tca_mid)
# Sun shining from camera side towards target
capture_view("Test_Conjunction_Outward", tca_cam_loc, tca_cam_rot, fov=44.0, sun_rotation=tca_cam_rot, sun_intensity=12.0)

print("Done test_enc_and_tca!")
unreal.SystemLibrary.execute_console_command(None, "QUIT_EDITOR")
