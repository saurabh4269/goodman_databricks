#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

from pyspark.sql import SparkSession
from pyspark.sql import functions as F

from dpdp_kavach.pipeline import CompliancePipeline


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run DPDP Kavach pipeline and persist Delta outputs"
    )
    parser.add_argument(
        "--schema", required=True, help="Path to schema file on DBFS/local"
    )
    parser.add_argument("--business", required=True)
    parser.add_argument(
        "--sector", required=True, choices=["fintech", "healthtech", "general"]
    )
    parser.add_argument("--language", default="English")
    parser.add_argument("--output", required=True, help="DBFS directory for outputs")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    spark = SparkSession.builder.appName("dpdp-kavach-pipeline").getOrCreate()

    pipeline = CompliancePipeline(
        base_dir=Path(__file__).resolve().parents[1] / "src" / "dpdp_kavach"
    )
    result, zip_path = pipeline.run(
        schema_path=Path(args.schema),
        business_name=args.business,
        sector=args.sector,
        language=args.language,
        artifact_output_dir=Path(args.output),
        use_spark=True,
        spark=spark,
    )

    serializable = pipeline.to_serializable(result)
    rows = serializable["classified_elements"]
    classified_df = spark.createDataFrame(rows)
    classified_df.write.format("delta").mode("overwrite").save(
        f"{args.output}/delta/classified_elements"
    )

    obligations_df = spark.createDataFrame(serializable["obligations"])
    obligations_df.write.format("delta").mode("overwrite").save(
        f"{args.output}/delta/obligations"
    )

    conflicts = serializable["conflicts"]
    if conflicts:
        spark.createDataFrame(conflicts).write.format("delta").mode("overwrite").save(
            f"{args.output}/delta/conflicts"
        )

    audit = {
        "scan_id": serializable["metrics"]["scan_id"],
        "business_name": args.business,
        "sector": args.sector,
        "language": args.language,
        "fields_scanned": serializable["metrics"]["fields_scanned"],
        "obligation_count": serializable["metrics"]["obligation_count"],
        "conflict_count": serializable["metrics"]["conflict_count"],
        "avg_confidence": serializable["metrics"]["avg_confidence"],
        "high_confidence_ratio": serializable["metrics"]["high_confidence_ratio"],
        "grounding_score": serializable["metrics"]["grounding_score"],
        "grounding_backend": str(
            serializable["metrics"].get("grounding_backend", "cosine_scan")
        ),
        "mllib_used": bool(serializable["metrics"].get("mllib_used", False)),
        "mllib_predictions": int(serializable["metrics"].get("mllib_predictions", 0)),
        "purpose_classifier_version": str(
            serializable["metrics"].get("purpose_classifier_version", "unknown")
        ),
        "mlflow_run_id": str(
            serializable["metrics"].get("mlflow_run_id", "unavailable")
        ),
        "indian_model_used": bool(
            serializable["metrics"].get("indian_model_used", False)
        ),
        "indian_model_name": str(
            serializable["metrics"].get("indian_model_name", "sarvam-m")
        ),
        "indian_model_status": str(
            serializable["metrics"].get("indian_model_status", "unavailable")
        ),
        "penalty_exposure_max_crore": serializable["metrics"][
            "penalty_exposure_max_crore"
        ],
        "penalty_exposure_current_crore": serializable["metrics"][
            "penalty_exposure_current_crore"
        ],
        "kit_zip_path": str(zip_path),
    }
    audit_df = spark.createDataFrame([audit]).withColumn(
        "ingested_at", F.current_timestamp()
    )
    audit_df.write.format("delta").mode("append").save(
        f"{args.output}/delta/artifact_audit_log"
    )

    Path(args.output).mkdir(parents=True, exist_ok=True)
    (Path(args.output) / "latest_result.json").write_text(
        json.dumps(serializable, indent=2), encoding="utf-8"
    )


if __name__ == "__main__":
    main()
