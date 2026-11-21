import unreal
import os
import math

print('=== TEST RED CUBE WITH M_SOLIDCOLOR ===')
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

cube_mesh = unreal.EditorAssetLibrary.load_asset('/Engine/BasicShapes/Cube.Cube')
print('Loaded cube mesh:', cube_mesh)

m_solid = unreal.EditorAssetLibrary.load_asset('/Game/Common/M_SolidColor')
print('Loaded M_SolidColor:', m_solid)

# Spawn test cube at (0, 0, 1000)
cube_actor = unreal.EditorLevelLibrary.spawn_actor_from_class(unreal.StaticMeshActor, unreal.Vector(0.0, 0.0, 1000.0))
smc = cube_actor.get_component_by_class(unreal.StaticMeshComponent)
smc.set_static_mesh(cube_mesh)

dyn_mat = smc.create_dynamic_material_instance(0, m_solid)
print('Created dyn_mat:', dyn_mat)
dyn_mat.set_vector_parameter_value('Color', unreal.LinearColor(1.0, 0.0, 0.0, 1.0))
dyn_mat.set_scalar_parameter_value('EmissiveMultiplier', 0.5)

# Camera at (500, 500, 1300) looking at (0, 0, 1000)
cam_loc = unreal.Vector(500.0, 500.0, 1300.0)
target = unreal.Vector(0.0, 0.0, 1000.0)
dx = target.x - cam_loc.x
dy = target.y - cam_loc.y
dz = target.z - cam_loc.z
yaw = math.degrees(math.atan2(dy, dx))
dist_xy = math.sqrt(dx*dx + dy*dy)
pitch = math.degrees(math.atan2(dz, dist_xy))
cam_rot = unreal.Rotator(pitch=pitch, yaw=yaw, roll=0.0)

# Configure Directional Light to shine directly from camera position towards cube
for a in all_actors:
    if isinstance(a, unreal.DirectionalLight):
        comp = a.get_component_by_class(unreal.DirectionalLightComponent)
        comp.set_editor_property('atmosphere_sun_light', False)
        comp.set_editor_property('use_temperature', False)
        comp.set_editor_property('light_color', unreal.Color(255, 255, 255, 255))
        comp.set_editor_property('intensity', 15.0)
        a.set_actor_rotation(cam_rot, False)
        print(f'Sun rotation set to match camera: pitch={pitch:.1f}, yaw={yaw:.1f}')
    elif isinstance(a, unreal.SkyLight):
        comp = a.get_component_by_class(unreal.SkyLightComponent)
        comp.set_editor_property('real_time_capture', False)
        comp.set_editor_property('intensity', 2.0)
        comp.set_editor_property('light_color', unreal.Color(200, 220, 255, 255))

cap = unreal.EditorLevelLibrary.spawn_actor_from_class(unreal.SceneCapture2D, cam_loc, cam_rot)
comp = cap.get_editor_property('capture_component2d')
comp.set_editor_property('fov_angle', 45.0)
comp.set_editor_property('capture_source', unreal.SceneCaptureSource.SCS_FINAL_COLOR_LDR)
pps = comp.get_editor_property('post_process_settings')
pps.set_editor_property('override_auto_exposure_bias', True)
pps.set_editor_property('auto_exposure_bias', 0.0)
comp.set_editor_property('post_process_settings', pps)

rt = unreal.RenderingLibrary.create_render_target2d(world, 512, 512, unreal.TextureRenderTargetFormat.RTF_RGBA8)
comp.set_editor_property('texture_target', rt)
comp.capture_scene()

out_dir = (unreal.Paths.project_saved_dir() + 'Screenshots/WindowsEditor').replace('\\', '/')
unreal.RenderingLibrary.export_render_target(world, rt, out_dir, 'Test_Red_Cube.png')

unreal.EditorLevelLibrary.destroy_actor(cap)
unreal.EditorLevelLibrary.destroy_actor(cube_actor)
print('Exported Test_Red_Cube.png successfully!')

unreal.SystemLibrary.execute_console_command(None, 'QUIT_EDITOR')
