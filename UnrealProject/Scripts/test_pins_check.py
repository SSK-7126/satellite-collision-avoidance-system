import unreal

mat_factory = unreal.MaterialFactoryNew()
asset_tools = unreal.AssetToolsHelpers.get_asset_tools()
temp_mat = asset_tools.create_asset('M_TestPinMat', '/Game/Common', unreal.Material, mat_factory)

param = unreal.MaterialEditingLibrary.create_material_expression(temp_mat, unreal.MaterialExpressionVectorParameter, -200, 0)
param.set_editor_property("parameter_name", "Color")
param.set_editor_property("default_value", unreal.LinearColor(1.0, 0.8, 0.0, 1.0))

print("Testing connect_material_property:")
for pin in ["", "RGB", "RGBA", "Color", "0"]:
    res = unreal.MaterialEditingLibrary.connect_material_property(param, pin, unreal.MaterialProperty.MP_BASE_COLOR)
    print(f"  pin '{pin}': {res}")

comp_ok = unreal.MaterialEditingLibrary.recompile_material(temp_mat)
print(f"Recompile: {comp_ok}")

unreal.EditorAssetLibrary.delete_asset('/Game/Common/M_TestPinMat')
unreal.SystemLibrary.execute_console_command(None, 'QUIT_EDITOR')
