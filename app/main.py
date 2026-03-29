from __future__ import annotations

import tempfile
import json
import os
from pathlib import Path
import sys
from typing import Any
from uuid import uuid4

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


class ChatRequest(BaseModel):
    message: str
    conversation_history: list[dict[str, str]] = []
    scan_context: dict[str, Any]
    language: str = "English"


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


@app.post("/api/chat")
def chat(payload: ChatRequest) -> JSONResponse:
    ctx = payload.scan_context
    elements = ctx.get("classified_elements", [])
    obligations = ctx.get("obligations", [])
    conflicts = ctx.get("conflicts", [])
    metrics = ctx.get("metrics", {})

    pii_summary = []
    for e in elements:
        cat = e.get("pii_category", "unknown")
        if cat != "non_pii":
            pii_summary.append(
                f"- {e.get('column_name', '?')} ({cat}) in table {e.get('table_name', '?')}"
            )

    obl_summary = []
    for o in obligations:
        obl_summary.append(
            f"- [{o.get('section', '?')}] {o.get('obligation_type', '?')}: {o.get('description', '')}"
        )

    conf_summary = []
    for c in conflicts:
        conf_summary.append(
            f"- {c.get('regulation', '?')} vs DPDP {c.get('dpdp_section', '?')}: {c.get('summary', '')}"
        )

    scan_info = f"""Compliance Scan Summary:
- Sector: {ctx.get("sector", "unknown")}
- Fields scanned: {metrics.get("fields_scanned", "?")}
- PII fields: {len(pii_summary)} (of types: {", ".join(sorted(set(e.get("pii_category", "?") for e in elements if e.get("pii_category", "?") != "non_pii"))) or "none"})
- Obligations triggered: {len(obligations)}
- Conflicts detected: {len(conflicts)}
- Estimated penalty exposure: ₹{metrics.get("penalty_exposure_current_crore", "?")} Crore

PII Fields Found ({len(pii_summary)}):
{chr(10).join(pii_summary) if pii_summary else "No PII fields detected."}

DPDP Obligations ({len(obl_summary)}):
{chr(10).join(obl_summary) if obl_summary else "No obligations triggered."}

Cross-Law Conflicts ({len(conf_summary)}):
{chr(10).join(conf_summary) if conf_summary else "No conflicts detected."}"""

    history_msgs = []
    for h in payload.conversation_history[-10:]:
        role = "assistant" if h.get("role") == "assistant" else "user"
        history_msgs.append({"role": role, "content": h.get("content", "")})

    lang = payload.language
    lang_instruction = "" if lang == "English" else f" Respond entirely in {lang}."

    system_prompt = (
        "You are a friendly DPDP Act compliance advisor for Indian MSMEs. "
        "You have access to the user's compliance scan results. Answer their questions clearly and helpfully. "
        "Use simple language — the user may not be a lawyer or technologist."
        f"{lang_instruction}\n\n{scan_info}"
    )

    messages = (
        [{"role": "system", "content": system_prompt}]
        + history_msgs
        + [{"role": "user", "content": payload.message}]
    )

    try:
        import urllib.request as _req

        batch_payload = json.dumps(
            {
                "model": os.environ.get("INDIAN_MODEL_NAME", "sarvam-m"),
                "messages": messages,
                "temperature": 0.4,
            }
        ).encode()
        req = _req.Request(
            "https://api.sarvam.ai/v1/chat/completions",
            data=batch_payload,
            headers={
                "Authorization": f"Bearer {SARVAM_API_KEY}",
                "Content-Type": "application/json",
            },
            method="POST",
        )
        with _req.urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read())
        reply = data["choices"][0]["message"]["content"].strip()
        return JSONResponse({"reply": reply})
    except Exception:
        return JSONResponse(
            {
                "reply": "Sorry, I couldn't generate a response right now. Please try again."
            }
        )


@app.post("/api/scan")
async def scan_schema(
    file: UploadFile = File(...),
    sector: str = Form(...),
    business_name: str = Form("My Organization"),
    language: str = Form("English"),
) -> JSONResponse:
    if not file.filename:
        return JSONResponse({"error": "No file provided"}, status_code=400)
    suffix = Path(file.filename).suffix.lower()
    if suffix not in (".sql", ".csv", ".json"):
        return JSONResponse(
            {"error": "Unsupported file type. Use .sql, .csv, or .json"},
            status_code=400,
        )

    with tempfile.NamedTemporaryFile(suffix=suffix, delete=False, mode="w+") as tmp:
        content = await file.read()
        if isinstance(content, bytes):
            content = content.decode("utf-8", errors="replace")
        tmp.write(content)
        tmp_path = Path(tmp.name)

    try:
        scan_run_id = str(uuid4().hex[:8])
        artifact_dir = artifact_root / f"scan_{scan_run_id}"
        artifact_dir.mkdir(parents=True, exist_ok=True)

        result, _ = pipeline.run(
            schema_path=tmp_path,
            business_name=business_name,
            sector=sector,
            language=language,
            artifact_output_dir=artifact_dir,
            require_mllib=REQUIRE_MLLIB,
            indian_api_key=SARVAM_API_KEY,
            use_spark=USE_SPARK_FOR_SCAN,
        )

        from dpdp_kavach.pipeline import CompliancePipeline

        serializable = CompliancePipeline.to_serializable(result)
        serializable["sector"] = sector
        return JSONResponse(serializable)
    except Exception as exc:
        return JSONResponse({"error": str(exc)}, status_code=500)
    finally:
        tmp_path.unlink(missing_ok=True)


@app.get("/api/grievance")
def get_grievance_info() -> JSONResponse:
    log_path = grievance_log_path
    if not log_path.exists():
        return JSONResponse({"requests": [], "count": 0})
    try:
        records = []
        with open(log_path) as f:
            for line in f:
                line = line.strip()
                if line:
                    try:
                        records.append(json.loads(line))
                    except Exception:
                        pass
        return JSONResponse({"requests": records, "count": len(records)})
    except Exception:
        return JSONResponse({"requests": [], "count": 0, "error": "Could not read log"})


@app.post("/api/grievance")
def submit_grievance(payload: GrievanceRequest) -> JSONResponse:
    record = payload.model_dump()
    record["timestamp"] = __import__("datetime").datetime.utcnow().isoformat()
    try:
        with open(grievance_log_path, "a") as f:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")
        return JSONResponse({"status": "logged", "id": record["timestamp"]})
    except Exception as exc:
        return JSONResponse({"status": "error", "message": str(exc)}, status_code=500)


pipeline = CompliancePipeline(base_dir=ROOT_DIR / "src" / "dpdp_kavach")
artifact_root = ROOT_DIR / "artifacts"
artifact_root.mkdir(parents=True, exist_ok=True)
grievance_log_path = artifact_root / "grievance_log.jsonl"
REQUIRE_MLLIB = os.environ.get("REQUIRE_MLLIB", "0") == "1"
USE_SPARK_FOR_SCAN = os.environ.get("USE_SPARK_FOR_SCAN", "1") == "1"
SARVAM_API_KEY = "sk_wuwzo5h0_N0yrZFaJw0T0uKjciZU1iMfz"


def _translate_text(text: str, target_lang: str) -> tuple[str, str]:
    if not text.strip() or target_lang == "English":
        return text, "ok"
    try:
        import json, urllib.request

        payload = json.dumps(
            {
                "model": os.environ.get("INDIAN_MODEL_NAME", "sarvam-m"),
                "messages": [
                    {
                        "role": "system",
                        "content": f"You are a professional translator. Translate the following text to {target_lang}. Preserve all formatting (markdown, line breaks, bullets, code blocks). Return ONLY the translation, no explanations, no quotes.",
                    },
                    {"role": "user", "content": text},
                ],
                "temperature": 0.1,
            }
        ).encode()
        req = urllib.request.Request(
            "https://api.sarvam.ai/v1/chat/completions",
            data=batch_payload,
            headers={
                "Authorization": f"Bearer {SARVAM_API_KEY}",
                "Content-Type": "application/json",
            },
            method="POST",
        )
        with _req.urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read())
        reply = data["choices"][0]["message"]["content"].strip()
        return JSONResponse({"reply": reply})
    except Exception:
        return JSONResponse(
            {
                "reply": "Sorry, I couldn't generate a response right now. Please try again."
            }
        )


TRANSLATIONS: dict[str, dict[str, str]] = {
    "English": {
        "app_title": "DPDP Kavach",
        "tagline": "DPDP Act Compliance Scanner for Indian Businesses",
        "hero_headline": "Automate Your DPDP Act Compliance",
        "hero_sub": "Scan your database schema, classify PII fields, map legal obligations, detect cross-law conflicts, and generate a ready-to-use compliance kit — all in one place.",
        "how_it_works": "How It Works",
        "step1_title": "Upload Schema",
        "step1_desc": "Upload your SQL, CSV, or JSON schema file. The scanner reads your table and column metadata to understand what personal data you hold.",
        "step2_title": "Classify & Map",
        "step2_desc": "Our engine classifies each field as PII or non-PII, identifies the category (name, health, financial, etc.), and maps obligations under the DPDP Act.",
        "step3_title": "Generate Kit",
        "step3_desc": "Get a downloadable ZIP with privacy notice, consent form, data deletion SOP, and Section 11–14 request intake — in your chosen language.",
        "what_is_dpdp": "What is the DPDP Act?",
        "dpdp_desc": "The Digital Personal Data Protection Act, 2023 (DPDP Act) is India's landmark data protection law. It governs how businesses collect, store, and process personal data of Indian citizens. Non-compliance can attract fines up to ₹250 Crore.",
        "key_provisions": "Key Provisions",
        "provision1": "Section 4 — Lawful Purpose: Data can only be collected for specified, lawful purposes.",
        "provision2": "Section 6 — Consent: Consent must be free, specific, informed, and unambiguous.",
        "provision3": "Section 8 — Data Accuracy: Businesses must keep personal data accurate and up to date.",
        "provision4": "Section 11 — Right to Erasure: Individuals can demand deletion of their personal data.",
        "provision5": "Sections 13–14 — Grievance Redressal: Every business must have a designated grievance officer.",
        "sectors_served": "Industries Covered",
        "stats_fields": "Fields Scanned",
        "stats_obligations": "Obligations Mapped",
        "stats_conflicts": "Conflicts Detected",
        "stats_kit": "Compliance Kit Generated",
        "upload_cta": "Scan My Schema →",
        "upload_placeholder": "Drop your .sql, .csv, or .json schema file",
        "sidebar_config": "Scan Configuration",
        "sidebar_risk": "Risk Overview",
        "sidebar_exposure": "Est. Penalty Exposure",
        "sidebar_risk_score": "Risk Score",
        "sidebar_grounding": "Grounding Confidence",
        "sidebar_fields": "Fields",
        "sidebar_obligations": "Obligations",
        "sidebar_conflicts": "Conflicts",
        "section_inventory": "Data Inventory",
        "section_obligations": "Obligations",
        "section_conflicts": "Conflicts",
        "section_artifacts": "Artifacts",
        "section_grievance": "Grievance",
        "no_conflicts": "No conflicts detected for this sector",
        "no_obligations": "No obligations triggered",
        "download_kit": "Download Kit",
        "download_zip": "Download ZIP",
        "submit": "Submit",
        "grievance_title": "Grievance & Data Requests",
        "grievance_sub": "Section 11–14 request intake — Access, Correction, Erasure, Nomination",
        "principal_id": "Data Principal ID",
        "no_requests": "No requests submitted yet",
        "ready_title": "DPDP Compliance Scanner",
        "ready_sub": "Upload your database schema (SQL, CSV, or JSON) to discover PII fields, map DPDP obligations, detect cross-law conflicts, and generate your compliance kit.",
        "result_exposure": "Penalty Exposure",
        "result_fields_scanned": "Fields Scanned",
        "result_obligations": "Obligations",
        "result_conflicts": "Conflicts",
        "result_grounding": "Grounding Score",
        "scan_failed": "Scan failed",
        "upload_first": "Upload a .sql/.csv/.json schema file first",
    },
    "Hindi": {
        "app_title": "DPDP कवच",
        "tagline": "भारतीय व्यापार के लिए DPDP अधिनियम अनुपालन स्कैनर",
        "hero_headline": "अपने DPDP अधिनियम अनुपालन को स्वचालित करें",
        "hero_sub": "अपना डेटाबेस स्कीमा अपलोड करें, PII फ़ील्ड को वर्गीकृत करें, कानूनी दायित्वों को मैप करें, क्रॉस-लॉ संघर्षों का पता लगाएं, और तैयार अनुपालन किट डाउनलोड करें — सब कुछ एक ही जगह।",
        "how_it_works": "यह कैसे काम करता है",
        "step1_title": "स्कीमा अपलोड करें",
        "step1_desc": "अपनी SQL, CSV, या JSON स्कीमा फ़ाइल अपलोड करें। स्कैनर आपकी टेबल और कॉलम मेटाडेटा पढ़कर समझता है कि आप कौन सा व्यक्तिगत डेटा रखते हैं।",
        "step2_title": "वर्गीकृत करें और मैप करें",
        "step2_desc": "हमारा इंजन प्रत्येक फ़ील्ड को PII या non-PII के रूप में वर्गीकृत करता है, श्रेणी (नाम, स्वास्थ्य, वित्तीय, आदि) की पहचान करता है, और DPDP अधिनियम के तहत दायित्वों को मैप करता है।",
        "step3_title": "किट बनाएं",
        "step3_desc": "गोपनीयता नोटिस, सहमति प्रपत्र, डेटा विलोपन SOP, और सेक्शन 11–14 अनुरोध इनटेक सहित एक डाउनलोड करने योग्य ZIP प्राप्त करें — आपकी पसंदीदा भाषा में।",
        "what_is_dpdp": "DPDP अधिनियम क्या है?",
        "dpdp_desc": "डिजिटल पर्सनल डेटा प्रोटेक्शन अधिनियम, 2023 (DPDP अधिनियम) भारत का ऐतिहासिक डेटा संरक्षण कानून है। यह व्यवसायों के लिए भारतीय नागरिकों के व्यक्तिगत डेटा के संग्रह, भंडारण और प्रसंस्करण को नियंत्रित करता है। अनुपालन न करने पर ₹250 करोड़ तक का जुर्माना लगाया जा सकता है।",
        "key_provisions": "प्रमुख प्रावधान",
        "provision1": "धारा 4 — वैध उद्देश्य: डेटा केवल निर्दिष्ट, वैध उद्देश्यों के लिए एकत्र किया जा सकता है।",
        "provision2": "धारा 6 — सहमति: सहमति स्वतंत्र, विशिष्ट, सूचित और स्पष्ट होनी चाहिए।",
        "provision3": "धारा 8 — डेटा सटीकता: व्यवसायों को व्यक्तिगत डेटा सही और अद्यतन रखना होगा।",
        "provision4": "धारा 11 — विलोपन का अधिकार: व्यक्ति अपने व्यक्तिगत डेटा के विलोपन की मांग कर सकते हैं।",
        "provision5": "धारा 13–14 — शिकायत निवारण: प्रत्येक व्यवसाय के पास एक नामित शिकायत अधिकारी होना चाहिए।",
        "sectors_served": "उद्योग",
        "stats_fields": "फ़ील्ड स्कैन किए गए",
        "stats_obligations": "दायित्व मैप किए गए",
        "stats_conflicts": "संघर्ष पाए गए",
        "stats_kit": "अनुपालन किट बनाई गई",
        "upload_cta": "मेरा स्कीमा स्कैन करें →",
        "upload_placeholder": "अपनी .sql, .csv, या .json स्कीमा फ़ाइल छोड़ें",
        "sidebar_config": "स्कैन कॉन्फ़िगरेशन",
        "sidebar_risk": "जोखिम अवलोकन",
        "sidebar_exposure": "अनुमानित जुर्माना",
        "sidebar_risk_score": "जोखिम स्कोर",
        "sidebar_grounding": "ग्राउंडिंग विश्वास",
        "sidebar_fields": "फ़ील्ड",
        "sidebar_obligations": "दायित्व",
        "sidebar_conflicts": "संघर्ष",
        "section_inventory": "डेटा इन्वेंट्री",
        "section_obligations": "दायित्व",
        "section_conflicts": "संघर्ष",
        "section_artifacts": "आर्टिफैक्ट्स",
        "section_grievance": "शिकायत",
        "no_conflicts": "इस क्षेत्र के लिए कोई संघर्ष नहीं पाया गया",
        "no_obligations": "कोई दायित्व ट्रिगर नहीं हुआ",
        "download_kit": "किट डाउनलोड करें",
        "download_zip": "ZIP डाउनलोड करें",
        "submit": "जमा करें",
        "grievance_title": "शिकायत और डेटा अनुरोध",
        "grievance_sub": "धारा 11–14 अनुरोध इनटेक — एक्सेस, सुधार, विलोपन, नामांकन",
        "principal_id": "डेटा प्रिंसिपल आईडी",
        "no_requests": "अभी तक कोई अनुरोध नहीं",
        "ready_title": "DPDP अनुपालन स्कैनर",
        "ready_sub": "PII फ़ील्ड खोजने, DPDP दायित्वों को मैप करने, क्रॉस-लॉ संघर्षों का पता लगाने और अपनी अनुपालन किट बनाने के लिए अपना डेटाबेस स्कीमा (SQL, CSV, या JSON) अपलोड करें।",
        "result_exposure": "जुर्माना",
        "result_fields_scanned": "फ़ील्ड स्कैन",
        "result_obligations": "दायित्व",
        "result_conflicts": "संघर्ष",
        "result_grounding": "ग्राउंडिंग स्कोर",
        "scan_failed": "स्कैन विफल",
        "upload_first": "पहले .sql/.csv/.json स्कीमा फ़ाइल अपलोड करें",
    },
    "Bengali": {
        "app_title": "DPDP কবচ",
        "tagline": "ভারতীয় ব্যবসার জন্য DPDP আইন সম্মতি স্ক্যানার",
        "hero_headline": "আপনার DPDP আইন সম্মতি স্বয়ংক্রিয় করুন",
        "hero_sub": "আপনার ডাটাবেস স্কিমা আপলোড করুন, PII ফিল্ড শ্রেণীবদ্ধ করুন, আইনি বাধ্যবাধকতা ম্যাপ করুন, ক্রস-লॉ দ্বন্দ্ব সনাক্ত করুন এবং প্রস্তুত ব্যবহারযোগ্য সম্মতি কিট ডাউনলোড করুন — সব এক জায়গায়।",
        "how_it_works": "এটি কীভাবে কাজ করে",
        "step1_title": "স্কিমা আপলোড করুন",
        "step1_desc": "আপনার SQL, CSV, বা JSON স্কিমা ফাইল আপলোড করুন। স্ক্যানার আপনার টেবিল এবং কলাম মেটাডেটা পড়ে বোঝে আপনি কোন ব্যক্তিগত ডেটা রাখেন।",
        "step2_title": "শ্রেণীবদ্ধ করুন ও ম্যাপ করুন",
        "step2_desc": "আমাদের ইঞ্জিন প্রতিটি ফিল্ডকে PII বা non-PII হিসাবে শ্রেণীবদ্ধ করে, বিভাগ (নাম, স্বাস্থ্য, আর্থিক, ইত্যাদি) চিহ্নিত করে এবং DPDP আইনের অধীনে বাধ্যবাধকতা ম্যাপ করে।",
        "step3_title": "কিট তৈরি করুন",
        "step3_desc": "গোপনীয়তা বিজ্ঞপ্তি, সম্মতি ফর্ম, ডেটা মুছে ফেলার SOP এবং ধারা 11–14 অনুরোধ গ্রহণ সহ একটি ডাউনলোডযোগ্য ZIP পান — আপনার পছন্দের ভাষায়।",
        "what_is_dpdp": "DPDP আইন কী?",
        "dpdp_desc": "ডিজিটাল পার্সোনাল ডেটা প্রোটেকশন অ্যাক্ট, 2023 (DPDP আইন) হলো ভারতের যুগান্তকারী ডেটা সুরক্ষা আইন। এটি ব্যবসায়ের জন্য ভারতীয় নাগরিকদের ব্যক্তিগত ডেটা সংগ্রহ, সংরক্ষণ এবং প্রক্রিয়াকরণ নিয়ন্ত্রণ করে। অ-সম্মতিতে ₹250 কোটি পর্যন্ত জরিমানা হতে পারে।",
        "key_provisions": "মূল বিধান",
        "provision1": "ধারা 4 — বৈধ উদ্দেশ্য: ডেটা কেবল নির্দিষ্ট, বৈধ উদ্দেশ্যে সংগ্রহ করা যেতে পারে।",
        "provision2": "ধারা 6 — সম্মতি: সম্মতি অবশ্যই বিনামূল্যে, নির্দিষ্ট, অবহিত এবং স্পষ্ট হতে হবে।",
        "provision3": "ধারা 8 — ডেটা সঠিকতা: ব্যবসাকে ব্যক্তিগত ডেটা সঠিক এবং আপডেট রাখতে হবে।",
        "provision4": "ধারা 11 — মুছে ফেলার অধিকার: ব্যক্তিরা তাদের ব্যক্তিগত ডেটা মুছে ফেলার দাবি করতে পারেন।",
        "provision5": "ধারা 13–14 — অভিযোগ প্রতিকার: প্রতিটি ব্যবসায় একজন মনোনীত অভিযোগ কর্মকর্তা থাকতে হবে।",
        "sectors_served": "শিল্প",
        "stats_fields": "ফিল্ড স্ক্যান করা হয়েছে",
        "stats_obligations": "বাধ্যবাধকতা ম্যাপ করা হয়েছে",
        "stats_conflicts": "দ্বন্দ্ব সনাক্ত করা হয়েছে",
        "stats_kit": "সম্মতি কিট তৈরি হয়েছে",
        "upload_cta": "আমার স্কিমা স্ক্যান করুন →",
        "upload_placeholder": "আপনার .sql, .csv, বা .json স্কিমা ফাইল ফেলুন",
        "sidebar_config": "স্ক্যান কনফিগারেশন",
        "sidebar_risk": "ঝুঁকির ওভারভিউ",
        "sidebar_exposure": "আনুমানিক জরিমানা",
        "sidebar_risk_score": "ঝুঁকি স্কোর",
        "sidebar_grounding": "গ্রাউন্ডিং আত্মবিশ্বাস",
        "sidebar_fields": "ফিল্ড",
        "sidebar_obligations": "বাধ্যবাধকতা",
        "sidebar_conflicts": "দ্বন্দ্ব",
        "section_inventory": "ডেটা ইনভেন্টরি",
        "section_obligations": "বাধ্যবাধকতা",
        "section_conflicts": "দ্বন্দ্ব",
        "section_artifacts": "আর্টিফ্যাক্টস",
        "section_grievance": "অভিযোগ",
        "no_conflicts": "এই খাতে কোনো দ্বন্দ্ব সনাক্ত হয়নি",
        "no_obligations": "কোনো বাধ্যবাধকতা ট্রিগার হয়নি",
        "download_kit": "কিট ডাউনলোড করুন",
        "download_zip": "ZIP ডাউনলোড করুন",
        "submit": "জমা দিন",
        "grievance_title": "অভিযোগ ও ডেটা অনুরোধ",
        "grievance_sub": "ধারা 11–14 অনুরোধ গ্রহণ — অ্যাক্সেস, সংশোধন, বিলোপ, মনোনয়ন",
        "principal_id": "ডেটা প্রিন্সিপাল আইডি",
        "no_requests": "এখনও কোনো অনুরোধ জমা হয়নি",
        "ready_title": "DPDP সম্মতি স্ক্যানার",
        "ready_sub": "PII ফিল্ড আবিষ্কার, DPDP বাধ্যবাধকতা ম্যাপ, ক্রস-লॉ দ্বন্দ্ব সনাক্ত এবং আপনার সম্মতি কিট তৈরি করতে আপনার ডাটাবেস স্কিমা (SQL, CSV, বা JSON) আপলোড করুন।",
        "result_exposure": "জরিমানা",
        "result_fields_scanned": "ফিল্ড স্ক্যান",
        "result_obligations": "বাধ্যবাধকতা",
        "result_conflicts": "দ্বন্দ্ব",
        "result_grounding": "গ্রাউন্ডিং স্কোর",
        "scan_failed": "স্ক্যান ব্যর্থ হয়েছে",
        "upload_first": "প্রথমে .sql/.csv/.json স্কিমা ফাইল আপলোড করুন",
    },
    "Assamese": {
        "app_title": "DPDP কবচ",
        "tagline": "ভারতীয় ব্যৱসায়ৰ বাবে DPDP আইন সম্মতি স্ক্যানাৰ",
        "hero_headline": "আপোনাৰ DPDP আইন সম্মতি স্বয়ংক্রিয় কৰক",
        "hero_sub": "আপোনাৰ ডাটাবেচ স্কিমা আপলোড কৰক, PII ফিল্ড শ্রেণীবদ্ধ কৰক, আইনী বাধ্যবাধকতা ম্যাপ কৰক, ক্রস-লॉ দ্বন্দ্ব সনাক্ত কৰক আৰু প্রস্তুত ব্যৱহাৰযোগ্য সম্মতি কিট ডাউনলোড কৰক।",
        "how_it_works": "এয়া কেনেকৈ কাম কৰে",
        "step1_title": "স্কিমা আপলোড কৰক",
        "step1_desc": "আপোনাৰ SQL, CSV, বা JSON স্কিমা ফাইল আপলোড কৰক। স্ক্যানাৰে আপোনাৰ টেবিল আৰু কলাম মেটাডাটা পঢ়ি বুজাৱে আপুনি কি ব্যক্তিগত ডাটা ৰাখে।",
        "step2_title": "শ্রেণীবদ্ধ কৰক আৰু ম্যাপ কৰক",
        "step2_desc": "আমাৰ ইঞ্জিনে প্ৰতিটো ফিল্ডক PII বা non-PII হিচাপে শ্রেণীবদ্ধ কৰে, বিভাগ (নাম, স্বাস্থ্য, আর্থিক, আদি) চিহ্নিত কৰে আৰু DPDP আইনৰ অধীন বাধ্যবাধকতা ম্যাপ কৰে।",
        "step3_title": "কিট তৈয়াৰ কৰক",
        "step3_desc": "গোপনীয়তা বিজ্ঞপ্তি, সম্মতি ফর্ম, ডাটা মুছি ফেলাৰ SOP আৰু ধারা 11–14 অনুৰোধ গ্রহণ সহ এটা ডাউনলোডযোগ্য ZIP বিল পাব।",
        "what_is_dpdp": "DPDP আইন কি?",
        "dpdp_desc": "ডিজিটাল পার্সোনাল ডাটা প্রটেকশন অ্যাক্ট, 2023 (DPDP আইন) ভাৰতৰ যুগান্তকাৰী ডাটা সুৰক্ষা আইন। অ-সম্মতিত ₹250 কোটি পর্যন্ত জৰিমানা হ'ব পাৰে।",
        "key_provisions": "মূল বিধান",
        "provision1": "ধারা 4 — বৈধ উদ্দেশ্য",
        "provision2": "ধারা 6 — সম্মতি",
        "provision3": "ধারা 8 — ডাটা সঠিকতা",
        "provision4": "ধারা 11 — মুছি ফেলাৰ অধিকাৰ",
        "provision5": "ধারা 13–14 — অভিযোগ প্রতিকাৰ",
        "sectors_served": "উদ্যোগ",
        "stats_fields": "ফিল্ড স্ক্যান কৰা হৈছে",
        "stats_obligations": "বাধ্যবাধকতা ম্যাপ কৰা হৈছে",
        "stats_conflicts": "দ্বন্দ্ব সনাক্ত কৰা হৈছে",
        "stats_kit": "সম্মতি কিট তৈয়াৰ হৈছে",
        "upload_cta": "মোৰ স্কিমা স্ক্যান কৰক →",
        "upload_placeholder": ".sql, .csv, বা .json স্কিমা ফাইল এৰক",
        "sidebar_config": "স্ক্যান কনফিগাৰেশন",
        "sidebar_risk": "ঝুঁকিৰ ওভাৰভিউ",
        "sidebar_exposure": "আনুমানিক জৰিমানা",
        "sidebar_risk_score": "ঝুঁকি স্কোৰ",
        "sidebar_grounding": "গ্রাউন্ডিং বিশ্বাস",
        "sidebar_fields": "ফিল্ড",
        "sidebar_obligations": "বাধ্যবাধকতা",
        "sidebar_conflicts": "দ্বন্দ্ব",
        "section_inventory": "ডাটা ইনভেন্টৰি",
        "section_obligations": "বাধ্যবাধকতা",
        "section_conflicts": "দ্বন্দ্ব",
        "section_artifacts": "আর্টিফ্যাক্টস",
        "section_grievance": "অভিযোগ",
        "no_conflicts": "এই খণ্ডত কোনো দ্বন্দ্ব সনাক্ত হোৱা নাই",
        "no_obligations": "কোনো বাধ্যবাধকতা ট্রিগাৰ হোৱা নাই",
        "download_kit": "কিট ডাউনলোড কৰক",
        "download_zip": "ZIP ডাউনলোড কৰক",
        "submit": "জমা দিন",
        "grievance_title": "অভিযোগ আৰু ডাটা অনুৰোধ",
        "grievance_sub": "ধারা 11–14 অনুৰোধ গ্রহণ — এক্সেস, সংশোধন, বিলোপ, মনোনয়ন",
        "principal_id": "ডাটা প্রিন্সিপাল আইডি",
        "no_requests": "এতিয়ালৈকে কোনো অনুৰোধ জমা হোৱা নাই",
        "ready_title": "DPDP সম্মতি স্ক্যানাৰ",
        "ready_sub": "PII ফিল্ড আবিষ্কাৰ, DPDP বাধ্যবাধকতা ম্যাপ, ক্রস-লॉ দ্বন্দ্ব সনাক্ত আৰু আপোনাৰ সম্মতি কিট তৈয়াৰ কৰিবলৈ আপোনাৰ ডাটাবেচ স্কিমা আপলোড কৰক।",
        "result_exposure": "জৰিমানা",
        "result_fields_scanned": "ফিল্ড স্ক্যান",
        "result_obligations": "বাধ্যবাধকতা",
        "result_conflicts": "দ্বন্দ্ব",
        "result_grounding": "গ্রাউন্ডিং স্কোৰ",
        "scan_failed": "স্ক্যান ব্যর্থ হৈছে",
        "upload_first": "প্রথমে .sql/.csv/.json স্কিমা ফাইল আপলোড কৰক",
    },
    "Gujarati": {
        "app_title": "DPDP કવચ",
        "tagline": "ભારતીય વ્યવસાય માટે DPDP અધિનિયમ અનુપાલન સ્કેનર",
        "hero_headline": "તમારા DPDP અધિનિયમ અનુપાલનને સ્વચાલિત કરો",
        "hero_sub": "તમારું ડેટાબેઝ સ્કીમા અપલોડ કરો, PII ફીલ્ડને વર્ગીકૃત કરો, કાયદેસર દાયિત્વોને મેપ કરો, ક્રૉસ-લૉ સંઘર્ષો શોધો અને તૈયાર અનુપાલન કિટ ડાઉનલોડ કરો.",
        "what_is_dpdp": "DPDP અધિનિયમ શું છે?",
        "dpdp_desc": "ડિજિટલ પર્સનલ ડેટા પ્રોટેક્શન એક્ટ, 2023 (DPDP એક્ટ) ભારતનો ઐતિહાસિક ડેટા સંરક્ષણ કાયદો છે. અ-અનુપાલનમાં ₹250 કરોડ સુધીનો દંડ થઈ શકે છે.",
        "key_provisions": "મુખ્ય જોગવાઈઓ",
        "provision1": "કલમ 4 — વૈધ હેતુ",
        "provision2": "કલમ 6 — સંમતિ",
        "provision3": "કલમ 8 — ડેટા ચોકસાઈ",
        "provision4": "કલમ 11 — ભૂંસવાનો અધિકાર",
        "provision5": "કલમ 13–14 — ફરિયાદ નિવારણ",
        "how_it_works": "તે કેવી રીતે કાર્ય કરે છે",
        "step1_title": "સ્કીમા અપલોડ કરો",
        "step1_desc": "તમારી SQL, CSV, અથવા JSON સ્કીમા ફાઇલ અપલોડ કરો.",
        "step2_title": "વર્ગીકૃત કરો અને મેપ કરો",
        "step2_desc": "અમારો એન્જિન દરેક ફીલ્ડને PII અથવા non-PII તરીકે વર્ગીકૃત કરે છે.",
        "step3_title": "કિટ બનાવો",
        "step3_desc": "ડાઉનલોડ કરી શકાય તેવો ZIP મેળવો.",
        "sectors_served": "ઉદ્યોગો",
        "stats_fields": "ફીલ્ડ સ્કેન થયા",
        "stats_obligations": "દાયિત્વો મેપ થયા",
        "stats_conflicts": "સંઘર્ષો મળ્યા",
        "stats_kit": "અનુપાલન કિટ બની",
        "upload_cta": "મારું સ્કીમા સ્કેન કરો →",
        "upload_placeholder": ".sql, .csv, અથવા .json સ્કીમા ફાઇલ મૂકો",
        "sidebar_config": "સ્કેન રૂપરેખા",
        "sidebar_risk": "જોખમ ઝાંકી",
        "sidebar_exposure": "અંદાજિત દંડ",
        "sidebar_risk_score": "જોખમ સ્કોર",
        "sidebar_grounding": "ગ્રાઉન્ડિંગ વિશ્વાસ",
        "sidebar_fields": "ફીલ્ડ",
        "sidebar_obligations": "દાયિત્વો",
        "sidebar_conflicts": "સંઘર્ષો",
        "section_inventory": "ડેટા ઇન્વેન્ટરી",
        "section_obligations": "દાયિત્વો",
        "section_conflicts": "સંઘર્ષો",
        "section_artifacts": "આર્ટિફેક્ટ્સ",
        "section_grievance": "ફરિયાદ",
        "no_conflicts": "આ ક્ષેત્ર માટે કોઈ સંઘર્ષ શોધાયો નથી",
        "no_obligations": "કોઈ દાયિત્વ ટ્રિગર થયું નથી",
        "download_kit": "કિટ ડાઉનલોડ કરો",
        "download_zip": "ZIP ડાઉનલોડ કરો",
        "submit": "સબમિટ",
        "grievance_title": "ફરિયાદ અને ડેટા વિનંતીઓ",
        "grievance_sub": "કલમ 11–14 વિનંતી ઇનટેક — ઍક્સેસ, સુધારો, ભૂંસવું, નામાંકન",
        "principal_id": "ડેટા પ્રિન્સિપલ આઈડી",
        "no_requests": "અત્યાર સુધી કોઈ વિનંતી નથી",
        "ready_title": "DPDP અનુપાલન સ્કેનર",
        "ready_sub": "PII ફીલ્ડ શોધવા, DPDP દાયિત્વો મેપ કરવા, ક્રૉસ-લૉ સંઘર્ષો શોધવા અને તમારી અનુપાલન કિટ બનાવવા માટે તમારું ડેટાબેઝ સ્કીમા અપલોડ કરો.",
        "result_exposure": "દંડ",
        "result_fields_scanned": "ફીલ્ડ સ્કેન",
        "result_obligations": "દાયિત્વો",
        "result_conflicts": "સંઘર્ષો",
        "result_grounding": "ગ્રાઉન્ડિંગ સ્કોર",
        "scan_failed": "સ્કેન નિષ્ફળ",
        "upload_first": "પહેલાં .sql/.csv/.json સ્કીમા ફાઇલ અપલોડ કરો",
    },
    "Kannada": {
        "app_title": "DPDP ಕವಚ",
        "tagline": "ಭಾರತೀಯ ವ್ಯಾಪಾರಕ್ಕಾಗಿ DPDP ಕಾನೂನು ಅನುಪಾಲನ ಸ್ಕ್ಯಾನರ್",
        "hero_headline": "ನಿಮ್ಮ DPDP ಕಾನೂನು ಅನುಪಾಲನೆಯನ್ನು ಸ್ವಯಂಚಾಲಿತಗೊಳಿಸಿ",
        "hero_sub": "ನಿಮ್ಮ ಡೇಟಾಬೇಸ್ ಸ್ಕೀಮಾ ಅಪ್‌ಲೋಡ್ ಮಾಡಿ, PII ಫೀಲ್ಡ್‌ಗಳನ್ನು ವರ್ಗೀಕರಿಸಿ, ಕಾನೂನು ಬಾಧ್ಯತೆಗಳನ್ನು ಮ್ಯಾಪ್ ಮಾಡಿ, ಕ್ರಾಸ್-ಲಾ ಘರ್ಷಣೆಗಳನ್ನು ಪತ್ತೆಹಚ್ಚಿ ಮತ್ತು ಡೌನ್‌ಲೋಡ್ ಮಾಡಬಹುದಾದ ಅನುಪಾಲನ ಕಿಟ್ ಪಡೆಯಿರಿ.",
        "what_is_dpdp": "DPDP ಕಾಯ್ದೆ ಎಂದರೇನು?",
        "dpdp_desc": "ಡಿಜಿಟಲ್ ಪರ್ಸನಲ್ ಡೇಟಾ ಪ್ರೊಟೆಕ್ಷನ್ ಆಕ್ಟ್, 2023 (DPDP ಆಕ್ಟ್) ಭಾರತದ ಸ್ಮರಣೀಯ ಡೇಟಾ ಸಂರಕ್ಷಣಾ ಕಾನೂನು. ಅನುಪಾಲನ ವಿಫಲತೆಯು ₹250 ಕೋಟಿ ದಂಡಕ್ಕೆ ಕಾರಣವಾಗಬಹುದು.",
        "key_provisions": "ಪ್ರಮುಖ ನಿಬಂಧನೆಗಳು",
        "provision1": "ಸೆಕ್ಷನ್ 4 — ವೈಧ ಉದ್ದೇಶ",
        "provision2": "ಸೆಕ್ಷನ್ 6 — ಒಪ್ಪಿಗೆ",
        "provision3": "ಸೆಕ್ಷನ್ 8 — ಡೇಟಾ ನಿಖರತೆ",
        "provision4": "ಸೆಕ್ಷನ್ 11 — ಅಳಿಸುವಿಕೆಯ ಹಕ್ಕು",
        "provision5": "ಸೆಕ್ಷನ್ 13–14 — ದೂರು ಪರಿಹಾರ",
        "how_it_works": "ಇದು ಹೇಗೆ ಕೆಲಸ ಮಾಡುತ್ತದೆ",
        "step1_title": "ಸ್ಕೀಮಾ ಅಪ್‌ಲೋಡ್ ಮಾಡಿ",
        "step1_desc": "ನಿಮ್ಮ SQL, CSV, ಅಥವಾ JSON ಸ್ಕೀಮಾ ಫೈಲ್ ಅಪ್‌ಲೋಡ್ ಮಾಡಿ.",
        "step2_title": "ವರ್ಗೀಕರಿಸಿ ಮತ್ತು ಮ್ಯಾಪ್ ಮಾಡಿ",
        "step2_desc": "ನಮ್ಮ ಎಂಜಿನ್ ಪ್ರತಿಯೊಂದು ಫೀಲ್ಡ್ ಅನ್ನು PII ಅಥವಾ non-PII ಆಗಿ ವರ್ಗೀಕರಿಸುತ್ತದೆ.",
        "step3_title": "ಕಿಟ್ ರಚಿಸಿ",
        "step3_desc": "ಡೌನ್‌ಲೋಡ್ ಮಾಡಬಹುದಾದ ZIP ಪಡೆಯಿರಿ.",
        "sectors_served": "ಕೈಗಾರಿಕೆಗಳು",
        "stats_fields": "ಫೀಲ್ಡ್‌ಗಳು ಸ್ಕ್ಯಾನ್ ಆಗಿವೆ",
        "stats_obligations": "ಬಾಧ್ಯತೆಗಳು ಮ್ಯಾಪ್ ಆಗಿವೆ",
        "stats_conflicts": "ಘರ್ಷಣೆಗಳು ಪತ್ತೆಯಾಗಿವೆ",
        "stats_kit": "ಅನುಪಾಲನ ಕಿಟ್ ರಚಿತವಾಗಿದೆ",
        "upload_cta": "ನನ್ನ ಸ್ಕೀಮಾ ಸ್ಕ್ಯಾನ್ ಮಾಡಿ →",
        "upload_placeholder": ".sql, .csv, ಅಥವಾ .json ಸ್ಕೀಮಾ ಫೈಲ್ ಅಪ್‌ಲೋಡ್ ಮಾಡಿ",
        "sidebar_config": "ಸ್ಕ್ಯಾನ್ ಕಾನ್ಫಿಗರೇಶನ್",
        "sidebar_risk": "ಅಪಾಯ ಅವಲೋಕನ",
        "sidebar_exposure": "ಅಂದಾಜು ದಂಡ",
        "sidebar_risk_score": "ಅಪಾಯ ಸ್ಕೋರ್",
        "sidebar_grounding": "ಗ್ರೌಂಡಿಂಗ್ ವಿಶ್ವಾಸ",
        "sidebar_fields": "ಫೀಲ್ಡ್‌ಗಳು",
        "sidebar_obligations": "ಬಾಧ್ಯತೆಗಳು",
        "sidebar_conflicts": "ಘರ್ಷಣೆಗಳು",
        "section_inventory": "ಡೇಟಾ ಇನ್ವೆಂಟರಿ",
        "section_obligations": "ಬಾಧ್ಯತೆಗಳು",
        "section_conflicts": "ಘರ್ಷಣೆಗಳು",
        "section_artifacts": "ಆರ್ಟಿಫ್ಯಾಕ್ಟ್‌ಗಳು",
        "section_grievance": "ದೂರು",
        "no_conflicts": "ಈ ಕ್ಷೇತ್ರಕ್ಕೆ ಯಾವುದೇ ಘರ್ಷಣೆಗಳು ಪತ್ತೆಯಾಗಿಲ್ಲ",
        "no_obligations": "ಯಾವುದೇ ಬಾಧ್ಯತೆಗಳು ಟ್ರಿಗರ್ ಆಗಿಲ್ಲ",
        "download_kit": "ಕಿಟ್ ಡೌನ್‌ಲೋಡ್ ಮಾಡಿ",
        "download_zip": "ZIP ಡೌನ್‌ಲೋಡ್ ಮಾಡಿ",
        "submit": "ಸಲ್ಲಿಸಿ",
        "grievance_title": "ದೂರು ಮತ್ತು ಡೇಟಾ ವಿನಂತಿಗಳು",
        "grievance_sub": "ಸೆಕ್ಷನ್ 11–14 ವಿನಂತಿ ಇನ್‌ಟೇಕ್ — ಆಕ್ಸೆಸ್, ಸುಧಾರಣೆ, ಅಳಿಸುವಿಕೆ, ನಾಮಾಂಕನ",
        "principal_id": "ಡೇಟಾ ಪ್ರಿನ್ಸಿಪಲ್ ಐಡಿ",
        "no_requests": "ಇನ್ನೂ ಯಾವುದೇ ವಿನಂತಿಗಳಿಲ್ಲ",
        "ready_title": "DPDP ಅನುಪಾಲನ ಸ್ಕ್ಯಾನರ್",
        "ready_sub": "PII ಫೀಲ್ಡ್‌ಗಳನ್ನು ಶೋಧಿಸಲು, DPDP ಬಾಧ್ಯತೆಗಳನ್ನು ಮ್ಯಾಪ್ ಮಾಡಲು, ಕ್ರಾಸ್-ಲಾ ಘರ್ಷಣೆಗಳನ್ನು ಪತ್ತೆಹಚ್ಚಲು ಮತ್ತು ನಿಮ್ಮ ಅನುಪಾಲನ ಕಿಟ್ ಅನ್ನು ರಚಿಸಲು ನಿಮ್ಮ ಡೇಟಾಬೇಸ್ ಸ್ಕೀಮಾ ಅಪ್‌ಲೋಡ್ ಮಾಡಿ.",
        "result_exposure": "ದಂಡ",
        "result_fields_scanned": "ಫೀಲ್ಡ್ ಸ್ಕ್ಯಾನ್",
        "result_obligations": "ಬಾಧ್ಯತೆಗಳು",
        "result_conflicts": "ಘರ್ಷಣೆಗಳು",
        "result_grounding": "ಗ್ರೌಂಡಿಂಗ್ ಸ್ಕೋರ್",
        "scan_failed": "ಸ್ಕ್ಯಾನ್ ವಿಫಳವಾಗಿದೆ",
        "upload_first": "ಮೊದಲು .sql/.csv/.json ಸ್ಕೀಮಾ ಫೈಲ್ ಅಪ್‌ಲೋಡ್ ಮಾಡಿ",
    },
    "Malayalam": {
        "app_title": "DPDP കവച്",
        "tagline": "ഇന്ത്യൻ ബിസിനസിനായി DPDP ആക്ട് പാലിക്കൽ സ്കാനർ",
        "hero_headline": "നിങ്ങളുടെ DPDP ആക്ട് പാലിക്കൽ സ്വയംചാലിതമാക്കുക",
        "hero_sub": "നിങ്ങളുടെ ഡാറ്റാബേസ് സ്കീമ അപ്‌ലോഡ് ചെയ്യുക, PII ഫീൽഡുകൾ തരംതിരിക്കുക, നിയമ ബാധ്യതകൾ മാപ്പ് ചെയ്യുക, ക്രോസ്-ലോ സംഘർഷങ്ങൾ കണ്ടെത്തുക, ഡൗൺലോഡ് ചെയ്യാവുന്ന പാലിക്കൽ കിറ്റ് നേടുക.",
        "what_is_dpdp": "DPDP ആക്ട് എന്താണ്?",
        "dpdp_desc": "ഡിജിറ്റൽ പേഴ്‌സണൽ ഡാറ്റാ പ്രൊട്ടക്ഷൻ ആക്ട്, 2023 (DPDP ആക്ട്) ഇന്ത്യയുടെ ചരിത്രപ്രധാന ഡാറ്റ സംരക്ഷണ നിയമമാണ്. പാലിക്കുന്നതിൽ പരാജയപ്പെട്ടാൽ ₹250 കോടി വരെ പിഴ ലഭിക്കാം.",
        "key_provisions": "പ്രമുഖ വകുപ്പുകൾ",
        "provision1": "വകുപ്പ് 4 — നിയമാനുസൃത ഉദ്ദേശ്യം",
        "provision2": "വകുപ്പ് 6 — സമ്മതം",
        "provision3": "വകുപ്പ് 8 — ഡാറ്റാ കൃത്യത",
        "provision4": "വകുപ്പ് 11 — മായ്ക്കൽ അവകാശം",
        "provision5": "വകുപ്പ് 13–14 — പരാതി പരിഹാരം",
        "how_it_works": "ഇതെങ്ങനെ പ്രവർത്തിക്കുന്നു",
        "step1_title": "സ്കീമ അപ്‌ലോഡ് ചെയ്യുക",
        "step1_desc": "നിങ്ങളുടെ SQL, CSV, അല്ലെങ്കിൽ JSON സ്കീമ ഫയൽ അപ്‌ലോഡ് ചെയ്യുക.",
        "step2_title": "തരംതിരിക്കുകയും മാപ്പ് ചെയ്യുകയും",
        "step2_desc": "ഞങ്ങളുടെ എഞ്ചിൻ ഓരോ ഫീൽഡും PII അല്ലെങ്കിൽ non-PII ആയി തരംതിരിക്കുന്നു.",
        "step3_title": "കിറ്റ് സൃഷ്ടിക്കുക",
        "step3_desc": "ഡൗൺലോഡ് ചെയ്യാവുന്ന ZIP നേടുക.",
        "sectors_served": "വ്യവസായങ്ങൾ",
        "stats_fields": "ഫീൽഡുകൾ സ്കാൻ ചെയ്തു",
        "stats_obligations": "ബാധ്യതകൾ മാപ്പ് ചെയ്തു",
        "stats_conflicts": "സംഘർഷങ്ങൾ കണ്ടെത്തി",
        "stats_kit": "പാലിക്കൽ കിറ്റ് സൃഷ്ടിച്ചു",
        "upload_cta": "എന്റെ സ്കീമ സ്കാൻ ചെയ്യുക →",
        "upload_placeholder": ".sql, .csv, അല്ലെങ്കിൽ .json സ്കീമ ഫയൽ അപ്‌ലോഡ് ചെയ്യുക",
        "sidebar_config": "സ്കാൻ കോൺഫിഗറേഷൻ",
        "sidebar_risk": "റിസ്ക് അവലോകനം",
        "sidebar_exposure": "കണക്കാക്കിയ പിഴ",
        "sidebar_risk_score": "റിസ്ക് സ്കോർ",
        "sidebar_grounding": "ഗ്ര roundണ്ടിംഗ് വിശ്വാസം",
        "sidebar_fields": "ഫീൽഡുകൾ",
        "sidebar_obligations": "ബാധ്യതകൾ",
        "sidebar_conflicts": "സംഘർഷങ്ങൾ",
        "section_inventory": "ഡാറ്റാ ഇൻവെൻററി",
        "section_obligations": "ബാധ്യതകൾ",
        "section_conflicts": "സംഘർഷങ്ങൾ",
        "section_artifacts": "ആർട്ടിഫാക്റ്റുകൾ",
        "section_grievance": "പരാതി",
        "no_conflicts": "ഈ മേഖലയിൽ സംഘർഷങ്ങളൊന്നും കണ്ടെത്തിയിട്ടില്ല",
        "no_obligations": "ബാധ്യതകളൊന്നും ട്രിഗർ ആയിട്ടില്ല",
        "download_kit": "കിറ്റ് ഡൗൺലോഡ് ചെയ്യുക",
        "download_zip": "ZIP ഡൗൺലോഡ് ചെയ്യുക",
        "submit": "സമർപ്പിക്കുക",
        "grievance_title": "പരാതിയും ഡാറ്റാ അഭ്യർത്ഥനകളും",
        "grievance_sub": "വകുപ്പ് 11–14 അഭ്യർത്ഥന ഇൻടേക്ക് — ആക്‌സസ്, തിരുത്തൽ, ഇല്ലാതാക്കൽ, നാമനിർദ്ദേശം",
        "principal_id": "ഡാറ്റാ പ്രിൻസിപ്പൽ ഐഡി",
        "no_requests": "ഇതുവരെ ഒരു അഭ്യർത്ഥനയും ലഭിച്ചിട്ടില്ല",
        "ready_title": "DPDP പാലിക്കൽ സ്കാനർ",
        "ready_sub": "PII ഫീൽഡുകൾ കണ്ടെത്താൻ, DPDP ബാധ്യതകൾ മാപ്പ് ചെയ്യാൻ, ക്രോസ്-ലോ സംഘർഷങ്ങൾ കണ്ടെത്താൻ, നിങ്ങളുടെ പാലിക്കൽ കിറ്റ് സൃഷ്ടിക്കാൻ നിങ്ങളുടെ ഡാറ്റാബേസ് സ്കീമ അപ്‌ലോഡ് ചെയ്യുക.",
        "result_exposure": "പിഴ",
        "result_fields_scanned": "ഫീൽഡ് സ്കാൻ",
        "result_obligations": "ബാധ്യതകൾ",
        "result_conflicts": "സംഘർഷങ്ങൾ",
        "result_grounding": "ഗ്ര roundണ്ടിംഗ് സ്കോർ",
        "scan_failed": "സ്കാൻ പരാജയപ്പെട്ടു",
        "upload_first": "ആദ്യം .sql/.csv/.json സ്കീമ ഫയൽ അപ്‌ലോഡ് ചെയ്യുക",
    },
    "Marathi": {
        "app_title": "DPDP कवच",
        "tagline": "भारतीय व्यवसायांसाठी DPDP कायदा अनुपालन स्कॅनर",
        "hero_headline": "तुमचे DPDP कायदा अनुपालन स्वयंचलित करा",
        "hero_sub": "तुमचे डेटाबेस स्कीमा अपलोड करा, PII फील्ड वर्गीकृत करा, कायदेशीर जबाबदाऱ्या नकाशे करा, क्रॉस-लॉ संघर्ष शोधा आणि डाउनलोड करण्यायोग्य अनुपालन किट मिळवा.",
        "what_is_dpdp": "DPDP कायदा काय आहे?",
        "dpdp_desc": "डिजिटल पर्सनल डेटा प्रोटेक्शन ॲक्ट, 2023 (DPDP ॲक्ट) हा भारताचा ऐतिहासिक डेटा संरक्षण कायदा आहे. अनुपालन न केल्यास ₹250 कोटी दंड होऊ शकतो.",
        "key_provisions": "मुख्य तरतुदी",
        "provision1": "कलम 4 — वैध उद्देश",
        "provision2": "कलम 6 — संमती",
        "provision3": "कलम 8 — डेटा अचूकता",
        "provision4": "कलम 11 — विलोपनाचा अधिकार",
        "provision5": "कलम 13–14 — तक्रार निवारण",
        "how_it_works": "हे कसे कार्य करते",
        "step1_title": "स्कीमा अपलोड करा",
        "step1_desc": "तुमची SQL, CSV, किंवा JSON स्कीमा फाइल अपलोड करा.",
        "step2_title": "वर्गीकृत करा आणि नकाशे करा",
        "step2_desc": "आमचे इंजिन प्रत्येक फील्ड PII किंवा non-PII म्हणून वर्गीकृत करते.",
        "step3_title": "किट तयार करा",
        "step3_desc": "डाउनलोड करण्यायोग्य ZIP मिळवा.",
        "sectors_served": "उद्योग",
        "stats_fields": "फील्ड स्कॅन केले",
        "stats_obligations": "जबाबदाऱ्या नकाशे केल्या",
        "stats_conflicts": "संघर्ष आढळले",
        "stats_kit": "अनुपालन किट तयार",
        "upload_cta": "माझे स्कीमा स्कॅन करा →",
        "upload_placeholder": ".sql, .csv, किंवा .json स्कीमा फाइल अपलोड करा",
        "sidebar_config": "स्कॅन कॉन्फिगरेशन",
        "sidebar_risk": "जोखिम ओव्हरव्ह्यू",
        "sidebar_exposure": "अंदाजे दंड",
        "sidebar_risk_score": "जोखिम स्कोअर",
        "sidebar_grounding": "ग्राउंडिंग विश्वास",
        "sidebar_fields": "फील्ड",
        "sidebar_obligations": "जबाबदाऱ्या",
        "sidebar_conflicts": "संघर्ष",
        "section_inventory": "डेटा इन्व्हेंटरी",
        "section_obligations": "जबाबदाऱ्या",
        "section_conflicts": "संघर्ष",
        "section_artifacts": "आर्टिफॅक्ट्स",
        "section_grievance": "तक्रार",
        "no_conflicts": "या क्षेत्रासाठी कोणतेही संघर्ष आढळले नाहीत",
        "no_obligations": "कोणतेही जबाबदाऱ्या ट्रिगर झाले नाहीत",
        "download_kit": "किट डाउनलोड करा",
        "download_zip": "ZIP डाउनलोड करा",
        "submit": "सबमिट",
        "grievance_title": "तक्रार आणि डेटा विनंत्या",
        "grievance_sub": "कलम 11–14 विनंती इनटेक — ॲक्सेस, सुधारणा, विलोपन, नामांकन",
        "principal_id": "डेटा प्रिन्सिपल आयडी",
        "no_requests": "अद्याप कोणतीही विनंती नाही",
        "ready_title": "DPDP अनुपालन स्कॅनर",
        "ready_sub": "PII फील्ड शोधण्यासाठी, DPDP जबाबदाऱ्या नकाशे करण्यासाठी, क्रॉस-लॉ संघर्ष शोधण्यासाठी आणि तुमचे अनुपालन किट तयार करण्यासाठी तुमचे डेटाबेस स्कीमा अपलोड करा.",
        "result_exposure": "दंड",
        "result_fields_scanned": "फील्ड स्कॅन",
        "result_obligations": "जबाबदाऱ्या",
        "result_conflicts": "संघर्ष",
        "result_grounding": "ग्राउंडिंग स्कोअर",
        "scan_failed": "स्कॅन अयशस्वी",
        "upload_first": "प्रथम .sql/.csv/.json स्कीमा फाइल अपलोड करा",
    },
    "Odia": {
        "app_title": "DPDP କବଚ",
        "tagline": "ଭାରତୀୟ ବ୍ୟବସାୟ ପାଇଁ DPDP ଅଧିନିୟମ ଅନୁପାଳନ ସ୍କାନର",
        "hero_headline": "ଆପଣଙ୍କର DPDP ଅଧିନିୟମ ଅନୁପାଳନକୁ ସ୍ବୟଂଚାଳିତ କରନ୍ତୁ",
        "hero_sub": "ଆପଣଙ୍କର ଡାଟାବେସ ସ୍କିମା ଅପଲୋଡ କରନ୍ତୁ, PII ଫିଲ୍ଡ ଶ୍ରେଣୀଭୁକ୍ତ କରନ୍ତୁ, ଆଇନ ଦାୟିତ୍ଵ ମ୍ୟାପ କରନ୍ତୁ, କ୍ରସ-ଲ ଦ୍ୱନ୍ଦ ଚିହ୍ନଟ କରନ୍ତୁ ଏବଂ ଡାଉନଲୋଡ ଯୋଗ୍ୟ ଅନୁପାଳନ କିଟ ପାଆନ୍ତୁ।",
        "what_is_dpdp": "DPDP ଅଧିନିୟମ କ'ଣ?",
        "dpdp_desc": "ଡିଜିଟାଲ ପର୍ସୋନାଲ ଡାଟା ପ୍ରୋଟେକସନ ଅଧିନିୟମ, 2023 (DPDP ଅଧିନିୟମ) ଭାରତର ଐତিহାସିକ ଡାଟା ସୁରକ୍ଷା ଆଇନ। ଅ-ଅନୁପାଳନରେ ₹250 କୋଟି ପର୍ଯ୍ୟନ୍ତ ଜରିମାନା ହୋଇପାରେ।",
        "key_provisions": "ମୁଖ୍ୟ ବିଧାନ",
        "provision1": "ଧାରା 4 — ବୈଧ ଉଦ୍ଦେଶ୍ୟ",
        "provision2": "ଧାରା 6 — ସମ୍ମତି",
        "provision3": "ଧାରା 8 — ଡାଟା ସଠିକତା",
        "provision4": "ଧାରା 11 — ବିଲୋପନର ଅଧିକାର",
        "provision5": "ଧାରା 13–14 — ଅଭିଯୋଗ ପ୍ରତିକାର",
        "how_it_works": "ଏହା କିପରି କାମ କରେ",
        "step1_title": "ସ୍କିମା ଅପଲୋଡ କରନ୍ତୁ",
        "step1_desc": "SQL, CSV, କିମ୍ବା JSON ସ୍କିମା ଫାଇଲ ଅପଲୋଡ କରନ୍ତୁ।",
        "step2_title": "ଶ୍ରେଣୀଭୁକ୍ତ କରନ୍ତୁ ଏବଂ ମ୍ୟାପ କରନ୍ତୁ",
        "step2_desc": "ଆମର ଇଞ୍ଜିନ ପ୍ରତ୍ୟେକ ଫିଲ୍ଡକୁ PII କିମ୍ବା non-PII ଭାବେ ଶ୍ରେଣୀଭୁକ୍ତ କରେ।",
        "step3_title": "କିଟ ତିଆରି କରନ୍ତୁ",
        "step3_desc": "ଡାଉନଲୋଡ ଯୋଗ୍ୟ ZIP ପାଆନ୍ତୁ।",
        "sectors_served": "ଶିଳ୍ପ",
        "stats_fields": "ଫିଲ୍ଡ ସ୍କାନ ହୋଇଛି",
        "stats_obligations": "ଦାୟିତ୍ଵ ମ୍ୟାପ ହୋଇଛି",
        "stats_conflicts": "ଦ୍ୱନ୍ଦ ଚିହ୍ନଟ ହୋଇଛି",
        "stats_kit": "ଅନୁପାଳନ କିଟ ତିଆରି ହୋଇଛି",
        "upload_cta": "ମୋର ସ୍କିମା ସ୍କାନ କରନ୍ତୁ →",
        "upload_placeholder": ".sql, .csv, କିମ୍ବା .json ସ୍କିମା ଫାଇଲ ଅପଲୋଡ କରନ୍ତୁ",
        "sidebar_config": "ସ୍କାନ କନଫିଗରେସନ",
        "sidebar_risk": "ବିପଦ ଅବଲୋକନ",
        "sidebar_exposure": "ଅଂଦାଜିତ ଜରିମାନା",
        "sidebar_risk_score": "ବିପଦ ସ୍କୋର",
        "sidebar_grounding": "ଗ୍ରାଉଣ୍ଡିଂ ବିଶ୍ୱାସ",
        "sidebar_fields": "ଫିଲ୍ଡ",
        "sidebar_obligations": "ଦାୟିତ୍ଵ",
        "sidebar_conflicts": "ଦ୍ୱନ୍ଦ",
        "section_inventory": "ଡାଟା ଇନ୍ଭେଣ୍ଟୋରୀ",
        "section_obligations": "ଦାୟିତ୍ଵ",
        "section_conflicts": "ଦ୍ୱନ୍ଦ",
        "section_artifacts": "ଆର୍ଟିଫାକ୍ଟ",
        "section_grievance": "ଅଭିଯୋଗ",
        "no_conflicts": "ଏହି କ୍ଷେତ୍ର ପାଇଁ କୌଣସି ଦ୍ୱନ୍ଦ ଚିହ୍ନଟ ହୋଇନାହିଁ",
        "no_obligations": "କୌଣସି ଦାୟିତ୍ଵ ଟ୍ରିଗର ହୋଇନାହିଁ",
        "download_kit": "କିଟ ଡାଉନଲୋଡ କରନ୍ତୁ",
        "download_zip": "ZIP ଡାଉନଲୋଡ କରନ୍ତୁ",
        "submit": "ଦାଖଲ କରନ୍ତୁ",
        "grievance_title": "ଅଭିଯୋଗ ଏବଂ ଡାଟା ଅନୁରୋଧ",
        "grievance_sub": "ଧାରା 11–14 ଅନୁରୋଧ ଇନଟେକ — ଆକ୍ସେସ, ସଂଶୋଧନ, ବିଲୋପ, ନାମାଂକନ",
        "principal_id": "ଡାଟା ପ୍ରିନ୍ସିପାଲ ଆଇଡି",
        "no_requests": "ଏପର୍ଯ୍ୟନ୍ତ କୌଣସି ଅନୁରୋଧ ନାହିଁ",
        "ready_title": "DPDP ଅନୁପାଳନ ସ୍କାନର",
        "ready_sub": "PII ଫିଲ୍ଡ ଆବିଷ୍କାର, DPDP ଦାୟିତ୍ଵ ମ୍ୟାପ, କ୍ରସ-ଲ ଦ୍ୱନ୍ଦ ଚିହ୍ନଟ ଏବଂ ଆପଣଙ୍କର ଅନୁପାଳନ କିଟ ତିଆରି କରିବାକୁ ଆପଣଙ୍କର ଡାଟାବେସ ସ୍କିମା ଅପଲୋଡ କରନ୍ତୁ।",
        "result_exposure": "ଜରିମାନା",
        "result_fields_scanned": "ଫିଲ୍ଡ ସ୍କାନ",
        "result_obligations": "ଦାୟିତ୍ଵ",
        "result_conflicts": "ଦ୍ୱନ୍ଦ",
        "result_grounding": "ଗ୍ରାଉଣ୍ଡିଂ ସ୍କୋର",
        "scan_failed": "ସ୍କାନ ବିଫଳ",
        "upload_first": "ପ୍ରଥମେ .sql/.csv/.json ସ୍କିମା ଫାଇଲ ଅପଲୋଡ କରନ୍ତୁ",
    },
    "Punjabi": {
        "app_title": "DPDP ਕਵਚ",
        "tagline": "ਭਾਰਤੀ ਕਾਰੋਬਾਰਾਂ ਲਈ DPDP ਐਕਟ ਅਨੁਪਾਲਨ ਸਕੈਨਰ",
        "hero_headline": "ਆਪਣੇ DPDP ਐਕਟ ਅਨੁਪਾਲਨ ਨੂੰ ਸਵੈਚਾਲਿਤ ਬਣਾਓ",
        "hero_sub": "ਆਪਣਾ ਡੇਟਾਬੇਸ ਸਕੀਮਾ ਅੱਪਲੋਡ ਕਰੋ, PII ਫੀਲਡਾਂ ਨੂੰ ਸ਼੍ਰੇਣੀਬੱਧ ਕਰੋ, ਕਾਨੂੰਨੀ ਜ਼ਿੰਮੇਵਾਰੀਆਂ ਨੂੰ ਮੈਪ ਕਰੋ, ਕ੍ਰਾਸ-ਲਾ ਟਕਰਾਅ ਲੱਭੋ ਅਤੇ ਡਾਊਨਲੋਡ ਯੋਗ ਅਨੁਪਾਲਨ ਕਿੱਟ ਪ੍ਰਾਪਤ ਕਰੋ।",
        "what_is_dpdp": "DPDP ਐਕਟ ਕੀ ਹੈ?",
        "dpdp_desc": "ਡਿਜੀਟਲ ਪਰਸਨਲ ਡੇਟਾ ਪ੍ਰੋਟੈਕਸ਼ਨ ਐਕਟ, 2023 (DPDP ਐਕਟ) ਭਾਰਤ ਦਾ ਇਤਿਹਾਸਕ ਡੇਟਾ ਸੁਰੱਖਿਆ ਕਾਨੂੰਨ ਹੈ। ਗੈਰ-ਅਨੁਪਾਲਨ 'ਤੇ ₹250 ਕਰੋੜ ਤੱਕ ਜੁਰਮਾਨਾ ਲੱਗ ਸਕਦਾ ਹੈ।",
        "key_provisions": "ਮੁੱਖ ਸੰਬੰਧਾਂ",
        "provision1": "ਧਾਰਾ 4 — ਕਾਨੂੰਨੀ ਉਦੇਸ਼",
        "provision2": "ਧਾਰਾ 6 — ਸਹਿਮਤੀ",
        "provision3": "ਧਾਰਾ 8 — ਡੇਟਾ ਸੁੀਯੋਗ",
        "provision4": "ਧਾਰਾ 11 — ਮਿਟਾਉਣ ਦਾ ਅਧਿਕਾਰ",
        "provision5": "ਧਾਰਾ 13–14 — ਸ਼ਿਕਾਇਆ ਹੱਲ",
        "how_it_works": "ਇਹ ਕਿਵੇਂ ਕੰਮ ਕਰਦਾ ਹੈ",
        "step1_title": "ਸਕੀਮਾ ਅੱਪਲੋਡ ਕਰੋ",
        "step1_desc": "SQL, CSV, ਜਾਂ JSON ਸਕੀਮਾ ਫਾਈਲ ਅੱਪਲੋਡ ਕਰੋ।",
        "step2_title": "ਸ਼੍ਰੇਣੀਬੱਧ ਕਰੋ ਅਤੇ ਮੈਪ ਕਰੋ",
        "step2_desc": "ਸਾਡਾ ਇੰਜਣ ਹਰੇਕ ਫੀਲਡ ਨੂੰ PII ਜਾਂ non-PII ਵਜੋਂ ਸ਼੍ਰੇਣੀਬੱਧ ਕਰਦਾ ਹੈ।",
        "step3_title": "ਕਿੱਟ ਬਣਾਓ",
        "step3_desc": "ਡਾਊਨਲੋਡ ਯੋਗ ZIP ਪ੍ਰਾਪਤ ਕਰੋ।",
        "sectors_served": "ਉਦਯੋਗ",
        "stats_fields": "ਫੀਲਡ ਸਕੈਨ ਕੀਤੇ",
        "stats_obligations": "ਜ਼ਿੰਮੇਵਾਰੀਆਂ ਮੈਪ ਕੀਤੀਆਂ",
        "stats_conflicts": "ਟਕਰਾਅ ਲੱਭੇ",
        "stats_kit": "ਅਨੁਪਾਲਨ ਕਿੱਟ ਬਣੀ",
        "upload_cta": "ਮੇਰਾ ਸਕੀਮਾ ਸਕੈਨ ਕਰੋ →",
        "upload_placeholder": ".sql, .csv, ਜਾਂ .json ਸਕੀਮਾ ਫਾਈਲ ਅੱਪਲੋਡ ਕਰੋ",
        "sidebar_config": "ਸਕੈਨ ਸੰਰਚਨਾ",
        "sidebar_risk": "ਜੋਖਮ ਸੰਖੇਪ",
        "sidebar_exposure": "ਅੰਦਾਜ਼ੀ ਜੁਰਮਾਨਾ",
        "sidebar_risk_score": "ਜੋਖਮ ਅੰਕ",
        "sidebar_grounding": "ਗ੍ਰਾਊਂਡਿੰਗ ਵਿਸ਼ਵਾਸ",
        "sidebar_fields": "ਫੀਲਡ",
        "sidebar_obligations": "ਜ਼ਿੰਮੇਵਾਰੀਆਂ",
        "sidebar_conflicts": "ਟਕਰਾਅ",
        "section_inventory": "ਡੇਟਾ ਇਨਵੈਂਟਰੀ",
        "section_obligations": "ਜ਼ਿੰਮੇਵਾਰੀਆਂ",
        "section_conflicts": "ਟਕਰਾਅ",
        "section_artifacts": "ਆਰਟੀਫੈਕਟ",
        "section_grievance": "ਸ਼ਿਕਾਇਆ",
        "no_conflicts": "ਇਸ ਖੇਤਰ ਲਈ ਕੋਈ ਟਕਰਾਅ ਨਹੀਂ ਲੱਭਾ",
        "no_obligations": "ਕੋਈ ਜ਼ਿੰਮੇਵਾਰੀ ਨਹੀਂ ਚਲਾਈ ਗਈ",
        "download_kit": "ਕਿੱਟ ਡਾਊਨਲੋਡ ਕਰੋ",
        "download_zip": "ZIP ਡਾਊਨਲੋਡ ਕਰੋ",
        "submit": "ਜਮ੍ਹਾਂ ਕਰੋ",
        "grievance_title": "ਸ਼ਿਕਾਇਆ ਅਤੇ ਡੇਟਾ ਬੇਨਤੀਆਂ",
        "grievance_sub": "ਧਾਰਾ 11–14 ਬੇਨਤੀ ਇਨਟੇਕ — ਐਕਸੈਸ, ਸੁਧਾਰ, ਮਿਟਾਉਣ, ਨਾਮਜ਼ਦਗੀ",
        "principal_id": "ਡੇਟਾ ਪ੍ਰਿੰਸੀਪਲ ਆਈਡੀ",
        "no_requests": "ਹੁਣ ਤੱਕ ਕੋਈ ਬੇਨਤੀ ਨਹੀਂ",
        "ready_title": "DPDP ਅਨੁਪਾਲਨ ਸਕੈਨਰ",
        "ready_sub": "PII ਫੀਲਡ ਲੱਭਣ, DPDP ਜ਼ਿੰਮੇਵਾਰੀਆਂ ਮੈਪ ਕਰਨ, ਕ੍ਰਾਸ-ਲਾ ਟਕਰਾਅ ਲੱਭਣ ਅਤੇ ਤੁਹਾਡੀ ਅਨੁਪਾਲਨ ਕਿੱਟ ਬਣਾਉਣ ਲਈ ਆਪਣਾ ਡੇਟਾਬੇਸ ਸਕੀਮਾ ਅੱਪਲੋਡ ਕਰੋ।",
        "result_exposure": "ਜੁਰਮਾਨਾ",
        "result_fields_scanned": "ਫੀਲਡ ਸਕੈਨ",
        "result_obligations": "ਜ਼ਿੰਮੇਵਾਰੀਆਂ",
        "result_conflicts": "ਟਕਰਾਅ",
        "result_grounding": "ਗ੍ਰਾਊਂਡਿੰਗ ਅੰਕ",
        "scan_failed": "ਸਕੈਨ ਅਸਫਲ",
        "upload_first": "ਪਹਿਲਾਂ .sql/.csv/.json ਸਕੀਮਾ ਫਾਈਲ ਅੱਪਲੋਡ ਕਰੋ",
    },
    "Tamil": {
        "app_title": "DPDP கவசம்",
        "tagline": "இந்திய வணிகங்களுக்கான DPDP சட்ட இணக்க ஸ்கேனர்",
        "hero_headline": "உங்கள் DPDP சட்ட இணக்கத்தை தானியங்கிப்படுத்துங்கள்",
        "hero_sub": "உங்கள் தரவுத்தள நிறுவலை பதிவேற்றம் செய்யுங்கள், PII புலங்களை வகைப்படுத்துங்கள், சட்டக் கடமைகளை வரைபடமாக்குங்கள், குறுக்கு-சட்ட மோதல்களைக் கண்டறிந்து, பதிவிறக்கக்கூடிய இணக்க கிட்டைப் பெறுங்கள்.",
        "what_is_dpdp": "DPDP சட்டம் என்றால் என்ன?",
        "dpdp_desc": "டிஜிட்டல் பர்சனல் டேட்டா ப்ரொடெக்ஷன் சட்டம், 2023 (DPDP சட்டம்) இந்தியாவின் சாதனை தரவு பாதுகாப்பு சட்டம். இணக்கமின்மையில் ₹250 கோடி வரை அபராதம் விதிக்கப்படலாம்.",
        "key_provisions": "முக்கிய விதிகள்",
        "provision1": "பிரிவு 4 — சட்டப்பூர்வ நோக்கம்",
        "provision2": "பிரிவு 6 — ஒப்புதல்",
        "provision3": "பிரிவு 8 — தரவு துல்லியம்",
        "provision4": "பிரிவு 11 — அழித்தல் உரிமை",
        "provision5": "பிரிவு 13–14 — புகார் தீர்வு",
        "how_it_works": "இது எப்படி செயல்படுகிறது",
        "step1_title": "நிறுவலை பதிவேற்றம் செய்யுங்கள்",
        "step1_desc": "உங்கள் SQL, CSV, அல்லது JSON நிறுவல் கோப்பை பதிவேற்றம் செய்யுங்கள்.",
        "step2_title": "வகைப்படுத்துங்கள் மற்றும் வரைபடமாக்குங்கள்",
        "step2_desc": "எங்கள் இயந்திரம் ஒவ்வொரு புலத்தையும் PII அல்லது non-PII ஆக வகைப்படுத்துகிறது.",
        "step3_title": "கிட்டை உருவாக்குங்கள்",
        "step3_desc": "பதிவிறக்கக்கூடிய ZIP ஐப் பெறுங்கள்.",
        "sectors_served": "தொழில்கள்",
        "stats_fields": "புலங்கள் ஸ்கேன் செய்யப்பட்டன",
        "stats_obligations": "கடமைகள் வரைபடமாக்கப்பட்டன",
        "stats_conflicts": "மோதல்கள் கண்டறியப்பட்டன",
        "stats_kit": "இணக்க கிட் உருவாக்கப்பட்டது",
        "upload_cta": "என் நிறுவலை ஸ்கேன் செய்யுங்கள் →",
        "upload_placeholder": ".sql, .csv, அல்லது .json நிறுவல் கோப்பை பதிவேற்றம் செய்யுங்கள்",
        "sidebar_config": "ஸ்கேன் உள்ளமைவு",
        "sidebar_risk": "ஆபத்து மேலோட்டம்",
        "sidebar_exposure": "மதிப்பிட்ட அபராதம்",
        "sidebar_risk_score": "ஆபத்து மதிப்பெண்",
        "sidebar_grounding": "கிரவுண்டிங் நம்பிக்கை",
        "sidebar_fields": "புலங்கள்",
        "sidebar_obligations": "கடமைகள்",
        "sidebar_conflicts": "மோதல்கள்",
        "section_inventory": "தரவு சரக்குகள்",
        "section_obligations": "கடமைகள்",
        "section_conflicts": "மோதல்கள்",
        "section_artifacts": "கலைப்பொருட்கள்",
        "section_grievance": "புகார்",
        "no_conflicts": "இந்த துறைக்கு மோதல்கள் எதுவும் கண்டறியப்படவில்லை",
        "no_obligations": "கடமைகள் எதுவும் தூண்டப்படவில்லை",
        "download_kit": "கிட்டை பதிவிறக்குங்கள்",
        "download_zip": "ZIP பதிவிறக்குங்கள்",
        "submit": "சமர்ப்பிக்க",
        "grievance_title": "புகார் மற்றும் தரவு கோரிக்கைகள்",
        "grievance_sub": "பிரிவு 11–14 கோரிக்கை உள்ளீடு — அணுகல், சரிசெய்தல், அழித்தல், நியமனம்",
        "principal_id": "தரவு முதன்மை ஐடி",
        "no_requests": "இன்னும் கோரிக்கைகள் இல்லை",
        "ready_title": "DPDP இணக்க ஸ்கேனர்",
        "ready_sub": "PII புலங்களைக் கண்டறிந்து, DPDP கடமைகளை வரைபடமாக்கி, குறுக்கு-சட்ட மோதல்களைக் கண்டறிந்து, உங்கள் இணக்க கிட்டை உருவாக்க உங்கள் தரவுத்தள நிறுவலைப் பதிவேற்றம் செய்யுங்கள்.",
        "result_exposure": "அபராதம்",
        "result_fields_scanned": "புல ஸ்கேன்",
        "result_obligations": "கடமைகள்",
        "result_conflicts": "மோதல்கள்",
        "result_grounding": "கிரவுண்டிங் மதிப்பெண்",
        "scan_failed": "ஸ்கேன் தோல்வி",
        "upload_first": "முதலில் .sql/.csv/.json நிறுவல் கோப்பை பதிவேற்றம் செய்யுங்கள்",
    },
    "Telugu": {
        "app_title": "DPDP కవచ",
        "tagline": "భారతీయ వ్యాపారాలకు DPDP చట్ట అనుసరణ స్కానర్",
        "hero_headline": "మీ DPDP చట్ట అనుసరణను స్వయంచాలకంగా చేయండి",
        "hero_sub": "మీ డేటాబేస్ స్కీమాను అప్‌లోడ్ చేయండి, PII ఫీల్డ్‌లను वर्गీకరించండి, చట్టపరమైన బాధ్యతలను మ్యాప్ చేయండి, క్రాస్-లా కలహాలను కనుగొనండి మరియు డౌన్‌లోడ్ చేయడానికి అనుమతించే అనుసరణ కిట్‌ను పొందండి.",
        "what_is_dpdp": "DPDP చట్టం అంటే ఏమిటి?",
        "dpdp_desc": "డిజిటల్ పర్సనల్ డేటా ప్రొటెక్షన్ యాక్ట్, 2023 (DPDP యాక్ట్) భారతదేశపు చారిత్రక డేటా రక్షణ చట్టం. అనుసరణ లేకపోవడంపై ₹250 కోట్ల వరకు జరిమానా విధించవచ్చు.",
        "key_provisions": "ప్రధాన నిబంధనలు",
        "provision1": "విభాగం 4 — చట్టపరమైన ఉద్దేశ్యం",
        "provision2": "విభాగం 6 — సమ్మతి",
        "provision3": "విభాగం 8 — డేటా ఖచ్చితత్వం",
        "provision4": "విభాగం 11 — తొలగింపు హక్కు",
        "provision5": "విభాగం 13–14 — ఫిర్యాదు పరిష్కారం",
        "how_it_works": "ఇది ఎలా పని చేస్తుంది",
        "step1_title": "స్కీమా అప్‌లోడ్ చేయండి",
        "step1_desc": "మీ SQL, CSV, లేదా JSON స్కీమా ఫైల్‌ను అప్‌లోడ్ చేయండి.",
        "step2_title": "वर्गీకरించండి మరియు మ్యాప్ చేయండి",
        "step2_desc": "మా ఇంజిన్ ప్రతి ఫీల్డ్‌ను PII లేదా non-PIIగా वर्गीకరిస్తుంది.",
        "step3_title": "కిట్‌ను సృష్టించండి",
        "step3_desc": "డౌన్‌లోడ్ చేయడానికి అనుమతించే ZIPని పొందండి.",
        "sectors_served": "పరిశ్రమలు",
        "stats_fields": "ఫీల్డ్‌లు స్కాన్ చేయబడ్డాయి",
        "stats_obligations": "బాధ్యతలు మ్యాప్ చేయబడ్డాయి",
        "stats_conflicts": "కలహాలు కనుగొనబడ్డాయి",
        "stats_kit": "అనుసరణ కిట్ సృష్టించబడింది",
        "upload_cta": "నా స్కీమా స్కాన్ చేయండి →",
        "upload_placeholder": ".sql, .csv, లేదా .json స్కీమా ఫైల్‌ను అప్‌లోడ్ చేయండి",
        "sidebar_config": "స్కాన్ కాన్ఫిగరేషన్",
        "sidebar_risk": "రిస్క్ ఓవర్‌వ్యూ",
        "sidebar_exposure": "అంచనా జరిమానా",
        "sidebar_risk_score": "రిస్క్ స్కోర్",
        "sidebar_grounding": "గ్రౌండింగ్ విశ్వాసం",
        "sidebar_fields": "ఫీల్డ్‌లు",
        "sidebar_obligations": "బాధ్యతలు",
        "sidebar_conflicts": "కలహాలు",
        "section_inventory": "డేటా ఇన్వెంటరీ",
        "section_obligations": "బాధ్యతలు",
        "section_conflicts": "కలహాలు",
        "section_artifacts": "ఆర్టిఫ్యాక్ట్‌లు",
        "section_grievance": "ఫిర్యాదు",
        "no_conflicts": "ఈ రంగానికి కలహాలు ఏవీ కనుగొనబడలేదు",
        "no_obligations": "ఏ బాధ్యతలు ట్రిగర్ చేయబడలేదు",
        "download_kit": "కిట్ డౌన్‌లోడ్ చేయండి",
        "download_zip": "ZIP డౌన్‌లోడ్ చేయండి",
        "submit": "సబ్మిట్",
        "grievance_title": "ఫిర్యాదు మరియు డేటా అభ్యర్థనలు",
        "grievance_sub": "విభాగం 11–14 అభ్యర్థన ఇన్‌టేక్ — యాక్సెస్, సవరణ, తొలగింపు, నామినేషన్",
        "principal_id": "డేటా ప్రిన్సిపల్ ఐడి",
        "no_requests": "ఇంకా అభ్యర్థనలు లేవు",
        "ready_title": "DPDP అనుసరణ స్కానర్",
        "ready_sub": "PII ఫీల్డ్‌లను కనుగొనడానికి, DPDP బాధ్యతలను మ్యాప్ చేయడానికి, క్రాస్-లా కలహాలను కనుగొనడానికి మరియు మీ అనుసరణ కిట్‌ను సృష్టించడానికి మీ డేటాబేస్ స్కీమాను అప్‌లోడ్ చేయండి.",
        "result_exposure": "జరిమానా",
        "result_fields_scanned": "ఫీల్డ్ స్కాన్",
        "result_obligations": "బాధ్యతలు",
        "result_conflicts": "కలహాలు",
        "result_grounding": "గ్రౌండింగ్ స్కోర్",
        "scan_failed": "స్కాన్ విఫలమైంది",
        "upload_first": "ముందుగా .sql/.csv/.json స్కీమా ఫైల్‌ను అప్‌లోడ్ చేయండి",
    },
    "Urdu": {
        "app_title": "DPDP کواچ",
        "tagline": "بھارتی کاروبار کے لیے DPDP ایکٹ کمپلائنس اسکینر",
        "hero_headline": "اپنے DPDP ایکٹ کمپلائنس کو خود کار بنائیں",
        "hero_sub": "اپنا ڈیٹابیس سکیما اپلوڈ کریں، PII فیلڈز کو درجہ بندی کریں، قانونی ذمہ داریوں کو میپ کریں، کراس-لاء تنازعات دریافت کریں اور ڈاؤنلوڈ کرنے کے قابل کمپلائنس کٹ حاصل کریں۔",
        "what_is_dpdp": "DPDP ایکٹ کیا ہے؟",
        "dpdp_desc": "ڈیجیٹل پرسنل ڈیٹا پروٹیکشن ایکٹ، 2023 (DPDP ایکٹ) بھارت کا سنگ میل ڈیٹا تحفظ قانون ہے۔ غیر کمپلائنس پر ₹250 کروڑ تک جرمانہ ہو سکتا ہے۔",
        "key_provisions": "اہم دفعات",
        "provision1": "شق 4 — قانونی مقصد",
        "provision2": "شق 6 — رضامندی",
        "provision3": "شق 8 — ڈیٹا درستگی",
        "provision4": "شق 11 — حذف کا حق",
        "provision5": "شق 13–14 — شکایت کا ازالہ",
        "how_it_works": "یہ کیسے کام کرتا ہے",
        "step1_title": "سکیما اپلوڈ کریں",
        "step1_desc": "اپنا SQL، CSV، یا JSON سکیما فائل اپلوڈ کریں۔",
        "step2_title": "درجہ بندی اور میپ کریں",
        "step2_desc": "ہمارا انجن ہر فیلڈ کو PII یا non-PII کے بطور درجہ بندی کرتا ہے۔",
        "step3_title": "کٹ بنائیں",
        "step3_desc": "ڈاؤنلوڈ کرنے کے قابل ZIP حاصل کریں۔",
        "sectors_served": "صنعتیں",
        "stats_fields": "فیلڈز اسکین ہوئیں",
        "stats_obligations": "ذمہ داریاں میپ ہوئیں",
        "stats_conflicts": "تنازعات ملے",
        "stats_kit": "کمپلائنس کٹ بنا",
        "upload_cta": "میرا سکیما اسکین کریں →",
        "upload_placeholder": ".sql، .csv، یا .json سکیما فائل اپلوڈ کریں",
        "sidebar_config": "اسکین کنفیگریشن",
        "sidebar_risk": "خطرہ جائزہ",
        "sidebar_exposure": "تخمینی جرمانہ",
        "sidebar_risk_score": "خطرہ اسکور",
        "sidebar_grounding": "گراؤنڈنگ اعتماد",
        "sidebar_fields": "فیلڈز",
        "sidebar_obligations": "ذمہ داریاں",
        "sidebar_conflicts": "تنازعات",
        "section_inventory": "ڈیٹا انوینٹری",
        "section_obligations": "ذمہ داریاں",
        "section_conflicts": "تنازعات",
        "section_artifacts": "آرٹیفیکٹس",
        "section_grievance": "شکایت",
        "no_conflicts": "اس سیکٹر کے لیے کوئی تنازعات نہیں ملے",
        "no_obligations": "کوئی ذمہ داری ٹرگر نہیں ہوئی",
        "download_kit": "کٹ ڈاؤنلوڈ کریں",
        "download_zip": "ZIP ڈاؤنلوڈ کریں",
        "submit": "جمع کروائیں",
        "grievance_title": "شکایت اور ڈیٹا درخواستیں",
        "grievance_sub": "شق 11–14 درخواست انٹیک — رسائی، تصحیح، حذف، نامزدگی",
        "principal_id": "ڈیٹا پرنسپل آئی ڈی",
        "no_requests": "ابھی تک کوئی درخواست نہیں",
        "ready_title": "DPDP کمپلائنس اسکینر",
        "ready_sub": "PII فیلڈز دریافت کرنے، DPDP ذمہ داریوں کو میپ کرنے، کراس-لاء تنازعات دریافت کرنے اور اپنا کمپلائنس کٹ بنانے کے لیے اپنا ڈیٹابیس سکیما اپلوڈ کریں۔",
        "result_exposure": "جرمانہ",
        "result_fields_scanned": "فیلڈ اسکین",
        "result_obligations": "ذمہ داریاں",
        "result_conflicts": "تنازعات",
        "result_grounding": "گراؤنڈنگ اسکور",
        "scan_failed": "اسکین ناکام",
        "upload_first": "پہلے .sql/.csv/.json سکیما فائل اپلوڈ کریں",
    },
    "Bodo": {
        "app_title": "DPDP Kavch",
        "hero_headline": "Hamaro DPDP Aayojan Proyojon Swayanganik Karo",
        "what_is_dpdp": "DPDP Aayojan Kya He?",
        "dpdp_desc": "Digital Personal Data Protection Aayojan, 2023 (DPDP Aayojan) Bharatko Laman Data Suraksha Kanoon He. Aswasta Sanga ₹250 Crore Saman Danda Laga Sakda He.",
        "sidebar_config": "Scan Sangrahi",
        "sidebar_risk": "Khatarnak Darbar",
        "section_inventory": "Data Sannali",
        "section_obligations": "Proyojon",
        "section_conflicts": "Lada Lada",
        "section_artifacts": "Drishtikon",
        "section_grievance": "Fariyad",
    },
    "Dogri": {
        "app_title": "DPDP ਕਵਚ",
        "hero_headline": "ਆਪਣੇ DPDP ਐਕਟ ਅਨੁਪਾਲਨ ਨੂੰ ਸਵੈਚਾਲਿਤ ਬਣਾਓ",
        "what_is_dpdp": "DPDP ਐਕਟ ਕੀ ਹੈ?",
        "dpdp_desc": "ਡਿਜੀਟਲ ਪਰਸਨਲ ਡੇਟਾ ਪ੍ਰੋਟੈਕਸ਼ਨ ਐਕਟ, 2023 (DPDP ਐਕਟ) ਭਾਰਤ ਦਾ ਇਤਿਹਾਸਕ ਡੇਟਾ ਸੁਰੱਖਿਆ ਕਾਨੂੰਨ ਹੈ। ਗੈਰ-ਅਨੁਪਾਲਨ 'ਤੇ ₹250 ਕਰੋੜ ਤੱਕ ਜੁਰਮਾਨਾ।",
        "sidebar_config": "ਸਕੈਨ ਸੰਰਚਨਾ",
        "sidebar_risk": "ਜੋਖਮ ਸੰਖੇਪ",
        "section_inventory": "ਡੇਟਾ ਇਨਵੈਂਟਰੀ",
        "section_obligations": "ਜ਼ਿੰਮੇਵਾਰੀਆਂ",
        "section_conflicts": "ਟਕਰਾਅ",
        "section_artifacts": "ਆਰਟੀਫੈਕਟ",
        "section_grievance": "ਸ਼ਿਕਾਇਆ",
    },
    "Kashmiri": {
        "app_title": "DPDP کَواچ",
        "hero_headline": "آپنے DPDP ایکٹ کمپلائنس کو خود کار بَنیو",
        "what_is_dpdp": "DPDP ایکٹ کیا ہے؟",
        "dpdp_desc": "ڈیجیٹل پرسنل ڈیٹا پروٹیکشن ایکٹ، 2023 (DPDP ایکٹ) بھارت کا سنگ میل ڈیٹا تحفظ قانون ہے۔",
        "sidebar_config": "اسکین کنفیگریشن",
        "sidebar_risk": "خطرہ جائزہ",
        "section_inventory": "ڈیٹا انوینٹری",
        "section_obligations": "ذمہ داریاں",
        "section_conflicts": "تنازعات",
        "section_artifacts": "آرٹیفیکٹس",
        "section_grievance": "شکایت",
    },
    "Konkani": {
        "app_title": "DPDP ಕವಚ",
        "hero_headline": "ನಿಮ್ಮ DPDP ಕಾನೂನು ಅನುಪಾಲನೆಯನ್ನು ಸ್ವಯಂಚಾಲಿತಗೊಳಿಸಿ",
        "what_is_dpdp": "DPDP ಕಾಯ್ದೆ ಎಂದರೇನು?",
        "dpdp_desc": "ಡಿಜಿಟಲ್ ಪರ್ಸನಲ್ ಡೇಟಾ ಪ್ರೊಟೆಕ್ಷನ್ ಆಕ್ಟ್, 2023 (DPDP ಆಕ್ಟ್) ಭಾರತದ ಸ್ಮರಣೀಯ ಡೇಟಾ ಸಂರಕ್ಷಣಾ ಕಾನೂನು.",
        "sidebar_config": "ಸ್ಕ್ಯಾನ್ ಕಾನ್ಫಿಗರೇಶನ್",
        "sidebar_risk": "ಅಪಾಯ ಅವಲೋಕನ",
        "section_inventory": "ಡೇಟಾ ಇನ್ವೆಂಟರಿ",
        "section_obligations": "ಬಾಧ್ಯತೆಗಳು",
        "section_conflicts": "ಘರ್ಷಣೆಗಳು",
        "section_artifacts": "ಆರ್ಟಿಫ್ಯಾಕ್ಟ್‌ಗಳು",
        "section_grievance": "ದೂರು",
    },
    "Maithili": {
        "app_title": "DPDP कवच",
        "hero_headline": "अपन सबGDPR कानून अनुपालनके स्वचालित करू",
        "what_is_dpdp": "DPDP कानून की अछि?",
        "dpdp_desc": "डिजिटल पर्सनल डेटा प्रोटेक्शन एक्ट, 2023 (DPDP एक्ट) भारतक लेल ऐतिहासिक डेटा संरक्षण कानून अछि।",
        "sidebar_config": "स्कैन कन्फिगरेसन",
        "sidebar_risk": "जोखिम अवलोकन",
        "section_inventory": "डेटा इन्वेंटरी",
        "section_obligations": "दायित्व",
        "section_conflicts": "संघर्ष",
        "section_artifacts": "आर्टिफैक्ट",
        "section_grievance": "शिकायत",
    },
    "Manipuri": {
        "app_title": "DPDP কবচ",
        "hero_headline": " অপনার DPDP অধিবিধান অনুসারীতা স্বয়ংক্রিয় কৰক",
        "what_is_dpdp": "DPDP অধিবিধান কি?",
        "dpdp_desc": "ডিজিটাল পার্সোনাল ডাটা প্রটেক্সন অধিবিধান, 2023 (DPDP অধিবিধান) ভারতবর্ষৰ ঐতিহাসিক ডাটা সুৰক্ষা আইন।",
        "sidebar_config": "স্ক্যান কনফিগারেশন",
        "sidebar_risk": "ঝুঁকিৰ ওভাৰভিউ",
        "section_inventory": "ডাটা ইনভেন্টৰি",
        "section_obligations": "বাধ্যবাধকতা",
        "section_conflicts": "সংঘাত",
        "section_artifacts": "আর্টিফ্যাক্ট",
        "section_grievance": "অভিযোগ",
    },
    "Nepali": {
        "app_title": "DPDP कवच",
        "hero_headline": "आफ्नो DPDP ऐन अनुपालन स्वचालित गर्नुहोस्",
        "what_is_dpdp": "DPDP ऐन के हो?",
        "dpdp_desc": "डिजिटल पर्सनल डेटा प्रोटेक्शन ऐन, 2023 (DPDP ऐन) भारतको ऐतिहासिक डेटा संरक्षण ऐन हो।",
        "sidebar_config": "स्क्यान कन्फिगरेसन",
        "sidebar_risk": "जोखिम अवलोकन",
        "section_inventory": "डेटा इन्भेन्टरी",
        "section_obligations": "दायित्व",
        "section_conflicts": "द्वन्द्व",
        "section_artifacts": "आर्टिफ्याक्ट",
        "section_grievance": "गुनासो",
    },
    "Sanskrit": {
        "app_title": "DPDP कवचम्",
        "hero_headline": "भवतः DPDP अधिनियम अनुपालनं स्वयंचालितं कुर्वन्तु",
        "what_is_dpdp": "DPDP अधिनियमः किम्?",
        "dpdp_desc": "डिजिटल पर्सनल डेटा प्रोटेक्शन अधिनियमः, 2023 (DPDP अधिनियमः) भारतस्य महत्त्वपूर्णं डेटा संरक्षणं विधिः अस्ति।",
        "sidebar_config": "स्कैन संरचना",
        "sidebar_risk": "जोखिमा दृश्य",
        "section_inventory": "डेटा सूची",
        "section_obligations": "कर्तव्यानि",
        "section_conflicts": "संघर्षाणि",
        "section_artifacts": "कलाकृतयः",
        "section_grievance": "शिकायतम्",
    },
    "Santali": {
        "app_title": "DPDP ᱫᱚᱢᱚᱜ",
        "hero_headline": "ᱟᱢᱟᱜ DPDP ᱥᱟᱹᱜᱩᱴ ᱮᱱᱮᱡ ᱟᱹᱯᱱᱟᱹᱨᱤᱭᱟᱹ ᱟᱠᱟᱫᱽ ᱢᱮ",
        "what_is_dpdp": "DPDP ᱥᱟᱹᱜᱩᱴ ᱥᱟᱹᱜᱩᱴ?",
        "dpdp_desc": "ᱰᱤᱡᱤᱴᱚᱞ ᱯᱟᱨᱥᱚᱱᱚᱞ ᱰᱟᱴᱟ ᱯᱨᱚᱴᱮᱠᱥᱚᱱ ᱢᱟᱹᱱ, 2023 (DPDP ᱢᱟᱹᱱ) ᱵᱷᱟᱨᱚᱛᱤᱭᱟᱹ ᱰᱟᱴᱟ ᱡᱤᱭᱟᱹᱞᱤ ᱟᱹᱯᱱᱟᱹᱨᱤ ᱢᱟᱹᱱ ᱠᱟᱱᱟ।",
        "sidebar_config": "ᱥᱠᱟᱹᱱ ᱠᱚᱱᱯᱤᱡᱚᱨᱮᱥᱚᱱ",
        "sidebar_risk": "ᱡᱚᱠᱷᱚᱱ ᱨᱮᱱᱟᱜ ᱢᱮᱱᱮᱛ",
        "section_inventory": "ᱰᱟᱴᱟ ᱤᱱᱵᱷᱮᱱᱴᱨᱤ",
        "section_obligations": "ᱡᱟᱹᱛᱤᱭᱟᱹᱨᱤᱭᱟᱹ",
        "section_conflicts": "ᱞᱚᱜᱚᱱ",
        "section_artifacts": "ᱟᱨᱴᱤᱯᱷᱮᱠᱴᱥ",
        "section_grievance": "ᱯᱟᱹᱞᱩ",
    },
    "Sindhi": {
        "app_title": "DPDP ڪواچ",
        "hero_headline": "پنهنجو DPDP ڪانوڻ لاڳپتي ٺيپ ڪريو",
        "what_is_dpdp": "DPDP ڪانوڻ ڇا آهي؟",
        "dpdp_desc": "ڊجيٽل پرسنل ڊيٽا پروٽيڪشن ڪانوڻ، 2023 (DPDP ڪانوڻ) هندستان جو لَنگ میل ڊيٽا حفاظت ڪانوڻ آهي.",
        "sidebar_config": "سکين ترتيب",
        "sidebar_risk": "خطرن جي جائزو",
        "section_inventory": "ڊيٽا انوینٹري",
        "section_obligations": "ذميواريون",
        "section_conflicts": "ٽڪر",
        "section_artifacts": "آرٽيفیکٽس",
        "section_grievance": "شڪايت",
    },
}

ALL_SECTOR_KEYS = list(TRANSLATIONS.keys())


@app.post("/api/translate")
async def translate(payload: dict[str, Any]) -> JSONResponse:
    target_lang = payload.get("language", "English")
    data = payload.get("data", [])
    if target_lang == "English" or not data:
        return JSONResponse({"translated": data, "status": "ok"})

    all_values: list[str] = []
    item_keys: list[list[str]] = []
    for item in data:
        if isinstance(item, dict):
            item_keys.append(list(item.keys()))
            for v in item.values():
                all_values.append(str(v) if v is not None else "")
        else:
            item_keys.append([])
            all_values.append(str(item))

    if not all_values:
        return JSONResponse({"translated": data, "status": "ok"})

    batch_text = "\n".join(f"{i + 1}. {v}" for i, v in enumerate(all_values))
    try:
        import json as _json, urllib.request as _req

        batch_payload = _json.dumps(
            {
                "model": os.environ.get("INDIAN_MODEL_NAME", "sarvam-m"),
                "messages": [
                    {
                        "role": "system",
                        "content": (
                            f"You are a professional translator. Translate every line of the following list to {target_lang}. "
                            "Return exactly {n} lines, one translated line per numbered line, preserving the numbering. "
                            "Return ONLY the {n} translated lines, nothing else."
                        ).format(n=len(all_values)),
                    },
                    {"role": "user", "content": batch_text},
                ],
                "temperature": 0.1,
            }
        ).encode()
        req = _req.Request(
            "https://api.sarvam.ai/chat/completions",
            data=batch_payload,
            headers={
                "Authorization": f"Bearer {SARVAM_API_KEY}",
                "Content-Type": "application/json",
            },
            method="POST",
        )
        with _req.urlopen(req, timeout=30) as resp:
            resp_data = _json.loads(resp.read())
        raw_lines = resp_data["choices"][0]["message"]["content"].strip().split("\n")
        translated_map: dict[int, str] = {}
        for line in raw_lines:
            line = line.strip()
            if not line:
                continue
            dot_idx = line.find(".")
            if dot_idx != -1 and dot_idx < 4:
                idx_str = line[:dot_idx].strip()
                try:
                    idx = int(idx_str) - 1
                    translated_map[idx] = line[dot_idx + 1 :].strip()
                except ValueError:
                    pass
        if len(translated_map) == len(all_values):
            translated = []
            pos = 0
            for keys in item_keys:
                if keys:
                    row = {
                        keys[i]: translated_map.get(pos + i, all_values[pos + i])
                        for i in range(len(keys))
                    }
                    translated.append(row)
                else:
                    translated.append(translated_map.get(pos, all_values[pos]))
                pos += len(keys) if keys else 1
            return JSONResponse({"translated": translated, "status": "ok"})
    except Exception:
        pass

    translated = []
    for item in data:
        if isinstance(item, dict):
            row = {}
            for k, v in item.items():
                val_str = str(v) if v is not None else ""
                t, _ = _translate_text(val_str, target_lang)
                row[k] = t
            translated.append(row)
        else:
            t, _ = _translate_text(str(item), target_lang)
            translated.append(t)
    return JSONResponse({"translated": translated, "status": "ok"})


@app.get("/api/text")
def get_static_text(lang: str = "English") -> JSONResponse:
    lang_key = lang if lang in TRANSLATIONS else "English"
    base = dict(TRANSLATIONS["English"])
    if lang_key != "English":
        base.update(TRANSLATIONS.get(lang_key, {}))
    return JSONResponse({"lang": lang_key, "text": base})


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
