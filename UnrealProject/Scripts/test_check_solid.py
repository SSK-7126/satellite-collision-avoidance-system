import unreal
m1 = unreal.load_object(None, "/Game/Common/M_SolidColor.M_SolidColor")
print("=== TEST M_SOLIDCOLOR ===")
print("unreal.load_object:", m1)
m2 = unreal.EditorAssetLibrary.load_asset("/Game/Common/M_SolidColor")
print("load_asset:", m2)
if m2:
    print("m2 class:", m2.get_class().get_name())
    for expr in m2.get_editor_property("expressions"):
        print("  Expr:", expr.get_class().get_name(), expr.get_name())
    vec_params = unreal.MaterialEditingLibrary.get_vector_parameter_names(m2)
    scalar_params = unreal.MaterialEditingLibrary.get_scalar_parameter_names(m2)
    print("  Vector params:", vec_params)
    print("  Scalar params:", scalar_params)
unreal.SystemLibrary.execute_console_command(None, "QUIT_EDITOR")
