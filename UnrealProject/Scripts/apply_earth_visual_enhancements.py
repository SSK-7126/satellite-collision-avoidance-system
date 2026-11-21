import sys
import time

sys.path.append(r"C:\Program Files\Epic Games\UE_5.7\Engine\Plugins\Experimental\PythonScriptPlugin\Content\Python")
import remote_execution

class Config(remote_execution.RemoteExecutionConfig):
    def __init__(self):
        super().__init__()
        self.multicast_bind_address = '0.0.0.0'

remote = remote_execution.RemoteExecution(Config())
remote.start()
time.sleep(1.0)

if not remote.remote_nodes:
    print("Error: Could not find Unreal Editor node!")
    sys.exit(1)

node = remote.remote_nodes[0]
print(f"Connecting to live Unreal Editor: {node['project_name']} (node: {node['node_id']})")
remote.open_command_connection(node["node_id"])

script = """
import unreal

world = unreal.EditorLevelLibrary.get_editor_world()
print("Updating visuals for level:", world.get_name())

all_actors = unreal.EditorLevelLibrary.get_all_level_actors()

# 1. Earth Actor material assignment
earth_actors = [a for a in all_actors if isinstance(a, unreal.EarthActor)]
if earth_actors:
    earth = earth_actors[0]
    print("Found EarthActor:", earth.get_actor_label())
    
    # Load materials
    m_earth = unreal.EditorAssetLibrary.load_asset("/Game/Earth/M_Earth")
    m_atmo = unreal.EditorAssetLibrary.load_asset("/Game/Earth/M_Atmosphere")
    t_earth = unreal.EditorAssetLibrary.load_asset("/Game/Earth/T_Earth_Day")
    
    print(f"Loaded assets - M_Earth: {m_earth is not None}, M_Atmosphere: {m_atmo is not None}, T_Earth_Day: {t_earth is not None}")
    
    # Update EarthMesh
    earth_mesh_comp = earth.get_component_by_class(unreal.StaticMeshComponent)
    # EarthMesh is RootComponent
    if m_earth:
        dyn_earth = unreal.MaterialInstanceDynamic.create(m_earth, earth)
        if t_earth:
            dyn_earth.set_texture_parameter_value("EarthTexture", t_earth)
        earth.get_editor_property("earth_mesh").set_material(0, dyn_earth)
        print("Assigned dynamic M_Earth to EarthMesh.")
    
    # Update AtmosphereMesh
    atmo_comp = earth.get_editor_property("atmosphere_mesh")
    if atmo_comp and m_atmo:
        dyn_atmo = unreal.MaterialInstanceDynamic.create(m_atmo, earth)
        dyn_atmo.set_vector_parameter_value("AtmosphereColor", unreal.LinearColor(0.2, 0.65, 1.0, 1.0))
        dyn_atmo.set_scalar_parameter_value("AtmosphereIntensity", 2.2)
        dyn_atmo.set_scalar_parameter_value("AtmosphereFresnelExp", 4.5)
        atmo_comp.set_material(0, dyn_atmo)
        # Ensure scale is 1.015 of Earth radius
        radius_ue = earth.get_editor_property("earth_radius_ue")
        atmo_scale = (radius_ue * 1.015) / 50.0
        atmo_comp.set_world_scale3d(unreal.Vector(atmo_scale, atmo_scale, atmo_scale))
        print("Assigned dynamic M_Atmosphere to AtmosphereMesh with subtle Fresnel rim.")

# 2. Background: Clean up terrestrial landscape template actors
destroyed_landscape_count = 0
for a in list(all_actors):
    cname = a.get_class().get_name()
    if "Landscape" in cname:
        unreal.EditorLevelLibrary.destroy_actor(a)
        destroyed_landscape_count += 1
    elif cname in ["VolumetricCloud", "ExponentialHeightFog"]:
        unreal.EditorLevelLibrary.destroy_actor(a)
        print(f"Removed terrestrial atmosphere artifact: {cname}")

print(f"Destroyed {destroyed_landscape_count} unrelated template Landscape actors.")

# 3. Configure Space Sky Sphere
m_space = unreal.EditorAssetLibrary.load_asset("/Game/Earth/M_SpaceSky")
for a in all_actors:
    if a.get_actor_label() == "SM_SkySphere":
        sm_comp = a.get_component_by_class(unreal.StaticMeshComponent)
        if sm_comp and m_space:
            sm_comp.set_material(0, m_space)
            print("Set SM_SkySphere to M_SpaceSky deep space background.")
    elif isinstance(a, unreal.SkyAtmosphere):
        # Disable or hide terrestrial ground sky atmosphere
        a.set_actor_hidden_in_game(True)
        print("Hidden SkyAtmosphere.")

# 4. Save Level
saved = unreal.EditorLevelLibrary.save_current_level()
print("Level saved successfully:", saved)
"""

res = remote.run_command(script)
for out in res.get("output", []):
    print(out.get("output"))

remote.stop()
print("Done applying Earth visual enhancements.")

