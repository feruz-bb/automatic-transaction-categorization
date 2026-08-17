---
marp: true
theme: default
paginate: true
header: 'FIN-001 Capstone Defense — Automatic Transaction Categorization'
footer: 'IT Park / World Bank AI-ML Capstone • Scenario FIN-01'
style: |
  section {
    background-color: #0f172a;
    color: #f8fafc;
    font-family: 'Inter', sans-serif;
    padding: 40px 60px;
  }
  h1 { color: #f8fafc; font-size: 2.2em; }
  h2 { color: #38bdf8; font-size: 1.6em; border-bottom: 2px solid #334155; padding-bottom: 8px; }
  h3 { color: #10b981; font-size: 1.2em; }
  p, li { color: #cbd5e1; font-size: 1.05em; line-height: 1.5; }
  strong { color: #ffffff; }
  table { background-color: #1e293b; color: #f8fafc; border-collapse: collapse; width: 100%; font-size: 0.85em; }
  th { background-color: #334155; color: #38bdf8; padding: 10px; }
  td { border-bottom: 1px solid #334155; padding: 10px; }
  .highlight { color: #10b981; font-weight: bold; }
  .warning { color: #f59e0b; font-weight: bold; }
---

# FIN-001: Automatic Transaction Categorization
### Scalable NLP Multi-Class Classification for Digital Banking with Confidence Fallback

**IT Park / World Bank AI-ML Capstone • Scenario FIN-01**
Presenter: Defense Presentation | Format: 5-Minute Pitch

* **Test Macro-F1:** <span class="highlight">0.9961</span> (17 Balanced Spending Categories)
* **Unseen Merchant Slice F1:** <span class="warning">0.9784</span> (Honest Generalization)
* **Inference Footprint:** <span class="highlight">1.2 MB bundle</span> | <1ms latency | Dual-Guard Review Engine

---

## 1. Business Problem & ML Formulation *(Rubric 1 & 8)*

### ⚠️ The Problem
* Raw bank descriptions are noisy and cryptic (`[debit] PUBLIX 7860`, `MTG PMT PENFED CU`).
* Rule-based regex systems break down rapidly as new merchants and formats appear.
* Manual transaction tagging is slow, expensive, and fails to scale.

### 🎯 Machine Learning Formulation
* **Target User:** Digital banking app users & personal budgeting dashboards.
* **ML Task:** Supervised NLP multi-class text classification (17 categories).
* **Inference Input:** Raw transaction string + optional `[debit]`/`[credit]` flag.
* **Inference Output:** Predicted category, calibrated confidence, top-3 candidates, & `needs_review` flag.

---

## 2. Dataset & Zero-Leakage Pipeline *(Rubric 2 & 3)*

### 📦 Dataset Architecture (`DoDataThings/us-bank-transaction-categories-v2`)
* 68,000 raw rows across 17 balanced categories (MIT License, Hugging Face).
* **De-Duplication (DQ-01):** 22,298 exact duplicate rows (32.8%) dropped **before** splitting (reduced to 45,692 unique descriptions).
* **ID Normalization (DQ-03):** Store #s, ZIPs, and reference IDs converted to `<num>`.

### 🛡️ Leakage Controls & Boundaries
* **Stratified Split:** 70% Train (31,984), 15% Valid (6,854), 15% Protected Test (6,854).
* **Strict Fit Boundary:** TF-IDF vectorizer fit **strictly on Train** split.
* **Boundary Proof:** `tests/test_data_gate.py` asserts 0 description overlap across partitions.

---

## 3. Model Sweep & Key Empirical Finding *(Rubric 3 & 4)*

| Model Architecture | Feature Setup | Val Macro-F1 | Calibrated Proba | Decision |
|---|---|:---:|:---:|:---:|
| **Naive Dummy Classifier** | Most Frequent | 0.0094 | No | Baseline Floor |
| **TF-IDF + Logistic Regression** | Word 1–2 grams | **0.9960** | **Yes** | **SELECTED WINNER** |
| **TF-IDF + LinearSVC** | Char_wb 3–5 grams | 0.9971 | No | Rejected (No Proba) |
| **Sentence Transformers (MiniLM)**| 384-dim Embeddings | 0.9468 | Yes | Rejected (Worse & 40x Slow) |

### 💡 Why Bag-of-Words Beat Transformers
* Discriminative signal in short bank strings lives in specific tokens (`MTG PMT`, `DIR DEP`, `PUBLIX`).
* Dense embeddings blur exact token boundaries, lowering F1 to 0.9468 and adding 400MB dependencies.

---

## 4. Protected Test & Honest Generalization *(Rubric 4, 7 & 8)*

### 🏆 Protected Test Results (Scored ONCE on frozen model)
* **Test Macro-F1:** <span class="highlight">0.9961</span> (>100x lift over majority baseline)
* **Accuracy:** 99.55% | **Top-3 Accuracy:** 99.90% (n=6,854)
* **Per-Class Reliability:** High across all 17 categories (Shopping 0.984, Groceries 0.986).

### 🔍 The Honest Generalization Slice (Crucial Finding)
* **Unseen-Merchant Slice (n=716):** Test rows from merchants *never seen in training*.
* **Unseen Slice Macro-F1:** <span class="warning">0.9784</span> (~1.8% realistic drop).
* **Takeaway:** The 0.9784 slice is our true estimate for live bank feeds. Pure bag-of-words cannot infer novel merchants, making confidence fallback essential.

---

## 5. Live Showcase & Safety Engine *(Rubric 5 & 6)*

### ⚡ Production Architecture
* **Committed Artifact:** `artifacts/transaction_categorizer.joblib` (1.2 MB).
* **Zero-Data Serving:** Runs without raw data or re-training.
* **Dual-Guard Safety Engine:**
  1. *Confidence Guard:* Flags predictions with confidence < 0.50.
  2. *OOV Guard:* Flags inputs with 0 recognized merchant terms.

### 📱 Live Demo Interactive Routes
* **Route 1 (Known Transaction):** `"[debit] MTG PMT PENFED CU"` ➔ **Mortgage (97.4% conf)**.
* **Route 2 (Unfamiliar Transaction):** `"SOME UNFAMILIAR MERCHANT LLC"` ➔ **⚠️ Needs Review Flag**.

---

## 6. Limitations, Next Steps & Defense *(Rubric 7 & 8)*

### ⚖️ Responsible AI & Limitations
* Advisory spending classification; no PII exposure or real financial credentials.
* Unseen merchants trigger human review rather than silent errors.

### 🚀 Recommended Next Steps
* **Time-Based Splits:** Validate seasonality and temporal merchant drift.
* **Active Learning:** User corrections expand merchant dictionary over time.
* **LLM Cascade:** Fast TF-IDF for 95% + LLM fallback for novel edge cases.

### ✅ Capstone Status: **ALL GATES GREEN / LOCAL-VERIFIED**
* Questions & Mentor Discussion Welcome!
