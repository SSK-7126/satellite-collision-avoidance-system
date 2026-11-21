
import numpy as np

from D2.dynamics.two_body import MU_EARTH
from D2.dynamics.orbit_propagator import propagate_orbit

# Initial circular orbit
radius = 7_000_000.0
velocity = np.sqrt(MU_EARTH / radius)

initial_state = np.array([
    radius, 0.0, 0.0,
    0.0, velocity, 0.0
])

# Simulation settings
duration = 600.0
dt = 1.0

times, states = propagate_orbit(
    initial_state, duration, dt
)

initial_radius = np.linalg.norm(initial_state[:3])
final_radius = np.linalg.norm(states[-1, :3])

print("Simulation duration:", times[-1], "seconds")
print("Number of states:", len(states))
print("Initial radius:", initial_radius, "m")
print("Final radius:", final_radius, "m")
print("Final position:", states[-1, :3])
print("Final velocity:", states[-1, 3:])

assert states.shape == (601, 6)
assert np.all(np.isfinite(states))
assert abs(final_radius - initial_radius) < 1.0

print("\nORBIT PROPAGATION TEST PASSED")
