import unreal

m_solid = unreal.EditorAssetLibrary.load_asset('/Game/Common/M_SolidColor')
vecs = unreal.MaterialEditingLibrary.get_vector_parameter_names(m_solid)
scals = unreal.MaterialEditingLibrary.get_scalar_parameter_names(m_solid)
print('Vector params:', [str(v) for v in vecs])
print('Scalar params:', [str(s) for s in scals])

unreal.SystemLibrary.execute_console_command(None, 'QUIT_EDITOR')
