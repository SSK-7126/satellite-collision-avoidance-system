"""
backend/propagation/multi_object_manager.py
===========================================
Multi-object propagation coordinator.
Propagates a collection of tracked satellites/debris across common time grids
using asynchronous worker jobs, caching, and per-object health metrics.
Keeps compute off the Unreal render thread.
"""

import time
import logging
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List, Optional, Tuple, Set
from dataclasses import dataclass, field
import numpy as np

from .sgp4_engine import SGP4Propagator, PropagatedState
from backend.catalogue.models import CatalogueObject

logger = logging.getLogger(__name__)


@dataclass
class TrajectorySample:
    time_offset_sec: float
    epoch_utc: str
    r_j2000_m: List[float]
    v_j2000_mps: List[float]
    r_unreal_uu: List[float]


@dataclass
class PropagationJobResult:
    object_id: str
    name: str
    samples_count: int
    is_success: bool
    error_message: Optional[str] = None
    trajectories: List[TrajectorySample] = field(default_factory=list)
    last_propagated_utc: str = ""
    compute_time_ms: float = 0.0


class MultiObjectPropagator:
    """
    Coordinates multi-object propagation across a shared simulation timeline.
    """
    def __init__(self, cache_ttl_seconds: int = 1800):
        self.cache_ttl_seconds = cache_ttl_seconds
        self._propagators: Dict[str, SGP4Propagator] = {}
        self._cache: Dict[str, Tuple[float, PropagationJobResult]] = {}
        self._object_health: Dict[str, Dict[str, Any]] = {}

    def register_object(self, obj: CatalogueObject) -> bool:
        """
        Instantiate and register an SGP4 propagator for a catalogue object.
        """
        oid = str(obj.object_id)
        if obj.raw_record and isinstance(obj.raw_record, str):
            lines = [l.strip() for l in obj.raw_record.splitlines() if l.strip()]
            l1, l2 = None, None
            for idx in range(len(lines)):
                if lines[idx].startswith("1 ") and idx + 1 < len(lines) and lines[idx + 1].startswith("2 "):
                    l1 = lines[idx]
                    l2 = lines[idx + 1]
                    break
            if l1 and l2:
                try:
                    self._propagators[oid] = SGP4Propagator(oid, l1, l2)
                    self._object_health[oid] = {
                        "registered_utc": datetime.now(timezone.utc).isoformat(),
                        "status": "READY",
                        "error": None,
                    }
                    return True
                except Exception as e:
                    self._object_health[oid] = {
                        "registered_utc": datetime.now(timezone.utc).isoformat(),
                        "status": "INIT_ERROR",
                        "error": str(e),
                    }
                    return False
        return False

    def propagate_grid(
        self,
        object_id: str,
        name: str,
        start_epoch: datetime,
        duration_sec: float = 1000.0,
        dt_sec: float = 10.0,
        scale: float = 0.01,
        cancel_token: Optional[dict] = None
    ) -> PropagationJobResult:
        """
        Propagate object over a discrete time grid [start_epoch, start_epoch + duration].
        """
        t_start = time.perf_counter()
        oid = str(object_id)
        cache_key = f"{oid}_{start_epoch.isoformat()}_{duration_sec}_{dt_sec}_{scale}"

        # Check in-memory cache
        now_ts = time.time()
        if cache_key in self._cache:
            ts, res = self._cache[cache_key]
            if now_ts - ts < self.cache_ttl_seconds:
                return res

        propagator = self._propagators.get(oid)
        if not propagator:
            return PropagationJobResult(
                object_id=oid,
                name=name,
                samples_count=0,
                is_success=False,
                error_message="Propagator not registered for object",
                last_propagated_utc=datetime.now(timezone.utc).isoformat(),
            )

        num_steps = int(duration_sec / dt_sec) + 1
        samples: List[TrajectorySample] = []
        is_success = True
        err_msg = None

        for step in range(num_steps):
            if cancel_token and cancel_token.get("cancelled", False):
                return PropagationJobResult(
                    object_id=oid,
                    name=name,
                    samples_count=len(samples),
                    is_success=False,
                    error_message="Propagation cancelled by caller",
                    last_propagated_utc=datetime.now(timezone.utc).isoformat(),
                )

            offset = step * dt_sec
            cur_dt = start_epoch + timedelta(seconds=offset)
            state = propagator.propagate_to_datetime(cur_dt, scale=scale)

            if not state.is_valid:
                is_success = False
                err_msg = state.error_message
                break

            samples.append(
                TrajectorySample(
                    time_offset_sec=offset,
                    epoch_utc=cur_dt.isoformat(),
                    r_j2000_m=state.r_j2000_m,
                    v_j2000_mps=state.v_j2000_mps,
                    r_unreal_uu=state.r_unreal_uu,
                )
            )

        compute_ms = (time.perf_counter() - t_start) * 1000.0
        now_iso = datetime.now(timezone.utc).isoformat()

        job_result = PropagationJobResult(
            object_id=oid,
            name=name,
            samples_count=len(samples),
            is_success=is_success,
            error_message=err_msg,
            trajectories=samples,
            last_propagated_utc=now_iso,
            compute_time_ms=compute_ms,
        )

        # Update health tracking
        self._object_health[oid] = {
            "status": "HEALTHY" if is_success else "DEGRADED",
            "last_propagated_utc": now_iso,
            "error": err_msg,
            "samples": len(samples),
            "compute_ms": compute_ms,
        }

        if is_success:
            self._cache[cache_key] = (now_ts, job_result)

        return job_result

    def propagate_all_tracked(
        self,
        objects: List[CatalogueObject],
        start_epoch: datetime,
        duration_sec: float = 1000.0,
        dt_sec: float = 10.0,
        scale: float = 0.01
    ) -> Dict[str, PropagationJobResult]:
        """
        Batch propagate a list of space objects.
        """
        results = {}
        for obj in objects:
            if str(obj.object_id) not in self._propagators:
                self.register_object(obj)
            res = self.propagate_grid(
                object_id=obj.object_id,
                name=obj.name,
                start_epoch=start_epoch,
                duration_sec=duration_sec,
                dt_sec=dt_sec,
                scale=scale,
            )
            results[str(obj.object_id)] = res
        return results

    def get_object_health(self, object_id: str) -> Optional[Dict[str, Any]]:
        """Return health and error record for object."""
        return self._object_health.get(str(object_id))
