from __future__ import annotations

import re
from collections import defaultdict
from typing import TYPE_CHECKING, Any

from .models import ClassifiedElement, DataElement

if TYPE_CHECKING:
    from pyspark.sql import SparkSession


class DataClassifier:
    def __init__(self, taxonomy: list[dict[str, Any]]) -> None:
        self.taxonomy = taxonomy

    def classify_spark(
        self, spark: "SparkSession", elements: list[DataElement], sector: str
    ) -> list[ClassifiedElement]:
        from pyspark.sql import functions as F
        from pyspark.sql.types import DoubleType, StringType, StructField, StructType

        taxonomy_bc = spark.sparkContext.broadcast(self.taxonomy)

        def _heuristic_classify_static(name: str) -> tuple | None:
            name_lower = name.lower()
            name_parts = set(name_lower.replace("_", " ").replace("-", " ").split())

            if any(
                t in name_parts
                for t in (
                    "first",
                    "last",
                    "full",
                    "given",
                    "middle",
                    "surname",
                    "sur",
                    "name",
                    "fname",
                    "lname",
                    "username",
                )
            ):
                return ("name", "personal", 0.80, "heuristic:name")

            if any(
                t in name_lower
                for t in (
                    "address",
                    "street",
                    "lane",
                    "road",
                    "area",
                    "locality",
                    "city",
                    "town",
                    "village",
                    "district",
                    "state",
                    "region",
                    "country",
                    "pin",
                    "zip",
                    "po_box",
                    "pobox",
                    "house",
                    "flat",
                    "building",
                    "landmark",
                    "residence",
                )
            ):
                return ("address", "personal", 0.80, "heuristic:address")

            if any(
                t in name_lower
                for t in (
                    "id",
                    "no",
                    "number",
                    "num",
                    "reg",
                    "roll",
                    "serial",
                    "enrollment",
                    "registration",
                    "ref",
                    "case",
                    "ticket",
                    "uuid",
                    "client",
                    "participant",
                    "member",
                    "staff",
                )
            ):
                if not any(
                    t in name_lower for t in ("amount", "price", "qty", "quantity")
                ):
                    return ("identifier", "personal", 0.75, "heuristic:id")

            if any(
                t in name_lower
                for t in (
                    "gender",
                    "sex",
                    "marital",
                    "religion",
                    "caste",
                    "income",
                    "salary",
                    "occupation",
                    "employer",
                    "designation",
                    "department",
                    "company",
                    "organization",
                    "org",
                )
            ):
                return ("demographic", "sensitive", 0.75, "heuristic:demographic")

            return None

        def _classify_row(
            name: str,
            text_blob: str,
            table_name: str,
            sibling_names: list[str],
        ) -> tuple:
            name_lower = name.lower()
            for entry in taxonomy_bc.value:
                for keyword in entry["common_column_names"]:
                    if keyword.lower() in name_lower:
                        purpose = _infer_purpose_static(
                            table_name, name, sibling_names, sector
                        )
                        return (
                            entry["pii_category"],
                            entry["sensitivity"],
                            0.95,
                            purpose,
                            "rule:name",
                        )

                pattern = entry.get("regex", "")
                if pattern and text_blob and re.search(pattern, text_blob):
                    purpose = _infer_purpose_static(
                        table_name, name, sibling_names, sector
                    )
                    return (
                        entry["pii_category"],
                        entry["sensitivity"],
                        0.90,
                        purpose,
                        "rule:value",
                    )

            heuristic = _heuristic_classify_static(name)
            if heuristic:
                purpose = _infer_purpose_static(table_name, name, sibling_names, sector)
                return (heuristic[0], heuristic[1], heuristic[2], purpose, heuristic[3])

            purpose = _infer_purpose_static(table_name, name, sibling_names, sector)
            if name_lower.endswith("id"):
                return ("identifier", "personal", 0.50, purpose, "heuristic")
            return ("non_pii", "none", 0.30, purpose, "default")

        def _infer_purpose_static(
            table_name: str, column_name: str, sibling_columns: list[str], sector: str
        ) -> str:
            tokens = " ".join(
                [table_name.lower(), column_name.lower(), *sibling_columns]
            )
            if any(
                token in tokens
                for token in ("payment", "transaction", "utr", "ifsc", "upi")
            ):
                return "payments"
            if any(
                token in tokens
                for token in ("diagnosis", "prescription", "medical", "patient")
            ):
                return "care_delivery"
            if any(
                token in tokens for token in ("campaign", "click", "analytics", "ad_")
            ):
                return "marketing"
            if "employee" in tokens:
                return "employment"

            if "classroom" in tokens or "grade" in tokens or "section" in tokens:
                return "education"

            if (
                "order" in tokens
                or "product" in tokens
                or "sku" in tokens
                or "item" in tokens
            ):
                return "commerce"

            if (
                "classroom" not in tokens
                and "grade" not in tokens
                and "section" not in tokens
            ):
                if sector == "healthtech":
                    return "care_delivery"
                if sector == "fintech":
                    return "kyc"

            return "service_delivery"

        classify_schema = StructType(
            [
                StructField("pii_category", StringType()),
                StructField("sensitivity", StringType()),
                StructField("confidence", DoubleType()),
                StructField("purpose", StringType()),
                StructField("source", StringType()),
            ]
        )

        classify_udf = F.udf(_classify_row, classify_schema)

        rows = []
        table_to_columns: dict[str, list[str]] = defaultdict(list)
        for el in elements:
            table_to_columns[el.table_name].append(el.column_name.lower())

        for idx, el in enumerate(elements):
            text_blob = " ".join(el.sample_values)
            siblings = table_to_columns.get(el.table_name, [])
            rows.append(
                {
                    "idx": idx,
                    "table_name": el.table_name,
                    "column_name": el.column_name,
                    "data_type": el.data_type,
                    "text_blob": text_blob,
                    "sibling_names": siblings,
                }
            )

        df = spark.createDataFrame(rows)
        classified_df = df.select(
            "idx",
            "table_name",
            "column_name",
            "data_type",
            classify_udf(
                F.col("column_name"),
                F.col("text_blob"),
                F.col("table_name"),
                F.col("sibling_names"),
            ).alias("classification"),
        ).select(
            "idx",
            "table_name",
            "column_name",
            "data_type",
            "classification.*",
        )

        collected = classified_df.orderBy("idx").collect()
        return [
            ClassifiedElement(
                table_name=str(r["table_name"]),
                column_name=str(r["column_name"]),
                data_type=str(r["data_type"]),
                pii_category=str(r["pii_category"]),
                sensitivity=str(r["sensitivity"]),
                confidence=float(r["confidence"]),
                purpose=str(r["purpose"]),
                source=str(r["source"]),
            )
            for r in collected
        ]

    def classify(
        self, elements: list[DataElement], sector: str
    ) -> list[ClassifiedElement]:
        classified: list[ClassifiedElement] = []
        table_to_columns: dict[str, list[str]] = defaultdict(list)
        for element in elements:
            table_to_columns[element.table_name].append(element.column_name.lower())

        for element in elements:
            label, sensitivity, confidence, source = self._classify_element(element)
            purpose = self._infer_purpose(
                element, table_to_columns[element.table_name], sector
            )
            classified.append(
                ClassifiedElement(
                    table_name=element.table_name,
                    column_name=element.column_name,
                    data_type=element.data_type,
                    pii_category=label,
                    sensitivity=sensitivity,
                    confidence=confidence,
                    purpose=purpose,
                    source=source,
                )
            )
        return classified

    def _classify_element(self, element: DataElement) -> tuple[str, str, float, str]:
        name = element.column_name.lower()
        text_blob = " ".join(element.sample_values)

        for entry in self.taxonomy:
            for keyword in entry["common_column_names"]:
                if keyword.lower() in name:
                    return (
                        entry["pii_category"],
                        entry["sensitivity"],
                        0.95,
                        "rule:name",
                    )

            pattern = entry.get("regex", "")
            if pattern and text_blob and re.search(pattern, text_blob):
                return entry["pii_category"], entry["sensitivity"], 0.90, "rule:value"

        heuristic = self._heuristic_classify(name)
        if heuristic:
            return heuristic

        if name.endswith("id"):
            return "identifier", "personal", 0.50, "heuristic"
        return "non_pii", "none", 0.30, "default"

    def _heuristic_classify(self, name: str) -> tuple[str, str, float, str] | None:
        name_parts = set(name.replace("_", " ").replace("-", " ").split())

        if any(
            t in name_parts
            for t in (
                "first",
                "last",
                "full",
                "given",
                "middle",
                "middle",
                "surname",
                "sur",
                "name",
                "fname",
                "lname",
                "username",
            )
        ):
            return "name", "personal", 0.80, "heuristic:name"

        if any(
            t in name
            for t in (
                "address",
                "street",
                "lane",
                "road",
                "area",
                "locality",
                "city",
                "town",
                "village",
                "district",
                "state",
                "region",
                "country",
                "pin",
                "zip",
                "po_box",
                "pobox",
                "house",
                "flat",
                "building",
                "landmark",
                "residence",
            )
        ):
            return "address", "personal", 0.80, "heuristic:address"

        if any(
            t in name
            for t in (
                "id",
                "no",
                "number",
                "num",
                "reg",
                "roll",
                "serial",
                "enrollment",
                "registration",
                "ref",
                "case",
                "ticket",
                "uuid",
                "client",
                "participant",
                "member",
                "staff",
            )
        ):
            if not any(t in name for t in ("amount", "price", "qty", "quantity")):
                return "identifier", "personal", 0.75, "heuristic:id"

        if any(
            t in name
            for t in (
                "gender",
                "sex",
                "marital",
                "religion",
                "caste",
                "income",
                "salary",
                "occupation",
                "employer",
                "designation",
                "department",
                "company",
                "organization",
                "org",
            )
        ):
            return "demographic", "sensitive", 0.75, "heuristic:demographic"

        return None

    def _infer_purpose(
        self, element: DataElement, sibling_columns: list[str], sector: str
    ) -> str:
        tokens = " ".join(
            [element.table_name.lower(), element.column_name.lower(), *sibling_columns]
        )
        if any(
            token in tokens
            for token in ("payment", "transaction", "utr", "ifsc", "upi")
        ):
            return "payments"
        if any(
            token in tokens
            for token in ("diagnosis", "prescription", "medical", "patient")
        ):
            return "care_delivery"
        if any(token in tokens for token in ("campaign", "click", "analytics", "ad_")):
            return "marketing"
        if "employee" in tokens:
            return "employment"

        if "classroom" in tokens or "grade" in tokens or "section" in tokens:
            return "education"

        if (
            "order" in tokens
            or "product" in tokens
            or "sku" in tokens
            or "item" in tokens
        ):
            return "commerce"

        if (
            "classroom" not in tokens
            and "grade" not in tokens
            and "section" not in tokens
        ):
            if sector == "healthtech":
                return "care_delivery"
            if sector == "fintech":
                return "kyc"

        return "service_delivery"
