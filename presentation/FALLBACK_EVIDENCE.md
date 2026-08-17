# Fallback Evidence — if the live demo fails

If `streamlit run app.py` won't start, hangs, or the network/projector fails during the
defense, do **not** improvise. Switch to this page. Everything here runs from the committed
artifact (`artifacts/transaction_categorizer.joblib`) — no dataset, no retraining, no
internet. Each command produces the same evidence the live demo would have shown.

Say this while switching: *"The app is a thin UI over `src/inference.py`. The model itself is
the committed artifact, and I can show it predicting from a plain terminal."*

---

## Route A — smoke test (fastest, ~2 s)

```bash
python smoke_test.py
```

- **Expected:** `SMOKE TEST PASSED`.
- **What it proves:** the artifact loads and categorizes correctly in a clean run — the same
  path the app uses.

## Route B — reload proof (the pre-captured evidence)

```bash
python scripts/reload_proof.py
```

- **Expected:** loads the bundle in a fresh process and prints `[debit] MTG PMT PENFED CU` →
  **Mortgage**, confidence **0.974**.
- **If you can't run it live,** point to the saved log: **`reports/results/reload_proof.txt`**.
  Same input, same output, captured earlier. Note there is no `.fit` on the load path.

## Route C — full test suite (contract + data gate)

```bash
python -m pytest -q
```

- **Expected:** all tests pass — inference contract (`tests/test_inference.py`) and data-gate
  leakage checks (`tests/test_data_gate.py`, including no-description-crosses-split-boundary).
- **What it proves:** the leakage controls and the inference behavior are enforced, not just
  claimed.

---

## Saved outputs to point at (no commands needed)

| Show this file | It demonstrates |
|---|---|
| `reports/results/reload_proof.txt` | The known-good input → Mortgage 0.974 from a fresh process |
| `artifacts/metrics.json` | Test macro-F1 0.9961, and the unseen-merchant slice 0.9784 |
| `reports/experiment_record.csv` | The full model sweep, incl. embeddings losing (0.9468) |
| `reports/model_gate.md` §8 | Final protected-test result and honest interpretation |
| `reports/error_analysis/ERROR_ANALYSIS.md` | Weakest classes and confusions |

## Known-good demo input (recite if nothing runs)

- Input: **`[debit] MTG PMT PENFED CU`** → **Mortgage**, confidence **≈ 0.974**.
- Contrast input: **`SOME UNFAMILIAR MERCHANT LLC`** → **"needs review"** (zero recognized
  merchant terms → OOV guard fires).

## Last resort — local app fallback

If online Streamlit is the thing that failed, run the app locally instead — see
`presentation/fallback_demo/README.md`. If even that fails, Routes A–C above are sufficient
evidence on their own; the artifact predicting correctly from a terminal is the same proof as
the UI.
