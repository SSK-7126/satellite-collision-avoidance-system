import sys
import time
import json
import os

sys.path.append(r"C:\Program Files\Epic Games\UE_5.7\Engine\Plugins\Experimental\PythonScriptPlugin\Content\Python")
import remote_execution

def run_audit():
    remote = remote_execution.RemoteExecution()
    remote.start()
    time.sleep(1.0)

    if not remote.remote_nodes:
        print("[ERROR] No running Unreal Editor remote execution node discovered!")
        return

    node = remote.remote_nodes[0]
    remote.open_command_connection(node["node_id"])

    audit_code = """
import unreal
import json

results = {}

world = unreal.EditorLevelLibrary.get_editor_world()
world_name = world.get_name() if world else "None"
world_path = world.get_path_name() if world else "None"

all_actors = unreal.EditorLevelLibrary.get_all_level_actors()

results["level_validation"] = {
    "world_name": world_name,
    "world_path": world_path,
    "total_actor_count": len(all_actors),
    "actor_classes": {}
}

for a in all_actors:
    cname = a.get_class().get_name()
    results["level_validation"]["actor_classes"][cname] = results["level_validation"]["actor_classes"].get(cname, 0) + 1

# 1. EARTH INSPECTION
earth_actors = [a for a in all_actors if isinstance(a, unreal.EarthActor)]
earth_info = {"exists": len(earth_actors) > 0, "count": len(earth_actors)}
if earth_actors:
    e = earth_actors[0]
    mesh_comp = e.get_editor_property("earth_mesh")
    earth_info["label"] = e.get_actor_label()
    earth_info["location"] = [e.get_actor_location().x, e.get_actor_location().y, e.get_actor_location().z]
    earth_info["has_mesh_component"] = mesh_comp is not None
    if mesh_comp:
        sm = mesh_comp.get_editor_property("static_mesh")
        earth_info["static_mesh_assigned"] = sm is not None
        earth_info["static_mesh_path"] = sm.get_path_name() if sm else None
        scale = mesh_comp.get_editor_property("relative_scale3d")
        earth_info["component_scale"] = [scale.x, scale.y, scale.z]
        earth_info["is_visible"] = mesh_comp.is_visible()
        earth_info["is_hidden_in_game"] = e.is_hidden_ed()
        earth_info["renders_visible_geometry"] = (sm is not None) and mesh_comp.is_visible()
results["earth"] = earth_info

# 2. SATELLITE INSPECTION
sat_actors = [a for a in all_actors if isinstance(a, unreal.SatelliteActor)]
sat_info = {"exists": len(sat_actors) > 0, "count": len(sat_actors)}
if sat_actors:
    s = sat_actors[0]
    sat_info["label"] = s.get_actor_label()
    sat_info["location"] = [s.get_actor_location().x, s.get_actor_location().y, s.get_actor_location().z]
    
    components = {}
    for comp_name in ["satellite_body", "solar_panel_left", "solar_panel_right"]:
        c = s.get_editor_property(comp_name)
        if c:
            sm = c.get_editor_property("static_mesh")
            components[comp_name] = {
                "exists": True,
                "static_mesh_assigned": sm is not None,
                "static_mesh_path": sm.get_path_name() if sm else None,
                "is_visible": c.is_visible(),
                "renders_geometry": (sm is not None) and c.is_visible()
            }
        else:
            components[comp_name] = {"exists": False, "static_mesh_assigned": False}
    sat_info["components"] = components
    sat_info["any_geometry_rendering"] = any(c.get("renders_geometry", False) for c in components.values())
results["satellite"] = sat_info

# 3. DEBRIS INSPECTION
deb_actors = [a for a in all_actors if isinstance(a, unreal.DebrisActor)]
deb_info = {"exists": len(deb_actors) > 0, "count": len(deb_actors)}
if deb_actors:
    d = deb_actors[0]
    deb_info["label"] = d.get_actor_label()
    deb_info["location"] = [d.get_actor_location().x, d.get_actor_location().y, d.get_actor_location().z]
    c = d.get_editor_property("debris_mesh")
    if c:
        sm = c.get_editor_property("static_mesh")
        deb_info["has_mesh_component"] = True
        deb_info["static_mesh_assigned"] = sm is not None
        deb_info["static_mesh_path"] = sm.get_path_name() if sm else None
        deb_info["is_visible"] = c.is_visible()
        deb_info["renders_visible_geometry"] = (sm is not None) and c.is_visible()
    else:
        deb_info["has_mesh_component"] = False
        deb_info["renders_visible_geometry"] = False
results["debris"] = deb_info

# 4. ORBIT TRAJECTORIES INSPECTION
path_actors = [a for a in all_actors if isinstance(a, unreal.OrbitPathActor)]
paths_info = {"exists": len(path_actors) > 0, "count": len(path_actors), "instances": []}
for p in path_actors:
    label = p.get_actor_label()
    spline = p.get_editor_property("trajectory_spline")
    pt_count = spline.get_number_of_spline_points() if spline else 0
    
    # Check for spline mesh components or procedural meshes
    all_comps = p.get_components_by_class(unreal.ActorComponent)
    comp_types = [c.get_class().get_name() for c in all_comps]
    
    spline_meshes = [c for c in all_comps if isinstance(c, unreal.SplineMeshComponent)]
    proc_meshes = [c for c in all_comps if "Procedural" in c.get_class().get_name()]
    static_meshes = [c for c in all_comps if isinstance(c, unreal.StaticMeshComponent)]
    
    paths_info["instances"].append({
        "label": label,
        "spline_points_count": pt_count,
        "component_types": comp_types,
        "spline_mesh_count": len(spline_meshes),
        "procedural_mesh_count": len(proc_meshes),
        "static_mesh_count": len(static_meshes),
        "renders_solid_geometry": (len(spline_meshes) > 0 or len(proc_meshes) > 0 or len(static_meshes) > 0)
    })
results["orbit_trajectories"] = paths_info

# 5. LIGHTING INSPECTION
dir_lights = [a for a in all_actors if isinstance(a, unreal.DirectionalLight)]
sky_lights = [a for a in all_actors if isinstance(a, unreal.SkyLight)]
point_lights = [a for a in all_actors if isinstance(a, unreal.PointLight)]
atmospheres = [a for a in all_actors if "Atmosphere" in a.get_class().get_name()]
post_processes = [a for a in all_actors if isinstance(a, unreal.PostProcessVolume)]

lighting_info = {
    "directional_lights_count": len(dir_lights),
    "directional_lights": [l.get_actor_label() for l in dir_lights],
    "sky_lights_count": len(sky_lights),
    "sky_lights": [l.get_actor_label() for l in sky_lights],
    "point_lights_count": len(point_lights),
    "sky_atmosphere_count": len(atmospheres),
    "post_process_volume_count": len(post_processes),
    "has_active_illumination": (len(dir_lights) > 0 or len(sky_lights) > 0)
}
results["lighting"] = lighting_info

# 6. TELEMETRY HUD INSPECTION
# Check if AvoidanceInfoPanelWidget class is loaded
widget_class = unreal.load_class(None, "/Script/SatelliteAvoidance.AvoidanceInfoPanelWidget")
widget_instances = []
try:
    widget_instances = unreal.WidgetBlueprintLibrary.get_all_widgets_of_class(world, widget_class, top_level_only=False)
except Exception as e:
    pass

hud_info = {
    "cpp_class_available": widget_class is not None,
    "widget_class_name": widget_class.get_name() if widget_class else None,
    "active_instances_count": len(widget_instances),
    "added_to_viewport": len(widget_instances) > 0,
    "active_hud_controller_exists": False
}
# Check player controller / HUD
pcs = [a for a in all_actors if isinstance(a, unreal.PlayerController)]
huds = [a for a in all_actors if isinstance(a, unreal.HUD)]
hud_info["player_controller_count"] = len(pcs)
hud_info["hud_actor_count"] = len(huds)
results["telemetry_hud"] = hud_info

# 7. CAMERA INSPECTION
cam_loc, cam_rot = unreal.EditorLevelLibrary.get_level_viewport_camera_info()
cam_actors = [a for a in all_actors if isinstance(a, unreal.CameraActor)]

camera_info = {
    "viewport_camera_location": [cam_loc.x, cam_loc.y, cam_loc.z] if cam_loc else None,
    "viewport_camera_rotation": [cam_rot.pitch, cam_rot.yaw, cam_rot.roll] if cam_rot else None,
    "camera_actors_in_scene": len(cam_actors),
    "camera_actor_labels": [c.get_actor_label() for c in cam_actors]
}
results["camera"] = camera_info

print("__AUDIT_JSON_BEGIN__")
print(json.dumps(results, indent=2))
print("__AUDIT_JSON_END__")
"""

    res = remote.run_command(audit_code)
    output_lines = []
    for out in res.get("output", []):
        output_lines.append(out.get("output", ""))
    full_output = "\n".join(output_lines)
    
    # Extract JSON
    if "__AUDIT_JSON_BEGIN__" in full_output and "__AUDIT_JSON_END__" in full_output:
        start = full_output.find("__AUDIT_JSON_BEGIN__") + len("__AUDIT_JSON_BEGIN__")
        end = full_output.find("__AUDIT_JSON_END__")
        audit_json = full_output[start:end].strip()
        data = json.loads(audit_json)
        print("\n================== READ-ONLY AUDIT RESULTS ==================")
        print(json.dumps(data, indent=2))
        
        # Save results locally for analysis
        with open("UnrealProject/visual_scene_audit.json", "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
        print("\nAudit results saved to UnrealProject/visual_scene_audit.json")
    else:
        print("[ERROR] Could not parse JSON from remote execution output. Full output:")
        print(full_output)

    remote.stop()

if __name__ == "__main__":
    run_audit()

