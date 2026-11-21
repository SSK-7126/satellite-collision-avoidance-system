import unreal
import os

print('=== TEST RENDER SPHERE MATS ===')
level_path = '/Game/Scenarios/CollisionAvoidanceDemo'
unreal.EditorLevelLibrary.load_level(level_path)
world = unreal.EditorLevelLibrary.get_editor_world()
all_actors = unreal.EditorLevelLibrary.get_all_level_actors()

# Clean up landscape
for a in list(all_actors):
    cname = a.get_class().get_name()
    if 'Landscape' in cname or cname in ['VolumetricCloud', 'ExponentialHeightFog']:
        a.set_actor_hidden_in_game(True)
    elif a.get_actor_label() == 'SM_SkySphere':
        a.set_actor_hidden_in_game(True)

# Find & configure lights
for a in all_actors:
    if isinstance(a, unreal.DirectionalLight):
        comp = a.get_component_by_class(unreal.DirectionalLightComponent)
        comp.set_editor_property('atmosphere_sun_light', False)
        comp.set_editor_property('use_temperature', False)
        comp.set_editor_property('light_color', unreal.Color(255, 255, 255, 255))
        comp.set_editor_property('intensity', 15.0)
        a.set_actor_rotation(unreal.Rotator(pitch=-35.0, yaw=-60.0, roll=0.0), False)
        print('Configured DirectionalLight: pure white, no atmosphere sun light, pitch=-35, yaw=-60')
    elif isinstance(a, unreal.SkyLight):
        comp = a.get_component_by_class(unreal.SkyLightComponent)
        comp.set_editor_property('real_time_capture', False)
        comp.set_editor_property('intensity', 2.0)
        comp.set_editor_property('light_color', unreal.Color(200, 220, 255, 255))

m_solid = unreal.EditorAssetLibrary.load_asset('/Game/Common/M_SolidColor')
basic_sphere = unreal.EditorAssetLibrary.load_asset('/Engine/BasicShapes/Sphere')

# Spawn Gold Sphere at (70000, -200, 0)
s1 = unreal.EditorLevelLibrary.spawn_actor_from_class(unreal.StaticMeshActor, unreal.Vector(70000.0, -200.0, 0.0))
smc1 = s1.get_component_by_class(unreal.StaticMeshComponent)
smc1.set_static_mesh(basic_sphere)
d1 = smc1.create_dynamic_material_instance(0, m_solid)
d1.set_vector_parameter_value('Color', unreal.LinearColor(0.98, 0.82, 0.28, 1.0))
d1.set_scalar_parameter_value('Metallic', 0.9)
d1.set_scalar_parameter_value('Roughness', 0.2)
d1.set_scalar_parameter_value('EmissiveMultiplier', 0.35)

# Spawn Blue Sphere at (70000, 200, 0)
s2 = unreal.EditorLevelLibrary.spawn_actor_from_class(unreal.StaticMeshActor, unreal.Vector(70000.0, 200.0, 0.0))
smc2 = s2.get_component_by_class(unreal.StaticMeshComponent)
smc2.set_static_mesh(basic_sphere)
d2 = smc2.create_dynamic_material_instance(0, m_solid)
d2.set_vector_parameter_value('Color', unreal.LinearColor(0.015, 0.08, 0.55, 1.0))
d2.set_scalar_parameter_value('Metallic', 0.85)
d2.set_scalar_parameter_value('Roughness', 0.15)
d2.set_scalar_parameter_value('EmissiveMultiplier', 0.25)

cam_loc = unreal.Vector(70000.0 + 800.0, -800.0, 400.0)
import math
dx = 70000.0 - cam_loc.x
dy = 0.0 - cam_loc.y
dz = 0.0 - cam_loc.z
yaw = math.degrees(math.atan2(dy, dx))
dist_xy = math.sqrt(dx*dx + dy*dy)
pitch = math.degrees(math.atan2(dz, dist_xy))
cam_rot = unreal.Rotator(pitch=pitch, yaw=yaw, roll=0.0)

cap = unreal.EditorLevelLibrary.spawn_actor_from_class(unreal.SceneCapture2D, cam_loc, cam_rot)
comp = cap.get_editor_property('capture_component2d')
comp.set_editor_property('fov_angle', 50.0)
comp.set_editor_property('capture_source', unreal.SceneCaptureSource.SCS_FINAL_COLOR_LDR)
pps = comp.get_editor_property('post_process_settings')
pps.set_editor_property('override_auto_exposure_bias', True)
pps.set_editor_property('auto_exposure_bias', 0.0)
comp.set_editor_property('post_process_settings', pps)

rt = unreal.RenderingLibrary.create_render_target2d(world, 1280, 720, unreal.TextureRenderTargetFormat.RTF_RGBA8)
comp.set_editor_property('texture_target', rt)
comp.capture_scene()

out_dir = (unreal.Paths.project_saved_dir() + 'Screenshots/WindowsEditor').replace('\\', '/')
unreal.RenderingLibrary.export_render_target(world, rt, out_dir, 'Test_Sphere_Mats.png')

unreal.EditorLevelLibrary.destroy_actor(cap)
unreal.EditorLevelLibrary.destroy_actor(s1)
unreal.EditorLevelLibrary.destroy_actor(s2)
print('Exported Test_Sphere_Mats.png')
print('=== DONE ===')

unreal.SystemLibrary.execute_console_command(None, 'QUIT_EDITOR')
