import unreal
import os

level_path = "/Game/Scenarios/CollisionAvoidanceDemo"
unreal.EditorLevelLibrary.load_level(level_path)
world = unreal.EditorLevelLibrary.get_editor_world()
all_actors = unreal.EditorLevelLibrary.get_all_level_actors()

# Clean landscape
for a in all_actors:
    cname = a.get_class().get_name()
    if "Landscape" in cname or cname in ["VolumetricCloud", "ExponentialHeightFog", "SkyAtmosphere"]:
        a.set_actor_hidden_in_game(True)
    elif a.get_actor_label() == "SM_SkySphere":
        a.set_actor_hidden_in_game(True)

earth = [a for a in all_actors if isinstance(a, unreal.EarthActor)][0]
dir_light = [a for a in all_actors if isinstance(a, unreal.DirectionalLight)][0]
sky_light = [a for a in all_actors if isinstance(a, unreal.SkyLight)][0]

m_earth = unreal.EditorAssetLibrary.load_asset("/Game/Earth/M_Earth")
m_atmo = unreal.EditorAssetLibrary.load_asset("/Game/Earth/M_Atmosphere")
t_earth = unreal.EditorAssetLibrary.load_asset("/Game/Earth/T_Earth_Day")

em = earth.get_editor_property("earth_mesh")
atm = earth.get_editor_property("atmosphere_mesh")

# Let's inspect em materials and properties
print("em static mesh:", em.get_editor_property("static_mesh"))
print("em materials num:", em.get_num_materials())
for i in range(em.get_num_materials()):
    print(f"em mat {i}:", em.get_material(i))

print("atm static mesh:", atm.get_editor_property("static_mesh"))
for i in range(atm.get_num_materials()):
    print(f"atm mat {i}:", atm.get_material(i))

# Test 1: Set M_Earth directly on EarthMesh, HIDE atmosphere mesh
em.set_material(0, m_earth)
atm.set_hidden_in_game(True)
atm.set_visibility(False)

dl_comp = dir_light.get_component_by_class(unreal.DirectionalLightComponent)
dl_comp.set_editor_property("atmosphere_sun_light", False)
dl_comp.set_editor_property("use_temperature", False)
dl_comp.set_editor_property("light_color", unreal.Color(255, 255, 255, 255))
dl_comp.set_editor_property("intensity", 8.0)

sl_comp = sky_light.get_component_by_class(unreal.SkyLightComponent)
sl_comp.set_editor_property("intensity", 2.0)

cam_loc = unreal.Vector(115000.0, -45000.0, 32000.0)
cam_rot = unreal.Rotator(roll=0.0, pitch=-19.0, yaw=152.0)

cap = unreal.EditorLevelLibrary.spawn_actor_from_class(unreal.SceneCapture2D, cam_loc, cam_rot)
comp = cap.get_editor_property("capture_component2d")
comp.set_editor_property("fov_angle", 65.0)
comp.set_editor_property("capture_source", unreal.SceneCaptureSource.SCS_FINAL_COLOR_LDR)
pps = comp.get_editor_property("post_process_settings")
pps.set_editor_property("override_auto_exposure_bias", True)
pps.set_editor_property("auto_exposure_bias", 0.0)
comp.set_editor_property("post_process_settings", pps)

rt = unreal.RenderingLibrary.create_render_target2d(world, 1920, 1080, unreal.TextureRenderTargetFormat.RTF_RGBA8)
comp.set_editor_property("texture_target", rt)

out_dir = (unreal.Paths.project_saved_dir() + "Screenshots/WindowsEditor").replace("\\", "/")

# Case A: Sun at pitch=-30, yaw=-60 (as in capture_earth_verification.py)
dir_light.set_actor_rotation(unreal.Rotator(pitch=-30.0, yaw=-60.0, roll=0.0), False)
comp.capture_scene()
unreal.RenderingLibrary.export_render_target(world, rt, out_dir, "Test_Earth_NoAtmo_YawM60.png")

# Case B: Sun at pitch=-22, yaw=148
dir_light.set_actor_rotation(unreal.Rotator(pitch=-22.0, yaw=148.0, roll=0.0), False)
comp.capture_scene()
unreal.RenderingLibrary.export_render_target(world, rt, out_dir, "Test_Earth_NoAtmo_Yaw148.png")

unreal.EditorLevelLibrary.destroy_actor(cap)
print("Finished test_earth_fix.py")
unreal.SystemLibrary.execute_console_command(None, "QUIT_EDITOR")
