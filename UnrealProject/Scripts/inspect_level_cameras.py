import unreal

world = unreal.EditorLevelLibrary.get_editor_world()
actors = unreal.EditorLevelLibrary.get_all_level_actors()

print(f"Total actors in {world.get_name()}: {len(actors)}")
for a in actors:
    lbl = a.get_actor_label()
    cls_name = a.get_class().get_name()
    if "Camera" in lbl or "Camera" in cls_name:
        loc = a.get_actor_location()
        rot = a.get_actor_rotation()
        print(f"CamActor: {lbl} (Class: {cls_name}) at ({loc.x:.1f}, {loc.y:.1f}, {loc.z:.1f}) rot (P={rot.pitch:.2f}, Y={rot.yaw:.2f}, R={rot.roll:.2f})")
    elif any(k in lbl for k in ["Satellite", "Debris", "Earth", "Light", "SimulationManager"]):
        loc = a.get_actor_location()
        scale = a.get_actor_scale3d()
        print(f"Actor: {lbl} (Class: {cls_name}) at ({loc.x:.1f}, {loc.y:.1f}, {loc.z:.1f}) scale ({scale.x:.3f}, {scale.y:.3f}, {scale.z:.3f})")
