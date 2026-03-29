#!/usr/bin/env python3
"""
Generate synthetic training data for the purpose classifier and
pre-train + persist the sklearn pipeline.

Outputs:
  src/dpdp_kavach/config/purpose_training_data.json  -- training examples
  artifacts/model_store/sklearn_purpose_pipeline.joblib -- saved sklearn pipeline
"""

from __future__ import annotations

import itertools
import random
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

DATA_OUT = ROOT / "src" / "dpdp_kavach" / "config" / "purpose_training_data.json"
MODEL_OUT_DIR = ROOT / "artifacts" / "model_store"
MODEL_OUT = MODEL_OUT_DIR / "sklearn_purpose_pipeline.joblib"

random.seed(42)

PAYMENTS_TERMS = [
    "transaction",
    "txn",
    "payment",
    "settle",
    "settlement",
    "ledger",
    "reconcile",
    "reconciliation",
    "upi",
    "imps",
    "neft",
    "rtgs",
    "wallet",
    "balance",
    "credit",
    "debit",
    "amount",
    "currency",
    "ifsc",
    "bank",
    "account",
    "beneficiary",
    "payee",
    "payer",
    "sender",
    "receiver",
    "refund",
    "chargeback",
    "dispute",
    "razorpay",
    "phonepe",
    "paytm",
    "stripe",
    "invoice",
    "billing",
    "subscription",
    "recurring",
    "mandate",
    "autopay",
    "emi",
    "installment",
    "split",
    "payout",
    "disbursement",
    "UTR",
    "vpa",
    "merchant",
    "order",
    "cart",
    "checkout",
    "gateway",
    "auth",
    "capture",
    "void",
    "refund_id",
    "txn_id",
    "order_id",
    "rrn",
    "auth_code",
]
KYC_TERMS = [
    "customer",
    "kyc",
    "onboard",
    "onboarding",
    "verify",
    "verification",
    "identity",
    "document",
    "pan",
    "aadhaar",
    "adhar",
    "voter",
    "passport",
    "driving",
    "license",
    "dl",
    "ein",
    "tan",
    "gstin",
    "cin",
    "llpin",
    "incorporation",
    "tax",
    "tax_id",
    "fingerprint",
    "face",
    "biometric",
    "liveness",
    "selfie",
    "video",
    "kyc_status",
    "kyc_tier",
    "aml",
    "caml",
    "fatca",
    "crs",
    "pep",
    "sanctions",
    "screening",
    "consent",
    "aof",
    "form_a",
    "ekyc",
    "ekyc_status",
    "dedupe",
    "fraud_score",
    "risk_tier",
    "tier",
    "limit",
    "account_type",
    "business_type",
    "entity_type",
]
CARE_TERMS = [
    "patient",
    "doctor",
    "physician",
    "clinic",
    "hospital",
    "diagnostic",
    "lab",
    "pathology",
    "radiology",
    "imaging",
    "xray",
    "mri",
    "ct",
    "ultrasound",
    "ecg",
    "diagnosis",
    "prognosis",
    "treatment",
    "therapy",
    "medication",
    "prescription",
    "rx",
    "drug",
    "dosage",
    "pharmacy",
    "chemist",
    "vitals",
    "bp",
    "heart_rate",
    "temperature",
    "spo2",
    "weight",
    "height",
    "bmi",
    "history",
    "allergy",
    "condition",
    "disease",
    "icd",
    "icd10",
    "icd11",
    "procedure",
    "surgery",
    "appointment",
    "booking",
    "slot",
    "bed",
    "ward",
    "icu",
    "emergency",
    "icu",
    "referral",
    "discharge",
    "admission",
    "bill",
    "insurance",
    "claim",
    "coverage",
    "copay",
    "preauth",
    "authorization",
    "referrer",
    "specialist",
    "gp",
]
MARKETING_TERMS = [
    "campaign",
    "ad",
    "advertisement",
    "creative",
    "banner",
    "impression",
    "click",
    "ctr",
    "conversion",
    "cpc",
    "cpm",
    "cpa",
    "roas",
    "attribution",
    "utm_source",
    "utm_medium",
    "utm_campaign",
    "utm_term",
    "utm_content",
    "funnel",
    "acquisition",
    "retention",
    "churn",
    "ltv",
    "clv",
    "segment",
    "cohort",
    "persona",
    "audience",
    "targeting",
    "lookalike",
    "suppression",
    "exclusion",
    "ab_test",
    "experiment",
    "variant",
    "control",
    "lift",
    "engagement",
    "like",
    "share",
    "comment",
    "view",
    "watch_time",
    "open_rate",
    "click_rate",
    "unsubscribe",
    "preference",
    "consent",
    "dni",
    "personalization",
    "recommendation",
    "abandon",
    "cart_abandon",
    "email",
    "push",
    "notification",
    "sms",
    "whatsapp",
    "in_app",
    "offer",
    "coupon",
    "discount",
]
EMPLOYMENT_TERMS = [
    "employee",
    "emp",
    "staff",
    "worker",
    "personnel",
    "hr",
    "human_resource",
    "payroll",
    "salary",
    "compensation",
    "bonus",
    "variable",
    "ctc",
    "gross",
    "net",
    "deduction",
    "tds",
    "pf",
    "epf",
    "esi",
    "hra",
    "allowance",
    "reimbursement",
    "attendance",
    "leave",
    "pto",
    "sick",
    "casual",
    "earned",
    "holiday",
    "wfh",
    "remote",
    "shift",
    "timesheet",
    "clock_in",
    "clock_out",
    "overtime",
    "ot",
    "performance",
    "review",
    "rating",
    "appraisal",
    "kpi",
    "okr",
    "promotion",
    "increment",
    "designation",
    "role",
    "department",
    "team",
    "manager",
    "reporting",
    "org",
    "hierarchy",
    "onboarding",
    "exit",
    "resignation",
    "termination",
    "firing",
    "probation",
    "confirmation",
    "contractor",
    "freelancer",
    "vendor",
    "consultant",
    "bank_ac",
    "ifsc_code",
    "pan_num",
    "uan",
    "aadhaar_num",
]
SERVICE_TERMS = [
    "user",
    "customer",
    "account",
    "profile",
    "registration",
    "signup",
    "login",
    "password",
    "otp",
    "token",
    "session",
    "refresh",
    "preference",
    "setting",
    "notification_pref",
    "email_pref",
    "sms_pref",
    "push_pref",
    "consent_pref",
    "subscription",
    "plan",
    "tier",
    "free",
    "premium",
    "enterprise",
    "upgrade",
    "downgrade",
    "cancel",
    "churn",
    "reactivation",
    "support",
    "ticket",
    "issue",
    "complaint",
    "resolution",
    "feedback",
    "rating",
    "review",
    "referral_code",
    "loyalty",
    "points",
    "reward",
    "redeem",
    "voucher",
    "coupon",
    "wishlist",
    "cart",
    "order",
    "delivery",
    "shipping",
    "address",
    "pincode",
    "tracking",
    "status",
    "return",
    "exchange",
    "refund",
    "invoice",
    "receipt",
    "statement",
    "device",
    "os",
    "browser",
    "ip",
    "location",
    "geo",
    "language",
    "timezone",
]

TABLE_PREFIXES = [
    "tbl",
    "table",
    "dwh",
    "dw",
    "stg",
    "stage",
    "raw",
    "ods",
    "mart",
    "analytics",
    "rpt",
    "report",
    "summary",
    "agg",
    "dim",
    "fact",
]

DATA_TYPES = [
    "string",
    "varchar",
    "text",
    "char",
    "nvarchar",
    "integer",
    "bigint",
    "decimal",
    "numeric",
    "float",
    "double",
    "boolean",
    "timestamp",
    "date",
    "datetime",
    "array",
    "json",
    "uuid",
]

PII_CATEGORIES = [
    "none",
    "name",
    "email",
    "phone",
    "aadhaar",
    "pan",
    "passport",
    "financial",
    "health",
    "biometric",
    "location",
    "device",
    "id_number",
    "authentication",
    "demographic",
]


def make_text(purpose_terms: list[str], label: str) -> str:
    """Build a realistic column text from domain terms."""
    table = random.choice(TABLE_PREFIXES) + "_" + random.choice(purpose_terms)
    col = random.choice(purpose_terms)
    dtype = random.choice(DATA_TYPES)
    pii = random.choice(PII_CATEGORIES)
    parts = random.sample(purpose_terms, min(random.randint(3, 5), len(purpose_terms)))
    extra = " ".join(parts)
    return f"{table} {col} {dtype} {pii} {extra}"


def generate_category(terms: list[str], label: str, n: int) -> list[dict]:
    texts = []
    for _ in range(n):
        texts.append({"text": make_text(terms, label), "label": label})
    return texts


def main() -> None:
    categories = [
        (PAYMENTS_TERMS, "payments"),
        (KYC_TERMS, "kyc"),
        (CARE_TERMS, "care_delivery"),
        (MARKETING_TERMS, "marketing"),
        (EMPLOYMENT_TERMS, "employment"),
        (SERVICE_TERMS, "service_delivery"),
    ]

    TOTAL_PER_CATEGORY = 120
    training_data: list[dict] = []
    for terms, label in categories:
        generated = generate_category(terms, label, TOTAL_PER_CATEGORY)
        training_data.extend(generated)

    random.shuffle(training_data)

    print(f"Generated {len(training_data)} training examples:")
    from collections import Counter

    counts = Counter(item["label"] for item in training_data)
    for label, cnt in sorted(counts.items()):
        print(f"  {label}: {cnt}")

    DATA_OUT.parent.mkdir(parents=True, exist_ok=True)
    import json

    with open(DATA_OUT, "w", encoding="utf-8") as f:
        json.dump(training_data, f, indent=2, ensure_ascii=False)
    print(f"\nSaved training data to {DATA_OUT}")

    print("\nTraining sklearn pipeline...")
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.linear_model import LogisticRegression
    from sklearn.pipeline import Pipeline

    X = [item["text"] for item in training_data]
    y = [item["label"] for item in training_data]

    pipeline = Pipeline(
        [
            ("tfidf", TfidfVectorizer(ngram_range=(1, 2), min_df=2, max_features=4096)),
            (
                "clf",
                LogisticRegression(max_iter=500, C=1.0, solver="lbfgs"),
            ),
        ]
    )
    pipeline.fit(X, y)
    print(
        f"Pipeline fitted. Vocabulary size: {len(pipeline.named_steps['tfidf'].vocabulary_)}"
    )

    MODEL_OUT_DIR.mkdir(parents=True, exist_ok=True)
    import joblib

    joblib.dump(pipeline, MODEL_OUT)
    print(f"Saved sklearn pipeline to {MODEL_OUT}")

    from collections import Counter

    preds = pipeline.predict(X)
    from sklearn.metrics import accuracy_score, classification_report

    print(f"\nTraining accuracy: {accuracy_score(y, preds):.4f}")
    print(classification_report(y, preds, digits=2))

    print("\nDone!")


if __name__ == "__main__":
    main()
