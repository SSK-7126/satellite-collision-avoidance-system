import unreal

unreal.EditorLevelLibrary.load_level('/Game/Scenarios/CollisionAvoidanceDemo')
actors = unreal.EditorLevelLibrary.get_all_level_actors()

print(f"=== ALL ACTORS IN LEVEL ({len(actors)}) ===")
for a in actors:
    print(f"  {a.get_class().get_name():30s} : {a.get_actor_label()}")

unreal.SystemLibrary.execute_console_command(None, "QUIT_EDITOR")
