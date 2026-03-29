from __future__ import annotations

from dataclasses import asdict
import json
from pathlib import Path
import tempfile
from uuid import uuid4

from .classifier import DataClassifier
from .config_loader import load_json_config
from .discovery import DiscoveryEngine
from .generator import ArtifactGenerator, summarize_confidence
from .indian_models import generate_indic_summary
from .mappers import ConflictDetector, ObligationMapper
from .mllib_purpose import enrich_purpose_with_mllib
from .models import ComplianceResult

try:
    from .verifier import GroundingVerifier, extract_obligation_claims
except ModuleNotFoundError:

    class GroundingVerifier:  # type: ignore[no-redef]
        def __init__(self, legal_text_path: Path, threshold: float = 0.0) -> None:
            self.threshold = threshold

        def score_claims(self, claims: list[str]) -> list[dict]:
            return [
                {
                    "claim": claim,
                    "score": 0.0,
                    "is_grounded": False,
                    "matched_snippet": "",
                }
                for claim in claims
            ]

    def extract_obligation_claims(artifacts: dict[str, str]) -> list[str]:  # type: ignore[no-redef]
        claims: list[str] = []
        seen: set[str] = set()
        for content in artifacts.values():
            for line in content.splitlines():
                normalized = line.strip()
                if normalized.startswith("-") or normalized[:2].isdigit():
                    claim = normalized.lstrip("- ").strip()
                    if claim and claim not in seen:
                        seen.add(claim)
                        claims.append(claim)
        return claims


class CompliancePipeline:
    def __init__(self, base_dir: Path | None = None) -> None:
        base = base_dir or Path(__file__).resolve().parent
        config_dir = base / "config"
        template_dir = base / "templates"

        self.discovery = DiscoveryEngine()
        self.classifier = DataClassifier(
            load_json_config(config_dir / "pii_taxonomy.json")
        )
        self.obligation_mapper = ObligationMapper(
            load_json_config(config_dir / "obligation_index.json")
        )
        self.conflict_detector = ConflictDetector(
            load_json_config(config_dir / "sector_conflicts.json")
        )
        self.purpose_training_samples = load_json_config(
            config_dir / "purpose_training_data.json"
        )
        self.generator = ArtifactGenerator(template_dir)
        self.model_store_dir = Path("artifacts/model_store")
        legal_text_candidates = [
            Path("data/DPDP_Rules_2025_English_only.md"),
            Path(__file__).resolve().parents[2]
            / "data"
            / "DPDP_Rules_2025_English_only.md",
        ]
        legal_text_path = next(
            (path for path in legal_text_candidates if path.exists()),
            legal_text_candidates[0],
        )
        self.verifier = GroundingVerifier(legal_text_path=legal_text_path)

    def _spark_session(self):
        try:
            from pyspark.sql import SparkSession

            return SparkSession.builder.appName("dpdp-kavach-online").getOrCreate()
        except Exception:
            return None

    def _discover_with_spark(self, schema_path: Path, spark=None):
        _spark = spark or self._spark_session()
        if _spark is None:
            return self.discovery.parse_schema_file(schema_path)
        try:
            return self.discovery.parse_schema_spark(_spark, schema_path)
        finally:
            if spark is None:
                _spark.stop()

    def _classify_with_spark(self, elements, sector: str, spark=None):
        _spark = spark or self._spark_session()
        if _spark is None:
            return self.classifier.classify(elements, sector=sector)
        try:
            return self.classifier.classify_spark(_spark, elements, sector=sector)
        finally:
            if spark is None:
                _spark.stop()

    def run(
        self,
        schema_path: Path,
        business_name: str,
        sector: str,
        language: str,
        artifact_output_dir: Path,
        require_mllib: bool = False,
        indian_api_key: str | None = None,
        use_spark: bool = False,
        spark=None,
    ) -> tuple[ComplianceResult, Path]:
        elements = (
            self._discover_with_spark(schema_path, spark)
            if use_spark
            else self.discovery.parse_schema_file(schema_path)
        )
        classified = (
            self._classify_with_spark(elements, sector, spark)
            if use_spark
            else self.classifier.classify(elements, sector=sector)
        )
        classified, mllib_metrics = enrich_purpose_with_mllib(
            classified,
            self.purpose_training_samples,
            model_store_dir=self.model_store_dir,
        )
        if require_mllib and not bool(mllib_metrics.get("mllib_used", False)):
            raise RuntimeError(
                "MLlib purpose refinement unavailable; Databricks demo requires active Spark MLlib."
            )
        obligations = self.obligation_mapper.map(classified)
        conflicts = self.conflict_detector.detect(sector)

        artifacts = self.generator.generate(
            business_name=business_name,
            sector=sector,
            language=language,
            classified=classified,
            obligations=obligations,
            conflicts=conflicts,
        )
        indic_summary, indic_meta = generate_indic_summary(
            business_name=business_name,
            sector=sector,
            language=language,
            obligations=[asdict(item) for item in obligations],
            conflicts=[asdict(item) for item in conflicts],
            api_key_override=indian_api_key,
        )
        if indic_summary:
            artifacts["indic_summary.md"] = indic_summary

        scan_id = uuid4().hex[:12]
        zip_path = self.generator.build_zip(artifact_output_dir / scan_id, artifacts)

        claims = extract_obligation_claims(artifacts)
        grounding_report = self.verifier.score_claims(claims)
        metrics = summarize_confidence(classified)
        grounded = [item for item in grounding_report if bool(item["is_grounded"])]
        metrics["grounding_score"] = (
            round(len(grounded) / len(grounding_report), 4) if grounding_report else 0.0
        )
        metrics["grounding_backend"] = getattr(self.verifier, "backend", "cosine_scan")
        penalty_max, penalty_current = self._estimate_penalty_exposure(
            obligations, conflicts, classified, metrics["grounding_score"]
        )
        metrics["scan_id"] = scan_id
        metrics["fields_scanned"] = len(classified)
        metrics["obligation_count"] = len(obligations)
        metrics["conflict_count"] = len(conflicts)
        metrics["penalty_exposure_max_crore"] = penalty_max
        metrics["penalty_exposure_current_crore"] = penalty_current
        metrics.update(mllib_metrics)
        metrics.update(indic_meta)
        metrics.update(self._log_mlflow_scan(metrics, business_name, sector, language))

        result = ComplianceResult(
            business_name=business_name,
            sector=sector,
            language=language,
            classified_elements=classified,
            obligations=obligations,
            conflicts=conflicts,
            artifacts=artifacts,
            grounding_report=grounding_report,
            metrics=metrics,
        )
        return result, zip_path

    @staticmethod
    def _log_mlflow_scan(
        metrics: dict, business_name: str, sector: str, language: str
    ) -> dict[str, str]:
        try:
            import mlflow

            mlflow.set_experiment("dpdp_kavach_scans")
            with mlflow.start_run(
                run_name=f"scan-{metrics.get('scan_id', 'unknown')}"
            ) as run:
                mlflow.log_params(
                    {
                        "business_name": business_name,
                        "sector": sector,
                        "language": language,
                        "purpose_classifier_version": str(
                            metrics.get("purpose_classifier_version", "unknown")
                        ),
                    }
                )
                mlflow.log_metrics(
                    {
                        "fields_scanned": float(metrics.get("fields_scanned", 0)),
                        "obligation_count": float(metrics.get("obligation_count", 0)),
                        "conflict_count": float(metrics.get("conflict_count", 0)),
                        "grounding_score": float(metrics.get("grounding_score", 0.0)),
                        "mllib_predictions": float(metrics.get("mllib_predictions", 0)),
                        "penalty_exposure_current_crore": float(
                            metrics.get("penalty_exposure_current_crore", 0.0)
                        ),
                    }
                )
                with tempfile.NamedTemporaryFile(
                    mode="w", suffix=".json", delete=False, encoding="utf-8"
                ) as tmp:
                    json.dump(metrics, tmp, indent=2)
                    temp_path = Path(tmp.name)
                mlflow.log_artifact(str(temp_path), artifact_path="scan_metrics")
                temp_path.unlink(missing_ok=True)
                return {"mlflow_run_id": run.info.run_id}
        except Exception:
            return {"mlflow_run_id": "unavailable"}

    @staticmethod
    def _estimate_penalty_exposure(
        obligations: list,
        conflicts: list,
        classified: list,
        grounding_score: float,
    ) -> tuple[float, float]:
        weight = {
            "notice": 1.0,
            "consent": 2.0,
            "security": 2.0,
            "breach": 2.5,
            "children": 3.0,
            "retention_erasure": 1.5,
        }
        base = sum(weight.get(item.obligation_type, 1.0) for item in obligations)
        sensitive_count = sum(
            1 for item in classified if getattr(item, "sensitivity", "") == "sensitive"
        )
        severity = (
            1.0 + (0.1 * min(len(conflicts), 3)) + (0.03 * min(sensitive_count, 15))
        )
        penalty_max = round(base * severity, 2)
        mitigation = max(0.35, min(0.9, grounding_score))
        penalty_current = round(penalty_max * (1.1 - mitigation), 2)
        return penalty_max, penalty_current

    @staticmethod
    def to_serializable(result: ComplianceResult) -> dict:
        return {
            "business_name": result.business_name,
            "sector": result.sector,
            "language": result.language,
            "classified_elements": [
                asdict(item) for item in result.classified_elements
            ],
            "obligations": [asdict(item) for item in result.obligations],
            "conflicts": [asdict(item) for item in result.conflicts],
            "artifacts": result.artifacts,
            "grounding_report": result.grounding_report,
            "metrics": result.metrics,
        }
