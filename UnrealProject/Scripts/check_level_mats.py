import unreal

world = unreal.EditorLevelLibrary.get_editor_world()
all_actors = unreal.EditorLevelLibrary.get_all_level_actors()

sat_actors = [a for a in all_actors if isinstance(a, unreal.SatelliteActor)]
print(f"Sat actors count: {len(sat_actors)}")
if sat_actors:
    sat = sat_actors[0]
    body = sat.get_editor_property("satellite_body")
    print(f"SatelliteBody: {body}")
    if body:
        mat0 = body.get_material(0)
        print(f"SatelliteBody mat 0: {mat0.get_path_name() if mat0 else 'None'}")

earth_actors = [a for a in all_actors if isinstance(a, unreal.EarthActor)]
if earth_actors:
    ea = earth_actors[0]
    em = ea.get_editor_property("earth_mesh")
    atm = ea.get_editor_property("atmosphere_mesh")
    print(f"EarthMesh mat: {em.get_material(0).get_path_name() if em and em.get_material(0) else 'None'}")
    print(f"AtmoMesh mat: {atm.get_material(0).get_path_name() if atm and atm.get_material(0) else 'None'}")
    print(f"AtmoMesh rel scale: {atm.get_relative_scale3d() if atm else 'None'}")
    print(f"AtmoMesh world scale: {atm.get_world_scale3d() if atm else 'None'}")

m_solid = unreal.EditorAssetLibrary.load_asset("/Game/Common/M_SolidColor")
print(f"Loaded /Game/Common/M_SolidColor: {m_solid.get_path_name() if m_solid else 'None'}")

unreal.SystemLibrary.execute_console_command(None, "QUIT_EDITOR")
