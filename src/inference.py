"""Categorize a single transaction from the saved bundle — FIN-001.

Depends on ``artifacts/`` ONLY. The raw dataset is not needed to run this, so the module
loads and predicts on a deployment host that has never seen ``data/``.

    from src.inference import load_bundle, categorize
    bundle = load_bundle()
    result = categorize("[debit] PUBLIX 7860 UNIVERSITY LN", bundle)
    print(result.category, result.confidence, result.is_uncertain)

No Streamlit import here and no refitting: the app is a thin UI over this module, and the
sklearn pipeline inside the bundle is used exactly as it was pickled.
"""

from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

import joblib

from src.features import normalize_description

ARTIFACTS = Path(__file__).resolve().parents[1] / "artifacts"
BUNDLE_PATH = ARTIFACTS / "transaction_categorizer.joblib"

#: Keys every valid bundle must carry. Guarded so a truncated/rebuilt artifact fails at
#: load time with a clear message instead of deep inside a prediction.
REQUIRED_KEYS = {
    "pipeline",
    "classes",
    "target",
    "model_version",
    "low_confidence_threshold",
}


class ValidationError(ValueError):
    """Raised for empty input or a structurally invalid bundle."""


@dataclass
class CategoryResult:
    category: str
    confidence: float
    is_uncertain: bool
    top_k: list[tuple[str, float]]
    normalized_text: str
    model_version: str
    known_terms: int  # recognized merchant terms; 0 means the model is guessing blind


@lru_cache(maxsize=1)
def load_bundle(path: str | Path = BUNDLE_PATH) -> dict:
    """Load and validate the model bundle. Cached so the app loads it once."""
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(
            f"{path} not found. Build it with `python -m src.finalize` "
            "(needs the data — see data/README.md)."
        )
    bundle = joblib.load(path)
    missing = REQUIRED_KEYS - set(bundle)
    if missing:
        raise ValidationError(f"Bundle is missing required keys: {sorted(missing)}")
    if not hasattr(bundle["pipeline"], "predict_proba"):
        raise ValidationError("Bundled pipeline cannot produce probabilities.")
    return bundle


def categorize(description: str, bundle: dict | None = None, k: int = 3) -> CategoryResult:
    """Categorize one transaction description.

    Returns the predicted category, its probability (confidence), the top-k alternatives,
    and an ``is_uncertain`` flag set when the top probability falls below the bundle's
    ``low_confidence_threshold`` — the confidence-based fallback the brief asks for.
    """
    if description is None or not str(description).strip():
        raise ValidationError("Empty transaction description.")
    if bundle is None:
        bundle = load_bundle()

    text = normalize_description(str(description))
    pipe = bundle["pipeline"]
    proba = pipe.predict_proba([text])[0]
    classes = pipe.classes_

    order = proba.argsort()[::-1]
    top_k = [(str(classes[i]), float(proba[i])) for i in order[:k]]
    best_label, best_p = top_k[0]
    threshold = float(bundle["low_confidence_threshold"])

    # OOV-coverage guard. A bag-of-words model silently ignores unknown words, so a string
    # of merchants it has never seen can still yield a high probability for a default
    # class. Count how many recognized MERCHANT terms (excluding the flag_* / <num>
    # structural tokens) the input actually hit; zero means the model is guessing blind and
    # the result must be treated as uncertain regardless of the probability.
    known_terms = _content_coverage(pipe, text)
    is_uncertain = bool(best_p < threshold or known_terms == 0)

    return CategoryResult(
        category=best_label,
        confidence=round(best_p, 4),
        is_uncertain=is_uncertain,
        top_k=[(lbl, round(p, 4)) for lbl, p in top_k],
        normalized_text=text,
        model_version=str(bundle["model_version"]),
        known_terms=known_terms,
    )


#: Structural tokens that carry no merchant identity. ``<num>`` is rendered as the token
#: ``num`` by the vectorizer (it strips the angle brackets), so both spellings are listed.
_STRUCTURAL_TOKENS = {"num", "<num>"}


def _is_content_feature(feature_name: str) -> bool:
    """True if a vectorizer feature contains at least one real merchant token.

    A feature is purely structural only if every one of its tokens is the ``num``
    placeholder or a ``flag_*`` marker. Unigram ``num`` -> structural; bigram
    ``num university`` -> content (it carries "university").
    """
    tokens = feature_name.split()
    return any(t not in _STRUCTURAL_TOKENS and not t.startswith("flag_") for t in tokens)


def _content_coverage(pipe, text: str) -> int:
    """Number of recognized MERCHANT-bearing vocabulary features the text activates.

    Works for the deployed TF-IDF pipeline; returns -1 (unknown) for any pipeline without
    a recognizable vectorizer step, so the caller falls back to the probability threshold.
    """
    vec = getattr(pipe, "named_steps", {}).get("tfidf")
    if vec is None or not hasattr(vec, "transform"):
        return -1
    row = vec.transform([text])
    names = vec.get_feature_names_out()
    return sum(1 for i in row.indices if _is_content_feature(names[i]))
