"""
visualization_3d.py
===================
Satellite Collision Avoidance System — Person 2 Deliverable
Integrated 3D Orbital Visualization, Live Telemetry Dashboard, and Control Interface.

Conforms to integration rules: consumes data_loader, propagator, relative_motion,
and analysis_engine without modifying the Person 1 backend.
"""

import sys
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.gridspec import GridSpec
from matplotlib.animation import FuncAnimation
from matplotlib.widgets import Button, Slider
from mpl_toolkits.mplot3d import Axes3D
from datetime import datetime, timedelta, timezone

# Person 1 Backend Integration
from data_loader import load_tle_data
from propagator import create_satellite, propagate_object
from analysis_engine import calculate_encounter_metrics, SAFE_DISTANCE_KM, CLOSE_APPROACH_KM


class SatelliteVisualizer3D:
    def __init__(self, mode="real", headless=False):
        """
        Parameters
        ----------
        mode : str
            'real' for real tracked TLE data or 'synthetic' for controlled close-approach test.
        headless : bool
            If True, runs without opening an interactive GUI window (for tests/automation).
        """
        self.mode = mode
        self.headless = headless
        self.is_paused = False

        # Simulation parameters
        self.speed_multipliers = [1, 5, 10, 60, 300]
        self.speed_idx = 3  # default 60x
        self.sim_speed = self.speed_multipliers[self.speed_idx]
        self.update_interval = 50  # milliseconds per frame

        # Earth constant
        self.R_EARTH = 6371.0  # km

        # Trail length
        self.max_trail = 300

        # Initialize Data & State
        self._init_real_data()
        self._init_synthetic_data()
        self.reset_state()

        if not self.headless:
            self._setup_ui()

    # =========================================================================
    # DATA INITIALIZATION (BACKEND INTEGRATION)
    # =========================================================================

    def _init_real_data(self):
        """Load TLE data and prepare SGP4 satellite objects."""
        tle_file = "data/orbital_data.txt"
        self.tle_objects = load_tle_data(tle_file)
        self.satellites = {}
        for obj in self.tle_objects:
            self.satellites[obj["name"]] = create_satellite(obj["line1"], obj["line2"])

        cartosat = self.satellites["CARTOSAT-3"]
        from sgp4.api import days2mdhms
        month, day, hour, minute, second = days2mdhms(
            cartosat.epochyr + 2000,
            cartosat.epochdays
        )
        self.real_start_time = datetime(
            cartosat.epochyr + 2000,
            month,
            day,
            hour,
            minute,
            int(second),
            tzinfo=timezone.utc
        )

        # Precompute 1 complete orbit (~100 min) for full 3D trajectory display
        self.cartosat_orbit_pts = []
        self.pslv_orbit_pts = []
        orbit_duration_min = 100
        step_sec = 45
        total_steps = int(orbit_duration_min * 60 / step_sec)

        for step in range(total_steps):
            t = self.real_start_time + timedelta(seconds=step * step_sec)
            pos_c, _ = propagate_object(self.satellites["CARTOSAT-3"], "CARTOSAT-3", t)
            pos_p, _ = propagate_object(self.satellites["PSLV R/B"], "PSLV R/B", t)
            self.cartosat_orbit_pts.append(pos_c)
            self.pslv_orbit_pts.append(pos_p)

        self.cartosat_orbit_pts = np.array(self.cartosat_orbit_pts)
        self.pslv_orbit_pts = np.array(self.pslv_orbit_pts)

    def _init_synthetic_data(self):
        """Define initial conditions for the controlled synthetic encounter."""
        self.syn_sat_initial = np.array([-1000.0, 7000.0, 0.0])
        self.syn_deb_initial = np.array([1000.0, 7005.0, 0.0])
        self.syn_sat_vel = np.array([5.0, 0.0, 0.0])
        self.syn_deb_vel = np.array([-5.0, 0.0, 0.0])

        # Precompute synthetic trajectory path (-200s to +400s)
        t_span = np.linspace(0, 400, 200)
        self.syn_sat_path = np.array([self.syn_sat_initial + self.syn_sat_vel * t for t in t_span])
        self.syn_deb_path = np.array([self.syn_deb_initial + self.syn_deb_vel * t for t in t_span])

    def reset_state(self):
        """Reset the simulation clock, telemetry, CAD, TCA, and event records."""
        # Simulation clock
        self.real_current_time = self.real_start_time
        self.synthetic_elapsed_sec = 0.0

        # Trajectory trail histories
        self.sat_trail_x, self.sat_trail_y, self.sat_trail_z = [], [], []
        self.sec_trail_x, self.sec_trail_y, self.sec_trail_z = [], [], []

        # Conjunction Tracking (CAD & TCA)
        self.minimum_distance = float("inf")
        self.tca_str = "Calculating..."
        self.cad_km = float("inf")

        # Persistent Close Approach Encounter Event (Task 4)
        self.close_approach_detected = False
        self.persisted_event_record = None

        # Current telemetry metrics dict
        self.current_metrics = None

    # =========================================================================
    # SIMULATION STEP ENGINE
    # =========================================================================

    def step(self):
        """
        Advance simulation by one time step, compute states using Person 1 backend,
        evaluate relative motion & encounter metrics, and update CAD/TCA.
        """
        if self.mode == "real":
            # Advance real-time clock
            self.real_current_time += timedelta(seconds=self.sim_speed)
            time_display = self.real_current_time.strftime("%Y-%m-%d %H:%M:%S UTC")

            # Propagate via SGP4 backend
            pos_a, vel_a = propagate_object(
                self.satellites["CARTOSAT-3"], "CARTOSAT-3", self.real_current_time
            )
            pos_b, vel_b = propagate_object(
                self.satellites["PSLV R/B"], "PSLV R/B", self.real_current_time
            )

            primary_name = "CARTOSAT-3 (Primary)"
            secondary_name = "PSLV R/B (Secondary)"

        else:
            # Advance synthetic scenario clock
            self.synthetic_elapsed_sec += (self.sim_speed * 0.1)  # scaled for visible smooth encounter
            time_display = f"T+ {self.synthetic_elapsed_sec:.1f} s"

            pos_a = self.syn_sat_initial + self.syn_sat_vel * self.synthetic_elapsed_sec
            vel_a = self.syn_sat_vel
            pos_b = self.syn_deb_initial + self.syn_deb_vel * self.synthetic_elapsed_sec
            vel_b = self.syn_deb_vel

            primary_name = "TEST SATELLITE"
            secondary_name = "TEST DEBRIS"

        pos_a = np.asarray(pos_a, dtype=float)
        vel_a = np.asarray(vel_a, dtype=float)
        pos_b = np.asarray(pos_b, dtype=float)
        vel_b = np.asarray(vel_b, dtype=float)

        # Call Shared Analysis Engine (Integration Rule: reuse Person 1 backend)
        metrics = calculate_encounter_metrics(pos_a, vel_a, pos_b, vel_b)
        dist = metrics["distance_km"]

        # Track CAD & TCA
        if dist < self.minimum_distance:
            self.minimum_distance = dist
            self.cad_km = dist
            self.tca_str = time_display

        # Persistent Encounter Event Record (Task 4)
        if dist <= CLOSE_APPROACH_KM and not self.close_approach_detected:
            self.close_approach_detected = True
            self.persisted_event_record = {
                "detected_at": time_display,
                "cad_km": self.cad_km,
                "tca": self.tca_str,
                "status": "CLOSE APPROACH",
                "level": "HIGH"
            }
        elif self.close_approach_detected:
            # Keep updating CAD in the persisted record as encounter progresses
            self.persisted_event_record["cad_km"] = self.cad_km
            self.persisted_event_record["tca"] = self.tca_str

        # Update Trail Buffer
        self.sat_trail_x.append(pos_a[0])
        self.sat_trail_y.append(pos_a[1])
        self.sat_trail_z.append(pos_a[2])

        self.sec_trail_x.append(pos_b[0])
        self.sec_trail_y.append(pos_b[1])
        self.sec_trail_z.append(pos_b[2])

        if len(self.sat_trail_x) > self.max_trail:
            self.sat_trail_x.pop(0)
            self.sat_trail_y.pop(0)
            self.sat_trail_z.pop(0)

        if len(self.sec_trail_x) > self.max_trail:
            self.sec_trail_x.pop(0)
            self.sec_trail_y.pop(0)
            self.sec_trail_z.pop(0)

        # Altitudes (km above Earth surface)
        alt_a = np.linalg.norm(pos_a) - self.R_EARTH
        alt_b = np.linalg.norm(pos_b) - self.R_EARTH
        spd_a = np.linalg.norm(vel_a)
        spd_b = np.linalg.norm(vel_b)

        self.current_metrics = {
            "mode": self.mode,
            "time_display": time_display,
            "primary_name": primary_name,
            "secondary_name": secondary_name,
            "pos_a": pos_a,
            "vel_a": vel_a,
            "alt_a": alt_a,
            "spd_a": spd_a,
            "pos_b": pos_b,
            "vel_b": vel_b,
            "alt_b": alt_b,
            "spd_b": spd_b,
            "encounter": metrics,
            "cad_km": self.cad_km,
            "tca_str": self.tca_str,
            "close_approach_detected": self.close_approach_detected,
            "persisted_event": self.persisted_event_record
        }

        return self.current_metrics

    # =========================================================================
    # 3D USER INTERFACE SETUP
    # =========================================================================

    def _setup_ui(self):
        """Construct the high-contrast space-grade 3D viewer, telemetry HUD, and interactive controls."""
        plt.style.use('dark_background')
        self.fig = plt.figure(figsize=(16, 9.5), facecolor="#0B0F19")
        self.fig.canvas.manager.set_window_title("Satellite Collision Avoidance System — 3D Operations Center")

        # Create Layout: 3D Visualization (left 63%), Telemetry Dashboard (right 37%), Bottom Controls
        gs = GridSpec(
            2, 2,
            width_ratios=[1.7, 1.0],
            height_ratios=[1.0, 0.08],
            left=0.03, right=0.97, top=0.94, bottom=0.03,
            wspace=0.12, hspace=0.10
        )

        self.ax_3d = self.fig.add_subplot(gs[0, 0], projection='3d')
        self.ax_hud = self.fig.add_subplot(gs[0, 1])
        self.ax_ctrl = self.fig.add_subplot(gs[1, :])

        # Style 3D Subplot
        self.ax_3d.set_facecolor("#080B12")
        self.ax_3d.xaxis.pane.set_edgecolor('#1E293B')
        self.ax_3d.yaxis.pane.set_edgecolor('#1E293B')
        self.ax_3d.zaxis.pane.set_edgecolor('#1E293B')
        self.ax_3d.xaxis.pane.fill = False
        self.ax_3d.yaxis.pane.fill = False
        self.ax_3d.zaxis.pane.fill = False
        self.ax_3d.grid(color='#1E293B', linestyle=':', linewidth=0.6)
        self.ax_3d.set_xlabel("X (km)", color="#94A3B8", fontsize=9)
        self.ax_3d.set_ylabel("Y (km)", color="#94A3B8", fontsize=9)
        self.ax_3d.set_zlabel("Z (km)", color="#94A3B8", fontsize=9)
        self.ax_3d.tick_params(colors="#64748B", labelsize=8)

        # Draw 3D Earth
        self._draw_earth()

        # 3D Graphic Elements
        self.cartosat_orbit_line, = self.ax_3d.plot([], [], [], color="#00F0FF", linestyle="--", linewidth=1.2, alpha=0.5, label="CARTOSAT-3 Orbit")
        self.pslv_orbit_line, = self.ax_3d.plot([], [], [], color="#F43F5E", linestyle="--", linewidth=1.2, alpha=0.5, label="PSLV R/B Orbit")

        self.sat_trail_line, = self.ax_3d.plot([], [], [], color="#38BDF8", linewidth=2.0, alpha=0.85)
        self.sec_trail_line, = self.ax_3d.plot([], [], [], color="#FB7185", linewidth=2.0, alpha=0.85)

        self.sat_point, = self.ax_3d.plot([], [], [], marker="o", markersize=9, color="#00F0FF", markeredgecolor="#FFFFFF", markeredgewidth=1.2)
        self.sec_point, = self.ax_3d.plot([], [], [], marker="s", markersize=8, color="#F43F5E", markeredgecolor="#FFFFFF", markeredgewidth=1.2)

        self.conjunction_line, = self.ax_3d.plot([], [], [], color="#EF4444", linestyle=":", linewidth=1.8, alpha=0.9)

        self.sat_text = self.ax_3d.text(0, 0, 0, "", color="#00F0FF", fontsize=9, fontweight="bold")
        self.sec_text = self.ax_3d.text(0, 0, 0, "", color="#F43F5E", fontsize=9, fontweight="bold")

        self.ax_3d.legend(loc="upper left", facecolor="#0B0F19", edgecolor="#334155", fontsize=8, labelcolor="#E2E8F0")

        # Style HUD Panel
        self.ax_hud.set_facecolor("#0F172A")
        self.ax_hud.set_xticks([])
        self.ax_hud.set_yticks([])
        for spine in self.ax_hud.spines.values():
            spine.set_edgecolor("#334155")
            spine.set_linewidth(1.5)

        self.hud_title = self.ax_hud.text(
            0.5, 0.965, "SATELLITE COLLISION AVOIDANCE SYSTEM",
            color="#38BDF8", fontsize=12, fontweight="bold", ha="center", va="top"
        )
        self.hud_content = self.ax_hud.text(
            0.05, 0.915, "", color="#F8FAFC", fontsize=8.8, fontfamily="monospace",
            va="top", ha="left", linespacing=1.28
        )
        self.hud_status_badge = self.ax_hud.text(
            0.5, 0.16, "", color="#FFFFFF", fontsize=11, fontweight="bold",
            ha="center", va="center", bbox=dict(boxstyle="round,pad=0.5", facecolor="#10B981", edgecolor="#34D399")
        )
        self.hud_event_box = self.ax_hud.text(
            0.5, 0.05, "", color="#CBD5E1", fontsize=8.5, fontfamily="monospace",
            ha="center", va="center"
        )

        # Style Control Subplot & Widgets
        self.ax_ctrl.set_facecolor("#0B0F19")
        self.ax_ctrl.axis("off")
        self._setup_control_widgets()

        # Keyboard Navigation
        self.fig.canvas.mpl_connect('key_press_event', self._on_key_press)

        # Setup initial view limits
        self._update_3d_view_limits()

    def _draw_earth(self):
        """Render a high-precision 3D Earth sphere with wireframe latitude/longitude grid."""
        phi = np.linspace(0, np.pi, 25)
        theta = np.linspace(0, 2 * np.pi, 35)
        phi_grid, theta_grid = np.meshgrid(phi, theta)

        x = self.R_EARTH * np.sin(phi_grid) * np.cos(theta_grid)
        y = self.R_EARTH * np.sin(phi_grid) * np.sin(theta_grid)
        z = self.R_EARTH * np.cos(phi_grid)

        # Earth sphere surface
        self.earth_surface = self.ax_3d.plot_surface(
            x, y, z, color="#0284C7", alpha=0.22, rstride=1, cstride=1,
            edgecolors="#1E40AF", linewidth=0.4, antialiased=True
        )

        # Highlight Equator ring
        eq_theta = np.linspace(0, 2 * np.pi, 100)
        eq_x = self.R_EARTH * np.cos(eq_theta)
        eq_y = self.R_EARTH * np.sin(eq_theta)
        eq_z = np.zeros_like(eq_theta)
        self.ax_3d.plot(eq_x, eq_y, eq_z, color="#38BDF8", linewidth=1.2, linestyle="--", alpha=0.7)

    def _setup_control_widgets(self):
        """Construct interactive buttons: START/PAUSE, RESET, SPEED, REAL DATA, TEST MODE."""
        # Button layout parameters
        btn_y = 0.02
        btn_h = 0.045

        # [PLAY / PAUSE]
        ax_play = self.fig.add_axes([0.05, btn_y, 0.11, btn_h])
        self.btn_play = Button(ax_play, "PAUSE", color="#1E293B", hovercolor="#334155")
        self.btn_play.label.set_color("#38BDF8")
        self.btn_play.label.set_fontsize(9)
        self.btn_play.label.set_fontweight("bold")
        self.btn_play.on_clicked(self.toggle_play_pause)

        # [RESET]
        ax_reset = self.fig.add_axes([0.17, btn_y, 0.09, btn_h])
        self.btn_reset = Button(ax_reset, "RESET", color="#1E293B", hovercolor="#334155")
        self.btn_reset.label.set_color("#F8FAFC")
        self.btn_reset.label.set_fontsize(9)
        self.btn_reset.on_clicked(self.on_reset_clicked)

        # [SPEED 1X]
        ax_sp1 = self.fig.add_axes([0.27, btn_y, 0.06, btn_h])
        self.btn_sp1 = Button(ax_sp1, "1x", color="#1E293B", hovercolor="#334155")
        self.btn_sp1.label.set_color("#94A3B8")
        self.btn_sp1.label.set_fontsize(8.5)
        self.btn_sp1.on_clicked(lambda event: self.set_speed(1))

        # [SPEED 10X]
        ax_sp10 = self.fig.add_axes([0.335, btn_y, 0.06, btn_h])
        self.btn_sp10 = Button(ax_sp10, "10x", color="#1E293B", hovercolor="#334155")
        self.btn_sp10.label.set_color("#94A3B8")
        self.btn_sp10.label.set_fontsize(8.5)
        self.btn_sp10.on_clicked(lambda event: self.set_speed(10))

        # [SPEED 60X]
        ax_sp60 = self.fig.add_axes([0.40, btn_y, 0.06, btn_h])
        self.btn_sp60 = Button(ax_sp60, "60x", color="#0284C7", hovercolor="#0369A1")
        self.btn_sp60.label.set_color("#FFFFFF")
        self.btn_sp60.label.set_fontsize(8.5)
        self.btn_sp60.label.set_fontweight("bold")
        self.btn_sp60.on_clicked(lambda event: self.set_speed(60))

        # [SPEED 300X]
        ax_sp300 = self.fig.add_axes([0.465, btn_y, 0.06, btn_h])
        self.btn_sp300 = Button(ax_sp300, "300x", color="#1E293B", hovercolor="#334155")
        self.btn_sp300.label.set_color("#94A3B8")
        self.btn_sp300.label.set_fontsize(8.5)
        self.btn_sp300.on_clicked(lambda event: self.set_speed(300))

        # [REAL DATA MODE]
        ax_real = self.fig.add_axes([0.55, btn_y, 0.18, btn_h])
        self.btn_real = Button(ax_real, "REAL DATA MODE", color="#0284C7" if self.mode == "real" else "#1E293B", hovercolor="#0369A1")
        self.btn_real.label.set_color("#FFFFFF" if self.mode == "real" else "#94A3B8")
        self.btn_real.label.set_fontsize(8.5)
        self.btn_real.label.set_fontweight("bold" if self.mode == "real" else "normal")
        self.btn_real.on_clicked(lambda event: self.set_mode("real"))

        # [SYNTHETIC TEST MODE]
        ax_test = self.fig.add_axes([0.74, btn_y, 0.20, btn_h])
        self.btn_test = Button(ax_test, "SYNTHETIC TEST MODE", color="#D97706" if self.mode == "synthetic" else "#1E293B", hovercolor="#B45309")
        self.btn_test.label.set_color("#FFFFFF" if self.mode == "synthetic" else "#94A3B8")
        self.btn_test.label.set_fontsize(8.5)
        self.btn_test.label.set_fontweight("bold" if self.mode == "synthetic" else "normal")
        self.btn_test.on_clicked(lambda event: self.set_mode("synthetic"))

    def _update_3d_view_limits(self):
        """Adjust 3D coordinate system bounding box based on active mode."""
        if self.mode == "real":
            lim = 8500.0
            self.ax_3d.set_xlim(-lim, lim)
            self.ax_3d.set_ylim(-lim, lim)
            self.ax_3d.set_zlim(-lim, lim)

            # Display real orbital ellipse trajectories
            self.cartosat_orbit_line.set_data(self.cartosat_orbit_pts[:, 0], self.cartosat_orbit_pts[:, 1])
            self.cartosat_orbit_line.set_3d_properties(self.cartosat_orbit_pts[:, 2])
            self.pslv_orbit_line.set_data(self.pslv_orbit_pts[:, 0], self.pslv_orbit_pts[:, 1])
            self.pslv_orbit_line.set_3d_properties(self.pslv_orbit_pts[:, 2])
        else:
            lim = 8500.0
            self.ax_3d.set_xlim(-lim, lim)
            self.ax_3d.set_ylim(-lim, lim)
            self.ax_3d.set_zlim(-lim, lim)

            # Display synthetic trajectory straight passes
            self.cartosat_orbit_line.set_data(self.syn_sat_path[:, 0], self.syn_sat_path[:, 1])
            self.cartosat_orbit_line.set_3d_properties(self.syn_sat_path[:, 2])
            self.pslv_orbit_line.set_data(self.syn_deb_path[:, 0], self.syn_deb_path[:, 1])
            self.pslv_orbit_line.set_3d_properties(self.syn_deb_path[:, 2])

    # =========================================================================
    # EVENT HANDLERS & CONTROLS
    # =========================================================================

    def toggle_play_pause(self, event=None):
        self.is_paused = not self.is_paused
        if self.is_paused:
            self.btn_play.label.set_text("PLAY")
            self.btn_play.label.set_color("#10B981")
        else:
            self.btn_play.label.set_text("PAUSE")
            self.btn_play.label.set_color("#38BDF8")
        self.fig.canvas.draw_idle()

    def on_reset_clicked(self, event=None):
        self.reset_state()
        self._update_3d_view_limits()
        self.fig.canvas.draw_idle()

    def set_speed(self, speed):
        self.sim_speed = speed
        for val, btn in [(1, self.btn_sp1), (10, self.btn_sp10), (60, self.btn_sp60), (300, self.btn_sp300)]:
            if val == speed:
                btn.color = "#0284C7"
                btn.label.set_color("#FFFFFF")
                btn.label.set_fontweight("bold")
            else:
                btn.color = "#1E293B"
                btn.label.set_color("#94A3B8")
                btn.label.set_fontweight("normal")
        self.fig.canvas.draw_idle()

    def set_mode(self, new_mode):
        if self.mode == new_mode:
            return
        self.mode = new_mode
        self.reset_state()
        self._update_3d_view_limits()

        if new_mode == "real":
            self.btn_real.color = "#0284C7"
            self.btn_real.label.set_color("#FFFFFF")
            self.btn_real.label.set_fontweight("bold")
            self.btn_test.color = "#1E293B"
            self.btn_test.label.set_color("#94A3B8")
            self.btn_test.label.set_fontweight("normal")
            self.set_speed(60)
        else:
            self.btn_real.color = "#1E293B"
            self.btn_real.label.set_color("#94A3B8")
            self.btn_real.label.set_fontweight("normal")
            self.btn_test.color = "#D97706"
            self.btn_test.label.set_color("#FFFFFF")
            self.btn_test.label.set_fontweight("bold")
            self.set_speed(10)

        self.fig.canvas.draw_idle()

    def _on_key_press(self, event):
        if event.key == " ":
            self.toggle_play_pause()
        elif event.key == "r":
            self.on_reset_clicked()
        elif event.key == "m":
            self.set_mode("synthetic" if self.mode == "real" else "real")
        elif event.key == "q":
            plt.close(self.fig)

    # =========================================================================
    # ANIMATION & FRAME RENDER
    # =========================================================================

    def update_frame(self, frame):
        """Update 3D positions, trail geometries, telemetry text, and proximity status."""
        if not self.is_paused:
            metrics = self.step()
        else:
            metrics = self.current_metrics

        if metrics is None:
            return []

        pos_a = metrics["pos_a"]
        pos_b = metrics["pos_b"]
        vel_a = metrics["vel_a"]
        vel_b = metrics["vel_b"]
        enc = metrics["encounter"]
        dist = enc["distance_km"]

        # 1. Update 3D Positions
        self.sat_point.set_data([pos_a[0]], [pos_a[1]])
        self.sat_point.set_3d_properties([pos_a[2]])

        self.sec_point.set_data([pos_b[0]], [pos_b[1]])
        self.sec_point.set_3d_properties([pos_b[2]])

        # 2. Update 3D Trails
        self.sat_trail_line.set_data(self.sat_trail_x, self.sat_trail_y)
        self.sat_trail_line.set_3d_properties(self.sat_trail_z)

        self.sec_trail_line.set_data(self.sec_trail_x, self.sec_trail_y)
        self.sec_trail_line.set_3d_properties(self.sec_trail_z)

        # 3. Update Labels
        self.sat_text.set_position((pos_a[0], pos_a[1]))
        self.sat_text.set_3d_properties(pos_a[2] + 400)
        self.sat_text.set_text(metrics["primary_name"].split()[0])

        self.sec_text.set_position((pos_b[0], pos_b[1]))
        self.sec_text.set_3d_properties(pos_b[2] + 400)
        self.sec_text.set_text(metrics["secondary_name"].split()[0])

        # 4. Conjunction Line between objects
        if dist < 3000.0:
            self.conjunction_line.set_data([pos_a[0], pos_b[0]], [pos_a[1], pos_b[1]])
            self.conjunction_line.set_3d_properties([pos_a[2], pos_b[2]])
            if dist <= CLOSE_APPROACH_KM:
                self.conjunction_line.set_color("#EF4444")
                self.conjunction_line.set_linewidth(2.4)
            elif dist <= SAFE_DISTANCE_KM:
                self.conjunction_line.set_color("#F59E0B")
                self.conjunction_line.set_linewidth(1.8)
            else:
                self.conjunction_line.set_color("#38BDF8")
                self.conjunction_line.set_linewidth(1.0)
        else:
            self.conjunction_line.set_data([], [])
            self.conjunction_line.set_3d_properties([])

        # 5. Format Live Dashboard Telemetry Text
        closing_state = "APPROACHING" if enc["closing_speed_km_s"] > 0 else "SEPARATING"

        hud_text = (
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f" SYSTEM MODE:  [{'REAL TRACKED DATA' if self.mode == 'real' else 'CONTROLLED SYNTHETIC TEST'}]\n"
            f" CLOCK:        {metrics['time_display']}\n"
            f" WARP SPEED:   {self.sim_speed}x {'[PAUSED]' if self.is_paused else '[ACTIVE]'}\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f" [PRIMARY OBJECT] {metrics['primary_name']}\n"
            f"  Altitude:     {metrics['alt_a']:>10.2f} km\n"
            f"  Velocity:     {metrics['spd_a']:>10.3f} km/s\n"
            f"  Pos (X,Y,Z):  [{pos_a[0]:>7.1f}, {pos_a[1]:>7.1f}, {pos_a[2]:>7.1f}] km\n"
            f"  Vel (Vx,Vy,Vz):[{vel_a[0]:>6.2f}, {vel_a[1]:>6.2f}, {vel_a[2]:>6.2f}] km/s\n"
            f"------------------------------------------------\n"
            f" [SECONDARY OBJECT] {metrics['secondary_name']}\n"
            f"  Altitude:     {metrics['alt_b']:>10.2f} km\n"
            f"  Velocity:     {metrics['spd_b']:>10.3f} km/s\n"
            f"  Pos (X,Y,Z):  [{pos_b[0]:>7.1f}, {pos_b[1]:>7.1f}, {pos_b[2]:>7.1f}] km\n"
            f"  Vel (Vx,Vy,Vz):[{vel_b[0]:>6.2f}, {vel_b[1]:>6.2f}, {vel_b[2]:>6.2f}] km/s\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f" [CONJUNCTION ANALYSIS — SHARED ENGINE]\n"
            f"  3D Separation:  {dist:>12.3f} km\n"
            f"  Relative Speed: {enc['relative_speed_km_s']:>12.4f} km/s\n"
            f"  Closing Speed:  {enc['closing_speed_km_s']:>12.4f} km/s ({closing_state})\n"
            f"  Approach Angle: {enc['approach_angle_deg']:>12.2f}°\n"
            f"------------------------------------------------\n"
            f" [CLOSEST APPROACH PARAMETERS]\n"
            f"  Observed CAD:   {self.cad_km:>12.3f} km\n"
            f"  Estimated TCA:  {self.tca_str}\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        )
        self.hud_content.set_text(hud_text)

        # 6. Status Badge Coloring
        status = enc["status"]
        level = enc["level"]
        if status == "CLOSE APPROACH":
            badge_color = "#DC2626"  # Red
            border_color = "#F87171"
        elif status == "MONITOR":
            badge_color = "#D97706"  # Amber
            border_color = "#FBBF24"
        else:
            badge_color = "#059669"  # Green
            border_color = "#34D399"

        self.hud_status_badge.set_text(f"  STATUS: {status}  [{level}]  ")
        self.hud_status_badge.set_bbox(dict(boxstyle="round,pad=0.5", facecolor=badge_color, edgecolor=border_color, linewidth=1.5))

        # 7. Persistent Close Approach Event Log (Task 4)
        if self.close_approach_detected and self.persisted_event_record:
            event_text = (
                f"[!] ENCOUNTER EVENT RECORDED & PERSISTED\n"
                f"Min Separation (CAD): {self.persisted_event_record['cad_km']:.2f} km | TCA: {self.persisted_event_record['tca']}\n"
                f"Alert Condition: HIGH PROXIMITY [CONJUNCTION LOGGED]"
            )
            self.hud_event_box.set_color("#FCA5A5")
        else:
            event_text = (
                f"Conjunction Assessment Normal\n"
                f"Thresholds: Safe > 100km | Monitor 10–100km | Close <= 10km"
            )
            self.hud_event_box.set_color("#94A3B8")
        self.hud_event_box.set_text(event_text)

        return [
            self.sat_point, self.sec_point,
            self.sat_trail_line, self.sec_trail_line,
            self.conjunction_line, self.sat_text, self.sec_text,
            self.hud_content, self.hud_status_badge, self.hud_event_box
        ]

    def run(self):
        """Start the interactive 3D visualization loop."""
        if self.headless:
            print("Visualizer initialized in headless mode.")
            return

        self.anim = FuncAnimation(
            self.fig,
            self.update_frame,
            interval=self.update_interval,
            blit=False,
            cache_frame_data=False
        )
        plt.show()


if __name__ == "__main__":
    mode_arg = "real"
    if len(sys.argv) > 1 and sys.argv[1].lower() in ["synthetic", "test"]:
        mode_arg = "synthetic"

    app = SatelliteVisualizer3D(mode=mode_arg)
    app.run()
