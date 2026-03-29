from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class DataElement:
    table_name: str
    column_name: str
    data_type: str
    sample_values: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class ClassifiedElement:
    table_name: str
    column_name: str
    data_type: str
    pii_category: str
    sensitivity: str
    confidence: float
    purpose: str
    source: str


@dataclass(frozen=True)
class Obligation:
    obligation_id: str
    section: str
    obligation_type: str
    description: str


@dataclass(frozen=True)
class Conflict:
    sector: str
    regulation: str
    dpdp_section: str
    summary: str
    resolution: str


@dataclass
class ComplianceResult:
    business_name: str
    sector: str
    language: str
    classified_elements: list[ClassifiedElement]
    obligations: list[Obligation]
    conflicts: list[Conflict]
    artifacts: dict[str, str]
    grounding_report: list[dict[str, Any]]
    metrics: dict[str, Any]
