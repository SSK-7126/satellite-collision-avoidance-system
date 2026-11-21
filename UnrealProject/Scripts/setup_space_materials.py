import unreal

print(">>> CREATING COMMON SPACE MATERIALS <<<")

asset_tools = unreal.AssetToolsHelpers.get_asset_tools()
mat_factory = unreal.MaterialFactoryNew()

# Ensure /Game/Common folder exists
common_path = "/Game/Common"

# 1. Create M_SolidColor
m_solid = unreal.EditorAssetLibrary.load_asset(f"{common_path}/M_SolidColor")
if not m_solid:
    m_solid = asset_tools.create_asset("M_SolidColor", common_path, unreal.Material, mat_factory)

if m_solid:
    m_solid.set_editor_property("two_sided", True)
    
    # Color Parameter
    col_param = unreal.MaterialEditingLibrary.create_material_expression(m_solid, unreal.MaterialExpressionVectorParameter, -400, -100)
    col_param.set_editor_property("parameter_name", "Color")
    col_param.set_editor_property("default_value", unreal.LinearColor(1.0, 1.0, 1.0, 1.0))
    
    # BaseColor connection
    unreal.MaterialEditingLibrary.connect_material_property(col_param, "", unreal.MaterialProperty.MP_BASE_COLOR)
    
    # Emissive connection with multiplier
    emissive_mult_param = unreal.MaterialEditingLibrary.create_material_expression(m_solid, unreal.MaterialExpressionScalarParameter, -400, 100)
    emissive_mult_param.set_editor_property("parameter_name", "EmissiveMultiplier")
    emissive_mult_param.set_editor_property("default_value", 0.6)
    
    mul_expr = unreal.MaterialEditingLibrary.create_material_expression(m_solid, unreal.MaterialExpressionMultiply, -200, 0)
    unreal.MaterialEditingLibrary.connect_material_expressions(col_param, "", mul_expr, "A")
    unreal.MaterialEditingLibrary.connect_material_expressions(emissive_mult_param, "", mul_expr, "B")
    unreal.MaterialEditingLibrary.connect_material_property(mul_expr, "", unreal.MaterialProperty.MP_EMISSIVE_COLOR)
    
    # Metallic parameter
    metal_param = unreal.MaterialEditingLibrary.create_material_expression(m_solid, unreal.MaterialExpressionScalarParameter, -400, 250)
    metal_param.set_editor_property("parameter_name", "Metallic")
    metal_param.set_editor_property("default_value", 0.5)
    unreal.MaterialEditingLibrary.connect_material_property(metal_param, "", unreal.MaterialProperty.MP_METALLIC)
    
    # Roughness parameter
    rough_param = unreal.MaterialEditingLibrary.create_material_expression(m_solid, unreal.MaterialExpressionScalarParameter, -400, 400)
    rough_param.set_editor_property("parameter_name", "Roughness")
    rough_param.set_editor_property("default_value", 0.3)
    unreal.MaterialEditingLibrary.connect_material_property(rough_param, "", unreal.MaterialProperty.MP_ROUGHNESS)
    
    unreal.MaterialEditingLibrary.recompile_material(m_solid)
    unreal.EditorAssetLibrary.save_loaded_asset(m_solid)
    print(">>> M_SolidColor created and saved successfully! <<<")

# 2. Also create M_TranslucentDisc for Conjunction Encounter Plane
m_disc = unreal.EditorAssetLibrary.load_asset(f"{common_path}/M_TranslucentDisc")
if not m_disc:
    m_disc = asset_tools.create_asset("M_TranslucentDisc", common_path, unreal.Material, mat_factory)

if m_disc:
    m_disc.set_editor_property("blend_mode", unreal.BlendMode.BLEND_TRANSLUCENT)
    m_disc.set_editor_property("shading_model", unreal.MaterialShadingModel.MSM_UNLIT)
    m_disc.set_editor_property("two_sided", True)
    
    disc_col = unreal.MaterialEditingLibrary.create_material_expression(m_disc, unreal.MaterialExpressionVectorParameter, -300, -50)
    disc_col.set_editor_property("parameter_name", "Color")
    disc_col.set_editor_property("default_value", unreal.LinearColor(0.7, 0.25, 1.0, 0.35))
    unreal.MaterialEditingLibrary.connect_material_property(disc_col, "", unreal.MaterialProperty.MP_EMISSIVE_COLOR)
    
    disc_op = unreal.MaterialEditingLibrary.create_material_expression(m_disc, unreal.MaterialExpressionConstant, -300, 150)
    disc_op.set_editor_property("r", 0.35)
    unreal.MaterialEditingLibrary.connect_material_property(disc_op, "", unreal.MaterialProperty.MP_OPACITY)
    
    unreal.MaterialEditingLibrary.recompile_material(m_disc)
    unreal.EditorAssetLibrary.save_loaded_asset(m_disc)
    print(">>> M_TranslucentDisc created and saved successfully! <<<")

print(">>> ALL COMMON MATERIALS SETUP COMPLETE <<<")
unreal.SystemLibrary.execute_console_command(None, "QUIT_EDITOR")
