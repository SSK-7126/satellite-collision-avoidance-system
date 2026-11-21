import unreal

m_solid = unreal.EditorAssetLibrary.load_asset('/Game/Common/M_SolidColor')
print('M_SolidColor:', m_solid)
if m_solid:
    print('  is_valid:', m_solid.is_valid_low_level())
    print('  two_sided:', m_solid.get_editor_property('two_sided'))
    print('  used_with_spline_meshes:', m_solid.get_editor_property('used_with_spline_meshes'))

m_earth = unreal.EditorAssetLibrary.load_asset('/Game/Earth/M_Earth')
print('M_Earth:', m_earth)
if m_earth:
    print('  is_valid:', m_earth.is_valid_low_level())

m_atmo = unreal.EditorAssetLibrary.load_asset('/Game/Earth/M_Atmosphere')
print('M_Atmosphere:', m_atmo)

# Check if there is asset compiling manager
try:
    mgr = unreal.AssetCompilingManager
    print('AssetCompilingManager available')
except Exception as e:
    print('AssetCompilingManager err:', e)

unreal.SystemLibrary.execute_console_command(None, 'QUIT_EDITOR')