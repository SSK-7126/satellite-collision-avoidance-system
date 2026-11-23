import unreal

world = unreal.EditorLevelLibrary.get_editor_world()
actors = unreal.EditorLevelLibrary.get_all_level_actors()

# Let's inspect all static mesh components and spline mesh components in the entire scene
for a in actors:
    # check spline meshes
    smc = a.get_components_by_class(unreal.SplineMeshComponent)
    if len(smc) > 0:
        print(f"Actor with SplineMesh: {a.get_actor_label()}, count: {len(smc)}")
        for i, m in enumerate(smc[:3]):
            mat = m.get_material(0)
            print(f"   Mesh {i}: mat={mat.get_name() if mat else 'None'}, start={m.get_start_position()}, end={m.get_end_position()}")
