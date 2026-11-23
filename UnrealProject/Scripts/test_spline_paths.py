import unreal
import traceback

world = unreal.EditorLevelLibrary.get_editor_world()
actors = unreal.EditorLevelLibrary.get_all_level_actors()

for a in actors:
    lbl = a.get_actor_label()
    if "OrbitPath" in lbl:
        print(f"Actor: {lbl}")
        try:
            print(f"  PathColor: {a.path_color}")
            print(f"  PathThickness: {a.path_thickness}")
            spline_comp = a.get_component_by_class(unreal.SplineComponent)
            if spline_comp:
                print(f"  Spline points: {spline_comp.get_number_of_spline_points()}")
            meshes = a.spline_meshes
            print(f"  Spline meshes: {len(meshes)}")
            if len(meshes) > 0:
                print(f"  Mesh 0 material: {meshes[0].get_material(0).get_name()}")
        except Exception as e:
            print(f"  Error: {e}")
            traceback.print_exc()
