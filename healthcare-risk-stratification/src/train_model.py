#!/usr/bin/env python3
"""Train and evaluate a small, educational healthcare outcome classifier."""
from __future__ import annotations

import argparse
import json
import sqlite3
from pathlib import Path
from typing import Any

import joblib
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score,
    average_precision_score,
    balanced_accuracy_score,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)
from sklearn.model_selection import StratifiedKFold, cross_val_predict
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DATABASE = PROJECT_ROOT / "data" / "processed" / "healthcare.db"
DEFAULT_MODEL = PROJECT_ROOT / "data" / "processed" / "high_risk_model.joblib"
DEFAULT_REPORT = PROJECT_ROOT / "reports" / "model_evaluation.md"
DEFAULT_METRICS = PROJECT_ROOT / "reports" / "model_evaluation.json"
QUERY_FILE = PROJECT_ROOT / "sql" / "03_modeling_dataset.sql"
FEATURES = ["age", "gender", "diagnosis"]


def make_pipeline() -> Pipeline:
    numeric = Pipeline(
        steps=[
            ("imputer", SimpleImputer(strategy="median")),
            ("scaler", StandardScaler()),
        ]
    )
    categorical = Pipeline(
        steps=[
            ("imputer", SimpleImputer(strategy="most_frequent")),
            ("one_hot", OneHotEncoder(handle_unknown="ignore")),
        ]
    )
    preprocessing = ColumnTransformer(
        transformers=[
            ("numeric", numeric, ["age"]),
            ("categorical", categorical, ["gender", "diagnosis"]),
        ]
    )
    return Pipeline(
        steps=[
            ("preprocessing", preprocessing),
            ("classifier", LogisticRegression(max_iter=2000, random_state=42)),
        ]
    )


def summarize_metrics(y_true: pd.Series, y_pred: Any, y_prob: Any) -> dict[str, float | int]:
    tn, fp, fn, tp = confusion_matrix(y_true, y_pred, labels=[0, 1]).ravel()
    specificity = tn / (tn + fp) if (tn + fp) else 0.0
    return {
        "accuracy": float(accuracy_score(y_true, y_pred)),
        "balanced_accuracy": float(balanced_accuracy_score(y_true, y_pred)),
        "precision_high_risk": float(precision_score(y_true, y_pred, zero_division=0)),
        "recall_high_risk": float(recall_score(y_true, y_pred, zero_division=0)),
        "specificity_recovered": float(specificity),
        "f1_high_risk": float(f1_score(y_true, y_pred, zero_division=0)),
        "roc_auc": float(roc_auc_score(y_true, y_prob)),
        "average_precision": float(average_precision_score(y_true, y_prob)),
        "true_negative": int(tn),
        "false_positive": int(fp),
        "false_negative": int(fn),
        "true_positive": int(tp),
    }


def markdown_report(results: dict[str, Any]) -> str:
    model = results["model_metrics"]
    baseline = results["baseline_metrics"]
    return f"""# Educational risk-classification model

## Question and target

This course exercise estimates whether a record belongs to the **high-risk label**: `1` for a recorded outcome of Complicated or Deceased, and `0` for Recovered. It is a retrospective classification exercise, not a clinical definition of patient risk.

## Method

- Records: {results['record_count']}
- Target counts: {results['target_counts']['high_risk']} high-risk labels and {results['target_counts']['recovered']} recovered labels
- Features available at the modeled prediction point: age, gender, and diagnosis
- Model: logistic regression with scaling for age and one-hot encoding for categories
- Evaluation: stratified 5-fold cross-validation; each reported prediction is made for a fold not used to fit that fold's model
- Comparison: a majority-class baseline
- Decision threshold for class metrics: 0.50

Treatment cost, discharge date, and length of stay are excluded because they are known after admission or may reflect later care. Lab values are excluded until units and reference-range definitions are verified.

## Cross-validated results

| Metric | Logistic regression | Majority baseline |
|---|---:|---:|
| Accuracy | {model['accuracy']:.3f} | {baseline['accuracy']:.3f} |
| Balanced accuracy | {model['balanced_accuracy']:.3f} | {baseline['balanced_accuracy']:.3f} |
| High-risk recall | {model['recall_high_risk']:.3f} | {baseline['recall_high_risk']:.3f} |
| Recovered specificity | {model['specificity_recovered']:.3f} | {baseline['specificity_recovered']:.3f} |
| ROC AUC | {model['roc_auc']:.3f} | {baseline['roc_auc']:.3f} |
| Average precision | {model['average_precision']:.3f} | {baseline['average_precision']:.3f} |

## Interpretation and limits

The dataset is small ({results['record_count']} records), class proportions are uneven, and the source data and label definitions have not been clinically validated. Cross-validation provides an educational estimate on this sample; it does not demonstrate performance on new hospitals or future patients. The displayed model score is not a calibrated medical probability and must not be used to make care decisions.

The trained pipeline is saved locally at `{results['model_path_relative']}`. No names or patient IDs are used as model features.
"""


def main() -> int:
    parser = argparse.ArgumentParser(description="Train/evaluate the course risk-classification model.")
    parser.add_argument("--database", type=Path, default=DEFAULT_DATABASE)
    parser.add_argument("--model", type=Path, default=DEFAULT_MODEL)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    parser.add_argument("--metrics", type=Path, default=DEFAULT_METRICS)
    args = parser.parse_args()

    if not args.database.exists():
        parser.error(f"Database not found at {args.database}. Run src/build_database.py first.")

    query = QUERY_FILE.read_text(encoding="utf-8")
    with sqlite3.connect(args.database) as connection:
        frame = pd.read_sql_query(query, connection)

    if frame.empty:
        parser.error("The modeling query returned no records.")
    if frame[FEATURES].isna().any().any() or frame["high_risk"].isna().any():
        parser.error("Model features or target contain missing values; resolve them before training.")

    X = frame[FEATURES]
    y = frame["high_risk"].astype(int)
    if y.nunique() != 2 or int(y.value_counts().min()) < 5:
        parser.error("Both target classes need at least five records for stratified 5-fold evaluation.")

    cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
    pipeline = make_pipeline()
    probabilities = cross_val_predict(pipeline, X, y, cv=cv, method="predict_proba")[:, 1]
    predictions = (probabilities >= 0.5).astype(int)
    model_metrics = summarize_metrics(y, predictions, probabilities)

    # A transparent constant baseline: always predict the majority class and
    # use its prevalence as the same probability for every record.
    majority_class = int(y.mean() >= 0.5)
    baseline_predictions = [majority_class] * len(y)
    baseline_probabilities = [float(y.mean())] * len(y)
    baseline_metrics = summarize_metrics(y, baseline_predictions, baseline_probabilities)

    pipeline.fit(X, y)
    args.model.parent.mkdir(parents=True, exist_ok=True)
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.metrics.parent.mkdir(parents=True, exist_ok=True)
    bundle = {
        "pipeline": pipeline,
        "features": FEATURES,
        "gender_options": sorted(frame["gender"].astype(str).unique().tolist()),
        "diagnosis_options": sorted(frame["diagnosis"].astype(str).unique().tolist()),
        "age_min": int(frame["age"].min()),
        "age_max": int(frame["age"].max()),
        "threshold": 0.5,
        "target_definition": "1 = Complicated or Deceased; 0 = Recovered",
    }
    joblib.dump(bundle, args.model)

    counts = y.value_counts().to_dict()
    results: dict[str, Any] = {
        "record_count": int(len(frame)),
        "target_counts": {
            "high_risk": int(counts.get(1, 0)),
            "recovered": int(counts.get(0, 0)),
        },
        "features": FEATURES,
        "cross_validation": "5-fold stratified out-of-fold; random_state=42",
        "threshold": 0.5,
        "model_metrics": model_metrics,
        "baseline_metrics": baseline_metrics,
        "model_path_relative": str(args.model.relative_to(PROJECT_ROOT))
        if args.model.is_relative_to(PROJECT_ROOT)
        else str(args.model),
    }
    args.report.write_text(markdown_report(results), encoding="utf-8")
    args.metrics.write_text(json.dumps(results, indent=2), encoding="utf-8")

    print(f"Records evaluated: {len(frame)}")
    print(f"High-risk labels: {results['target_counts']['high_risk']}; recovered: {results['target_counts']['recovered']}")
    print("5-fold out-of-fold metrics:")
    for name in ("accuracy", "balanced_accuracy", "recall_high_risk", "specificity_recovered", "roc_auc"):
        print(f"- {name}: model={model_metrics[name]:.3f}; baseline={baseline_metrics[name]:.3f}")
    print(f"Saved local model: {args.model}")
    print(f"Saved report: {args.report}")
    print(f"Saved aggregate metrics: {args.metrics}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
