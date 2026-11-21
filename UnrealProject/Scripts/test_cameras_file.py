"""
test_cameras_file.py
"""
import unreal
import os

out_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "../Saved/camera_test_results.txt"))
os.makedirs(os.path.dirname(out_path), exist_ok=True)
f = open(out_path, "w", encoding="utf-8")

level_path = "/Game/Scenarios/CollisionAvoidanceDemo"
unreal.EditorLevelLibrary.load_level(level_path)
all_actors = unreal.EditorLevelLibrary.get_all_level_actors()
sim_mgr = [a for a in all_actors if isinstance(a, unreal.OrbitSimulationManager)][0]
cameras = [a for a in all_actors if isinstance(a, unreal.CameraActor)]

f.write(f"Cameras in Level ({len(cameras)} total):\n")
for i, c in enumerate(cameras):
    f.write(f"  [{i}] {c.get_actor_label()}\n")

sim_mgr.camera_views = cameras
f.write("\nTesting CycleCameraView:\n")
for i in range(len(cameras)):
    sim_mgr.cycle_camera_view()
    idx = sim_mgr.current_camera_index
    f.write(f"  Cycle {i+1}: idx={idx} -> {cameras[idx].get_actor_label()}\n")

f.write("\nTesting SetCameraForStep (Steps 1 to 8):\n")
for s in range(1, 9):
    sim_mgr.set_camera_for_step(s)
    idx = sim_mgr.current_camera_index
    f.write(f"  Step {s}: idx={idx} -> {cameras[idx].get_actor_label()}\n")

f.close()
unreal.SystemLibrary.execute_console_command(None, "QUIT_EDITOR")
