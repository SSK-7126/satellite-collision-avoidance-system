import unreal
import os
import math

level_path = '/Game/Scenarios/CollisionAvoidanceDemo'
unreal.EditorLevelLibrary.load_level(level_path)
world = unreal.EditorLevelLibrary.get_editor_world()

asset_tools = unreal.AssetToolsHelpers.get_asset_tools()
mat_factory = unreal.MaterialFactoryNew()

# 1. Delete and recreate M_SolidColor cleanly
unreal.EditorAssetLibrary.delete_asset('/Game/Common/M_SolidColor')
m_solid = asset_tools.create_asset('M_SolidColor', '/Game/Common', unreal.Material, mat_factory)
m_solid.set_editor_property('two_sided', True)

# Color Parameter
col_param = unreal.MaterialEditingLibrary.create_material_expression(m_solid, unreal.MaterialExpressionVectorParameter, -400, -100)
col_param.set_editor_property('parameter_name', 'Color')
col_param.set_editor_property('default_value', unreal.LinearColor(1.0, 1.0, 1.0, 1.0))
unreal.MaterialEditingLibrary.connect_material_property(col_param, '', unreal.MaterialProperty.MP_BASE_COLOR)

# Emissive connection with multiplier
em_param = unreal.MaterialEditingLibrary.create_material_expression(m_solid, unreal.MaterialExpressionScalarParameter, -400, 100)
em_param.set_editor_property('parameter_name', 'EmissiveMultiplier')
em_param.set_editor_property('default_value', 0.35)

mult_expr = unreal.MaterialEditingLibrary.create_material_expression(m_solid, unreal.MaterialExpressionMultiply, -200, 0)
unreal.MaterialEditingLibrary.connect_material_expressions(col_param, '', mult_expr, 'A')
unreal.MaterialEditingLibrary.connect_material_expressions(em_param, '', mult_expr, 'B')
unreal.MaterialEditingLibrary.connect_material_property(mult_expr, '', unreal.MaterialProperty.MP_EMISSIVE_COLOR)

# Metallic & Roughness
metal_param = unreal.MaterialEditingLibrary.create_material_expression(m_solid, unreal.MaterialExpressionScalarParameter, -400, 250)
metal_param.set_editor_property('parameter_name', 'Metallic')
metal_param.set_editor_property('default_value', 0.8)
unreal.MaterialEditingLibrary.connect_material_property(metal_param, '', unreal.MaterialProperty.MP_METALLIC)

rough_param = unreal.MaterialEditingLibrary.create_material_expression(m_solid, unreal.MaterialExpressionScalarParameter, -400, 400)
rough_param.set_editor_property('parameter_name', 'Roughness')
rough_param.set_editor_property('default_value', 0.2)
unreal.MaterialEditingLibrary.connect_material_property(rough_param, '', unreal.MaterialProperty.MP_ROUGHNESS)

unreal.MaterialEditingLibrary.recompile_material(m_solid)
unreal.EditorAssetLibrary.save_loaded_asset(m_solid)
print('M_SolidColor created and compiled cleanly!')

cube_mesh = unreal.EditorAssetLibrary.load_asset('/Engine/BasicShapes/Cube.Cube')

# Test gold dynamic material instance on cube
target = unreal.Vector(75000.0, 0.0, 0.0)
cube_actor = unreal.EditorLevelLibrary.spawn_actor_from_class(unreal.StaticMeshActor, target)
smc = cube_actor.get_component_by_class(unreal.StaticMeshComponent)
smc.set_static_mesh(cube_mesh)
smc.set_world_scale3d(unreal.Vector(2.0, 2.0, 2.0))

dyn_gold = smc.create_dynamic_material_instance(0, m_solid)
dyn_gold.set_vector_parameter_value('Color', unreal.LinearColor(0.98, 0.82, 0.28, 1.0))
dyn_gold.set_scalar_parameter_value('Metallic', 0.9)
dyn_gold.set_scalar_parameter_value('Roughness', 0.2)
dyn_gold.set_scalar_parameter_value('EmissiveMultiplier', 0.35)

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
unreal.RenderingLibrary.export_render_target(world, rt, out_dir, 'Test_GoldCube.png')

unreal.EditorLevelLibrary.destroy_actor(cap)
unreal.EditorLevelLibrary.destroy_actor(cube_actor)
print('Exported Test_GoldCube.png')

unreal.SystemLibrary.execute_console_command(None, 'QUIT_EDITOR')
