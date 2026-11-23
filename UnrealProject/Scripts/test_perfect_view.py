import unreal
import math
import os
import shutil

log_file = os.path.abspath(os.path.join(unreal.Paths.project_saved_dir(), "view_test.log"))
f_log = open(log_file, "w", encoding="utf-8")

def log(msg):
    print(msg)
    unreal.log(msg)
    f_log.write(str(msg) + "\n")
    f_log.flush()

try:
    log("=== TEST PERFECT ORBITAL VIEW ===")
    out_dir = (unreal.Paths.project_saved_dir() + "Screenshots/WindowsEditor/VisualDesign").replace("\\", "/")
    os.makedirs(out_dir, exist_ok=True)

    world = unreal.EditorLevelLibrary.get_editor_world()
    actors = unreal.EditorLevelLibrary.get_all_level_actors()

    sat = None
    deb = None
    earth = None
    sim = None
    conj = None
    man = None
    sat_nom = None
    deb_nom = None
    sat_mod = None

    for a in actors:
        lbl = a.get_actor_label()
        if isinstance(a, unreal.SatelliteActor):
            sat = a
        elif isinstance(a, unreal.DebrisActor):
            deb = a
        elif isinstance(a, unreal.EarthActor):
            earth = a
        elif isinstance(a, unreal.OrbitSimulationManager):
            sim = a
        elif isinstance(a, unreal.ConjunctionVisualizer):
            conj = a
        elif isinstance(a, unreal.ManoeuvreVisualizer):
            man = a
        elif lbl == "OrbitPath_SatelliteNominal":
            sat_nom = a
        elif lbl == "OrbitPath_DebrisNominal":
            deb_nom = a
        elif lbl == "OrbitPath_SatelliteModified":
            sat_mod = a

    # Jump to Step 6 (T=169.6s) so burn and modified orbit are active
    if sim:
        sim.jump_to_step(6)
        log("Jumped to Step 6")

    # Scale up satellite and debris models so their 3D shapes are clearly visible at orbital distance
    if sat:
        sat.set_actor_scale3d(unreal.Vector(18.0, 18.0, 18.0))
        sat.set_actor_hidden_in_game(False)
        log(f"Satellite pos: {sat.get_actor_location()}")
    if deb:
        deb.set_actor_scale3d(unreal.Vector(20.0, 20.0, 20.0))
        deb.set_actor_hidden_in_game(False)
        log(f"Debris pos: {deb.get_actor_location()}")

    # Increase path thickness and rebuild geometry
    for path, thick, color in [
        (sat_nom, 280.0, unreal.LinearColor(0.0, 0.85, 1.0, 1.0)),     # Cyan solid
        (deb_nom, 280.0, unreal.LinearColor(1.0, 0.55, 0.05, 1.0)),    # Orange dashed
        (sat_mod, 280.0, unreal.LinearColor(0.15, 1.0, 0.35, 1.0)),    # Green dashed
    ]:
        if path:
            path.set_editor_property("PathThickness", thick)
            path.set_editor_property("PathColor", color)
            path.set_actor_hidden_in_game(False)
            # path.build_spline_mesh_geometry()
            log(f"Rebuilt path: {path.get_actor_label()} with thickness {thick}")

    if conj:
        conj.set_actor_scale3d(unreal.Vector(12.0, 12.0, 12.0))
        conj.set_actor_hidden_in_game(False)
    if man:
        man.set_actor_scale3d(unreal.Vector(12.0, 12.0, 12.0))
        man.set_actor_hidden_in_game(False)

    # Setup Elevated Camera
    tgt = unreal.Vector(15000.0, -25000.0, 0.0)
    cam_pos = unreal.Vector(50000.0, -480000.0, 330000.0)

    dx = tgt.x - cam_pos.x
    dy = tgt.y - cam_pos.y
    dz = tgt.z - cam_pos.z
    yaw = math.degrees(math.atan2(dy, dx))
    pitch = math.degrees(math.atan2(dz, math.sqrt(dx*dx + dy*dy)))
    cam_rot = unreal.Rotator(pitch=pitch, yaw=yaw, roll=0.0)

    cap = unreal.EditorLevelLibrary.spawn_actor_from_class(unreal.SceneCapture2D, cam_pos, cam_rot)
    comp = cap.get_editor_property("capture_component2d")
    comp.set_editor_property("fov_angle", 52.0)
    comp.set_editor_property("capture_source", unreal.SceneCaptureSource.SCS_FINAL_COLOR_LDR)

    pps = comp.get_editor_property("post_process_settings")
    pps.set_editor_property("override_auto_exposure_bias", True)
    pps.set_editor_property("auto_exposure_bias", 0.0)
    comp.set_editor_property("post_process_settings", pps)

    rt = unreal.RenderingLibrary.create_render_target2d(world, 1920, 1080, unreal.TextureRenderTargetFormat.RTF_RGBA8)
    comp.set_editor_property("texture_target", rt)
    comp.capture_scene()

    png = "Perfect_Orbital_View_Test.png"
    unreal.RenderingLibrary.export_render_target(world, rt, out_dir, png)
    unreal.EditorLevelLibrary.destroy_actor(cap)
    log(f"Exported {png} successfully!")

except Exception as e:
    import traceback
    log(f"ERROR: {e}\n{traceback.format_exc()}")
finally:
    f_log.close()
