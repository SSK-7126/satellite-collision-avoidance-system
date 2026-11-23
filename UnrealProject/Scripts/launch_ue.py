import subprocess
import sys

exe = r"C:\Program Files\Epic Games\UE_5.7\Engine\Binaries\Win64\UnrealEditor.exe"
proj = r"C:\Users\Sriram Krovi\satellite-collision-avoidance-system\UnrealProject\SatelliteAvoidance.uproject"

print(f"Launching UnrealEditor: {exe}")
proc = subprocess.Popen([exe, proj, "-ResX=1920", "-ResY=1080"])
print(f"UnrealEditor launched with PID: {proc.pid}")
sys.stdout.flush()
proc.wait()
