# Data Audit — FIN-001 Transaction Categorization

> Data Gate evidence. Companion to `data/README.md` (provenance) and
> `reports/preprocessing_manifest.json` (machine-readable fit boundary).

## 1. Project and data context

- **Task:** assign a bank transaction to one of 17 spending categories from its description.
- **Dataset:** `DoDataThings/us-bank-transaction-categories-v2` (MIT), 68,000 rows, columns `description`, `category`.
- **Unit of analysis:** one transaction description.
- **Prediction moment:** at posting time only the description string is known — the model uses nothing else, so no post-outcome field can leak.

## 2. Audit summary

| Check | Result | Action |
|---|---|---|
| Rows / columns | 68,000 × 2 | — |
| Nulls | 0 in both columns | none needed |
| Classes | 17, balanced (4,000 each) | macro-F1 as primary metric |
| Exact duplicate rows | 22,298 (32.8%) | de-duplicate before splitting (DQ-01) |
| Ambiguous descriptions (same text, >1 label) | 5 | drop both sides (DQ-02) |
| Random identifiers in text (store #, ZIP, PPD/ref IDs) | pervasive | normalize to `<num>` (DQ-03) |
| Debit/credit prefix present | all rows (60,007 debit / 7,993 credit) | keep as `flag_*` token |
| Description length | median 3 tokens, max 14 | short-text TF-IDF settings |
| Rows after cleaning | 45,692 unique descriptions | model-ready |

**Written EDA conclusions.** The category is strongly recoverable from merchant tokens
(`MTG PMT`→Mortgage, `DIR DEP`→Income, `PUBLIX`→Groceries), which a TF-IDF model captures
directly — validation macro-F1 0.996 vs a 0.009 majority baseline. The signal is real, not
an artifact of duplicates: after de-duplication the score holds at 0.997. The main risks are
not "is there signal?" but "is the signal honestly measured?" (duplicates, ID memorization)
and "does it generalize to unseen merchants?" — both addressed below.

## 3. Data-quality issue log

| ID | Issue | Decision | Status |
|---|---|---|---|
| DQ-01 | 22,298 exact-duplicate rows | De-duplicate to one row per unique description **before** the split so no identical string can cross the boundary | Resolved (`src/preprocessing.py:clean`) |
| DQ-02 | 5 descriptions with two different labels | Drop both sides — unresolvable label noise | Resolved |
| DQ-03 | Store numbers, ZIPs, PPD/reference IDs vary per transaction | Replace identifier tokens with `<num>` in `normalize_description` | Resolved (`src/features.py`) |
| DQ-04 | Synthetic-format data → optimistic accuracy | Report an unseen-merchant evaluation slice as the honest generalization estimate | Resolved (`reports/error_analysis/`) |
| DQ-05 | Fixed 17-category taxonomy; some categories overlap (e.g. Groceries/Shopping) | Surface low-confidence predictions for human review rather than auto-apply | Resolved (inference confidence + OOV guard) |

## 4. Split decision

- **Strategy:** stratified by category into train / valid / test = 70 / 15 / 15, `random_state=42` (`src/preprocessing.py:make_split`). Counts: train 31,984 · valid 6,854 · test 6,854.
- **What must stay unseen:** the `test` split is read only by `src/finalize.py`, after the candidate is frozen. Validation drives model selection.
- **Why it matches real use:** each transaction is categorized independently from its own text, so a per-row stratified split reflects the real prediction setting; stratification keeps all 17 classes proportionally represented in every partition.
- **Verification output:** `tests/test_data_gate.py` asserts (a) descriptions are unique after cleaning, (b) **no description appears in more than one split**, (c) every row is assigned a split, (d) class shares are preserved within 2 points across partitions. All pass.
- **Generalization view:** a secondary *unseen-merchant* slice (test rows whose merchant never appears in training, n=716) is evaluated separately to answer the brief's "how are unseen merchants handled?" — it is not used for selection.

## 5. Leakage risks and controls

| Risk | Why it would leak | Control | Verification | Severity |
|---|---|---|---|---|
| Duplicate strings across splits | Identical description in train and test = memorization scored as generalization | De-duplicate before splitting | `test_no_description_crosses_split_boundary` | High |
| Fitting TF-IDF/IDF on all data | Vocabulary/IDF would encode valid+test tokens | Vectorizer fit on `train` split only; valid/test only transformed | `reports/preprocessing_manifest.json` `fit_boundary`; code path in `src/experiments.py` / `src/finalize.py` | High |
| Per-transaction IDs as features | Random store/ref numbers could act as row fingerprints | Replace identifier tokens with `<num>` | `test_normalizer_is_deterministic_and_strips_ids` | Medium |
| Selecting on the test set | Tuning to test inflates the reported number | Test read only in `finalize.py` after candidate frozen | `reports/model_gate.md` §6–§7 | High |
| Post-outcome / future fields | Would use information unavailable at posting time | Dataset has none — only the description exists at inference | data/README §2 | Low |

## 6. Preprocessing design and fit boundary

- **Steps:** `normalize_description` (stateless: extract debit/credit flag, lowercase, drop punctuation, replace identifier tokens with `<num>`, collapse whitespace) → TF-IDF word 1–2 grams (`min_df=2`, sublinear TF) → Logistic Regression.
- **Fit boundary (explicit):** every *learned* transformation — the TF-IDF vocabulary and IDF weights, and the model parameters — is fit on **training data only**. Validation and test are only `transform`-ed. `normalize_description` is deterministic and stateless, so it is leakage-safe regardless of split. Recorded in `reports/preprocessing_manifest.json`.
- **Reusability:** the same normalizer + fitted pipeline are reused unchanged at inference (`src/inference.py`), so training-time and serving-time preprocessing cannot drift.

## 7. Project-type notes (NLP)

- Text is short and templated; no empty descriptions remain after cleaning (verified).
- Out-of-vocabulary handling is a first-class concern: bag-of-words silently ignores unknown words, so inference adds an OOV guard that flags inputs with zero recognized merchant terms.

## 8. Data Gate status

- **Status: GREEN.** Source and license documented, EDA has written conclusions, issue log with decisions, split matches the real prediction setting and is boundary-verified by tests, leakage risks identified and controlled, preprocessing is reusable and fit on train only.
- **Named blocker:** none.
- **Owner:** project owner (FIN-001).
