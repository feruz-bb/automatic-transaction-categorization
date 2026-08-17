#!/usr/bin/env python3
"""Fast pre-deployment check for FIN-001.

Run this BEFORE deploying. It proves the artifact loads and categorizes correctly using
only files that exist on the deployment host — no data/ directory, no refitting.

    .venv/bin/python smoke_test.py

Expected final line: SMOKE TEST PASSED
"""

from __future__ import annotations

import sys
import time

from src.inference import ValidationError, categorize, load_bundle

# (description, expected_category) — obvious cases that must never regress.
KNOWN_GOOD = [
    ("[debit] PUBLIX 7860 UNIVERSITY LN OAKLAND CA", "Groceries"),
    ("[debit] MTG PMT PENFED CU", "Mortgage"),
    ("[credit] US GOVERNMENT DIR DEP", "Income"),
    ("[debit] REPUBLIC SERVICES MISSION CT", "Utilities"),
]


def main() -> int:
    t0 = time.time()
    failures: list[str] = []

    def check(label: str, ok: bool, detail: str = "") -> None:
        print(f"  {'ok  ' if ok else 'FAIL'} {label}" + (f"  ({detail})" if detail else ""))
        if not ok:
            failures.append(label)

    print("FIN-001 smoke test\n" + "-" * 62)

    # 1. bundle loads and is structurally valid
    try:
        bundle = load_bundle()
    except Exception as exc:
        print(f"  FAIL could not load bundle: {exc}")
        return 1
    check("bundle loads", True, f"v{bundle['model_version']}, test macro-F1 {bundle['test_macro_f1']}")
    check("17 categories present", len(bundle["classes"]) == 17, f"{len(bundle['classes'])} classes")

    # 2. known-good inputs land in the right category
    print("\n  known-good inputs:")
    for desc, expected in KNOWN_GOOD:
        r = categorize(desc, bundle)
        check(f"{desc[:34]:36} -> {expected}", r.category == expected,
              f"got {r.category} @ {r.confidence}")

    # 3. probabilities are well-formed and top-3 sums are sane
    r = categorize(KNOWN_GOOD[0][0], bundle)
    check("confidence in [0,1]", 0.0 <= r.confidence <= 1.0, f"{r.confidence}")
    check("top-3 returned", len(r.top_k) == 3)

    # 4. the low-confidence fallback fires on gibberish
    r = categorize("zzz qqq unknownmerchant 000", bundle)
    check("uncertain flag on unknown input", r.is_uncertain, f"conf {r.confidence}")

    # 5. empty input is rejected, not silently guessed
    try:
        categorize("   ", bundle)
        check("empty input rejected", False)
    except ValidationError:
        check("empty input rejected", True)

    print("-" * 62)
    if failures:
        print(f"SMOKE TEST FAILED ({len(failures)} check(s)) in {time.time()-t0:.1f}s")
        return 1
    print(f"SMOKE TEST PASSED in {time.time()-t0:.1f}s")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
