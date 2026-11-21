import unreal

unreal.EditorLevelLibrary.load_level('/Game/Scenarios/CollisionAvoidanceDemo')
actors = unreal.EditorLevelLibrary.get_all_level_actors()
for a in actors:
    if isinstance(a, unreal.SatelliteActor):
        print('Found SatelliteActor:', a.get_actor_label())
        body = a.get_editor_property('satellite_body')
        if body:
            mat0 = body.get_material(0)
            print('SatelliteBody Material 0:', mat0.get_path_name() if mat0 else 'None')
            if isinstance(mat0, unreal.MaterialInstanceDynamic):
                print('  Parent:', mat0.get_editor_property('parent').get_path_name())
        panel = a.get_editor_property('solar_panel_left')
        if panel:
            mat0 = panel.get_material(0)
            print('SolarPanelLeft Material 0:', mat0.get_path_name() if mat0 else 'None')
            if isinstance(mat0, unreal.MaterialInstanceDynamic):
                print('  Parent:', mat0.get_editor_property('parent').get_path_name())
    elif isinstance(a, unreal.EarthActor):
        print('Found EarthActor:', a.get_actor_label())
        em = a.get_editor_property('earth_mesh')
        if em:
            mat0 = em.get_material(0)
            print('EarthMesh Material 0:', mat0.get_path_name() if mat0 else 'None')
            if isinstance(mat0, unreal.MaterialInstanceDynamic):
                print('  Parent:', mat0.get_editor_property('parent').get_path_name())
        atm = a.get_editor_property('atmosphere_mesh')
        if atm:
            mat0 = atm.get_material(0)
            print('AtmosphereMesh Material 0:', mat0.get_path_name() if mat0 else 'None')
            if isinstance(mat0, unreal.MaterialInstanceDynamic):
                print('  Parent:', mat0.get_editor_property('parent').get_path_name())

unreal.SystemLibrary.execute_console_command(None, 'QUIT_EDITOR')