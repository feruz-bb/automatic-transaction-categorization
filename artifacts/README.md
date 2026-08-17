# Artifact Loading and Reload Evidence

> File location: `artifacts/README.md`

## Artifact identity

- **Artifact name:** `transaction_categorizer.joblib`
- **Artifact version:** 1.0.0 (`bundle["model_version"]`)
- **Framework / library versions:** scikit-learn 1.7.2, joblib 1.5.3, numpy 2.2.6, Python 3.10.11 (see `requirements.txt`).
- **Repository path:** `artifacts/transaction_categorizer.joblib` (~1.2 MB, committed on purpose so the Streamlit app can start).
- **External storage URL, if applicable:** Not used.
- **Checksum, if applicable:** Not used (regenerate deterministically with `python -m src.finalize`).

## What the artifact contains

The bundle is a single `dict` saved with `joblib.dump(..., compress=3)`:

- **Estimator / model:** a fitted `sklearn.Pipeline` = `TfidfVectorizer` → `LogisticRegression`, under `bundle["pipeline"]`.
- **Learned preprocessing:** the fitted TF-IDF vocabulary + IDF weights live inside that pipeline (fit on the training split only).
- **Tokenizer / vectorizer / processor:** the TF-IDF vectorizer is the pipeline's first step; the stateless text normalizer that runs before it is versioned in `src/features.py:normalize_description`.
- **Label map / target mapping:** `bundle["classes"]` — the 17 category strings in the pipeline's class order (`pipeline.classes_`).
- **Configuration:** `bundle["low_confidence_threshold"] = 0.50`, `bundle["target"] = "category"`, `bundle["final_run"] = "tfidf_word_logreg"`, `bundle["test_macro_f1"] = 0.9961`.
- **Interpretation assumptions:** categories are best-effort spending labels; low-confidence and zero-recognized-term inputs are surfaced for human review, not auto-applied.

## Raw input schema

Describe the exact input expected at prediction time.

| Field / component | Type / shape | Required | Example | Notes |
|---|---|---|---|---|
| description | str | yes | `[debit] PUBLIX 7860 UNIVERSITY LN OAKLAND CA` | One transaction string; the `[debit]`/`[credit]` prefix is optional. Normalized internally before the model sees it. |

## Dependencies

```text
See requirements.txt (deployment surface). The artifact loads with just:
scikit-learn==1.7.2, joblib==1.5.3, numpy==2.2.6
```

## Retrieval steps

1. Clone the repository (the bundle is committed under `artifacts/`).
2. Create the environment: `python3.10 -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt`.
3. No download needed for inference — the artifact is already present.

Do not include passwords, tokens, or API keys.

## Load instructions

```python
from src.inference import load_bundle
bundle = load_bundle()          # loads + validates artifacts/transaction_categorizer.joblib
print(bundle["model_version"], len(bundle["classes"]))
```

## Prediction instructions

```python
from src.inference import load_bundle, categorize
bundle = load_bundle()
result = categorize("[debit] MTG PMT PENFED CU", bundle)
print(result.category, result.confidence, result.is_uncertain)
# -> Mortgage 0.974 False
```

## Known input and expected output path

- **Known input file / value:** `"[debit] MTG PMT PENFED CU"` (and the set in `scripts/reload_proof.py`).
- **Observed output:** `Mortgage`, confidence ≈ 0.974, `is_uncertain=False`.
- **Output interpretation:** the predicted spending category, its probability, and whether it should be sent for human review.

## Reload proof

- **Fresh process/runtime command:** `.venv/bin/python scripts/reload_proof.py`
- **Reload proof location:** `reports/results/reload_proof.txt`
- **Confirmed no refit/fine-tune after load:** yes — the load path calls only `predict_proba`; there is no `.fit()` after `joblib.load`.
- **Hidden notebook state excluded:** yes — the proof runs as a standalone script, not a notebook, so nothing from a prior cell can help.

## Known limitations

- Trained on synthetic-format data templated around ~500 real merchants; accuracy on messy live bank feeds will be lower (unseen-merchant test-slice macro-F1 is 0.9784 vs 0.9961 overall).
- Bag-of-words cannot categorize a genuinely unseen merchant correctly; such inputs are flagged uncertain rather than trusted.
