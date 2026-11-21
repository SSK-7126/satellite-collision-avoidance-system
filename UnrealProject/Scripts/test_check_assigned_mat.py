import unreal

unreal.EditorLevelLibrary.load_level("/Game/Scenarios/CollisionAvoidanceDemo")
all_actors = unreal.EditorLevelLibrary.get_all_level_actors()
sat = [a for a in all_actors if isinstance(a, unreal.SatelliteActor)][0]

m_solid = unreal.EditorAssetLibrary.load_asset("/Game/Common/M_SolidColor")
print("=== SAT MATERIAL CHECK ===")
print("Loaded m_solid:", m_solid)

body = sat.get_editor_property("satellite_body")
mid = body.create_dynamic_material_instance(0, m_solid)
print("Created MID:", mid)
mid.set_vector_parameter_value("Color", unreal.LinearColor(1.0, 0.0, 0.0, 1.0)) # PURE RED
body.set_material(0, mid)

assigned_mat = body.get_material(0)
print("Assigned Material on body:", assigned_mat)
print("Assigned Material class:", assigned_mat.get_class().get_name() if assigned_mat else "None")

# Check vector parameter
col_val = assigned_mat.get_vector_parameter_value("Color") if hasattr(assigned_mat, "get_vector_parameter_value") else "N/A"
print("Vector Parameter 'Color':", col_val)

unreal.SystemLibrary.execute_console_command(None, "QUIT_EDITOR")
