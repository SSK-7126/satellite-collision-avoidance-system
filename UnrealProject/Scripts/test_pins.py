import unreal

mat_factory = unreal.MaterialFactoryNew()
asset_tools = unreal.AssetToolsHelpers.get_asset_tools()
temp_mat = asset_tools.create_asset('M_TestMat', '/Game/Common', unreal.Material, mat_factory)

param = unreal.MaterialEditingLibrary.create_material_expression(temp_mat, unreal.MaterialExpressionVectorParameter, -200, 0)
r1 = unreal.MaterialEditingLibrary.connect_material_property(param, '', unreal.MaterialProperty.MP_BASE_COLOR)
print('Connect with empty string:', r1)
r2 = unreal.MaterialEditingLibrary.connect_material_property(param, 'RGB', unreal.MaterialProperty.MP_BASE_COLOR)
print('Connect with RGB:', r2)

comp_ok = unreal.MaterialEditingLibrary.recompile_material(temp_mat)
print('Recompile test mat:', comp_ok)
unreal.EditorAssetLibrary.delete_asset('/Game/Common/M_TestMat')

unreal.SystemLibrary.execute_console_command(None, 'QUIT_EDITOR')