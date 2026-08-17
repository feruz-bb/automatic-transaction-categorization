# Project Brief — FIN-01 Automatic Transaction Categorization

This is the completed FIN-01 field brief: the two planning tables the scenario requires
before implementation, plus the problem framing (rubric criterion 1).

## Client problem (from the FIN-01 scenario)

A digital-banking app displays thousands of transactions with raw, inconsistent merchant
descriptions. Users want spending summaries, but manual categorization does not scale and
rule-based systems become unmaintainable as new merchants and formats appear. The client
wants an ML solution that assigns an incoming transaction to a meaningful spending category
from its description and any suitable non-sensitive metadata.

## Data & Problem Discovery

| Decision / Question | Response |
|---|---|
| Selected dataset and source | `DoDataThings/us-bank-transaction-categories-v2` (Hugging Face, MIT license, openly downloadable). See `data/README.md`. |
| What does one record represent? | One bank transaction: a description string + its spending `category` (the label). |
| Proposed target / ML objective | Multi-class text classification into 17 spending categories (Groceries, Restaurants, Mortgage, Income, Utilities, …). |
| Key info available at inference time | The transaction description only (with an optional `[debit]`/`[credit]` prefix) — exactly what posts with a live transaction. No post-outcome fields. |
| Main data quality issues | 22,298 exact-duplicate rows (33%), 5 label-ambiguous descriptions, pervasive random identifiers (store #, ZIP, PPD/ref IDs) in the text. Handled in `docs/data_audit.md` (DQ-01…DQ-03). |
| Potential leakage risks | Duplicate strings across the split; fitting TF-IDF on all data; per-transaction IDs acting as row fingerprints; tuning on the test set. Controls in `docs/data_audit.md` §5. |
| Privacy / fairness / licensing | MIT-licensed, synthetic-in-format, no real PII. Model is best-effort, not financial advice. See `docs/RESPONSIBLE_AI_AND_LIMITATIONS.md`. |

## Technical Proposal

| Decision / Question | Response |
|---|---|
| ML problem formulation | Supervised multi-class classification of short merchant text into 17 categories. |
| Proposed baseline | Most-frequent-class (`DummyClassifier`) — validation macro-F1 0.009, the floor to beat. |
| Main modeling approach(es) | TF-IDF (word 1–2 grams) + Logistic Regression (deployed); compared against char-n-gram + LinearSVC and MiniLM sentence-embeddings + LogReg. See `reports/model_gate.md`. |
| Data splitting / validation strategy | Stratified train/valid/test = 70/15/15, `random_state=42`, on de-duplicated unique descriptions. Select on validation; test read once in `finalize.py`. |
| Primary evaluation metric | Macro-F1 (17 roughly balanced classes, all matter equally). Accuracy + top-3 accuracy as support. |
| Expected inference input | One transaction description string. |
| Expected inference output | A category label + confidence + top-3 alternatives + an `is_uncertain` review flag. |
| Main technical risks / assumptions | Synthetic-format data → optimistic accuracy (mitigated by the unseen-merchant slice); bag-of-words cannot categorize truly novel merchants (mitigated by the OOV/low-confidence fallback); fixed taxonomy. |

## Functional requirements coverage

- Accepts a new transaction description and returns a spending category — `src/inference.py:categorize`, `app.py`.
- Taxonomy is clearly defined (17 categories) and user/analytics-suitable — `data/README.md` §2.
- Handles previously unseen merchants reasonably — unseen-merchant slice evaluated; low-confidence fallback surfaces novel inputs — `reports/error_analysis/ERROR_ANALYSIS.md`.
- Ambiguous / low-confidence cases considered — confidence threshold (0.50) + zero-recognized-term OOV guard flag "needs review".
- No real credentials / card numbers / PII exposed — synthetic-format data, no PII.
