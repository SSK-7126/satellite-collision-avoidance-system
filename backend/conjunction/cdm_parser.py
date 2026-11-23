"""
backend/conjunction/cdm_parser.py
=================================
Parser for CCSDS Conjunction Data Messages (CDM).
Supports CCSDS 508.0-B-1 JSON format with provenance tracking.
"""

import json
from typing import Dict, Any, Optional, Union

from .models import CDMRecord


def parse_cdm_json(json_content: Union[str, Dict[str, Any]]) -> CDMRecord:
    """
    Parse a CCSDS Conjunction Data Message (CDM) from JSON string or dict.
    """
    if isinstance(json_content, str):
        data = json.loads(json_content)
    else:
        data = data = json_content

    header = data.get("header") or data.get("HEADER") or {}
    body = data.get("body") or data.get("BODY") or data

    rel_metadata = body.get("relative_metadata") or body.get("RELATIVE_METADATA") or {}
    tca_str = rel_metadata.get("TCA") or data.get("TCA", "")
    miss_dist = float(rel_metadata.get("MISS_DISTANCE", data.get("MISS_DISTANCE", 0.0)))
    rel_speed = float(rel_metadata.get("RELATIVE_SPEED", data.get("RELATIVE_SPEED", 0.0)))
    coll_prob = rel_metadata.get("COLLISION_PROBABILITY") or data.get("COLLISION_PROBABILITY")
    if coll_prob is not None:
        coll_prob = float(coll_prob)

    hbr = rel_metadata.get("COLLISION_PROBABILITY_METHOD_PARAMETERS", {}).get("HARD_BODY_RADIUS") or data.get("HARD_BODY_RADIUS")
    if hbr is not None:
        hbr = float(hbr)

    # Segment 1 (Primary / Target)
    seg1 = body.get("segment1") or body.get("SEGMENT1") or {}
    meta1 = seg1.get("metadata") or seg1.get("METADATA") or {}
    prim_id = str(meta1.get("OBJECT_DESIGNATOR") or data.get("OBJECT1_ID", "UNKNOWN_1"))
    prim_name = meta1.get("OBJECT_NAME") or data.get("OBJECT1_NAME", f"OBJECT {prim_id}")

    # Segment 2 (Secondary / Chaser)
    seg2 = body.get("segment2") or body.get("SEGMENT2") or {}
    meta2 = seg2.get("metadata") or seg2.get("METADATA") or {}
    sec_id = str(meta2.get("OBJECT_DESIGNATOR") or data.get("OBJECT2_ID", "UNKNOWN_2"))
    sec_name = meta2.get("OBJECT_NAME") or data.get("OBJECT2_NAME", f"OBJECT {sec_id}")

    msg_id = header.get("MESSAGE_ID") or data.get("MESSAGE_ID", "CDM-GEN")
    originator = header.get("ORIGINATOR") or data.get("ORIGINATOR", "UNKNOWN_ORIGINATOR")
    creation_date = header.get("CREATION_DATE") or data.get("CREATION_DATE", "")

    return CDMRecord(
        message_id=msg_id,
        originator=originator,
        creation_date=creation_date,
        tca_utc=tca_str,
        miss_distance_m=miss_dist,
        relative_speed_mps=rel_speed,
        primary_id=prim_id,
        primary_name=prim_name,
        secondary_id=sec_id,
        secondary_name=sec_name,
        collision_probability=coll_prob,
        hard_body_radius_m=hbr,
        provenance={"parsed_from": "CCSDS_CDM_JSON", "originator": originator},
    )
