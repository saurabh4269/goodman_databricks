from __future__ import annotations

import csv
import json
import re
from collections import defaultdict
from pathlib import Path
from typing import TYPE_CHECKING

from .models import DataElement

if TYPE_CHECKING:
    from pyspark.sql import SparkSession

CREATE_TABLE_PATTERN = re.compile(
    r"create\s+table\s+(?:if\s+not\s+exists\s+)?([\w.`\"]+)\s*\((.*?)\);",
    re.IGNORECASE | re.DOTALL,
)


def _is_spark_available() -> bool:
    try:
        from pyspark.sql import SparkSession

        SparkSession.builder.appName("dpdp-probe").getOrCreate()
        return True
    except Exception:
        return False


class DiscoveryEngine:
    def parse_schema_file(self, path: Path) -> list[DataElement]:
        suffix = path.suffix.lower()
        if suffix == ".sql":
            return self._parse_sql(path)
        if suffix == ".csv":
            return self._parse_csv(path)
        if suffix == ".json":
            return self._parse_json(path)
        raise ValueError(f"Unsupported input format: {suffix}")

    def parse_schema_spark(
        self, spark: "SparkSession", path: Path
    ) -> list[DataElement]:
        suffix = path.suffix.lower()
        if suffix == ".sql":
            return self._parse_sql_spark(spark, path)
        if suffix == ".csv":
            return self._parse_csv_spark(spark, path)
        if suffix == ".json":
            return self._parse_json_spark(spark, path)
        raise ValueError(f"Unsupported input format: {suffix}")

    def _parse_sql(self, path: Path) -> list[DataElement]:
        text = path.read_text(encoding="utf-8", errors="ignore")
        elements: list[DataElement] = []
        for match in CREATE_TABLE_PATTERN.finditer(text):
            table_name = match.group(1).strip('"`')
            body = match.group(2)
            for raw_line in body.splitlines():
                line = raw_line.strip().rstrip(",")
                if not line or line.lower().startswith(
                    ("primary key", "foreign key", "constraint")
                ):
                    continue
                parts = re.split(r"\s+", line, maxsplit=2)
                if len(parts) < 2:
                    continue
                elements.append(
                    DataElement(
                        table_name=table_name,
                        column_name=parts[0].strip('"`'),
                        data_type=parts[1],
                    )
                )
        return elements

    def _parse_sql_spark(self, spark: "SparkSession", path: Path) -> list[DataElement]:
        text = path.read_text(encoding="utf-8", errors="ignore")
        matches = list(CREATE_TABLE_PATTERN.finditer(text))
        if not matches:
            return []

        rows = [
            {"table_name": m.group(1).strip('"`'), "raw_def": m.group(2)}
            for m in matches
        ]
        df = spark.createDataFrame(rows)

        def parse_columns(row: dict) -> list[dict]:
            table = row["table_name"]
            body = row["raw_def"]
            cols = []
            for raw_line in body.splitlines():
                line = raw_line.strip().rstrip(",")
                if not line or line.lower().startswith(
                    ("primary key", "foreign key", "constraint", "index", "unique")
                ):
                    continue
                parts = re.split(r"\s+", line, maxsplit=2)
                if len(parts) < 2:
                    continue
                cols.append(
                    {
                        "table_name": table,
                        "column_name": parts[0].strip('"`'),
                        "data_type": parts[1],
                        "is_nullable": "not null" not in line.lower(),
                    }
                )
            return cols

        from pyspark.sql import functions as F
        from pyspark.sql.types import StringType, ArrayType, StructType, StructField

        parse_udf = F.udf(
            parse_columns,
            ArrayType(
                StructType(
                    [
                        StructField("table_name", StringType()),
                        StructField("column_name", StringType()),
                        StructField("data_type", StringType()),
                        StructField("is_nullable", StringType()),
                    ]
                )
            ),
        )

        exploded = df.withColumn("col", F.explode(parse_udf(F.col("raw_def")))).select(
            "col.table_name", "col.column_name", "col.data_type", "col.is_nullable"
        )

        collected = exploded.collect()
        return [
            DataElement(
                table_name=str(r["table_name"]),
                column_name=str(r["column_name"]),
                data_type=str(r["data_type"]),
            )
            for r in collected
        ]

    def _parse_csv(self, path: Path) -> list[DataElement]:
        with path.open("r", encoding="utf-8", newline="") as handle:
            reader = csv.DictReader(handle)
            rows = list(reader)
            headers = reader.fieldnames or []

        table_name = path.stem
        elements: list[DataElement] = []
        for header in headers:
            samples = [str(row.get(header, "")) for row in rows[:20] if row.get(header)]
            elements.append(
                DataElement(
                    table_name=table_name,
                    column_name=header,
                    data_type="string",
                    sample_values=samples,
                )
            )
        return elements

    def _parse_csv_spark(self, spark: "SparkSession", path: Path) -> list[DataElement]:
        df = (
            spark.read.option("header", "true")
            .option("inferSchema", "true")
            .csv(str(path))
        )
        table_name = path.stem
        schema = df.schema
        collected = df.limit(20).collect()
        sample_map: dict[str, list[str]] = defaultdict(list)
        for row in collected:
            for field in schema:
                val = str(row[field.name]) if row[field.name] is not None else ""
                if val and len(sample_map[field.name]) < 20:
                    sample_map[field.name].append(val)
        elements = []
        for field in schema:
            elements.append(
                DataElement(
                    table_name=table_name,
                    column_name=field.name,
                    data_type=str(field.dataType),
                    sample_values=sample_map.get(field.name, []),
                )
            )
        return elements

    def _parse_json(self, path: Path) -> list[DataElement]:
        payload = json.loads(path.read_text(encoding="utf-8"))
        if isinstance(payload, dict):
            payload = [payload]
        if not isinstance(payload, list) or not payload:
            return []

        table_name = path.stem
        keys = sorted(
            {key for row in payload if isinstance(row, dict) for key in row.keys()}
        )
        elements: list[DataElement] = []
        for key in keys:
            sample_values = [
                str(row.get(key, ""))
                for row in payload[:20]
                if isinstance(row, dict) and key in row
            ]
            elements.append(
                DataElement(
                    table_name=table_name,
                    column_name=key,
                    data_type="string",
                    sample_values=sample_values,
                )
            )
        return elements

    def _parse_json_spark(self, spark: "SparkSession", path: Path) -> list[DataElement]:
        df = spark.read.option("multiline", "true").json(str(path))
        table_name = path.stem
        schema = df.schema
        collected = df.limit(20).collect()
        sample_map: dict[str, list[str]] = defaultdict(list)
        for row in collected:
            for field in schema:
                val = str(row[field.name]) if row[field.name] is not None else ""
                if val and len(sample_map[field.name]) < 20:
                    sample_map[field.name].append(val)
        elements = []
        for field in schema:
            elements.append(
                DataElement(
                    table_name=table_name,
                    column_name=field.name,
                    data_type=str(field.dataType),
                    sample_values=sample_map.get(field.name, []),
                )
            )
        return elements
