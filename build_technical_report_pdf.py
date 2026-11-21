"""
build_technical_report_pdf.py
=============================
Compiles the authoritative Final_Technical_Report.pdf using ReportLab.
Includes executive title page, all 17 sections, performance tables, and
embedded high-resolution scientific charts.
"""

import os
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image, KeepTogether, PageBreak, HRFlowable
)
from reportlab.pdfgen import canvas

PDF_PATH = os.path.abspath("Project_Deliverables/Final_Milestone/Final_Technical_Report.pdf")
CHARTS_DIR = os.path.abspath("Project_Deliverables/Final_Milestone/Performance_Charts")

class NumberedCanvas(canvas.Canvas):
    def __init__(self, *args, **kwargs):
        super(NumberedCanvas, self).__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_page_decorations(num_pages)
            super(NumberedCanvas, self).showPage()
        super(NumberedCanvas, self).save()

    def draw_page_decorations(self, total_pages):
        self.saveState()
        self.setFont("Helvetica", 8)
        self.setFillColor(colors.HexColor("#4A5568"))
        
        # Suppress headers/footers on page 1
        if self._pageNumber > 1:
            # Header
            self.drawString(54, 11 * inch - 36, "SATELLITE COLLISION AVOIDANCE SYSTEM (ICPS) — TECHNICAL REPORT")
            self.drawRightString(8.5 * inch - 54, 11 * inch - 36, "MILESTONE 4 FINAL DELIVERABLE")
            self.setStrokeColor(colors.HexColor("#CBD5E0"))
            self.setLineWidth(0.5)
            self.line(54, 11 * inch - 42, 8.5 * inch - 54, 11 * inch - 42)
            
            # Footer
            self.line(54, 46, 8.5 * inch - 54, 46)
            self.drawString(54, 34, "REFERENCE SCENARIO EVALUATION & PERFORMANCE VALIDATION")
            page_text = f"Page {self._pageNumber} of {total_pages}"
            self.drawRightString(8.5 * inch - 54, 34, page_text)
            
        self.restoreState()

print("Compiling Final Technical Report PDF...")

doc = SimpleDocTemplate(
    PDF_PATH,
    pagesize=letter,
    leftMargin=54,
    rightMargin=54,
    topMargin=54,
    bottomMargin=54
)

styles = getSampleStyleSheet()

# Custom styles
style_title = ParagraphStyle(
    'DocTitle',
    parent=styles['Normal'],
    fontName='Helvetica-Bold',
    fontSize=22,
    leading=26,
    textColor=colors.HexColor('#1D3557'),
    alignment=1, # Center
    spaceAfter=8
)

style_subtitle = ParagraphStyle(
    'DocSubtitle',
    parent=styles['Normal'],
    fontName='Helvetica',
    fontSize=12,
    leading=16,
    textColor=colors.HexColor('#457B9D'),
    alignment=1,
    spaceAfter=15
)

style_meta = ParagraphStyle(
    'DocMeta',
    parent=styles['Normal'],
    fontName='Helvetica-Bold',
    fontSize=9,
    leading=13,
    textColor=colors.HexColor('#2B2D42'),
    alignment=1,
    spaceAfter=15
)

style_h1 = ParagraphStyle(
    'Heading1_Custom',
    parent=styles['Heading1'],
    fontName='Helvetica-Bold',
    fontSize=13.5,
    leading=17,
    textColor=colors.HexColor('#1D3557'),
    spaceBefore=14,
    spaceAfter=6,
    keepWithNext=True
)

style_h2 = ParagraphStyle(
    'Heading2_Custom',
    parent=styles['Heading2'],
    fontName='Helvetica-Bold',
    fontSize=10.5,
    leading=14,
    textColor=colors.HexColor('#2A9D8F'),
    spaceBefore=10,
    spaceAfter=4,
    keepWithNext=True
)

style_body = ParagraphStyle(
    'Body_Custom',
    parent=styles['BodyText'],
    fontName='Helvetica',
    fontSize=9.2,
    leading=13.2,
    textColor=colors.HexColor('#2B2D42'),
    spaceAfter=7
)

style_body_bold = ParagraphStyle(
    'BodyBold_Custom',
    parent=style_body,
    fontName='Helvetica-Bold'
)

style_callout = ParagraphStyle(
    'Callout_Custom',
    parent=styles['Normal'],
    fontName='Helvetica-Oblique',
    fontSize=8.5,
    leading=12,
    textColor=colors.HexColor('#1D3557')
)

style_table_header = ParagraphStyle(
    'TableHeader',
    parent=styles['Normal'],
    fontName='Helvetica-Bold',
    fontSize=8,
    leading=10.5,
    textColor=colors.white,
    alignment=1
)

style_table_cell = ParagraphStyle(
    'TableCell',
    parent=styles['Normal'],
    fontName='Helvetica',
    fontSize=7.8,
    leading=10.5,
    textColor=colors.HexColor('#2B2D42')
)

style_table_cell_bold = ParagraphStyle(
    'TableCellBold',
    parent=style_table_cell,
    fontName='Helvetica-Bold'
)

story = []

# ==============================================================================
# COVER / HEADER
# ==============================================================================
story.append(Spacer(1, 10))
story.append(Paragraph("SATELLITE COLLISION AVOIDANCE SYSTEM (ICPS)", style_title))
story.append(Paragraph("Milestone 4: Reference Scenario Evaluation & Performance Validation", style_subtitle))
story.append(Paragraph("Unreal Engine 5.7.4 Visualizer &bull; Authoritative D1/D2 Python Astrodynamics Solvers &bull; November 2026", style_meta))
story.append(HRFlowable(width="100%", thickness=2, color=colors.HexColor('#1D3557'), spaceBefore=3, spaceAfter=12))

# Operational Scope Notice
scope_notice_text = (
    "<b>Operational Scope Notice:</b> The scenario evaluated in this report is a frozen, physics-based simulation "
    "scenario developed strictly for system testing and demonstration. It does not represent live operational tracking, "
    "real-world collision warning, or spacecraft command execution on the physical CARTOSAT-3 satellite or operational ground segment."
)
story.append(Paragraph(scope_notice_text, style_callout))
story.append(Spacer(1, 10))

# ==============================================================================
# 1. ABSTRACT
# ==============================================================================
story.append(Paragraph("1. Abstract", style_h1))
story.append(Paragraph(
    "This report presents an <b>engineering evaluation of the reference scenario</b> for the Autonomous Satellite Collision Avoidance System (ICPS). "
    "Designed for congested Low Earth Orbit (LEO) operational regimes, the system integrates authoritative Python astrodynamic "
    "solvers with a physics-synchronized, interactive 3D playback and telemetry visualization environment implemented in Unreal Engine 5.7.4. "
    "The scientific backend models two-body orbital dynamics via a fourth-order Runge-Kutta (RK4) integrator, performs conjunction screening "
    "against close-approach thresholds, estimates the Time of Closest Approach (TCA) via iterative root-finding, propagates "
    "state covariances, and evaluates collision probability (Pc) via the Foster (1992) formulation. "
    "In the reference conjunction, a critical nominal encounter (predicted miss distance 1563.48 m vs project-defined 2000 m safety threshold) "
    "is mitigated by an autonomous 3.00 m/s radial inward (-R) impulse executed 600 s prior to nominal TCA. "
    "The manoeuvre expands the predicted miss distance to 2454.42 m (+890.94 m / +56.985% clearance improvement), shifts predicted TCA by +133.40 s, and "
    "attenuates the calculated collision probability from 3.958e-14 down to 1.239e-22, representing an 8.50 order-of-magnitude reduction "
    "(approximately a 3.195 &times; 10<sup>8</sup> reduction in calculated collision probability). "
    "<b>39 automated regression tests passed</b> in the authoritative Python suite, and Unreal Engine renders the physics-synchronized playback across an eight-step demonstration sequence.",
    style_body
))

# ==============================================================================
# 2. PROBLEM STATEMENT
# ==============================================================================
story.append(Paragraph("2. Problem Statement", style_h1))
story.append(Paragraph(
    "Orbital congestion in Low Earth Orbit has escalated significantly. With over 30,000 tracked objects and hundreds of thousands "
    "of untracked lethal fragments traveling at orbital speeds exceeding 7.5 km/s, collisions produce catastrophic cascading debris. "
    "Contemporary satellite collision avoidance workflows face specific challenges: (1) latency in manual ground-based review cycles that "
    "cannot scale to mega-constellations; (2) excessive fuel expenditure caused by conservative, unoptimized avoidance burns; and (3) a lack "
    "of high-fidelity 3D spatial visualization tools to contextualize orbital hazards for mission controllers.",
    style_body
))

# ==============================================================================
# 3. PROJECT OBJECTIVES
# ==============================================================================
story.append(Paragraph("3. Project Objectives", style_h1))
story.append(Paragraph(
    "The project objectives comprise: (1) scientific rigor in <b>two-body Keplerian orbital mechanics</b> without synthetic approximations; "
    "(2) automated optimal impulse planning across along-track, radial, and cross-track axes; (3) seamless, physics-synchronized data bridging "
    "from Python numerical solvers into Unreal Engine 5.7; (4) a high-fidelity interactive playback interface featuring photorealistic Earth, "
    "spacecraft, debris, and trajectory splines; and (5) rigorous quantitative verification with <b>39 automated regression tests passed</b>.",
    style_body
))

# ==============================================================================
# 4. SYSTEM ARCHITECTURE
# ==============================================================================
story.append(Paragraph("4. System Architecture", style_h1))
story.append(Paragraph(
    "The architecture enforces strict decoupling between scientific computation and visualization. The Python Scientific Core (D1/D2) "
    "integrates equations of motion, computes encounter geometry, and outputs an immutable JSON payload (unreal_simulation_payload.json). "
    "The Unreal Engine layer functions strictly as a playback client: USimulationDataBridge deserializes the trajectory samples, "
    "AOrbitSimulationManager synchronizes the simulation clock, and UAvoidanceInfoPanelWidget paints authoritative Slate telemetry.",
    style_body
))

# ==============================================================================
# 5 & 6. D1 BASELINE & D2 CONJUNCTION DETECTION
# ==============================================================================
story.append(Paragraph("5. D1 Baseline Debris Simulation", style_h1))
story.append(Paragraph(
    "The baseline simulator models two-body gravitational dynamics: d²r/dt² = -mu/||r||³ * r, with mu = 3.986004418e14 m³/s². "
    "Equations are integrated via RK4 with dt = 0.1 s. Protected satellite CARTOSAT-3 is simulated in a 7000 km circular orbit (altitude 621.87 km, "
    "speed 7546.05 m/s, period 5828.53 s). Debris piece Object99 is placed in a near-coplanar orbit 10 km ahead with a calibrated relative velocity.",
    style_body
))

story.append(Paragraph("6. D2 Conjunction Detection", style_h1))
story.append(Paragraph(
    "Conjunction filtering applies a broad-phase Euclidean threshold of 25000.0 m (25.0 km), followed by narrow-phase root-finding. "
    "Relative separation d(t) = ||r_sat(t) - r_deb(t)|| is monitored for local minima where d(d²)/dt = 2 * r_rel . v_rel = 0.",
    style_body
))

# ==============================================================================
# 7 & 8. TCA, MISS DISTANCE & COLLISION PROBABILITY
# ==============================================================================
story.append(Paragraph("7. TCA and Miss-Distance Estimation", style_h1))
story.append(Paragraph(
    "The system evaluates the <b>numerically estimated TCA using Brent's minimization method</b> with a convergence tolerance of 1e-6 s. "
    "For the nominal conjunction: TCA = 769.63197 s, Miss Distance = 1563.48 m, Relative Speed = 13.234 m/s. "
    "Because the miss distance breaches the project-defined 2000.0 m safety clearance threshold, autonomous avoidance planning is invoked.",
    style_body
))

story.append(Paragraph("8. Covariance Propagation and Collision Probability Estimation", style_h1))
story.append(Paragraph(
    "State error covariances are propagated via state transition matrices to TCA, projected onto the 2D B-plane, and integrated "
    "over a 5.00 m combined spherical hard-body radius using the Foster (1992) series method. "
    "Nominal Pc is evaluated at 3.958e-14 (log10(Pc) = -13.40). The asymptotic underflow status [NUMERICAL_UNDERFLOW] is strictly "
    "preserved rather than zero-clamped.<br/><br/>"
    "<b>Crucial Parameter Distinctions:</b><br/>"
    "&bull; <i>Combined Hard-Body Radius (5.00 m):</i> Physical spherical envelope enclosing the primary satellite and debris.<br/>"
    "&bull; <i>Operational Safety Clearance Threshold (2000.0 m):</i> Project-defined operational screening envelope chosen for simulation evaluation, not a universal orbital safety standard.<br/>"
    "&bull; <i>Broad-Phase Screening Distance (25000.0 m):</i> Initial broad-phase filter boundary for candidate conjunction tracking.<br/><br/>"
    "A low calculated Pc does not guarantee absolute collision prevention in physical spaceflight where non-Gaussian distribution tails, unmodeled drag variations, and debris attitude dynamics exist.",
    style_body
))

# Embedded Plot 3: Collision Probability
p3_path = os.path.join(CHARTS_DIR, "collision_probability_log_scale.png")
if os.path.exists(p3_path):
    story.append(KeepTogether([
        Spacer(1, 4),
        Image(p3_path, width=6.8 * inch, height=3.0 * inch),
        Spacer(1, 2),
        Paragraph("<b>Figure 1:</b> Logarithmic collision probability reduction (8.50 decades) and numerical underflow preservation.", style_callout),
        Spacer(1, 6)
    ]))

# ==============================================================================
# 9 & 10. MANOEUVRE PLANNING & DATA BRIDGE
# ==============================================================================
story.append(Paragraph("9. Autonomous Avoidance Manoeuvre Planning", style_h1))
story.append(Paragraph(
    "The avoidance planner evaluates an impulsive Delta-V budget executed at an early warning epoch (T+169.63197 s, exactly 600.0 s / 10.0 min prior to nominal TCA). "
    "The optimal selected manoeuvre is MAN_006_-R_3.00mps_T170s with magnitude Delta-V = 3.00 m/s in the radial inward (-R) direction.<br/><br/>"
    "<b>Analytical Orbital Mechanics Verification:</b><br/>"
    "The impulsive burn is applied to the protected satellite in a circular Low Earth Orbit (r0 = 7000.0 km, v0 = 7546.053 m/s, mu = 3.986004418e14 m^3/s^2):<br/>"
    "• <b>Pre-Burn State:</b> r_pre = [6883287.72, 1272929.77, 0.00] m (|r_pre| = 7000.000 km), v_pre = [-1372.23, 7420.24, 0.00] m/s (|v_pre| = 7546.053 m/s).<br/>"
    "• <b>Post-Burn State:</b> r_post = r_pre (continuous), v_post = v_pre + Delta_v_eci = [-1375.18, 7419.69, 0.00] m/s (|v_post| = 7546.054 m/s).<br/>"
    "• <b>Specific Energy & Semi-Major Axis:</b> Specific energy increases by Delta_E = (Delta_v)^2 / 2 = +4.50 J/kg (-28471460.13 to -28471455.63 J/kg). "
    "The semi-major axis increases by Delta_a approx a * (Delta_v / v0)^2 = +1.11 m (7000000.00 m to 7000001.11 m, Delta_a/a = +1.58e-7).<br/>"
    "• <b>Orbital Period & Eccentricity:</b> Orbital period increases by Delta_T approx (3/2) * T * (Delta_a/a) approx +1.38 ms (5828.517 s to 5828.518 s). "
    "Induced orbital eccentricity is e approx Delta_v / v0 approx 0.000398. Specific angular momentum is unchanged (Delta |h| = 0.0 m^2/s).<br/>"
    "• <b>Coupled Avoidance Mechanism at Nominal TCA (600 s post-burn):</b> At continuous nominal TCA (t = 769.63 s), the displacement vector Delta_r = [-1961.61, -478.26, 0.00] m ECI resolves in the nominal RTN frame as "
    "Delta_r_R = -1677.14 m (radial lower altitude) and Delta_r_T = +1124.21 m (along-track forward phasing lead), with Delta_r_N = 0.00 m, yielding exact Euclidean norm 2019.07 m "
    "(at discrete 770.0 s grid sample in Simulation_Results.json, Delta_r_R = -1676.69 m, Delta_r_T = +1124.73 m, norm = 2018.99 m). "
    "Squared-component contributions are 69.0% radial and 31.0% along-track (or 59.8% / 40.2% by absolute linear ratio). "
    "Miss distance dilation is driven jointly by coupled radial altitude displacement and along-track phasing lead.",
    style_body
))

# Embedded Plot 5: Manoeuvre Geometry
p5_path = os.path.join(CHARTS_DIR, "manoeuvre_deltav_geometry.png")
if os.path.exists(p5_path):
    story.append(KeepTogether([
        Spacer(1, 4),
        Image(p5_path, width=6.4 * inch, height=3.1 * inch),
        Spacer(1, 2),
        Paragraph("<b>Figure 2:</b> Impulsive avoidance manoeuvre geometry and RTN coordinate alignment.", style_callout),
        Spacer(1, 6)
    ]))

story.append(Paragraph("10. Python-to-Unreal Integration & Data Bridge", style_h1))
story.append(Paragraph(
    "Coordinate conversion transforms ECI right-handed coordinates (m) to Unreal left-handed coordinates (uu, 1 uu = 100 m): "
    "X_ue = 0.01 * X_eci, Y_ue = -0.01 * Y_eci, Z_ue = 0.01 * Z_eci. "
    "The JSON payload feeds native C++ data structures in USimulationDataBridge without runtime solver drift.",
    style_body
))

# ==============================================================================
# 11 & 12. VISUALIZATION & PERFORMANCE EVALUATION
# ==============================================================================
story.append(Paragraph("11. Interactive Visualization & Telemetry HUD", style_h1))
story.append(Paragraph(
    "The visual scene incorporates photorealistic Earth surface and atmospheric limb shaders, high-detail spacecraft with golden Kapton "
    "insulation and segmented photovoltaic arrays, tumbling debris fragments, and three continuous spline trajectory paths (cyan nominal, "
    "red debris, green modified). A custom Slate HUD displays simulation clock, TCA, miss distance, Delta-V, and collision probability in real time.",
    style_body
))

story.append(Paragraph("12. Quantitative Performance Evaluation", style_h1))
story.append(Paragraph(
    "The table below presents the authoritative metrics comparing the nominal and post-manoeuvre states:",
    style_body
))

# Table: Performance Metrics
eval_table_data = [
    [Paragraph("<b>Performance Metric</b>", style_table_header),
     Paragraph("<b>Nominal State</b>", style_table_header),
     Paragraph("<b>Post-Manoeuvre</b>", style_table_header),
     Paragraph("<b>Delta (Change)</b>", style_table_header),
     Paragraph("<b>Operational Impact</b>", style_table_header)],
    
    [Paragraph("Miss Distance", style_table_cell_bold),
     Paragraph("1563.48 m", style_table_cell),
     Paragraph("2454.42 m", style_table_cell),
     Paragraph("+890.94 m (+56.99%)", style_table_cell_bold),
     Paragraph("Meets project-defined 2000.0 m threshold", style_table_cell)],
    
    [Paragraph("Time of Closest Approach", style_table_cell_bold),
     Paragraph("769.63 s", style_table_cell),
     Paragraph("903.03 s", style_table_cell),
     Paragraph("+133.40 s (+2.22 min)", style_table_cell),
     Paragraph("Encounter phase delayed safely", style_table_cell)],
    
    [Paragraph("Collision Probability (Pc)", style_table_cell_bold),
     Paragraph("3.958e-14", style_table_cell),
     Paragraph("1.239e-22", style_table_cell),
     Paragraph("approx. 3.195e8 x reduction", style_table_cell_bold),
     Paragraph("approx. 3.195 &times; 10<sup>8</sup> reduction in Pc", style_table_cell)],
    
    [Paragraph("Logarithmic Risk log10(Pc)", style_table_cell_bold),
     Paragraph("-13.40", style_table_cell),
     Paragraph("-21.91", style_table_cell),
     Paragraph("-8.50 decades", style_table_cell_bold),
     Paragraph("8.50 orders of magnitude drop", style_table_cell)],
    
    [Paragraph("Operational Risk Classification", style_table_cell_bold),
     Paragraph("CRITICAL ALERT", style_table_cell),
     Paragraph("RESOLVED SAFE", style_table_cell),
     Paragraph("Threshold satisfied", style_table_cell),
     Paragraph("Meets the defined simulation safety threshold", style_table_cell)],
    
    [Paragraph("Manoeuvre Control Effort", style_table_cell_bold),
     Paragraph("0.00 m/s", style_table_cell),
     Paragraph("3.00 m/s (-R)", style_table_cell),
     Paragraph("+3.00 m/s", style_table_cell),
     Paragraph("Radial inward impulse (illustrative ~1.4 kg)", style_table_cell)],
    
    [Paragraph("Peak Trajectory Separation", style_table_cell_bold),
     Paragraph("0.00 m", style_table_cell),
     Paragraph("3008.50 m", style_table_cell),
     Paragraph("+3008.50 m", style_table_cell),
     Paragraph("Maximum nominal-to-modified deviation at T=1000s", style_table_cell)]
]

t_eval = Table(eval_table_data, colWidths=[1.5 * inch, 1.2 * inch, 1.2 * inch, 1.4 * inch, 1.7 * inch])
t_eval.setStyle(TableStyle([
    ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1D3557')),
    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
    ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#CBD5E0')),
    ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.HexColor('#F8F9FA'), colors.white]),
    ('TOPPADDING', (0, 0), (-1, -1), 3),
    ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
]))

story.append(KeepTogether([
    t_eval,
    Spacer(1, 3),
    Paragraph("<b>Measurement Distinction:</b> Nominal-to-modified trajectory deviation (||r_mod - r_nom||) measures protected spacecraft divergence from its nominal path (3008.5 m peak). Satellite-to-debris relative miss distance (||r_sat - r_deb||) measures separation between satellite and debris (1563.5 m nominal, 2454.4 m post-manoeuvre).", style_callout),
    Spacer(1, 8)
]))

# Embedded Plot 2: Miss Distance Comparison
p2_path = os.path.join(CHARTS_DIR, "miss_distance_comparison.png")
if os.path.exists(p2_path):
    story.append(KeepTogether([
        Spacer(1, 4),
        Image(p2_path, width=6.8 * inch, height=3.3 * inch),
        Spacer(1, 2),
        Paragraph("<b>Figure 3:</b> Relative separation distance vs time comparing nominal and post-manoeuvre encounters.", style_callout),
        Spacer(1, 6)
    ]))

# Embedded Plot 4: Trajectory Deviation
p4_path = os.path.join(CHARTS_DIR, "trajectory_deviation_vs_time.png")
if os.path.exists(p4_path):
    story.append(KeepTogether([
        Spacer(1, 4),
        Image(p4_path, width=6.8 * inch, height=3.3 * inch),
        Spacer(1, 2),
        Paragraph("<b>Figure 4:</b> Spacecraft trajectory deviation accumulated along the modified orbit away from nominal path.", style_callout),
        Spacer(1, 6)
    ]))

# ==============================================================================
# 13. RESULTS AND DISCUSSION
# ==============================================================================
story.append(Paragraph("13. Results and Comparative Discussion", style_h1))
story.append(Paragraph(
    "The analysis demonstrates that early radial inward impulsive burns represent an <b>effective strategy for the evaluated reference scenario</b>. "
    "In the nominal encounter, the miss distance was 1563.48 m, breaching the project-defined 2000.0 m safety clearance threshold. "
    "Execution of the -R 3.00 m/s impulse expanded the miss distance to 2454.42 m (+890.94 m / +56.985%), establishing a 454.4 m buffer beyond the threshold. "
    "The manoeuvre achieves an <b>approximate 3.195 &times; 10<sup>8</sup> reduction in calculated collision probability</b>, corresponding to an 8.50 decade reduction in risk.<br/><br/>"
    "<b>Propellant Mass Estimation Context:</b><br/>"
    "<i>Illustrative propellant estimate based on assumed spacecraft mass and specific impulse; not a measured or planner-generated mission propellant requirement.</i><br/>"
    "Using Tsiolkovsky's equation dm = m0 * (1 - exp(-dv / (Isp * g0))) with assumed parameters: initial mass m0 = 1000 kg, Isp = 220 s (representative monopropellant hydrazine), "
    "Delta-V = 3.00 m/s, g0 = 9.80665 m/s²:<br/>"
    "dm = 1000 * (1 - exp(-3.00 / (220 * 9.80665))) &asymp; 1.39 kg.<br/>"
    "This illustrates that an expenditure of under 1.4 kg of propellant represents modest fuel consumption for a 1000 kg class bus. The system reports the authoritative Delta-V = 3.00 m/s as the standardized control effort metric.",
    style_body
))

# Embedded Plot 6: TCA Shift Timeline
p6_path = os.path.join(CHARTS_DIR, "tca_shift_timeline.png")
if os.path.exists(p6_path):
    story.append(KeepTogether([
        Spacer(1, 4),
        Image(p6_path, width=6.8 * inch, height=3.0 * inch),
        Spacer(1, 2),
        Paragraph("<b>Figure 5:</b> Mission chronology, impulsive burn timing, and TCA shift verification.", style_callout),
        Spacer(1, 6)
    ]))

# ==============================================================================
# 14. CURRENT LIMITATIONS
# ==============================================================================
story.append(Paragraph("14. Current System Limitations", style_h1))
story.append(Paragraph(
    "In accordance with engineering integrity, current limitations are explicitly documented: "
    "(1) Gravitational dynamics are modeled using ideal two-body Newtonian formulations, omitting geopotential harmonics (J2, J3), "
    "atmospheric drag, solar radiation pressure, and third-body lunisolar perturbations; "
    "(2) Manoeuvres are treated as instantaneous velocity impulses (Delta-V) rather than finite-duration burns subject to attitude slew "
    "dynamics and thruster ramp-up; "
    "(3) Covariance propagation assumes linear dynamics with Gaussian probability distributions; "
    "(4) The software operates as a validated simulation testbed on a frozen reference scenario; and "
    "(5) The software does not interface with physical flight hardware. Operational flight readiness is not claimed.",
    style_body
))

# ==============================================================================
# 15. FUTURE IMPROVEMENTS
# ==============================================================================
story.append(Paragraph("15. Future Improvements & Roadmap", style_h1))
story.append(Paragraph(
    "Future development will focus on: (1) High-Precision Orbit Propagation (HPOP) incorporating EGM2008 gravity and NRLMSISE-00 drag; "
    "(2) Continuous low-thrust electric propulsion optimal control formulations; (3) Non-linear Gaussian Mixture Model (GMM) collision "
    "probability estimators; (4) Automated live CCSDS Conjunction Data Message (CDM) network ingestion; and (5) Real-time hardware-in-the-loop "
    "(HIL) testing on embedded flight computing architectures.",
    style_body
))

# ==============================================================================
# 16. CONCLUSION
# ==============================================================================
story.append(Paragraph("16. Conclusion", style_h1))
story.append(Paragraph(
    "Milestone 4 concludes the engineering evaluation of the Autonomous Satellite Collision Avoidance System. "
    "The implementation <b>demonstrates in the evaluated simulation</b> that coupling rigorous, frozen Python astrodynamics with a real-time Unreal Engine 5.7 visualization "
    "layer yields an optimal, transparent, and verifiable collision avoidance platform. With <b>39 automated regression tests passed</b> in the D2 regression test suite, "
    "an 890.94 m clearance expansion, an 8.50 order-of-magnitude collision probability reduction (approximately a 3.195 &times; 10<sup>8</sup> reduction in calculated collision probability), "
    "and a complete suite of engineering deliverables, the system satisfies all defined simulation safety thresholds.",
    style_body
))

# ==============================================================================
# 17. REFERENCES
# ==============================================================================
story.append(Paragraph("17. References", style_h1))
refs = [
    "1. Foster, J. L., & Estes, H. S. (1992). A Parametric Analysis of Orbital Debris Collision Probability and Maneuver Strategy for Space Station Freedom. NASA-JSC-25898.",
    "2. Alfriend, K. T., et al. (1999). Probability of Collision Error Analysis. Space Debris, 1(1), 17-35.",
    "3. Vallado, D. A. (2013). Fundamentals of Astrodynamics and Applications (4th ed.). Microcosm Press / Springer.",
    "4. Battin, R. H. (1999). An Introduction to the Mathematics and Methods of Astrodynamics. AIAA Education Series.",
    "5. Klinkrad, H. (2006). Space Debris: Models and Risk Analysis. Springer Praxis Publishing.",
    "6. Chan, K. (2008). Spacecraft Collision Probability. The Aerospace Press.",
    "7. CCSDS (2019). Conjunction Data Message (CDM). Recommended Standard CCSDS 508.0-B-1."
]
for ref in refs:
    story.append(Paragraph(ref, style_body))

doc.build(story, canvasmaker=NumberedCanvas)
file_size_kb = os.path.getsize(PDF_PATH) / 1024
print(f"Final Technical Report PDF compiled successfully!")
print(f"Output: {PDF_PATH} ({file_size_kb:.1f} KB)")
