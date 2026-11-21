"""
Test HUD overlay drawing with Pillow
"""
from PIL import Image, ImageDraw, ImageFont
import os

w, h = 1920, 1080
img = Image.new("RGBA", (w, h), (10, 15, 25, 255))
draw = ImageDraw.Draw(img)

# Try loading font or use default
try:
    title_font = ImageFont.truetype("arialbd.ttf", 15)
    header_font = ImageFont.truetype("arialbd.ttf", 13)
    body_font = ImageFont.truetype("consola.ttf", 13)
    footer_font = ImageFont.truetype("arialbd.ttf", 12)
except Exception:
    title_font = ImageFont.load_default()
    header_font = ImageFont.load_default()
    body_font = ImageFont.load_default()
    footer_font = ImageFont.load_default()

px, py, pw, ph = 30, 30, 560, 370

# Outer glow / shadow
draw.rectangle([px-2, py-2, px+pw+2, py+ph+2], outline=(0, 204, 255, 120), width=1)
# Background
draw.rectangle([px, py, px+pw, py+ph], fill=(3, 8, 20, 230), outline=(0, 204, 255, 220), width=2)
# Header
draw.rectangle([px, py, px+pw, py+36], fill=(0, 89, 166, 240))
draw.text((px+16, py+9), "SATELLITE COLLISION AVOIDANCE SYSTEM (ICPS)", fill=(255, 255, 255), font=title_font)
draw.text((px+pw-140, py+9), "● PLAYING (5.0x)", fill=(50, 255, 100), font=title_font)

rows = [
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

cy = py + 46
for label, val, color in rows:
    draw.text((px+16, cy), label, fill=(166, 209, 242), font=header_font)
    draw.text((px+180, cy), val, fill=color, font=body_font)
    cy += 28

# Footer Controls Bar
f_y = py + ph - 34
draw.rectangle([px+2, f_y, px+pw-2, py+ph-2], fill=(5, 20, 40, 240), outline=(0, 150, 215, 150), width=1)
draw.text((px+12, f_y+8), "[SPACE] Play/Pause | [R] Reset | [1-8] Steps | [↑/↓] Speed | [C] Camera | [←/→] Step", fill=(140, 215, 255), font=footer_font)

img.save("UnrealProject/Saved/Screenshots/test_hud_render.png")
print("Saved test_hud_render.png successfully!")
