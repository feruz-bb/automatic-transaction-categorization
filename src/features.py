"""Text normalization and the feature contract for FIN-001.

Two things live here and nowhere else:

1. ``normalize_description`` — the single, deterministic cleaning function applied to EVERY
   transaction string, at training time and at inference time. If training and serving
   normalized text differently the model would silently degrade in production, so both
   paths import THIS function.

2. ``merchant_key`` — the coarse merchant identity used to measure generalization to
   unseen merchants (see the split and the error analysis). It is an evaluation tool, not
   a model input.

Design note (answers the brief's "normalize noisy descriptions without losing signal"):
raw strings carry store numbers, ZIP codes, reference/PPD IDs and phone numbers that are
essentially random per transaction. Left in, they bloat the vocabulary and let the model
memorize noise instead of learning the merchant. We replace pure-digit and long
alphanumeric ID tokens with a single ``<num>`` placeholder, keep the debit/credit flag as
an explicit token, and preserve the merchant words that actually carry the category.
"""

from __future__ import annotations

import re

#: Raw columns as they arrive in data/raw/transactions-synthetic.csv.
RAW_TEXT_COL = "description"
LABEL_COL = "category"

#: The normalized text column produced by this module and consumed by the vectorizer.
TEXT_COL = "text_norm"

# --------------------------------------------------------------------------------------
# Normalization
# --------------------------------------------------------------------------------------

_PREFIX_RE = re.compile(r"^\s*\[(debit|credit)\]\s*", re.IGNORECASE)
# A token that is "an identifier": all digits, or a long alnum run mixing digits, or a
# digit-bearing code like 94587-4574. These vary per transaction and carry no category.
_ID_TOKEN_RE = re.compile(r"^(?=\S*\d)[\w\-\*\.#/]{2,}$")
_MULTISPACE_RE = re.compile(r"\s+")
_PUNCT_RE = re.compile(r"[^\w\s<>]")


def split_prefix(raw: str) -> tuple[str, str]:
    """Return ``(flag, body)`` where flag is 'credit', 'debit' or '' and body is the rest."""
    m = _PREFIX_RE.match(raw or "")
    if not m:
        return "", (raw or "").strip()
    return m.group(1).lower(), raw[m.end():].strip()


def normalize_description(raw: str) -> str:
    """Deterministic cleaning applied identically at train and inference time.

    Steps: extract the debit/credit flag as an explicit ``flag_*`` token, lowercase the
    body, drop punctuation (keeping the ``<num>`` placeholder marker), replace any
    identifier-like token (store numbers, ZIPs, PPD/reference codes) with ``<num>``, and
    collapse whitespace. Deterministic and stateless — no fitting, so it is leakage-safe
    by construction.
    """
    flag, body = split_prefix(str(raw))
    body = body.lower()
    body = _PUNCT_RE.sub(" ", body)
    tokens = []
    for tok in body.split():
        if _ID_TOKEN_RE.match(tok):
            tokens.append("<num>")
        else:
            tokens.append(tok)
    text = " ".join(tokens)
    text = _MULTISPACE_RE.sub(" ", text).strip()
    flag_token = f"flag_{flag}" if flag else "flag_none"
    return f"{flag_token} {text}".strip()


def merchant_key(raw: str) -> str:
    """Coarse merchant identity for the unseen-merchant evaluation slice.

    The first 1-2 meaningful (non-id, non-flag) tokens of the normalized body. Used ONLY
    to decide which merchants are held out of training for the generalization test; never
    fed to the model.
    """
    _, body = split_prefix(str(raw))
    body = _PUNCT_RE.sub(" ", body.lower())
    words = [t for t in body.split() if not _ID_TOKEN_RE.match(t)]
    if not words:
        return "<none>"
    return " ".join(words[:2])
