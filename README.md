# FIN-001 — Automatic Transaction Categorization

A machine-learning capstone (IT Park / World Bank Module 8, scenario **FIN-01**). It
assigns a bank transaction to one of **17 spending categories** from its raw description
string, and serves the model through a small Streamlit app with a confidence-based
"needs review" fallback for ambiguous or unrecognized transactions.

- **Task:** NLP multi-class text classification.
- **Model:** TF-IDF (word 1–2 grams) + Logistic Regression.
- **Held-out test macro-F1:** **0.9961** (majority-class baseline: 0.009).
- **Honest generalization:** unseen-merchant test slice macro-F1 **0.9784**.

## 3. Problem

A digital-banking app shows users their spending, but raw transaction descriptions are
inconsistent and abbreviated. Manual or rule-based categorization does not scale as new
merchants and formats appear. FIN-01 asks for an ML solution that categorizes a
transaction from its description and handles unseen merchants and low-confidence cases.

## 4. Approach

1. **Data** — public `DoDataThings/us-bank-transaction-categories-v2` (MIT, open). 68,000
   transactions, 17 balanced categories, built from 500+ real merchant names. See
   `data/README.md`.
2. **Preprocess** — a deterministic normalizer strips per-transaction identifiers
   (store numbers, ZIPs, reference IDs) to `<num>`, keeps the debit/credit flag, and
   preserves merchant words. De-duplicate to one row per unique description *before*
   splitting so nothing leaks across the boundary.
3. **Model** — baseline → TF-IDF + linear models → a transformer-embedding comparison
   (which *loses* here — see `reports/model_gate.md` §5). Candidate selected on validation,
   frozen, then scored once on the protected test set.
4. **Serve** — `app.py` loads only the committed artifact and returns a category, a
   confidence, the top-3 alternatives, and a review flag for uncertain inputs.

## Repository map

| Path | What it is |
|---|---|
| `src/features.py` | Text normalization + the feature/merchant contract |
| `src/preprocessing.py` | Load, clean, stratified split, the fit boundary |
| `src/experiments.py` | Model-Gate sweep (baseline → TF-IDF → embeddings), MLflow record |
| `src/evaluate.py` | Metrics, per-class report, unseen-merchant slice |
| `src/finalize.py` | Freeze candidate, score test once, build the bundle |
| `src/inference.py` | Load the bundle and categorize one transaction |
| `app.py` | Streamlit demo (thin UI over `inference.py`) |
| `smoke_test.py` | Fast pre-deploy check |
| `artifacts/` | Committed model bundle + `README.md` + metrics/schema |
| `reports/` | `model_gate.md`, experiment record, error analysis, reload proof |
| `docs/` | Project brief, data audit, reproduction test, responsible-AI |
| `tests/` | Data-gate + inference contract tests |
| `presentation/` | Defense speaker flow, Q&A, deck map, fallback evidence |

## Quickstart

```bash
python3.10 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

python scripts/download_data.py     # fetch the dataset (MIT, open)
python -m src.experiments           # run the sweep -> experiment record + MLflow
python -m src.finalize              # score test once, build the artifact
python smoke_test.py                # expect: SMOKE TEST PASSED
python -m pytest -q                 # contract + data-gate tests
streamlit run app.py                # the demo
```

The committed `artifacts/transaction_categorizer.joblib` means `smoke_test.py`, the tests,
and the app all run **without** re-training or the raw data.

## 15. Responsible use and limitations

The data is synthetic-in-format (real bank data is private), so in-distribution accuracy is
optimistic; the unseen-merchant slice is the honest estimate. No real PII is used. Output is
best-effort and **not financial advice**; low-confidence and unrecognized transactions are
surfaced for human review rather than auto-applied. Full detail:
`docs/RESPONSIBLE_AI_AND_LIMITATIONS.md`.

## 16. Status

See `PROJECT_STATUS.md`. Gates C2–C4 GREEN, C5 verified locally, C6 evidence complete.
GitHub push and public Streamlit deployment are the owner's remaining step.

## Attribution

Dataset: *US Bank Transaction Categories v2*, DoDataThings, Hugging Face, MIT License —
<https://huggingface.co/datasets/DoDataThings/us-bank-transaction-categories-v2>.
