# DPDP Kavach Gap Audit

Date: 2026-03-29  
Source of truth: `hackathon.md` + `DPDP_Kavach_Architecture.md`

## 1) Mandatory Hackathon Requirements

| Requirement | Current Status | Evidence | Gap |
|---|---|---|---|
| Databricks as core | Partial | Spark + Delta outputs in `scripts/databricks_pipeline.py`; Databricks App deployed | Core app request path (`/api/scan`) runs pure Python pipeline, not Spark/Delta-first |
| AI central | Partial | PII/purpose classifier + grounding score pipeline | No MLlib training, no MLflow tracking, no FAISS embeddings pipeline, no Indian LLM inference wired |
| Prefer Indian models | Partial (declared) | Architecture/docs mention Param-1, Sarvam-m, IndicTrans2 | No runtime invocation of these models in code |
| Working demo reproducible | Yes | Local CLI + API + deployed Databricks App + tests passing | Need stronger demo evidence artifacts for judging (grievance persistence + explicit audit trail) |
| Databricks App / Notebook UI | Yes | FastAPI + Vite UI served as Databricks App | UI can be tightened for submission narrative only (non-critical) |

## 2) Architecture vs Implementation

### Implemented
- Discovery from `.sql`, `.csv`, `.json` inputs.
- PII classification via taxonomy + regex + heuristics.
- Obligation mapping and sector conflict detection.
- Artifact generation + ZIP packaging.
- Claim-level grounding score (heuristic similarity).
- Deployed Databricks App with working upload/scan/download flow.
- Spark job to persist `classified_elements`, `obligations`, `conflicts`, and `artifact_audit_log` as Delta outputs.

### Missing / Not Yet Implemented
- Input modes: GitHub repo scanner, API spec parser, guided questionnaire as first-class pipeline inputs.
- PySpark-first discovery/classification in online app path.
- Delta-backed knowledge layer tables (`dpdp_obligation_index`, `pii_taxonomy`, `sector_conflict`, `vendor_intelligence`) as live tables.
- ML pipeline: Spark MLlib model training + model store + MLflow experiment logging.
- Retrieval layer: FAISS index construction/query against DPDP corpus embeddings.
- Generation layer with Indian models (Param-1/Sarvam-m) and IndicTrans2 translation.
- DPA template generation per detected vendor.
- Penalty exposure calculator based on schedule/severity factors.
- Monitoring layer: schema watcher, retention monitor, and compliance tracker dashboards/jobs.
- Grievance intake persistence to backend audit log/Delta.

## 3) Risk to Judging

### High Risk
- “AI central” can be challenged as mostly rule-based unless ML/grounding evidence is strengthened in demo.
- “Databricks as core” can be challenged because interactive scan path does not execute Spark pipeline.

### Medium Risk
- Architecture promises many advanced capabilities that are not yet in code; judges may ask direct implementation questions.

### Low Risk
- Reproducibility and deployability are currently good (app running + tests passing).

## 4) Fastest Closure Plan (Execution Order)

1. Add missing high-visibility outputs: DPA artifact + penalty exposure metric in dashboard.
2. Persist grievance intake in backend and include in audit export.
3. Tighten README demo script to match actual implemented features only.
4. Optional stretch: wire `/api/scan?spark=true` path to run Spark Delta pipeline for stronger Databricks-core proof.
5. Optional stretch: add minimal MLflow logging during scan and expose run ID in UI.

## 5) Current Live Deployment Snapshot

- App name: `dpdp-kavach`
- URL: `https://dpdp-kavach-7474650615353088.aws.databricksapps.com`
- Last deployment status: `SUCCEEDED`
- App status: `RUNNING`
