import unreal

m_earth = unreal.EditorAssetLibrary.load_asset("/Game/Earth/M_Earth")
print(f"M_Earth: {m_earth}")
if m_earth:
    print("M_Earth BlendMode:", m_earth.get_editor_property("blend_mode"))
    print("M_Earth ShadingModel:", m_earth.get_editor_property("shading_model"))
    print("M_Earth Textures:", [t.get_name() for t in unreal.MaterialEditingLibrary.get_used_textures(m_earth)])

m_atmo = unreal.EditorAssetLibrary.load_asset("/Game/Earth/M_Atmosphere")
print(f"M_Atmosphere: {m_atmo}")
if m_atmo:
    print("M_Atmosphere BlendMode:", m_atmo.get_editor_property("blend_mode"))
    print("M_Atmosphere ShadingModel:", m_atmo.get_editor_property("shading_model"))
    print("M_Atmosphere VectorParams:", [str(n) for n in unreal.MaterialEditingLibrary.get_vector_parameter_names(m_atmo)])
    print("M_Atmosphere ScalarParams:", [str(n) for n in unreal.MaterialEditingLibrary.get_scalar_parameter_names(m_atmo)])

unreal.SystemLibrary.execute_console_command(None, "QUIT_EDITOR")
