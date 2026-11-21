
import numpy as np

from D2.dynamics.rk4 import rk4_step
from D2.dynamics.two_body import MU_EARTH

# Initial circular orbit
radius = 7_000_000.0

velocity = np.sqrt(MU_EARTH / radius)

initial_state = np.array([
    radius, 0.0, 0.0,
    0.0, velocity, 0.0
])

# Integrate for 10 seconds
dt = 10.0

new_state = rk4_step(initial_state, dt)

print("Initial state:")
print(initial_state)

print("\nUpdated state:")
print(new_state)

print("\nNew orbital radius:")
print(np.linalg.norm(new_state[:3]))

assert new_state.shape == (6,)
assert np.all(np.isfinite(new_state))
assert not np.allclose(initial_state, new_state)

print("\nRK4 TEST PASSED")
