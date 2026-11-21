import unreal

print(">>> TESTING MATERIAL EDITING LIBRARY <<<")
print("Has MaterialEditingLibrary:", hasattr(unreal, "MaterialEditingLibrary"))
if hasattr(unreal, "MaterialEditingLibrary"):
    methods = [m for m in dir(unreal.MaterialEditingLibrary) if not m.startswith("_")]
    print("Methods:", methods[:10])

unreal.SystemLibrary.execute_console_command(None, "QUIT_EDITOR")

