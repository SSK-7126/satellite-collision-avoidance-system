import unreal

print(">>> DIAGNOSTIC SCRIPT STARTING <<<")

# Load level
level_path = "/Game/Scenarios/CollisionAvoidanceDemo"
loaded = unreal.EditorLevelLibrary.load_level(level_path)
print(f">>> Level loaded: {loaded} <<<")

world = unreal.EditorLevelLibrary.get_editor_world()
print(f">>> World name: {world.get_name() if world else 'None'} <<<")

all_actors = unreal.EditorLevelLibrary.get_all_level_actors()
print(f">>> Total actors in level: {len(all_actors)} <<<")

class_counts = {}
landscape_actors = []
for a in all_actors:
    cname = a.get_class().get_name()
    class_counts[cname] = class_counts.get(cname, 0) + 1
    if "Landscape" in cname:
        landscape_actors.append(a.get_actor_label())

print(">>> Actor counts by class: <<<")
for cname, count in sorted(class_counts.items(), key=lambda x: -x[1]):
    print(f"  {cname}: {count}")

print(f">>> Total Landscape actors: {len(landscape_actors)} <<<")
if landscape_actors:
    print(f"  Sample landscape actors: {landscape_actors[:5]}")

print(">>> DIAGNOSTIC SCRIPT COMPLETE. Exiting editor. <<<")
unreal.SystemLibrary.execute_console_command(None, "QUIT_EDITOR")

