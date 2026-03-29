from __future__ import annotations

import json
import os
import re
from typing import Any
from urllib import error, request


def generate_indic_summary(
    business_name: str,
    sector: str,
    language: str,
    obligations: list[dict[str, Any]],
    conflicts: list[dict[str, Any]],
    api_key_override: str | None = None,
) -> tuple[str | None, dict[str, Any]]:
    api_key = (api_key_override or os.environ.get("SARVAM_API_KEY", "")).strip()
    model_name = os.environ.get("INDIAN_MODEL_NAME", "sarvam-m")
    if not api_key:
        return None, {
            "indian_model_used": False,
            "indian_model_name": model_name,
            "indian_model_status": "missing_api_key",
        }

    target_language = language if language else "English"
    obligation_lines = "\n".join(
        [
            f"- {row.get('obligation_type', '')}: {row.get('section', '')}"
            for row in obligations[:8]
        ]
    )
    conflict_lines = (
        "\n".join(
            [
                f"- {row.get('regulation', '')}: {row.get('summary', '')}"
                for row in conflicts[:6]
            ]
        )
        or "- none"
    )

    prompt = (
        "Create a concise executive compliance summary for an Indian MSME.\n"
        f"Business: {business_name}\n"
        f"Sector: {sector}\n"
        f"Output Language: {target_language}\n\n"
        "Include:\n"
        "1) top obligations\n2) key conflict risks\n3) immediate next 3 actions\n"
        "Keep it practical and audit-ready.\n\n"
        f"Obligations:\n{obligation_lines}\n\n"
        f"Conflicts:\n{conflict_lines}\n"
    )

    payload = {
        "model": model_name,
        "messages": [
            {
                "role": "system",
                "content": "You are a DPDP compliance assistant. Be precise and concise.",
            },
            {"role": "user", "content": prompt},
        ],
        "max_completion_tokens": 900,
    }

    req = request.Request(
        url="https://api.sarvam.ai/v1/chat/completions",
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}",
        },
        method="POST",
    )
    try:
        with request.urlopen(req, timeout=25) as resp:
            body = json.loads(resp.read().decode("utf-8"))
            content = body["choices"][0]["message"]["content"].strip()
            import re

            content = re.sub(
                r"<\/?start_reasoning\/?>", "", content, flags=re.IGNORECASE
            )
            content = re.sub(r"<\/?reasoning\/?>", "", content, flags=re.IGNORECASE)
            content = re.sub(r"<think>[\s\S]*?</think>", "", content).strip()
            return content, {
                "indian_model_used": True,
                "indian_model_name": model_name,
                "indian_model_status": "ok",
            }
    except error.HTTPError as exc:
        return None, {
            "indian_model_used": False,
            "indian_model_name": model_name,
            "indian_model_status": f"http_{exc.code}",
        }
    except Exception:
        return None, {
            "indian_model_used": False,
            "indian_model_name": model_name,
            "indian_model_status": "request_failed",
        }
