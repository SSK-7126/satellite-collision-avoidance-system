"""
D2/tests/test_rk4.py
====================
Verification test suite for D2 RK4 numerical integration.
Follows Section 3.2 and Section 12.1 of the Technical Guide:
- RK4 state step evaluation and finite value check
- O(h^4) global error scaling under step-size reduction
"""

import numpy as np
import pytest

from D2.dynamics.rk4 import rk4_step, verify_rk4_convergence
from D2.dynamics.two_body import MU_EARTH


def test_rk4_step_basic():
    """Verify single RK4 step in circular LEO."""
    radius = 7_000_000.0
    velocity = np.sqrt(MU_EARTH / radius)
    initial_state = np.array([radius, 0.0, 0.0, 0.0, velocity, 0.0], dtype=np.float64)

    dt = 10.0
    new_state = rk4_step(initial_state, dt)

    assert new_state.shape == (6,)
    assert np.all(np.isfinite(new_state))
    assert not np.allclose(initial_state, new_state)


def test_rk4_convergence_scaling():
    """
    Verify numerical convergence of RK4 integrator by checking that successive
    differences scale with order p ~ 4 when halving step sizes. (Guide Section 3.2 & 12.1)
    """
    radius = 7_000_000.0
    velocity = np.sqrt(MU_EARTH / radius)
    initial_state = np.array([radius, 0.0, 0.0, 0.0, velocity, 0.0], dtype=np.float64)

    res = verify_rk4_convergence(
        initial_state=initial_state,
        duration=100.0,
        step_sizes=(8.0, 4.0, 2.0, 1.0, 0.5)
    )

    assert res["is_converging"], "RK4 must exhibit monotonic convergence under step-size refinement."
    assert len(res["observed_orders"]) >= 2
    # Mean observed convergence order should be close to 4.0 (3.5 <= p <= 4.5)
    assert 3.5 <= res["mean_observed_order"] <= 4.5, (
        f"Expected 4th-order convergence (3.5 <= p <= 4.5), got {res['mean_observed_order']:.2f}"
    )


if __name__ == "__main__":
    test_rk4_step_basic()
    test_rk4_convergence_scaling()
    print("ALL RK4 TESTS PASSED")
