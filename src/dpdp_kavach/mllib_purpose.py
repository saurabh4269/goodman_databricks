from __future__ import annotations

from datetime import UTC, datetime
from dataclasses import replace
from pathlib import Path
from typing import Any

from .models import ClassifiedElement


def _fallback_with_sklearn(
    classified: list[ClassifiedElement],
    train_rows: list[tuple[str, str]],
    model_store_dir: Path | None = None,
) -> tuple[list[ClassifiedElement], dict[str, Any]]:
    try:
        import joblib

        from sklearn.feature_extraction.text import TfidfVectorizer
        from sklearn.linear_model import LogisticRegression
        from sklearn.pipeline import Pipeline
    except Exception:
        return classified, {
            "mllib_used": False,
            "mllib_predictions": 0,
            "purpose_classifier_version": "unavailable",
            "mllib_status": "spark_unavailable",
            "ml_model_used": False,
            "ml_engine": "none",
        }

    sklearn_model_path = (
        (model_store_dir / "sklearn_purpose_pipeline.joblib")
        if model_store_dir
        else None
    )
    pipeline: Pipeline | None = None
    model_version = "sklearn-fallback-v1"

    if sklearn_model_path and sklearn_model_path.exists():
        try:
            pipeline = joblib.load(sklearn_model_path)
            model_version = "sklearn-pipeline-v1"
        except Exception:
            pipeline = None

    if pipeline is None:
        vectorizer = TfidfVectorizer(ngram_range=(1, 2), min_df=2, max_features=4096)
        x_train = vectorizer.fit_transform([row[0] for row in train_rows])
        y_train = [row[1] for row in train_rows]
        clf = LogisticRegression(max_iter=500, C=1.0, solver="lbfgs")
        clf.fit(x_train, y_train)
        pipeline = Pipeline([("tfidf", vectorizer), ("clf", clf)])
        model_version = "sklearn-fallback-v1"

        if sklearn_model_path and model_store_dir:
            try:
                model_store_dir.mkdir(parents=True, exist_ok=True)
                joblib.dump(pipeline, sklearn_model_path)
                model_version = "sklearn-pipeline-v1"
            except Exception:
                pass

    texts = [
        f"{row.table_name} {row.column_name} {row.data_type} {row.pii_category} {row.purpose}"
        for row in classified
    ]
    predictions = pipeline.predict(texts)

    updated: list[ClassifiedElement] = []
    changed = 0
    for idx, predicted_label in enumerate(predictions):
        original = classified[idx]
        use_model = (
            original.source in {"default", "heuristic"} or original.confidence < 0.75
        )
        final_purpose = str(predicted_label) if use_model else original.purpose
        final_source = f"{original.source}|sklearn" if use_model else original.source
        if final_purpose != original.purpose:
            changed += 1
        updated.append(replace(original, purpose=final_purpose, source=final_source))

    return updated, {
        "mllib_used": False,
        "mllib_predictions": changed,
        "purpose_classifier_version": model_version,
        "mllib_status": "spark_unavailable_sklearn_fallback",
        "ml_model_used": True,
        "ml_engine": "sklearn",
    }


def enrich_purpose_with_mllib(
    classified: list[ClassifiedElement],
    training_samples: list[dict[str, Any]],
    model_store_dir: Path | None = None,
) -> tuple[list[ClassifiedElement], dict[str, Any]]:
    if not classified or not training_samples:
        return classified, {
            "mllib_used": False,
            "mllib_predictions": 0,
            "purpose_classifier_version": "unavailable",
            "mllib_status": "no_training_data",
            "ml_model_used": False,
            "ml_engine": "none",
        }

    try:
        from pyspark.ml import Pipeline
        from pyspark.ml import PipelineModel
        from pyspark.ml.classification import LogisticRegression
        from pyspark.ml.feature import HashingTF, IDF, StringIndexer, Tokenizer
        from pyspark.sql import SparkSession
        from pyspark.sql import functions as F

        spark = SparkSession.builder.appName("dpdp-kavach-purpose").getOrCreate()
    except Exception:
        train_rows = [
            (item["text"], item["label"])
            for item in training_samples
            if item.get("text") and item.get("label")
        ]
        if len(train_rows) >= 4:
            return _fallback_with_sklearn(classified, train_rows, model_store_dir)
        return classified, {
            "mllib_used": False,
            "mllib_predictions": 0,
            "purpose_classifier_version": "unavailable",
            "mllib_status": "spark_unavailable",
            "ml_model_used": False,
            "ml_engine": "none",
        }

    train_rows = [
        (item["text"], item["label"])
        for item in training_samples
        if item.get("text") and item.get("label")
    ]
    if len(train_rows) < 4:
        return classified, {
            "mllib_used": False,
            "mllib_predictions": 0,
            "purpose_classifier_version": "unavailable",
            "mllib_status": "insufficient_training_rows",
            "ml_model_used": False,
            "ml_engine": "none",
        }

    train_df = spark.createDataFrame(train_rows, ["text", "label"])
    scan_rows = [
        (
            idx,
            f"{row.table_name} {row.column_name} {row.data_type} {row.pii_category} {row.purpose}",
            row.source,
        )
        for idx, row in enumerate(classified)
    ]
    scan_df = spark.createDataFrame(scan_rows, ["row_id", "text", "source"])

    label_indexer = StringIndexer(
        inputCol="label", outputCol="label_idx", handleInvalid="keep"
    )
    tokenizer = Tokenizer(inputCol="text", outputCol="tokens")
    hashing_tf = HashingTF(
        inputCol="tokens", outputCol="raw_features", numFeatures=2048
    )
    idf = IDF(inputCol="raw_features", outputCol="features")
    lr = LogisticRegression(
        featuresCol="features", labelCol="label_idx", maxIter=40, regParam=0.05
    )

    model_path = None
    model_version = "runtime-ephemeral"
    if model_store_dir is not None:
        model_store_dir.mkdir(parents=True, exist_ok=True)
        model_path = model_store_dir / "purpose_classifier"

    model = None
    if model_path is not None and model_path.exists():
        try:
            model = PipelineModel.load(str(model_path))
            model_version = "purpose_classifier-v1"
        except Exception:
            model = None

    if model is None:
        pipeline = Pipeline(stages=[label_indexer, tokenizer, hashing_tf, idf, lr])
        model = pipeline.fit(train_df)
        if model_path is not None:
            try:
                model.write().overwrite().save(str(model_path))
                model_version = "purpose_classifier-v1"
            except Exception:
                model_version = f"runtime-{datetime.now(UTC).strftime('%Y%m%d%H%M%S')}"

    predicted = model.transform(scan_df)

    labels = model.stages[0].labels  # StringIndexerModel labels
    predicted_rows = (
        predicted.select(
            "row_id",
            "source",
            F.col("prediction").cast("int").alias("prediction"),
            F.array_max(F.col("probability").cast("array<double>")).alias("score"),
        )
        .orderBy("row_id")
        .collect()
    )

    updated: list[ClassifiedElement] = []
    changed = 0
    for row in predicted_rows:
        original = classified[row["row_id"]]
        label_idx = row["prediction"]
        predicted_label = (
            labels[label_idx] if 0 <= label_idx < len(labels) else original.purpose
        )
        # Keep strong rules as-is; use MLlib for weaker/default detections.
        use_mllib = (
            original.source in {"default", "heuristic"} or original.confidence < 0.75
        )
        final_purpose = predicted_label if use_mllib else original.purpose
        final_source = f"{original.source}|mllib" if use_mllib else original.source
        if final_purpose != original.purpose:
            changed += 1
        updated.append(replace(original, purpose=final_purpose, source=final_source))

    return updated, {
        "mllib_used": True,
        "mllib_predictions": changed,
        "purpose_classifier_version": model_version,
        "mllib_status": "ok",
        "ml_model_used": True,
        "ml_engine": "mllib",
    }
