import unreal

level_path = '/Game/Scenarios/CollisionAvoidanceDemo'
unreal.EditorLevelLibrary.load_level(level_path)
world = unreal.EditorLevelLibrary.get_editor_world()

m_solid = unreal.EditorAssetLibrary.load_asset('/Game/Common/M_SolidColor')
print('=== M_SOLIDCOLOR PARAMETERS ===')
print('Vector params:', unreal.MaterialEditingLibrary.get_vector_parameter_names(m_solid))
print('Scalar params:', unreal.MaterialEditingLibrary.get_scalar_parameter_names(m_solid))

actors = unreal.EditorLevelLibrary.get_all_level_actors()
sat = [a for a in actors if isinstance(a, unreal.SatelliteActor)][0]
body = sat.get_editor_property('satellite_body')
mat = body.get_material(0)
print('Satellite body material:', mat)
if mat:
    print('  Material class:', mat.get_class().get_name())
    if isinstance(mat, unreal.MaterialInstanceDynamic):
        print('  MID Parent:', mat.get_editor_property('parent'))
        print('  MID Vector params:', unreal.MaterialEditingLibrary.get_vector_parameter_names(mat))
        for v in unreal.MaterialEditingLibrary.get_vector_parameter_names(mat):
            val = mat.get_vector_parameter_value(v)
            print(f'    Vector {v} = ({val.r}, {val.g}, {val.b}, {val.a})')

# Let's also test creating a fresh MID from m_solid and applying it
dyn_gold = unreal.MaterialInstanceDynamic.create(m_solid, sat)
dyn_gold.set_vector_parameter_value('Color', unreal.LinearColor(0.98, 0.82, 0.28, 1.0))
dyn_gold.set_scalar_parameter_value('Metallic', 0.9)
dyn_gold.set_scalar_parameter_value('Roughness', 0.2)
dyn_gold.set_scalar_parameter_value('EmissiveMultiplier', 0.5)
body.set_material(0, dyn_gold)
print('Directly assigned dyn_gold to body. Material now:', body.get_material(0))

unreal.SystemLibrary.execute_console_command(None, 'QUIT_EDITOR')
