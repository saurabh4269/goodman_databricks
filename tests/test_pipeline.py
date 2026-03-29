from pathlib import Path

from dpdp_kavach.pipeline import CompliancePipeline


def test_pipeline_generates_obligations_and_zip(tmp_path: Path) -> None:
    pipeline = CompliancePipeline(base_dir=Path("src/dpdp_kavach"))
    result, zip_path = pipeline.run(
        schema_path=Path("data/demo_schema.sql"),
        business_name="TestBiz",
        sector="fintech",
        language="English",
        artifact_output_dir=tmp_path,
    )

    assert result.metrics["fields_scanned"] > 0
    assert result.metrics["obligation_count"] > 0
    assert "grounding_score" in result.metrics
    assert "penalty_exposure_max_crore" in result.metrics
    assert "penalty_exposure_current_crore" in result.metrics
    assert "mllib_used" in result.metrics
    assert "mllib_predictions" in result.metrics
    assert "mllib_status" in result.metrics
    assert "purpose_classifier_version" in result.metrics
    assert "grounding_backend" in result.metrics
    assert "mlflow_run_id" in result.metrics
    assert "indian_model_used" in result.metrics
    assert "indian_model_name" in result.metrics
    assert "indian_model_status" in result.metrics
    assert "dpa_templates.md" in result.artifacts
    assert len(result.grounding_report) > 0
    assert zip_path.exists()
