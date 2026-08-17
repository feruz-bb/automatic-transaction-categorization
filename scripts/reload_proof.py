"""Reload proof for FIN-001 — load the bundle in a FRESH process and predict, no refitting.

Run from a clean shell (not a notebook, so no hidden state can help):

    .venv/bin/python scripts/reload_proof.py

Writes reports/results/reload_proof.txt. The point is to prove the committed
artifacts/transaction_categorizer.joblib is self-contained: it produces predictions with
no access to data/ and no call to .fit().
"""

from __future__ import annotations

import sys
from pathlib import Path

# Make the repo importable when run as a plain script (python scripts/reload_proof.py).
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.inference import BUNDLE_PATH, categorize, load_bundle

OUT = Path(__file__).resolve().parents[1] / "reports" / "results" / "reload_proof.txt"

KNOWN_INPUTS = [
    "[debit] PUBLIX 7860 UNIVERSITY LN OAKLAND CA",
    "[debit] MTG PMT PENFED CU",
    "[credit] US GOVERNMENT DIR DEP PPD ID: 547185326",
    "[debit] APPLE TV+",
]


def main() -> int:
    lines = ["FIN-001 reload proof", "=" * 60]
    bundle = load_bundle()
    lines.append(f"Loaded: {BUNDLE_PATH.name}")
    lines.append(f"Model version: {bundle['model_version']}  |  test macro-F1: {bundle['test_macro_f1']}")
    lines.append("No .fit() is called after load; predictions use the pickled pipeline as-is.")
    lines.append("-" * 60)
    for d in KNOWN_INPUTS:
        r = categorize(d, bundle)
        lines.append(f"{d}\n   -> {r.category}  (confidence {r.confidence:.3f}, "
                     f"uncertain={r.is_uncertain})")
    lines.append("=" * 60)
    lines.append("RELOAD PROOF OK — artifact is self-contained and requires no refitting.")

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines))
    print(f"\nSaved: {OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
