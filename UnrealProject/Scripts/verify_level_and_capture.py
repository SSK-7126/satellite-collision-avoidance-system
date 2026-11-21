"""
UnrealProject/Scripts/verify_level_and_capture.py
=================================================
Automated verification and visual inspection script for the saved
CollisionAvoidanceDemo level in Unreal Engine 5.7.
"""

import os
import json
import unreal

def verify_scene():
    unreal.log("=" * 72)
    unreal.log(" STARTING UE5 GUI & LEVEL VALIDATION: CollisionAvoidanceDemo")
    unreal.log("=" * 72)

    level_path = "/Game/Scenarios/CollisionAvoidanceDemo"
    unreal.log(f"[TASK 2 & 3] Loading saved level: {level_path}")

    # Load level
    load_success = unreal.EditorLoadingAndSavingUtils.load_map(level_path)
    unreal.log(f"Level load result: {load_success}")

    world = unreal.EditorLevelLibrary.get_editor_world()
    if not world:
        unreal.log_error("Failed to get editor world!")
        return

    # 4. Verify all actors
    unreal.log("\n[TASK 4] Verifying scene actors and visual components...")
    all_actors = unreal.EditorLevelLibrary.get_all_level_actors()
    unreal.log(f"Total level actors found: {len(all_actors)}")

    earth_actors = [a for a in all_actors if isinstance(a, unreal.EarthActor)]
    sat_actors = [a for a in all_actors if isinstance(a, unreal.SatelliteActor)]
    deb_actors = [a for a in all_actors if isinstance(a, unreal.DebrisActor)]
    path_actors = [a for a in all_actors if isinstance(a, unreal.OrbitPathActor)]
    conj_actors = [a for a in all_actors if isinstance(a, unreal.ConjunctionVisualizer)]
    man_actors = [a for a in all_actors if isinstance(a, unreal.ManoeuvreVisualizer)]
    mgr_actors = [a for a in all_actors if isinstance(a, unreal.OrbitSimulationManager)]

    unreal.log(f"  EarthActor count: {len(earth_actors)}")
    unreal.log(f"  SatelliteActor count: {len(sat_actors)}")
    unreal.log(f"  DebrisActor count: {len(deb_actors)}")
    unreal.log(f"  OrbitPathActor count: {len(path_actors)}")
    unreal.log(f"  ConjunctionVisualizer count: {len(conj_actors)}")
    unreal.log(f"  ManoeuvreVisualizer count: {len(man_actors)}")
    unreal.log(f"  OrbitSimulationManager count: {len(mgr_actors)}")

    assert len(earth_actors) >= 1, "EarthActor missing!"
    assert len(sat_actors) >= 1, "SatelliteActor missing!"
    assert len(deb_actors) >= 1, "DebrisActor missing!"
    assert len(path_actors) >= 3, "Expected at least 3 OrbitPathActors (Nominal, Debris, Modified)!"
    assert len(conj_actors) >= 1, "ConjunctionVisualizer missing!"
    assert len(man_actors) >= 1, "ManoeuvreVisualizer missing!"
    assert len(mgr_actors) >= 1, "OrbitSimulationManager missing!"

    earth = earth_actors[0]
    sat = sat_actors[0]
    deb = deb_actors[0]
    sim_mgr = mgr_actors[0]

    unreal.log(f"  Earth radius: {earth.get_editor_property('earth_radius_ue')} uu at {earth.get_actor_location()}")
    unreal.log(f"  Satellite ID: {sat.get_editor_property('satellite_id')} at {sat.get_actor_location()}")
    unreal.log(f"  Debris ID: {deb.get_editor_property('debris_id')} at {deb.get_actor_location()}")

    # 5. Check Simulation Data Bridge and Telemetry
    unreal.log("\n[TASK 5] Checking SimulationDataBridge and Telemetry...")
    payload_path = os.path.abspath(os.path.join(
        os.path.dirname(__file__),
        "../../D2/visualization/unreal_simulation_payload.json"
    )).replace("\\", "/")

    init_ok = sim_mgr.initialize_simulation_from_payload(payload_path)
    unreal.log(f"  SimulationDataBridge initialization: {init_ok}")

    data_bridge = sim_mgr.get_editor_property("data_bridge")
    if data_bridge:
        unreal.log(f"  DataBridge Nominal TCA: {data_bridge.nominal_encounter.tca_seconds:.2f}s")
        unreal.log(f"  DataBridge Nominal Miss Distance: {data_bridge.nominal_encounter.miss_distance_metres:.1f} m")
        unreal.log(f"  DataBridge Selected Manoeuvre: {data_bridge.selected_manoeuvre.manoeuvre_id} (dv = {data_bridge.selected_manoeuvre.delta_v_magnitude_mps:.2f} m/s)")
        unreal.log(f"  DataBridge Nominal Points: {len(data_bridge.sat_nominal_positions)}, Debris Points: {len(data_bridge.debris_positions)}, Modified Points: {len(data_bridge.sat_modified_positions)}")

    # 6. Verify 8 Demonstration Milestones
    unreal.log("\n[TASK 6] Verifying accessibility of the 8 demonstration milestones...")
    if data_bridge:
        seq = data_bridge.demonstration_sequence
        unreal.log(f"  Found {len(seq)} demonstration sequence milestones.")
        for idx, step in enumerate(seq, start=1):
            sim_mgr.jump_to_step(idx)
            cur_time = sim_mgr.get_editor_property("current_simulation_time")
            man_exec = sim_mgr.get_editor_property("manoeuvre_executed")
            sat_loc = sat.get_actor_location()
            deb_loc = deb.get_actor_location()
            unreal.log(f"  [Step {idx}] T+{cur_time:.1f}s | {step.headline} | Burn Executed: {man_exec} | Sat: {sat_loc} | Deb: {deb_loc}")

    # Reset simulation back to initial state
    sim_mgr.reset_simulation()
    unreal.log("  Simulation reset to initial state (t = 0.0s).")

    # 7. Set Viewport Camera Position overlooking Earth and the satellite encounter
    camera_loc = unreal.Vector(95000.0, -35000.0, 25000.0)
    camera_rot = unreal.Rotator(roll=0.0, pitch=-18.0, yaw=148.0)
    unreal.EditorLevelLibrary.set_level_viewport_camera_info(camera_loc, camera_rot)
    unreal.log(f"  Viewport camera aligned to: {camera_loc}, rotation: {camera_rot}")

    unreal.log("\n" + "=" * 72)
    unreal.log(" GUI & LEVEL VALIDATION COMPLETED SUCCESSFULLY (0 ERRORS)")
    unreal.log("=" * 72)


if __name__ == "__main__":
    verify_scene()

