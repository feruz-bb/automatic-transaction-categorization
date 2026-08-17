# Error Analysis — FIN-001 Transaction Categorization

Model: `tfidf_word_logreg` (version 1.0.0). Numbers below are on the **protected test split** (n=6854), scored once after the candidate was frozen.

## 1. Headline

- Test macro-F1: **0.9961**, accuracy 0.9955, top-3 accuracy 0.999.
- Majority-class baseline macro-F1 was ~0.01, so the model is a large, real lift.

## 2. Generalization to unseen merchants (the brief's key question)

- 716 test transactions come from merchants that never appear in training.
- On those unseen merchants: macro-F1 **0.9784**, accuracy 0.9930.
- On previously-seen merchants: macro-F1 0.9962.
- The gap between these two numbers is the honest estimate of real-world degradation: templated in-vocabulary merchants are near-perfect; genuinely novel merchant strings are harder, which is where the char-n-gram model and the low-confidence fallback matter.

## 3. Weakest categories

| Category | Precision | Recall | F1 | Support |
|---|---:|---:|---:|---:|
| Healthcare | 0.984 | 0.984 | 0.984 | 381 |
| Shopping | 0.995 | 0.976 | 0.986 | 595 |
| Groceries | 0.983 | 0.989 | 0.986 | 536 |
| Subscription | 0.989 | 0.995 | 0.992 | 365 |
| Transfer | 0.993 | 1.000 | 0.997 | 431 |

## 4. Most common confusions (true → predicted)

| True | Predicted | Count |
|---|---|---:|
| Shopping | Healthcare | 5 |
| Shopping | Groceries | 4 |
| Healthcare | Groceries | 3 |
| Subscription | Groceries | 2 |
| Shopping | Subscription | 2 |
| Shopping | Personal Care | 2 |
| Healthcare | Shopping | 2 |
| Restaurants | Subscription | 1 |
| Shopping | Transfer | 1 |
| Restaurants | Transfer | 1 |

## 5. What this implies

- Confusions cluster where merchant text is genuinely ambiguous (e.g. a big-box store selling both Groceries and Shopping). These are inherent taxonomy overlaps, not model defects.
- The product mitigation is the confidence-based fallback: predictions below the 0.50 top-class probability are surfaced as 'needs review / uncertain' rather than auto-applied, exactly as the brief's ambiguous-case requirement asks.

