"""
execute_safe_visual_capture.py
==============================
Automates the visual verification capture safely:
1. Launches UnrealEditor.exe with -nosound and windowed resolution.
2. Waits with a strict timeout (max 120s) for Python Remote Execution.
3. Renders the 5 required views:
   1. Default Overview
   2. Satellite Close-up
   3. Debris Close-up
   4. Earth Close-up
   5. Full Dashboard with Step 6
4. Exports 1920x1080 renders and closes Unreal Editor cleanly.
"""
import subprocess
import time
import os
import sys
import shutil

sys.path.append(r"C:\Program Files\Epic Games\UE_5.7\Engine\Plugins\Experimental\PythonScriptPlugin\Content\Python")
import remote_execution

UE_EXE = r"C:\Program Files\Epic Games\UE_5.7\Engine\Binaries\Win64\UnrealEditor.exe"
PROJECT_FILE = r"C:\Users\Sriram Krovi\satellite-collision-avoidance-system\UnrealProject\SatelliteAvoidance.uproject"
OUT_DIR = r"C:\Users\Sriram Krovi\satellite-collision-avoidance-system\Project_Deliverables\Windows_Package\Reports\Screenshots"
ARTIFACTS_DIR = r"C:\Users\Sriram Krovi\.gemini\antigravity\brain\cdd0c206-fcf3-4310-8916-ebe32a293b35"

os.makedirs(OUT_DIR, exist_ok=True)
os.makedirs(ARTIFACTS_DIR, exist_ok=True)

UE_SCRIPT = r"""
import unreal
import math
import os

print(">>> [RENDER SUITE] Loading /Game/Scenarios/CollisionAvoidanceDemo...")
level_path = "/Game/Scenarios/CollisionAvoidanceDemo"
unreal.EditorLevelLibrary.load_level(level_path)
world = unreal.EditorLevelLibrary.get_editor_world()
all_actors = unreal.EditorLevelLibrary.get_all_level_actors()

sat = None
deb = None
earth = None
sun = None
sat_nom_path = None
deb_path = None
sat_mod_path = None
conj_viz = None
man_viz = None

for a in all_actors:
    lbl = a.get_actor_label()
    if isinstance(a, unreal.SatelliteActor):
        sat = a
    elif isinstance(a, unreal.DebrisActor):
        deb = a
    elif isinstance(a, unreal.EarthActor):
        earth = a
    elif isinstance(a, unreal.DirectionalLight):
        sun = a
    elif lbl == "OrbitPath_SatelliteNominal":
        sat_nom_path = a
    elif lbl == "OrbitPath_DebrisNominal":
        deb_path = a
    elif lbl == "OrbitPath_SatelliteModified":
        sat_mod_path = a
    elif lbl == "Conjunction_Visualizer" or isinstance(a, unreal.ConjunctionVisualizer):
        conj_viz = a
    elif lbl == "Manoeuvre_Visualizer" or isinstance(a, unreal.ManoeuvreVisualizer):
        man_viz = a

# 1. Earth Setup: centered in background, visual radius 7,500 uu
if earth:
    earth.set_actor_location(unreal.Vector(0.0, 0.0, 0.0), False, False)
    em = earth.get_editor_property("earth_mesh")
    m_earth = unreal.EditorAssetLibrary.load_asset("/Game/Earth/M_Earth")
    if em and m_earth:
        em.set_material(0, m_earth)
        em.set_relative_scale3d(unreal.Vector(75.0, 75.0, 75.0))
    atm = earth.get_editor_property("atmosphere_mesh")
    m_atmo = unreal.EditorAssetLibrary.load_asset("/Game/Earth/M_Atmosphere")
    if atm and m_atmo:
        atm.set_material(0, m_atmo)
        atm.set_relative_scale3d(unreal.Vector(77.0, 77.0, 77.0))
        atm.set_visibility(True)
        atm.set_hidden_in_game(False)

# 2. Materials
m_solid = unreal.EditorAssetLibrary.load_asset("/Game/Common/M_SolidColor")

# 3. Satellite: Scaled 5.5x, bold foreground presence
sat_pos = unreal.Vector(68828.0, -12756.0, 0.0)
if sat:
    sat.set_actor_location_and_rotation(sat_pos, unreal.Rotator(12.0, -65.0, 5.0), False, False)
    vroot = sat.get_editor_property("visual_root")
    if vroot:
        vroot.set_relative_scale3d(unreal.Vector(5.5, 5.5, 5.5))
    sat_body = sat.get_editor_property("satellite_body")
    if sat_body and m_solid:
        mb = sat_body.create_dynamic_material_instance(0, m_solid)
        mb.set_vector_parameter_value("Color", unreal.LinearColor(0.98, 0.82, 0.28, 1.0))
        mb.set_scalar_parameter_value("Metallic", 0.92)
        mb.set_scalar_parameter_value("Roughness", 0.18)
        mb.set_scalar_parameter_value("EmissiveMultiplier", 0.45)

# 4. Debris: Scaled 4.8x, bold mid-right presence
deb_pos = unreal.Vector(68828.0, -12838.0, 0.0)
if deb:
    deb.set_actor_location_and_rotation(deb_pos, unreal.Rotator(25.0, 40.0, 15.0), False, False)
    vroot = deb.get_editor_property("visual_root")
    if vroot:
        vroot.set_relative_scale3d(unreal.Vector(4.8, 4.8, 4.8))
    deb_mesh = deb.get_editor_property("debris_mesh")
    if deb_mesh and m_solid:
        mdb = deb_mesh.create_dynamic_material_instance(0, m_solid)
        mdb.set_vector_parameter_value("Color", unreal.LinearColor(0.85, 0.85, 0.88, 1.0))
        mdb.set_scalar_parameter_value("Metallic", 0.80)
        mdb.set_scalar_parameter_value("Roughness", 0.35)
        mdb.set_scalar_parameter_value("EmissiveMultiplier", 0.25)

# 5. Hide pink encounter disc on ConjunctionVisualizer
if conj_viz:
    disc = conj_viz.get_editor_property("encounter_plane_disc")
    if disc:
        disc.set_visibility(False)
        disc.set_hidden_in_game(True)

# 6. Show modified trajectory
if sat_mod_path:
    sat_mod_path.set_actor_hidden_in_game(False)

out_dir = "C:/Users/Sriram Krovi/satellite-collision-avoidance-system/Project_Deliverables/Windows_Package/Reports/Screenshots"
os.makedirs(out_dir, exist_ok=True)

def capture_view(cam_pos, cam_rot, fov, filename):
    cap = unreal.EditorLevelLibrary.spawn_actor_from_class(unreal.SceneCapture2D, cam_pos, cam_rot)
    comp = cap.get_editor_property("capture_component2d")
    comp.set_editor_property("fov_angle", fov)
    comp.set_editor_property("capture_source", unreal.SceneCaptureSource.SCS_FINAL_COLOR_LDR)
    pps = comp.get_editor_property("post_process_settings")
    pps.set_editor_property("override_auto_exposure_bias", True)
    pps.set_editor_property("auto_exposure_bias", 0.0)
    comp.set_editor_property("post_process_settings", pps)
    rt = unreal.RenderingLibrary.create_render_target2d(world, 1920, 1080, unreal.TextureRenderTargetFormat.RTF_RGBA8)
    comp.set_editor_property("texture_target", rt)
    comp.capture_scene()
    unreal.RenderingLibrary.export_render_target(world, rt, out_dir, filename)
    unreal.EditorLevelLibrary.destroy_actor(cap)
    print(f">>> [RENDERED] {filename}")

# View 1: Default Overview
# Camera above orbit looking toward Earth and spacecraft arc
cam1_pos = unreal.Vector(69500.0, -32000.0, 12500.0)
cam1_rot = unreal.Rotator(pitch=-16.0, yaw=148.0, roll=0.0)
capture_view(cam1_pos, cam1_rot, 48.0, "View1_DefaultOverview.png")

# View 2: Primary Satellite Close-up
cam2_pos = unreal.Vector(68650.0, -12500.0, 300.0)
cam2_rot = unreal.Rotator(pitch=-18.0, yaw=-45.0, roll=0.0)
capture_view(cam2_pos, cam2_rot, 40.0, "View2_SatelliteCloseUp.png")

# View 3: Debris Close-up
cam3_pos = unreal.Vector(68680.0, -12600.0, 250.0)
cam3_rot = unreal.Rotator(pitch=-15.0, yaw=-55.0, roll=0.0)
capture_view(cam3_pos, cam3_rot, 42.0, "View3_DebrisCloseUp.png")

# View 4: Earth Close-up (Framing spherical Earth and atmosphere)
cam4_pos = unreal.Vector(28000.0, -18000.0, 8000.0)
cam4_rot = unreal.Rotator(pitch=-15.0, yaw=148.0, roll=0.0)
capture_view(cam4_pos, cam4_rot, 35.0, "View4_EarthCloseUp.png")

# View 5: Step 6 Manoeuvre Burn Scene (for full dashboard)
cam5_pos = unreal.Vector(69500.0, -32000.0, 12500.0)
cam5_rot = unreal.Rotator(pitch=-16.0, yaw=148.0, roll=0.0)
capture_view(cam5_pos, cam5_rot, 48.0, "View5_Step6_Scene.png")

print(">>> [RENDER SUITE] All 5 views rendered successfully!")
unreal.SystemLibrary.quit_editor()
"""

def main():
    print(">>> 1. Launching Unreal Editor GUI with -nosound...")
    proc = subprocess.Popen([UE_EXE, PROJECT_FILE, "-nosound", "-windowed", "-ResX=1280", "-ResY=720"])
    pid = proc.pid
    print(f">>> Unreal Editor process launched (PID: {pid}). Waiting for Remote Execution...")

    remote = remote_execution.RemoteExecution()
    remote.start()
    connected = False
    start_t = time.time()
    max_wait = 150 # 2.5 minutes timeout (well below 5-minute limit)

    while (time.time() - start_t) < max_wait:
        if remote.remote_nodes:
            connected = True
            node_id = remote.remote_nodes[0]["node_id"]
            print(f">>> Connected to Unreal Editor node: {node_id} after {time.time() - start_t:.1f}s!")
            break
        time.sleep(2.0)
        print(f"    Waiting for editor initialization... ({time.time() - start_t:.1f}s elapsed)")

    if not connected:
        print(">>> [TIMEOUT] Unreal Editor did not open Remote Execution within timeout.")
        remote.stop()
        proc.kill()
        return False

    print(">>> 2. Executing render suite in Unreal Editor...")
    node_id = remote.remote_nodes[0]["node_id"]
    remote.open_command_connection(node_id)
    result = remote.run_command(UE_SCRIPT)
    for entry in result.get("output", []):
        msg = entry.get("output", "")
        print(f"    [UE] {msg}", end="")
    remote.stop()

    print(">>> 3. Waiting for editor process to exit cleanly...")
    try:
        proc.wait(timeout=30)
    except subprocess.TimeoutExpired:
        proc.kill()

    print(">>> 4. Verifying exported files...")
    views = [
        "View1_DefaultOverview.png",
        "View2_SatelliteCloseUp.png",
        "View3_DebrisCloseUp.png",
        "View4_EarthCloseUp.png",
        "View5_Step6_Scene.png",
    ]
    all_ok = True
    for v in views:
        fpath = os.path.join(OUT_DIR, v)
        art_path = os.path.join(ARTIFACTS_DIR, v)
        if os.path.exists(fpath):
            shutil.copy(fpath, art_path)
            print(f"    [OK] {v} ({os.path.getsize(fpath)} bytes) -> copied to artifacts")
        else:
            print(f"    [MISSING] {v}")
            all_ok = False

    return all_ok

if __name__ == "__main__":
    t0 = time.time()
    success = main()
    print(f">>> Script completed in {time.time() - t0:.1f}s with success={success}")
    sys.exit(0 if success else 1)
