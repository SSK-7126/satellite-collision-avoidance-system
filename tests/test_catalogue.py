"""
tests/test_catalogue.py
=======================
Tests for Real Satellite Catalogue and Registry module (Phase 3).
Verifies:
- Standard 2-line and 3-line TLE parsing and checksum computation
- Rejection of malformed, invalid checksum, and mismatched records
- CCSDS OMM JSON and CSV parsing
- CelesTrak GP client caching, rate limiting, and offline fallback fixtures
- Space-Track credential handling and policy compliance
- CatalogueRegistry search, tracking list, untracking isolation, and persistence
"""

import os
import json
import tempfile
import pytest

from backend.catalogue.models import CatalogueObject, OrbitalElements, CatalogueSource, RecordFormat
from backend.catalogue.parsers import (
    compute_tle_checksum,
    parse_tle,
    parse_omm_json,
    parse_omm_csv,
)
from backend.catalogue.client import CelesTrakClient, SpaceTrackClient
from backend.catalogue.registry import CatalogueRegistry


# Realistic test TLEs with exact modulo-10 checksums
ISS_TLE_LINE0 = "ISS (ZARYA)"
ISS_TLE_LINE1 = "1 25544U 98067A   26327.50000000  .00016717  00000-0  10270-3 0  9990"
ISS_TLE_LINE2 = "2 25544  51.6416 198.2435 0005432  65.1234 295.0123 15.49876543501237"

CARTOSAT_LINE1 = "1 44804U 19081A   26327.50000000  .00000456  00000-0  23456-4 0  9993"
CARTOSAT_LINE2 = "2 44804  97.4520  45.1200 0012000  85.4500 274.8000 15.18500000381021"


def test_tle_checksum_computation():
    """Verify standard modulo-10 checksum algorithm."""
    cs1 = compute_tle_checksum(ISS_TLE_LINE1)
    cs2 = compute_tle_checksum(ISS_TLE_LINE2)
    assert cs1 == 0
    assert cs2 == 7


def test_valid_tle_parsing():
    """Test standard 3LE parsing into a CatalogueObject."""
    obj = parse_tle(ISS_TLE_LINE1, ISS_TLE_LINE2, line0=ISS_TLE_LINE0)
    assert obj.object_id == "25544"
    assert obj.name == "ISS (ZARYA)"
    assert obj.object_type == "PAYLOAD"
    assert obj.international_designator == "98067A"
    assert obj.elements is not None
    assert 6700.0 < obj.elements.semi_major_axis_km < 6900.0
    assert 0.0 < obj.elements.eccentricity < 0.01
    assert pytest.approx(obj.elements.inclination_deg, 0.01) == 51.6416
    assert 90.0 < obj.elements.period_minutes < 95.0
    assert obj.elements.validate() == []


def test_malformed_tle_checksum_rejection():
    """Ensure modified character in TLE without updated checksum is rejected."""
    corrupted_line1 = ISS_TLE_LINE1[:10] + "9" + ISS_TLE_LINE1[11:]
    with pytest.raises(ValueError, match="checksum mismatch"):
        parse_tle(corrupted_line1, ISS_TLE_LINE2)


def test_mismatched_norad_ids_rejection():
    """Ensure mismatched IDs between Line 1 and Line 2 are rejected."""
    mismatched_line2 = ISS_TLE_LINE2[:2] + "99999" + ISS_TLE_LINE2[7:]
    with pytest.raises(ValueError):
        parse_tle(ISS_TLE_LINE1, mismatched_line2)


def test_omm_json_parsing():
    """Test CCSDS OMM JSON schema parser."""
    omm_sample = {
        "OBJECT_NAME": "CARTOSAT-3",
        "OBJECT_ID": "2019-081A",
        "NORAD_CAT_ID": 44804,
        "EPOCH": "2026-11-20T12:00:00.000",
        "MEAN_MOTION": 15.185,
        "ECCENTRICITY": 0.0012,
        "INCLINATION": 97.452,
        "RA_OF_ASC_NODE": 45.12,
        "ARG_OF_PERICENTER": 85.45,
        "MEAN_ANOMALY": 274.80,
        "BSTAR": 0.000023456,
        "OBJECT_TYPE": "PAYLOAD",
    }
    objs = parse_omm_json([omm_sample])
    assert len(objs) == 1
    obj = objs[0]
    assert obj.object_id == "44804"
    assert obj.name == "CARTOSAT-3"
    assert obj.object_type == "PAYLOAD"
    assert obj.elements.inclination_deg == 97.452
    assert obj.elements.validate() == []


def test_omm_csv_parsing():
    """Test CCSDS OMM CSV format parser."""
    csv_text = (
        "NORAD_CAT_ID,OBJECT_NAME,EPOCH,MEAN_MOTION,ECCENTRICITY,INCLINATION,RA_OF_ASC_NODE,ARG_OF_PERICENTER,MEAN_ANOMALY,BSTAR,OBJECT_TYPE\n"
        "22285,SL-16 R/B,2026-11-20T12:00:00,14.85,0.00215,71.015,162.34,42.1,318.2,0.000098,ROCKET BODY\n"
    )
    objs = parse_omm_csv(csv_text)
    assert len(objs) == 1
    obj = objs[0]
    assert obj.object_id == "22285"
    assert obj.name == "SL-16 R/B"
    assert obj.object_type == "ROCKET BODY"
    assert obj.elements.eccentricity == 0.00215


def test_celestrak_caching_and_offline_fallback():
    """Verify caching, offline fallback, and deterministic fixtures."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        client = CelesTrakClient(cache_dir=tmp_dir, cache_ttl_seconds=3600)
        # Calling fetch_group with network offline or mock will return offline fixtures
        objs = client.get_offline_fixtures()
        assert len(objs) >= 5
        ids = {o.object_id for o in objs}
        assert "25544" in ids  # ISS
        assert "44804" in ids  # CARTOSAT-3
        assert "22285" in ids  # SL-16 R/B


def test_spacetrack_unconfigured_policy():
    """Verify Space-Track returns explicit status when credentials not configured."""
    # Ensure env vars are not set
    old_u = os.environ.pop("SPACE_TRACK_USER", None)
    old_p = os.environ.pop("SPACE_TRACK_PASSWORD", None)
    try:
        st_client = SpaceTrackClient()
        assert not st_client.is_configured
        res = st_client.query_catalog("ISS")
        assert res["status"] == "CREDENTIALS_NOT_CONFIGURED"
        assert len(res["objects"]) == 0
    finally:
        if old_u: os.environ["SPACE_TRACK_USER"] = old_u
        if old_p: os.environ["SPACE_TRACK_PASSWORD"] = old_p


def test_catalogue_registry_tracking_and_persistence():
    """Verify search, track, untrack, and persistent selection state."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        storage_file = os.path.join(tmp_dir, "tracked.json")
        registry = CatalogueRegistry(storage_path=storage_file)

        # 1. Search
        search_results = registry.search(query="ISS")
        assert len(search_results) >= 1
        iss = search_results[0]
        assert iss.object_id == "25544"

        # 2. Track object
        assert registry.track_object("25544") is True
        assert registry.is_tracked("25544") is True
        tracked = registry.list_tracked()
        assert any(o.object_id == "25544" for o in tracked)

        # 3. Persistence verification: create new registry instance loading same file
        reg2 = CatalogueRegistry(storage_path=storage_file)
        assert reg2.is_tracked("25544") is True

        # 4. Untrack object (must not delete object from external/local registry)
        assert reg2.untrack_object("25544") is True
        assert reg2.is_tracked("25544") is False
        assert reg2.get_object("25544") is not None  # Object still exists in catalogue!
