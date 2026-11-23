"""
backend/catalogue/parsers.py
============================
Parsers for Space-Track / CelesTrak orbital records:
- Two-Line Element Set (TLE) / Three-Line Element Set (3LE)
- CCSDS Orbit Mean-Elements Message (OMM) JSON & CSV

Enforces rigorous checksum validation, physical bounds checks, and accurate epoch parsing.
"""

import math
import re
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List, Optional, Tuple, Union

from .models import CatalogueObject, OrbitalElements, RecordFormat, CatalogueSource

# Gravitational parameter of Earth in km^3 / s^2 (WGS-84 / EGM96 standard)
MU_EARTH_KM = 398600.4418
EARTH_RADIUS_KM = 6378.137


def compute_tle_checksum(line: str) -> int:
    """
    Compute standard NORAD TLE modulo-10 checksum for a 69-character line.
    Numbers add their value; '-' adds 1; all other characters add 0.
    """
    clean_line = line.rstrip("\r\n")
    # Take first 68 characters (69th is the checksum digit itself)
    check_chars = clean_line[:68]
    checksum = 0
    for ch in check_chars:
        if ch.isdigit():
            checksum += int(ch)
        elif ch == "-":
            checksum += 1
    return checksum % 10


def parse_tle_exponential(val_str: str) -> float:
    """
    Parse TLE compact exponential format, e.g. ' 12345-4' -> 0.12345e-4, '-12345-4' -> -0.12345e-4.
    """
    val_str = val_str.strip()
    if not val_str or val_str == "0" or val_str == "+0" or val_str == "-0":
        return 0.0

    sign = 1.0
    if val_str.startswith("-"):
        sign = -1.0
        val_str = val_str[1:]
    elif val_str.startswith("+"):
        val_str = val_str[1:]

    # Match mantissa and exponent
    match = re.match(r"^(\d+)([+-]\d+)$", val_str)
    if match:
        mantissa_str, exp_str = match.groups()
        mantissa = float("0." + mantissa_str)
        exp = int(exp_str)
        return sign * mantissa * (10 ** exp)

    try:
        return sign * float(val_str)
    except ValueError:
        return 0.0


def parse_tle_epoch(epoch_str: str) -> datetime:
    """
    Parse TLE 14-character epoch string: YYDDD.DDDDDDDD.
    Years 57-99 map to 1957-1999; 00-56 map to 2000-2056.
    """
    epoch_str = epoch_str.strip()
    year_digits = int(epoch_str[:2])
    day_fraction = float(epoch_str[2:])

    full_year = 1900 + year_digits if year_digits >= 57 else 2000 + year_digits
    base_date = datetime(full_year, 1, 1, 0, 0, 0, tzinfo=timezone.utc)
    epoch_dt = base_date + timedelta(days=day_fraction - 1.0)
    return epoch_dt


def parse_tle(
    line1: str,
    line2: str,
    line0: Optional[str] = None,
    source: str = CatalogueSource.CELESTRAK_GP.value,
    retrieval_time_utc: Optional[str] = None
) -> CatalogueObject:
    """
    Parse a standard 2-line or 3-line TLE record into a CatalogueObject.
    """
    line1 = line1.strip()
    line2 = line2.strip()

    if len(line1) < 68 or len(line2) < 68:
        raise ValueError(f"TLE lines too short. Line 1 length: {len(line1)}, Line 2 length: {len(line2)}")

    if not line1.startswith("1 "):
        raise ValueError(f"Invalid TLE Line 1 prefix: '{line1[:2]}', expected '1 '")
    if not line2.startswith("2 "):
        raise ValueError(f"Invalid TLE Line 2 prefix: '{line2[:2]}', expected '2 '")

    # Checksum validation
    cs1_calc = compute_tle_checksum(line1)
    cs2_calc = compute_tle_checksum(line2)
    cs1_given = int(line1[68]) if len(line1) >= 69 and line1[68].isdigit() else cs1_calc
    cs2_given = int(line2[68]) if len(line2) >= 69 and line2[68].isdigit() else cs2_calc

    if cs1_calc != cs1_given:
        raise ValueError(f"TLE Line 1 checksum mismatch: calculated {cs1_calc}, given {cs1_given}")
    if cs2_calc != cs2_given:
        raise ValueError(f"TLE Line 2 checksum mismatch: calculated {cs2_calc}, given {cs2_given}")

    # Extract fields from Line 1
    norad_id = line1[2:7].strip()
    classification = line1[7].strip() or "U"
    intl_desig = line1[9:17].strip()
    epoch_str = line1[18:32].strip()
    bstar = parse_tle_exponential(line1[53:61])

    # Extract fields from Line 2
    norad_id2 = line2[2:7].strip()
    if norad_id != norad_id2:
        raise ValueError(f"NORAD ID mismatch between Line 1 ({norad_id}) and Line 2 ({norad_id2})")

    inc_deg = float(line2[8:16])
    raan_deg = float(line2[17:25])
    ecc = float("0." + line2[26:33].strip())
    arg_p_deg = float(line2[34:42])
    mean_anom_deg = float(line2[43:51])
    mean_motion_rev_day = float(line2[52:63])

    epoch_dt = parse_tle_epoch(epoch_str)
    epoch_utc_iso = epoch_dt.isoformat()

    # Derived orbital quantities
    # n in rad/s: n = mean_motion * 2*pi / 86400
    n_rad_per_s = mean_motion_rev_day * (2.0 * math.pi) / 86400.0
    if n_rad_per_s <= 0.0:
        raise ValueError(f"Non-positive mean motion: {mean_motion_rev_day}")

    # Semi-major axis from Kepler's third law: a = (mu / n^2)^(1/3)
    sma_km = (MU_EARTH_KM / (n_rad_per_s ** 2)) ** (1.0 / 3.0)
    periapsis_km = sma_km * (1.0 - ecc)
    apoapsis_km = sma_km * (1.0 + ecc)
    period_minutes = (2.0 * math.pi / n_rad_per_s) / 60.0

    name = line0.strip() if line0 else f"OBJECT {norad_id}"
    if name.startswith("0 "):
        name = name[2:].strip()

    elements = OrbitalElements(
        semi_major_axis_km=round(sma_km, 4),
        eccentricity=round(ecc, 7),
        inclination_deg=round(inc_deg, 4),
        raan_deg=round(raan_deg, 4),
        arg_perigee_deg=round(arg_p_deg, 4),
        mean_anomaly_deg=round(mean_anom_deg, 4),
        mean_motion_rev_per_day=round(mean_motion_rev_day, 8),
        bstar=bstar,
        epoch_utc=epoch_utc_iso,
        period_minutes=round(period_minutes, 2),
        apoapsis_km=round(apoapsis_km, 2),
        periapsis_km=round(periapsis_km, 2),
    )

    retrieval_iso = retrieval_time_utc or datetime.now(timezone.utc).isoformat()
    raw_str = f"{name}\n{line1}\n{line2}" if line0 else f"{line1}\n{line2}"
    record_fmt = RecordFormat.TLE_3LINE.value if line0 else RecordFormat.TLE_2LINE.value

    # Infer object type from name heuristics
    obj_type = "UNKNOWN"
    name_upper = name.upper()
    if "DEB" in name_upper or "DEBRIS" in name_upper:
        obj_type = "DEBRIS"
    elif "R/B" in name_upper or "ROCKET" in name_upper:
        obj_type = "ROCKET BODY"
    elif any(kw in name_upper for kw in ["SAT", "STARLINK", "ISS", "TIANGONG", "CARTOSAT", "GPS", "GALILEO"]):
        obj_type = "PAYLOAD"

    return CatalogueObject(
        object_id=norad_id,
        name=name,
        international_designator=intl_desig,
        object_type=obj_type,
        source=source,
        format=record_fmt,
        epoch_utc=epoch_utc_iso,
        retrieval_time_utc=retrieval_iso,
        raw_record=raw_str,
        elements=elements,
        is_tracked=False,
        group=None,
        provenance={"parsed_from": "TLE", "bstar": bstar, "classification": classification},
    )


def parse_omm_json(
    json_data: Union[dict, str],
    source: str = CatalogueSource.CELESTRAK_GP.value,
    retrieval_time_utc: Optional[str] = None
) -> List[CatalogueObject]:
    """
    Parse CCSDS OMM JSON array or single object into CatalogueObject list.
    """
    import json
    if isinstance(json_data, str):
        records = json.loads(json_data)
    else:
        records = json_data

    if isinstance(records, dict):
        records = [records]

    now_iso = retrieval_time_utc or datetime.now(timezone.utc).isoformat()
    results = []

    for rec in records:
        norad_id = str(rec.get("NORAD_CAT_ID") or rec.get("OBJECT_ID", ""))
        name = rec.get("OBJECT_NAME", f"OBJECT {norad_id}")
        epoch_str = rec.get("EPOCH", "")

        # Try to parse ISO epoch
        try:
            # e.g. "2026-11-20T12:00:00.000000"
            if epoch_str.endswith("Z"):
                epoch_str = epoch_str[:-1] + "+00:00"
            epoch_dt = datetime.fromisoformat(epoch_str)
            if epoch_dt.tzinfo is None:
                epoch_dt = epoch_dt.replace(tzinfo=timezone.utc)
            epoch_iso = epoch_dt.isoformat()
        except Exception:
            epoch_iso = epoch_str

        mean_motion = float(rec.get("MEAN_MOTION", 0.0))
        ecc = float(rec.get("ECCENTRICITY", 0.0))
        inc_deg = float(rec.get("INCLINATION", 0.0))
        raan_deg = float(rec.get("RA_OF_ASC_NODE", 0.0))
        arg_p_deg = float(rec.get("ARG_OF_PERICENTER", 0.0))
        mean_anom_deg = float(rec.get("MEAN_ANOMALY", 0.0))
        bstar = float(rec.get("BSTAR", 0.0))

        if mean_motion <= 0.0:
            continue

        n_rad_per_s = mean_motion * (2.0 * math.pi) / 86400.0
        sma_km = (MU_EARTH_KM / (n_rad_per_s ** 2)) ** (1.0 / 3.0)
        periapsis_km = sma_km * (1.0 - ecc)
        apoapsis_km = sma_km * (1.0 + ecc)
        period_minutes = (2.0 * math.pi / n_rad_per_s) / 60.0

        elements = OrbitalElements(
            semi_major_axis_km=round(sma_km, 4),
            eccentricity=round(ecc, 7),
            inclination_deg=round(inc_deg, 4),
            raan_deg=round(raan_deg, 4),
            arg_perigee_deg=round(arg_p_deg, 4),
            mean_anomaly_deg=round(mean_anom_deg, 4),
            mean_motion_rev_per_day=round(mean_motion, 8),
            bstar=bstar,
            epoch_utc=epoch_iso,
            period_minutes=round(period_minutes, 2),
            apoapsis_km=round(apoapsis_km, 2),
            periapsis_km=round(periapsis_km, 2),
        )

        obj_type = rec.get("OBJECT_TYPE", "UNKNOWN").upper()
        if obj_type not in ["PAYLOAD", "ROCKET BODY", "DEBRIS", "UNKNOWN"]:
            obj_type = "UNKNOWN"

        results.append(
            CatalogueObject(
                object_id=norad_id,
                name=name,
                international_designator=rec.get("INTLDES"),
                object_type=obj_type,
                source=source,
                format=RecordFormat.OMM_JSON.value,
                epoch_utc=epoch_iso,
                retrieval_time_utc=now_iso,
                raw_record=rec,
                elements=elements,
                is_tracked=False,
                group=rec.get("GROUP"),
                provenance={"omm_center": rec.get("CENTER_NAME"), "ref_frame": rec.get("REF_FRAME")},
            )
        )

    return results


def parse_omm_csv(
    csv_text: str,
    source: str = CatalogueSource.CELESTRAK_GP.value,
    retrieval_time_utc: Optional[str] = None
) -> List[CatalogueObject]:
    """
    Parse CCSDS OMM CSV formatted text into CatalogueObject list.
    """
    import csv
    import io

    reader = csv.DictReader(io.StringIO(csv_text.strip()))
    now_iso = retrieval_time_utc or datetime.now(timezone.utc).isoformat()
    results = []

    for row in reader:
        norad_id = str(row.get("NORAD_CAT_ID", "")).strip()
        if not norad_id:
            continue

        name = row.get("OBJECT_NAME", f"OBJECT {norad_id}").strip()
        epoch_str = row.get("EPOCH", "").strip()

        try:
            mean_motion = float(row.get("MEAN_MOTION", 0.0))
            ecc = float(row.get("ECCENTRICITY", 0.0))
            inc_deg = float(row.get("INCLINATION", 0.0))
            raan_deg = float(row.get("RA_OF_ASC_NODE", 0.0))
            arg_p_deg = float(row.get("ARG_OF_PERICENTER", 0.0))
            mean_anom_deg = float(row.get("MEAN_ANOMALY", 0.0))
            bstar = float(row.get("BSTAR", 0.0))
        except (ValueError, TypeError):
            continue

        if mean_motion <= 0.0:
            continue

        n_rad_per_s = mean_motion * (2.0 * math.pi) / 86400.0
        sma_km = (MU_EARTH_KM / (n_rad_per_s ** 2)) ** (1.0 / 3.0)
        periapsis_km = sma_km * (1.0 - ecc)
        apoapsis_km = sma_km * (1.0 + ecc)
        period_minutes = (2.0 * math.pi / n_rad_per_s) / 60.0

        elements = OrbitalElements(
            semi_major_axis_km=round(sma_km, 4),
            eccentricity=round(ecc, 7),
            inclination_deg=round(inc_deg, 4),
            raan_deg=round(raan_deg, 4),
            arg_perigee_deg=round(arg_p_deg, 4),
            mean_anomaly_deg=round(mean_anom_deg, 4),
            mean_motion_rev_per_day=round(mean_motion, 8),
            bstar=bstar,
            epoch_utc=epoch_str,
            period_minutes=round(period_minutes, 2),
            apoapsis_km=round(apoapsis_km, 2),
            periapsis_km=round(periapsis_km, 2),
        )

        results.append(
            CatalogueObject(
                object_id=norad_id,
                name=name,
                international_designator=row.get("INTLDES"),
                object_type=row.get("OBJECT_TYPE", "UNKNOWN").upper(),
                source=source,
                format=RecordFormat.OMM_CSV.value,
                epoch_utc=epoch_str,
                retrieval_time_utc=now_iso,
                raw_record=dict(row),
                elements=elements,
                is_tracked=False,
                group=row.get("GROUP"),
                provenance={"csv_source": source},
            )
        )

    return results
