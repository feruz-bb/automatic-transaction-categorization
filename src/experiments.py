"""Model-Gate experiment sweep for FIN-001.

    .venv/bin/python -m src.experiments            # full sweep (incl. embedding run)
    .venv/bin/python -m src.experiments --quick    # classic runs only, skip embeddings

PROTECTED-TEST RULE
-------------------
Every run in this sweep is trained on the TRAIN split and scored on the VALIDATION split.
The TEST split is never loaded here. The candidate is chosen by validation macro-F1; the
test set is touched exactly once, later, by ``src/finalize.py``, after the winner is frozen.

Writes ``reports/experiment_record.csv`` (the human-readable record) and, when MLflow is
installed, logs params + metrics to a local ``mlflow.db`` under experiment "FIN-001".
"""

from __future__ import annotations

import argparse
import time
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.dummy import DummyClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.naive_bayes import ComplementNB
from sklearn.pipeline import Pipeline
from sklearn.svm import LinearSVC

from src.evaluate import score
from src.features import LABEL_COL, TEXT_COL
from src.preprocessing import load_split, make_vectorizer, write_manifest

warnings.filterwarnings("ignore", category=UserWarning)

ROOT = Path(__file__).resolve().parents[1]
REPORTS = ROOT / "reports"
RECORD_PATH = REPORTS / "experiment_record.csv"
EMBED_MODEL = "all-MiniLM-L6-v2"

#: One row per run. Exactly one major factor changes between comparable runs.
CLASSIC_RUNS = [
    {"run": "baseline_majority", "kind": "baseline",
     "hypothesis": "Predicting the most frequent class sets the floor any model must beat."},
    {"run": "tfidf_word_logreg", "kind": "tfidf", "analyzer": "word", "ngram": (1, 2),
     "clf": "logreg",
     "hypothesis": "Merchant words alone linearly separate the 17 categories."},
    {"run": "tfidf_char_linsvm", "kind": "tfidf", "analyzer": "char_wb", "ngram": (3, 5),
     "clf": "linsvm",
     "hypothesis": "Character n-grams generalize better to unseen/misspelled merchants."},
    {"run": "tfidf_word_complementnb", "kind": "tfidf", "analyzer": "word", "ngram": (1, 2),
     "clf": "cnb",
     "hypothesis": "A fast Naive-Bayes text baseline is competitive with linear models."},
]
EMBED_RUN = {
    "run": "embed_minilm_logreg", "kind": "embed", "clf": "logreg",
    "hypothesis": "Semantic sentence embeddings beat sparse bag-of-words on this text.",
}


# --------------------------------------------------------------------------------------
# Estimator builders
# --------------------------------------------------------------------------------------
def _classifier(name: str):
    if name == "logreg":
        return LogisticRegression(max_iter=2000, C=5.0)
    if name == "linsvm":
        return LinearSVC(C=1.0)
    if name == "cnb":
        return ComplementNB()
    raise ValueError(name)


def build_tfidf_pipeline(cfg: dict) -> Pipeline:
    vec = make_vectorizer(analyzer=cfg["analyzer"], ngram_range=cfg["ngram"], min_df=2)
    return Pipeline([("tfidf", vec), ("clf", _classifier(cfg["clf"]))])


class SentenceEmbedder:
    """Thin sklearn-style transformer wrapping sentence-transformers.

    Kept out of ``src/inference.py`` on purpose: the deployed model is the TF-IDF
    pipeline, so torch/sentence-transformers never reach the Streamlit host.
    """

    def __init__(self, model_name: str = EMBED_MODEL):
        from sentence_transformers import SentenceTransformer

        self.model = SentenceTransformer(model_name)

    def fit(self, X, y=None):
        return self

    def transform(self, X):
        return self.model.encode(list(X), batch_size=256, show_progress_bar=False,
                                 normalize_embeddings=True)


def build_embed_pipeline() -> Pipeline:
    return Pipeline([("embed", SentenceEmbedder()), ("clf", LogisticRegression(max_iter=2000, C=5.0))])


# --------------------------------------------------------------------------------------
# Run a single experiment
# --------------------------------------------------------------------------------------
def run_one(cfg: dict, data: pd.DataFrame) -> dict:
    tr = data[data["split"] == "train"]
    va = data[data["split"] == "valid"]
    Xtr, ytr = tr[TEXT_COL], tr[LABEL_COL]
    Xva, yva = va[TEXT_COL], va[LABEL_COL]

    t0 = time.time()
    if cfg["kind"] == "baseline":
        est = DummyClassifier(strategy="most_frequent")
        est.fit(Xtr.values.reshape(-1, 1), ytr)
        pred = est.predict(Xva.values.reshape(-1, 1))
    else:
        est = build_tfidf_pipeline(cfg) if cfg["kind"] == "tfidf" else build_embed_pipeline()
        est.fit(Xtr, ytr)
        pred = est.predict(Xva)
    elapsed = time.time() - t0

    metrics = score(yva, pred)
    return {
        "run": cfg["run"],
        "kind": cfg["kind"],
        "hypothesis": cfg["hypothesis"],
        "valid_accuracy": round(metrics["accuracy"], 4),
        "valid_macro_f1": round(metrics["macro_f1"], 4),
        "valid_weighted_f1": round(metrics["weighted_f1"], 4),
        "fit_predict_seconds": round(elapsed, 1),
        "n_valid": metrics["n"],
    }


# --------------------------------------------------------------------------------------
# Sweep
# --------------------------------------------------------------------------------------
def main(quick: bool = False) -> pd.DataFrame:
    REPORTS.mkdir(parents=True, exist_ok=True)
    data = load_split()
    write_manifest(data)

    runs = list(CLASSIC_RUNS)
    if not quick:
        try:
            import sentence_transformers  # noqa: F401
            runs.append(EMBED_RUN)
        except ImportError:
            print("NOTE: sentence-transformers not installed; skipping the embedding run.\n"
                  "      Install with: pip install -r requirements-experiments.txt")

    # Optional MLflow logging.
    mlflow = None
    try:
        import mlflow as _mlflow
        _mlflow.set_tracking_uri(f"sqlite:///{ROOT / 'mlflow.db'}")
        _mlflow.set_experiment("FIN-001")
        mlflow = _mlflow
    except Exception as exc:  # pragma: no cover
        print(f"NOTE: MLflow unavailable ({exc}); writing CSV record only.")

    records = []
    for cfg in runs:
        print(f"→ {cfg['run']} ...", flush=True)
        rec = run_one(cfg, data)
        records.append(rec)
        print(f"  valid macro-F1={rec['valid_macro_f1']}  acc={rec['valid_accuracy']}  "
              f"({rec['fit_predict_seconds']}s)")
        if mlflow is not None:
            with mlflow.start_run(run_name=rec["run"]):
                mlflow.log_param("kind", rec["kind"])
                mlflow.log_param("hypothesis", rec["hypothesis"])
                mlflow.log_metric("valid_macro_f1", rec["valid_macro_f1"])
                mlflow.log_metric("valid_accuracy", rec["valid_accuracy"])
                mlflow.log_metric("valid_weighted_f1", rec["valid_weighted_f1"])

    df = pd.DataFrame(records).sort_values("valid_macro_f1", ascending=False).reset_index(drop=True)
    df.to_csv(RECORD_PATH, index=False)
    winner = df.iloc[0]
    print(f"\nExperiment record -> {RECORD_PATH}")
    print(f"Best on validation: {winner['run']} (macro-F1={winner['valid_macro_f1']})")
    print("Candidate is selected on VALIDATION only. finalize.py scores test once.")
    return df


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--quick", action="store_true", help="classic runs only, skip embeddings")
    args = ap.parse_args()
    main(quick=args.quick)
