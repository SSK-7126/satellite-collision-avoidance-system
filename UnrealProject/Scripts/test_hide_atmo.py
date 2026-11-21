import unreal

world = unreal.EditorLevelLibrary.get_editor_world()
all_actors = unreal.EditorLevelLibrary.get_all_level_actors()

ea = [a for a in all_actors if isinstance(a, unreal.EarthActor)][0]
atm = ea.get_editor_property('atmosphere_mesh')
atm.set_hidden_in_game(True)
atm.set_visibility(False)

cam_loc = unreal.Vector(115000.0, -45000.0, 32000.0)
cam_rot = unreal.Rotator(roll=0.0, pitch=-19.0, yaw=152.0)

capture_actor = unreal.EditorLevelLibrary.spawn_actor_from_class(unreal.SceneCapture2D, cam_loc, cam_rot)
comp = capture_actor.get_editor_property('capture_component2d')
comp.set_editor_property('fov_angle', 65.0)
comp.set_editor_property('capture_source', unreal.SceneCaptureSource.SCS_FINAL_COLOR_LDR)

rt = unreal.RenderingLibrary.create_render_target2d(world, 1920, 1080, unreal.TextureRenderTargetFormat.RTF_RGBA8)
comp.set_editor_property('texture_target', rt)
comp.capture_scene()

out_dir = (unreal.Paths.project_saved_dir() + 'Screenshots/WindowsEditor').replace('\\', '/')
unreal.RenderingLibrary.export_render_target(world, rt, out_dir, 'Test_Earth_NoAtmo.png')
unreal.EditorLevelLibrary.destroy_actor(capture_actor)
print('Exported Test_Earth_NoAtmo.png')

unreal.SystemLibrary.execute_console_command(None, 'QUIT_EDITOR')