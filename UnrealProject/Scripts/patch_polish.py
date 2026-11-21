with open('UnrealProject/Scripts/test_milestone2_polish.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

# 1. Update lines 201-220 (0-indexed)
lines[201] = '            mat_b.set_vector_parameter_value("Color", unreal.LinearColor(1.0, 0.80, 0.18, 1.0))\n'
lines[202] = '            mat_b.set_scalar_parameter_value("Metallic", 0.95)\n'
lines[203] = '            mat_b.set_scalar_parameter_value("Roughness", 0.18)\n'
lines[204] = '            mat_b.set_scalar_parameter_value("EmissiveMultiplier", 0.35)\n'

lines[214] = '            cell_blue = unreal.LinearColor(0.02, 0.22, 0.85, 1.0) if i in [0, 2] else unreal.LinearColor(0.04, 0.38, 0.98, 1.0)\n'
lines[216] = '            mat_blue.set_scalar_parameter_value("Metallic", 0.05)\n'
lines[217] = '            mat_blue.set_scalar_parameter_value("Roughness", 0.18)\n'
lines[218] = '            mat_blue.set_scalar_parameter_value("EmissiveMultiplier", 0.55)\n'

lines[226] = '            mat_silver.set_vector_parameter_value("Color", unreal.LinearColor(0.88, 0.92, 0.96, 1.0))\n'
lines[229] = '            mat_silver.set_scalar_parameter_value("EmissiveMultiplier", 0.30)\n'

# 2. Update lines 345-397 (0-indexed)
lines[345] = '    sat_nominal_path.set_editor_property("path_thickness", 14.0)\n'
lines[349] = '    debris_path.set_editor_property("path_thickness", 14.0)\n'
lines[353] = '    sat_modified_path.set_editor_property("path_thickness", 14.0)\n'

lines[364] = 'cam_overview_loc = unreal.Vector(125000.0, -75000.0, 52000.0)\n'
lines[365] = 'cam_overview_rot = look_at(cam_overview_loc, unreal.Vector(40000.0, -25000.0, 0.0))\n'
lines[366] = 'capture_view("Milestone2_Earth_Overview", cam_overview_loc, cam_overview_rot, fov=54.0, sun_rotation=sun_earth_rot, sun_intensity=14.0)\n'

lines[391] = 'sat_cam_loc = unreal.Vector(sat_pos_0.x - 1100.0, sat_pos_0.y - 1100.0, sat_pos_0.z + 750.0)\n'
lines[392] = 'sat_cam_rot = look_at(sat_cam_loc, sat_pos_0)\n'
lines[395] = 'sun_sat_rot = unreal.Rotator(pitch=-35.0, yaw=40.0, roll=0.0)\n'
lines[396] = 'capture_view("Milestone2_Satellite_Detail", sat_cam_loc, sat_cam_rot, fov=42.0, sun_rotation=sun_sat_rot, sun_intensity=35.0)\n'

with open('UnrealProject/Scripts/test_milestone2_polish.py', 'w', encoding='utf-8') as f:
    f.writelines(lines)

print("Patch applied successfully!")
