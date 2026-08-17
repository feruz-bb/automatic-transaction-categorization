"""FIN-001 — Automatic Transaction Categorization demo.
?ЭЁ
Жз-=хзъхжэЮджбб?

Paste a bank transaction description and get its spending category, the model's confidence,
and the runner-up categories. Low-confidence or unrecognized inputs are flagged for review
instead of being auto-applied.

    streamlit run app.py

Loads from artifacts/ only — no dataset and no training happen here.
"""

from __future__ import annotations

import streamlit as st

from src.inference import ValidationError, categorize, load_bundle

st.set_page_config(page_title="FIN-001 Transaction Categorizer", page_icon="🏦", layout="centered")

EXAMPLES = {
    "Grocery store": "[debit] PUBLIX 7860 UNIVERSITY LN OAKLAND CA",
    "Mortgage payment": "[debit] MTG PMT PENFED CU",
    "Government deposit (income)": "[credit] US GOVERNMENT DIR DEP PPD ID: 547185326",
    "Streaming subscription": "[debit] APPLE TV+",
    "Unknown merchant": "SOME UNFAMILIAR MERCHANT LLC",
}


@st.cache_resource
def _bundle() -> dict:
    return load_bundle()


st.title("🏦 Transaction Categorizer")
st.caption(
    "FIN-001 capstone — assigns a bank transaction to one of 17 spending categories from "
    "its description. Model: TF-IDF + Logistic Regression."
)

try:
    bundle = _bundle()
except Exception as exc:  # bundle missing / corrupt
    st.error(
        f"Model bundle could not be loaded: {exc}\n\n"
        "Build it with `python -m src.finalize` (see README)."
    )
    st.stop()

st.write(
    f"**Model version:** {bundle['model_version']} · "
    f"**held-out test macro-F1:** {bundle.get('test_macro_f1', '—')} · "
    f"**categories:** {len(bundle['classes'])}"
)

with st.form("categorize"):
    preset = st.selectbox("Try an example (optional)", ["—"] + list(EXAMPLES))
    default = EXAMPLES.get(preset, "")
    description = st.text_input(
        "Transaction description",
        value=default,
        placeholder="e.g. [debit] STARBUCKS STORE 4471 SEATTLE WA",
    )
    submitted = st.form_submit_button("Categorize", type="primary")

if submitted:
    try:
        result = categorize(description, bundle)
    except ValidationError as exc:
        st.warning(str(exc))
        st.stop()

    if result.is_uncertain:
        st.warning(
            f"**Needs review — low confidence.** Best guess: **{result.category}** "
            f"({result.confidence:.0%}). "
            + ("No familiar merchant terms were recognized in this description."
               if result.known_terms == 0
               else "The model is not confident enough to auto-apply this category.")
        )
    else:
        st.success(f"**{result.category}**  ·  confidence {result.confidence:.0%}")

    st.subheader("Top 3 categories")
    for label, prob in result.top_k:
        st.write(f"{label}")
        st.progress(min(max(prob, 0.0), 1.0))

    with st.expander("How the model saw this input"):
        st.code(result.normalized_text, language="text")
        st.caption(
            "Store numbers, ZIP codes and reference IDs are replaced with `<num>`; the "
            "debit/credit flag is kept as `flag_*`. "
            f"Recognized merchant terms: {result.known_terms}."
        )

st.divider()
st.caption(
    "Trained on the public DoDataThings/us-bank-transaction-categories-v2 dataset (MIT, "
    "synthetic-format). Not financial advice; categories are best-effort and low-confidence "
    "cases are surfaced for human review."
)
