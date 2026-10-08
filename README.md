# Automatic Transaction Categorization (FIN-01)

[![Python 3.10](https://img.shields.io/badge/python-3.10-blue.svg)](https://www.python.org/downloads/release/python-31011/)
[![Status](https://img.shields.io/badge/Status-Complete%20%26%20Verified-brightgreen.svg)](PROJECT_STATUS.md)
[![Macro-F1](https://img.shields.io/badge/Test%20Macro--F1-0.9961-success.svg)](artifacts/metrics.json)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

**Live demo:** [Link](https://automatic-transaction-categorization.streamlit.app)

An end-to-end machine-learning project that sorts raw bank-transaction descriptions into **17 spending categories** and serves the model in a Streamlit web app with a confidence score, top-3 alternatives, and a **"needs review"** flag for ambiguous or unfamiliar merchants.

Built by **Feruzbek Baqoyev** as the capstone project (Module 8, scenario FIN-01) of the **AI & Machine Learning program by IT Park, Digital.uz, IT Academy and the World Bank** (Uzbekistan Digital Inclusion Project), August 2026.

- **Task:** multi-class text classification (17 categories)
- **Model:** TF-IDF (word 1–2-grams) + Logistic Regression, a ~1.2 MB artifact that runs without a GPU
- **Held-out test macro-F1:** **0.9961** overall · **0.9784** on merchants never seen in training (majority-class baseline: 0.0094)
- **Engineering:** leakage-safe preprocessing, a protected test set scored exactly once, 16 automated tests, a smoke test, and a deployable Streamlit app

---

## 1. Problem

Digital banking apps show thousands of raw card and account descriptions every day (e.g. `"[debit] PUBLIX 7860"`, `"[credit] DIRECT DEP PAYROLL"`, `"MTG PMT PENFED CU"`). These strings are noisy, abbreviated and inconsistent. Manual categorization doesn't scale, and hand-written regex rules break as new merchant formats appear.

**Goal:** take a raw transaction string, predict its spending category, return a confidence score and top-3 alternatives, and send low-confidence or unrecognized inputs to human review instead of silently misclassifying them.

---

## 2. Approach

1. **Data:** public dataset [`DoDataThings/us-bank-transaction-categories-v2`](https://huggingface.co/datasets/DoDataThings/us-bank-transaction-categories-v2) (Hugging Face, MIT license): 68,000 transactions, 17 balanced categories, 500+ merchants. See [data/README.md](data/README.md).
2. **Leakage-safe preprocessing:**
   - removed 22,298 exact duplicates *before* splitting (68,000 → 45,692 unique descriptions);
   - normalized store numbers, ZIP codes and payment IDs to `<num>` so the model can't memorize row fingerprints;
   - 70/15/15 stratified split; the TF-IDF vectorizer is fit on the training split only. See [docs/data_audit.md](docs/data_audit.md).
3. **Model selection:** compared a majority-class baseline, three TF-IDF models and sentence-transformer embeddings on the validation split. See [reports/model_gate.md](reports/model_gate.md).
4. **Safeguard:** a prediction is flagged `needs_review` when its top probability is below 0.50 or the input contains no known merchant terms.
5. **Serving:** a Streamlit app ([app.py](app.py)) loads the frozen model bundle directly, with no retraining.

---

## 3. Results

### Validation comparison (n = 6,854)

| Model | Features | Val macro-F1 | Val accuracy | Fit + predict | Notes |
|---|---|:---:|:---:|:---:|---|
| Majority-class baseline | — | 0.0094 | 0.0867 | 0.0 s | Floor to beat |
| TF-IDF + ComplementNB | word 1–2-grams | 0.9915 | 0.9905 | 0.2 s | Fast, slightly lower |
| **TF-IDF + Logistic Regression** | **word 1–2-grams** | **0.9960** | **0.9955** | **1.2 s** | **Selected** |
| TF-IDF + LinearSVC | char 3–5-grams | 0.9971 | 0.9968 | 4.6 s | Best F1, but no probability outputs |
| MiniLM embeddings + LogReg | dense, 384-dim | 0.9468 | 0.9395 | 46.8 s | Worse and ~40× slower: rejected |

**Why not the top scorer?** LinearSVC is 0.0011 higher in macro-F1 but produces no probabilities. The "needs review" safeguard depends on a confidence score, so Logistic Regression was chosen.

### Protected test set (scored once, after the model was frozen)

| Slice | n | Macro-F1 | Accuracy |
|---|:---:|:---:|:---:|
| **Overall** | 6,854 | **0.9961** | 0.9955 |
| Merchants seen in training | 6,138 | 0.9962 | 0.9958 |
| **Merchants never seen in training** | 716 | **0.9784** | 0.9930 |

Overall top-3 accuracy: **0.999**. The unseen-merchant slice is the honest estimate of real-world performance. Most remaining errors are Shopping ↔ Healthcare/Groceries confusions (stores that sell across categories). See [reports/error_analysis/ERROR_ANALYSIS.md](reports/error_analysis/ERROR_ANALYSIS.md) and [reports/results/per_class_test.csv](reports/results/per_class_test.csv).

---

## 4. Quickstart

```bash
git clone https://github.com/feruz-bb/automatic-transaction-categorization.git
cd automatic-transaction-categorization

python3.10 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### Run tests

```bash
pytest -q             # 16 tests; the 6 data-gate tests are skipped until the dataset is downloaded
python smoke_test.py  # pre-deployment sanity check
```

### Launch the web app

```bash
streamlit run app.py
```

The trained model bundle (`artifacts/transaction_categorizer.joblib`) is committed, so the tests, smoke test and app run immediately without downloading data or retraining.

### Full retraining (optional)

```bash
python scripts/download_data.py   # download the 68k-row dataset
python -m src.experiments         # run the experiment sweep (logged to MLflow)
python -m src.finalize            # freeze the selected model and export the bundle
```

---

## 5. Responsible AI & limitations

- **Advisory only:** predictions help categorize spending; they are not financial or legal advice.
- **Human-in-the-loop:** low-confidence (< 0.50) or unrecognized inputs are flagged `needs_review` instead of being auto-applied.
- **Privacy:** the dataset contains no real customer names or account numbers; numeric identifiers are replaced with `<num>`.
- **Generalization:** the dataset is synthetic in format, so in-distribution scores are optimistic. Performance on unseen merchants (0.9784) is the more realistic figure, and genuinely new merchant formats will be harder still.
- Details: [docs/RESPONSIBLE_AI_AND_LIMITATIONS.md](docs/RESPONSIBLE_AI_AND_LIMITATIONS.md).

---

## 6. Repository structure

```
├── app.py                          # Streamlit web app
├── smoke_test.py                   # pre-deployment smoke test
├── requirements.txt                # app dependencies
├── requirements-experiments.txt    # extra dependencies for the experiment sweep
├── PROJECT_STATUS.md               # project status by stage
├── RUBRIC_EVIDENCE_MATRIX.md       # capstone criteria → evidence
├── .devcontainer/                  # dev container config
├── .streamlit/config.toml          # Streamlit UI settings
├── artifacts/                      # frozen model bundle, schema, metrics
├── data/README.md                  # dataset provenance and download steps
├── docs/
│   ├── PROJECT_BRIEF.md            # problem framing and technical proposal
│   ├── data_audit.md               # data quality and leakage controls
│   ├── AI_DEBUG_REPORT.md          # debugging case study
│   ├── REPRODUCTION_TEST.md        # clean-environment reproduction steps
│   ├── RESPONSIBLE_AI_AND_LIMITATIONS.md
│   └── submission/                 # capstone brief and submission form
├── notebooks/
│   ├── 01_data_audit.ipynb
│   └── 02_experiments.ipynb
├── presentation/                   # slide deck (PPTX + HTML), speaker flow, Q&A
├── reports/
│   ├── model_gate.md               # model selection report
│   ├── experiment_record.csv       # all experiment runs
│   ├── error_analysis/             # weakest classes and confusions
│   └── results/                    # test metrics, per-class scores, reload proof
├── scripts/                        # data download, reload proof, deck generator
├── src/
│   ├── preprocessing.py            # cleaning, de-duplication, splitting
│   ├── features.py                 # text normalization and TF-IDF features
│   ├── experiments.py              # experiment sweep (MLflow)
│   ├── evaluate.py                 # metrics and slices
│   ├── finalize.py                 # model freezing and export
│   └── inference.py                # prediction with confidence safeguards
└── tests/                          # 16 pytest tests
```

All capstone criteria (1–8) are mapped to evidence in [RUBRIC_EVIDENCE_MATRIX.md](RUBRIC_EVIDENCE_MATRIX.md).

---

## 7. Attribution & license

- **Dataset:** *US Bank Transaction Categories v2* by DoDataThings ([Hugging Face](https://huggingface.co/datasets/DoDataThings/us-bank-transaction-categories-v2)), MIT license.
- **Code:** MIT license (see [LICENSE](LICENSE)).
- **Author:** Feruzbek Baqoyev
