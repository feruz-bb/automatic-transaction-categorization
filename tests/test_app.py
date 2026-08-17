"""End-to-end verification for the Streamlit demo — FIN-001.

The unit tests in `test_inference.py` cover the `src.inference` library, but nothing
exercises `app.py` — the documented main entry point (`streamlit run app.py`, rubric
criterion 5). These tests close that gap using Streamlit's built-in `AppTest` harness
(no server, no network, uses the committed artifact only).

Coverage:
  * normal case      — a known-good transaction renders its category (must keep working);
  * edge case        — empty input is handled without crashing the app;
  * the CONFIRMED gap — a bundle that `load_bundle` accepts as valid but lacks
                        `test_macro_f1` (a key app.py reads) must not crash the app.
                        This currently fails: `test_macro_f1` is outside the validated
                        contract, so the app raises KeyError on a "valid" bundle.
"""

from __future__ import annotations

import joblib
import pytest

from src.inference import BUNDLE_PATH, load_bundle

pytestmark = pytest.mark.skipif(
    not BUNDLE_PATH.exists(),
    reason="bundle not built yet; run `python -m src.finalize`",
)

# streamlit.testing is part of streamlit>=1.28; the project pins 1.61.1.
AppTest = pytest.importorskip("streamlit.testing.v1").AppTest

APP = str(BUNDLE_PATH.resolve().parents[1] / "app.py")


def _fresh_app():
    """A fresh AppTest with Streamlit's resource cache cleared between runs."""
    import streamlit as st

    st.cache_resource.clear()
    return AppTest.from_file(APP, default_timeout=30)


# --- normal case: the main user flow must render a prediction ------------------------
def test_app_renders_known_good_prediction():
    at = _fresh_app().run()
    assert not at.exception, f"app raised on load: {at.exception}"
    at.text_input[0].set_value("[debit] MTG PMT PENFED CU").run()
    at.button[0].click().run()
    assert not at.exception
    rendered = " | ".join(m.value for m in at.markdown)
    assert "Mortgage" in rendered, f"expected Mortgage in output, got: {rendered}"


# --- edge case: empty input is rejected gracefully, not with a crash -----------------
def test_app_handles_empty_input_without_crashing():
    at = _fresh_app().run()
    at.text_input[0].set_value("   ").run()
    at.button[0].click().run()
    assert not at.exception, f"empty input crashed the app: {at.exception}"
    assert len(at.warning) >= 1, "empty input should surface a warning, not a silent pass"


# --- the confirmed gap: a contract-valid bundle missing test_macro_f1 ----------------
def test_app_survives_contract_valid_bundle_missing_metric(tmp_path, monkeypatch):
    """`load_bundle` validates only REQUIRED_KEYS; `test_macro_f1` is not one of them.
    So a bundle missing that key is 'valid' yet the app reads it at module load.
    The app must not crash on any bundle load_bundle accepts."""
    good = load_bundle()
    trimmed = {k: v for k, v in good.items() if k != "test_macro_f1"}
    p = tmp_path / "trimmed.joblib"
    joblib.dump(trimmed, p)

    # Sanity: the trimmed bundle really is accepted by the validated contract.
    load_bundle.cache_clear()
    reloaded = load_bundle(p)
    assert "test_macro_f1" not in reloaded, "precondition: key is absent"

    # Point the app at this contract-valid-but-trimmed bundle.
    monkeypatch.setattr("src.inference.load_bundle", lambda *a, **k: trimmed)
    at = _fresh_app().run()
    assert not at.exception, (
        "app crashed on a bundle that load_bundle accepts as valid: "
        f"{at.exception}. app.py reads a bundle key outside the validated contract."
    )
