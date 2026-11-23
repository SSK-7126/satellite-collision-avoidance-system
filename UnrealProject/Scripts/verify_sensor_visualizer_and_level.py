"""
verify_sensor_visualizer_and_level.py
======================================
Automated in-engine headless verification for Unreal Engine 5.7:
1. Verify that unreal.SensorVisualizerComponent is registered in engine reflection.
2. Load /Game/Scenarios/CollisionAvoidanceDemo level.
3. Verify that all key actors (Satellite, Debris, Paths, Cameras, SimulationManager) exist.
4. Instantiate SensorVisualizerComponent, attach to satellite, and test UpdateTrackingState.
5. Verify 8-step camera playback and visualizer state transitions.
"""

import unreal
import sys
import os

out_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "../Saved/sensor_verification_output.txt"))
os.makedirs(os.path.dirname(out_path), exist_ok=True)
out_f = open(out_path, "w", encoding="utf-8")

def log(msg=""):
    print(msg)
    unreal.log(msg)
    sys.stdout.flush()
    out_f.write(msg + "\n")
    out_f.flush()

log("=" * 80)
log("IN-ENGINE VERIFICATION: SENSOR VISUALIZER & COLLISION AVOIDANCE DEMO")
log("=" * 80)

# 1. Verify SensorVisualizerComponent in Unreal Python reflection
try:
    sensor_cls = unreal.SensorVisualizerComponent
    log(f"[PASS] SensorVisualizerComponent found in engine reflection: {sensor_cls}")
except AttributeError as e:
    log(f"[FAIL] SensorVisualizerComponent not found in unreal module: {e}")
    sys.exit(1)

# 2. Load Demo Level
level_path = "/Game/Scenarios/CollisionAvoidanceDemo"
log(f"[INFO] Loading Level: {level_path}")
unreal.EditorLevelLibrary.load_level(level_path)
world = unreal.EditorLevelLibrary.get_editor_world()
all_actors = unreal.EditorLevelLibrary.get_all_level_actors()
log(f"[PASS] Level loaded successfully. Total actors in level: {len(all_actors)}")

# 3. Verify Actor classes
sat_actors = [a for a in all_actors if isinstance(a, unreal.SatelliteActor)]
deb_actors = [a for a in all_actors if isinstance(a, unreal.DebrisActor)]
sim_mgrs = [a for a in all_actors if isinstance(a, unreal.OrbitSimulationManager)]
paths = [a for a in all_actors if isinstance(a, unreal.OrbitPathActor)]
cameras = [a for a in all_actors if isinstance(a, unreal.CameraActor)]

log(f"  SatelliteActor count          : {len(sat_actors)}")
log(f"  DebrisActor count             : {len(deb_actors)}")
log(f"  OrbitSimulationManager count  : {len(sim_mgrs)}")
log(f"  OrbitPathActor count          : {len(paths)}")
log(f"  CameraActor count             : {len(cameras)}")

assert len(sat_actors) > 0, "No SatelliteActor found!"
assert len(deb_actors) > 0, "No DebrisActor found!"
assert len(sim_mgrs) > 0, "No OrbitSimulationManager found!"
assert len(paths) >= 2, f"Expected at least 2 OrbitPathActor instances, found {len(paths)}"
assert len(cameras) >= 6, f"Expected at least 6 CameraActor instances, found {len(cameras)}"
log("[PASS] All required level actors confirmed present.")

# 4. Instantiate and test SensorVisualizerComponent on Satellite
sat = sat_actors[0]
log(f"[INFO] Instantiating SensorVisualizerComponent on {sat.get_actor_label()}...")

comp = unreal.new_object(unreal.SensorVisualizerComponent, sat, "RuntimeSensorVisualizer")
comp.attach_to_component(
    sat.root_component,
    unreal.Name(),
    unreal.AttachmentRule.KEEP_RELATIVE,
    unreal.AttachmentRule.KEEP_RELATIVE,
    unreal.AttachmentRule.KEEP_RELATIVE,
    False
)

fov = comp.get_editor_property("field_of_view_deg")
max_range = comp.get_editor_property("max_range_ue")
sensor_label = comp.get_editor_property("sensor_type_label")
log(f"  Component Default FOV        : {fov} deg")
log(f"  Component Default Max Range  : {max_range} uu")
log(f"  Component Sensor Type        : {sensor_label}")

# Test UpdateTrackingState with bInTargetVisible
deb = deb_actors[0]
target_pos = deb.get_actor_location()
log(f"[INFO] Invoking UpdateTrackingState with TargetPos={target_pos}, bInTargetVisible=True...")

comp.update_tracking_state(target_pos, True, "OPTICAL_TRACKING_LOCKED")

is_tracking = comp.get_editor_property("is_tracking")
target_in_fov = comp.get_editor_property("target_in_fov")
tracking_status = comp.get_editor_property("tracking_status")
current_target_pos = comp.get_editor_property("current_target_position_ue")

log(f"  Updated bIsTracking          : {is_tracking}")
log(f"  Updated bTargetInFov         : {target_in_fov}")
log(f"  Updated TrackingStatus       : {tracking_status}")
log(f"  Updated TargetPosition       : {current_target_pos}")

assert is_tracking is True, "Expected bIsTracking to be True!"
assert target_in_fov is True, "Expected bTargetInFov to be True!"
assert str(tracking_status) == "OPTICAL_TRACKING_LOCKED", f"Unexpected status: {tracking_status}"
log("[PASS] SensorVisualizerComponent runtime execution verified.")

# 5. Verify camera step sequence and simulation manager
sim_mgr = sim_mgrs[0]
sim_mgr.camera_views = cameras

expected_cameras = {
    1: "Camera_Earth_Overview",
    2: "Camera_Satellite_Detail",
    3: "Camera_Encounter_Overview",
    4: "Camera_Conjunction_TCA",
    5: "Camera_Satellite_Detail",
    6: "Camera_Manoeuvre_Burn",
    7: "Camera_Encounter_Overview",
    8: "Camera_Earth_Overview"
}

log("[INFO] Verifying 8-step camera playback...")
for step_idx in range(1, 9):
    sim_mgr.set_camera_for_step(step_idx)
    active_idx = sim_mgr.current_camera_index
    active_cam = cameras[active_idx]
    active_label = active_cam.get_actor_label()
    expected = expected_cameras[step_idx]
    assert active_label == expected, f"Step {step_idx}: expected {expected}, got {active_label}"
    log(f"  Step {step_idx}: Camera [{active_label}] (Index {active_idx}) -> OK")

log("[PASS] All 8 milestone camera views confirmed working.")
log("=" * 80)
log("IN-ENGINE SENSOR VISUALIZER & LEVEL INTEGRATION VERIFIED SUCCESSFULLY")
log("=" * 80)
out_f.close()
