"""
UnrealProject/Scripts/ue_demo_automation.py
===========================================
Unreal Engine 5 Python Automation Script for Collision Avoidance Demonstration.
Can be executed within Unreal Editor's Python environment:
    unreal.PythonScriptLibrary.execute_python_command("exec(open('.../ue_demo_automation.py').read())")
or via command-line:
    UnrealEditor-Cmd.exe <path/to/SatelliteAvoidance.uproject> -ExecutePythonScript="<path>/ue_demo_automation.py"
"""

import json
import os
import sys

try:
    import unreal
    IN_UNREAL = True
except ImportError:
    IN_UNREAL = False

PAYLOAD_PATH = os.path.abspath(os.path.join(
    os.path.dirname(__file__),
    "../../D2/visualization/unreal_simulation_payload.json"
))


def load_simulation_payload(path=PAYLOAD_PATH):
    if not os.path.exists(path):
        raise FileNotFoundError(f"Simulation payload not found at {path}")
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def run_unreal_setup():
    if not IN_UNREAL:
        print(f"[UE AUTOMATION] Script initialized outside Unreal Editor. Payload located at: {PAYLOAD_PATH}")
        data = load_simulation_payload()
        print(f"[UE AUTOMATION] Scenario: {data['scenario_metadata']['scenario_id']}")
        print(f"[UE AUTOMATION] Duration: {data['scenario_metadata']['duration_sec']}s, Samples: {data['scenario_metadata']['num_samples']}")
        print(f"[UE AUTOMATION] TCA: {data['nominal_encounter']['tca_seconds']}s, Miss: {data['nominal_encounter']['miss_distance_m']}m")
        print(f"[UE AUTOMATION] Manoeuvre: {data['selected_manoeuvre']['manoeuvre_id']} (dv = {data['selected_manoeuvre']['delta_v_magnitude_mps']} m/s)")
        print(f"[UE AUTOMATION] New Miss: {data['post_manoeuvre_encounter']['new_miss_distance_m']}m")
        return

    unreal.log("Initializing Satellite Avoidance Visualization in Unreal Engine 5...")
    data = load_simulation_payload()

    # 1. Create or load the demonstration level
    map_asset_path = "/Game/Scenarios/CollisionAvoidanceDemo"
    unreal.log(f"Setting up scene level at: {map_asset_path}")

    unreal.EditorLevelLibrary.new_level(map_asset_path)
    world = unreal.EditorLevelLibrary.get_editor_world()

    # 2. Spawn Earth Actor at Origin
    earth_loc = unreal.Vector(0.0, 0.0, 0.0)
    earth_rot = unreal.Rotator(0.0, 0.0, 0.0)
    earth_radius_uu = data["physical_constants"]["earth_radius_uu"]
    earth_actor = unreal.EditorLevelLibrary.spawn_actor_from_class(unreal.EarthActor, earth_loc, earth_rot)
    if earth_actor:
        earth_actor.set_actor_label("Earth_CelestialBody")
        earth_actor.set_editor_property("EarthRadiusUe", float(earth_radius_uu))
        unreal.log(f"Spawned EarthActor at (0,0,0) with radius {earth_radius_uu:.1f} uu")

    # 3. Spawn Primary Satellite at Initial Position
    sat_init = data["primary_satellite"]["initial_state_ue"]["position_uu"]
    sat_rot_data = data["primary_satellite"]["initial_state_ue"].get(
        "rotation_deg_rpy",
        data["primary_satellite"]["initial_state_ue"].get("flight_rotator_deg", [0.0, 0.0, 0.0])
    )
    sat_loc = unreal.Vector(float(sat_init[0]), float(sat_init[1]), float(sat_init[2]))
    sat_rot = unreal.Rotator(float(sat_rot_data[0]), float(sat_rot_data[1]), float(sat_rot_data[2]))
    sat_actor = unreal.EditorLevelLibrary.spawn_actor_from_class(unreal.SatelliteActor, sat_loc, sat_rot)
    if sat_actor:
        sat_actor.set_actor_label("ProtectedSatellite_Payload01")
        sat_actor.set_editor_property("SatelliteId", "SAT_PAYLOAD_01")
        unreal.log(f"Spawned SatelliteActor at {sat_loc}")

    # 4. Spawn Secondary Debris at Initial Position
    deb_init = data["secondary_debris"]["initial_state_ue"]["position_uu"]
    deb_rot_data = data["secondary_debris"]["initial_state_ue"].get(
        "rotation_deg_rpy",
        data["secondary_debris"]["initial_state_ue"].get("flight_rotator_deg", [0.0, 0.0, 0.0])
    )
    deb_loc = unreal.Vector(float(deb_init[0]), float(deb_init[1]), float(deb_init[2]))
    deb_rot = unreal.Rotator(float(deb_rot_data[0]), float(deb_rot_data[1]), float(deb_rot_data[2]))
    deb_actor = unreal.EditorLevelLibrary.spawn_actor_from_class(unreal.DebrisActor, deb_loc, deb_rot)
    if deb_actor:
        deb_actor.set_actor_label("SecondaryDebris_Object99")
        deb_actor.set_editor_property("DebrisId", "DEBRIS_PIECE_99")
        unreal.log(f"Spawned DebrisActor at {deb_loc}")

    # 5. Spawn Orbit Path Visualizers
    zero_vec = unreal.Vector(0.0, 0.0, 0.0)
    zero_rot = unreal.Rotator(0.0, 0.0, 0.0)

    sat_nom_path = unreal.EditorLevelLibrary.spawn_actor_from_class(unreal.OrbitPathActor, zero_vec, zero_rot)
    if sat_nom_path:
        sat_nom_path.set_actor_label("OrbitPath_SatelliteNominal")

    debris_path = unreal.EditorLevelLibrary.spawn_actor_from_class(unreal.OrbitPathActor, zero_vec, zero_rot)
    if debris_path:
        debris_path.set_actor_label("OrbitPath_DebrisNominal")

    sat_mod_path = unreal.EditorLevelLibrary.spawn_actor_from_class(unreal.OrbitPathActor, zero_vec, zero_rot)
    if sat_mod_path:
        sat_mod_path.set_actor_label("OrbitPath_SatelliteModified")

    # 6. Spawn Conjunction & Manoeuvre Visualizers
    conj_vis = unreal.EditorLevelLibrary.spawn_actor_from_class(unreal.ConjunctionVisualizer, zero_vec, zero_rot)
    if conj_vis:
        conj_vis.set_actor_label("Conjunction_Visualizer")

    man_vis = unreal.EditorLevelLibrary.spawn_actor_from_class(unreal.ManoeuvreVisualizer, zero_vec, zero_rot)
    if man_vis:
        man_vis.set_actor_label("Manoeuvre_Visualizer")

    # 7. Spawn Simulation Manager and Link All Actors
    sim_mgr = unreal.EditorLevelLibrary.spawn_actor_from_class(unreal.OrbitSimulationManager, zero_vec, zero_rot)
    if sim_mgr:
        sim_mgr.set_actor_label("OrbitSimulationManager")
        sim_mgr.set_editor_property("EarthActor", earth_actor)
        sim_mgr.set_editor_property("SatelliteActor", sat_actor)
        sim_mgr.set_editor_property("DebrisActor", deb_actor)
        sim_mgr.set_editor_property("SatNominalPathActor", sat_nom_path)
        sim_mgr.set_editor_property("DebrisPathActor", debris_path)
        sim_mgr.set_editor_property("SatModifiedPathActor", sat_mod_path)
        sim_mgr.set_editor_property("ConjunctionVisualizer", conj_vis)
        sim_mgr.set_editor_property("ManoeuvreVisualizer", man_vis)

        # 7b. Spawn Dedicated Encounter Overview Camera
        cam_loc = unreal.Vector(115000.0, -45000.0, 32000.0)
        cam_rot = unreal.Rotator(roll=0.0, pitch=-19.0, yaw=152.0)
        cam_actor = unreal.EditorLevelLibrary.spawn_actor_from_class(unreal.CameraActor, cam_loc, cam_rot)
        if cam_actor:
            cam_actor.set_actor_label("Camera_EncounterOverview")
            cam_comp = cam_actor.get_editor_property("camera_component")
            if cam_comp:
                cam_comp.set_editor_property("field_of_view", 65.0)
            unreal.log(f"Spawned CameraActor at {cam_loc} (FOV: 65°)")
            sim_mgr.set_editor_property("OverviewCamera", cam_actor)

        # Align Level Viewport camera as well
        unreal.EditorLevelLibrary.set_level_viewport_camera_info(cam_loc, cam_rot)

        # Initialize and populate trajectory points and encounter indicators from JSON payload
        payload_file_str = PAYLOAD_PATH.replace("\\", "/")
        init_ok = sim_mgr.initialize_simulation_from_payload(payload_file_str)
        unreal.log(f"Simulation Manager initialized with payload: {init_ok}")

    # 8. Log Demonstration Sequence Steps
    steps = data["demonstration_sequence"]
    unreal.log(f"Configured {len(steps)} Demonstration Sequence Milestones:")
    for s in steps:
        unreal.log(f"  Step {s['step']}: {s['headline']} at T+{s['simulation_time_sec']}s")

    # 9. Save Generated Level Map to disk
    save_ok = unreal.EditorLevelLibrary.save_current_level()
    save_map_ok = unreal.EditorLoadingAndSavingUtils.save_map(world, map_asset_path)
    save_packages_ok = unreal.EditorLoadingAndSavingUtils.save_dirty_packages(True, True)
    unreal.log(f"Level saved to {map_asset_path}: LevelSave={save_ok}, MapSave={save_map_ok}, PackagesSave={save_packages_ok}")
    unreal.log("Unreal Engine 5 Collision Avoidance Simulation Scene Successfully Generated and Saved.")


if __name__ == "__main__":
    run_unreal_setup()
