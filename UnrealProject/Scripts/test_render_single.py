import unreal
import os

print(">>> TEST RENDER SINGLE STARTING <<<")

level_path = "/Game/Scenarios/CollisionAvoidanceDemo"
unreal.EditorLevelLibrary.load_level(level_path)
world = unreal.EditorLevelLibrary.get_editor_world()
all_actors = unreal.EditorLevelLibrary.get_all_level_actors()

# Find Earth and Satellite
earth = [a for a in all_actors if isinstance(a, unreal.EarthActor)][0]
sat = [a for a in all_actors if isinstance(a, unreal.SatelliteActor)][0]

m_earth = unreal.EditorAssetLibrary.load_asset("/Game/Earth/M_Earth")
m_atmo = unreal.EditorAssetLibrary.load_asset("/Game/Earth/M_Atmosphere")
m_solid = unreal.EditorAssetLibrary.load_asset("/Game/Common/M_SolidColor")

print(f"Loaded assets - Earth: {m_earth is not None}, Atmo: {m_atmo is not None}, Solid: {m_solid is not None}")

# Direct material assignment
em = earth.get_editor_property("earth_mesh")
am = earth.get_editor_property("atmosphere_mesh")
em.set_material(0, m_earth)
am.set_material(0, m_atmo)
am.set_relative_scale3d(unreal.Vector(1.015, 1.015, 1.015))

# Satellite C++ materials
sat.set_visual_state(unreal.SatelliteVisualState.NOMINAL_FLIGHT)

# Configure sunlight
for a in all_actors:
    if isinstance(a, unreal.DirectionalLight):
        comp = a.get_component_by_class(unreal.DirectionalLightComponent)
        comp.set_editor_property("intensity", 14.0)
        a.set_actor_rotation(unreal.Rotator(pitch=-22.0, yaw=148.0, roll=0.0), False)
    elif isinstance(a, unreal.SkyLight):
        comp = a.get_component_by_class(unreal.SkyLightComponent)
        comp.set_editor_property("intensity", 2.2)

out_dir = (unreal.Paths.project_saved_dir() + "Screenshots/WindowsEditor").replace("\\", "/")
os.makedirs(out_dir, exist_ok=True)

# Capture Earth Overview
cam_loc = unreal.Vector(115000.0, -45000.0, 32000.0)
cam_rot = unreal.Rotator(roll=0.0, pitch=-19.0, yaw=152.0)

capture_actor = unreal.EditorLevelLibrary.spawn_actor_from_class(unreal.SceneCapture2D, cam_loc, cam_rot)
comp = capture_actor.get_editor_property("capture_component2d")
comp.set_editor_property("fov_angle", 65.0)
comp.set_editor_property("capture_source", unreal.SceneCaptureSource.SCS_FINAL_COLOR_LDR)

pps = comp.get_editor_property("post_process_settings")
pps.set_editor_property("override_auto_exposure_bias", True)
pps.set_editor_property("auto_exposure_bias", 0.0)
comp.set_editor_property("post_process_settings", pps)

rt = unreal.RenderingLibrary.create_render_target2d(world, 1920, 1080, unreal.TextureRenderTargetFormat.RTF_RGBA8)
comp.set_editor_property("texture_target", rt)
comp.capture_scene()

unreal.RenderingLibrary.export_render_target(world, rt, out_dir, "Test_Single_Capture.png")
unreal.EditorLevelLibrary.destroy_actor(capture_actor)
print(f"Exported {out_dir}/Test_Single_Capture.png")

# Also capture satellite
sat_pos = unreal.Vector(70000.0, 0.0, 0.0)
sat.set_actor_location_and_rotation(sat_pos, unreal.Rotator(0.0, -90.0, 0.0), False, False)
sat_cam_loc = unreal.Vector(sat_pos.x + 650.0, sat_pos.y - 850.0, sat_pos.z + 450.0)

dx = sat_pos.x - sat_cam_loc.x
dy = sat_pos.y - sat_cam_loc.y
dz = sat_pos.z - sat_cam_loc.z
import math
yaw = math.degrees(math.atan2(dy, dx))
dist_xy = math.sqrt(dx*dx + dy*dy)
pitch = math.degrees(math.atan2(dz, dist_xy))
sat_cam_rot = unreal.Rotator(pitch=pitch, yaw=yaw, roll=0.0)

sat_cap = unreal.EditorLevelLibrary.spawn_actor_from_class(unreal.SceneCapture2D, sat_cam_loc, sat_cam_rot)
scomp = sat_cap.get_editor_property("capture_component2d")
scomp.set_editor_property("fov_angle", 42.0)
scomp.set_editor_property("capture_source", unreal.SceneCaptureSource.SCS_FINAL_COLOR_LDR)
scomp.set_editor_property("post_process_settings", pps)
scomp.set_editor_property("texture_target", rt)
scomp.capture_scene()

unreal.RenderingLibrary.export_render_target(world, rt, out_dir, "Test_Sat_Capture.png")
unreal.EditorLevelLibrary.destroy_actor(sat_cap)
print(f"Exported {out_dir}/Test_Sat_Capture.png")

print(">>> TEST RENDER SINGLE FINISHED <<<")
unreal.SystemLibrary.execute_console_command(None, "QUIT_EDITOR")
