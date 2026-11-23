import unreal

world = unreal.EditorLevelLibrary.get_editor_world()
actors = unreal.EditorLevelLibrary.get_all_level_actors()

for a in actors:
    lbl = a.get_actor_label()
    if "OrbitPath" in lbl:
        comps = a.get_components_by_class(unreal.SplineMeshComponent)
        print(f"Path: {lbl}, SplineMeshes: {len(comps)}")
        if len(comps) > 0:
            mat = comps[0].get_material(0)
            print(f"  Material: {mat.get_name() if mat else 'None'}, Class: {mat.get_class().get_name() if mat else 'None'}")
            if isinstance(mat, unreal.MaterialInstanceDynamic):
                col = mat.get_vector_parameter_value("Color")
                emiss = mat.get_scalar_parameter_value("EmissiveMultiplier")
                print(f"  Color: {col}, Emissive: {emiss}")
