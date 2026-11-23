"""
backend/propagation/sgp4_engine.py
==================================
SGP4 propagator engine wrapping official 'sgp4' Python library.
Propagates individual satellites to designated epoch with full error tracking,
unit conversions, and frame transformations.
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Dict, Any, Optional, Tuple, List
import numpy as np

try:
    from sgp4.api import Satrec, WGS72, jday
except ImportError:
    # Safe stub if sgp4 not present
    Satrec = None
    WGS72 = None
    jday = None

from .frames import julian_date, teme_to_j2000, j2000_to_unreal, DEFAULT_RENDER_SCALE


# SGP4 error code descriptions
SGP4_ERROR_MESSAGES = {
    0: "OK",
    1: "Mean elements eccentriciy < 0 or >= 1 or semi-major axis < 0",
    2: "Mean motion < 0 rev/day",
    3: "Perturbed eccentricity < 0 or >= 1",
    4: "Semi-latus rectum < 0",
    5: "Epoch elements are sub-orbital",
    6: "Satellite has decayed / penetrated dense atmosphere",
}


@dataclass
class PropagatedState:
    """
    State vector at a discrete epoch in TEME, ECI J2000, and Unreal coordinates.
    """
    object_id: str
    epoch_utc: str
    error_code: int = 0
    error_message: str = "OK"

    # Native SGP4 output (km, km/s)
    r_teme_km: Optional[List[float]] = None
    v_teme_km_s: Optional[List[float]] = None

    # Authoritative SI ECI J2000 (metres, m/s)
    r_j2000_m: Optional[List[float]] = None
    v_j2000_mps: Optional[List[float]] = None

    # Unreal Engine Display (Unreal Units, uu/s)
    r_unreal_uu: Optional[List[float]] = None
    v_unreal_uups: Optional[List[float]] = None

    latency_ms: float = 0.0

    @property
    def is_valid(self) -> bool:
        return self.error_code == 0 and self.r_j2000_m is not None


class SGP4Propagator:
    """
    Encapsulates SGP4 propagation for a single satellite.
    """
    def __init__(self, object_id: str, line1: str, line2: str):
        if Satrec is None:
            raise RuntimeError("The 'sgp4' package is required but not installed.")

        self.object_id = str(object_id)
        self.line1 = line1.strip()
        self.line2 = line2.strip()

        # Initialize native SGP4 satellite record
        self.satrec = Satrec.twoline2rv(self.line1, self.line2, WGS72)
        self.satnum = self.satrec.satnum

    def propagate_to_datetime(
        self,
        dt: datetime,
        scale: float = DEFAULT_RENDER_SCALE
    ) -> PropagatedState:
        """
        Propagate to an exact datetime in UTC.
        """
        import time
        t_start = time.perf_counter()

        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        else:
            dt = dt.astimezone(timezone.utc)

        jd, fr = julian_date(dt)
        err_code, r_teme, v_teme = self.satrec.sgp4(jd, fr)

        latency = (time.perf_counter() - t_start) * 1000.0

        if err_code != 0:
            msg = SGP4_ERROR_MESSAGES.get(err_code, f"SGP4 error code {err_code}")
            return PropagatedState(
                object_id=self.object_id,
                epoch_utc=dt.isoformat(),
                error_code=err_code,
                error_message=msg,
                latency_ms=latency,
            )

        r_teme_arr = np.array(r_teme, dtype=np.float64)
        v_teme_arr = np.array(v_teme, dtype=np.float64)

        # 1. Transform TEME (km, km/s) -> ECI J2000 (m, m/s)
        r_j2k_m, v_j2k_mps = teme_to_j2000(r_teme_arr, v_teme_arr, dt)

        # 2. Transform ECI J2000 (m, m/s) -> Unreal Display Coordinates (uu, uu/s)
        r_ue, v_ue = j2000_to_unreal(r_j2k_m, v_j2k_mps, scale=scale)

        return PropagatedState(
            object_id=self.object_id,
            epoch_utc=dt.isoformat(),
            error_code=0,
            error_message="OK",
            r_teme_km=r_teme_arr.tolist(),
            v_teme_km_s=v_teme_arr.tolist(),
            r_j2000_m=r_j2k_m.tolist(),
            v_j2000_mps=v_j2k_mps.tolist(),
            r_unreal_uu=r_ue.tolist(),
            v_unreal_uups=v_ue.tolist(),
            latency_ms=latency,
        )
