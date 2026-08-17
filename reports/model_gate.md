# Model Gate Evidence

> File location: `reports/model_gate.md`
> All numbers below are produced by `python -m src.experiments` (validation) and
> `python -m src.finalize` (protected test), and mirrored in `artifacts/metrics.json`.

## 1. Project task and primary metric

- **Project task:** NLP multi-class text classification — assign a bank transaction to one of 17 spending categories from its description string (FIN-01 brief).
- **Expected user or stakeholder:** a digital-banking / personal-finance app that shows users categorized spending summaries and needs categorization to scale beyond hand-maintained rules.
- **Raw input:** one transaction description, e.g. `"[debit] PUBLIX 7860 UNIVERSITY LN OAKLAND CA"`. The debit/credit prefix is optional.
- **Model output:** one category label (of 17) plus a confidence and the top-3 alternatives; low-confidence / unrecognized inputs are flagged for human review.
- **Primary metric:** macro-averaged F1.
- **Why this metric matches the project need:** the 17 categories are roughly balanced and all matter to the user (Fees and Transfer are as important to get right as Groceries), so a macro average — which weights every class equally — is the honest scoreboard. Accuracy and top-3 accuracy are reported alongside for interpretability.

## 2. Data and split identifiers

- **Data version or snapshot:** `DoDataThings/us-bank-transaction-categories-v2` (Hugging Face, MIT), file `transactions-synthetic.csv`, 68,000 raw rows. Retrieval: `python scripts/download_data.py`.
- **Split ID / strategy:** stratified by category into train / valid / test = 70 / 15 / 15, `random_state=42` (`src/preprocessing.py:make_split`). After cleaning: 45,692 unique descriptions → train 31,984 · valid 6,854 · test 6,854.
- **Train / validation / protected test boundaries:** experiments train on `train`, select on `valid`; `test` is loaded only by `src/finalize.py`.
- **Leakage-prevention note:** the raw file has 22,298 exact-duplicate rows and 5 label-ambiguous descriptions. `src/preprocessing.py:clean` reduces to one row per unique description **before** the split, so no identical string can appear in two partitions. Verified by `tests/test_data_gate.py::test_no_description_crosses_split_boundary`. Store numbers, ZIPs and reference/PPD IDs are replaced with `<num>` so the model cannot key on per-transaction random codes.
- **Preprocessing fit boundary:** the TF-IDF vocabulary and the model are fit on the `train` split only; `valid`/`test` are only transformed. Text normalization (`src/features.py:normalize_description`) is deterministic and stateless, so it is leakage-safe by construction. Documented in `reports/preprocessing_manifest.json` (`fit_boundary`).

## 3. Baseline

- **Baseline run ID / record:** `baseline_majority` in `reports/experiment_record.csv`.
- **Baseline type:** naive most-frequent-class classifier (`sklearn.DummyClassifier`).
- **Baseline configuration:** `strategy="most_frequent"`, same split and metric as every other run.
- **Baseline validation/CV result:** macro-F1 **0.0094**, accuracy 0.0867 (the majority class is ~8.7% of rows).
- **Baseline artifact link:** row `baseline_majority` in `reports/experiment_record.csv`; reproduced by `python -m src.experiments`.

## 4. Experiment hypotheses

| Run ID | Hypothesis | One changed factor | Stable controls | Validation/CV result | Artifact | Conclusion |
|---|---|---|---|---|---|---|
| baseline_majority | Most-frequent class sets the floor | classifier = Dummy | split, metric, protocol | macro-F1 0.0094 | experiment_record.csv | Floor established |
| tfidf_word_logreg | Merchant words linearly separate the 17 classes | word 1–2gram + LogReg | split, metric, protocol | macro-F1 0.9960 | transaction_categorizer.joblib | Strong; probabilistic — selected |
| tfidf_char_linsvm | Char n-grams generalize better to unseen merchants | char_wb 3–5gram + LinearSVC | split, metric, protocol | macro-F1 0.9971 | experiment_record.csv | Best F1 but no predict_proba |
| tfidf_word_complementnb | A fast NB text baseline is competitive | word 1–2gram + ComplementNB | split, metric, protocol | macro-F1 0.9915 | experiment_record.csv | Competitive, slightly lower |
| embed_minilm_logreg | Semantic embeddings beat bag-of-words | MiniLM embeddings + LogReg | split, metric, protocol | macro-F1 0.9468 | experiment_record.csv | Worse and heavier — rejected |

## 5. Run comparison

- **MLflow experiment / equivalent record:** MLflow experiment `FIN-001` in `mlflow.db` (regenerate with `python -m src.experiments`), plus the human-readable `reports/experiment_record.csv`.
- **Comparison table or screenshot:** `reports/experiment_record.csv` (sorted by validation macro-F1).
- **Same split and metric confirmed:** yes — every run calls the same `load_split()` and `src/evaluate.py:score`; validation rows n=6,854 for all runs.
- **Important failed or neutral experiment:** `embed_minilm_logreg` — general-purpose sentence embeddings scored 0.9468, clearly below the sparse TF-IDF models (0.9915–0.9971), at ~40× the fit/predict time.
- **What that experiment taught:** for short, highly structured merchant strings the discriminative signal is specific tokens (`MTG PMT`, `PUBLIX`, `DIR DEP`), which sparse bag-of-words captures directly; dense semantic embeddings blur exactly those distinctions. This justifies shipping the lightweight TF-IDF model rather than a transformer.

## 6. Selected candidate or current blocker

- **Selected run ID:** `tfidf_word_logreg`.
- **Compared directly with baseline:** macro-F1 0.9960 vs 0.0094 on validation — a ~106× lift over the majority-class floor.
- **Decisive quality / error / cost trade-off:** `tfidf_char_linsvm` scores marginally higher (0.9971 vs 0.9960) but a `LinearSVC` produces no calibrated probabilities. The brief explicitly requires confidence-based handling of ambiguous transactions, so a model with `predict_proba` is a functional requirement, not a nicety. LogReg delivers that at a 0.0011 macro-F1 cost.
- **One rejected alternative and reason:** `embed_minilm_logreg` rejected — lower accuracy and it would drag torch/sentence-transformers onto the free Streamlit host.
- **Current limitation:** in-vocabulary/templated merchants are near-perfect; genuinely novel merchant strings are harder (see §8–§9). This inflates headline numbers relative to messy real bank data.
- **If blocked, exact blocker and next action:** not blocked.

## 7. Protected test status

- **Protected test used for candidate selection or tuning:** no. The `test` split is referenced only in `src/finalize.py`, which runs after the candidate is chosen from validation.
- **Candidate locked before final test evaluation:** yes — `FINAL_RUN = "tfidf_word_logreg"` is fixed in `src/finalize.py` before any test prediction.
- **Final test access date / run:** produced by `python -m src.finalize`; results in `artifacts/metrics.json` and `reports/results/test_metrics.json`.
- **Repair note if test contamination occurred:** not applicable — no contamination.

## 8. Final evaluation

- **Selected candidate protected-test result:** macro-F1 **0.9961**, accuracy 0.9955, top-3 accuracy 0.9990 (n=6,854).
- **Baseline protected-test result:** majority-class macro-F1 ≈ 0.01 (baseline is trivial by construction; the validation floor of 0.0094 stands as the comparison point).
- **Primary and supporting metrics:** primary macro-F1 0.9961; supporting — unseen-merchant slice (716 test rows from merchants never seen in training) macro-F1 **0.9784**, accuracy 0.9930, vs seen-merchant macro-F1 0.9962.
- **Honest interpretation:** the model is genuinely strong, but the ~1.8-point macro-F1 drop on unseen merchants is the realistic signal of how it would degrade on novel real-world merchant strings. The near-perfect in-distribution score reflects that the data is templated around a fixed set of ~500 merchants; it should not be read as production accuracy on messy live bank feeds.

## 9. Error / failure analysis

- **Critical error or failure type:** (a) confusions between semantically overlapping categories (e.g. big-box merchants that are both Groceries and Shopping); (b) over-confident predictions on out-of-vocabulary input, because bag-of-words silently ignores unknown words.
- **Saved examples / residuals / unstable cases:** `reports/error_analysis/ERROR_ANALYSIS.md`, `reports/results/per_class_test.csv`, `reports/results/top_confusions_test.csv`.
- **Likely cause:** (a) inherent taxonomy overlap in merchant semantics; (b) sparse features produce a near-empty vector for novel text, collapsing to an intercept-dominated class.
- **User or stakeholder impact:** a wrong auto-applied category misstates a user's spending summary. Mitigated by the confidence-based fallback: predictions below 0.50 top-probability, or with zero recognized merchant terms, are surfaced as "needs review" rather than auto-applied (`src/inference.py`, `known_terms` guard).
- **Known subgroup / class / range weakness:** the weakest categories and top confusions are tabulated in `reports/error_analysis/ERROR_ANALYSIS.md`; unseen-merchant transactions are the known weak slice.

## 10. Complete inference artifact

- **Artifact path:** `artifacts/transaction_categorizer.joblib` (committed; ~1.2 MB).
- **Framework and version:** scikit-learn 1.7.2, joblib 1.5.3, Python 3.10.11 (see `requirements.txt`).
- **Included learned preprocessing:** the fitted TF-IDF vectorizer is inside the pickled `sklearn.Pipeline`; the stateless text normalizer is versioned in `src/features.py`.
- **Input schema / label map / processor:** raw input schema and the 17-class list in `artifacts/feature_schema.json`; class order in `bundle["classes"]`.
- **Loading instructions:** see `artifacts/README.md`.

## 11. Reload proof

- **Fresh runtime/process used:** `.venv/bin/python scripts/reload_proof.py` — a plain process, not a notebook, so no hidden state can assist.
- **Known raw input:** `"[debit] MTG PMT PENFED CU"` (and three others).
- **Observed output:** `Mortgage` at confidence 0.974 (full log in `reports/results/reload_proof.txt`).
- **No fit/fine-tune step after load:** confirmed — `src/inference.py` only calls `predict_proba`; there is no `.fit` on the load path.
- **Reload proof file / screenshot / log:** `reports/results/reload_proof.txt`.

## 12. Limitations

- The dataset is synthetic-in-format (real bank data is private). Text is templated around ~500 real merchants, so in-distribution accuracy is optimistic relative to messy live feeds.
- Bag-of-words has no understanding of unseen merchants; the OOV guard flags them but cannot categorize them correctly.
- The taxonomy is fixed at 17 categories; transactions that fit none of them are forced into the nearest class (surfaced via low confidence).
- No personal or real financial data is used; the model must not be presented as production-grade or as financial advice.

## 13. Next action and milestone commit

- **Next evidence-based action:** deploy the frozen bundle to Streamlit Community Cloud (C5) and complete the C6 finalization evidence.
- **Model Gate status:** GREEN.
- **Named correction and deadline if YELLOW:** not applicable.
- **Milestone commit hash / message:** to be recorded by the student at commit time — suggested message: `"Model Gate: TF-IDF+LogReg categorizer, test macro-F1 0.9961, artifact + reload proof"` (GitHub step deferred per project owner).

---

### Final self-check

- [x] Baseline is visible and reproducible.
- [x] Runs are controlled and traceable.
- [x] Candidate was selected from validation/CV evidence.
- [x] Protected test did not choose the winner.
- [x] Error/failure examples are repository-visible.
- [x] Complete artifact includes learned preprocessing.
- [x] Fresh-runtime reload works without refitting.
- [x] `artifacts/README.md` contains exact loading instructions.
- [ ] Repository contains one meaningful model-stage commit. *(commit is the owner's deferred GitHub step)*
