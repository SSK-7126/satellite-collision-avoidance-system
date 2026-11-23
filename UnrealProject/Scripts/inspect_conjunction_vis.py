import unreal

world = unreal.EditorLevelLibrary.get_editor_world()
actors = unreal.EditorLevelLibrary.get_all_level_actors()

for a in actors:
    if "Conjunction" in a.get_actor_label():
        print(f"Actor: {a.get_actor_label()} ({a.get_class().get_name()})")
        print(f"  Location: {a.get_actor_location()}")
        print(f"  Rotation: {a.get_actor_rotation()}")
        print(f"  Scale: {a.get_actor_scale3d()}")
        comps = a.get_components_by_class(unreal.StaticMeshComponent)
        for c in comps:
            mat = c.get_material(0)
            print(f"    MeshComp: {c.get_name()}, RelLoc: {c.get_editor_property('relative_location')}, Scale: {c.get_editor_property('relative_scale3d')}, Mat: {mat.get_name() if mat else 'None'}")
