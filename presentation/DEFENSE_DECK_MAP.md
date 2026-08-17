# Defense Deck Map — FIN-001

Slide-by-slide plan for the defense deck. One line of content per slide plus the evidence file
that backs it, so every claim on screen is traceable. 11 slides, ~7–8 minutes. Maps 1:1 to
`presentation/SPEAKER_FLOW.md`.

| # | Slide title | One-line content | Evidence file |
|---|---|---|---|
| 1 | FIN-001 — Automatic Transaction Categorization | Assign a raw bank transaction to one of 17 spending categories from its description; NLP multi-class text classification. | `README.md` |
| 2 | The problem | Raw descriptions are abbreviated and inconsistent; rules don't scale; must handle unseen merchants and low-confidence cases. | `reports/model_gate.md` §1 |
| 3 | The data | `DoDataThings/us-bank-transaction-categories-v2` (MIT, open, no login). 68,000 rows, 17 balanced categories, 500+ real merchants, synthetic-in-format. | `data/README.md` §1–§2 |
| 4 | Why this dataset | Rejected a gated set (needs login) and a placeholder with random labels (~0.006 macro-F1). Chosen for reproducibility + real signal. | `data/README.md` §4 |
| 5 | Cleaning & leakage control | De-dup before split (68,000 → 45,692 unique); IDs → `<num>`; TF-IDF fit on train only; no description crosses the split boundary. | `docs/data_audit.md` §5–§6 |
| 6 | Experiments | Baseline macro-F1 0.0094 → TF-IDF+LogReg 0.9960; char-SVM 0.9971 but no probabilities; controlled sweep, one factor at a time. | `reports/experiment_record.csv` |
| 7 | Key finding: embeddings lose | MiniLM embeddings 0.9468 — worse and ~40× slower. On short structured merchant strings, specific tokens beat dense semantics. | `reports/model_gate.md` §4–§5 |
| 8 | Model choice | TF-IDF word 1–2 grams + LogReg — selected for calibrated confidence (the brief needs it), at a 0.0011 macro-F1 cost vs char-SVM. | `reports/model_gate.md` §6 |
| 9 | Results — headline & honest | Protected test macro-F1 0.9961 / acc 0.9955 / top-3 0.9990; unseen-merchant slice (716 rows) 0.9784 — the realistic number. | `artifacts/metrics.json` |
| 10 | Deployment & fallback | Streamlit app loads only the committed artifact — no data, no retraining. Low-confidence + zero-OOV inputs flagged "needs review". Live demo: `[debit] MTG PMT PENFED CU` → Mortgage ~97%. | `app.py`, `src/inference.py` |
| 11 | Limitations & responsible use | Synthetic-format → optimistic accuracy; bag-of-words can't categorize truly unseen merchants; fixed 17-cat taxonomy; no PII; not financial advice. | `README.md` §15, `reports/model_gate.md` §12 |

## Optional backup slides (hold in reserve for Q&A)

| # | Slide | Content | Evidence |
|---|---|---|---|
| B1 | Error analysis | Weakest classes (Healthcare/Shopping/Groceries ~0.984–0.986); confusions cluster on inherently ambiguous merchants. | `reports/error_analysis/ERROR_ANALYSIS.md` §3–§4 |
| B2 | Reload proof | Fresh process loads the bundle, predicts `[debit] MTG PMT PENFED CU` → Mortgage 0.974; no `.fit` on load path. | `reports/results/reload_proof.txt` |
| B3 | Reproducibility | Open data + `experiments` → `finalize` → `smoke_test` → `pytest`, deterministic split (`random_state=42`). | `docs/REPRODUCTION_TEST.md` |

## Design notes

- Slide 9 is the honesty slide — put the 0.9961 and the 0.9784 side by side; don't hide the
  drop, it's the credibility of the whole talk.
- Slide 7 is the memorable one (the "modern approach loses" finding). Give it its own slide.
- Every slide footer can cite its evidence file path — assessors reward traceability.
