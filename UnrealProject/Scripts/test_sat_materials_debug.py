import unreal
import os

unreal.EditorLevelLibrary.load_level("/Game/Scenarios/CollisionAvoidanceDemo")
world = unreal.EditorLevelLibrary.get_editor_world()
all_actors = unreal.EditorLevelLibrary.get_all_level_actors()

sat = [a for a in all_actors if isinstance(a, unreal.SatelliteActor)][0]
body = sat.get_editor_property("satellite_body")
print("SatelliteActor:", sat.get_name())
print("Before material:", body.get_material(0))

m_solid = unreal.EditorAssetLibrary.load_asset("/Game/Common/M_SolidColor")
print("Loaded M_SolidColor:", m_solid)

mat_gold = body.create_dynamic_material_instance(0, m_solid)
print("Created MID:", mat_gold)
mat_gold.set_vector_parameter_value("Color", unreal.LinearColor(0.98, 0.82, 0.28, 1.0))
mat_gold.set_scalar_parameter_value("Metallic", 0.9)
mat_gold.set_scalar_parameter_value("Roughness", 0.2)
mat_gold.set_scalar_parameter_value("EmissiveMultiplier", 0.5)
body.set_material(0, mat_gold)
print("After set_material:", body.get_material(0))

# Spawn camera close to satellite at (70000, 0, 0)
cam_loc = unreal.Vector(70000.0 + 500.0, -500.0, 300.0)
cam_rot = unreal.Rotator(roll=0.0, pitch=-25.0, yaw=135.0)

# Sunlight matching camera
dl = [a for a in all_actors if isinstance(a, unreal.DirectionalLight)][0]
dl.set_actor_rotation(cam_rot, False)
dl_comp = dl.get_component_by_class(unreal.DirectionalLightComponent)
dl_comp.set_editor_property("intensity", 15.0)

capture_actor = unreal.EditorLevelLibrary.spawn_actor_from_class(unreal.SceneCapture2D, cam_loc, cam_rot)
comp = capture_actor.get_editor_property("capture_component2d")
comp.set_editor_property("fov_angle", 45.0)
comp.set_editor_property("capture_source", unreal.SceneCaptureSource.SCS_FINAL_COLOR_LDR)

rt = unreal.RenderingLibrary.create_render_target2d(world, 1280, 720, unreal.TextureRenderTargetFormat.RTF_RGBA8)
comp.set_editor_property("texture_target", rt)
comp.capture_scene()

out_dir = (unreal.Paths.project_saved_dir() + "Screenshots/WindowsEditor").replace("\\", "/")
unreal.RenderingLibrary.export_render_target(world, rt, out_dir, "Test_Sat_Debug.png")
unreal.EditorLevelLibrary.destroy_actor(capture_actor)
print("Saved Test_Sat_Debug.png")

unreal.SystemLibrary.execute_console_command(None, "QUIT_EDITOR")
