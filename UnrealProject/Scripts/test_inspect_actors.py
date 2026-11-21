import unreal

unreal.EditorLevelLibrary.load_level("/Game/Scenarios/CollisionAvoidanceDemo")
actors = unreal.EditorLevelLibrary.get_all_level_actors()
print("=" * 60)
for a in actors:
    cname = a.get_class().get_name()
    if any(k in cname for k in ["Satellite", "Debris", "Earth", "Orbit", "Conjunction", "Manoeuvre"]):
        print(f"ACTOR: {a.get_name()} | Label: {a.get_actor_label()} | Class: {cname} | Loc: {a.get_actor_location()}")
print("=" * 60)
unreal.SystemLibrary.execute_console_command(None, "QUIT_EDITOR")
