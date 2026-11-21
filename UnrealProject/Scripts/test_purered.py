import unreal
import os
import math

level_path = '/Game/Scenarios/CollisionAvoidanceDemo'
unreal.EditorLevelLibrary.load_level(level_path)
world = unreal.EditorLevelLibrary.get_editor_world()

asset_tools = unreal.AssetToolsHelpers.get_asset_tools()
mat_factory = unreal.MaterialFactoryNew()

# Create M_PureRed
m_red = asset_tools.create_asset('M_PureRed', '/Game/Common', unreal.Material, mat_factory)
param = unreal.MaterialEditingLibrary.create_material_expression(m_red, unreal.MaterialExpressionVectorParameter, -200, 0)
param.set_editor_property('parameter_name', 'Color')
param.set_editor_property('default_value', unreal.LinearColor(1.0, 0.0, 0.0, 1.0))
unreal.MaterialEditingLibrary.connect_material_property(param, '', unreal.MaterialProperty.MP_BASE_COLOR)
unreal.MaterialEditingLibrary.recompile_material(m_red)
unreal.EditorAssetLibrary.save_loaded_asset(m_red)

cube_mesh = unreal.EditorAssetLibrary.load_asset('/Engine/BasicShapes/Cube.Cube')

target = unreal.Vector(75000.0, 0.0, 0.0)
cube_actor = unreal.EditorLevelLibrary.spawn_actor_from_class(unreal.StaticMeshActor, target)
smc = cube_actor.get_component_by_class(unreal.StaticMeshComponent)
smc.set_static_mesh(cube_mesh)
smc.set_world_scale3d(unreal.Vector(2.0, 2.0, 2.0))
smc.set_material(0, m_red)

# Camera
cam_loc = unreal.Vector(75500.0, -500.0, 300.0)
dx = target.x - cam_loc.x
dy = target.y - cam_loc.y
dz = target.z - cam_loc.z
yaw = math.degrees(math.atan2(dy, dx))
dist_xy = math.sqrt(dx*dx + dy*dy)
pitch = math.degrees(math.atan2(dz, dist_xy))
cam_rot = unreal.Rotator(pitch=pitch, yaw=yaw, roll=0.0)

all_actors = unreal.EditorLevelLibrary.get_all_level_actors()
for a in all_actors:
    if isinstance(a, unreal.DirectionalLight):
        comp = a.get_component_by_class(unreal.DirectionalLightComponent)
        comp.set_editor_property('atmosphere_sun_light', False)
        comp.set_editor_property('use_temperature', False)
        comp.set_editor_property('light_color', unreal.Color(255, 255, 255, 255))
        comp.set_editor_property('intensity', 15.0)
        a.set_actor_rotation(cam_rot, False)

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
unreal.RenderingLibrary.export_render_target(world, rt, out_dir, 'Test_PureRed.png')

unreal.EditorLevelLibrary.destroy_actor(cap)
unreal.EditorLevelLibrary.destroy_actor(cube_actor)
unreal.EditorAssetLibrary.delete_asset('/Game/Common/M_PureRed')
print('Exported Test_PureRed.png')

unreal.SystemLibrary.execute_console_command(None, 'QUIT_EDITOR')
