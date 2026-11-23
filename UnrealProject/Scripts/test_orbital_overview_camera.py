import unreal
import math
import os
import traceback

log_file = os.path.abspath(os.path.join(unreal.Paths.project_saved_dir(), "cam_test.log"))
f_log = open(log_file, "w", encoding="utf-8")

def log(msg):
    print(msg)
    unreal.log(msg)
    f_log.write(str(msg) + "\n")
    f_log.flush()

try:
    log("=== TEST ORBITAL OVERVIEW CAMERA ===")
    out_dir = (unreal.Paths.project_saved_dir() + "Screenshots/WindowsEditor/VisualDesign").replace("\\", "/")
    os.makedirs(out_dir, exist_ok=True)

    level_path = "/Game/Scenarios/CollisionAvoidanceDemo"
    log(f"Loading level: {level_path}")
    unreal.EditorLevelLibrary.load_level(level_path)

    world = unreal.EditorLevelLibrary.get_editor_world()
    actors = unreal.EditorLevelLibrary.get_all_level_actors()
    log(f"Actors found: {len(actors)}")

    sat = None
    deb = None
    earth = None
    sim = None
    cam_overview = None
    sat_nom_path = None
    deb_path = None
    sat_mod_path = None
    conj_vis = None
    man_vis = None
    sun = None

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
        elif lbl == "Camera_Earth_Overview":
            cam_overview = a
        elif lbl == "OrbitPath_SatelliteNominal":
            sat_nom_path = a
        elif lbl == "OrbitPath_DebrisNominal":
            deb_path = a
        elif lbl == "OrbitPath_SatelliteModified":
            sat_mod_path = a
        elif isinstance(a, unreal.ConjunctionVisualizer):
            conj_vis = a
        elif isinstance(a, unreal.ManoeuvreVisualizer):
            man_vis = a
        elif isinstance(a, unreal.DirectionalLight):
            sun = a

    log(f"Actors: sat={sat is not None}, deb={deb is not None}, earth={earth is not None}, sim={sim is not None}")

    # Set Step 6 (T=169.6s - Burn Point)
    if sim:
        sim.jump_to_step(6)
        log(f"Simulation jumped to Step 6 (T={sim.get_editor_property('current_simulation_time')})")

    # Target point: Near Earth center, slightly offset towards encounter region
    target_point = unreal.Vector(5000.0, -10000.0, 0.0)

    def look_at(cam_pos, tgt):
        dx = tgt.x - cam_pos.x
        dy = tgt.y - cam_pos.y
        dz = tgt.z - cam_pos.z
        yaw = math.degrees(math.atan2(dy, dx))
        pitch = math.degrees(math.atan2(dz, math.sqrt(dx*dx + dy*dy)))
        return unreal.Rotator(pitch=pitch, yaw=yaw, roll=0.0)

    def capture(tag, cam_pos, fov=44.0):
        cam_rot = look_at(cam_pos, target_point)
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

        png = f"{tag}.png"
        unreal.RenderingLibrary.export_render_target(world, rt, out_dir, png)
        unreal.EditorLevelLibrary.destroy_actor(cap)
        log(f"Exported {tag} from {cam_pos}")

    # Test 3 Elevated Vantage Points
    capture("Orbital_Vantage_A", unreal.Vector(25000.0, -210000.0, 165000.0), fov=42.0)
    capture("Orbital_Vantage_B", unreal.Vector(20000.0, -195000.0, 190000.0), fov=40.0)
    capture("Orbital_Vantage_C", unreal.Vector(35000.0, -225000.0, 150000.0), fov=45.0)

    log("SUCCESS: All captures completed!")
except Exception as e:
    log(f"ERROR: {e}\n{traceback.format_exc()}")
finally:
    f_log.close()
