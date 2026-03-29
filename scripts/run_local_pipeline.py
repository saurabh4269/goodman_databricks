#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

from dpdp_kavach.pipeline import CompliancePipeline


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run DPDP Kavach locally")
    parser.add_argument("--schema", default="data/demo_schema.sql")
    parser.add_argument("--business", default="Demo MSME")
    parser.add_argument("--sector", default="fintech", choices=["fintech", "healthtech", "general"])
    parser.add_argument("--language", default="English")
    parser.add_argument("--output", default="artifacts")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    pipeline = CompliancePipeline(base_dir=Path("src/dpdp_kavach"))
    result, zip_path = pipeline.run(
        schema_path=Path(args.schema),
        business_name=args.business,
        sector=args.sector,
        language=args.language,
        artifact_output_dir=Path(args.output),
    )
    print(json.dumps(pipeline.to_serializable(result), indent=2))
    print(f"Compliance kit: {zip_path}")


if __name__ == "__main__":
    main()
