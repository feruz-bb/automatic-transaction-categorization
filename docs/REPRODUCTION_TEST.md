# Reproduction Test — FIN-001

Anyone with Python 3.10 can reproduce every result from a clean clone. These are the exact
steps, with the expected output at each checkpoint.

## 0. Prerequisites

- Python **3.10.x** (the pins in `requirements.txt` are verified on 3.10.11; 3.10 is also
  what Streamlit Community Cloud runs, so the artifact loads identically there).
- macOS/Linux shell.

## 1. Environment

```bash
python3.10 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## 2. Fastest path — verify the shipped artifact (no data, no training)

The model bundle is committed, so these run immediately:

```bash
python smoke_test.py          # expect final line: SMOKE TEST PASSED
python -m pytest -q           # expect: all tests pass (13 passed)
python scripts/reload_proof.py  # expect: RELOAD PROOF OK ...
```

`smoke_test.py` and the tests prove the deployed inference path works with only the files a
Streamlit host has.

## 3. Full path — rebuild everything from raw data

```bash
python scripts/download_data.py        # downloads data/raw/transactions-synthetic.csv (68,000 rows)
python -m src.experiments              # rebuilds split + reports/experiment_record.csv + mlflow.db
python -m src.finalize                 # scores the protected test once, rebuilds the artifact
```

Expected key numbers (deterministic under `random_state=42`):

| Checkpoint | Expected |
|---|---|
| Rows after cleaning | 45,692 (train 31,984 / valid 6,854 / test 6,854) |
| Best validation run | `tfidf_char_linsvm` macro-F1 0.9971; deployed `tfidf_word_logreg` 0.9960 |
| Majority baseline (valid) | macro-F1 0.0094 |
| Embedding run (valid) | `embed_minilm_logreg` macro-F1 0.9468 |
| **Protected test** | macro-F1 **0.9961**, accuracy 0.9955, top-3 0.9990 |
| Unseen-merchant slice | macro-F1 0.9784 (n=716) |

> The embedding run needs the extra deps: `pip install -r requirements-experiments.txt`.
> Without them, `python -m src.experiments` runs the classic runs and logs a skip note.

## 4. The app

```bash
streamlit run app.py
```

Type the known-good input `[debit] MTG PMT PENFED CU` → expect **Mortgage**, confidence
≈ 0.97, not flagged for review. Type gibberish (`zzz qqq 000`) → expect a **needs-review**
warning (no recognized merchant terms).

## 5. Gate validators (course tooling)

```bash
python ../04_C4_model_gate/validators/validate_model_gate_evidence.py .   # expect: GREEN, exit 0
```
