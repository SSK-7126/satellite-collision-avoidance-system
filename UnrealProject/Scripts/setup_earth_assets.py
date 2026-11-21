import unreal

print(">>> STARTING EARTH ASSETS SETUP <<<")

asset_tools = unreal.AssetToolsHelpers.get_asset_tools()
mat_factory = unreal.MaterialFactoryNew()

# 1. T_Earth_Day
tex_asset = unreal.EditorAssetLibrary.load_asset("/Game/Earth/T_Earth_Day")
if not tex_asset:
    png_path = "C:/Users/Sriram Krovi/satellite-collision-avoidance-system/UnrealProject/Content/Earth/T_Earth_Day.png"
    task = unreal.AssetImportTask()
    task.filename = png_path
    task.destination_path = "/Game/Earth"
    task.destination_name = "T_Earth_Day"
    task.replace_existing = True
    task.automated = True
    task.save = True
    unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task])
    tex_asset = unreal.EditorAssetLibrary.load_asset("/Game/Earth/T_Earth_Day")
print(f">>> Loaded T_Earth_Day: {tex_asset is not None} <<<")

# 2. M_Earth
m_earth = unreal.EditorAssetLibrary.load_asset("/Game/Earth/M_Earth")
if not m_earth:
    m_earth = asset_tools.create_asset("M_Earth", "/Game/Earth", unreal.Material, mat_factory)
    m_earth.set_editor_property("two_sided", False)
    tex_expr = unreal.MaterialEditingLibrary.create_material_expression(m_earth, unreal.MaterialExpressionTextureSampleParameter2D, -300, 0)
    tex_expr.set_editor_property("parameter_name", "EarthTexture")
    if tex_asset:
        tex_expr.set_editor_property("texture", tex_asset)
    unreal.MaterialEditingLibrary.connect_material_property(tex_expr, "RGB", unreal.MaterialProperty.MP_BASE_COLOR)

    rough_expr = unreal.MaterialEditingLibrary.create_material_expression(m_earth, unreal.MaterialExpressionConstant, -150, 150)
    rough_expr.set_editor_property("r", 0.65)
    unreal.MaterialEditingLibrary.connect_material_property(rough_expr, "", unreal.MaterialProperty.MP_ROUGHNESS)

    unreal.MaterialEditingLibrary.recompile_material(m_earth)
    unreal.EditorAssetLibrary.save_loaded_asset(m_earth)
print(">>> M_Earth confirmed <<<")

# 3. Create M_Atmosphere
m_atmo = unreal.EditorAssetLibrary.load_asset("/Game/Earth/M_Atmosphere")
if not m_atmo:
    m_atmo = asset_tools.create_asset("M_Atmosphere", "/Game/Earth", unreal.Material, mat_factory)

if m_atmo:
    m_atmo.set_editor_property("blend_mode", unreal.BlendMode.BLEND_TRANSLUCENT)
    m_atmo.set_editor_property("shading_model", unreal.MaterialShadingModel.MSM_UNLIT)
    m_atmo.set_editor_property("two_sided", False)

    fresnel = unreal.MaterialEditingLibrary.create_material_expression(m_atmo, unreal.MaterialExpressionFresnel, -450, 100)
    fresnel.set_editor_property("exponent", 4.5)
    fresnel.set_editor_property("base_reflect_fraction", 0.0)

    col_param = unreal.MaterialEditingLibrary.create_material_expression(m_atmo, unreal.MaterialExpressionVectorParameter, -450, -100)
    col_param.set_editor_property("parameter_name", "AtmosphereColor")
    col_param.set_editor_property("default_value", unreal.LinearColor(0.2, 0.65, 1.0, 1.0))

    intensity = unreal.MaterialEditingLibrary.create_material_expression(m_atmo, unreal.MaterialExpressionScalarParameter, -450, 0)
    intensity.set_editor_property("parameter_name", "AtmosphereIntensity")
    intensity.set_editor_property("default_value", 2.2)

    mul_col = unreal.MaterialEditingLibrary.create_material_expression(m_atmo, unreal.MaterialExpressionMultiply, -250, -50)
    unreal.MaterialEditingLibrary.connect_material_expressions(col_param, "", mul_col, "A")
    unreal.MaterialEditingLibrary.connect_material_expressions(intensity, "", mul_col, "B")

    mul_emissive = unreal.MaterialEditingLibrary.create_material_expression(m_atmo, unreal.MaterialExpressionMultiply, -100, -50)
    unreal.MaterialEditingLibrary.connect_material_expressions(mul_col, "", mul_emissive, "A")
    unreal.MaterialEditingLibrary.connect_material_expressions(fresnel, "", mul_emissive, "B")
    unreal.MaterialEditingLibrary.connect_material_property(mul_emissive, "", unreal.MaterialProperty.MP_EMISSIVE_COLOR)

    op_mult = unreal.MaterialEditingLibrary.create_material_expression(m_atmo, unreal.MaterialExpressionMultiply, -100, 150)
    scalar_op = unreal.MaterialEditingLibrary.create_material_expression(m_atmo, unreal.MaterialExpressionConstant, -250, 200)
    scalar_op.set_editor_property("r", 0.75)
    unreal.MaterialEditingLibrary.connect_material_expressions(fresnel, "", op_mult, "A")
    unreal.MaterialEditingLibrary.connect_material_expressions(scalar_op, "", op_mult, "B")
    unreal.MaterialEditingLibrary.connect_material_property(op_mult, "", unreal.MaterialProperty.MP_OPACITY)

    unreal.MaterialEditingLibrary.recompile_material(m_atmo)
    unreal.EditorAssetLibrary.save_loaded_asset(m_atmo)
    print(">>> M_Atmosphere successfully created and saved <<<")

# 4. Create M_SpaceSky
m_space = unreal.EditorAssetLibrary.load_asset("/Game/Earth/M_SpaceSky")
if not m_space:
    m_space = asset_tools.create_asset("M_SpaceSky", "/Game/Earth", unreal.Material, mat_factory)

if m_space:
    m_space.set_editor_property("shading_model", unreal.MaterialShadingModel.MSM_UNLIT)
    m_space.set_editor_property("two_sided", True)

    space_col = unreal.MaterialEditingLibrary.create_material_expression(m_space, unreal.MaterialExpressionVectorParameter, -200, 0)
    space_col.set_editor_property("parameter_name", "SpaceColor")
    space_col.set_editor_property("default_value", unreal.LinearColor(0.001, 0.0015, 0.004, 1.0))
    unreal.MaterialEditingLibrary.connect_material_property(space_col, "", unreal.MaterialProperty.MP_EMISSIVE_COLOR)

    unreal.MaterialEditingLibrary.recompile_material(m_space)
    unreal.EditorAssetLibrary.save_loaded_asset(m_space)
    print(">>> M_SpaceSky successfully created and saved <<<")

print(">>> ALL MATERIAL ASSETS READY. Exiting. <<<")
unreal.SystemLibrary.execute_console_command(None, "QUIT_EDITOR")
