import subprocess
import time
import sys

editor_exe = r"C:\Program Files\Epic Games\UE_5.7\Engine\Binaries\Win64\UnrealEditor.exe"
uproject = r"C:\Users\Sriram Krovi\satellite-collision-avoidance-system\UnrealProject\SatelliteAvoidance.uproject"

print(f"Launching {editor_exe} with project {uproject}...")
proc = subprocess.Popen([editor_exe, uproject], creationflags=subprocess.DETACHED_PROCESS)
print(f"Launched UnrealEditor with PID {proc.pid}")
