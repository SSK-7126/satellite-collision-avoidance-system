import sys
import time

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

world = unreal.EditorLevelLibrary.get_editor_world()
for a in unreal.EditorLevelLibrary.get_all_level_actors():
    if isinstance(a, unreal.DirectionalLight):
        comp = a.get_component_by_class(unreal.DirectionalLightComponent)
        comp.set_editor_property("intensity", 12.0)
        # Point sunlight towards Earth and orbital encounter from the camera side
        a.set_actor_rotation(unreal.Rotator(pitch=-35.0, yaw=-65.0, roll=0.0), False)
        print("Updated DirectionalLight rotation and intensity.")
    elif isinstance(a, unreal.SkyLight):
        comp = a.get_component_by_class(unreal.SkyLightComponent)
        comp.set_editor_property("intensity", 4.0)
        comp.set_editor_property("light_color", unreal.Color(r=180, g=210, b=255, a=255))
        print("Updated SkyLight.")
"""

res = remote.run_command(script)
for out in res.get("output", []):
    print(out.get("output"))

remote.stop()

