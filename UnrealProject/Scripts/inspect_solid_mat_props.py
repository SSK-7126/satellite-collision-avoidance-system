import unreal

mat = unreal.EditorAssetLibrary.load_asset('/Game/Common/M_SolidColor')
print('Material:', mat)
print('BaseColor connected:', mat.get_editor_property('base_color'))
print('EmissiveColor connected:', mat.get_editor_property('emissive_color'))
print('Roughness connected:', mat.get_editor_property('roughness'))
print('Metallic connected:', mat.get_editor_property('metallic'))

unreal.SystemLibrary.execute_console_command(None, 'QUIT_EDITOR')
