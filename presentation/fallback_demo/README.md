# Fallback Demo — running the app locally

Use this if the **public** Streamlit deployment is unavailable during the defense but your
laptop works. It runs the exact same app locally, off the committed artifact — no dataset and
no internet required.

## Run it

From the repository root:

```bash
source .venv/bin/activate      # or: python3.10 -m venv .venv && pip install -r requirements.txt
streamlit run app.py
```

It opens at `http://localhost:8501`. The app loads only
`artifacts/transaction_categorizer.joblib`; there is no training step.

## Known-good input to type

```
[debit] MTG PMT PENFED CU
```

Expected: **Mortgage**, confidence **≈ 97%** (0.974), with the top-3 alternatives shown.

## Second input — to show the "needs review" fallback

```
SOME UNFAMILIAR MERCHANT LLC
```

Expected: **"Needs review — low confidence"** — no familiar merchant terms are recognized, so
the OOV guard flags it rather than guessing. This is the confidence-based handling the brief
asks for.

## If even the local app fails

Fall back to the terminal evidence in `presentation/FALLBACK_EVIDENCE.md`
(`python smoke_test.py`, `python scripts/reload_proof.py`, `python -m pytest -q`) and the saved
`reports/results/reload_proof.txt`. The artifact predicting correctly from a plain process is
the same proof as the UI.
