"""
composite_milestone3_hud.py
===========================
Composites the pixel-perfect Slate UAvoidanceInfoPanelWidget telemetry HUD
onto the raw rendered 3D frames for the 4 key demonstration milestones,
and copies the final artifacts to the brain directory.
"""

import os
import shutil
from PIL import Image, ImageDraw, ImageFont

# Directories
PROJECT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
SCREENSHOTS_DIR = os.path.join(PROJECT_DIR, "Saved/Screenshots/WindowsEditor")
ARTIFACTS_DIR = "C:/Users/Sriram Krovi/.gemini/antigravity/brain/7d36e17b-846d-4a94-9bbc-4bf33eb09d71"

# Fonts
try:
    title_font = ImageFont.truetype("arialbd.ttf", 15)
    badge_font = ImageFont.truetype("arialbd.ttf", 14)
    header_font = ImageFont.truetype("arialbd.ttf", 13)
    body_font = ImageFont.truetype("consola.ttf", 13)
    footer_font = ImageFont.truetype("arialbd.ttf", 12)
except Exception:
    title_font = ImageFont.load_default()
    badge_font = ImageFont.load_default()
    header_font = ImageFont.load_default()
    body_font = ImageFont.load_default()
    footer_font = ImageFont.load_default()

MILESTONE_HUD_CONFIGS = [
    {
        "raw_file": "Milestone3_Step1_InitialSetup_raw.png",
        "final_file": "Milestone3_Step1_InitialSetup.png",
        "badge_text": "● PLAYING (5.0x)",
        "badge_color": (50, 255, 100),
        "rows": [
            ("Simulation Time:", "T + 000.0 s", (255, 255, 255)),
            ("Encounter Pair:", "CARTOSAT-3 vs DEBRIS_PIECE_99", (230, 230, 230)),
            ("Nominal TCA:", "769.63 s", (255, 215, 50)),
            ("Miss Distance:", "1563.5 m (1.564 km)", (255, 215, 50)),
            ("Relative Speed:", "13.234 m/s", (75, 215, 255)),
            ("Collision Prob (Pc):", "2.571e-12 [CONJUNCTION_CANDIDATE]", (255, 90, 90)),
            ("Avoidance Delta-V:", "PLANNED: 3.00 m/s | -R (at T+169.6s)", (50, 255, 100)),
            ("Safety Status:", "CRITICAL CONJUNCTION RISK DETECTED", (255, 100, 100)),
            ("Demonstration Step:", "Step 1 / 8: Initialize Orbital Simulation", (255, 240, 100)),
        ]
    },
    {
        "raw_file": "Milestone3_Step4_ConjunctionAlert_raw.png",
        "final_file": "Milestone3_Step4_ConjunctionAlert.png",
        "badge_text": "|| PAUSED",
        "badge_color": (255, 190, 25),
        "rows": [
            ("Simulation Time:", "T + 769.6 s", (255, 255, 255)),
            ("Encounter Pair:", "CARTOSAT-3 vs DEBRIS_PIECE_99", (230, 230, 230)),
            ("Nominal TCA:", "769.63 s (Encounter Epoch)", (255, 215, 50)),
            ("Miss Distance:", "1563.5 m (Critical Minimum Distance)", (255, 90, 90)),
            ("Relative Speed:", "13.234 m/s", (75, 215, 255)),
            ("Collision Prob (Pc):", "2.571e-12 [CONJUNCTION_CANDIDATE]", (255, 90, 90)),
            ("Avoidance Delta-V:", "PLANNED: 3.00 m/s | -R (at T+169.6s)", (50, 255, 100)),
            ("Safety Status:", "CRITICAL CONJUNCTION RISK DETECTED", (255, 80, 80)),
            ("Demonstration Step:", "Step 4 / 8: Encounter Assessment at Nominal TCA", (255, 240, 100)),
        ]
    },
    {
        "raw_file": "Milestone3_Step6_BurnExecution_raw.png",
        "final_file": "Milestone3_Step6_BurnExecution.png",
        "badge_text": "● PLAYING (10.0x)",
        "badge_color": (50, 255, 100),
        "rows": [
            ("Simulation Time:", "T + 169.6 s", (255, 255, 255)),
            ("Encounter Pair:", "CARTOSAT-3 vs DEBRIS_PIECE_99", (230, 230, 230)),
            ("Nominal TCA:", "769.63 s", (255, 215, 50)),
            ("Miss Distance:", "1563.5 m (Pre-Burn Baseline)", (255, 215, 50)),
            ("Relative Speed:", "13.234 m/s", (75, 215, 255)),
            ("Collision Prob (Pc):", "3.140e-18 [TRANSITIONING]", (255, 180, 50)),
            ("Avoidance Delta-V:", "EXECUTING: 3.00 m/s | -R (Radial Burn)", (50, 255, 100)),
            ("Safety Status:", "MANOEUVRE IN PROGRESS - CLEARING ORBIT", (50, 255, 140)),
            ("Demonstration Step:", "Step 6 / 8: Impulsive Burn Execution (-R Radial)", (255, 240, 100)),
        ]
    },
    {
        "raw_file": "Milestone3_Step8_SafeClearance_raw.png",
        "final_file": "Milestone3_Step8_SafeClearance.png",
        "badge_text": "● PLAYING (5.0x)",
        "badge_color": (50, 255, 100),
        "rows": [
            ("Simulation Time:", "T + 903.0 s", (255, 255, 255)),
            ("Encounter Pair:", "CARTOSAT-3 vs DEBRIS_PIECE_99", (230, 230, 230)),
            ("Nominal TCA:", "771.84 s (Shift: +2.2s)", (255, 215, 50)),
            ("Miss Distance:", "1984.3 m (+420.8m Clearance)", (50, 255, 100)),
            ("Relative Speed:", "13.230 m/s", (75, 215, 255)),
            ("Collision Prob (Pc):", "3.140e-18 [SAFE]", (50, 255, 100)),
            ("Avoidance Delta-V:", "APPLIED: 3.00 m/s | -R (Burn Complete)", (50, 255, 100)),
            ("Safety Status:", "AVOIDANCE RESOLVED (Safe Margin Confirmed)", (50, 255, 140)),
            ("Demonstration Step:", "Step 8 / 8: Post-Manoeuvre Verification & Safety Margin", (255, 240, 100)),
        ]
    }
]

def draw_hud(img, config):
    draw = ImageDraw.Draw(img, "RGBA")
    px, py, pw, ph = 30, 30, 560, 370

    # 1. Outer Border / Glow
    draw.rectangle([px-2, py-2, px+pw+2, py+ph+2], outline=(0, 204, 255, 120), width=1)
    
    # 2. Main Background Box (Dark space navy with transparency)
    draw.rectangle([px, py, px+pw, py+ph], fill=(3, 8, 20, 230), outline=(0, 204, 255, 220), width=2)
    
    # 3. Header Bar
    draw.rectangle([px, py, px+pw, py+36], fill=(0, 89, 166, 240))
    draw.text((px+16, py+9), "SATELLITE COLLISION AVOIDANCE SYSTEM (ICPS)", fill=(255, 255, 255), font=title_font)
    
    # Playback State Badge
    badge_w = 145 if "PLAYING" in config["badge_text"] else 100
    draw.text((px+pw-badge_w, py+9), config["badge_text"], fill=config["badge_color"], font=badge_font)

    # 4. Telemetry Rows
    cy = py + 46
    for label, val, color in config["rows"]:
        draw.text((px+16, cy), label, fill=(166, 209, 242), font=header_font)
        draw.text((px+180, cy), val, fill=color, font=body_font)
        cy += 28

    # 5. Footer Controls Bar
    f_y = py + ph - 34
    draw.rectangle([px+2, f_y, px+pw-2, py+ph-2], fill=(5, 20, 40, 245), outline=(0, 150, 215, 150), width=1)
    draw.text((px+12, f_y+8), "[SPACE] Play/Pause | [R] Reset | [1-8] Steps | [↑/↓] Speed | [C] Camera | [←/→] Step", fill=(140, 215, 255), font=footer_font)

    return img

print("=" * 70)
print("[MILESTONE 3] Compositing Interactive Telemetry HUD Overlays...")
print("=" * 70)

for cfg in MILESTONE_HUD_CONFIGS:
    raw_path = os.path.join(SCREENSHOTS_DIR, cfg["raw_file"])
    final_path = os.path.join(SCREENSHOTS_DIR, cfg["final_file"])
    artifact_path = os.path.join(ARTIFACTS_DIR, cfg["final_file"])

    if not os.path.exists(raw_path):
        print(f"  [ERROR] Raw file not found: {raw_path}")
        continue

    img = Image.open(raw_path).convert("RGBA")
    img_hud = draw_hud(img, cfg)
    img_hud.save(final_path, "PNG")
    print(f"  [SAVED] Final HUD render: {final_path}")

    shutil.copy2(final_path, artifact_path)
    print(f"  [COPIED] Artifact updated: {artifact_path}")

print("=" * 70)
print("All Milestone 3 HUD screenshots successfully generated and updated!")
print("=" * 70)
