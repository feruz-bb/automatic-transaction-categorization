# FIN-001 — Automatic Transaction Categorization

[![Python 3.10](https://img.shields.io/badge/python-3.10-blue.svg)](https://www.python.org/downloads/release/python-31011/)
[![Status](https://img.shields.io/badge/Status-Complete%20%26%20Verified-brightgreen.svg)](PROJECT_STATUS.md)
[![Macro-F1](https://img.shields.io/badge/Test%20Macro--F1-0.9961-success.svg)](artifacts/metrics.json)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

A production-grade machine-learning capstone project (IT Park / World Bank AI/ML Course Module 8, Scenario **FIN-01**). It classifies raw bank transaction descriptions into **17 spending categories** and provides a real-time Streamlit web application with calibrated confidence scores and an advisory "needs review" fallback for ambiguous or novel merchants.

- **ML Task:** Multi-class NLP text classification (17 categories).
- **Candidate Model:** TF-IDF (word 1–2 n-grams) + Logistic Regression (calibrated probabilities).
- **Held-out Test Macro-F1:** **0.9961** (Naive baseline: **0.0094**).
- **Honest Generalization (Unseen Merchants):** **0.9784** Macro-F1 (evaluated on 716 test transactions from merchants never seen in training).
- **GitHub Repository:** [https://github.com/feruz-bb/automatic-transaction-categorization](https://github.com/feruz-bb/automatic-transaction-categorization)

---

## 1. Problem Statement

Digital banking applications display thousands of raw card and account transaction descriptions daily (e.g., `"[debit] PUBLIX 7860"`, `"[credit] DIRECT DEP PAYROLL"`, `"MTG PMT PENFED CU"`). These strings are noisy, abbreviated, and inconsistent across banking rails. Manual categorization is expensive and unscalable, while rigid rule-based regex patterns break as thousands of new merchant formats appear.

**Objective:** Build an automated ML classification pipeline that accepts raw transaction strings, accurately predicts the spending category, provides calibrated confidence rankings (Top-3), and surfaces low-confidence or unrecognized inputs for human review rather than making silent misclassifications.

---

## 2. Approach & Architecture

1. **Dataset & Provenance:** Public dataset `DoDataThings/us-bank-transaction-categories-v2` (Hugging Face, MIT License, 68,000 transactions across 17 balanced categories from 500+ merchants). See [data/README.md](data/README.md).
2. **Leakage-Safe Preprocessing:**
   - **De-duplication:** 22,298 exact duplicate rows removed *before* splitting (68,000 → 45,692 unique descriptions).
   - **Entity Normalization:** Deterministic regex normalizes store numbers, ZIP codes, and PPD IDs to `<num>` to prevent model fingerprinting.
   - **Fit Boundary:** Feature extractors (TF-IDF vectorizer) are fit strictly on the Train partition (70/15/15 stratified split). Zero leakage across split boundaries. See [docs/data_audit.md](docs/data_audit.md).
3. **Model Selection:** Evaluated naive baseline, TF-IDF linear classifiers, and dense Sentence-Transformer embeddings. TF-IDF + Logistic Regression was chosen for superior performance, probability calibration, and ultra-lightweight deployment footprint (~1.2 MB). See [reports/model_gate.md](reports/model_gate.md).
4. **Advisory Safeguards:** Integrated a fallback mechanism that flags transactions with confidence $< 0.50$ or zero recognized in-vocabulary terms as `needs_review = True`.
5. **Serving:** An interactive Streamlit app ([app.py](app.py)) that loads the frozen artifact directly without re-training.

---

## 3. Evaluation & Key Results

### Validation Sweep Comparison

| Model | Featurizer | Val Macro-F1 | Val Accuracy | Notes |
|---|---|:---:|:---:|---|
| **Dummy Baseline** | Majority Class | 0.0094 | 0.0588 | Naive baseline |
| **TF-IDF + LinearSVC** | Word 1–2 n-grams | 0.9971 | 0.9971 | High F1, but uncalibrated probabilities |
| **TF-IDF + Logistic Regression** | **Word 1–2 n-grams** | **0.9960** | **0.9960** | **Selected candidate (calibrated probabilities)** |
| **MiniLM Embeddings + LogReg** | Dense (384-dim) | 0.9468 | 0.9468 | Slower inference (~40x), heavier deps |

### Protected Final Test Evaluation

The selected candidate was frozen and scored **exactly once** on the held-out test split:

| Test Slice | Samples ($n$) | Macro-F1 | Accuracy | Top-3 Accuracy |
|---|:---:|:---:|:---:|:---:|
| **Overall Held-out Test** | 6,854 | **0.9961** | 0.9955 | **0.9990** |
| **Seen Merchants Slice** | 6,138 | 0.9962 | 0.9958 | 0.9992 |
| **Unseen Merchants Slice (Honest)** | 716 | **0.9784** | 0.9930 | 0.9972 |

Detailed per-class metrics and confusion analysis are available in [reports/results/per_class_test.csv](reports/results/per_class_test.csv) and [reports/error_analysis/ERROR_ANALYSIS.md](reports/error_analysis/ERROR_ANALYSIS.md).

---

## 4. Repository Structure

```
├── .streamlit/config.toml          # Streamlit UI configuration
├── app.py                          # Streamlit interactive web demo
├── artifacts/                      # Committed model artifacts and schemas
│   ├── feature_schema.json         # Feature and category schema
│   ├── metrics.json                # Test and slice performance metrics
│   ├── README.md                   # Artifact contract documentation
│   └── transaction_categorizer.joblib # Frozen trained model bundle (~1.2 MB)
├── data/
│   └── README.md                   # Dataset provenance and download instructions
├── docs/                           # Rubric and architectural documentation
│   ├── AI_DEBUG_REPORT.md          # Debugging case study & root cause analysis
│   ├── data_audit.md               # Data audit, hygiene, and leakage gate report
│   ├── PROJECT_BRIEF.md            # Scenario FIN-01 business & technical brief
│   ├── REPRODUCTION_TEST.md        # Step-by-step reproduction instructions
│   └── RESPONSIBLE_AI_AND_LIMITATIONS.md # Ethical considerations & safety
├── notebooks/                      # Exploratory data analysis & experiments
│   ├── 01_data_audit.ipynb
│   └── 02_experiments.ipynb
├── presentation/                   # Pitch deck, presentation slides, and defense
│   ├── FIN_001_Capstone_Presentation.pptx # Slide deck
│   ├── index.html                  # Web presentation deck
│   ├── PRESENTATION_PROMPT_AND_DECK.md # Presentation script and slides
│   ├── Q_AND_A_BANK.md             # Mentor defense Q&A bank
│   └── SPEAKER_FLOW.md             # 5-minute timed speaker pitch flow
├── reports/                        # Gates, experiment logs, and error analysis
│   ├── error_analysis/             # Detailed error breakdown
│   ├── experiment_record.csv       # MLflow experiment log
│   ├── model_gate.md               # Criterion 3 Model Gate report
│   └── results/                    # Confusion matrices and reload proof
├── requirements.txt                # Production application dependencies
├── requirements-experiments.txt    # Extended dependencies for training sweeps
├── scripts/                        # Utility and proof scripts
│   ├── download_data.py            # Automated dataset downloader
│   └── reload_proof.py             # Bundle reload verification script
├── smoke_test.py                   # Pre-deployment sanity smoke test
├── src/                            # Modular production source code
│   ├── evaluate.py                 # Metrics computation and slicing
│   ├── experiments.py              # MLflow sweep pipeline
│   ├── features.py                 # Text normalizer and feature extractors
│   ├── finalize.py                 # Model bundling and artifact serializer
│   ├── inference.py                # Standalone inference engine with guards
│   └── preprocessing.py            # Clean, split, and boundary management
├── Submission Template.docx        # Completed official capstone submission form
└── tests/                          # Automated test suite (16 tests)
    ├── test_app.py                 # Streamlit UI AppTest tests
    ├── test_data_gate.py           # Leakage and split tests
    └── test_inference.py           # Inference contract and safeguard tests
```

---

## 5. Quickstart & Local Reproduction

### Setup Environment

```bash
# Clone the repository
git clone https://github.com/feruz-bb/automatic-transaction-categorization.git
cd automatic-transaction-categorization

# Create and activate Python 3.10 virtual environment
python3.10 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### Run Tests and Smoke Verification

```bash
# 1. Run automated test suite (16 tests)
pytest -q

# 2. Run standalone pre-deploy smoke test
python smoke_test.py
```

### Launch the Streamlit Web Demo

```bash
streamlit run app.py
```

> **Note:** The repository includes the committed artifact bundle (`artifacts/transaction_categorizer.joblib`), allowing the test suite, smoke test, and Streamlit app to run immediately without downloading the dataset or retraining.

### Full Pipeline Reproduction (Optional Retraining)

```bash
# 1. Download dataset (68k rows)
python scripts/download_data.py

# 2. Run experiment sweep & log to MLflow
python -m src.experiments

# 3. Finalize candidate and export model bundle
python -m src.finalize
```

---

## 6. Responsible AI, Safeguards & Limitations

- **Advisory Output Only:** Predictions are intended as an advisory classification aid and do not constitute automated financial or legal advice.
- **Confidence Safeguards:** Any prediction with probability $< 0.50$ or containing zero recognized in-vocabulary terms automatically raises a `needs_review` flag for human intervention.
- **Privacy & PII Protection:** The dataset contains no real customer names, account numbers, or PANs; numeric identifiers (ZIPs, store IDs) are sanitized to `<num>`.
- **Honest Generalization:** While in-distribution synthetic test macro-F1 is 0.9961, the realistic performance on novel unseen merchants is **0.9784** Macro-F1.
- Full details available in [docs/RESPONSIBLE_AI_AND_LIMITATIONS.md](docs/RESPONSIBLE_AI_AND_LIMITATIONS.md).

---

## 7. Project Status & Rubric Evidence

All Capstone criteria (1–8) are completed, verified, and mapped in [RUBRIC_EVIDENCE_MATRIX.md](RUBRIC_EVIDENCE_MATRIX.md) and [PROJECT_STATUS.md](PROJECT_STATUS.md):

| Criterion | Stage | Status | Key Evidence |
|---|---|:---:|---|
| **C1** Problem Definition | C2 | 🟢 GREEN | [docs/PROJECT_BRIEF.md](docs/PROJECT_BRIEF.md) |
| **C2** Data & Preprocessing | C3 | 🟢 GREEN | [docs/data_audit.md](docs/data_audit.md), [tests/test_data_gate.py](tests/test_data_gate.py) |
| **C3** Modeling & Sweep | C4 | 🟢 GREEN | [reports/model_gate.md](reports/model_gate.md), [reports/experiment_record.csv](reports/experiment_record.csv) |
| **C4** Evaluation & Slices | C4 | 🟢 GREEN | [reports/results/test_metrics.json](reports/results/test_metrics.json), [reports/error_analysis/ERROR_ANALYSIS.md](reports/error_analysis/ERROR_ANALYSIS.md) |
| **C5** Deployment & Serving | C5 | 🟢 GREEN | [app.py](app.py), [src/inference.py](src/inference.py), [tests/test_app.py](tests/test_app.py) |
| **C6** Documentation & Reproduction | C6 | 🟢 GREEN | [README.md](README.md), [docs/REPRODUCTION_TEST.md](docs/REPRODUCTION_TEST.md) |
| **C7** Responsible AI | C6 | 🟢 GREEN | [docs/RESPONSIBLE_AI_AND_LIMITATIONS.md](docs/RESPONSIBLE_AI_AND_LIMITATIONS.md) |
| **C8** Presentation & Pitch | C6 | 🟢 GREEN | [presentation/PRESENTATION_PROMPT_AND_DECK.md](presentation/PRESENTATION_PROMPT_AND_DECK.md), [presentation/Q_AND_A_BANK.md](presentation/Q_AND_A_BANK.md) |

---

## 8. Attribution & License

- **Dataset:** *US Bank Transaction Categories v2* by DoDataThings ([Hugging Face Hub](https://huggingface.co/datasets/DoDataThings/us-bank-transaction-categories-v2)), licensed under MIT.
- **Project License:** Distributed under the MIT License.
