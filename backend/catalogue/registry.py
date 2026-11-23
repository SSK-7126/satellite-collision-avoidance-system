"""
backend/catalogue/registry.py
=============================
Catalogue Registry for Space Objects in ICPS.
Maintains the in-memory object store, active tracked list, search indexes,
and persistent selection store.
"""

import os
import json
import logging
from typing import Dict, Any, List, Optional, Set

from .models import CatalogueObject, CatalogueSource
from .client import CelesTrakClient

logger = logging.getLogger(__name__)


class CatalogueRegistry:
    """
    Central space object registry managing real catalogue items, search,
    and user tracking selections.
    """
    def __init__(
        self,
        storage_path: Optional[str] = None,
        client: Optional[CelesTrakClient] = None,
    ):
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        self.storage_path = storage_path or os.path.join(base_dir, "data", "tracked_catalog.json")
        self.client = client or CelesTrakClient()

        self._objects_by_id: Dict[str, CatalogueObject] = {}
        self._tracked_ids: Set[str] = set()

        self.initialize()

    def initialize(self):
        """Populate initial registry and restore saved tracked state."""
        # 1. Load initial catalogue from fixtures / cache
        initial_objects = self.client.get_offline_fixtures()
        for obj in initial_objects:
            self._objects_by_id[obj.object_id] = obj

        # 2. Restore tracked list from persistence
        self.load_tracked_state()

    def add_object(self, obj: CatalogueObject) -> None:
        """Add or update an object in the registry."""
        self._objects_by_id[obj.object_id] = obj
        if obj.object_id in self._tracked_ids:
            obj.is_tracked = True

    def get_object(self, object_id: str) -> Optional[CatalogueObject]:
        """Lookup object by unique NORAD or custom ID."""
        return self._objects_by_id.get(str(object_id))

    def track_object(self, object_id: str) -> bool:
        """
        Add object to active tracking list.
        Returns True if successful, False if object not in registry.
        """
        oid = str(object_id)
        if oid in self._objects_by_id:
            self._tracked_ids.add(oid)
            self._objects_by_id[oid].is_tracked = True
            self.save_tracked_state()
            return True
        return False

    def untrack_object(self, object_id: str) -> bool:
        """
        Remove object from active tracking list.
        Preserves object in catalogue; does not delete external records.
        """
        oid = str(object_id)
        if oid in self._tracked_ids:
            self._tracked_ids.remove(oid)
            if oid in self._objects_by_id:
                self._objects_by_id[oid].is_tracked = False
            self.save_tracked_state()
            return True
        return False

    def is_tracked(self, object_id: str) -> bool:
        """Return whether object is in active tracked list."""
        return str(object_id) in self._tracked_ids

    def list_tracked(self) -> List[CatalogueObject]:
        """Return all actively tracked objects."""
        return [self._objects_by_id[oid] for oid in self._tracked_ids if oid in self._objects_by_id]

    def list_all(self) -> List[CatalogueObject]:
        """Return all known registry objects."""
        return list(self._objects_by_id.values())

    def search(
        self,
        query: str = "",
        group: Optional[str] = None,
        object_type: Optional[str] = None,
        tracked_only: bool = False
    ) -> List[CatalogueObject]:
        """
        Search registry by query string (matching name or ID), group, or type.
        """
        q = query.strip().upper()
        results = []

        for obj in self._objects_by_id.values():
            if tracked_only and not obj.is_tracked:
                continue

            if group and obj.group and obj.group.lower() != group.lower() and group.lower() != "all":
                continue

            if object_type and obj.object_type.upper() != object_type.upper():
                continue

            if q:
                id_match = q in obj.object_id.upper()
                name_match = q in obj.name.upper()
                desig_match = obj.international_designator and q in obj.international_designator.upper()
                if not (id_match or name_match or desig_match):
                    continue

            results.append(obj)

        return results

    def load_group(self, group_name: str, force_refresh: bool = False) -> int:
        """
        Fetch and register objects from a specific CelesTrak group.
        Returns count of new/updated objects added.
        """
        fetched = self.client.fetch_group(group_name, fmt="json", force_refresh=force_refresh)
        count = 0
        for obj in fetched:
            self.add_object(obj)
            count += 1
        return count

    def save_tracked_state(self) -> None:
        """Persist tracked IDs and user metadata to disk."""
        try:
            os.makedirs(os.path.dirname(self.storage_path), exist_ok=True)
            data = {
                "schema_version": "1.0",
                "tracked_ids": sorted(list(self._tracked_ids)),
                "total_tracked": len(self._tracked_ids),
            }
            with open(self.storage_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            logger.warning(f"Failed to persist tracked catalogue state: {e}")

    def load_tracked_state(self) -> None:
        """Load tracked IDs from disk."""
        if not os.path.exists(self.storage_path):
            # By default track CARTOSAT-3 and SL-16 R/B matching demo
            self._tracked_ids = {"44804", "22285"}
            for oid in self._tracked_ids:
                if oid in self._objects_by_id:
                    self._objects_by_id[oid].is_tracked = True
            return

        try:
            with open(self.storage_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            saved_ids = set(str(x) for x in data.get("tracked_ids", []))
            self._tracked_ids = saved_ids
            for oid in self._tracked_ids:
                if oid in self._objects_by_id:
                    self._objects_by_id[oid].is_tracked = True
        except Exception as e:
            logger.warning(f"Failed to load tracked catalogue state: {e}")
