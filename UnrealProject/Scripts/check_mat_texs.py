import unreal

m_solid = unreal.EditorAssetLibrary.load_asset('/Game/Common/M_SolidColor')
texs = unreal.MaterialEditingLibrary.get_used_textures(m_solid)
print('Used textures in M_SolidColor:', [t.get_path_name() for t in texs])

unreal.SystemLibrary.execute_console_command(None, 'QUIT_EDITOR')
