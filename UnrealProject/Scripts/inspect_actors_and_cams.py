"""
inspect_actors_and_cams.py
"""
import unreal
import os

out_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "../Saved/inspect_output.txt"))
os.makedirs(os.path.dirname(out_path), exist_ok=True)

with open(out_path, "w", encoding="utf-8") as f:
    def log(msg):
        unreal.log(msg)
        f.write(msg + "\n")
        f.flush()

    level_path = "/Game/Scenarios/CollisionAvoidanceDemo"
    unreal.EditorLevelLibrary.load_level(level_path)
    world = unreal.EditorLevelLibrary.get_editor_world()
    all_actors = unreal.EditorLevelLibrary.get_all_level_actors()

    log("=" * 80)
    log(f"ACTOR INSPECTION IN {level_path}")
    log("=" * 80)

    for a in all_actors:
        label = a.get_actor_label()
        cls_name = a.get_class().get_name()
        if any(k in label.lower() for k in ["sat", "deb", "cam", "earth", "sim"]):
            loc = a.get_actor_location()
            scale = a.get_actor_scale3d()
            rot = a.get_actor_rotation()
            log(f"Actor: {label:30} | Class: {cls_name:25} | Loc: {loc} | Scale: {scale} | Rot: {rot}")
            if isinstance(a, unreal.CameraActor):
                cc = a.get_component_by_class(unreal.CameraComponent)
                if cc:
                    log(f"   Camera FOV: {cc.get_editor_property('field_of_view')}")
            if isinstance(a, (unreal.SatelliteActor, unreal.DebrisActor)):
                for comp in a.get_components_by_class(unreal.SceneComponent):
                    parent_name = comp.get_attach_parent().get_name() if comp.get_attach_parent() else "NONE"
                    r_scale = comp.get_editor_property("relative_scale3d")
                    r_loc = comp.get_editor_property("relative_location")
                    log(f"   Comp: {comp.get_name():25} ({comp.get_class().get_name():20}) Parent: {parent_name:20} RelLoc: {r_loc} RelScale: {r_scale}")

    log("=" * 80)
    log("INSPECTION COMPLETE")
