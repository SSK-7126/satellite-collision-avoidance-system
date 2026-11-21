import unreal

m_earth = unreal.EditorAssetLibrary.load_asset("/Game/Earth/M_Earth")
print("=== M_EARTH NODES ===")
print("Material:", m_earth)
exprs = m_earth.get_editor_property("material_expression_editor_only_data") # or get_editor_property("expressions")
# Let's inspect expressions
for prop in dir(m_earth):
    if "expression" in prop.lower():
        print("Prop:", prop, getattr(m_earth, prop, None))

tex_sample = unreal.MaterialEditingLibrary.get_used_textures(m_earth)
print("Used textures:", tex_sample)
for t in tex_sample:
    print("Tex name:", t.get_name(), "path:", t.get_path_name())

# Let's check T_Earth_Day
t_day = unreal.EditorAssetLibrary.load_asset("/Game/Earth/T_Earth_Day")
print("T_Earth_Day loaded:", t_day)
if t_day:
    print("T_Earth_Day format:", t_day.get_editor_property("format") if hasattr(t_day, "format") else "N/A")
    print("T_Earth_Day lod_group:", t_day.get_editor_property("lod_group"))
    print("T_Earth_Day compression_settings:", t_day.get_editor_property("compression_settings"))

unreal.SystemLibrary.execute_console_command(None, "QUIT_EDITOR")
