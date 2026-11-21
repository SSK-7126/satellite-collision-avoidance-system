import unreal

level_path = '/Game/Scenarios/CollisionAvoidanceDemo'
unreal.EditorLevelLibrary.load_level(level_path)
world = unreal.EditorLevelLibrary.get_editor_world()

actors = unreal.EditorLevelLibrary.get_all_level_actors()
sat = [a for a in actors if isinstance(a, unreal.SatelliteActor)][0]
body = sat.get_editor_property('satellite_body')
m_solid = unreal.EditorAssetLibrary.load_asset('/Game/Common/M_SolidColor')

print('Before body material:', body.get_material(0))

dyn = body.create_dynamic_material_instance(0, m_solid)
print('Created dyn:', dyn)
print('After body material:', body.get_material(0))
print('Dyn parent:', dyn.get_editor_property('parent'))
print('Dyn vector params:', unreal.MaterialEditingLibrary.get_vector_parameter_names(dyn))

unreal.SystemLibrary.execute_console_command(None, 'QUIT_EDITOR')
