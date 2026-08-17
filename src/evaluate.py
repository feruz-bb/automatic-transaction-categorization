"""Metrics, per-class reporting, and the unseen-merchant slice for FIN-001.

The headline metric is **macro-F1**: with 17 roughly balanced categories we care equally
about rare ones (Fees, Transfer), so a macro average is the honest scoreboard and
accuracy is reported alongside only for interpretability.

The unseen-merchant slice is the part that makes error analysis meaningful. Because the
data is templated around real merchants, in-distribution accuracy is very high; the real
question the brief poses is how the model treats a merchant it never saw in training.
``unseen_merchant_mask`` isolates exactly those test rows.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix,
    f1_score,
)


def score(y_true, y_pred) -> dict:
    """Core metrics as a flat dict (JSON/CSV friendly)."""
    return {
        "accuracy": float(accuracy_score(y_true, y_pred)),
        "macro_f1": float(f1_score(y_true, y_pred, average="macro", zero_division=0)),
        "weighted_f1": float(f1_score(y_true, y_pred, average="weighted", zero_division=0)),
        "n": int(len(y_true)),
    }


def per_class_report(y_true, y_pred, labels: list[str]) -> pd.DataFrame:
    """Precision/recall/F1/support per category, sorted by F1 ascending (worst first)."""
    rep = classification_report(
        y_true, y_pred, labels=labels, output_dict=True, zero_division=0
    )
    rows = [
        {"category": c, **{k: rep[c][k] for k in ("precision", "recall", "f1-score", "support")}}
        for c in labels
    ]
    df = pd.DataFrame(rows).rename(columns={"f1-score": "f1"})
    return df.sort_values("f1").reset_index(drop=True)


def confusion(y_true, y_pred, labels: list[str]) -> pd.DataFrame:
    """Confusion matrix as a labelled DataFrame (rows = true, cols = predicted)."""
    cm = confusion_matrix(y_true, y_pred, labels=labels)
    return pd.DataFrame(cm, index=labels, columns=labels)


def top_confusions(y_true, y_pred, labels: list[str], k: int = 10) -> pd.DataFrame:
    """The k most frequent (true -> predicted) off-diagonal mistakes."""
    cm = confusion(y_true, y_pred, labels)
    pairs = []
    for t in labels:
        for p in labels:
            if t != p and cm.loc[t, p] > 0:
                pairs.append({"true": t, "predicted": p, "count": int(cm.loc[t, p])})
    return (
        pd.DataFrame(pairs).sort_values("count", ascending=False).head(k).reset_index(drop=True)
        if pairs
        else pd.DataFrame(columns=["true", "predicted", "count"])
    )


def top_k_accuracy(proba: np.ndarray, classes: np.ndarray, y_true, k: int = 3) -> float:
    """Fraction of rows whose true label is among the model's top-k predicted classes."""
    y_true = np.asarray(y_true)
    topk = np.argsort(proba, axis=1)[:, -k:]
    topk_labels = classes[topk]
    hits = [y_true[i] in topk_labels[i] for i in range(len(y_true))]
    return float(np.mean(hits))


def unseen_merchant_mask(df_split: pd.DataFrame, split_value: str = "test") -> pd.Series:
    """Boolean mask over ``split_value`` rows whose merchant_key never appears in train.

    This is the generalization test: predictions on merchants held out of training.
    """
    train_merchants = set(df_split.loc[df_split["split"] == "train", "merchant_key"])
    sub = df_split[df_split["split"] == split_value]
    return ~sub["merchant_key"].isin(train_merchants)
