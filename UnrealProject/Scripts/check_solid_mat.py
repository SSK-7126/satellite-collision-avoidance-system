import unreal

mat = unreal.EditorAssetLibrary.load_asset('/Game/Common/M_SolidColor')
print('Loaded mat:', mat)
print('Material class:', mat.get_class().get_name())

# Check expressions in material
expressions = mat.get_editor_property('expressions')
print(f'Expressions count: {len(expressions)}')
for exp in expressions:
    print(' ', exp.get_class().get_name(), exp.get_name())

unreal.SystemLibrary.execute_console_command(None, 'QUIT_EDITOR')