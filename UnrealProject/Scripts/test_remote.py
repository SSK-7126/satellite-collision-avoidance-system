import sys
import time

sys.path.append(r"C:\Program Files\Epic Games\UE_5.7\Engine\Plugins\Experimental\PythonScriptPlugin\Content\Python")
import remote_execution

remote = remote_execution.RemoteExecution()
remote.start()
time.sleep(1.0)

print(f"Discovered remote nodes: {len(remote.remote_nodes)}")
for node in remote.remote_nodes:
    print(f"Node: {node['node_id']} - {node.get('project_name')} - {node.get('engine_version')}")

if remote.remote_nodes:
    node = remote.remote_nodes[0]
    remote.open_command_connection(node["node_id"])
    cmd = """
import unreal
world = unreal.EditorLevelLibrary.get_editor_world()
print(f"LIVE EDITOR WORLD: {world.get_name() if world else 'None'}")
actors = unreal.EditorLevelLibrary.get_all_level_actors()
print(f"TOTAL LEVEL ACTORS IN GUI: {len(actors)}")
for a in actors:
    cname = a.get_class().get_name()
    if 'Actor' in cname or 'Visualizer' in cname or 'Simulation' in cname:
        print(f"  Actor: {a.get_actor_label()} ({cname}) at {a.get_actor_location()}")
"""
    res = remote.run_command(cmd)
    print("OUTPUT FROM RUNNING UNREAL EDITOR GUI:")
    for out in res.get("output", []):
        print(" ", out.get("output"))

remote.stop()

