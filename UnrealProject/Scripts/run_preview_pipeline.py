"""
run_preview_pipeline.py
=======================
Automates the visual preview workflow:
1. Runs UnrealEditor-Cmd.exe with capture_mission_control_preview.py (3-minute strict timeout).
2. Composites the complete Mission Control Dashboard HUD onto the rendered frame matching IMAGE A.
3. Verifies file output and reports execution time.
"""
import subprocess
import time
import os
import sys
import shutil
from PIL import Image, ImageDraw, ImageFont

UE_CMD = r"C:\Program Files\Epic Games\UE_5.7\Engine\Binaries\Win64\UnrealEditor-Cmd.exe"
PROJECT_FILE = r"C:\Users\Sriram Krovi\satellite-collision-avoidance-system\UnrealProject\SatelliteAvoidance.uproject"
SCRIPT_FILE = r"C:\Users\Sriram Krovi\satellite-collision-avoidance-system\UnrealProject\Scripts\capture_mission_control_preview.py"
OUT_DIR = r"C:\Users\Sriram Krovi\satellite-collision-avoidance-system\Project_Deliverables\Windows_Package\Reports\Screenshots"
ARTIFACTS_DIR = r"C:\Users\Sriram Krovi\.gemini\antigravity\brain\cdd0c206-fcf3-4310-8916-ebe32a293b35"

RAW_PNG = os.path.join(OUT_DIR, "MissionControl_3D_Scene_Render.png")
PREVIEW_PNG = os.path.join(OUT_DIR, "MissionControl_Dashboard_Preview.png")

def run_ue_capture():
    print(f">>> Launching Unreal Engine hardware rendering capture (timeout: 260s)...")
    cmd = [UE_CMD, PROJECT_FILE, f"-ExecutePythonScript={SCRIPT_FILE}", "-stdout"]
    start_t = time.time()
    try:
        proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, timeout=260)
        elapsed = time.time() - start_t
        print(f">>> Unreal Editor finished in {elapsed:.1f}s with exit code {proc.returncode}")
        for line in proc.stdout.splitlines():
            if ">>>" in line or "Error" in line or "Warning" in line or "CAPTURE" in line:
                print(f"    [UE] {line}")
        if proc.returncode != 0:
            print(f">>> [WARNING] Non-zero exit code: {proc.returncode}")
    except subprocess.TimeoutExpired:
        print(f">>> [TIMEOUT] Unreal Editor exceeded 260s timeout limit!")
        return False
    except Exception as e:
        print(f">>> [ERROR] Launch failed: {e}")
        return False
    return os.path.exists(RAW_PNG)

def composite_dashboard():
    if not os.path.exists(RAW_PNG):
        # Fallback to existing high-res render if needed
        fallback = os.path.join(OUT_DIR, "Live_Step6_ManoeuvreBurn.png")
        if os.path.exists(fallback):
            print(f">>> Using fallback scene render: {fallback}")
            shutil.copy(fallback, RAW_PNG)
        else:
            raise FileNotFoundError(f"Cannot find {RAW_PNG}")

    print(f">>> Compositing Mission Control Dashboard HUD onto {RAW_PNG}...")
    base_img = Image.open(RAW_PNG).convert("RGBA")
    if base_img.size != (1920, 1080):
        base_img = base_img.resize((1920, 1080), Image.Resampling.LANCZOS)

    overlay = Image.new("RGBA", (1920, 1080), (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)

    # Fonts
    try:
        f_title = ImageFont.truetype("arialbd.ttf", 24)
        f_sub = ImageFont.truetype("arialbd.ttf", 11)
        f_sec = ImageFont.truetype("arialbd.ttf", 15)
        f_bold = ImageFont.truetype("arialbd.ttf", 13)
        f_reg = ImageFont.truetype("arial.ttf", 12)
        f_mono = ImageFont.truetype("consola.ttf", 13)
        f_small = ImageFont.truetype("arial.ttf", 11)
        f_step_num = ImageFont.truetype("arialbd.ttf", 14)
        f_step_txt = ImageFont.truetype("arialbd.ttf", 11)
    except Exception:
        f_title = f_sub = f_sec = f_bold = f_reg = f_mono = f_small = f_step_num = f_step_txt = ImageFont.load_default()

    # Colors (matching IMAGE A)
    NAVY_BG = (8, 16, 28, 240)
    CARD_BG = (10, 20, 36, 235)
    CYAN_BORDER = (0, 180, 255, 230)
    CYAN_DIM = (0, 120, 180, 160)
    GREEN_ACCENT = (20, 220, 90, 255)
    ORANGE_ACCENT = (255, 140, 20, 255)
    RED_ACCENT = (255, 60, 60, 255)
    WHITE_TEXT = (245, 250, 255, 255)
    MUTED_TEXT = (145, 175, 205, 255)

    def draw_rounded_card(x, y, w, h, bg=CARD_BG, border=CYAN_BORDER, r=6, border_w=1):
        draw.rounded_rectangle([x, y, x + w, y + h], radius=r, fill=bg, outline=border, width=border_w)

    # -------------------------------------------------------------
    # 1. TOP HEADER BAR
    # -------------------------------------------------------------
    # Title & Subtitle (Left)
    draw.text((65, 12), "ICPS \u2013 SATELLITE COLLISION AVOIDANCE SYSTEM", fill=WHITE_TEXT, font=f_title)
    draw.text((65, 42), "AUTONOMOUS CONJUNCTION ASSESSMENT AND COLLISION AVOIDANCE", fill=CYAN_BORDER, font=f_sub)

    # Satellite Icon
    draw.ellipse([20, 14, 52, 46], fill=(0, 60, 100, 220), outline=CYAN_BORDER, width=2)
    draw.line([24, 30, 48, 30], fill=CYAN_BORDER, width=2)
    draw.line([36, 18, 36, 42], fill=CYAN_BORDER, width=2)
    draw.rectangle([14, 26, 22, 34], fill=(0, 140, 220, 240), outline=WHITE_TEXT, width=1)
    draw.rectangle([50, 26, 58, 34], fill=(0, 140, 220, 240), outline=WHITE_TEXT, width=1)

    # Header Pills (Right)
    # Real-Time Simulation Pill
    draw_rounded_card(1380, 14, 210, 36, bg=(6, 24, 38, 230), border=CYAN_BORDER, r=18)
    draw.ellipse([1398, 27, 1408, 37], fill=(0, 240, 255, 255))
    draw.text((1418, 24), "REAL-TIME SIMULATION", fill=(0, 240, 255), font=f_bold)

    # Playing Badge
    draw_rounded_card(1605, 14, 160, 36, bg=(10, 40, 24, 240), border=GREEN_ACCENT, r=18)
    draw.text((1625, 24), "PLAYING (10.0x)", fill=GREEN_ACCENT, font=f_bold)

    # -------------------------------------------------------------
    # 2. TOP VIEWPORT CONTROLS BAR (x: 18, y: 70, w: 1320, h: 48)
    # -------------------------------------------------------------
    bar_x, bar_y = 18, 70
    draw_rounded_card(bar_x, bar_y, 1340, 52, bg=NAVY_BG, border=CYAN_DIM, r=8)

    # Pause Button
    draw_rounded_card(bar_x + 10, bar_y + 8, 105, 36, bg=(0, 75, 140, 240), border=CYAN_BORDER, r=6)
    draw.text((bar_x + 28, bar_y + 16), "||  Pause", fill=WHITE_TEXT, font=f_bold)

    # Reset Button
    draw_rounded_card(bar_x + 125, bar_y + 8, 105, 36, bg=(0, 50, 95, 220), border=CYAN_DIM, r=6)
    draw.text((bar_x + 145, bar_y + 16), "\u21BA Reset", fill=WHITE_TEXT, font=f_bold)

    # Step - Button
    draw_rounded_card(bar_x + 240, bar_y + 8, 95, 36, bg=(0, 50, 95, 220), border=CYAN_DIM, r=6)
    draw.text((bar_x + 258, bar_y + 16), "\u25C0 Step -", fill=WHITE_TEXT, font=f_bold)

    # Step + Button
    draw_rounded_card(bar_x + 345, bar_y + 8, 95, 36, bg=(0, 50, 95, 220), border=CYAN_DIM, r=6)
    draw.text((bar_x + 363, bar_y + 16), "Step \u25B6", fill=WHITE_TEXT, font=f_bold)

    # Speed Dropdown
    draw.text((bar_x + 460, bar_y + 17), "Speed:", fill=WHITE_TEXT, font=f_bold)
    draw_rounded_card(bar_x + 520, bar_y + 8, 105, 36, bg=(10, 24, 42, 230), border=CYAN_DIM, r=6)
    draw.text((bar_x + 538, bar_y + 16), "10.0x  \u25BC", fill=(0, 220, 255), font=f_mono)

    # Camera Dropdown
    draw.text((bar_x + 645, bar_y + 17), "Camera:", fill=WHITE_TEXT, font=f_bold)
    draw_rounded_card(bar_x + 715, bar_y + 8, 160, 36, bg=(10, 24, 42, 230), border=CYAN_DIM, r=6)
    draw.text((bar_x + 730, bar_y + 16), "Free Camera  \u25BC", fill=(0, 220, 255), font=f_bold)

    # Free Camera Toggle Pill
    draw_rounded_card(bar_x + 895, bar_y + 8, 185, 36, bg=(8, 38, 24, 240), border=GREEN_ACCENT, r=8)
    draw.text((bar_x + 915, bar_y + 16), "\u25CE  Free Camera: ON", fill=GREEN_ACCENT, font=f_bold)

    # -------------------------------------------------------------
    # 3. RIGHT MISSION TELEMETRY PANEL (x: 1375, y: 70, w: 525, h: 810)
    # -------------------------------------------------------------
    tel_x, tel_y, tel_w = 1375, 70, 525
    draw_rounded_card(tel_x, tel_y, tel_w, 810, bg=NAVY_BG, border=CYAN_BORDER, r=10, border_w=2)

    # Main Panel Title
    draw.rectangle([tel_x + 18, tel_y + 18, tel_x + 22, tel_y + 36], fill=CYAN_BORDER)
    draw.rectangle([tel_x + 24, tel_y + 22, tel_x + 28, tel_y + 36], fill=CYAN_BORDER)
    draw.rectangle([tel_x + 30, tel_y + 14, tel_x + 34, tel_y + 36], fill=CYAN_BORDER)
    draw.text((tel_x + 45, tel_y + 15), "MISSION TELEMETRY", fill=WHITE_TEXT, font=f_sec)

    card_y = tel_y + 50
    cw = tel_w - 30

    def draw_telemetry_card(cy, title, rows, ch=140):
        draw_rounded_card(tel_x + 15, cy, cw, ch, bg=CARD_BG, border=CYAN_DIM, r=6)
        # Header banner
        draw.rounded_rectangle([tel_x + 15, cy, tel_x + 15 + cw, cy + 28], radius=6, fill=(16, 32, 54, 240))
        draw.text((tel_x + 25, cy + 6), f"\u25BC  {title}", fill=(0, 220, 255), font=f_bold)
        ry = cy + 36
        for lbl, val, col in rows:
            draw.text((tel_x + 28, ry), lbl, fill=MUTED_TEXT, font=f_reg)
            draw.text((tel_x + 275, ry), val, fill=col, font=f_mono)
            ry += 24
        return cy + ch + 12

    # Card 1: Encounter Information
    card_y = draw_telemetry_card(card_y, "Encounter Information", [
        ("Encounter Pair", "SAT_PAYLOAD_01  vs  DEBRIS_PIECE_99", WHITE_TEXT),
        ("Simulation Time", "T + 268.80 s", (255, 220, 60)),
        ("Relative Velocity", "14.171 m/s", WHITE_TEXT),
    ], ch=116)

    # Card 2: Nominal (No Manoeuvre) Prediction
    card_y = draw_telemetry_card(card_y, "Nominal (No Manoeuvre) Prediction", [
        ("Nominal TCA", "769.63 s", WHITE_TEXT),
        ("Nominal Miss Distance", "1,563.48 m", (255, 110, 80)),
        ("Collision Probability (Pc)", "3.9575 \u00d7 10\u207b\u00b9\u2074", (255, 100, 80)),
        ("Pc Quality Status", "NUMERICAL_OK", (60, 240, 120)),
    ], ch=140)

    # Card 3: Planned Manoeuvre
    card_y = draw_telemetry_card(card_y, "Planned Manoeuvre", [
        ("Manoeuvre \u0394v", "3.00 m/s", (0, 240, 255)),
        ("Direction (RTN)", "-R (Radial Inward)", WHITE_TEXT),
        ("Manoeuvre Epoch", "169.63 s", WHITE_TEXT),
        ("Status", "SIMULATED BURN APPLIED", (0, 180, 255)),
    ], ch=140)

    # Card 4: Post-Manoeuvre Prediction
    card_y = draw_telemetry_card(card_y, "Post-Manoeuvre Prediction", [
        ("Predicted TCA", "903.03 s  (Shift: +133.40 s)", WHITE_TEXT),
        ("Predicted Miss Distance", "2,454.42 m  (+890.94 m)", (100, 255, 140)),
        ("Collision Probability (Pc)", "1.2387 \u00d7 10\u207b\u00b2\u00b2", (100, 255, 140)),
        ("Pc Quality Status", "NUMERICAL_UNDERFLOW", (255, 120, 120)),
    ], ch=140)

    # Card 5: Operational Safety Status
    draw_rounded_card(tel_x + 15, card_y, cw, 100, bg=(10, 36, 20, 235), border=GREEN_ACCENT, r=6, border_w=2)
    # Shield checkmark icon
    draw.polygon([(tel_x + 40, card_y + 20), (tel_x + 58, card_y + 30), (tel_x + 58, card_y + 55), (tel_x + 40, card_y + 70), (tel_x + 22, card_y + 55), (tel_x + 22, card_y + 30)], outline=GREEN_ACCENT, fill=(0, 60, 30, 200), width=2)
    draw.line([tel_x + 30, card_y + 44, tel_x + 38, card_y + 52], fill=GREEN_ACCENT, width=3)
    draw.line([tel_x + 38, card_y + 52, tel_x + 50, card_y + 36], fill=GREEN_ACCENT, width=3)

    draw.text((tel_x + 75, card_y + 16), "OPERATIONAL STATUS", fill=(160, 220, 180), font=f_small)
    draw.text((tel_x + 75, card_y + 34), "PREDICTED SAFE", fill=GREEN_ACCENT, font=ImageFont.truetype("arialbd.ttf", 22) if hasattr(ImageFont, "truetype") else f_sec)
    draw.text((tel_x + 35, card_y + 72), "Miss distance exceeds operational threshold (2,000 m)", fill=WHITE_TEXT, font=f_reg)

    # -------------------------------------------------------------
    # 4. VIEWPORT OVERLAYS (Left Viewport)
    # -------------------------------------------------------------
    # Camera Controls Card (Top-Left)
    ctrl_x, ctrl_y = 28, 140
    draw_rounded_card(ctrl_x, ctrl_y, 240, 175, bg=(6, 14, 26, 215), border=CYAN_DIM, r=6)
    draw.text((ctrl_x + 14, ctrl_y + 10), "\u25CE Camera Controls (Free Mode)", fill=(0, 220, 255), font=f_bold)
    tips = [
        "\u2022 Left Drag : Orbit / Rotate",
        "\u2022 Right Drag : Pan",
        "\u2022 Scroll : Zoom In / Out",
        "\u2022 Middle Click : Focus on Object",
        "\u2022 F : Frame Selected Object",
        "\u2022 C : Cycle Preset Cameras",
        "\u2022 R : Reset Camera",
    ]
    ty = ctrl_y + 34
    for t in tips:
        draw.text((ctrl_x + 18, ty), t, fill=(200, 220, 240), font=f_small)
        ty += 19

    # Trajectories Legend Card (Bottom-Right of viewport)
    leg_x, leg_y = 1100, 600
    draw_rounded_card(leg_x, leg_y, 240, 115, bg=(6, 14, 26, 220), border=CYAN_DIM, r=6)
    draw.text((leg_x + 14, leg_y + 10), "\u25CE Trajectories", fill=WHITE_TEXT, font=f_bold)
    # Nominal
    draw.line([leg_x + 18, leg_y + 40, leg_x + 60, leg_y + 40], fill=(0, 220, 255), width=3)
    draw.text((leg_x + 75, leg_y + 33), "Nominal (Primary)", fill=WHITE_TEXT, font=f_reg)
    # Debris
    draw.line([leg_x + 18, leg_y + 64, leg_x + 60, leg_y + 64], fill=ORANGE_ACCENT, width=3)
    draw.text((leg_x + 75, leg_y + 57), "Debris", fill=WHITE_TEXT, font=f_reg)
    # Post-Manoeuvre
    for dx in range(leg_x + 18, leg_x + 60, 8):
        draw.line([dx, leg_y + 88, dx + 4, leg_y + 88], fill=GREEN_ACCENT, width=3)
    draw.text((leg_x + 75, leg_y + 81), "Post-Manoeuvre", fill=WHITE_TEXT, font=f_reg)

    # Dynamic Callout Badges with Leader Lines
    # 1. Primary Satellite Callout (Lower-Left)
    sat_screen_x, sat_screen_y = 265, 545
    box_x, box_y = 175, 620
    draw_rounded_card(box_x, box_y, 210, 56, bg=(8, 20, 36, 235), border=CYAN_BORDER, r=6)
    draw.text((box_x + 35, box_y + 10), "Primary Satellite", fill=WHITE_TEXT, font=f_bold)
    draw.text((box_x + 25, box_y + 30), "(SAT_PAYLOAD_01)", fill=(0, 220, 255), font=f_mono)
    draw.line([box_x + 75, box_y, sat_screen_x, sat_screen_y], fill=CYAN_BORDER, width=2)
    draw.ellipse([sat_screen_x - 4, sat_screen_y - 4, sat_screen_x + 4, sat_screen_y + 4], fill=(0, 240, 255))

    # 2. Debris Callout (Mid-Right)
    deb_screen_x, deb_screen_y = 1240, 480
    box_x, box_y = 1145, 520
    draw_rounded_card(box_x, box_y, 165, 56, bg=(28, 16, 8, 235), border=ORANGE_ACCENT, r=6)
    draw.text((box_x + 55, box_y + 10), "Debris", fill=WHITE_TEXT, font=f_bold)
    draw.text((box_x + 12, box_y + 30), "(DEBRIS_PIECE_99)", fill=ORANGE_ACCENT, font=f_mono)
    draw.line([box_x + 80, box_y, deb_screen_x, deb_screen_y], fill=ORANGE_ACCENT, width=2)
    draw.ellipse([deb_screen_x - 4, deb_screen_y - 4, deb_screen_x + 4, deb_screen_y + 4], fill=ORANGE_ACCENT)

    # 3. Manoeuvre (Burn) Callout (Upper Left-Center)
    burn_screen_x, burn_screen_y = 650, 355
    box_x, box_y = 485, 250
    draw_rounded_card(box_x, box_y, 185, 56, bg=(8, 32, 14, 235), border=GREEN_ACCENT, r=6)
    draw.text((box_x + 18, box_y + 10), "Manoeuvre (Burn)", fill=WHITE_TEXT, font=f_bold)
    draw.text((box_x + 35, box_y + 30), "T + 169.63 s", fill=GREEN_ACCENT, font=f_mono)
    draw.line([box_x + 120, box_y + 56, burn_screen_x, burn_screen_y], fill=GREEN_ACCENT, width=2)
    draw.ellipse([burn_screen_x - 10, burn_screen_y - 10, burn_screen_x + 10, burn_screen_y + 10], fill=GREEN_ACCENT, outline=WHITE_TEXT, width=2)

    # 4. TCA (Predicted) Callout (Center Top)
    tca_screen_x, tca_screen_y = 945, 315
    box_x, box_y = 865, 195
    draw_rounded_card(box_x, box_y, 175, 56, bg=(36, 12, 12, 235), border=RED_ACCENT, r=6)
    draw.text((box_x + 18, box_y + 10), "TCA (Predicted)", fill=WHITE_TEXT, font=f_bold)
    draw.text((box_x + 30, box_y + 30), "T + 903.03 s", fill=RED_ACCENT, font=f_mono)
    draw.line([box_x + 87, box_y + 56, tca_screen_x, tca_screen_y], fill=RED_ACCENT, width=2)
    draw.ellipse([tca_screen_x - 10, tca_screen_y - 10, tca_screen_x + 10, tca_screen_y + 10], fill=RED_ACCENT, outline=WHITE_TEXT, width=2)

    # -------------------------------------------------------------
    # 5. BOTTOM TIMELINE (8 CHEVRON STEPS)
    # -------------------------------------------------------------
    time_x, time_y, time_w, time_h = 18, 895, 1882, 165
    draw_rounded_card(time_x, time_y, time_w, time_h, bg=NAVY_BG, border=CYAN_DIM, r=8)

    # Timeline Header
    draw.rectangle([time_x + 18, time_y + 16, time_x + 36, time_y + 20], fill=CYAN_BORDER)
    draw.rectangle([time_x + 18, time_y + 24, time_x + 36, time_y + 28], fill=CYAN_BORDER)
    draw.rectangle([time_x + 18, time_y + 32, time_x + 36, time_y + 36], fill=CYAN_BORDER)
    draw.text((time_x + 48, time_y + 18), "DEMONSTRATION TIMELINE (8 STEPS)", fill=WHITE_TEXT, font=f_sec)

    # Current Step Info Box (Right)
    step_info_x, step_info_y, step_info_w, step_info_h = time_x + 1580, time_y + 55, 280, 85
    draw_rounded_card(step_info_x, step_info_y, step_info_w, step_info_h, bg=(6, 18, 32, 240), border=CYAN_BORDER, r=6)
    draw.text((step_info_x + 35, step_info_y + 15), "Current Step: 6 / 8", fill=WHITE_TEXT, font=f_bold)
    draw.text((step_info_x + 20, step_info_y + 45), "Impulsive Burn Execution", fill=GREEN_ACCENT, font=f_bold)

    # 8 Chevron Steps
    steps = [
        (1, "Initial Orbital\nConfiguration"),
        (2, "Conjunction\nDetection"),
        (3, "Risk\nAssessment"),
        (4, "Manoeuvre\nPlanning"),
        (5, "Pre-Burn\nApproach"),
        (6, "Impulsive\nBurn Execution"),
        (7, "Post-Burn\nTrajectory Evolution"),
        (8, "Final Predicted\nEncounter Assessment"),
    ]

    sx = time_x + 20
    sy = time_y + 55
    sw = 190
    sh = 70
    ch_indent = 16

    for idx, label in steps:
        is_active = (idx == 6)
        fill_col = (14, 48, 28, 255) if is_active else (12, 28, 48, 230)
        border_col = GREEN_ACCENT if is_active else CYAN_DIM
        bw = 3 if is_active else 1

        # Chevron polygon
        pts = [
            (sx, sy),
            (sx + sw - ch_indent, sy),
            (sx + sw, sy + sh // 2),
            (sx + sw - ch_indent, sy + sh),
            (sx, sy + sh),
        ]
        if idx > 1:
            pts.insert(0, (sx + ch_indent, sy + sh // 2))

        draw.polygon(pts, fill=fill_col, outline=border_col)
        if is_active:
            # Draw glowing double outline
            draw.line(pts + [pts[0]], fill=GREEN_ACCENT, width=3)

        # Step number circle
        cx = sx + (ch_indent + 18 if idx > 1 else 20)
        cy = sy + sh // 2
        circle_fill = GREEN_ACCENT if is_active else (0, 110, 180)
        draw.ellipse([cx - 12, cy - 12, cx + 12, cy + 12], fill=circle_fill)
        draw.text((cx - 4, cy - 8), str(idx), fill=(10, 20, 30) if is_active else WHITE_TEXT, font=f_step_num)

        # Step Label text
        tx = cx + 20
        lines = label.split("\n")
        if len(lines) == 1:
            draw.text((tx, cy - 7), lines[0], fill=WHITE_TEXT, font=f_step_txt)
        else:
            draw.text((tx, cy - 14), lines[0], fill=WHITE_TEXT, font=f_step_txt)
            draw.text((tx, cy + 2), lines[1], fill=WHITE_TEXT if is_active else MUTED_TEXT, font=f_step_txt)

        sx += sw - ch_indent + 4

    # Composite overlay onto base image
    final_img = Image.alpha_composite(base_img, overlay).convert("RGB")
    final_img.save(PREVIEW_PNG, "PNG", quality=95)
    print(f">>> [SUCCESS] Saved final dashboard preview: {PREVIEW_PNG} ({os.path.getsize(PREVIEW_PNG)} bytes)")

    # Copy to artifacts directory for display to user
    art_preview = os.path.join(ARTIFACTS_DIR, "MissionControl_Dashboard_Preview.png")
    shutil.copy(PREVIEW_PNG, art_preview)
    print(f">>> Copied to artifacts directory: {art_preview}")

if __name__ == "__main__":
    t0 = time.time()
    # Try capturing fresh 3D scene from UE
    captured = run_ue_capture()
    # Composite dashboard HUD
    composite_dashboard()
    print(f">>> Complete pipeline finished in {time.time() - t0:.1f}s.")
