import unreal
import math
import os
import shutil

print(">>> [TEST T73] Starting script...")
level_path = "/Game/Scenarios/CollisionAvoidanceDemo"
unreal.EditorLevelLibrary.load_level(level_path)
world = unreal.EditorLevelLibrary.get_editor_world()
all_actors = unreal.EditorLevelLibrary.get_all_level_actors()

sat = None
deb = None
cam = None

for a in all_actors:
    lbl = a.get_actor_label()
    if isinstance(a, unreal.SatelliteActor):
        sat = a
    elif isinstance(a, unreal.DebrisActor):
        deb = a
    elif lbl == "Camera_Earth_Overview":
        cam = a

print(f">>> Found sat: {sat is not None}, deb: {deb is not None}, cam: {cam is not None}")

# Fix scale to 1.0
sat.set_actor_scale3d(unreal.Vector(1.0, 1.0, 1.0))
deb.set_actor_scale3d(unreal.Vector(1.0, 1.0, 1.0))

sat_vroot = sat.get_editor_property("visual_root")
sat_body = sat.get_editor_property("satellite_body")
if sat_vroot and sat_body:
    sat_body.attach_to_component(sat_vroot, unreal.Name(""), unreal.AttachmentRule.KEEP_RELATIVE, unreal.AttachmentRule.KEEP_RELATIVE, unreal.AttachmentRule.KEEP_RELATIVE, False)
    sat_body.set_editor_property("relative_location", unreal.Vector(0.0, 0.0, 0.0))
    sat_vroot.set_editor_property("relative_scale3d", unreal.Vector(0.35, 0.35, 0.35))
    sat.set_editor_property("visual_mesh_scale", 0.35)

deb_vroot = deb.get_editor_property("visual_root")
deb_mesh = deb.get_editor_property("debris_mesh")
if deb_vroot and deb_mesh:
    deb_mesh.attach_to_component(deb_vroot, unreal.Name(""), unreal.AttachmentRule.KEEP_RELATIVE, unreal.AttachmentRule.KEEP_RELATIVE, unreal.AttachmentRule.KEEP_RELATIVE, False)
    deb_mesh.set_editor_property("relative_location", unreal.Vector(0.0, 0.0, 0.0))
    deb_vroot.set_editor_property("relative_scale3d", unreal.Vector(0.40, 0.40, 0.40))
    deb.set_editor_property("visual_mesh_scale", 0.40)

# Set exact positions at T=73.0s
sat_pos = unreal.Vector(69789.25, -5427.70, 0.0)
deb_pos = unreal.Vector(69789.28, -5520.21, 0.0)
sat.set_actor_location_and_rotation(sat_pos, unreal.Rotator(0.0, -90.0, 0.0), False, False)
deb.set_actor_location_and_rotation(deb_pos, unreal.Rotator(35.0, 45.0, 20.0), False, False)

# Compute Framing using the proven elevated flank vantage
mid = (sat_pos + deb_pos) * 0.5
r_dir = unreal.Vector(mid.x, mid.y, 0.0).normal()
v_dir = unreal.Vector(-r_dir.y, r_dir.x, 0.0).normal()
if v_dir.y > 0:
    v_dir = v_dir * -1.0
z_dir = unreal.Vector(0.0, 0.0, 1.0)

cam_pos = mid + (r_dir * 300.0) - (v_dir * 870.0) + (z_dir * 750.0)
target = mid + (v_dir * 30.0)
to_tgt = target - cam_pos
yaw = math.degrees(math.atan2(to_tgt.y, to_tgt.x))
pitch = math.degrees(math.atan2(to_tgt.z, math.sqrt(to_tgt.x**2 + to_tgt.y**2)))
cam_rot = unreal.Rotator(pitch=pitch, yaw=yaw, roll=0.0)

print(f">>> CamPos: {cam_pos}, CamRot: {cam_rot}")

if cam:
    cam.set_actor_location_and_rotation(cam_pos, cam_rot, False, False)
    cc = cam.get_component_by_class(unreal.CameraComponent)
    if cc:
        cc.set_editor_property("field_of_view", 48.0)

cap = unreal.EditorLevelLibrary.spawn_actor_from_class(unreal.SceneCapture2D, cam_pos, cam_rot)
comp = cap.get_editor_property("capture_component2d")
comp.set_editor_property("fov_angle", 48.0)
comp.set_editor_property("capture_source", unreal.SceneCaptureSource.SCS_FINAL_COLOR_LDR)

pps = comp.get_editor_property("post_process_settings")
pps.set_editor_property("override_auto_exposure_bias", True)
pps.set_editor_property("auto_exposure_bias", 0.0)
comp.set_editor_property("post_process_settings", pps)

rt = unreal.RenderingLibrary.create_render_target2d(world, 1920, 1080, unreal.TextureRenderTargetFormat.RTF_RGBA8)
comp.set_editor_property("texture_target", rt)
comp.capture_scene()

out_dir = (unreal.Paths.project_saved_dir() + "Screenshots/WindowsEditor/TestT73").replace("\\", "/")
os.makedirs(out_dir, exist_ok=True)
png = "Test_T73_Capture.png"
unreal.RenderingLibrary.export_render_target(world, rt, out_dir, png)
unreal.EditorLevelLibrary.destroy_actor(cap)

art_file = "C:/Users/Sriram Krovi/.gemini/antigravity/brain/7d36e17b-846d-4a94-9bbc-4bf33eb09d71/" + png
src_file = os.path.join(out_dir, png)
if os.path.exists(src_file):
    shutil.copy(src_file, art_file)
    print(f">>> SUCCESS! Exported and copied to: {art_file}, Size: {os.path.getsize(art_file)}")
else:
    print(f">>> FAILED: src_file not found at {src_file}")
