"""
backend/resources/registry.py
=============================
Hardware and Resource Registry managing spacecraft hardware profiles,
burn execution accounting, and persistence.
"""

import os
import json
import logging
import uuid
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional

from .models import (
    SpacecraftHardwareRecord,
    ThrusterSpecification,
    FuelEvent,
    ProvenanceType,
)
from .fuel_calculator import estimate_propellant_consumption, G0_STANDARD

logger = logging.getLogger(__name__)


class HardwareRegistry:
    """
    Registry maintaining spacecraft physical properties, thrusters, and propellant states.
    """
    def __init__(self, storage_path: Optional[str] = None):
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        self.storage_path = storage_path or os.path.join(base_dir, "data", "hardware_registry.json")
        self._records_by_id: Dict[str, SpacecraftHardwareRecord] = {}

        self.initialize()

    def initialize(self):
        """Populate initial registry with default baseline records and load persistence."""
        # Baseline demo records
        # 1. CARTOSAT-3 (ISRO Primary Spacecraft)
        cartosat = SpacecraftHardwareRecord(
            object_id="44804",
            owner_operator="ISRO (Indian Space Research Organisation)",
            spacecraft_model="I-1K Bus",
            dimensions_xyz_m=[2.4, 1.8, 1.6],
            dry_mass_kg=1100.0,
            initial_propellant_kg=55.0,
            current_propellant_kg=55.0,
            propellant_type="HYDRAZINE_MONOPROPELLANT",
            thrusters=[
                ThrusterSpecification(
                    thruster_type="HYDRAZINE_RCS",
                    count=8,
                    thrust_n=11.0,
                    isp_sec=220.0,
                    max_continuous_burn_sec=120.0,
                )
            ],
            field_provenances={
                "mass": {"source": ProvenanceType.SIMULATED_DEMO.value, "confidence": "ASSUMED"},
                "propellant": {"source": ProvenanceType.SIMULATED_DEMO.value, "confidence": "ASSUMED"},
            }
        )
        self._records_by_id["44804"] = cartosat

        # 2. SL-16 R/B (Inert Debris / Spent Upper Stage)
        sl16 = SpacecraftHardwareRecord(
            object_id="22285",
            owner_operator="FORMER_USSR_CIS",
            spacecraft_model="Zenit-2 Second Stage",
            dimensions_xyz_m=[3.9, 3.9, 10.4],
            dry_mass_kg=8300.0,
            initial_propellant_kg=0.0,
            current_propellant_kg=0.0,
            propellant_type="NONE (DEPLETED)",
            thrusters=[],
            field_provenances={
                "propellant": {"source": ProvenanceType.PUBLIC_DATABASE.value, "confidence": "MEASURED_ZERO"}
            }
        )
        self._records_by_id["22285"] = sl16

        # Load persisted records if present
        self.load_from_storage()

    def get_record(self, object_id: str) -> Optional[SpacecraftHardwareRecord]:
        return self._records_by_id.get(str(object_id))

    def set_record(self, record: SpacecraftHardwareRecord) -> None:
        self._records_by_id[str(record.object_id)] = record
        self.save_to_storage()

    def record_manoeuvre_burn(
        self,
        object_id: str,
        manoeuvre_id: str,
        delta_v_mps: float,
        isp_sec: Optional[float] = None
    ) -> FuelEvent:
        """
        Record an impulsive burn, calculate Tsiolkovsky propellant consumed,
        update spacecraft current propellant, and append to fuel event history.
        """
        oid = str(object_id)
        record = self.get_record(oid)
        if not record:
            raise KeyError(f"No hardware record found for space object {oid}")

        effective_isp = isp_sec
        if effective_isp is None:
            if record.thrusters:
                effective_isp = record.thrusters[0].isp_sec
            else:
                effective_isp = 220.0  # Default monopropellant Isp assumption

        # Initial mass before burn
        mass_before = record.total_mass_kg

        # Calculate consumed propellant
        consumed_kg = estimate_propellant_consumption(
            initial_mass_kg=mass_before,
            delta_v_mps=delta_v_mps,
            isp_sec=effective_isp,
        )

        if consumed_kg > record.current_propellant_kg:
            raise ValueError(
                f"Burn requires {consumed_kg:.2f} kg of propellant, but only "
                f"{record.current_propellant_kg:.2f} kg is available."
            )

        # Update remaining propellant
        record.current_propellant_kg = max(0.0, record.current_propellant_kg - consumed_kg)
        mass_after = record.total_mass_kg

        event = FuelEvent(
            event_id=f"FUEL-{uuid.uuid4().hex[:8].upper()}",
            manoeuvre_id=manoeuvre_id,
            timestamp_utc=datetime.now(timezone.utc).isoformat(),
            delta_v_mps=round(delta_v_mps, 3),
            estimated_propellant_used_kg=round(consumed_kg, 4),
            mass_before_kg=round(mass_before, 2),
            mass_after_kg=round(mass_after, 2),
            remaining_propellant_kg=round(record.current_propellant_kg, 2),
            assumptions=f"Tsiolkovsky equation estimate, Isp={effective_isp}s, g0={G0_STANDARD} m/s^2",
            is_estimate=True,
        )

        record.fuel_events.append(event)
        self.save_to_storage()
        return event

    def save_to_storage(self) -> None:
        try:
            os.makedirs(os.path.dirname(self.storage_path), exist_ok=True)
            data = {
                "schema_version": "1.0",
                "records": {k: v.to_dict() for k, v in self._records_by_id.items()},
            }
            with open(self.storage_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            logger.warning(f"Error saving hardware registry: {e}")

    def load_from_storage(self) -> None:
        if not os.path.exists(self.storage_path):
            return
        try:
            with open(self.storage_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            records_dict = data.get("records", {})
            for k, v in records_dict.items():
                self._records_by_id[k] = SpacecraftHardwareRecord.from_dict(v)
        except Exception as e:
            logger.warning(f"Error loading hardware registry: {e}")
