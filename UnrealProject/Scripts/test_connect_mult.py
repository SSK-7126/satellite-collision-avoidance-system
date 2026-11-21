import unreal

mat_factory = unreal.MaterialFactoryNew()
asset_tools = unreal.AssetToolsHelpers.get_asset_tools()
temp_mat = asset_tools.create_asset('M_TestMult', '/Game/Common', unreal.Material, mat_factory)

param = unreal.MaterialEditingLibrary.create_material_expression(temp_mat, unreal.MaterialExpressionVectorParameter, -400, 0)
param.set_editor_property('parameter_name', 'Color')

mult = unreal.MaterialEditingLibrary.create_material_expression(temp_mat, unreal.MaterialExpressionMultiply, -200, 0)

c1 = unreal.MaterialEditingLibrary.connect_material_expressions(param, '', mult, 'A')
c2 = unreal.MaterialEditingLibrary.connect_material_expressions(param, 'RGB', mult, 'A')
print('connect_material_expressions param to mult A with \"\":', c1)
print('connect_material_expressions param to mult A with \"RGB\":', c2)

c_prop = unreal.MaterialEditingLibrary.connect_material_property(mult, '', unreal.MaterialProperty.MP_EMISSIVE_COLOR)
print('connect mult to MP_EMISSIVE_COLOR:', c_prop)

recomp = unreal.MaterialEditingLibrary.recompile_material(temp_mat)
print('Recompile:', recomp)

unreal.EditorAssetLibrary.delete_asset('/Game/Common/M_TestMult')
unreal.SystemLibrary.execute_console_command(None, 'QUIT_EDITOR')
