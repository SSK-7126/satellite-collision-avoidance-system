import sys
import time
import os

sys.path.append(r"C:\Program Files\Epic Games\UE_5.7\Engine\Plugins\Experimental\PythonScriptPlugin\Content\Python")
import remote_execution

remote = remote_execution.RemoteExecution()
remote.start()
time.sleep(1.0)

if not remote.remote_nodes:
    print("No remote node found!")
    sys.exit(1)

node = remote.remote_nodes[0]
remote.open_command_connection(node["node_id"])

script = """
import unreal
import os

world = unreal.EditorLevelLibrary.get_editor_world()
all_actors = unreal.EditorLevelLibrary.get_all_level_actors()

mgrs = [a for a in all_actors if isinstance(a, unreal.OrbitSimulationManager)]
paths = [a for a in all_actors if isinstance(a, unreal.OrbitPathActor)]
earth_actors = [a for a in all_actors if isinstance(a, unreal.EarthActor)]
sat_actors = [a for a in all_actors if isinstance(a, unreal.SatelliteActor)]
deb_actors = [a for a in all_actors if isinstance(a, unreal.DebrisActor)]
conj_actors = [a for a in all_actors if isinstance(a, unreal.ConjunctionVisualizer)]
man_actors = [a for a in all_actors if isinstance(a, unreal.ManoeuvreVisualizer)]
cam_actors = [a for a in all_actors if isinstance(a, unreal.CameraActor)]

print(f"Mgr: {len(mgrs)}, Paths: {len(paths)}, Earth: {len(earth_actors)}, Sat: {len(sat_actors)}, Deb: {len(deb_actors)}, Conj: {len(conj_actors)}, Man: {len(man_actors)}, Cam: {len(cam_actors)}")

if mgrs:
    sim_mgr = mgrs[0]
    payload_path = (unreal.Paths.project_dir() + "../D2/visualization/unreal_simulation_payload.json").replace("\\\\", "/")
    init_res = sim_mgr.initialize_simulation_from_payload(payload_path)
    print("InitializeSimulationFromPayload result:", init_res)

for p in paths:
    sm_comps = p.get_components_by_class(unreal.SplineMeshComponent)
    print(f"Path '{p.get_actor_label()}': Spline points = {p.get_editor_property('trajectory_spline').get_number_of_spline_points()}, SplineMeshComponents = {len(sm_comps)}")

# Check visualizers
if conj_actors:
    c = conj_actors[0]
    tca_mesh = c.get_editor_property("tca_marker_sphere").get_editor_property("static_mesh")
    dist_mesh = c.get_editor_property("miss_distance_line").get_editor_property("static_mesh")
    plane_mesh = c.get_editor_property("encounter_plane_disc").get_editor_property("static_mesh")
    print(f"ConjunctionVisualizer meshes: TCA={tca_mesh is not None}, Line={dist_mesh is not None}, Plane={plane_mesh is not None}")

if man_actors:
    m = man_actors[0]
    ring_mesh = m.get_editor_property("burn_marker_ring").get_editor_property("static_mesh")
    arrow_mesh = m.get_editor_property("delta_v_arrow").get_editor_property("static_mesh")
    print(f"ManoeuvreVisualizer meshes: Ring={ring_mesh is not None}, Arrow={arrow_mesh is not None}")
"""

res = remote.run_command(script)
print("Execution result:")
for out in res.get("output", []):
    print(" ", out.get("output"))

remote.stop()

