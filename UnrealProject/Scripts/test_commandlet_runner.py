import subprocess
import time
import os

code_file = "C:/Users/Sriram Krovi/satellite-collision-avoidance-system/UnrealProject/Scripts/test_direct_py.py"
log_file = "C:/Users/Sriram Krovi/satellite-collision-avoidance-system/UnrealProject/Saved/Logs/test_direct_run.log"

cmd = [
    "C:/Program Files/Epic Games/UE_5.7/Engine/Binaries/Win64/UnrealEditor-Cmd.exe",
    "C:/Users/Sriram Krovi/satellite-collision-avoidance-system/UnrealProject/SatelliteAvoidance.uproject",
    "-run=pythonscript",
    f"-script={code_file}",
    "-NoLiveCoding",
    "-nosound",
    "-notrace",
    "-stdout"
]
print("Running commandlet with file redirection...")
t0 = time.time()
with open(log_file, "w", encoding="utf-8") as out_f:
    proc = subprocess.Popen(cmd, stdout=out_f, stderr=subprocess.STDOUT)
    try:
        ret = proc.wait(timeout=40)
        print(f"PROCESS EXITED PROMPTLY in {time.time()-t0:.1f}s with returncode {ret}!")
    except subprocess.TimeoutExpired:
        proc.kill()
        print("Still timed out after 40s!")

if os.path.exists(log_file):
    with open(log_file, "r", encoding="utf-8", errors="ignore") as f:
        for line in f:
            if "***" in line or "Success" in line:
                print("  [LOG]", line.strip())
