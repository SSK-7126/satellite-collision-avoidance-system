
import unreal

unreal.EditorLevelLibrary.load_level('/Game/Scenarios/CollisionAvoidanceDemo')
actors = unreal.EditorLevelLibrary.get_all_level_actors()
print(f'=== TOTAL ACTORS: {len(actors)} ===')
for a in actors:
    lbl = a.get_actor_label()
    cls = a.get_class().get_name()
    loc = a.get_actor_location()
    rot = a.get_actor_rotation()
    scale = a.get_actor_scale3d()
    hidden = a.is_hidden_ed()
    if any(k in lbl.lower() or k in cls.lower() for k in ['sky', 'fog', 'light', 'earth', 'sat', 'debris', 'camera', 'orbit', 'manager']):
        print(f'ACTOR: [{lbl}] ({cls}) Loc={loc} Rot={rot} Scale={scale} Hidden={hidden}')
