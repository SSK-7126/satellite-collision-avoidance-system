import unreal

unreal.EditorLevelLibrary.load_level('/Game/Scenarios/CollisionAvoidanceDemo')
actors = unreal.EditorLevelLibrary.get_all_level_actors()

for a in actors:
    if isinstance(a, unreal.DirectionalLight):
        comp = a.get_component_by_class(unreal.DirectionalLightComponent)
        print("DirectionalLight:")
        print("  LightColor:", comp.get_editor_property("light_color"))
        print("  AtmosphereSunLight:", comp.get_editor_property("atmosphere_sun_light"))
        print("  Temperature:", comp.get_editor_property("temperature"))
        print("  UseTemperature:", comp.get_editor_property("use_temperature"))
    elif isinstance(a, unreal.SkyLight):
        comp = a.get_component_by_class(unreal.SkyLightComponent)
        print("SkyLight:")
        print("  LightColor:", comp.get_editor_property("light_color"))
        print("  RealTimeCapture:", comp.get_editor_property("real_time_capture"))

unreal.SystemLibrary.execute_console_command(None, "QUIT_EDITOR")
