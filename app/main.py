from __future__ import annotations

import tempfile
import json
import os
from pathlib import Path
import sys
from typing import Any

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel

ROOT_DIR = Path(__file__).resolve().parents[1]
SRC_DIR = ROOT_DIR / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from dpdp_kavach.pipeline import CompliancePipeline


class HealthResponse(BaseModel):
    status: str


class GrievanceRequest(BaseModel):
    request_type: str
    principal_id: str
    details: str


app = FastAPI(
    title="DPDP Kavach API",
    version="1.0.0",
    docs_url=None,
    redoc_url=None,
    openapi_url="/api/openapi.json",
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

pipeline = CompliancePipeline(base_dir=ROOT_DIR / "src" / "dpdp_kavach")
artifact_root = ROOT_DIR / "artifacts"
artifact_root.mkdir(parents=True, exist_ok=True)
grievance_log_path = artifact_root / "grievance_log.jsonl"
REQUIRE_MLLIB = os.environ.get("REQUIRE_MLLIB", "0") == "1"
USE_SPARK_FOR_SCAN = os.environ.get("USE_SPARK_FOR_SCAN", "1") == "1"
SARVAM_API_KEY = "sk_wuwzo5h0_N0yrZFaJw0T0uKjciZU1iMfz"


def _write_scan_to_lakehouse(
    serializable: dict[str, Any], business_name: str, sector: str, language: str
) -> dict[str, Any]:
    try:
        from pyspark.sql import SparkSession
        from pyspark.sql import functions as F

        spark = SparkSession.builder.appName("dpdp-kavach-app-scan").getOrCreate()
        scan_id = serializable["metrics"]["scan_id"]
        delta_base = artifact_root / "delta_live"
        delta_base.mkdir(parents=True, exist_ok=True)

        classified_df = spark.createDataFrame(
            serializable["classified_elements"]
        ).withColumn("scan_id", F.lit(scan_id))
        classified_df.write.format("delta").mode("append").save(
            str(delta_base / "classified_elements")
        )

        obligations_df = spark.createDataFrame(serializable["obligations"]).withColumn(
            "scan_id", F.lit(scan_id)
        )
        obligations_df.write.format("delta").mode("append").save(
            str(delta_base / "obligations")
        )

        if serializable["conflicts"]:
            conflicts_df = spark.createDataFrame(serializable["conflicts"]).withColumn(
                "scan_id", F.lit(scan_id)
            )
            conflicts_df.write.format("delta").mode("append").save(
                str(delta_base / "conflicts")
            )

        audit = {
            "scan_id": scan_id,
            "business_name": business_name,
            "sector": sector,
            "language": language,
            "fields_scanned": serializable["metrics"]["fields_scanned"],
            "obligation_count": serializable["metrics"]["obligation_count"],
            "conflict_count": serializable["metrics"]["conflict_count"],
            "grounding_score": serializable["metrics"]["grounding_score"],
            "grounding_backend": str(
                serializable["metrics"].get("grounding_backend", "cosine_scan")
            ),
            "mllib_used": bool(serializable["metrics"].get("mllib_used", False)),
            "mllib_predictions": int(
                serializable["metrics"].get("mllib_predictions", 0)
            ),
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
            "penalty_exposure_current_crore": serializable["metrics"][
                "penalty_exposure_current_crore"
            ],
        }
        audit_df = spark.createDataFrame([audit]).withColumn(
            "ingested_at", F.current_timestamp()
        )
        audit_df.write.format("delta").mode("append").save(
            str(delta_base / "artifact_audit_log")
        )
        return {
            "lakehouse_status": "ok",
            "lakehouse_path": str(delta_base),
            "lakehouse_reason": "spark_delta_write_success",
        }
    except Exception as exc:
        reason = "spark_unavailable_in_apps_runtime"
        msg = str(exc)
        if "JAVA_HOME" not in msg and "Java gateway process exited" not in msg:
            reason = "spark_or_delta_write_failed"
        try:
            import pandas as pd
            from deltalake.writer import write_deltalake

            scan_id = serializable["metrics"]["scan_id"]
            delta_base = artifact_root / "delta_live"
            delta_base.mkdir(parents=True, exist_ok=True)

            classified_rows = [
                dict(row, scan_id=scan_id)
                for row in serializable["classified_elements"]
            ]
            obligations_rows = [
                dict(row, scan_id=scan_id) for row in serializable["obligations"]
            ]
            conflicts_rows = [
                dict(row, scan_id=scan_id) for row in serializable["conflicts"]
            ]

            write_deltalake(
                str(delta_base / "classified_elements"),
                pd.DataFrame(classified_rows),
                mode="append",
            )
            write_deltalake(
                str(delta_base / "obligations"),
                pd.DataFrame(obligations_rows),
                mode="append",
            )
            if conflicts_rows:
                write_deltalake(
                    str(delta_base / "conflicts"),
                    pd.DataFrame(conflicts_rows),
                    mode="append",
                )

            audit_row = {
                "scan_id": scan_id,
                "business_name": business_name,
                "sector": sector,
                "language": language,
                "fields_scanned": serializable["metrics"]["fields_scanned"],
                "obligation_count": serializable["metrics"]["obligation_count"],
                "conflict_count": serializable["metrics"]["conflict_count"],
                "grounding_score": serializable["metrics"]["grounding_score"],
                "mllib_used": bool(serializable["metrics"].get("mllib_used", False)),
                "mllib_predictions": int(
                    serializable["metrics"].get("mllib_predictions", 0)
                ),
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
                "penalty_exposure_current_crore": serializable["metrics"][
                    "penalty_exposure_current_crore"
                ],
            }
            write_deltalake(
                str(delta_base / "artifact_audit_log"),
                pd.DataFrame([audit_row]),
                mode="append",
            )
            return {
                "lakehouse_status": "ok",
                "lakehouse_path": str(delta_base),
                "lakehouse_reason": "delta_rs_fallback_success",
            }
        except Exception as fallback_exc:
            return {
                "lakehouse_status": "skipped",
                "lakehouse_reason": reason,
                "lakehouse_error": f"{msg[:160]} | fallback_failed: {str(fallback_exc)[:160]}",
            }


@app.get("/api/health", response_model=HealthResponse)
def health() -> HealthResponse:
    return HealthResponse(status="ok")


@app.post("/api/scan")
async def scan(
    file: UploadFile = File(...),
    business_name: str = Form("Demo MSME"),
    sector: str = Form("fintech"),
    language: str = Form("English"),
) -> JSONResponse:
    if sector not in {"fintech", "healthtech", "general"}:
        raise HTTPException(status_code=400, detail="Invalid sector")

    suffix = Path(file.filename or "upload.sql").suffix.lower() or ".sql"
    if suffix not in {".sql", ".csv", ".json"}:
        raise HTTPException(status_code=400, detail="Unsupported file format")

    payload = await file.read()
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        tmp.write(payload)
        temp_path = Path(tmp.name)

    try:
        try:
            result, zip_path = pipeline.run(
                schema_path=temp_path,
                business_name=business_name,
                sector=sector,
                language=language,
                artifact_output_dir=artifact_root,
                require_mllib=REQUIRE_MLLIB,
                indian_api_key=SARVAM_API_KEY,
                use_spark=USE_SPARK_FOR_SCAN,
            )
        except RuntimeError as exc:
            raise HTTPException(status_code=503, detail=str(exc)) from exc
        serializable: dict[str, Any] = pipeline.to_serializable(result)
        serializable.update(
            _write_scan_to_lakehouse(serializable, business_name, sector, language)
        )
        serializable["download_url"] = f"/api/download/{result.metrics['scan_id']}"
        serializable["zip_name"] = zip_path.name
        return JSONResponse(serializable)
    finally:
        if temp_path.exists():
            temp_path.unlink(missing_ok=True)


@app.get("/api/download/{scan_id}")
def download(scan_id: str) -> FileResponse:
    zip_path = artifact_root / scan_id / "compliance_kit.zip"
    if not zip_path.exists():
        raise HTTPException(status_code=404, detail="Compliance kit not found")
    return FileResponse(
        path=zip_path, filename="compliance_kit.zip", media_type="application/zip"
    )


@app.get("/api/grievance")
def list_grievances() -> JSONResponse:
    if not grievance_log_path.exists():
        return JSONResponse({"items": []})
    items: list[dict[str, str]] = []
    for line in grievance_log_path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        items.append(json.loads(line))
    return JSONResponse({"items": items[-200:]})


@app.post("/api/grievance")
def create_grievance(payload: GrievanceRequest) -> JSONResponse:
    grievance_log_path.parent.mkdir(parents=True, exist_ok=True)
    with grievance_log_path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(payload.model_dump(), ensure_ascii=True) + "\n")
    return JSONResponse({"ok": True})


def _mount_frontend() -> None:
    dist_dir = ROOT_DIR / "web" / "dist"
    index_path = dist_dir / "index.html"

    @app.get("/", response_model=None)
    async def root():
        if index_path.exists():
            return FileResponse(index_path)
        return JSONResponse(
            status_code=503,
            content={
                "detail": "Frontend build missing. Run `cd web && npm run build` before deploy."
            },
        )

    if not dist_dir.exists():
        return

    @app.get("/{full_path:path}")
    async def spa(full_path: str) -> FileResponse:
        candidate = dist_dir / full_path
        if full_path and candidate.exists() and candidate.is_file():
            return FileResponse(candidate)
        return FileResponse(index_path)


_mount_frontend()


if __name__ == "__main__":
    import uvicorn

    port = int(__import__("os").environ.get("DATABRICKS_APP_PORT", "8000"))
    uvicorn.run("app.main:app", host="0.0.0.0", port=port)
