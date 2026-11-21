import unreal

m_solid = unreal.EditorAssetLibrary.load_asset("/Game/Common/M_SolidColor")
print("=== INSPECT M_SOLIDCOLOR ===")
print("Material:", m_solid)
for expr in m_solid.get_editor_property("expressions"):
    pname = expr.get_editor_property("parameter_name") if hasattr(expr, "get_editor_property") and hasattr(expr, "parameter_name") else "N/A"
    print("  Expr:", expr.get_class().get_name(), "ParamName:", pname)

print("Vector params:", unreal.MaterialEditingLibrary.get_vector_parameter_names(m_solid))
print("Scalar params:", unreal.MaterialEditingLibrary.get_scalar_parameter_names(m_solid))
unreal.SystemLibrary.execute_console_command(None, "QUIT_EDITOR")
