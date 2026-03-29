from __future__ import annotations

from collections import Counter
from datetime import UTC, datetime
from pathlib import Path
from string import Template
from typing import Iterable
import zipfile

from .models import ClassifiedElement, Conflict, Obligation


class ArtifactGenerator:
    def __init__(self, template_dir: Path) -> None:
        self.template_dir = template_dir

    def generate(
        self,
        business_name: str,
        sector: str,
        language: str,
        classified: list[ClassifiedElement],
        obligations: list[Obligation],
        conflicts: list[Conflict],
    ) -> dict[str, str]:
        categories = Counter(item.pii_category for item in classified if item.pii_category != "non_pii")
        category_lines = "\n".join([f"- {name}: {count} fields" for name, count in categories.items()]) or "- none"
        obligation_lines = "\n".join([f"- {item.obligation_type}: {item.section}" for item in obligations])
        conflict_lines = "\n".join([f"- {item.regulation}: {item.summary}" for item in conflicts]) or "- none"
        vendors = infer_vendors(classified)
        vendor_lines = "\n".join([f"- {name}: {summary}" for name, summary in vendors]) or "- no high-risk processors inferred"

        context = {
            "business_name": business_name,
            "sector": sector,
            "language": language,
            "generated_at": datetime.now(UTC).isoformat(),
            "categories": category_lines,
            "obligations": obligation_lines,
            "conflicts": conflict_lines,
            "vendors": vendor_lines,
        }

        files = {
            "privacy_notice.md": self._render("privacy_notice.md.tmpl", context),
            "consent_package.md": self._render("consent_package.md.tmpl", context),
            "retention_policy.md": self._render("retention_policy.md.tmpl", context),
            "breach_playbook.md": self._render("breach_playbook.md.tmpl", context),
            "compliance_register.md": self._render("compliance_register.md.tmpl", context),
            "dpa_templates.md": self._render("dpa_templates.md.tmpl", context),
        }

        if any(item.obligation_type == "children" for item in obligations):
            files["children_data_package.md"] = self._render("children_data_package.md.tmpl", context)
        return files

    def build_zip(self, artifact_dir: Path, artifacts: dict[str, str], zip_name: str = "compliance_kit.zip") -> Path:
        artifact_dir.mkdir(parents=True, exist_ok=True)
        for file_name, content in artifacts.items():
            (artifact_dir / file_name).write_text(content, encoding="utf-8")

        zip_path = artifact_dir / zip_name
        with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
            for file_name in artifacts:
                zf.write(artifact_dir / file_name, arcname=file_name)
        return zip_path

    def _render(self, template_name: str, context: dict[str, str]) -> str:
        template_path = self.template_dir / template_name
        template = Template(template_path.read_text(encoding="utf-8"))
        return template.safe_substitute(context)


def summarize_confidence(classified: Iterable[ClassifiedElement]) -> dict[str, float]:
    rows = list(classified)
    if not rows:
        return {"avg_confidence": 0.0, "high_confidence_ratio": 0.0}
    avg = sum(item.confidence for item in rows) / len(rows)
    high = sum(1 for item in rows if item.confidence >= 0.8) / len(rows)
    return {"avg_confidence": round(avg, 4), "high_confidence_ratio": round(high, 4)}


def infer_vendors(classified: Iterable[ClassifiedElement]) -> list[tuple[str, str]]:
    rows = list(classified)
    has_payments = any(item.purpose in {"payments", "kyc"} or item.pii_category in {"financial_data", "pan"} for item in rows)
    has_identity = any(item.pii_category in {"aadhaar", "pan", "identifier"} for item in rows)
    has_communications = any(item.pii_category in {"mobile_number", "email"} for item in rows)

    vendors: list[tuple[str, str]] = []
    if has_payments:
        vendors.append(("Razorpay", "Payment processor; execute Section 8(2) processor contract and breach notice clauses."))
    if has_identity:
        vendors.append(("Digio/eKYC Partner", "Identity verification processor; restrict usage to KYC purpose and retention basis."))
    if has_communications:
        vendors.append(("SMS/Email Gateway", "Communication processor; include consent withdrawal propagation obligations."))
    return vendors
