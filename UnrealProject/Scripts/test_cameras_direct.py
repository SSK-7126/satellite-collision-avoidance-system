"""
test_cameras_direct.py
"""
import unreal

level_path = '/Game/Scenarios/CollisionAvoidanceDemo'
unreal.EditorLevelLibrary.load_level(level_path)
all_actors = unreal.EditorLevelLibrary.get_all_level_actors()
sim_mgr = [a for a in all_actors if isinstance(a, unreal.OrbitSimulationManager)][0]
cameras = [a for a in all_actors if isinstance(a, unreal.CameraActor)]

print("=" * 60)
print(f"Cameras in Level ({len(cameras)} total):")
for i, c in enumerate(cameras):
    print(f"  [{i}] {c.get_actor_label()}")

# Assign to sim_mgr
sim_mgr.camera_views = cameras
print("\nTesting CycleCameraView:")
for i in range(len(cameras)):
    sim_mgr.cycle_camera_view()
    idx = sim_mgr.current_camera_index
    print(f"  Cycle {i+1}: idx={idx} -> {cameras[idx].get_actor_label()}")

print("\nTesting SetCameraForStep (Steps 1 to 8):")
for s in range(1, 9):
    sim_mgr.set_camera_for_step(s)
    idx = sim_mgr.current_camera_index
    print(f"  Step {s}: idx={idx} -> {cameras[idx].get_actor_label()}")

print("=" * 60)
unreal.SystemLibrary.execute_console_command(None, "QUIT_EDITOR")
