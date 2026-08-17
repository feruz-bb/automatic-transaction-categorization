# Responsible AI and Limitations — FIN-001

## What this model is, and is not

It is a prototype that categorizes a bank transaction into one of 17 spending categories
from its description text. It is **not** a production system, **not** financial advice, and
**not** a fraud or risk detector. Its output is a best-effort label to help a person or a
spending-summary feature, always subject to human review.

## Data ethics and privacy

- **No personal data.** The dataset (`DoDataThings/us-bank-transaction-categories-v2`, MIT)
  is synthetic-in-format: real account numbers, names, and PII do not appear. Real bank
  transaction data is private, which is exactly why a synthetic-format dataset is the
  responsible public choice.
- **Licensing.** MIT — free to use and redistribute with attribution (given in `README.md`
  and `data/README.md`). No scraping, no gated or unauthorized data.
- **No identifiers as features.** Store numbers, ZIPs, and reference/PPD IDs are normalized
  to `<num>` so the model cannot key on anything resembling an account fingerprint.

## Fairness and misuse

- Categories are spending *types*, not judgments about people; the model does not use or
  infer demographics.
- The taxonomy is fixed at 17 categories. A transaction that fits none is forced into the
  nearest one — surfaced as low confidence rather than silently mislabeled.
- Misuse guardrail: because output can be wrong (see below), it must not drive automated
  financial decisions without a human in the loop.

## Honest limitations

1. **Optimistic accuracy.** The data is templated around ~500 real merchants, so the headline
   test macro-F1 (0.9961) overstates real-world performance. The **unseen-merchant slice**
   (macro-F1 0.9784) is the honest generalization estimate; messy live bank feeds with novel
   merchants and typos would be harder still.
2. **Bag-of-words blindness.** A TF-IDF model silently ignores unknown words, so a genuinely
   novel merchant can produce a confident-looking but unreliable guess. Mitigation: the
   inference layer flags any input with **zero recognized merchant terms** (or top
   probability below 0.50) as "needs review" rather than auto-applying it.
3. **Category overlap.** Some merchants legitimately span categories (a big-box store is both
   Groceries and Shopping); these confusions are inherent to the taxonomy, not fixable by the
   model alone. Documented in `reports/error_analysis/ERROR_ANALYSIS.md`.
4. **Scope.** US-style retail banking merchants, a fixed 2023–2024-era merchant set. Not
   validated for other countries, business banking, or the current live merchant landscape.

## Recommended next steps

- Validate on a sample of real (consented, de-identified) transactions before any production
  use.
- Add an "Other / uncategorized" class and a human-review queue for low-confidence items.
- Periodically retrain as the merchant landscape drifts.
