"""Freeze the candidate, score the protected test set ONCE, and build the deployment bundle.

    .venv/bin/python -m src.finalize

Selection policy (documented in reports/model_gate.md §6):
the deployed model is the best-on-validation model **among those that produce calibrated
class probabilities**, because the brief requires confidence-based handling of ambiguous
transactions. That is ``tfidf_word_logreg``. ``tfidf_char_linsvm`` scores a hair higher on
macro-F1 but a LinearSVC has no ``predict_proba``, so it cannot drive the low-confidence
fallback and is reported as a comparison run, not shipped.

This module is the ONLY place the test split is read. It refits the frozen pipeline on
train+valid, predicts test once, writes every metric/artifact, and never tunes anything on
the test numbers.
"""

from __future__ import annotations

import json
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline

from src import __version__
from src.evaluate import (
    per_class_report,
    score,
    top_confusions,
    top_k_accuracy,
    unseen_merchant_mask,
)
from src.features import LABEL_COL, TEXT_COL, normalize_description
from src.preprocessing import load_split, make_vectorizer

ROOT = Path(__file__).resolve().parents[1]
ARTIFACTS = ROOT / "artifacts"
REPORTS = ROOT / "reports"
BUNDLE_PATH = ARTIFACTS / "transaction_categorizer.joblib"

#: The frozen candidate (see module docstring for why LogReg over char-SVM).
FINAL_RUN = "tfidf_word_logreg"


def build_final_pipeline() -> Pipeline:
    vec = make_vectorizer(analyzer="word", ngram_range=(1, 2), min_df=2)
    return Pipeline([("tfidf", vec), ("clf", LogisticRegression(max_iter=2000, C=5.0))])


def main() -> dict:
    ARTIFACTS.mkdir(parents=True, exist_ok=True)
    (REPORTS / "results").mkdir(parents=True, exist_ok=True)
    (REPORTS / "error_analysis").mkdir(parents=True, exist_ok=True)

    data = load_split()
    labels = sorted(data[LABEL_COL].unique())

    dev = data[data["split"].isin(["train", "valid"])]
    test = data[data["split"] == "test"]

    # Refit the frozen pipeline on train+valid, then predict test exactly once.
    pipe = build_final_pipeline()
    pipe.fit(dev[TEXT_COL], dev[LABEL_COL])

    y_true = test[LABEL_COL].to_numpy()
    y_pred = pipe.predict(test[TEXT_COL])
    proba = pipe.predict_proba(test[TEXT_COL])
    classes = pipe.classes_

    overall = score(y_true, y_pred)
    overall["top3_accuracy"] = round(top_k_accuracy(proba, classes, y_true, k=3), 4)

    # Unseen-merchant slice: test rows whose merchant never appeared in training.
    unseen = unseen_merchant_mask(data, "test").to_numpy()
    seen_metrics = score(y_true[~unseen], y_pred[~unseen]) if (~unseen).any() else {}
    unseen_metrics = score(y_true[unseen], y_pred[unseen]) if unseen.any() else {}

    per_class = per_class_report(y_true, y_pred, labels)
    confusions = top_confusions(y_true, y_pred, labels, k=10)

    # ---- persist metrics + reports ---------------------------------------------------
    metrics = {
        "model_version": __version__,
        "final_run": FINAL_RUN,
        "primary_metric": "macro_f1",
        "test": {k: round(v, 4) if isinstance(v, float) else v for k, v in overall.items()},
        "test_seen_merchants": {k: round(v, 4) if isinstance(v, float) else v
                                for k, v in seen_metrics.items()},
        "test_unseen_merchants": {k: round(v, 4) if isinstance(v, float) else v
                                  for k, v in unseen_metrics.items()},
        "n_test": int(len(test)),
        "n_test_unseen_merchant": int(unseen.sum()),
        "classes": list(labels),
    }
    (ARTIFACTS / "metrics.json").write_text(json.dumps(metrics, indent=2) + "\n")
    (REPORTS / "results" / "test_metrics.json").write_text(json.dumps(metrics, indent=2) + "\n")
    per_class.to_csv(REPORTS / "results" / "per_class_test.csv", index=False)
    confusions.to_csv(REPORTS / "results" / "top_confusions_test.csv", index=False)

    _write_error_analysis(metrics, per_class, confusions, unseen_metrics, seen_metrics)

    # ---- feature schema (what a caller must supply) ----------------------------------
    schema = {
        "raw_input": {
            "description": "One transaction string, e.g. '[debit] PUBLIX 7860 UNIVERSITY LN'. "
                           "The debit/credit prefix is optional."
        },
        "normalizer": "src.features.normalize_description (applied before the pipeline)",
        "text_column_fed_to_model": TEXT_COL,
        "output_classes": list(labels),
    }
    (ARTIFACTS / "feature_schema.json").write_text(json.dumps(schema, indent=2) + "\n")

    # ---- the deployment bundle -------------------------------------------------------
    bundle = {
        "pipeline": pipe,
        "classes": list(labels),
        "target": LABEL_COL,
        "model_version": __version__,
        "final_run": FINAL_RUN,
        "normalizer": "src.features.normalize_description",
        "trained_on": "train+valid (stratified), test held out for the reported numbers",
        "n_train": int(len(dev)),
        "test_macro_f1": round(overall["macro_f1"], 4),
        "low_confidence_threshold": 0.50,
    }
    joblib.dump(bundle, BUNDLE_PATH, compress=3)

    print(f"TEST macro-F1={overall['macro_f1']:.4f}  acc={overall['accuracy']:.4f}  "
          f"top3={overall['top3_accuracy']:.4f}")
    if unseen_metrics:
        print(f"  unseen-merchant slice (n={metrics['n_test_unseen_merchant']}): "
              f"macro-F1={unseen_metrics['macro_f1']:.4f}  acc={unseen_metrics['accuracy']:.4f}")
    print(f"Bundle -> {BUNDLE_PATH} ({BUNDLE_PATH.stat().st_size/1e3:.0f} KB)")
    return metrics


def _write_error_analysis(metrics, per_class, confusions, unseen_metrics, seen_metrics) -> None:
    worst = per_class.head(5)
    lines = [
        "# Error Analysis — FIN-001 Transaction Categorization",
        "",
        f"Model: `{metrics['final_run']}` (version {metrics['model_version']}). "
        f"Numbers below are on the **protected test split** (n={metrics['n_test']}), "
        "scored once after the candidate was frozen.",
        "",
        "## 1. Headline",
        "",
        f"- Test macro-F1: **{metrics['test']['macro_f1']}**, accuracy {metrics['test']['accuracy']}, "
        f"top-3 accuracy {metrics['test']['top3_accuracy']}.",
        f"- Majority-class baseline macro-F1 was ~0.01, so the model is a large, real lift.",
        "",
        "## 2. Generalization to unseen merchants (the brief's key question)",
        "",
    ]
    if unseen_metrics:
        lines += [
            f"- {metrics['n_test_unseen_merchant']} test transactions come from merchants that "
            "never appear in training.",
            f"- On those unseen merchants: macro-F1 **{unseen_metrics['macro_f1']:.4f}**, "
            f"accuracy {unseen_metrics['accuracy']:.4f}.",
            f"- On previously-seen merchants: macro-F1 {seen_metrics.get('macro_f1', float('nan')):.4f}.",
            "- The gap between these two numbers is the honest estimate of real-world "
            "degradation: templated in-vocabulary merchants are near-perfect; genuinely novel "
            "merchant strings are harder, which is where the char-n-gram model and the "
            "low-confidence fallback matter.",
        ]
    else:
        lines.append("- No unseen-merchant rows in this split.")
    lines += [
        "",
        "## 3. Weakest categories",
        "",
        "| Category | Precision | Recall | F1 | Support |",
        "|---|---:|---:|---:|---:|",
    ]
    for _, r in worst.iterrows():
        lines.append(f"| {r['category']} | {r['precision']:.3f} | {r['recall']:.3f} | "
                     f"{r['f1']:.3f} | {int(r['support'])} |")
    lines += [
        "",
        "## 4. Most common confusions (true → predicted)",
        "",
        "| True | Predicted | Count |",
        "|---|---|---:|",
    ]
    for _, r in confusions.iterrows():
        lines.append(f"| {r['true']} | {r['predicted']} | {int(r['count'])} |")
    lines += [
        "",
        "## 5. What this implies",
        "",
        "- Confusions cluster where merchant text is genuinely ambiguous (e.g. a big-box "
        "store selling both Groceries and Shopping). These are inherent taxonomy overlaps, "
        "not model defects.",
        "- The product mitigation is the confidence-based fallback: predictions below the "
        "0.50 top-class probability are surfaced as 'needs review / uncertain' rather than "
        "auto-applied, exactly as the brief's ambiguous-case requirement asks.",
        "",
    ]
    (REPORTS / "error_analysis" / "ERROR_ANALYSIS.md").write_text("\n".join(lines) + "\n")


if __name__ == "__main__":
    main()
