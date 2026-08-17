"""Contract tests for the deployed inference path — FIN-001.

These run against the committed bundle only (no data/, no training), which is exactly what
the deployment host has. If any of these fail, the app would misbehave in production.
"""

from __future__ import annotations

import pytest

from src.inference import (
    BUNDLE_PATH,
    REQUIRED_KEYS,
    CategoryResult,
    ValidationError,
    categorize,
    load_bundle,
)

pytestmark = pytest.mark.skipif(
    not BUNDLE_PATH.exists(),
    reason="bundle not built yet; run `python -m src.finalize`",
)


@pytest.fixture(scope="module")
def bundle():
    return load_bundle()


def test_bundle_has_required_keys(bundle):
    assert REQUIRED_KEYS <= set(bundle)
    assert len(bundle["classes"]) == 17
    assert hasattr(bundle["pipeline"], "predict_proba")


def test_known_good_predictions(bundle):
    cases = {
        "[debit] PUBLIX 7860 UNIVERSITY LN": "Groceries",
        "[debit] MTG PMT PENFED CU": "Mortgage",
        "[credit] US GOVERNMENT DIR DEP": "Income",
    }
    for desc, expected in cases.items():
        r = categorize(desc, bundle)
        assert isinstance(r, CategoryResult)
        assert r.category == expected, f"{desc}: got {r.category}"
        assert 0.0 <= r.confidence <= 1.0


def test_prediction_is_a_known_class(bundle):
    r = categorize("some arbitrary merchant string 123", bundle)
    assert r.category in bundle["classes"]
    assert len(r.top_k) == 3
    # top_k probabilities are sorted descending
    probs = [p for _, p in r.top_k]
    assert probs == sorted(probs, reverse=True)


def test_low_confidence_fallback_on_spread(bundle):
    """A genuinely ambiguous input the model spreads probability over is flagged."""
    r = categorize("some totally unknown merchant xyz", bundle)
    assert r.is_uncertain is True
    assert r.confidence < bundle["low_confidence_threshold"]


def test_oov_guard_flags_blind_guess(bundle):
    """Gibberish with no recognized merchant terms is uncertain even if the raw
    probability is high (bag-of-words silently ignores unknown words)."""
    r = categorize("zzz qqq unknownmerchant 000", bundle)
    assert r.known_terms == 0
    assert r.is_uncertain is True


def test_empty_input_rejected(bundle):
    with pytest.raises(ValidationError):
        categorize("   ", bundle)


def test_prefix_optional(bundle):
    """A description without a debit/credit prefix still classifies."""
    r = categorize("WAL-MART #0006", bundle)
    assert r.category in bundle["classes"]
