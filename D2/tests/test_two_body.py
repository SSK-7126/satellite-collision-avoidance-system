
import numpy as np
from D2.dynamics.two_body import gravitational_acceleration

position = np.array([7000000.0, 0.0, 0.0])

acceleration = gravitational_acceleration(position)

print("Position:", position)
print("Gravitational acceleration:", acceleration)
print("Acceleration magnitude:", np.linalg.norm(acceleration))

assert acceleration[0] < 0
assert np.isclose(acceleration[1], 0)
assert np.isclose(acceleration[2], 0)

print("TEST PASSED")
