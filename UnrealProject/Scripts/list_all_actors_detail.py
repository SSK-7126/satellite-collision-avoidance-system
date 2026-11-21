import unreal

unreal.EditorLevelLibrary.load_level('/Game/Scenarios/CollisionAvoidanceDemo')
actors = unreal.EditorLevelLibrary.get_all_level_actors()
print('=== ALL LEVEL ACTORS ===')
for a in actors:
    loc = a.get_actor_location()
    scale = a.get_actor_scale3d()
    print(f'{a.get_actor_label()} ({a.get_class().get_name()}): Loc={loc}, Scale={scale}')

unreal.SystemLibrary.execute_console_command(None, 'QUIT_EDITOR')
