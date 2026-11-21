import unreal

m_solid = unreal.EditorAssetLibrary.load_asset("/Game/Common/M_SolidColor")
print(f"M_SolidColor: {m_solid}")

# Check if BaseColor expression is connected
# In Unreal Engine Material Editing Library, let's test connecting to MP_BASE_COLOR
# and check if the material compiles without errors
print("Recompiling M_SolidColor...")
success = unreal.MaterialEditingLibrary.recompile_material(m_solid)
print(f"Recompile success: {success}")

# Check textures or expressions
unreal.SystemLibrary.execute_console_command(None, "QUIT_EDITOR")
