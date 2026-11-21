import unreal

m_solid = unreal.EditorAssetLibrary.load_asset("/Game/Common/M_SolidColor")
print(f"M_SolidColor: {m_solid}")
if m_solid:
    print("M_SolidColor BlendMode:", m_solid.get_editor_property("blend_mode"))
    print("M_SolidColor ShadingModel:", m_solid.get_editor_property("shading_model"))
    print("M_SolidColor VectorParams:", [str(n) for n in unreal.MaterialEditingLibrary.get_vector_parameter_names(m_solid)])
    print("M_SolidColor ScalarParams:", [str(n) for n in unreal.MaterialEditingLibrary.get_scalar_parameter_names(m_solid)])

unreal.SystemLibrary.execute_console_command(None, "QUIT_EDITOR")
