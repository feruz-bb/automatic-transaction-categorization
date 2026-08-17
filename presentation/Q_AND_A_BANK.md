# Q&A Bank — FIN-001 Defense

Likely examiner questions with honest, evidence-backed answers. Every claim points to a real
file. Answer short, then offer the file. When a number is optimistic, say so first — that
lands better than being caught.

---

### 1. Isn't a 99% score suspicious?

Yes, and I treated it as a red flag, not a trophy. Three things explain it and one caveat
qualifies it:
- **Duplicates handled.** The raw file is 33% exact duplicates (22,298 of 68,000). I
  de-duplicate to one row per unique description *before* splitting, so no identical string
  can memorize across train/test. A test asserts this (`test_no_description_crosses_split_boundary`).
- **The honest slice.** On 716 test transactions from merchants *never seen in training*, the
  score drops to macro-F1 0.9784 — that ~1.8-point gap is the realistic degradation.
- **The caveat.** The data is synthetic-in-format, templated around ~500 merchants, so the
  in-distribution 0.9961 is optimistic. I don't present it as production accuracy.
- **Evidence:** `docs/data_audit.md` §2, `artifacts/metrics.json`, `reports/error_analysis/ERROR_ANALYSIS.md` §2.

### 2. Why not deep learning / transformers?

I tested them and they lost. MiniLM sentence embeddings + LogReg scored 0.9468 on validation
versus 0.9960 for TF-IDF + LogReg — worse, and about 40× slower to fit/predict. The reason is
the data: these are short, structured merchant strings where the discriminative signal is
specific tokens (`MTG PMT`, `DIR DEP`, `PUBLIX`). Sparse bag-of-words captures those directly;
dense semantic embeddings blur exactly the distinctions that matter. Shipping a heavy
transformer would also drag torch onto a free Streamlit host for no accuracy gain.
- **Evidence:** `reports/experiment_record.csv` (`embed_minilm_logreg` row), `reports/model_gate.md` §5.

### 3. How do you handle unseen merchants?

Two ways — measurement and a runtime guard. **Measurement:** I carved out a 716-row slice of
test transactions whose merchant never appears in training and score it separately (macro-F1
0.9784) so the "how does it generalize?" question has a number, not a hope. **Runtime:**
bag-of-words silently ignores unknown words, so a fully novel string can still return a
confident default class. The inference layer counts recognized *merchant* terms (excluding the
`<num>`/`flag_*` structural tokens); if zero are recognized, the result is flagged "needs
review" regardless of probability.
- **Evidence:** `src/inference.py` (`_content_coverage`, `known_terms` guard), `reports/error_analysis/ERROR_ANALYSIS.md` §2.

### 4. Where's the leakage protection?

Four controls, each verified:
- De-duplicate before the split (no string in two partitions) — `test_no_description_crosses_split_boundary`.
- TF-IDF vocabulary/IDF fit on **train only**; valid/test only transformed — `reports/preprocessing_manifest.json` `fit_boundary`.
- Per-transaction IDs (store #, ZIP, PPD/ref) normalized to `<num>` so the model can't
  fingerprint rows — `test_normalizer_is_deterministic_and_strips_ids`.
- The protected test set is read only in `src/finalize.py`, after the candidate is frozen.
- **Evidence:** `docs/data_audit.md` §5, `reports/model_gate.md` §2 and §7.

### 5. Why macro-F1 rather than accuracy?

The 17 categories are roughly balanced and all matter equally to the user — getting Fees or
Transfer right is as important as Groceries. Macro-F1 weights every class equally, so a model
can't win by acing the big classes and neglecting small ones. Accuracy and top-3 accuracy are
reported alongside for interpretability, but macro-F1 is the scoreboard.
- **Evidence:** `reports/model_gate.md` §1.

### 6. What happens on a transaction that fits no category?

The taxonomy is fixed at 17 classes, so the model is forced to pick the nearest one — I don't
pretend otherwise. The mitigation is confidence-based: if the top probability is below 0.50,
*or* zero merchant terms are recognized, the app returns "needs review — low confidence"
instead of auto-applying. That's the brief's ambiguous-case requirement. A wrong auto-applied
category would misstate a user's spending summary, so surfacing for human review is the safe
default.
- **Evidence:** `src/inference.py` (`is_uncertain`), `app.py`, `reports/model_gate.md` §9.

### 7. Is this real bank data?

No, and I'm explicit about it everywhere. It's synthetic-in-format: realistic debit/credit
formats built around 500+ real merchant names with randomized store numbers and reference
codes, but no real accounts, names, or PII. Real transaction data is private. The consequence
is that in-distribution accuracy is optimistic, which is exactly why I report the
unseen-merchant slice as the honest estimate.
- **Evidence:** `data/README.md` §4, `README.md` §15.

### 8. How would this degrade in production?

The unseen-merchant slice is my proxy: expect roughly a 1.8-point macro-F1 drop as a floor,
and likely more on genuinely messy live feeds, because real descriptions are noisier than this
templated set. Failure modes: novel merchants collapse to an intercept-dominated default class
(caught by the OOV guard), and inherently ambiguous merchants — big-box stores that are both
Groceries and Shopping — get confused (caught by the confidence threshold). Both surface as
"needs review" rather than silent errors. In production I'd monitor the review-flag rate and
retrain as the merchant landscape shifts.
- **Evidence:** `reports/model_gate.md` §8–§9, `reports/error_analysis/ERROR_ANALYSIS.md` §4–§5.

### 9. Why Logistic Regression over the higher-scoring char-SVM?

The char-n-gram LinearSVC scored 0.9971 vs 0.9960 — 0.0011 higher — but a LinearSVC produces
no calibrated probabilities. The brief explicitly requires confidence-based handling of
ambiguous transactions, so `predict_proba` is a functional requirement, not a nicety. LogReg
delivers confidence and top-3 alternatives at a 0.0011 macro-F1 cost. That's a deliberate,
documented trade-off.
- **Evidence:** `reports/model_gate.md` §6, `reports/experiment_record.csv`.

### 10. How do you know the artifact actually works after loading — not just in your notebook?

A reload proof runs in a fresh, plain Python process (not a notebook, so no hidden state):
`scripts/reload_proof.py` loads the committed bundle and predicts on `[debit] MTG PMT PENFED
CU` → `Mortgage` at 0.974. There's no `.fit` on the load path — `src/inference.py` only calls
`predict_proba`. The whole app, smoke test, and tests run from the committed artifact without
the raw data.
- **Evidence:** `reports/results/reload_proof.txt`, `reports/model_gate.md` §11.

### 11. Did the test set ever influence model selection?

No. Every candidate is selected on the validation split (n=6,854). The test split is
referenced only inside `src/finalize.py`, which runs *after* `FINAL_RUN = "tfidf_word_logreg"`
is fixed. It's scored exactly once. There was no tuning loop against test.
- **Evidence:** `reports/model_gate.md` §7, `docs/data_audit.md` §4.

### 12. What are the weakest categories, and why?

Healthcare, Shopping and Groceries have the lowest per-class F1 (~0.984–0.986). The confusions
cluster where merchant text is genuinely ambiguous — a big-box store that sells both groceries
and general goods, for example. These are inherent taxonomy overlaps, not model defects, and
they're the cases the confidence fallback is designed to catch.
- **Evidence:** `reports/error_analysis/ERROR_ANALYSIS.md` §3–§4.

### 13. Why 0.50 as the confidence threshold?

It's the operating point for the "needs review" fallback — below it, or with zero recognized
merchant terms, the app declines to auto-apply. It's stored in the bundle
(`low_confidence_threshold`) rather than hard-coded, so it's tunable without retraining. In a
real deployment I'd set it from the precision/coverage trade-off the product wants (how many
auto-applied categories vs how many sent to review).
- **Evidence:** `src/inference.py`, `app.py`.

### 14. Is this reproducible by the assessor?

Yes, end to end. Open dataset with no login (`python scripts/download_data.py`), then
`python -m src.experiments` rebuilds the split and experiment record, `python -m src.finalize`
rebuilds the artifact and metrics, `python smoke_test.py` and `python -m pytest -q` verify.
The split isn't committed but is deterministic (`random_state=42`).
- **Evidence:** `README.md` Quickstart, `docs/REPRODUCTION_TEST.md`, `data/README.md` §5.

### 15. Could you just use rules / a lookup table instead of ML?

Rules are exactly what doesn't scale — that's the problem statement. New merchants and format
variants appear constantly, and a hand-maintained rule set decays. The model generalizes from
merchant tokens it learned, and the unseen-merchant slice shows it holds up reasonably on
merchants no rule would cover. Where it's unsure, it defers to a human — which is what a rules
system can't gracefully do.
- **Evidence:** `README.md` §3, `reports/error_analysis/ERROR_ANALYSIS.md` §2.
