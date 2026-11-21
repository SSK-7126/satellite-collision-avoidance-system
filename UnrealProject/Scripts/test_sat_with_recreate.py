import unreal
import os
import math

level_path = '/Game/Scenarios/CollisionAvoidanceDemo'
unreal.EditorLevelLibrary.load_level(level_path)
world = unreal.EditorLevelLibrary.get_editor_world()
all_actors = unreal.EditorLevelLibrary.get_all_level_actors()

# 1. Hide unwanted actors
for a in all_actors:
    cname = a.get_class().get_name()
    if 'Landscape' in cname or cname in ['VolumetricCloud', 'ExponentialHeightFog', 'SkyAtmosphere']:
        a.set_actor_hidden_in_game(True)
    elif a.get_actor_label() == 'SM_SkySphere':
        a.set_actor_hidden_in_game(True)

# 2. Find Actors
sat = [a for a in all_actors if isinstance(a, unreal.SatelliteActor)][0]
deb = [a for a in all_actors if isinstance(a, unreal.DebrisActor)][0]
dir_light = [a for a in all_actors if isinstance(a, unreal.DirectionalLight)][0]
sky_light = [a for a in all_actors if isinstance(a, unreal.SkyLight)][0]

# Setup DirectionalLight
dl_comp = dir_light.get_component_by_class(unreal.DirectionalLightComponent)
dl_comp.set_editor_property('atmosphere_sun_light', False)
dl_comp.set_editor_property('use_temperature', False)
dl_comp.set_editor_property('light_color', unreal.Color(255, 255, 255, 255))
dl_comp.set_editor_property('intensity', 15.0)

# Setup SkyLight
sl_comp = sky_light.get_component_by_class(unreal.SkyLightComponent)
sl_comp.set_editor_property('real_time_capture', False)
sl_comp.set_editor_property('light_color', unreal.Color(200, 220, 255, 255))
sl_comp.set_editor_property('intensity', 3.0)

# RECREATE M_SolidColor in memory and compile it!
asset_tools = unreal.AssetToolsHelpers.get_asset_tools()
mat_factory = unreal.MaterialFactoryNew()
unreal.EditorAssetLibrary.delete_asset('/Game/Common/M_SolidColor')
m_solid = asset_tools.create_asset('M_SolidColor', '/Game/Common', unreal.Material, mat_factory)
m_solid.set_editor_property('two_sided', True)

col_param = unreal.MaterialEditingLibrary.create_material_expression(m_solid, unreal.MaterialExpressionVectorParameter, -400, -100)
col_param.set_editor_property('parameter_name', 'Color')
col_param.set_editor_property('default_value', unreal.LinearColor(1.0, 1.0, 1.0, 1.0))
unreal.MaterialEditingLibrary.connect_material_property(col_param, '', unreal.MaterialProperty.MP_BASE_COLOR)

em_param = unreal.MaterialEditingLibrary.create_material_expression(m_solid, unreal.MaterialExpressionScalarParameter, -400, 100)
em_param.set_editor_property('parameter_name', 'EmissiveMultiplier')
em_param.set_editor_property('default_value', 0.35)

mult_expr = unreal.MaterialEditingLibrary.create_material_expression(m_solid, unreal.MaterialExpressionMultiply, -200, 0)
unreal.MaterialEditingLibrary.connect_material_expressions(col_param, '', mult_expr, 'A')
unreal.MaterialEditingLibrary.connect_material_expressions(em_param, '', mult_expr, 'B')
unreal.MaterialEditingLibrary.connect_material_property(mult_expr, '', unreal.MaterialProperty.MP_EMISSIVE_COLOR)

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
print('Fresh M_SolidColor created and recompiled!')

# Hide debris while photographing satellite
deb.set_actor_hidden_in_game(True)
sat.set_actor_hidden_in_game(False)

sat_pos = unreal.Vector(70000.0, 0.0, 0.0)
sat.set_actor_location_and_rotation(sat_pos, unreal.Rotator(0.0, -90.0, 0.0), False, False)

# 1. Golden Central Bus
body = sat.get_editor_property('satellite_body')
mat_gold = body.create_dynamic_material_instance(0, m_solid)
mat_gold.set_vector_parameter_value('Color', unreal.LinearColor(0.98, 0.82, 0.28, 1.0))
mat_gold.set_scalar_parameter_value('Metallic', 0.9)
mat_gold.set_scalar_parameter_value('Roughness', 0.2)
mat_gold.set_scalar_parameter_value('EmissiveMultiplier', 0.4)
body.set_material(0, mat_gold)

# 2. Photovoltaic Solar Panels (Deep Blue)
for p_name in ['solar_panel_left', 'solar_panel_left_outboard', 'solar_panel_right', 'solar_panel_right_outboard']:
    p_comp = sat.get_editor_property(p_name)
    if p_comp:
        mat_blue = p_comp.create_dynamic_material_instance(0, m_solid)
        mat_blue.set_vector_parameter_value('Color', unreal.LinearColor(0.015, 0.08, 0.55, 1.0))
        mat_blue.set_scalar_parameter_value('Metallic', 0.85)
        mat_blue.set_scalar_parameter_value('Roughness', 0.15)
        mat_blue.set_scalar_parameter_value('EmissiveMultiplier', 0.35)
        p_comp.set_material(0, mat_blue)

# 3. Structural Silver
for m_name in ['payload_deck', 'solar_yoke_left', 'solar_yoke_right', 'antenna_mast', 'thruster_nozzle']:
    m_comp = sat.get_editor_property(m_name)
    if m_comp:
        mat_silver = m_comp.create_dynamic_material_instance(0, m_solid)
        mat_silver.set_vector_parameter_value('Color', unreal.LinearColor(0.78, 0.82, 0.86, 1.0))
        mat_silver.set_scalar_parameter_value('Metallic', 0.9)
        mat_silver.set_scalar_parameter_value('Roughness', 0.25)
        mat_silver.set_scalar_parameter_value('EmissiveMultiplier', 0.25)
        m_comp.set_material(0, mat_silver)

# 4. Antenna Dish (Gold Reflector)
dish = sat.get_editor_property('antenna_dish')
if dish:
    mat_dish = dish.create_dynamic_material_instance(0, m_solid)
    mat_dish.set_vector_parameter_value('Color', unreal.LinearColor(0.95, 0.88, 0.55, 1.0))
    mat_dish.set_scalar_parameter_value('Metallic', 0.95)
    mat_dish.set_scalar_parameter_value('Roughness', 0.2)
    mat_dish.set_scalar_parameter_value('EmissiveMultiplier', 0.4)
    dish.set_material(0, mat_dish)

# 5. Earth Sensor (Dark Optics)
sensor = sat.get_editor_property('earth_sensor')
if sensor:
    mat_sensor = sensor.create_dynamic_material_instance(0, m_solid)
    mat_sensor.set_vector_parameter_value('Color', unreal.LinearColor(0.02, 0.03, 0.05, 1.0))
    mat_sensor.set_scalar_parameter_value('Metallic', 0.1)
    mat_sensor.set_scalar_parameter_value('Roughness', 0.1)
    mat_sensor.set_scalar_parameter_value('EmissiveMultiplier', 0.1)
    sensor.set_material(0, mat_sensor)

print('Satellite materials configured.')

# Camera position: framed to view entire 11.6m wingspan
cam_loc = unreal.Vector(sat_pos.x + 1200.0, sat_pos.y - 1200.0, sat_pos.z + 600.0)
dx = sat_pos.x - cam_loc.x
dy = sat_pos.y - cam_loc.y
dz = sat_pos.z - cam_loc.z
yaw = math.degrees(math.atan2(dy, dx))
dist_xy = math.sqrt(dx*dx + dy*dy)
pitch = math.degrees(math.atan2(dz, dist_xy))
cam_rot = unreal.Rotator(pitch=pitch, yaw=yaw, roll=0.0)

# Set sun to illuminate the spacecraft directly from camera perspective
dir_light.set_actor_rotation(cam_rot, False)

# Capture 1920x1080 screenshot
out_dir = (unreal.Paths.project_saved_dir() + 'Screenshots/WindowsEditor').replace('\\', '/')
os.makedirs(out_dir, exist_ok=True)

cap = unreal.EditorLevelLibrary.spawn_actor_from_class(unreal.SceneCapture2D, cam_loc, cam_rot)
comp = cap.get_editor_property('capture_component2d')
comp.set_editor_property('fov_angle', 45.0)
comp.set_editor_property('capture_source', unreal.SceneCaptureSource.SCS_FINAL_COLOR_LDR)
pps = comp.get_editor_property('post_process_settings')
pps.set_editor_property('override_auto_exposure_bias', True)
pps.set_editor_property('auto_exposure_bias', 0.0)
comp.set_editor_property('post_process_settings', pps)

rt = unreal.RenderingLibrary.create_render_target2d(world, 1920, 1080, unreal.TextureRenderTargetFormat.RTF_RGBA8)
comp.set_editor_property('texture_target', rt)
comp.capture_scene()

unreal.RenderingLibrary.export_render_target(world, rt, out_dir, 'Test_Sat_Recreated.png')
unreal.EditorLevelLibrary.destroy_actor(cap)
print(f'Exported {out_dir}/Test_Sat_Recreated.png')

unreal.SystemLibrary.execute_console_command(None, 'QUIT_EDITOR')
