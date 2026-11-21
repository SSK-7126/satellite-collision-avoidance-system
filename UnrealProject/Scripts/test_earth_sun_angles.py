import unreal
import os

level_path = "/Game/Scenarios/CollisionAvoidanceDemo"
unreal.EditorLevelLibrary.load_level(level_path)
world = unreal.EditorLevelLibrary.get_editor_world()
all_actors = unreal.EditorLevelLibrary.get_all_level_actors()

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

em = earth.get_editor_property("earth_mesh")
atm = earth.get_editor_property("atmosphere_mesh")
if em and m_earth:
    em.set_material(0, m_earth)
if atm and m_atmo:
    atm.set_material(0, m_atmo)
    radius_ue = earth.get_editor_property("earth_radius_ue")
    atmo_scale = (radius_ue * 1.015) / 50.0
    atm.set_world_scale3d(unreal.Vector(atmo_scale, atmo_scale, atmo_scale))
    atm.set_visibility(True)
    atm.set_hidden_in_game(False)

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

for yaw in [110.0, 130.0, 150.0]:
    dir_light.set_actor_rotation(unreal.Rotator(pitch=-20.0, yaw=yaw, roll=0.0), False)
    comp.capture_scene()
    unreal.RenderingLibrary.export_render_target(world, rt, out_dir, f"Test_Earth_Yaw_{int(yaw)}.png")
    print(f"Captured Test_Earth_Yaw_{int(yaw)}.png")

unreal.EditorLevelLibrary.destroy_actor(cap)
unreal.SystemLibrary.execute_console_command(None, "QUIT_EDITOR")
