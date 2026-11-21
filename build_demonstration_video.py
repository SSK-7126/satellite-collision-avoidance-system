"""
build_demonstration_video.py
============================
Generates the authoritative Final Demonstration Video (MP4, 720p HD @ 30 FPS)
for Milestone 4 of the Satellite Collision Avoidance System project.

Features:
- Professional title and objective opening card.
- 8 milestone scene sequences corresponding to the authoritative demonstration sequence.
- On-screen telemetry HUD bars and sequence timestamps.
- Smooth cross-fade dissolves between orbital views.
- Final quantitative evaluation and conclusions summary card.
"""

import os
import json
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import imageio

ARTIFACT_DIR = r"C:\Users\Sriram Krovi\.gemini\antigravity\brain\7d36e17b-846d-4a94-9bbc-4bf33eb09d71"
OUT_VIDEO_PATH = os.path.abspath("Project_Deliverables/Final_Milestone/Final_Demonstration_Video.mp4")
CHARTS_DIR = os.path.abspath("Project_Deliverables/Final_Milestone/Performance_Charts")

WIDTH = 1280
HEIGHT = 720
FPS = 30

# Load Fonts
try:
    font_title = ImageFont.truetype("arialbd.ttf", 34)
    font_subtitle = ImageFont.truetype("arial.ttf", 20)
    font_step = ImageFont.truetype("arialbd.ttf", 18)
    font_desc = ImageFont.truetype("arial.ttf", 15)
    font_telemetry_label = ImageFont.truetype("arialbd.ttf", 13)
    font_telemetry_val = ImageFont.truetype("arial.ttf", 13)
    font_badge = ImageFont.truetype("arialbd.ttf", 13)
except Exception:
    font_title = ImageFont.load_default()
    font_subtitle = font_title
    font_step = font_title
    font_desc = font_title
    font_telemetry_label = font_title
    font_telemetry_val = font_title
    font_badge = font_title

def create_title_card(title, subtitle, details, bg_color=(10, 15, 30)):
    img = Image.new("RGB", (WIDTH, HEIGHT), bg_color)
    draw = ImageDraw.Draw(img)
    
    # Outer border
    draw.rectangle([20, 20, WIDTH - 20, HEIGHT - 20], outline=(0, 180, 216), width=2)
    draw.rectangle([26, 26, WIDTH - 26, HEIGHT - 26], outline=(30, 60, 90), width=1)
    
    # Header bar
    draw.rectangle([22, 22, WIDTH - 22, 70], fill=(0, 70, 130))
    draw.text((40, 32), "SATELLITE COLLISION AVOIDANCE SYSTEM (ICPS) — FINAL DEMONSTRATION", fill=(255, 255, 255), font=font_subtitle)
    
    # Main Title
    draw.text((WIDTH // 2, 180), title, fill=(255, 255, 255), font=font_title, anchor="mm")
    draw.text((WIDTH // 2, 230), subtitle, fill=(0, 212, 255), font=font_subtitle, anchor="mm")
    
    # Details Box
    draw.rectangle([240, 300, WIDTH - 240, 620], fill=(15, 25, 45), outline=(0, 180, 216), width=1)
    y_pos = 330
    for label, val in details:
        draw.text((280, y_pos), label, fill=(150, 190, 225), font=font_desc)
        draw.text((620, y_pos), val, fill=(255, 255, 255), font=font_step)
        y_pos += 45
        
    return img

def create_scene_frame(bg_image, step_num, step_title, step_desc, sim_time, telemetry_dict, badge_text, badge_color):
    # Resize bg_image to fill/fit 1280x720
    frame = bg_image.copy()
    if frame.size != (WIDTH, HEIGHT):
        frame = frame.resize((WIDTH, HEIGHT), Image.Resampling.LANCZOS)
        
    draw = ImageDraw.Draw(frame)
    
    # 1. Top HUD Bar
    hud_h = 60
    draw.rectangle([0, 0, WIDTH, hud_h], fill=(8, 18, 35, 235))
    draw.line([0, hud_h, WIDTH, hud_h], fill=(0, 180, 216), width=2)
    
    # Title & Step
    step_str = f"STEP {step_num} / 8 : {step_title.upper()}"
    draw.text((25, 12), step_str, fill=(0, 220, 255), font=font_step)
    draw.text((25, 36), step_desc, fill=(210, 225, 240), font=font_desc)
    
    # Clock Badge on right
    draw.rectangle([WIDTH - 210, 12, WIDTH - 25, 48], fill=(15, 30, 55), outline=(0, 180, 216), width=1)
    draw.text((WIDTH - 117, 30), f"SIM TIME: T+{sim_time:.1f}s", fill=(255, 255, 255), font=font_telemetry_label, anchor="mm")
    
    # 2. Bottom Telemetry Overlay Bar
    bot_h = 75
    bot_y = HEIGHT - bot_h
    draw.rectangle([0, bot_y, WIDTH, HEIGHT], fill=(8, 18, 35, 235))
    draw.line([0, bot_y, WIDTH, bot_y], fill=(0, 180, 216), width=2)
    
    # Render Telemetry Items (up to 4 columns)
    col_w = (WIDTH - 220) // max(len(telemetry_dict), 1)
    col_x = 25
    for lbl, val, col in telemetry_dict:
        draw.text((col_x, bot_y + 16), lbl, fill=(140, 180, 215), font=font_telemetry_label)
        draw.text((col_x, bot_y + 40), val, fill=col, font=font_step)
        col_x += col_w
        
    # State Badge (right side of bottom bar)
    draw.rectangle([WIDTH - 200, bot_y + 15, WIDTH - 25, bot_y + 60], fill=badge_color[1], outline=badge_color[0], width=2)
    draw.text((WIDTH - 112, bot_y + 37), badge_text, fill=badge_color[0], font=font_badge, anchor="mm")
    
    return frame

print("Building Final Demonstration Video...")

# Define Scenes
scenes_data = [
    {
        "type": "title",
        "title": "SATELLITE COLLISION AVOIDANCE SYSTEM",
        "subtitle": "Deliverable 4: Quantitative Performance Evaluation & Verification",
        "details": [
            ("Target Orbit Regime", "Low Earth Orbit (7000 km Semi-Major Axis)"),
            ("Primary Protected Satellite", "CARTOSAT-3 (Payload Bus Payload01)"),
            ("Threat Secondary Object", "DEBRIS_PIECE_99 (Track Object99)"),
            ("Authoritative Solvers", "Python RK4 Numerical Integrator & Covariance"),
            ("Visualization Engine", "Unreal Engine 5.7.4 (Physics-Synchronized Playback)")
        ],
        "duration_sec": 3.0
    },
    {
        "type": "scene",
        "step_num": 1,
        "title": "Initialize Orbital Simulation",
        "desc": "Earth and space objects initialized in ECI frame. Protected satellite in 7000 km circular orbit; debris 10 km ahead.",
        "sim_time": 0.0,
        "image_file": os.path.join(ARTIFACT_DIR, "Milestone3_Step1_InitialSetup.png"),
        "telemetry": [
            ("Nominal Miss Distance:", "1563.5 m (1.564 km)", (255, 215, 0)),
            ("Predicted Nominal TCA:", "769.63 s", (255, 255, 255)),
            ("Collision Prob (Pc):", "3.958e-14 [UNDERFLOW]", (255, 120, 120)),
            ("Avoidance Delta-V:", "PLANNED: 3.00 m/s (-R)", (80, 230, 120))
        ],
        "badge_text": "SCREENING TRIGGERED",
        "badge_color": ((255, 180, 0), (45, 35, 10)),
        "duration_sec": 4.5
    },
    {
        "type": "scene",
        "step_num": 2,
        "title": "Nominal Trajectory Propagation",
        "desc": "Satellite propagates along circular orbit. High-detail spacecraft bus with dual solar panels and antenna array.",
        "sim_time": 60.0,
        "image_file": os.path.join(ARTIFACT_DIR, "Milestone2_Satellite_Detail.png"),
        "telemetry": [
            ("Tracking Status:", "ACTIVE KEPLERIAN PROPAGATION", (80, 230, 120)),
            ("Orbital Altitude:", "621.87 km (r = 7000 km)", (255, 255, 255)),
            ("Orbital Speed:", "7546.05 m/s (7.546 km/s)", (0, 220, 255)),
            ("Collision Probability:", "3.958e-14 (log10: -13.40)", (255, 120, 120))
        ],
        "badge_text": "NOMINAL TRACKING",
        "badge_color": ((0, 220, 255), (10, 35, 50)),
        "duration_sec": 4.0
    },
    {
        "type": "scene",
        "step_num": 3,
        "title": "Conjunction Screening Trigger",
        "desc": "Conjunction filter breached (< 25.0 km threshold). Threatening secondary debris fragment approaching from forward orbit.",
        "sim_time": 120.0,
        "image_file": os.path.join(ARTIFACT_DIR, "Milestone2_Debris_Detail.png"),
        "telemetry": [
            ("Secondary Threat Object:", "DEBRIS_PIECE_99", (255, 100, 100)),
            ("Relative Approach Speed:", "13.234 m/s", (255, 215, 0)),
            ("Distance at Screening:", "18.42 km (< 25.0 km threshold)", (255, 150, 0)),
            ("Lead Time to TCA:", "649.6 s (~10.8 min)", (0, 220, 255))
        ],
        "badge_text": "CONJUNCTION ALERT",
        "badge_color": ((255, 80, 80), (50, 15, 15)),
        "duration_sec": 4.0
    },
    {
        "type": "scene",
        "step_num": 4,
        "title": "Encounter Assessment & Risk Metrics",
        "desc": "Nominal miss distance evaluated: 1563.5 m (< 2000.0 m safety limit). Critical collision alert triggered at TCA=769.6s.",
        "sim_time": 150.0,
        "image_file": os.path.join(ARTIFACT_DIR, "Milestone3_Step4_ConjunctionAlert.png"),
        "telemetry": [
            ("Nominal Miss Distance:", "1563.5 m (CRITICAL < 2000 m)", (255, 80, 80)),
            ("Nominal TCA Epoch:", "769.63 s (T+769.6s)", (255, 215, 0)),
            ("Collision Prob (Pc):", "3.958e-14 [NUMERICAL_UNDERFLOW]", (255, 80, 80)),
            ("Combined Hard-Body R:", "5.00 m (Spherical Model)", (255, 255, 255))
        ],
        "badge_text": "CRITICAL RISK DETECTED",
        "badge_color": ((255, 50, 50), (60, 10, 10)),
        "duration_sec": 5.0
    },
    {
        "type": "scene",
        "step_num": 5,
        "title": "Autonomous Avoidance Planning",
        "desc": "Planner searches candidate catalog. Optimal impulsive solution selected: MAN_006_-R_3.00mps_T170s (lead time 600s).",
        "sim_time": 169.6,
        "image_file": os.path.join(ARTIFACT_DIR, "Milestone2_Encounter_Overview.png"),
        "telemetry": [
            ("Selected Manoeuvre ID:", "MAN_006_-R_3.00mps_T170s", (80, 230, 120)),
            ("Burn Epoch:", "169.63 s (600s before Nom TCA)", (255, 255, 255)),
            ("Delta-V Magnitude:", "3.00 m/s in -R Direction", (80, 230, 120)),
            ("Avoidance Strategy:", "Radial inward orbit phasing shift", (255, 215, 0))
        ],
        "badge_text": "MANOEUVRE PLANNED",
        "badge_color": ((80, 230, 120), (15, 45, 25)),
        "duration_sec": 4.0
    },
    {
        "type": "scene",
        "step_num": 6,
        "title": "Impulsive Burn Execution",
        "desc": "Instantaneous delta-v applied in RTN frame (-R 3.00 m/s). Velocity updated in ECI; position remains continuous.",
        "sim_time": 169.6,
        "image_file": os.path.join(ARTIFACT_DIR, "Milestone3_Step6_BurnExecution.png"),
        "telemetry": [
            ("Applied Delta-V Vector:", "[-3.00, 0.00, 0.00] m/s (RTN)", (255, 180, 0)),
            ("ECI Delta-V Vector:", "[-2.95, -0.55, 0.00] m/s", (255, 255, 255)),
            ("Spacecraft Visual State:", "MANOEUVRED (Thruster Active)", (255, 120, 0)),
            ("Lead Time to Encounter:", "600.0 s (10.0 minutes)", (0, 220, 255))
        ],
        "badge_text": "BURN EXECUTED",
        "badge_color": ((255, 160, 0), (50, 30, 5)),
        "duration_sec": 5.0
    },
    {
        "type": "scene",
        "step_num": 7,
        "title": "Modified Trajectory & Covariance Drift",
        "desc": "Satellite drifts onto modified orbit. Trajectory deviation accumulates safely away from debris approach path.",
        "sim_time": 300.0,
        "image_file": os.path.join(ARTIFACT_DIR, "Milestone2_Trajectories_Divergence.png"),
        "telemetry": [
            ("Instant Trajectory Deviation:", "1386.4 m (Accumulating)", (80, 230, 120)),
            ("Peak Trajectory Deviation:", "3008.5 m (at T=1000s)", (255, 215, 0)),
            ("Modified Orbit Period:", "5822.4 s (Shifted Phasing)", (255, 255, 255)),
            ("Trajectory Separation:", "SAFE CLEARANCE DIVERGENCE", (80, 230, 120))
        ],
        "badge_text": "TRAJECTORY DIVERGING",
        "badge_color": ((80, 230, 120), (15, 45, 25)),
        "duration_sec": 4.5
    },
    {
        "type": "scene",
        "step_num": 8,
        "title": "Post-Manoeuvre Verification & Safety Margin",
        "desc": "Encounter successfully resolved. Miss distance increased to 2454.4 m (+890.9 m clearance). Collision risk mitigated.",
        "sim_time": 903.0,
        "image_file": os.path.join(ARTIFACT_DIR, "Milestone3_Step8_SafeClearance.png"),
        "telemetry": [
            ("Post-Manoeuvre Miss Distance:", "2454.4 m (+890.9 m / +57.0%)", (80, 230, 120)),
            ("New TCA Epoch:", "903.03 s (Shift: +133.4 s)", (255, 215, 0)),
            ("Post-Manoeuvre Pc:", "1.239e-22 (log10: -21.91)", (80, 230, 120)),
            ("Risk Reduction Factor:", "3.195 x 10^8 x (319.5M x safer)", (0, 220, 255))
        ],
        "badge_text": "RESOLVED SAFE",
        "badge_color": ((80, 230, 120), (10, 50, 25)),
        "duration_sec": 5.5
    },
    {
        "type": "title",
        "title": "PERFORMANCE EVALUATION SUMMARY",
        "subtitle": "Quantitative Validation Results from Authoritative Simulation",
        "details": [
            ("Miss Distance Improvement", "+890.94 m increase (+56.985% gain, 1563.5m -> 2454.4m)"),
            ("Time of Closest Approach Shift", "+133.40 seconds delay (769.63s -> 903.03s)"),
            ("Collision Probability Reduction", "8.50 orders of magnitude (10^-13.40 -> 10^-21.91)"),
            ("Safety Improvement Factor", "319.48 Million times safer (Pc = 1.239e-22)"),
            ("Fuel Efficiency & Control Effort", "Optimal 3.00 m/s impulse in radial inward (-R)"),
            ("System Verification Baseline", "39/39 D2 Pytest Passed | UE 5.7.4 Engine Validated")
        ],
        "duration_sec": 4.5
    }
]

# Write Video
writer = imageio.get_writer(OUT_VIDEO_PATH, fps=FPS, codec='libx264', quality=8)

transition_frames = 15 # 0.5s dissolve transition

last_frame_np = None

for sc_idx, sc in enumerate(scenes_data):
    print(f"  Rendering Scene {sc_idx + 1} / {len(scenes_data)}: {sc['title']}...")
    if sc["type"] == "title":
        img = create_title_card(sc["title"], sc["subtitle"], sc["details"])
    else:
        bg = Image.open(sc["image_file"]).convert("RGB")
        img = create_scene_frame(
            bg,
            sc["step_num"],
            sc["title"],
            sc["desc"],
            sc["sim_time"],
            sc["telemetry"],
            sc["badge_text"],
            sc["badge_color"]
        )
        
    img = img.convert("RGB")
    cur_frame_np = np.array(img)
    total_frames = int(sc["duration_sec"] * FPS)
    
    # Cross-dissolve from previous frame if available
    if last_frame_np is not None:
        for f in range(transition_frames):
            alpha = (f + 1) / float(transition_frames)
            blended = (1.0 - alpha) * last_frame_np + alpha * cur_frame_np
            writer.append_data(blended.astype(np.uint8))
        hold_frames = total_frames - transition_frames
    else:
        hold_frames = total_frames
        
    for _ in range(hold_frames):
        writer.append_data(cur_frame_np)
        
    last_frame_np = cur_frame_np

writer.close()
file_size_mb = os.path.getsize(OUT_VIDEO_PATH) / (1024 * 1024)
print(f"\nDemonstration Video generated successfully!")
print(f"Output: {OUT_VIDEO_PATH} ({file_size_mb:.2f} MB)")
