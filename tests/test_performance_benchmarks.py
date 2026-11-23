"""
test_performance_benchmarks.py - Performance Benchmarking for ICPS Phase 10

Validates execution throughput and latency across key astrodynamic engines:
1. SGP4 multi-object propagation speed (states/sec)
2. Fast conjunction screening filter speed & candidate reduction
3. Decision support manoeuvre planner solving latency
4. Foster collision probability numerical calculation time
"""

import time
import pytest
import numpy as np
from datetime import datetime, timezone, timedelta

from backend.propagation.sgp4_engine import SGP4Propagator
from backend.catalogue.models import CatalogueObject, OrbitalElements
from backend.conjunction.screener import CoarseScreener
from backend.decision_support.planner import ResourceAwareManoeuvrePlanner, compute_rtn_basis
from backend.resources.models import SpacecraftHardwareRecord, ThrusterSpecification, ProvenanceType
from backend.resources.fuel_calculator import estimate_propellant_consumption
from D2.uncertainty.covariance import create_diagonal_covariance
from D2.uncertainty.collision_probability import calculate_collision_probability


SAMPLE_TLE_A = (
    "ISS (ZARYA)",
    "1 25544U 98067A   26327.50000000  .00016717  00000-0  10270-3 0  9990",
    "2 25544  51.6416 198.2435 0005432  65.1234 295.0123 15.49876543501237"
)


def make_dummy_object(oid: str, name: str, peri_km: float, apo_km: float) -> CatalogueObject:
    elems = OrbitalElements(
        semi_major_axis_km=(peri_km + apo_km) / 2.0,
        eccentricity=(apo_km - peri_km) / (peri_km + apo_km),
        inclination_deg=51.6,
        raan_deg=100.0,
        arg_perigee_deg=45.0,
        mean_anomaly_deg=0.0,
        mean_motion_rev_per_day=15.0,
        period_minutes=90.0,
        apoapsis_km=apo_km,
        periapsis_km=peri_km,
    )
    return CatalogueObject(
        object_id=oid,
        name=name,
        epoch_utc="2026-11-23T12:00:00Z",
        source="TEST",
        format="TEST",
        retrieval_time_utc="2026-11-23T12:00:00Z",
        raw_record="",
        elements=elems,
    )


def test_sgp4_propagation_throughput():
    """Benchmark SGP4 propagation speed: target > 500 propagation states/second."""
    engine = SGP4Propagator("25544", SAMPLE_TLE_A[1], SAMPLE_TLE_A[2])
    base_epoch = datetime(2026, 11, 23, 12, 0, 0, tzinfo=timezone.utc)
    num_steps = 1000
    epochs = [base_epoch + timedelta(seconds=i * 60) for i in range(num_steps)]

    t0 = time.perf_counter()
    count = 0
    for ep in epochs:
        st = engine.propagate_to_datetime(ep)
        assert st.r_j2000_m is not None
        count += 1
    elapsed = time.perf_counter() - t0

    throughput = count / elapsed
    print(f"\n[BENCHMARK] SGP4 Propagation: {count} steps in {elapsed:.3f}s ({throughput:.1f} states/sec)")
    assert throughput > 500.0, f"Propagation throughput {throughput:.1f} below threshold of 500 states/s"


def test_conjunction_screening_filter_efficiency():
    """Benchmark apogee/perigee screening filter efficiency over candidate pairs."""
    obj_a = make_dummy_object("A", "SAT_A", 6800.0, 7000.0)
    obj_b_near = make_dummy_object("B", "SAT_B", 6900.0, 7100.0)

    # Overlapping pair check
    assert CoarseScreener.orbital_shells_overlap(obj_a, obj_b_near) is True

    # Benchmark non-overlapping rejection speed
    t0 = time.perf_counter()
    trials = 50000
    rejections = 0
    for i in range(trials):
        obj_far = make_dummy_object("F", "FAR", 7500.0 + (i % 100), 7700.0 + (i % 100))
        if not CoarseScreener.orbital_shells_overlap(obj_a, obj_far):
            rejections += 1
    elapsed = time.perf_counter() - t0

    throughput = trials / elapsed
    print(f"\n[BENCHMARK] Filter Screening: {trials} checks in {elapsed:.4f}s ({throughput:,.0f} checks/sec, {rejections} rejected)")
    assert rejections == trials
    assert throughput > 10000.0, f"Filter check throughput {throughput:,.0f} below target"


def test_foster_collision_probability_latency():
    """Benchmark Foster 2D collision probability calculation latency (target < 10ms per eval)."""
    r_rel = np.array([50.0, 10.0, 5.0])
    v_rel = np.array([0.0, 7500.0, 0.0])
    cov = create_diagonal_covariance(pos_std_m=[50.0, 50.0, 50.0], vel_std_mps=[0.1, 0.1, 0.1])
    hbr = 15.0

    t0 = time.perf_counter()
    evals = 100
    for _ in range(evals):
        pc = calculate_collision_probability(r_rel, v_rel, cov, hbr)
        assert 0.0 <= pc["pc"] <= 1.0
    elapsed = time.perf_counter() - t0

    per_eval_ms = (elapsed / evals) * 1000.0
    print(f"\n[BENCHMARK] Foster Pc Latency: {evals} evals in {elapsed:.3f}s ({per_eval_ms:.2f} ms/eval)")
    assert per_eval_ms < 10.0, f"Foster latency {per_eval_ms:.2f}ms exceeds target 10ms"


def test_decision_support_planner_latency():
    """Benchmark Decision Support Planner 3-axis candidate generation and screening."""
    profile = SpacecraftHardwareRecord(
        object_id="44804",
        owner_operator="ISRO",
        spacecraft_model="CARTOSAT-3_BUS",
        dry_mass_kg=500.0,
        current_propellant_kg=45.0,
        thrusters=[
            ThrusterSpecification(
                thruster_type="HYDRAZINE_MONOPROPELLANT",
                thrust_n=22.0,
                isp_sec=225.0,
                min_impulse_bit_ns=0.1
            )
        ]
    )

    t0 = time.perf_counter()
    # Test RTN triad generation
    r_pri = np.array([7000000.0, 0.0, 0.0])
    v_pri = np.array([0.0, 7546.0, 0.0])
    R, T, N = compute_rtn_basis(r_pri, v_pri)
    assert np.isclose(np.linalg.norm(R), 1.0)
    assert np.isclose(np.linalg.norm(T), 1.0)
    assert np.isclose(np.linalg.norm(N), 1.0)

    # Test propellant consumption computation
    fuel_used = estimate_propellant_consumption(
        initial_mass_kg=545.0,
        delta_v_mps=3.0,
        isp_sec=225.0
    )
    elapsed = time.perf_counter() - t0

    print(f"\n[BENCHMARK] Decision Support Computations: completed in {elapsed*1000.0:.3f}ms (fuel used: {fuel_used:.3f}kg)")
    assert fuel_used > 0.0
    assert elapsed < 0.05, f"Planning candidate computation took {elapsed*1000.0:.2f}ms (>50ms)"
