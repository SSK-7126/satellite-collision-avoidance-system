import unreal

print("=== CMD TEST SCRIPT RUNNING ===")
world = unreal.EditorLevelLibrary.get_editor_world()
print("Editor World:", world.get_name() if world else "None")
actors = unreal.EditorLevelLibrary.get_all_level_actors()
print("Total actors:", len(actors))
for a in actors:
    cname = a.get_class().get_name()
    if 'Actor' in cname or 'Visualizer' in cname or 'Simulation' in cname:
        print(f"Actor: {a.get_actor_label()} ({cname}) at {a.get_actor_location()}")
print("=== CMD TEST SCRIPT FINISHED ===")

