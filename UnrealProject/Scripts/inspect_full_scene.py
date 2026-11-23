import unreal

level_path = "/Game/Scenarios/CollisionAvoidanceDemo"
loaded = unreal.EditorLevelLibrary.load_level(level_path)
print(f"=== Level Loaded: {loaded} ===")

world = unreal.EditorLevelLibrary.get_editor_world()
actors = unreal.EditorLevelLibrary.get_all_level_actors()
print(f"Total level actors: {len(actors)}")

for a in actors:
    lbl = a.get_actor_label()
    cls_name = a.get_class().get_name()
    loc = a.get_actor_location()
    rot = a.get_actor_rotation()
    scale = a.get_actor_scale3d()
    
    if "Camera" in lbl or "Camera" in cls_name:
        comp = a.get_component_by_class(unreal.CameraComponent)
        fov = comp.get_editor_property("field_of_view") if comp else -1
        print(f"CAMERA: {lbl} ({cls_name})")
        print(f"  Loc: ({loc.x:.1f}, {loc.y:.1f}, {loc.z:.1f}), Rot: (P={rot.pitch:.2f}, Y={rot.yaw:.2f}, R={rot.roll:.2f}), FOV: {fov}")
    else:
        print(f"ACTOR: {lbl} ({cls_name}) Loc=({loc.x:.1f}, {loc.y:.1f}, {loc.z:.1f}) Scale=({scale.x:.3f}, {scale.y:.3f}, {scale.z:.3f})")
        if "Satellite" in lbl or "Debris" in lbl:
            for c in a.get_components_by_class(unreal.SceneComponent):
                cname = c.get_name()
                cloc = c.get_world_location()
                relscale = c.get_relative_scale3d()
                print(f"    Comp: {cname} ({c.get_class().get_name()}) RelScale=({relscale.x:.3f}, {relscale.y:.3f}, {relscale.z:.3f}) WorldLoc=({cloc.x:.1f}, {cloc.y:.1f}, {cloc.z:.1f})")
