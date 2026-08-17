"""Data-Gate invariants — FIN-001.

These assert the leakage controls that docs/data_audit.md claims, so the claims cannot
silently rot. They need the raw data present (skipped otherwise).
"""

from __future__ import annotations

import pytest

from src.features import merchant_key, normalize_description
from src.preprocessing import RAW_CSV, clean, load_raw, make_split

pytestmark = pytest.mark.skipif(
    not RAW_CSV.exists(),
    reason="raw data not downloaded; run `python scripts/download_data.py`",
)


@pytest.fixture(scope="module")
def split():
    return make_split(clean(load_raw()))


def test_clean_yields_unique_descriptions(split):
    assert split["description"].is_unique, "duplicate descriptions survived cleaning"


def test_no_description_crosses_split_boundary(split):
    """The core leakage guard: no identical string in two splits."""
    per_desc_splits = split.groupby("description")["split"].nunique()
    assert (per_desc_splits == 1).all()


def test_all_rows_assigned_a_split(split):
    assert set(split["split"].unique()) == {"train", "valid", "test"}
    assert split["split"].isna().sum() == 0


def test_stratification_preserves_class_share(split):
    """Each class keeps roughly its overall proportion in train and test."""
    overall = split["category"].value_counts(normalize=True)
    for part in ("train", "test"):
        share = split.loc[split["split"] == part, "category"].value_counts(normalize=True)
        for cat, p in overall.items():
            assert abs(share.get(cat, 0) - p) < 0.02, f"{cat} drifted in {part}"


def test_normalizer_is_deterministic_and_strips_ids():
    raw = "[debit] PUBLIX 7860 UNIVERSITY LN OAKLAND 94601-4574 CA USA"
    a = normalize_description(raw)
    b = normalize_description(raw)
    assert a == b
    assert "flag_debit" in a
    assert "publix" in a
    assert "<num>" in a            # store number / zip replaced
    assert "7860" not in a         # raw id token gone


def test_merchant_key_ignores_ids():
    # Same merchant + same following words but different store numbers -> same key.
    k1 = merchant_key("[debit] PUBLIX 7860 UNIVERSITY LN")
    k2 = merchant_key("[debit] PUBLIX 9999 UNIVERSITY LN")
    assert k1 == k2 == "publix university"
