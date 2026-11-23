import subprocess
import time
import os
import glob

ue_exe = r"C:\Program Files\Epic Games\UE_5.7\Engine\Binaries\Win64\UnrealEditor.exe"
proj = r"C:\Users\Sriram Krovi\satellite-collision-avoidance-system\UnrealProject\SatelliteAvoidance.uproject"
shots_dir = r"C:\Users\Sriram Krovi\satellite-collision-avoidance-system\UnrealProject\Saved\Screenshots"

# List screenshots before
before_shots = set(glob.glob(os.path.join(shots_dir, "**", "*.png"), recursive=True))

cmd = [
    ue_exe,
    proj,
    "-game",
    "-windowed",
    "-ResX=1920",
    "-ResY=1080",
    "-nosound",
    "-ExecCmds=delay 6; Shot; delay 2; quit"
]

print("Launching UnrealEditor -game for visual screenshot test...")
t0 = time.time()
proc = subprocess.Popen(cmd)
try:
    proc.wait(timeout=45)
    print(f"UnrealEditor -game completed in {time.time()-t0:.1f}s with exit code {proc.returncode}!")
except subprocess.TimeoutExpired:
    proc.kill()
    print("Timed out after 45s!")

# Check new screenshots
after_shots = set(glob.glob(os.path.join(shots_dir, "**", "*.png"), recursive=True))
new_shots = after_shots - before_shots
print("New screenshots found:", len(new_shots))
for s in new_shots:
    print("  ->", s, f"({os.path.getsize(s)} bytes)")
