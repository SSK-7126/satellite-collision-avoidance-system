import unreal

mat_factory = unreal.MaterialFactoryNew()
asset_tools = unreal.AssetToolsHelpers.get_asset_tools()
temp_mat = asset_tools.create_asset('M_TestTexPins', '/Game/Common', unreal.Material, mat_factory)

tex_expr = unreal.MaterialEditingLibrary.create_material_expression(temp_mat, unreal.MaterialExpressionTextureSampleParameter2D, -300, 0)
t_earth = unreal.EditorAssetLibrary.load_asset("/Game/Earth/T_Earth_Day")
if t_earth:
    tex_expr.set_editor_property("texture", t_earth)

print("=== TESTING TEXTURE SAMPLE PINS ===")
for pin in ["", "RGB", "RGBA", "Color", "Output", "0", "None"]:
    res = unreal.MaterialEditingLibrary.connect_material_property(tex_expr, pin, unreal.MaterialProperty.MP_BASE_COLOR)
    print(f"Pin '{pin}': connect result = {res}")

# Check recompile
ok = unreal.MaterialEditingLibrary.recompile_material(temp_mat)
print("Recompile:", ok)

unreal.EditorAssetLibrary.delete_asset('/Game/Common/M_TestTexPins')
unreal.SystemLibrary.execute_console_command(None, 'QUIT_EDITOR')
