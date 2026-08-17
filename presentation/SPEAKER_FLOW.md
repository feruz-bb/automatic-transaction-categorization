# Speaker Flow — FIN-001 Defense Talk Track (~7–8 min)

A timed track for the defense. Each section says what to **SAY** and what to **SHOW**.
Numbers are the real ones from `artifacts/metrics.json` and `reports/model_gate.md`. Keep it
honest — the strongest move in this project is admitting where the score is optimistic.

Total budget: ~7:30. Live demo is ~1:00 of that; if the clock is tight, cut the experiments
detail (§5) before cutting the demo or the honesty (§6, §8).

---

## 0. Opening — 0:20

- **SAY:** "FIN-001, scenario FIN-01: automatic transaction categorization. Given a raw bank
  transaction description, assign it to one of 17 spending categories. It's an NLP
  multi-class text classification problem, and it ships as a small Streamlit app."
- **SHOW:** `README.md` (top block) or the title slide.

## 1. Problem — 0:45

- **SAY:** "A banking app shows users their spending, but raw descriptions are abbreviated
  and inconsistent — `MTG PMT PENFED CU`, `PUBLIX 7860 UNIVERSITY LN`. Hand-written rules
  don't scale as new merchants and formats appear. The brief asks for an ML solution that
  categorizes from the description alone and handles two hard cases: unseen merchants and
  low-confidence transactions."
- **SHOW:** `reports/model_gate.md` §1 (task, raw input, model output).

## 2. Data — 1:00

- **SAY:** "Public dataset — `DoDataThings/us-bank-transaction-categories-v2`, MIT-licensed,
  open with no login, so any assessor can reproduce it. 68,000 rows, 17 balanced categories,
  built from 500+ real merchant names. It's synthetic-in-format: real formats around real
  merchants, but not real private bank data — which matters for how I read the results."
- **SHOW:** `data/README.md` §1–§2, then the audit table in `docs/data_audit.md` §2.

## 3. Why this dataset — 0:30

- **SAY:** "I deliberately rejected two alternatives: a gated Hugging Face set that needs a
  login, and a placeholder CSV that had randomly-assigned labels — a model on it scored
  ~0.006 macro-F1, no better than chance. Reproducibility and real signal were the selection
  criteria."
- **SHOW:** `data/README.md` §4 ("Why the original placeholder was rejected").

## 4. Preprocessing & leakage control — 1:00

- **SAY:** "Three things had to be right before any modeling. One: 33% of rows — 22,298 — are
  exact duplicates, so I de-duplicate to one row per unique description *before* the split;
  68,000 rows become 45,692 unique. Two: store numbers, ZIPs and reference IDs are replaced
  with `<num>` so the model learns merchants, not random per-transaction codes. Three: the
  TF-IDF vocabulary is fit on the training split only; validation and test are only
  transformed. A test asserts no description crosses the split boundary."
- **SHOW:** `docs/data_audit.md` §5 (leakage table) and §6 (fit boundary), or
  `tests/test_data_gate.py`.

## 5. Experiments & the embedding finding — 1:15

- **SAY:** "Baseline first — most-frequent class, macro-F1 0.0094. Then a controlled sweep,
  same split and metric for every run. TF-IDF word 1–2 grams plus Logistic Regression scored
  0.9960 on validation. A char-n-gram SVM scored marginally higher, 0.9971, but it produces
  no probabilities. And the interesting negative result: MiniLM sentence embeddings — the
  'modern' choice — scored only 0.9468, worse and about 40× slower. On short structured
  merchant strings the signal *is* specific tokens like `MTG PMT` or `DIR DEP`; dense
  embeddings blur exactly those distinctions. That's why I ship classic TF-IDF."
- **SHOW:** `reports/experiment_record.csv` (sorted by validation macro-F1) and
  `reports/model_gate.md` §4–§5.

## 6. Results & the honest number — 1:00

- **SAY:** "Candidate frozen on validation, then scored **once** on the protected test set:
  macro-F1 0.9961, accuracy 0.9955, top-3 accuracy 0.9990. That headline number is
  optimistic because the data is templated around a fixed merchant set. So I report the
  honest number too: a slice of 716 test transactions from merchants *never seen in
  training* scores macro-F1 0.9784 — about 1.8 points lower. That gap is my real estimate of
  how this degrades on novel live merchants."
- **SHOW:** `artifacts/metrics.json` (the three blocks: `test`, `test_seen_merchants`,
  `test_unseen_merchants`) and `reports/error_analysis/ERROR_ANALYSIS.md` §2.

## 7. Live demo — 1:00

- **SAY:** "Same frozen artifact, served through Streamlit — it loads only
  `artifacts/transaction_categorizer.joblib`, no data, no retraining." Then type the
  known-good input: **`[debit] MTG PMT PENFED CU`** → **Mortgage, ~97% confidence**, with the
  top-3 shown. Then type **`SOME UNFAMILIAR MERCHANT LLC`** → it comes back **"needs review"**.
  "Zero recognized merchant terms, so the OOV guard flags it instead of guessing — that's the
  low-confidence fallback the brief asked for."
- **SHOW:** the running app (`streamlit run app.py`). If it fails, switch to
  `presentation/FALLBACK_EVIDENCE.md`.

## 8. Limitations & close — 0:40

- **SAY:** "Honest limits: synthetic-format data means the in-distribution score is
  optimistic — the unseen-merchant slice is the number to trust. Bag-of-words can't correctly
  categorize a truly novel merchant; it can only flag it. The taxonomy is fixed at 17
  categories, so a transaction fitting none is forced to the nearest and surfaced as
  low-confidence. It uses no PII and is not financial advice. Everything I've shown is
  reproducible from the committed artifact. Happy to take questions."
- **SHOW:** `README.md` §15 (Responsible use) or `reports/model_gate.md` §12.

---

### Timing cheat-sheet

| § | Section | Cum. |
|---|---|---|
| 0 | Opening | 0:20 |
| 1 | Problem | 1:05 |
| 2 | Data | 2:05 |
| 3 | Why this dataset | 2:35 |
| 4 | Preprocessing & leakage | 3:35 |
| 5 | Experiments & embedding finding | 4:50 |
| 6 | Results & honest number | 5:50 |
| 7 | Live demo | 6:50 |
| 8 | Limitations & close | 7:30 |
