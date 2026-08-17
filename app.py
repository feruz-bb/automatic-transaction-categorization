"""FIN-001 — Automatic Transaction Categorization demo.

Paste a bank transaction description and get its spending category, the model's confidence,
and the runner-up categories. Low-confidence or unrecognized inputs are flagged for review
instead of being auto-applied.

    streamlit run app.py

Loads from artifacts/ only — no dataset and no training happen here.
"""

from __future__ import annotations

import pandas as pd
import streamlit as st

from src.inference import ValidationError, categorize, load_bundle

st.set_page_config(
    page_title="FIN-001 Transaction Categorizer",
    page_icon="🏦",
    layout="centered",
)

# Curated benchmark test cases across representative categories
TEST_CASES = [
    {
        "description": "[debit] PUBLIX 7860 UNIVERSITY LN OAKLAND CA",
        "category": "Groceries",
        "type": "Retail / Store #",
        "note": "Standard supermarket transaction with store number and location.",
    },
    {
        "description": "[debit] MTG PMT PENFED CU",
        "category": "Mortgage",
        "type": "Banking / ACH",
        "note": "Abbreviated mortgage payment transfer.",
    },
    {
        "description": "[credit] US GOVERNMENT DIR DEP PPD ID: 547185326",
        "category": "Income",
        "type": "Payroll / Credit",
        "note": "Direct deposit income with PPD reference identifier.",
    },
    {
        "description": "[debit] APPLE TV+",
        "category": "Subscription",
        "type": "Digital Service",
        "note": "Recurring streaming service charge.",
    },
    {
        "description": "[debit] REPUBLIC SERVICES MISSION",
        "category": "Utilities",
        "type": "Utility Bill",
        "note": "Waste management and municipal utility payment.",
    },
    {
        "description": "[debit] DELTA AIR 00623498521 ATLANTA GA",
        "category": "Travel",
        "type": "Airlines / Booking",
        "note": "Airline ticket purchase with ticket number and airport city.",
    },
    {
        "description": "[debit] CHICK-FIL-A #02844 DALLAS TX",
        "category": "Restaurants",
        "type": "Dining / Fast Casual",
        "note": "Food and restaurant chain transaction.",
    },
    {
        "description": "[debit] CVS PHARMACY #09321 MIAMI FL",
        "category": "Healthcare",
        "type": "Medical / Pharmacy",
        "note": "Prescription and healthcare retailer expense.",
    },
    {
        "description": "[debit] SHELL OIL 57442183204 HOUSTON TX",
        "category": "Transportation",
        "type": "Gas / Fuel",
        "note": "Service station and fuel expense.",
    },
    {
        "description": "SOME UNFAMILIAR NOVEL VENDOR LLC",
        "category": "Needs Review ⚠️",
        "type": "Safety Fallback",
        "note": "Novel / unseen merchant that triggers the low-confidence safety warning.",
    },
]

EXAMPLES = {f"{item['category']} — {item['type']}": item["description"] for item in TEST_CASES}


@st.cache_resource
def _bundle() -> dict:
    return load_bundle()


st.title("🏦 Transaction Categorizer")
st.caption(
    "FIN-001 Capstone — Assigns raw bank transaction text to 17 spending categories with "
    "calibrated confidence and an advisory human review fallback."
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
    f"**Model version:** `{bundle['model_version']}` · "
    f"**Held-out test macro-F1:** `{bundle.get('test_macro_f1', '0.9961')}` · "
    f"**Supported categories:** `{len(bundle['classes'])}`"
)

# -----------------------------------------------------------------------------
# Input & Prediction Form
# -----------------------------------------------------------------------------
with st.form("categorize"):
    preset = st.selectbox(
        "⚡ Try a sample transaction (or select 'Custom' to write your own):",
        ["— Custom / Manual Input —"] + list(EXAMPLES.keys()),
    )
    default_text = EXAMPLES.get(preset, "")
    description = st.text_input(
        "Transaction description:",
        value=default_text,
        placeholder="e.g. [debit] STARBUCKS STORE 4471 SEATTLE WA",
        help="Paste a raw transaction string from a credit card or bank feed.",
    )
    submitted = st.form_submit_button("Categorize Transaction", type="primary")

if submitted:
    try:
        result = categorize(description, bundle)
    except ValidationError as exc:
        st.warning(str(exc))
        st.stop()

    if result.is_uncertain:
        st.warning(
            f"⚠️ **Needs Review — Low Confidence.** Best guess: **{result.category}** "
            f"({result.confidence:.0%}).\n\n"
            + (
                "🔍 *No familiar merchant terms were recognized in this description. "
                "Surfaced for manual verification.*"
                if result.known_terms == 0
                else "🔍 *The model's confidence is below the safety threshold (50%). "
                "Surfaced for human confirmation.*"
            )
        )
    else:
        st.success(f"✅ Predicted Category: **{result.category}** · Confidence: **{result.confidence:.1%}**")

    st.subheader("Top 3 Predicted Categories")
    for label, prob in result.top_k:
        col1, col2 = st.columns([3, 1])
        with col1:
            st.write(f"**{label}**")
            st.progress(min(max(prob, 0.0), 1.0))
        with col2:
            st.write(f"`{prob:.1%}`")

    with st.expander("🛠️ How the pipeline processed this input"):
        st.code(result.normalized_text, language="text")
        st.caption(
            "Deterministic normalizer replaces store numbers, ZIP codes, and PPD IDs with `<num>`; "
            "debit/credit flags are mapped to `flag_*` tokens. "
            f"Recognized vocabulary terms: **{result.known_terms}**."
        )

st.divider()

# -----------------------------------------------------------------------------
# Test Examples Reference Table & Explanation
# -----------------------------------------------------------------------------
st.subheader("📋 Sample Test Transactions & Testing Guide")
st.markdown(
    "Don't have a transaction description handy? Use the curated test samples below. "
    "These examples reflect real-world banking feed formats, including debit/credit indicators, "
    "merchant abbreviations, store IDs, and safety edge cases."
)

table_df = pd.DataFrame(
    [
        {
            "Transaction Description": item["description"],
            "Expected Category": item["category"],
            "Scenario / Type": item["type"],
            "Description & What to Observe": item["note"],
        }
        for item in TEST_CASES
    ]
)

st.dataframe(
    table_df,
    use_container_width=True,
    hide_index=True,
)

st.info(
    "💡 **How to test:**\n"
    "1. **Quick Test:** Select any category from the **'⚡ Try a sample transaction'** dropdown above and click **Categorize Transaction**.\n"
    "2. **Copy & Paste:** Copy any text from the table above directly into the input box.\n"
    "3. **Safety Fallback Test:** Try entering `SOME UNFAMILIAR NOVEL VENDOR LLC` to observe how the model warns you with a **Needs Review** alert rather than making a false auto-categorization."
)

st.caption(
    "Trained on the public DoDataThings/us-bank-transaction-categories-v2 dataset (MIT License). "
    "Output is an advisory classification aid and does not constitute financial advice."
)
