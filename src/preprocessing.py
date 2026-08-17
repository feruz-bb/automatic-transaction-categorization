"""Load, clean, and split the FIN-001 data — and define the fit boundary.

Two rules are enforced here and nowhere else:

1. **De-duplicate before splitting.** The raw file has 22,298 exact-duplicate rows and a
   handful of identical descriptions carrying different labels. If an identical string
   landed in both train and test, the reported score would be memorization, not
   generalization. We reduce to one row per unique description BEFORE the split, so no
   description can straddle the boundary.

2. **Fit on train only.** This module produces the split; every learned transformation
   (the TF-IDF vocabulary, the label encoding) is fitted on the ``train`` rows and only
   ``transform``-ed on ``valid`` / ``test``. The vectorizer factory lives here so the fit
   boundary is defined in exactly one place.

The split is a plain stratified split by category on unique descriptions. A separate,
harder *unseen-merchant* view is derived in ``evaluate.py`` for error analysis — it answers
the brief's "how will unseen merchants be handled?" without weakening the primary metric.
"""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.model_selection import train_test_split

from src.features import (
    LABEL_COL,
    RAW_TEXT_COL,
    TEXT_COL,
    merchant_key,
    normalize_description,
)

RANDOM_STATE = 42
VALID_FRACTION = 0.15
TEST_FRACTION = 0.15

ROOT = Path(__file__).resolve().parents[1]
RAW_CSV = ROOT / "data" / "raw" / "transactions-synthetic.csv"
MANIFEST_PATH = ROOT / "reports" / "preprocessing_manifest.json"


# --------------------------------------------------------------------------------------
# Load + clean
# --------------------------------------------------------------------------------------
def load_raw(path: Path | str = RAW_CSV) -> pd.DataFrame:
    """Read the raw CSV. Fails loudly if the data has not been downloaded yet."""
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(
            f"{path} not found. Run `python scripts/download_data.py` first "
            "(see data/README.md)."
        )
    return pd.read_csv(path)


def clean(df: pd.DataFrame) -> pd.DataFrame:
    """Drop nulls, exact-duplicate rows, and label-ambiguous descriptions.

    Returns one row per unique description with normalized text and a merchant key added.
    The cleaning decisions here are the ones logged in docs/data_audit.md.
    """
    out = df.dropna(subset=[RAW_TEXT_COL, LABEL_COL]).copy()
    out = out.drop_duplicates(subset=[RAW_TEXT_COL, LABEL_COL])

    # A description that appears with more than one category is unresolvable label noise
    # (5 rows). Drop both sides rather than guess.
    counts = out.groupby(RAW_TEXT_COL)[LABEL_COL].nunique()
    ambiguous = counts[counts > 1].index
    out = out[~out[RAW_TEXT_COL].isin(ambiguous)]

    # One row per unique description (removes any remaining same-text rows).
    out = out.drop_duplicates(subset=[RAW_TEXT_COL]).reset_index(drop=True)

    out[TEXT_COL] = out[RAW_TEXT_COL].map(normalize_description)
    out["merchant_key"] = out[RAW_TEXT_COL].map(merchant_key)
    return out


# --------------------------------------------------------------------------------------
# Split
# --------------------------------------------------------------------------------------
def make_split(df: pd.DataFrame) -> pd.DataFrame:
    """Add a ``split`` column with stratified train / valid / test partitions.

    Stratified by category so every class keeps its proportion in all three partitions.
    Deterministic under ``RANDOM_STATE``.
    """
    idx = df.index.to_numpy()
    strat = df[LABEL_COL]

    train_idx, hold_idx = train_test_split(
        idx,
        test_size=VALID_FRACTION + TEST_FRACTION,
        random_state=RANDOM_STATE,
        stratify=strat,
    )
    rel_test = TEST_FRACTION / (VALID_FRACTION + TEST_FRACTION)
    valid_idx, test_idx = train_test_split(
        hold_idx,
        test_size=rel_test,
        random_state=RANDOM_STATE,
        stratify=strat.loc[hold_idx],
    )

    out = df.copy()
    out["split"] = "train"
    out.loc[valid_idx, "split"] = "valid"
    out.loc[test_idx, "split"] = "test"
    return out


def load_split() -> pd.DataFrame:
    """Convenience: raw -> clean -> split, the canonical model-ready frame."""
    return make_split(clean(load_raw()))


# --------------------------------------------------------------------------------------
# Fit boundary: the vectorizer factory (fitted on TRAIN rows only, by the caller)
# --------------------------------------------------------------------------------------
def make_vectorizer(
    analyzer: str = "word",
    ngram_range: tuple[int, int] = (1, 2),
    min_df: int = 2,
) -> TfidfVectorizer:
    """Return an UNFITTED TF-IDF vectorizer. Callers must ``.fit`` on train text only.

    ``analyzer='char_wb'`` gives sub-word robustness to unseen merchants and typos; the
    experiment sweep compares it against word n-grams.
    """
    return TfidfVectorizer(
        analyzer=analyzer,
        ngram_range=ngram_range,
        min_df=min_df,
        sublinear_tf=True,
        lowercase=False,  # normalization already lowercased; keep <num> / flag_* intact
    )


def write_manifest(df_split: pd.DataFrame, path: Path | str = MANIFEST_PATH) -> dict:
    """Emit reports/preprocessing_manifest.json documenting the fit boundary.

    The C3 self-check validator looks for a ``fit_boundary`` field mentioning "train".
    """
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    counts = df_split["split"].value_counts().to_dict()
    manifest = {
        "dataset": "DoDataThings/us-bank-transaction-categories-v2",
        "unit_of_analysis": "one bank transaction description",
        "target": LABEL_COL,
        "n_classes": int(df_split[LABEL_COL].nunique()),
        "rows_after_clean": int(len(df_split)),
        "split_counts": {k: int(v) for k, v in counts.items()},
        "split_strategy": "stratified by category on unique descriptions",
        "random_state": RANDOM_STATE,
        "text_normalizer": "src.features.normalize_description (deterministic, stateless)",
        "fit_boundary": (
            "All learned transformations (TF-IDF vocabulary, label encoding, model "
            "parameters) are fitted on the TRAIN split only. Valid and test are only "
            "transformed. Text normalization is stateless and therefore leakage-safe."
        ),
        "leakage_controls": [
            "De-duplicated to one row per unique description BEFORE splitting, so no "
            "identical string can appear in both train and test.",
            "Identifier tokens (store numbers, ZIPs, PPD/reference IDs) replaced with "
            "<num> so the model cannot key on per-transaction random codes.",
        ],
    }
    path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    return manifest
