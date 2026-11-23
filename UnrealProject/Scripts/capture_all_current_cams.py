import unreal
import os
import traceback

out_dir = (unreal.Paths.project_saved_dir() + "Screenshots/WindowsEditor/CurrentCams").replace("\\", "/")
os.makedirs(out_dir, exist_ok=True)

world = unreal.EditorLevelLibrary.get_editor_world()
actors = unreal.EditorLevelLibrary.get_all_level_actors()

cam_actors = {}
for a in actors:
    lbl = a.get_actor_label()
    if isinstance(a, unreal.CameraActor):
        cam_actors[lbl] = a

print(f"Found {len(cam_actors)} cameras.")

for name, cam in cam_actors.items():
    try:
        loc = cam.get_actor_location()
        rot = cam.get_actor_rotation()
        cam_comp = cam.get_component_by_class(unreal.CameraComponent)
        fov = cam_comp.get_editor_property("field_of_view") if cam_comp else 60.0
        print(f"Camera {name}: loc=({loc.x:.1f}, {loc.y:.1f}, {loc.z:.1f}), rot=({rot.pitch:.2f}, {rot.yaw:.2f}, {rot.roll:.2f}), fov={fov:.1f}")

        capture_actor = unreal.EditorLevelLibrary.spawn_actor_from_class(unreal.SceneCapture2D, loc, rot)
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

        png_name = f"{name}.png"
        unreal.RenderingLibrary.export_render_target(world, rt, out_dir, png_name)
        unreal.EditorLevelLibrary.destroy_actor(capture_actor)
        print(f"  [SAVED] {out_dir}/{png_name}")
    except Exception as e:
        print(f"Error on {name}: {e}")
        traceback.print_exc()

print("ALL_CURRENT_CAMS_CAPTURED")
