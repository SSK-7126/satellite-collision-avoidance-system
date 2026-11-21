import unreal

mat = unreal.EditorAssetLibrary.load_asset('/Game/Common/M_SolidColor')
print('Loaded:', mat)
res = unreal.MaterialEditingLibrary.recompile_material(mat)
print('Recompile result:', res)

# Check if there are compile errors or if it's compiled
comp_status = unreal.MaterialEditingLibrary.get_statistics(mat) if hasattr(unreal.MaterialEditingLibrary, 'get_statistics') else None
print('Stats:', comp_status)

unreal.SystemLibrary.execute_console_command(None, 'QUIT_EDITOR')
