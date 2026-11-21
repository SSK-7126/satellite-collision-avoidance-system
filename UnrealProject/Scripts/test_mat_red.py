import unreal
import os

print(">>> TEST MAT RED STARTING <<<")

level_path = "/Game/Scenarios/CollisionAvoidanceDemo"
unreal.EditorLevelLibrary.load_level(level_path)
world = unreal.EditorLevelLibrary.get_editor_world()

m_solid = unreal.EditorAssetLibrary.load_asset("/Game/Common/M_SolidColor")
print("M_SolidColor loaded:", m_solid)

# Spawn a test sphere at (0, 0, 500)
sphere_actor = unreal.EditorLevelLibrary.spawn_actor_from_class(unreal.StaticMeshActor, unreal.Vector(0, 0, 500))
smc = sphere_actor.get_component_by_class(unreal.StaticMeshComponent)
basic_sphere = unreal.EditorAssetLibrary.load_asset("/Engine/BasicShapes/Sphere")
smc.set_static_mesh(basic_sphere)

# Create dynamic material instance on the sphere
dyn_mat = smc.create_dynamic_material_instance(0, m_solid)
print("dyn_mat created:", dyn_mat)
if dyn_mat:
    dyn_mat.set_vector_parameter_value("Color", unreal.LinearColor(1.0, 0.0, 0.0, 1.0))
    dyn_mat.set_scalar_parameter_value("EmissiveMultiplier", 1.0)

# Camera looking directly at sphere
cam_pos = unreal.Vector(500, 0, 500)
cam_rot = unreal.Rotator(pitch=0, yaw=180, roll=0)

capture_actor = unreal.EditorLevelLibrary.spawn_actor_from_class(unreal.SceneCapture2D, cam_pos, cam_rot)
comp = capture_actor.get_editor_property("capture_component2d")
comp.set_editor_property("fov_angle", 60.0)
comp.set_editor_property("capture_source", unreal.SceneCaptureSource.SCS_FINAL_COLOR_LDR)

rt = unreal.RenderingLibrary.create_render_target2d(world, 512, 512, unreal.TextureRenderTargetFormat.RTF_RGBA8)
comp.set_editor_property("texture_target", rt)
comp.capture_scene()

out_dir = (unreal.Paths.project_saved_dir() + "Screenshots/WindowsEditor").replace("\\", "/")
unreal.RenderingLibrary.export_render_target(world, rt, out_dir, "Test_Mat_Red.png")

unreal.EditorLevelLibrary.destroy_actor(capture_actor)
unreal.EditorLevelLibrary.destroy_actor(sphere_actor)
print(">>> EXPORTED Test_Mat_Red.png <<<")

unreal.SystemLibrary.execute_console_command(None, "QUIT_EDITOR")
