import unreal

world = unreal.EditorLevelLibrary.get_editor_world()
actors = unreal.EditorLevelLibrary.get_all_level_actors()

for a in actors:
    loc = a.get_actor_location()
    dx = loc.x - 70000.0
    dy = loc.y
    dz = loc.z
    dist = (dx*dx + dy*dy + dz*dz)**0.5
    if dist < 20000.0:
        print(f"Near Actor: {a.get_actor_label()} ({a.get_class().get_name()}) at ({loc.x:.1f}, {loc.y:.1f}, {loc.z:.1f})")
