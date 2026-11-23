import unreal

world = unreal.EditorLevelLibrary.get_editor_world()
actors = unreal.EditorLevelLibrary.get_all_level_actors()

cam = None
vis = None
for a in actors:
    lbl = a.get_actor_label()
    if lbl == "Camera_Conjunction_TCA":
        cam = a
    elif lbl == "Conjunction_Visualizer":
        vis = a

if cam and vis:
    print(f"Cam loc: {cam.get_actor_location()}")
    print(f"Cam rot: {cam.get_actor_rotation()}")
    print(f"Vis loc: {vis.get_actor_location()}")
    print(f"Vis scale: {vis.get_actor_scale3d()}")
    comps = vis.get_components_by_class(unreal.StaticMeshComponent)
    for c in comps:
        print(f"  Comp: {c.get_name()}")
        print(f"    WorldLoc: {c.get_world_location()}")
        print(f"    WorldScale: {c.get_world_scale()}")
        print(f"    Material: {c.get_material(0).get_name() if c.get_material(0) else 'None'}")
