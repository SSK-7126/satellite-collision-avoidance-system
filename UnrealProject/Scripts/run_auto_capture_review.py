import subprocess
import time
import os
import shutil

ue_exe = r"C:\Program Files\Epic Games\UE_5.7\Engine\Binaries\Win64\UnrealEditor.exe"
proj = r"C:\Users\Sriram Krovi\satellite-collision-avoidance-system\UnrealProject\SatelliteAvoidance.uproject"
out_dir = r"C:\Users\Sriram Krovi\satellite-collision-avoidance-system\Project_Deliverables\Windows_Package\Reports\Screenshots"
artifacts_dir = r"C:\Users\Sriram Krovi\.gemini\antigravity\brain\cdd0c206-fcf3-4310-8916-ebe32a293b35"

os.makedirs(out_dir, exist_ok=True)
os.makedirs(artifacts_dir, exist_ok=True)

cmd = [
    ue_exe,
    proj,
    "-game",
    "-windowed",
    "-ResX=1920",
    "-ResY=1080",
    "-nosound",
    "-AutoCaptureReview"
]

print(">>> Launching Unreal Engine standalone review capture (-AutoCaptureReview)...")
t0 = time.time()
proc = subprocess.Popen(cmd)
try:
    ret = proc.wait(timeout=120)
    print(f">>> Process completed cleanly in {time.time()-t0:.1f}s with exit code {ret}!")
except subprocess.TimeoutExpired:
    print(f">>> Timed out after 120s, terminating...")
    proc.kill()

views = [
    "View1_DefaultOverview.png",
    "View2_EarthCentredOverview.png",
    "View3_SatelliteInspection.png",
    "View4_DebrisInspection.png",
    "View5_FullDashboard_Step6.png",
    "View2_SatelliteCloseUp.png",
    "View3_DebrisCloseUp.png",
    "View4_EarthCloseUp.png"
]

print(">>> Verifying captured review screenshots:")
for v in views:
    src = os.path.join(out_dir, v)
    dst = os.path.join(artifacts_dir, v)
    found = False
    for alt_base in [
        r"C:\Users\Sriram Krovi\satellite-collision-avoidance-system\UnrealProject\Saved\Screenshots\WindowsEditor",
        r"C:\Users\Sriram Krovi\satellite-collision-avoidance-system\UnrealProject\Saved\Screenshots\Windows",
        out_dir
    ]:
        candidate = os.path.join(alt_base, v)
        if os.path.exists(candidate):
            sz = os.path.getsize(candidate)
            if os.path.abspath(candidate) != os.path.abspath(src):
                shutil.copy(candidate, src)
            if os.path.abspath(candidate) != os.path.abspath(dst):
                shutil.copy(candidate, dst)
            print(f"  [OK] {v} ({sz:,} bytes) from {alt_base} -> copied to artifacts")
            found = True
            break
    if not found:
        print(f"  [MISSING] {v}")

# Alias copies for closeups
for src_name, alias_name in [("View3_SatelliteInspection.png", "View2_SatelliteCloseUp.png"), ("View4_DebrisInspection.png", "View3_DebrisCloseUp.png")]:
    for base in [out_dir, artifacts_dir]:
        s = os.path.join(base, src_name)
        a = os.path.join(base, alias_name)
        if os.path.exists(s):
            shutil.copy(s, a)
            print(f"  [ALIAS] Copied {src_name} -> {alias_name} in {base}")
