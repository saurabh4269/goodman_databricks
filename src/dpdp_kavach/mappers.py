from __future__ import annotations

from typing import Any

from .models import ClassifiedElement, Conflict, Obligation


class ObligationMapper:
    def __init__(self, obligation_index: list[dict[str, Any]]) -> None:
        self.obligation_index = obligation_index

    def map(self, classified: list[ClassifiedElement]) -> list[Obligation]:
        has_sensitive = any(item.sensitivity == "sensitive" for item in classified)
        has_children = any(item.pii_category == "children_data" for item in classified)
        has_personal = any(item.sensitivity in {"personal", "sensitive"} for item in classified)

        obligations: list[Obligation] = []
        for row in self.obligation_index:
            trigger = False
            categories = set(row["trigger_categories"])
            if "personal" in categories and has_personal:
                trigger = True
            if "sensitive" in categories and has_sensitive:
                trigger = True
            if "children" in categories and has_children:
                trigger = True
            if trigger:
                obligations.append(
                    Obligation(
                        obligation_id=row["id"],
                        section=row["section"],
                        obligation_type=row["obligation_type"],
                        description=row["description"],
                    )
                )
        return obligations


class ConflictDetector:
    def __init__(self, conflict_index: list[dict[str, Any]]) -> None:
        self.conflict_index = conflict_index

    def detect(self, sector: str) -> list[Conflict]:
        return [
            Conflict(
                sector=row["sector"],
                regulation=row["regulation"],
                dpdp_section=row["dpdp_section"],
                summary=row["summary"],
                resolution=row["resolution"],
            )
            for row in self.conflict_index
            if row["sector"] == sector
        ]
