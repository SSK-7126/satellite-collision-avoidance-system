"""
render_orbital_perspective_raw.py
=================================
Renders the 3D orbital scene from the elevated perspective camera inside Unreal Engine 5.7:
- Earth centered in orbital plane
- Radius 70,000 uu orbital paths
- Satellite and debris in upper encounter arc
- Clean 1080p output saved directly to an absolute path
"""

import unreal
import math
import os
import traceback

def run():
    screenshot_dir = os.path.abspath(os.path.join(unreal.Paths.project_saved_dir(), "Screenshots/WindowsEditor/VisualDesign"))
    os.makedirs(screenshot_dir, exist_ok=True)

    level_path = "/Game/Scenarios/CollisionAvoidanceDemo"
    unreal.EditorLevelLibrary.load_level(level_path)

    world = unreal.EditorLevelLibrary.get_editor_world()
    actors = unreal.EditorLevelLibrary.get_all_level_actors()

    sat = None
    deb = None
    earth = None
    sim = None
    sun = None
    sat_nom_path = None
    deb_path = None
    sat_mod_path = None

    for a in actors:
        lbl = a.get_actor_label()
        cname = a.get_class().get_name()
        if lbl == "SM_SkySphere" or cname in ["SkyAtmosphere", "ExponentialHeightFog", "VolumetricCloud"]:
            a.set_actor_hidden_in_game(True)
        elif isinstance(a, unreal.SatelliteActor):
            sat = a
        elif isinstance(a, unreal.DebrisActor):
            deb = a
        elif isinstance(a, unreal.OrbitSimulationManager):
            sim = a
        elif "Earth" in lbl:
            earth = a
        elif isinstance(a, unreal.DirectionalLight):
            sun = a
        elif lbl == "OrbitPath_SatelliteNominal":
            sat_nom_path = a
        elif lbl == "OrbitPath_DebrisNominal":
            deb_path = a
        elif lbl == "OrbitPath_SatelliteModified":
            sat_mod_path = a

    # Earth
    if earth:
        earth.set_actor_location(unreal.Vector(0.0, 0.0, 0.0), False, False)
        earth.set_actor_scale3d(unreal.Vector(1.0, 1.0, 1.0))

    # Sun
    if sun:
        sun.set_actor_rotation(unreal.Rotator(pitch=-32.0, yaw=140.0, roll=0.0), False)
        comp = sun.get_component_by_class(unreal.DirectionalLightComponent)
        if comp:
            comp.set_editor_property("intensity", 16.0)

    # Path visibility
    if sat_nom_path:
        sat_nom_path.set_actor_hidden_in_game(False)
    if deb_path:
        deb_path.set_actor_hidden_in_game(False)
    if sat_mod_path:
        sat_mod_path.set_actor_hidden_in_game(False)

    # Jump to Step 6 (T=169.6s) to show burn and modified trajectory
    if sim:
        sim.jump_to_step(6)

    # Visual scale for satellite and debris
    if sat:
        sat.set_actor_scale3d(unreal.Vector(3.5, 3.5, 3.5))
    if deb:
        deb.set_actor_scale3d(unreal.Vector(4.0, 4.0, 4.0))

    # Camera framing
    cam_pos = unreal.Vector(38000.0, -185000.0, 145000.0)
    tgt_pos = unreal.Vector(5000.0, -15000.0, 0.0)

    dx = tgt_pos.x - cam_pos.x
    dy = tgt_pos.y - cam_pos.y
    dz = tgt_pos.z - cam_pos.z
    yaw = math.degrees(math.atan2(dy, dx))
    pitch = math.degrees(math.atan2(dz, math.sqrt(dx*dx + dy*dy)))
    cam_rot = unreal.Rotator(pitch=pitch, yaw=yaw, roll=0.0)

    cap = unreal.EditorLevelLibrary.spawn_actor_from_class(unreal.SceneCapture2D, cam_pos, cam_rot)
    comp = cap.get_editor_property("capture_component2d")
    comp.set_editor_property("fov_angle", 42.0)
    comp.set_editor_property("capture_source", unreal.SceneCaptureSource.SCS_FINAL_COLOR_LDR)

    pps = comp.get_editor_property("post_process_settings")
    pps.set_editor_property("override_auto_exposure_bias", True)
    pps.set_editor_property("auto_exposure_bias", 0.0)
    comp.set_editor_property("post_process_settings", pps)

    rt = unreal.RenderingLibrary.create_render_target2d(world, 1920, 1080, unreal.TextureRenderTargetFormat.RTF_RGBA8)
    comp.set_editor_property("texture_target", rt)
    comp.capture_scene()

    png_name = "Raw_Orbital_Perspective_Step6.png"
    unreal.RenderingLibrary.export_render_target(world, rt, screenshot_dir, png_name)
    unreal.EditorLevelLibrary.destroy_actor(cap)

    print(f"EXPORT_COMPLETE: {screenshot_dir}/{png_name}")

try:
    run()
except Exception as e:
    print(f"ERROR: {e}")
    traceback.print_exc()
