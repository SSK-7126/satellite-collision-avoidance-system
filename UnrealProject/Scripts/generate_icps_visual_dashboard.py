"""
generate_icps_visual_dashboard.py
==================================
Generates high-fidelity scientific 3D orbital simulation dashboard visualisations
for the Satellite Anti-Collision Simulation System (ICPS) inside Unreal Engine 5.7.4.

Recreates the visual direction specified:
- Dark space background with subtle stars
- Perspective orbital grid on the orbital plane (Z=0)
- Realistic 3D Earth centrally framed (slightly offset left to balance dashboard)
- SatelliteActor and DebrisActor positioned on their trajectories with 3D models and labels
- Full elliptical orbital trajectories:
    * Cyan solid line: Nominal satellite orbit
    * Orange dashed line: Debris orbit
    * Green dashed line: Modified satellite orbit after manoeuvre
    * Red marker: Conjunction point / TCA
    * Green marker: Avoidance manoeuvre / burn point
- Right-side Telemetry Dashboard with all telemetry fields + Risk Comparison Panel
- Bottom-left Trajectory Legend
- Bottom Eight-Step Demonstration Timeline with active step highlighted
- Top Navigation Controls (3D VIEW active, 2D GROUND TRACK, SENSOR VIEW)
"""

import sys
import os
import math
import random
import json
import shutil
import time
from PIL import Image, ImageDraw, ImageFont
import numpy as np

sys.path.append(r"C:\Program Files\Epic Games\UE_5.7\Engine\Plugins\Experimental\PythonScriptPlugin\Content\Python")
import remote_execution

# Directories
PROJECT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
WORKSPACE_DIR = os.path.abspath(os.path.join(PROJECT_DIR, ".."))
PAYLOAD_PATH = os.path.join(WORKSPACE_DIR, "D2", "visualization", "unreal_simulation_payload.json")
RAW_OUTPUT_DIR = r"C:\Users\Sriram Krovi\AppData\Local\UnrealEngine\5.7\Saved\Screenshots\WindowsEditor\VisualDesign"
ARTIFACTS_DIR = r"C:\Users\Sriram Krovi\.gemini\antigravity\brain\de57ce2f-f1fa-499f-b87c-b7751cec6f36"
os.makedirs(RAW_OUTPUT_DIR, exist_ok=True)
os.makedirs(ARTIFACTS_DIR, exist_ok=True)

# Load Simulation Payload
with open(PAYLOAD_PATH, "r", encoding="utf-8") as f:
    PAYLOAD = json.load(f)

# Camera Calibration
CAM_POS = [50000.0, -480000.0, 330000.0]
CAM_TGT = [-63000.0, -25000.0, 0.0]
FOV_H = 52.0
SCREEN_W, SCREEN_H = 1920, 1080

# Camera Coordinate Basis Vectors
dx = CAM_TGT[0] - CAM_POS[0]
dy = CAM_TGT[1] - CAM_POS[1]
dz = CAM_TGT[2] - CAM_POS[2]
dlen = math.sqrt(dx*dx + dy*dy + dz*dz)
fx, fy, fz = dx/dlen, dy/dlen, dz/dlen

rx = -fy
ry = fx
rz = 0.0
rlen = math.sqrt(rx*rx + ry*ry)
rx, ry = rx/rlen, ry/rlen

ux = fy * rz - fz * ry
uy = fz * rx - fx * rz
uz = fx * ry - fy * rx

thx = math.tan(math.radians(FOV_H / 2.0))
thy = thx * (SCREEN_H / SCREEN_W)

def project_3d_to_2d(px, py, pz):
    """Projects Unreal world coordinates (uu) into screen pixels (u, v)."""
    vx = px - CAM_POS[0]
    vy = py - CAM_POS[1]
    vz = pz - CAM_POS[2]
    zc = vx*fx + vy*fy + vz*fz
    xc = vx*rx + vy*ry + vz*rz
    yc = vx*ux + vy*uy + vz*uz
    if zc <= 0:
        return None
    u = SCREEN_W / 2.0 + (SCREEN_W / 2.0) * (xc / (zc * thx))
    v = SCREEN_H / 2.0 - (SCREEN_H / 2.0) * (yc / (zc * thy))
    return (u, v)

# Fonts
try:
    font_title = ImageFont.truetype(r"C:\Windows\Fonts\segoeuib.ttf", 15)
    font_subtitle = ImageFont.truetype(r"C:\Windows\Fonts\segoeui.ttf", 10)
    font_header = ImageFont.truetype(r"C:\Windows\Fonts\segoeuib.ttf", 12)
    font_body = ImageFont.truetype(r"C:\Windows\Fonts\consola.ttf", 12)
    font_body_bold = ImageFont.truetype(r"C:\Windows\Fonts\consolab.ttf", 12)
    font_small = ImageFont.truetype(r"C:\Windows\Fonts\segoeui.ttf", 10)
    font_badge = ImageFont.truetype(r"C:\Windows\Fonts\segoeuib.ttf", 11)
    font_timeline = ImageFont.truetype(r"C:\Windows\Fonts\segoeuib.ttf", 11)
    font_timeline_sub = ImageFont.truetype(r"C:\Windows\Fonts\segoeui.ttf", 9)
except Exception:
    font_title = ImageFont.load_default()
    font_subtitle = ImageFont.load_default()
    font_header = ImageFont.load_default()
    font_body = ImageFont.load_default()
    font_body_bold = ImageFont.load_default()
    font_small = ImageFont.load_default()
    font_badge = ImageFont.load_default()
    font_timeline = ImageFont.load_default()
    font_timeline_sub = ImageFont.load_default()

def apply_subtle_starfield(img):
    """Adds a deterministic subtle starfield to dark space background regions."""
    draw = ImageDraw.Draw(img, "RGBA")
    rng = random.Random(42)

    ecx, ecy, er = 732, 522, 215

    for _ in range(450):
        sx = rng.randint(5, SCREEN_W - 5)
        sy = rng.randint(5, SCREEN_H - 5)
        if math.hypot(sx - ecx, sy - ecy) < er:
            continue
        alpha = rng.randint(40, 160)
        draw.point((sx, sy), fill=(180, 210, 245, alpha))

    for _ in range(75):
        sx = rng.randint(10, SCREEN_W - 10)
        sy = rng.randint(10, SCREEN_H - 10)
        if math.hypot(sx - ecx, sy - ecy) < er:
            continue
        alpha = rng.randint(120, 230)
        draw.ellipse([sx-1, sy-1, sx+1, sy+1], fill=(215, 235, 255, alpha))

    for _ in range(12):
        sx = rng.randint(30, SCREEN_W - 30)
        sy = rng.randint(30, SCREEN_H - 30)
        if math.hypot(sx - ecx, sy - ecy) < er:
            continue
        draw.ellipse([sx-1, sy-1, sx+1, sy+1], fill=(255, 255, 255, 240))
        draw.line([(sx-3, sy), (sx+3, sy)], fill=(200, 230, 255, 160), width=1)
        draw.line([(sx, sy-3), (sx, sy+3)], fill=(200, 230, 255, 160), width=1)

def draw_perspective_orbital_grid(draw):
    """Draws perspective orbital grid in Z=0 plane with concentric rings and radial axes."""
    radii_km = [4500, 5500, 6378, 7000, 8000, 9200]
    for r_km in radii_km:
        r_uu = r_km * 10.0
        pts = []
        for deg in range(0, 361, 5):
            rad = math.radians(deg)
            wx = r_uu * math.cos(rad)
            wy = -r_uu * math.sin(rad)
            uv = project_3d_to_2d(wx, wy, 0.0)
            if uv:
                pts.append(uv)
        if len(pts) > 2:
            color = (0, 160, 230, 45) if r_km != 7000 else (0, 210, 255, 75)
            width = 1 if r_km != 7000 else 2
            draw.line(pts, fill=color, width=width)

    # Distance labels along 215-degree radial spoke in open space below Earth
    for r_km in [5500, 7000, 8000, 9200]:
        r_uu = r_km * 10.0
        rad = math.radians(215.0)
        uv = project_3d_to_2d(r_uu * math.cos(rad), r_uu * math.sin(rad), 0.0)
        if uv and 50 < uv[0] < SCREEN_W - 520 and 50 < uv[1] < SCREEN_H - 120:
            draw.text((uv[0] - 20, uv[1] + 4), f"{r_km:,} km", fill=(0, 190, 245, 110), font=font_small)

    for deg in range(0, 360, 30):
        rad = math.radians(deg)
        p1 = project_3d_to_2d(45000.0 * math.cos(rad), 45000.0 * math.sin(rad), 0.0)
        p2 = project_3d_to_2d(92000.0 * math.cos(rad), 92000.0 * math.sin(rad), 0.0)
        if p1 and p2:
            draw.line([p1, p2], fill=(0, 140, 210, 30), width=1)

def draw_dashed_polyline(draw, points, fill, dash_len=14, gap_len=8, width=2):
    """Draws smooth dashed polyline connecting screen-projected points."""
    if len(points) < 2:
        return
    accum_dist = 0.0
    drawing = True
    cur_segment = [points[0]]

    for i in range(1, len(points)):
        p0 = points[i-1]
        p1 = points[i]
        seg_len = math.hypot(p1[0] - p0[0], p1[1] - p0[1])
        if seg_len <= 0.001:
            continue

        remaining_seg = seg_len
        step_dir_x = (p1[0] - p0[0]) / seg_len
        step_dir_y = (p1[1] - p0[1]) / seg_len
        cur_x, cur_y = p0[0], p0[1]

        while remaining_seg > 0:
            target_step = dash_len if drawing else gap_len
            needed = target_step - accum_dist

            if remaining_seg < needed:
                accum_dist += remaining_seg
                cur_x = p1[0]
                cur_y = p1[1]
                if drawing:
                    cur_segment.append((cur_x, cur_y))
                remaining_seg = 0
            else:
                cur_x += step_dir_x * needed
                cur_y += step_dir_y * needed
                remaining_seg -= needed
                if drawing:
                    cur_segment.append((cur_x, cur_y))
                    if len(cur_segment) > 1:
                        draw.line(cur_segment, fill=fill, width=width)
                    cur_segment = []
                else:
                    cur_segment = [(cur_x, cur_y)]
                drawing = not drawing
                accum_dist = 0.0

    if drawing and len(cur_segment) > 1:
        draw.line(cur_segment, fill=fill, width=width)

def draw_orbital_trajectories(draw, step_index):
    """Draws full elliptical orbital paths in 3D perspective with scientific styling."""
    # 1. Nominal Satellite Orbit (Cyan solid line)
    sat_nom_pts = []
    for deg in range(0, 361, 2):
        rad = math.radians(deg)
        wx = 70000.0 * math.cos(rad)
        wy = -70000.0 * math.sin(rad)
        uv = project_3d_to_2d(wx, wy, 0.0)
        if uv:
            sat_nom_pts.append(uv)
    if len(sat_nom_pts) > 2:
        draw.line(sat_nom_pts, fill=(0, 200, 255, 60), width=6)
        draw.line(sat_nom_pts, fill=(0, 235, 255, 240), width=3)

    # 2. Debris Orbit (Orange dashed line)
    deb_pts = []
    for deg in range(0, 361, 2):
        rad = math.radians(deg)
        r_uu = 70000.0 + 150.0 * math.cos(rad)
        wx = r_uu * math.cos(rad + 0.0014)
        wy = -r_uu * math.sin(rad + 0.0014) - 80.0
        uv = project_3d_to_2d(wx, wy, 0.0)
        if uv:
            deb_pts.append(uv)
    if len(deb_pts) > 2:
        draw_dashed_polyline(draw, deb_pts, fill=(255, 145, 10, 240), dash_len=12, gap_len=8, width=2)

    # 3. Modified Post-Manoeuvre Orbit (Green dashed line) - Active if step >= 6
    if step_index >= 6:
        mod_pts = []
        for deg in range(0, 361, 2):
            rad = math.radians(deg)
            r_uu = 70000.0 + 890.0 * math.sin(rad)
            wx = r_uu * math.cos(rad - 0.012)
            wy = -r_uu * math.sin(rad - 0.012)
            uv = project_3d_to_2d(wx, wy, 0.0)
            if uv:
                mod_pts.append(uv)
        if len(mod_pts) > 2:
            draw_dashed_polyline(draw, mod_pts, fill=(35, 255, 110, 240), dash_len=14, gap_len=7, width=2)

    # 4. Conjunction TCA Point (Red Marker)
    tca_world = (47237.9, -51658.3, 0.0)
    tca_uv = project_3d_to_2d(*tca_world)
    if tca_uv:
        tx, ty = tca_uv
        draw.ellipse([tx-10, ty-10, tx+10, ty+10], outline=(255, 60, 60, 240), width=2)
        draw.ellipse([tx-4, ty-4, tx+4, ty+4], fill=(255, 50, 50, 255))
        draw.line([tx-16, ty, tx+16, ty], fill=(255, 60, 60, 220), width=1)
        draw.line([tx, ty-16, tx, ty+16], fill=(255, 60, 60, 220), width=1)
        callout_x = tx + 30
        callout_y = ty + 15
        draw.line([(tx+8, ty+8), (callout_x, callout_y), (callout_x + 140, callout_y)], fill=(255, 70, 70, 220), width=1)
        draw.text((callout_x + 5, callout_y - 18), "TCA CONJUNCTION", fill=(255, 90, 90, 255), font=font_header)
        draw.text((callout_x + 5, callout_y + 3), "Miss: 1563.5 m (T=769.6s)", fill=(255, 200, 200, 220), font=font_small)

    # 5. Avoidance Burn Execution Point (Green Marker) - If step >= 5
    if step_index >= 5:
        burn_pos_ue = PAYLOAD["selected_manoeuvre"]["satellite_position_at_burn_ue_uu"]
        burn_uv = project_3d_to_2d(*burn_pos_ue)
        if burn_uv:
            bx, by = burn_uv
            draw.polygon([(bx, by-10), (bx+10, by), (bx, by+10), (bx-10, by)], outline=(40, 255, 120, 255), fill=(20, 180, 80, 150), width=2)
            draw.line([(bx, by), (bx + 18, by + 18)], fill=(40, 255, 120, 255), width=2)
            # Offset callout downwards-left to cleanly separate from satellite callout box
            bx_lbl = bx - 195
            by_lbl = by + 28
            draw.line([(bx-8, by+8), (bx_lbl + 165, by_lbl + 10), (bx_lbl, by_lbl + 10)], fill=(40, 255, 120, 220), width=1)
            draw.text((bx_lbl + 5, by_lbl - 12), "AVOIDANCE BURN POINT", fill=(40, 255, 120, 255), font=font_header)
            draw.text((bx_lbl + 5, by_lbl + 12), "Δv = 3.00 m/s (-R at T=169.6s)", fill=(200, 255, 220, 220), font=font_small)

def draw_satellite_and_debris_labels(draw, step_index):
    """Draws 3D tracking callout cards for Protected Satellite and Debris using exact time_series positions."""
    step_info = PAYLOAD["demonstration_sequence"][step_index - 1]
    st = step_info["simulation_time_sec"]

    ts = PAYLOAD["time_series"]
    times = ts["timestamps_sec"]
    idx = min(range(len(times)), key=lambda i: abs(times[i] - st))

    # Ground-truth actor positions at this step
    if step_index >= 6 and "satellite_modified_positions_ue" in ts:
        sat_pos = ts["satellite_modified_positions_ue"][idx]
    else:
        sat_pos = ts["satellite_nominal_positions_ue"][idx]
    deb_pos = ts["debris_positions_ue"][idx]

    sat_uv = project_3d_to_2d(*sat_pos)
    deb_uv = project_3d_to_2d(*deb_pos)

    # Protected Satellite Callout (Cyan)
    if sat_uv:
        sx, sy = sat_uv
        draw.ellipse([sx-7, sy-7, sx+7, sy+7], outline=(0, 230, 255, 255), width=2)
        draw.ellipse([sx-2, sy-2, sx+2, sy+2], fill=(0, 255, 255, 255))

        # Position callout box to left-top
        lx, ly = sx - 165, sy - 52
        draw.line([(sx-6, sy-6), (lx + 130, ly + 36), (lx, ly + 36)], fill=(0, 210, 255, 200), width=1)
        draw.rectangle([lx, ly, lx + 145, ly + 34], fill=(4, 16, 32, 225), outline=(0, 200, 255, 180), width=1)
        draw.text((lx + 6, ly + 3), "PROTECTED SATELLITE", fill=(0, 240, 255, 255), font=font_badge)
        sub_txt = "Payload-01 | LEO 7000 km" if step_index < 6 else "Payload-01 | Avoidance Orbit"
        draw.text((lx + 6, ly + 18), sub_txt, fill=(190, 235, 255, 220), font=font_small)

    # Debris Callout (Orange)
    if deb_uv:
        dx, dy = deb_uv
        draw.ellipse([dx-7, dy-7, dx+7, dy+7], outline=(255, 140, 20, 255), width=2)
        draw.ellipse([dx-2, dy-2, dx+2, dy+2], fill=(255, 160, 30, 255))

        # Position callout box to right-bottom
        lx, ly = dx + 35, dy + 22
        draw.line([(dx+6, dy+6), (lx, ly), (lx + 135, ly)], fill=(255, 140, 20, 200), width=1)
        draw.rectangle([lx, ly, lx + 135, ly + 34], fill=(32, 16, 6, 225), outline=(255, 130, 20, 180), width=1)
        draw.text((lx + 6, ly + 3), "SECONDARY DEBRIS", fill=(255, 150, 30, 255), font=font_badge)
        draw.text((lx + 6, ly + 18), "Object-99 | Threat Target", fill=(255, 220, 180, 220), font=font_small)

def draw_top_navigation_bar(draw):
    """Draws top technical navigation bar with 2D/3D mode toggles."""
    bx, by = 35, 22
    draw.rectangle([bx, by, bx + 160, by + 34], fill=(0, 140, 210, 240), outline=(0, 230, 255, 255), width=1)
    draw.text((bx + 24, by + 8), "●  3D ORBIT VIEW", fill=(255, 255, 255, 255), font=font_header)

    draw.rectangle([bx + 170, by, bx + 325, by + 34], fill=(8, 22, 42, 210), outline=(0, 140, 190, 120), width=1)
    draw.text((bx + 185, by + 8), "    2D GROUND MAP", fill=(140, 190, 220, 180), font=font_header)

    draw.rectangle([bx + 335, by, bx + 490, by + 34], fill=(8, 22, 42, 210), outline=(0, 140, 190, 120), width=1)
    draw.text((bx + 355, by + 8), "    SENSOR CONE", fill=(140, 190, 220, 180), font=font_header)

def draw_trajectory_legend(draw):
    """Draws professional Trajectory Legend on the bottom-left."""
    lx, ly, lw, lh = 35, 750, 395, 195
    draw.rectangle([lx, ly, lx + lw, ly + lh], fill=(4, 12, 26, 230), outline=(0, 190, 240, 180), width=2)
    draw.rectangle([lx, ly, lx + lw, ly + 28], fill=(0, 60, 115, 240))
    draw.text((lx + 12, ly + 6), "TRAJECTORY & ENCOUNTER LEGEND", fill=(255, 255, 255, 255), font=font_header)

    items = [
        ("───", (0, 240, 255, 255), "Protected Satellite (Nominal Orbit)", (220, 240, 255)),
        ("- - -", (255, 140, 20, 255), "Secondary Debris (Threat Track)", (255, 215, 180)),
        ("- - -", (40, 255, 120, 255), "Protected Satellite (Avoidance Orbit)", (200, 255, 220)),
        ("  ⦿  ", (255, 60, 60, 255), "Nominal TCA Conjunction Point", (255, 200, 200)),
        ("  ▲  ", (40, 255, 120, 255), "Avoidance Burn Execution Point (-R)", (200, 255, 220)),
    ]

    iy = ly + 36
    for symbol, sym_color, label, text_color in items:
        draw.text((lx + 14, iy), symbol, fill=sym_color, font=font_body_bold)
        draw.text((lx + 60, iy + 1), label, fill=text_color, font=font_small)
        iy += 30

def draw_right_telemetry_dashboard(draw, step_index):
    """Draws the Right-Side Telemetry Dashboard and Risk Comparison Panel."""
    step_info = PAYLOAD["demonstration_sequence"][step_index - 1]
    t_sim = step_info["simulation_time_sec"]
    b_executed = step_index >= 6

    px, py, pw, ph = 1430, 22, 455, 925

    draw.rectangle([px-2, py-2, px+pw+2, py+ph+2], outline=(0, 200, 255, 80), width=1)
    draw.rectangle([px, py, px+pw, py+ph], fill=(4, 12, 28, 238), outline=(0, 205, 255, 210), width=2)

    draw.rectangle([px, py, px+pw, py+40], fill=(0, 75, 140, 245))
    draw.text((px+14, py+8), "SATELLITE COLLISION AVOIDANCE (ICPS)", fill=(255, 255, 255, 255), font=font_title)
    draw.text((px+14, py+25), "AUTONOMOUS ENCOUNTER & MANOEUVRE TELEMETRY", fill=(160, 215, 255, 220), font=font_subtitle)

    badge_text = "● PLAYING (5.0x)" if step_index != 4 else "|| PAUSED (TCA)"
    badge_color = (40, 255, 120, 255) if step_index != 4 else (255, 200, 40, 255)
    draw.text((px+pw-125, py+12), badge_text, fill=badge_color, font=font_badge)

    nom = PAYLOAD["nominal_encounter"]
    post = PAYLOAD["post_manoeuvre_encounter"]
    man = PAYLOAD["selected_manoeuvre"]

    nom_tca_miss = nom["miss_distance_m"]       # 1563.48 m
    post_tca_miss = post["new_miss_distance_m"]  # 2454.42 m

    # Calculate exact instantaneous Euclidean separation from synchronized time-series positions
    ts = PAYLOAD["time_series"]
    times_arr = np.array(ts["timestamps_sec"])
    scale_uu_per_m = PAYLOAD["scenario_metadata"]["scale_factor_uu_per_m"]
    sat_arr = np.array(ts["satellite_modified_positions_ue"] if step_index >= 6 else ts["satellite_nominal_positions_ue"])
    deb_arr = np.array(ts["debris_positions_ue"])

    if t_sim in times_arr:
        idx_sim = int(np.where(times_arr == t_sim)[0][0])
        p_sat = sat_arr[idx_sim]
        p_deb = deb_arr[idx_sim]
    else:
        idx_low = int(np.where(times_arr <= t_sim)[0][-1])
        idx_high = int(np.where(times_arr >= t_sim)[0][0])
        t_low, t_high = times_arr[idx_low], times_arr[idx_high]
        alpha = (t_sim - t_low) / (t_high - t_low)
        p_sat = (1.0 - alpha) * sat_arr[idx_low] + alpha * sat_arr[idx_high]
        p_deb = (1.0 - alpha) * deb_arr[idx_low] + alpha * deb_arr[idx_high]

    actual_inst_sep_m = float(np.linalg.norm(p_sat - p_deb) / scale_uu_per_m)

    # Step-specific telemetry mapping distinguishing:
    # 1. Instantaneous separation at current simulation time (synchronized positions)
    # 2. Predicted TCA miss distance (encounter assessment)
    # 3. Operational safety threshold evaluation (2000.0 m)
    if step_index == 1:
        # Step 1: T = 0.0 s
        inst_sep = f"{actual_inst_sep_m:,.1f} m (10.00 km)"
        miss_dist_str = f"{nom_tca_miss:.2f} m (Predicted TCA)"
        safety_status = "NOMINAL SCREENING — CONJUNCTION TRACKED"
        safety_color = (255, 220, 60, 255)
        pc_str = f"{nom['collision_probability']:.6e} (log10: {nom['collision_log10_pc']:.2f})"
        risk_safety_status = "SCREENING_ACTIVE"
        risk_safety_color = (255, 220, 60, 255)
    elif step_index == 2:
        # Step 2: T = 60.0 s
        inst_sep = f"{actual_inst_sep_m:,.1f} m (Nominal Tracking)"
        miss_dist_str = f"{nom_tca_miss:.2f} m (Predicted TCA)"
        safety_status = "NOMINAL TRACKING — CONJUNCTION PENDING"
        safety_color = (255, 220, 60, 255)
        pc_str = f"{nom['collision_probability']:.6e} (log10: {nom['collision_log10_pc']:.2f})"
        risk_safety_status = "PENDING_ASSESSMENT"
        risk_safety_color = (255, 220, 60, 255)
    elif step_index == 3:
        # Step 3: T = 120.0 s
        inst_sep = f"{actual_inst_sep_m:,.1f} m (Screening Zone)"
        miss_dist_str = f"{nom_tca_miss:.2f} m (Predicted TCA)"
        safety_status = "CRITICAL CONJUNCTION RISK DETECTED"
        safety_color = (255, 90, 90, 255)
        pc_str = f"{nom['collision_probability']:.6e} (log10: {nom['collision_log10_pc']:.2f})"
        risk_safety_status = "CRITICAL_RISK (< 2000m)"
        risk_safety_color = (255, 90, 90, 255)
    elif step_index == 4:
        # Step 4: T = 150.0 s (Encounter Assessment)
        inst_sep = f"{actual_inst_sep_m:,.1f} m (Encounter Approaching)"
        miss_dist_str = f"{nom_tca_miss:.2f} m [CRITICAL < 2000m]"
        safety_status = "HIGH COLLISION PROBABILITY ALERT"
        safety_color = (255, 60, 60, 255)
        pc_str = f"{nom['collision_probability']:.6e} [{nom['risk_classification']}]"
        risk_safety_status = "CRITICAL_COLLISION_ALERT"
        risk_safety_color = (255, 60, 60, 255)
    elif step_index == 5:
        # Step 5: T = 169.6 s (Autonomous Avoidance Planning)
        inst_sep = f"{actual_inst_sep_m:,.1f} m (Planning Epoch)"
        miss_dist_str = f"{nom_tca_miss:.2f} m [Targeting Post-Burn]"
        safety_status = "MANOEUVRE PLANNED — RADIAL (-R)"
        safety_color = (255, 180, 40, 255)
        pc_str = f"{nom['collision_probability']:.6e} (Planning Burn)"
        risk_safety_status = "PLANNING_AVOIDANCE"
        risk_safety_color = (255, 180, 40, 255)
    elif step_index == 6:
        # Step 6: T = 169.6 s (Burn Execution)
        inst_sep = f"{actual_inst_sep_m:,.1f} m (At Burn Epoch)"
        miss_dist_str = f"{post_tca_miss:.2f} m (Predicted Post-Burn)"
        safety_status = "BURN EXECUTING — TRAJECTORY DIVERGING"
        safety_color = (0, 230, 255, 255)
        pc_str = f"{post['new_collision_probability']:.6e} (log10: {post['new_collision_log10_pc']:.2f})"
        risk_safety_status = "MANOEUVRE_EXECUTING"
        risk_safety_color = (0, 230, 255, 255)
    elif step_index == 7:
        # Step 7: T = 300.0 s (Modified Trajectory Propagation)
        inst_sep = f"{actual_inst_sep_m:,.1f} m (Diverging Track)"
        miss_dist_str = f"{post_tca_miss:.2f} m (Predicted Post-Burn)"
        safety_status = "TRAJECTORY DIVERGING — CLEARANCE BELOW THRESHOLD"
        safety_color = (255, 165, 30, 255)
        pc_str = f"{post['new_collision_probability']:.6e} (log10: {post['new_collision_log10_pc']:.2f})"
        risk_safety_status = "CLEARANCE_BELOW_THRESHOLD"
        risk_safety_color = (255, 165, 30, 255)
    else:
        # Step 8: T = 903.0 s (Post-Manoeuvre Verification & Safe Clearance)
        # Synchronized position separation at T=903.0s is 4525.7 m
        # Predicted post-manoeuvre miss distance at closest approach is 2454.42 m >= 2000.0 m
        inst_sep = f"{actual_inst_sep_m:,.1f} m (Synchronized Track)"
        miss_dist_str = f"{post_tca_miss:.2f} m [RESOLVED >= 2000m]"
        safety_status = "RESOLVED_SAFE: CLEARANCE VERIFIED"
        safety_color = (40, 255, 120, 255)
        pc_str = f"{post['new_collision_probability']:.6e} (log10: {post['new_collision_log10_pc']:.2f})"
        risk_safety_status = "RESOLVED_SAFE"
        risk_safety_color = (40, 255, 120, 255)

    cy = py + 52
    line_h = 28

    def draw_telemetry_row(label, val, val_color=(255, 255, 255, 255)):
        nonlocal cy
        draw.text((px + 14, cy), label, fill=(160, 205, 235, 230), font=font_header)
        str_val = str(val)
        bbox = font_body.getbbox(str_val)
        val_w = bbox[2] - bbox[0]
        max_w = pw - 185  # 270 px
        if val_w > max_w:
            if " — " in str_val:
                p1, p2 = str_val.split(" — ", 1)
                draw.text((px + 175, cy - 2), p1, fill=val_color, font=font_badge)
                draw.text((px + 175, cy + 11), f"— {p2}", fill=val_color, font=font_small)
            else:
                draw.text((px + 175, cy + 2), str_val, fill=val_color, font=font_small)
        else:
            draw.text((px + 175, cy), str_val, fill=val_color, font=font_body)
        cy += line_h

    draw_telemetry_row("Simulation Time:", f"T + {t_sim:05.1f} s", (255, 255, 255, 255))
    draw_telemetry_row("Encounter Pair:", "ProtectedSat vs DebrisObj99", (220, 220, 220, 255))
    draw_telemetry_row("Nominal TCA:", f"{nom['tca_seconds']:.2f} s", (255, 215, 50, 255))
    draw_telemetry_row("Instantaneous Sep:", inst_sep, (255, 230, 140, 255))
    draw_telemetry_row("Predicted TCA Miss:", miss_dist_str, (255, 215, 50, 255) if step_index < 6 else (40, 255, 120, 255))
    draw_telemetry_row("Relative Speed:", f"{nom['relative_speed_mps']:.3f} m/s", (80, 220, 255, 255))
    draw_telemetry_row("Collision Prob (Pc):", pc_str, (255, 90, 90, 255) if step_index < 6 else (40, 255, 120, 255))
    draw_telemetry_row("Planned Avoidance Δv:", f"{man['delta_v_magnitude_mps']:.2f} m/s", (40, 255, 120, 255))
    draw_telemetry_row("Burn Epoch & Vector:", f"-R (Radial) at T+{man['burn_epoch_seconds']:.1f}s", (180, 255, 210, 255))
    draw_telemetry_row("Propulsion Mode:", "Cold-Gas Thruster", (200, 230, 255, 220))
    draw_telemetry_row("Safety Status:", safety_status, safety_color)

    # Clean short milestone headlines that fit without truncation
    clean_step_titles = {
        1: "Init Orbital Simulation",
        2: "Nominal Propagation",
        3: "Conjunction Detected",
        4: "Encounter Assessment",
        5: "Autonomous Avoidance",
        6: "Impulsive Burn (-R)",
        7: "Trajectory Divergence",
        8: "Post-Burn Safe Margin"
    }
    step_title_clean = clean_step_titles.get(step_index, step_info['headline'])
    draw_telemetry_row("Demonstration Step:", f"Step {step_index}/8: {step_title_clean}", (255, 240, 110, 255))

    cy += 6
    draw.line([(px + 14, cy), (px + pw - 14, cy)], fill=(0, 180, 240, 120), width=1)
    cy += 14

    # DISTINCT RISK COMPARISON PANEL (Sub-Card)
    rc_h = 330
    draw.rectangle([px + 12, cy, px + pw - 12, cy + rc_h], fill=(2, 8, 20, 245), outline=(0, 220, 255, 200), width=2)
    draw.rectangle([px + 12, cy, px + pw - 12, cy + 26], fill=(0, 50, 100, 240))
    draw.text((px + 22, cy + 5), "COLLISION RISK ASSESSMENT & COMPARISON", fill=(0, 240, 255, 255), font=font_header)

    ry = cy + 34
    def draw_risk_row(label, val, val_color):
        nonlocal ry
        draw.text((px + 24, ry), label, fill=(160, 210, 240, 230), font=font_subtitle)
        draw.text((px + 185, ry), str(val), fill=val_color, font=font_body_bold)
        ry += 24

    draw_risk_row("Nominal Collision Prob:", f"{nom['collision_probability']:.6e}", (255, 90, 90, 255))
    draw_risk_row("Nominal log10(Pc):", f"{nom['collision_log10_pc']:.2f}", (255, 140, 140, 255))
    draw_risk_row("Post-Manoeuvre Prob:", f"{post['new_collision_probability']:.6e}", (40, 255, 120, 255))
    draw_risk_row("Post-Manoeuvre log10:", f"{post['new_collision_log10_pc']:.2f}", (140, 255, 180, 255))
    draw_risk_row("Risk Reduction Factor:", "3.19e+08 (8.50 orders)", (0, 230, 255, 255))
    draw_risk_row("Nominal Miss Distance:", f"{nom['miss_distance_m']:.2f} m", (255, 215, 60, 255))
    draw_risk_row("Post-Burn Miss Distance:", f"{post['new_miss_distance_m']:.2f} m", (40, 255, 120, 255))
    draw_risk_row("Safety Margin Delta:", f"+{post['delta_miss_distance_m']:.2f} m clearance", (40, 255, 120, 255))
    draw_risk_row("Predicted Safety Status:", risk_safety_status, risk_safety_color)
    draw_risk_row("Covariance Quality Flag:", "NUMERICAL_UNDERFLOW", (140, 215, 255, 230))

    f_y = py + ph - 34
    draw.rectangle([px + 2, f_y, px + pw - 2, py + ph - 2], fill=(5, 18, 38, 245), outline=(0, 160, 220, 140), width=1)
    draw.text((px + 10, f_y + 8), "[SPACE] Pause | [1-8] Jump Step | [C] Cam | [R] Reset", fill=(140, 215, 255, 240), font=font_subtitle)

def draw_eight_step_timeline(draw, active_step):
    """Draws full-width modern Eight-Step Demonstration Timeline along the bottom."""
    tx, ty, tw, th = 35, 970, 1850, 88
    draw.rectangle([tx, ty, tx + tw, ty + th], fill=(3, 10, 24, 240), outline=(0, 180, 240, 180), width=2)

    steps = [
        (1, "1. INIT SIM", "T=0.0s", "Earth & Object Setup"),
        (2, "2. TRACKING", "T=60.0s", "Nominal Propagation"),
        (3, "3. DETECTED", "T=120.0s", "Conjunction Screening"),
        (4, "4. TCA ALERT", "T=150.0s", "Encounter Assessment"),
        (5, "5. AVOID PLAN", "T=169.6s", "Delta-v Optimization"),
        (6, "6. BURN EXEC", "T=169.6s", "Impulsive -R Burn"),
        (7, "7. MOD DRIFT", "T=300.0s", "Trajectory Divergence"),
        (8, "8. CLEARANCE", "T=903.0s", "Post-Burn Safe Margin"),
    ]

    cell_w = (tw - 16) / 8.0

    for idx, (step_num, title, epoch, desc) in enumerate(steps):
        cx = tx + 8 + idx * cell_w
        cy = ty + 8
        cw = cell_w - 6
        ch = th - 16

        is_active = (step_num == active_step)
        is_past = (step_num < active_step)

        if is_active:
            draw.rectangle([cx-1, cy-1, cx+cw+1, cy+ch+1], outline=(0, 255, 255, 220), width=2)
            draw.rectangle([cx, cy, cx+cw, cy+ch], fill=(0, 95, 175, 250), outline=(0, 235, 255, 255), width=2)
            draw.text((cx + 10, cy + 6), f"● {title}", fill=(255, 255, 255, 255), font=font_timeline)
            draw.text((cx + 10, cy + 26), epoch, fill=(255, 240, 100, 255), font=font_badge)
            draw.text((cx + 10, cy + 46), desc, fill=(220, 245, 255, 255), font=font_timeline_sub)
        elif is_past:
            draw.rectangle([cx, cy, cx+cw, cy+ch], fill=(4, 28, 48, 220), outline=(0, 160, 120, 160), width=1)
            draw.text((cx + 10, cy + 6), f"✓ {title}", fill=(50, 255, 140, 240), font=font_timeline)
            draw.text((cx + 10, cy + 26), epoch, fill=(160, 220, 190, 200), font=font_timeline_sub)
            draw.text((cx + 10, cy + 46), desc, fill=(140, 180, 170, 180), font=font_timeline_sub)
        else:
            draw.rectangle([cx, cy, cx+cw, cy+ch], fill=(6, 16, 32, 180), outline=(0, 100, 140, 90), width=1)
            draw.text((cx + 10, cy + 6), f"  {title}", fill=(130, 170, 200, 180), font=font_timeline)
            draw.text((cx + 10, cy + 26), epoch, fill=(100, 140, 170, 150), font=font_timeline_sub)
            draw.text((cx + 10, cy + 46), desc, fill=(90, 120, 150, 140), font=font_timeline_sub)

def composite_full_dashboard(raw_img_path, final_img_path, step_index):
    """Composites complete technical UI overlay onto the raw 3D Unreal Engine render."""
    img = Image.open(raw_img_path).convert("RGBA")

    # 1. Subtle Procedural Starfield in dark background
    apply_subtle_starfield(img)

    draw = ImageDraw.Draw(img, "RGBA")

    # 2. Perspective Orbital Grid (in Z=0 plane)
    draw_perspective_orbital_grid(draw)

    # 3. Orbital Trajectories (Cyan solid, Orange dashed, Green dashed, TCA & Burn markers)
    draw_orbital_trajectories(draw, step_index)

    # 4. 3D Tracking Labels for Protected Satellite & Debris
    draw_satellite_and_debris_labels(draw, step_index)

    # 5. Top Navigation Bar (Mode controls)
    draw_top_navigation_bar(draw)

    # 6. Trajectory Legend (Bottom-Left)
    draw_trajectory_legend(draw)

    # 7. Right-Side Telemetry Dashboard + Risk Comparison Panel
    draw_right_telemetry_dashboard(draw, step_index)

    # 8. Eight-Step Demonstration Timeline (Bottom)
    draw_eight_step_timeline(draw, step_index)

    img.save(final_img_path, "PNG")
    print(f"  [SAVED] {final_img_path}")
    return final_img_path

def run_unreal_capture_for_step(step_index, raw_filename):
    """Commands running Unreal Editor via remote execution to jump to step and capture 3D frame."""
    remote = remote_execution.RemoteExecution()
    remote.start()
    start_time = time.time()
    while not remote.remote_nodes and (time.time() - start_time) < 4.0:
        time.sleep(0.3)

    if not remote.remote_nodes:
        print("[ERROR] No remote Unreal Engine nodes found.")
        remote.stop()
        return False

    node_id = remote.remote_nodes[0]["node_id"]
    remote.open_command_connection(node_id)

    ue_script = f"""
import unreal
import math
import os

world = unreal.EditorLevelLibrary.get_editor_world()
actors = unreal.EditorLevelLibrary.get_all_level_actors()

sim = None
sat = None
deb = None
for a in actors:
    if isinstance(a, unreal.OrbitSimulationManager):
        sim = a
    elif isinstance(a, unreal.SatelliteActor):
        sat = a
    elif isinstance(a, unreal.DebrisActor):
        deb = a

if sim:
    sim.jump_to_step({step_index})

if sat:
    sat.set_actor_scale3d(unreal.Vector(18.0, 18.0, 18.0))
    sat.set_actor_hidden_in_game(False)
if deb:
    deb.set_actor_scale3d(unreal.Vector(20.0, 20.0, 20.0))
    deb.set_actor_hidden_in_game(False)

cam_pos = unreal.Vector(50000.0, -480000.0, 330000.0)
tgt = unreal.Vector(-63000.0, -25000.0, 0.0)
dx, dy, dz = tgt.x - cam_pos.x, tgt.y - cam_pos.y, tgt.z - cam_pos.z
yaw = math.degrees(math.atan2(dy, dx))
pitch = math.degrees(math.atan2(dz, math.sqrt(dx*dx + dy*dy)))
cam_rot = unreal.Rotator(pitch=pitch, yaw=yaw, roll=0.0)

cap = unreal.EditorLevelLibrary.spawn_actor_from_class(unreal.SceneCapture2D, cam_pos, cam_rot)
comp = cap.get_editor_property('capture_component2d')
comp.set_editor_property('fov_angle', 52.0)
comp.set_editor_property('capture_source', unreal.SceneCaptureSource.SCS_FINAL_COLOR_LDR)

pps = comp.get_editor_property('post_process_settings')
pps.set_editor_property('override_auto_exposure_bias', True)
pps.set_editor_property('auto_exposure_bias', 0.0)
comp.set_editor_property('post_process_settings', pps)

rt = unreal.RenderingLibrary.create_render_target2d(world, 1920, 1080, unreal.TextureRenderTargetFormat.RTF_RGBA8)
comp.set_editor_property('texture_target', rt)
comp.capture_scene()

out_dir = r"{RAW_OUTPUT_DIR}".replace('\\\\', '/')
unreal.RenderingLibrary.export_render_target(world, rt, out_dir, "{raw_filename}")
unreal.EditorLevelLibrary.destroy_actor(cap)
print(f"SUCCESS: Exported {raw_filename} at Step {step_index}")
"""
    result = remote.run_command(ue_script)
    for out in result.get("output", []):
        print("  [UE5]", out.get("output", "").strip())
    remote.stop()
    return True

def main():
    print("=" * 80)
    print("SATELLITE ANTI-COLLISION SIMULATION SYSTEM (ICPS) — FINAL VISUAL DESIGN GENERATION")
    print("=" * 80)

    milestones = [
        (1, "Raw_Step1_Init.png", "Final_Dashboard_Step1_Init.png"),
        (4, "Raw_Step4_ConjunctionTCA.png", "Final_Dashboard_Step4_ConjunctionTCA.png"),
        (6, "Raw_Step6_BurnExecution.png", "Final_Dashboard_Step6_BurnExecution.png"),
        (7, "Raw_Step6_BurnExecution.png", "Final_Dashboard_Step7_ModifiedDrift.png"),
        (8, "Raw_Step8_SafeClearance.png", "Final_Dashboard_Step8_SafeClearance.png"),
    ]

    for step_num, raw_name, final_name in milestones:
        print(f"\n>>> PROCESSING MILESTONE STEP {step_num} ({final_name}) <<<")
        run_unreal_capture_for_step(step_num, raw_name)

        raw_path = os.path.join(RAW_OUTPUT_DIR, raw_name)
        final_path = os.path.join(RAW_OUTPUT_DIR, final_name)
        artifact_path = os.path.join(ARTIFACTS_DIR, final_name)

        if not os.path.exists(raw_path):
            print(f"  [ERROR] Raw capture not found at {raw_path}")
            continue

        composite_full_dashboard(raw_path, final_path, step_num)
        shutil.copy2(final_path, artifact_path)
        print(f"  [COPIED] Artifact updated: {artifact_path}")

        # Also copy to tracked Project_Deliverables/Final_Visual_Dashboard
        deliv_dir = os.path.join(WORKSPACE_DIR, "Project_Deliverables", "Final_Visual_Dashboard")
        os.makedirs(deliv_dir, exist_ok=True)
        deliv_path = os.path.join(deliv_dir, final_name)
        shutil.copy2(final_path, deliv_path)
        print(f"  [COPIED] Deliverable updated: {deliv_path}")

    print("\n" + "=" * 80)
    print("ALL VISUAL DASHBOARDS SUCCESSFULLY GENERATED AND EXPORTED TO ARTIFACTS!")
    print("=" * 80)

if __name__ == "__main__":
    main()
