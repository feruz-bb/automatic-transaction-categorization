# Data README — FIN-001 Transaction Categorization

## 1. Dataset identity and source

- **Dataset name:** US Bank Transaction Categories v2
- **Source URL / owner:** <https://huggingface.co/datasets/DoDataThings/us-bank-transaction-categories-v2> — Hugging Face, publisher `DoDataThings`.
- **Accessed on:** 2026-08-12.
- **Usage / license conditions:** MIT License. Free to use, modify and redistribute. Openly downloadable with **no authentication** — a deliberate selection criterion so any assessor can reproduce the project (a gated alternative, `mitulshah/transaction-categorization`, was rejected for requiring a login).
- **How to obtain the data:** run `python scripts/download_data.py`. It fetches `transactions-synthetic.csv` into `data/raw/` and verifies the row count. **No raw CSV is committed to Git** — see §3.

## 2. What the data represents

- **Unit of analysis:** one **bank transaction**, represented by its free-text description string.
- **Target:** `category` — one of **17** spending categories: Education, Entertainment, Fees, Groceries, Healthcare, Income, Insurance, Mortgage, Personal Care, Rent, Restaurants, Shopping, Subscription, Transfer, Transportation, Travel, Utilities.
- **Prediction / inference moment:** when a new transaction posts, the app has only the description string (with an optional debit/credit prefix). That is exactly the information available to the model — no post-hoc fields are used, so there is no temporal leakage.
- **Population / coverage:** US retail-banking-style transaction strings built from 500+ real merchant names in realistic debit/credit formats.

## 3. Files and paths

| File | Rows | Size | One row represents | Committed to Git? |
|---|---:|---:|---|---|
| `data/raw/transactions-synthetic.csv` | 68,000 | 3.3 MB | One transaction: `description` + `category` | **No** |
| `data/README.md` | — | — | This file | **Yes** |
| `data/_rejected_placeholder/Banking_Transactions_USA_2023_2024.csv` | 5,389 | 1.3 MB | The original placeholder dataset, **rejected** — see §4 | **No** |

### Columns

- `description` — the transaction string, e.g. `[debit] PUBLIX 7860 UNIVERSITY LN OAKLAND 94601-4574 CA USA`. Carries a `[debit]`/`[credit]` prefix, a merchant name, and often a store number, address, ZIP, and reference/PPD ID.
- `category` — the ground-truth spending category (the label).

### Key distributions (raw file)

- 68,000 rows, 2 columns, **0 nulls**.
- Categories are balanced: 4,000 rows each (17 categories).
- **22,298 exact-duplicate rows** and **5 label-ambiguous descriptions** (same text, two categories) — handled in cleaning (§ data_audit).
- Prefix split: 60,007 `debit` / 7,993 `credit`. `Income` is 100% credit; `Transfer` ~36% credit; all others are overwhelmingly debit.
- Description length (excluding prefix): median 3 tokens, 95th percentile 8, max 14 — short text.

## 4. Known limitations

These are the facts established by direct inspection on 2026-08-12. Each one that affects modeling also appears in the Data Gate issue log (`docs/data_audit.md`).

- **Synthetic-in-format, not real bank data.** Real transaction data is private; this dataset generates realistic *formats* around 500+ real merchant names with randomized store numbers, addresses and reference codes. Consequence: in-distribution accuracy is **optimistic**. The unseen-merchant evaluation slice (`reports/error_analysis/ERROR_ANALYSIS.md`) is the honest estimate of real-world degradation.
- **Heavy duplication (33%).** 22,298 of 68,000 rows are exact duplicates. Left in, identical strings would straddle the train/test boundary and inflate scores; cleaning de-duplicates to one row per unique description **before** splitting.
- **A few ambiguous labels.** 5 descriptions appear with two categories — unresolvable label noise; both sides are dropped.
- **Random per-transaction identifiers.** Store numbers, ZIP codes and PPD/reference IDs vary every transaction and carry no category signal; they are normalized to `<num>` so the model learns merchants, not noise.
- **Fixed taxonomy.** Only 17 categories exist; a transaction that fits none is forced into the nearest one (surfaced through low confidence at inference).
- **Coverage.** US-style retail banking merchants. Findings should not be presented as generalizing to other countries, business banking, or the present-day live merchant landscape.
- **No personal data.** No real account numbers, names, or PII are present; the model must not be presented as production-grade or as financial advice.

### Why the original placeholder was rejected

`data/_rejected_placeholder/Banking_Transactions_USA_2023_2024.csv` was the file initially in the project folder. It is synthetic with **randomly assigned labels**: 4,880 unique merchants in 5,389 rows, word-salad descriptions unrelated to the category, and a 50/50 `Fraud_Flag` (real fraud is <1%). A TF-IDF + LogReg model on it scores ~0.006 macro-F1 — no better than chance — so it cannot support the Modeling and Evaluation criteria. It is kept only to document the rejection.

## 5. Reproduction notes

1. `python scripts/download_data.py` — downloads and row-count-verifies `data/raw/transactions-synthetic.csv` (expects 68,000 rows).
2. Create the environment from the repository root:
   ```bash
   python3.10 -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   ```
3. `python -m src.experiments` rebuilds the split + experiment record; `python -m src.finalize` rebuilds the artifact and metrics. Neither the raw data nor the split is committed.
