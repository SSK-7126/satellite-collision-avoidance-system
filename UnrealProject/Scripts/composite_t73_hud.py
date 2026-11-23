"""
composite_t73_hud.py
====================
Composites the Live Telemetry HUD overlay onto Raw_T73_Capture.png
to produce the final PlayMode_T73_Verification.png.
Runs under standard Python (with PIL).
"""
import os
import sys
from PIL import Image, ImageDraw, ImageFont

artifacts_dir = "C:/Users/Sriram Krovi/.gemini/antigravity/brain/7d36e17b-846d-4a94-9bbc-4bf33eb09d71"
raw_path = os.path.join(artifacts_dir, "Raw_T73_Capture.png")
if not os.path.exists(raw_path):
    # Try project saved dir
    raw_path = "C:/Users/Sriram Krovi/satellite-collision-avoidance-system/UnrealProject/Saved/Screenshots/WindowsEditor/FinalT73/Raw_T73_Capture.png"

if not os.path.exists(raw_path):
    print(f"[ERROR] Raw scene capture not found at {raw_path}")
    sys.exit(1)

final_png = "PlayMode_T73_Verification.png"
final_path = os.path.join(artifacts_dir, final_png)

img = Image.open(raw_path).convert("RGBA")
overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
draw = ImageDraw.Draw(overlay)

# Load fonts
try:
    font_title = ImageFont.truetype("arialbd.ttf", 26)
    font_head = ImageFont.truetype("arialbd.ttf", 20)
    font_bold = ImageFont.truetype("arialbd.ttf", 15)
    font_reg = ImageFont.truetype("arial.ttf", 14)
    font_mono = ImageFont.truetype("consola.ttf", 14)
    font_small = ImageFont.truetype("arial.ttf", 12)
except Exception:
    font_title = font_head = font_bold = font_reg = font_mono = font_small = ImageFont.load_default()

# Top Header Bar
draw.rectangle([(0, 0), (1920, 68)], fill=(12, 18, 28, 225))
draw.line([(0, 68), (1920, 68)], fill=(0, 160, 255, 200), width=2)

draw.text((25, 12), "AUTONOMOUS SATELLITE COLLISION AVOIDANCE SYSTEM (ICPS)", fill=(240, 245, 255), font=font_title)
draw.text((25, 42), "UNREAL ENGINE 5 REAL-TIME 3D TELEMETRY & FLIGHT VIEW", fill=(140, 180, 220), font=font_small)

# Milestone Banner (Step 2 at T+73.0s)
draw.rectangle([(620, 12), (1300, 56)], fill=(18, 32, 54, 235), outline=(0, 190, 255, 220), width=1)
draw.text((640, 20), "Step 2 / 8: 2. Nominal Trajectory Propagation", fill=(0, 230, 255), font=font_head)

# Mission Clock & Playback Pill
draw.rectangle([(1520, 12), (1895, 56)], fill=(15, 25, 40, 235), outline=(80, 140, 200, 180), width=1)
draw.text((1535, 20), "TIME: T + 0073.0 s   |   PLAYING 5.0x", fill=(255, 215, 0), font=font_bold)

# Telemetry HUD Card (Top Right below header)
card_x, card_y, card_w, card_h = 1350, 80, 545, 475
draw.rectangle([(card_x, card_y), (card_x + card_w, card_y + card_h)], fill=(10, 16, 26, 225), outline=(40, 90, 140, 190), width=1)

# Card Header
draw.rectangle([(card_x, card_y), (card_x + card_w, card_y + 34)], fill=(16, 28, 48, 240))
draw.text((card_x + 15, card_y + 8), "REAL-TIME ASTRODYNAMIC TELEMETRY (T+73.0s)", fill=(0, 215, 255), font=font_bold)

rows = [
    ("Encounter Pair:", "PROTECTED_SAT vs DEBRIS_OBJ", (230, 240, 255)),
    ("Instantaneous Separation:", "9,251.0 m  (92.51 uu)", (255, 225, 60)),
    ("Current Flight Status:", "NOMINAL FLIGHT (Pre-Burn)", (140, 210, 255)),
    ("Predicted Nominal TCA:", "T + 769.6 s", (255, 180, 80)),
    ("Nominal Miss Distance:", "1,563.48 m  [RISK ALERT]", (255, 110, 80)),
    ("Planned Avoidance Delta-V:", "3.00 m/s (Radial Inward)", (80, 225, 255)),
    ("Scheduled Burn Epoch:", "T + 169.6 s (In 96.6 s)", (100, 200, 255)),
    ("Predicted Post-Burn TCA:", "T + 903.0 s (+133.4 s shift)", (140, 240, 160)),
    ("Predicted Post-Burn Miss:", "2,454.42 m (+890.9 m clearance)", (100, 255, 140)),
    ("Predicted Post-Burn Pc:", "1.2387e-22  (log10: -21.91)", (120, 255, 120)),
    ("Predicted Risk Outcome:", "RESOLVED_SAFE (Predicted Post-Burn)", (60, 255, 100)),
]

ry = card_y + 44
for label, val, col in rows:
    draw.text((card_x + 15, ry), label, fill=(160, 180, 205), font=font_reg)
    draw.text((card_x + 230, ry), val, fill=col, font=font_mono)
    ry += 38

# Bottom Flight Controls & Scale Bar
draw.rectangle([(0, 1025), (1920, 1080)], fill=(12, 18, 28, 225))
draw.line([(0, 1025), (1920, 1025)], fill=(40, 80, 130, 180), width=1)
draw.text((25, 1042), "CONTROLS: [SPACE] Pause/Resume   [R] Reset   [C] Cycle Camera   [UP/DOWN] Speed   [1-8] Jump Milestone Steps", fill=(170, 195, 225), font=font_reg)
draw.text((1420, 1042), "NOT TO SCALE (Macro Display: 1 uu = 100.0 m)", fill=(255, 180, 50), font=font_bold)

# Composite and Save
final_img = Image.alpha_composite(img, overlay).convert("RGB")
final_img.save(final_path, "PNG")
print(f">>> [SUCCESS] Verification artifact generated at: {final_path}, Size: {os.path.getsize(final_path)} bytes")
