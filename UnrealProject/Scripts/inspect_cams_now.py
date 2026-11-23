import unreal
world = unreal.EditorLevelLibrary.get_editor_world()
for a in unreal.EditorLevelLibrary.get_all_level_actors():
    lbl = a.get_actor_label()
    if 'Camera' in lbl:
        loc = a.get_actor_location()
        rot = a.get_actor_rotation()
        parent = a.get_attach_parent_actor()
        parent_name = parent.get_actor_label() if parent else 'None'
        comp = a.get_component_by_class(unreal.CameraComponent)
        fov = comp.get_editor_property('field_of_view') if comp else -1
        print(f'{lbl}: Loc=({loc.x:.1f}, {loc.y:.1f}, {loc.z:.1f}) Rot=(P={rot.pitch:.2f}, Y={rot.yaw:.2f}, R={rot.roll:.2f}) FOV={fov} Parent={parent_name}')
