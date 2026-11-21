
import numpy as np
import matplotlib.pyplot as plt

from D2.dynamics.two_body import MU_EARTH
from D2.dynamics.orbit_propagator import propagate_orbit


def visualize_orbit():
    # Initial circular orbit
    radius = 7_000_000.0
    velocity = np.sqrt(MU_EARTH / radius)

    initial_state = np.array([
        radius, 0.0, 0.0,
        0.0, velocity, 0.0
    ])

    # Propagate for one orbital period
    period = 2 * np.pi * np.sqrt(radius**3 / MU_EARTH)

    times, states = propagate_orbit(
        initial_state,
        duration=period,
        dt=10.0
    )

    x = states[:, 0] / 1000
    y = states[:, 1] / 1000
    z = states[:, 2] / 1000

    # Create Earth sphere
    earth_radius = 6371
    u = np.linspace(0, 2 * np.pi, 50)
    v = np.linspace(0, np.pi, 50)

    earth_x = earth_radius * np.outer(np.cos(u), np.sin(v))
    earth_y = earth_radius * np.outer(np.sin(u), np.sin(v))
    earth_z = earth_radius * np.outer(np.ones_like(u), np.cos(v))

    fig = plt.figure(figsize=(10, 8))
    ax = fig.add_subplot(111, projection="3d")

    ax.plot_surface(
        earth_x, earth_y, earth_z,
        alpha=0.4
    )

    ax.plot(x, y, z, label="Satellite Orbit", linewidth=2)

    ax.scatter(x[0], y[0], z[0], label="Initial Position")
    ax.scatter(x[-1], y[-1], z[-1], label="Final Position")

    ax.set_xlabel("X (km)")
    ax.set_ylabel("Y (km)")
    ax.set_zlabel("Z (km)")

    ax.set_title("Satellite Two-Body Orbital Simulation")
    ax.legend()

    ax.set_box_aspect((1, 1, 1))

    plt.tight_layout()
    plt.show()


if __name__ == "__main__":
    visualize_orbit()
