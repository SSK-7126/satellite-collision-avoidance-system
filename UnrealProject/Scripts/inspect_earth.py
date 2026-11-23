import unreal

world = unreal.EditorLevelLibrary.get_editor_world()
actors = unreal.EditorLevelLibrary.get_all_level_actors()

earth = None
for a in actors:
    if a.get_actor_label() == "Earth_CelestialBody":
        earth = a
        break

if earth:
    mesh = earth.get_editor_property("earth_mesh")
    mat = mesh.get_material(0)
    print(f"Earth Material: {mat.get_name()}, Class: {mat.get_class().get_name()}")
    
    # Check atmosphere mesh
    atm = earth.get_editor_property("atmosphere_mesh")
    print(f"Atmosphere Mesh: {atm.get_name() if atm else 'None'}")
    if atm:
        amat = atm.get_material(0)
        print(f"Atmosphere Material: {amat.get_name() if amat else 'None'}")
