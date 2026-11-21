import unreal

m_earth = unreal.EditorAssetLibrary.load_asset("/Game/Earth/M_Earth")
print("=== INSPECT M_EARTH ===")
print("m_earth:", m_earth)
texs = unreal.MaterialEditingLibrary.get_used_textures(m_earth)
print("Used textures:", [t.get_name() for t in texs])
vecs = unreal.MaterialEditingLibrary.get_vector_parameter_names(m_earth)
print("Vector parameter names:", vecs)
scals = unreal.MaterialEditingLibrary.get_scalar_parameter_names(m_earth)
print("Scalar parameter names:", scals)

t_earth = unreal.EditorAssetLibrary.load_asset("/Game/Earth/T_Earth_Day")
print("T_Earth_Day asset:", t_earth)

unreal.SystemLibrary.execute_console_command(None, "QUIT_EDITOR")
