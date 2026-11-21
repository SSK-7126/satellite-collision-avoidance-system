import unreal

m_earth = unreal.EditorAssetLibrary.load_asset("/Game/Earth/M_Earth")
m_atmo = unreal.EditorAssetLibrary.load_asset("/Game/Earth/M_Atmosphere")
m_solid = unreal.EditorAssetLibrary.load_asset("/Game/Common/M_SolidColor")

print("=== MATERIAL DIAGNOSTICS ===")
print("M_Earth:", m_earth)
if m_earth:
    print("  BlendMode:", m_earth.get_editor_property("blend_mode"))
    print("  ShadingModel:", m_earth.get_editor_property("shading_model"))
    print("  TwoSided:", m_earth.get_editor_property("two_sided"))

print("M_Atmosphere:", m_atmo)
if m_atmo:
    print("  BlendMode:", m_atmo.get_editor_property("blend_mode"))
    print("  ShadingModel:", m_atmo.get_editor_property("shading_model"))
    print("  TwoSided:", m_atmo.get_editor_property("two_sided"))

print("M_SolidColor:", m_solid)
if m_solid:
    print("  BlendMode:", m_solid.get_editor_property("blend_mode"))
    print("  ShadingModel:", m_solid.get_editor_property("shading_model"))
    print("  TwoSided:", m_solid.get_editor_property("two_sided"))

unreal.SystemLibrary.execute_console_command(None, "QUIT_EDITOR")
