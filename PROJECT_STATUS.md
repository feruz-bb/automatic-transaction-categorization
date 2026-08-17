# PROJECT STATUS — FIN-001 Automatic Transaction Categorization

## Stage

- **Current stage:** Model Gate (C4) complete; Deployment (C5) built and verified locally; Finalization (C6) evidence in place. Remaining owner step: push to GitHub and deploy to Streamlit Community Cloud.
- **Scenario:** FIN-01 — assign bank transactions to spending categories from their description text.

## Status

| Gate | Criterion | Status | Note |
|---|---|---|---|
| C2 Repo | 1, 6 | GREEN | Repo scaffold, README, docs, tests in place |
| C3 Data Gate | 2 | GREEN | `docs/data_audit.md`, leakage tests pass |
| C4 Model Gate | 3, 4 | GREEN | `validate_model_gate_evidence.py` exit 0; test macro-F1 0.9961 |
| C5 Deployment | 5 | LOCAL-VERIFIED | `streamlit run app.py` serves predictions; smoke test + pytest green. Public deploy is the owner's deferred GitHub step |
| C6 Finalization | 6, 7, 8 | GREEN | Rubric matrix, reproduction test, responsible-AI, presentation pack |

- **Next step:** owner creates the GitHub repo, commits milestones, and deploys `app.py` to share.streamlit.io.
- **Blockers:** none. Deployment is gated only on the owner's GitHub decision ("i will tell").

### Debugging milestone — 2026-08-12

- **Fixed:** the Streamlit demo (`app.py`) crashed with `KeyError` when the model bundle
  lacked the optional `test_macro_f1` display metric — a key outside the validated
  `load_bundle` contract. Now read defensively via `.get()`. See `docs/AI_DEBUG_REPORT.md`.
- **Verification added:** `tests/test_app.py` (Streamlit `AppTest`) — the main run path had
  no automated coverage before; it now has 3 tests (render, empty input, bundle-contract edge).
- **Result:** full suite 16 passed (was 13); live app boots HTTP 200.
- **Next project step:** owner's GitHub + Streamlit Community Cloud deployment.

## Evidence

- **Dataset:** `data/README.md` — `DoDataThings/us-bank-transaction-categories-v2` (MIT, open).
- **Data Gate:** `docs/data_audit.md`, `reports/preprocessing_manifest.json`, `tests/test_data_gate.py`.
- **Model Gate:** `reports/model_gate.md`, `reports/experiment_record.csv`, `mlflow.db`, `artifacts/metrics.json`.
- **Error analysis:** `reports/error_analysis/ERROR_ANALYSIS.md`, `reports/results/`.
- **Artifact + reload proof:** `artifacts/transaction_categorizer.joblib`, `artifacts/README.md`, `reports/results/reload_proof.txt`.
- **Deployment:** `app.py`, `src/inference.py`, `smoke_test.py`, `tests/test_inference.py`.
- **Reproduction:** `docs/REPRODUCTION_TEST.md`.
- **Known-good input:** `"[debit] MTG PMT PENFED CU"` → `Mortgage` (confidence ≈ 0.974).

_Last updated: 2026-08-12._
