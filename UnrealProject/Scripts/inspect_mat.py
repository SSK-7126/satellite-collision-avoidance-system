import unreal

mat = unreal.EditorAssetLibrary.load_asset("/Game/Common/M_SolidColor")
print(f"MAT: {mat}")
if mat:
    exprs = mat.get_editor_property("expressions")
    print(f"Expressions count: {len(exprs)}")
    for e in exprs:
        print(f"  Expr: {e.get_name()}, Type: {type(e)}")

earth_mat = unreal.EditorAssetLibrary.load_asset("/Game/Earth/M_Earth")
print(f"Earth Mat: {earth_mat}")

unreal.SystemLibrary.execute_console_command(None, "QUIT_EDITOR")
