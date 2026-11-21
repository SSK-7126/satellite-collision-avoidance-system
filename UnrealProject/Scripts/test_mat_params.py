import unreal

mat = unreal.EditorAssetLibrary.load_asset("/Game/Common/M_SolidColor")
print("M_SolidColor:", mat)

# Check parameters
vp_names = unreal.MaterialEditingLibrary.get_vector_parameter_names(mat)
print("Vector Parameter Names:", [str(n) for n in vp_names])

sp_names = unreal.MaterialEditingLibrary.get_scalar_parameter_names(mat)
print("Scalar Parameter Names:", [str(n) for n in sp_names])

# Test creating MID
mid = unreal.MaterialInstanceDynamic.create(mat, None) if hasattr(unreal.MaterialInstanceDynamic, 'create') else None
print("MID via create:", mid)

unreal.SystemLibrary.execute_console_command(None, "QUIT_EDITOR")
