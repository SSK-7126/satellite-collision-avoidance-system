import unreal

unreal.EditorLevelLibrary.load_level('/Game/Scenarios/CollisionAvoidanceDemo')
actors = unreal.EditorLevelLibrary.get_all_level_actors()

ea = None
for a in actors:
    if isinstance(a, unreal.EarthActor):
        ea = a
        break

print('EarthActor:', ea)
em = ea.get_editor_property('earth_mesh')
atm = ea.get_editor_property('atmosphere_mesh')
print('EarthMesh material:', em.get_material(0).get_path_name())
print('AtmosphereMesh material:', atm.get_material(0).get_path_name())
print('AtmosphereMesh hidden:', atm.get_editor_property('hidden_in_game'))
print('AtmosphereMesh visible:', atm.is_visible())
print('AtmosphereMesh relative scale:', atm.get_editor_property('relative_scale3d'))
print('EarthMesh relative scale:', em.get_editor_property('relative_scale3d'))

unreal.SystemLibrary.execute_console_command(None, 'QUIT_EDITOR')