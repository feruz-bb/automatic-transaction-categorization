# Rubric Evidence Matrix — FIN-001

Where an assessor can verify each criterion. Pass = 60/100; every criterion is above its
minimum. Status: 🟢 strong evidence present.

| # | Criterion | Max | Min | Status | Evidence (exact paths) |
|---|---|---:|---:|:--:|---|
| 1 | Problem Definition & Project Alignment | 10 | 6 | 🟢 | `docs/PROJECT_BRIEF.md` (both FIN-01 tables filled), `README.md` §1–§2 |
| 2 | Data & Preprocessing Pipeline | 15 | 9 | 🟢 | `data/README.md`, `docs/data_audit.md`, `reports/preprocessing_manifest.json`, `src/preprocessing.py`, `src/features.py`, `tests/test_data_gate.py` |
| 3 | Modeling & Experiments | 20 | 12 | 🟢 | `reports/model_gate.md`, `reports/experiment_record.csv`, `mlflow.db`, `src/experiments.py`, `notebooks/02_experiments.ipynb` |
| 4 | Evaluation & Error Analysis | 15 | 9 | 🟢 | `reports/error_analysis/ERROR_ANALYSIS.md`, `reports/results/` (test_metrics.json, per_class_test.csv, top_confusions_test.csv), `src/evaluate.py` |
| 5 | End-to-End Implementation & Delivery | 20 | 12 | 🟢 | `app.py`, `src/inference.py`, `artifacts/transaction_categorizer.joblib`, `artifacts/README.md`, `smoke_test.py`, `tests/test_inference.py`, `reports/results/reload_proof.txt` |
| 6 | Documentation & Reproducibility | 10 | 6 | 🟢 | `README.md`, `requirements.txt`, `docs/REPRODUCTION_TEST.md`, `scripts/download_data.py` |
| 7 | Responsible AI & Limitations | 5 | 3 | 🟢 | `docs/RESPONSIBLE_AI_AND_LIMITATIONS.md`, `README.md` §6 |
| 8 | Presentation, Demo & Q&A | 5 | 3 | 🟢 | `presentation/SPEAKER_FLOW.md`, `presentation/Q_AND_A_BANK.md`, `presentation/DEFENSE_DECK_MAP.md`, `presentation/FALLBACK_EVIDENCE.md`, live `streamlit run app.py` |

## Hard requirements

- ✅ **Trained model:** `artifacts/transaction_categorizer.joblib` (TF-IDF + LogReg).
- ✅ **Evaluated on unseen data:** protected test macro-F1 0.9961 (`artifacts/metrics.json`).
- ✅ **Working end-to-end demo:** `streamlit run app.py` (verified locally, HTTP 200 + real prediction).
- ✅ **Reproduction instructions:** `docs/REPRODUCTION_TEST.md`.
- ✅ **Repository:** Published on GitHub at https://github.com/feruz-bb/automatic-transaction-categorization
- ⏳ **Defense attendance:** owner action.
