import unreal

mat = unreal.EditorAssetLibrary.load_asset("/Game/Common/M_SolidColor")
print(f"Loaded /Game/Common/M_SolidColor: {mat}")

if mat:
    # Check if used with spline meshes
    mat.set_editor_property("used_with_spline_meshes", True)
    unreal.MaterialEditingLibrary.recompile_material(mat)
    unreal.EditorAssetLibrary.save_loaded_asset(mat)
    print("Recompiled and saved M_SolidColor with used_with_spline_meshes=True")

unreal.SystemLibrary.execute_console_command(None, "QUIT_EDITOR")
