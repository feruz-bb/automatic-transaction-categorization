# PRESENTATION DECK, PITCH SCRIPT & AI GENERATION PROMPTS — FIN-001

> **Scenario:** FIN-01 — Automatic Transaction Categorization  
> **Format:** 5-Minute Pitch Deck aligned with `EXTC4_Demo_Pitch_Examples.docx` & IT Park Capstone Rubric Criteria 1–8.

---

## 🎯 Part 1: AI Slide Generator Prompts (Gamma.app / Canva / Marp / ChatGPT)

You can copy and paste the prompt below into **Gamma.app**, **ChatGPT (for PowerPoint/Marp)**, or **Canva AI** to automatically build your presentation slides.

```text
Create a modern, clean, 7-slide pitch deck (16:9 aspect ratio) for an AI/ML Capstone Project titled "FIN-001: Automatic Transaction Categorization". Use a dark fintech color theme (navy blue, slate gray, accent green for metrics, coral accent for low-confidence flags).

Slide 1: Title & Opening
- Title: FIN-001 — Automatic Transaction Categorization
- Subtitle: Scalable Machine Learning for Digital Banking & Spending Analytics
- Presenter: [Your Name] | Capstone Scenario FIN-01
- Key Message: Classifies raw bank transaction text into 17 spending categories with a confidence-based human review fallback.

Slide 2: Business Problem & Target User
- Target User: Digital Banking Users & Personal Finance Analytics Teams.
- The Problem: Raw descriptions (e.g., "[debit] PUBLIX 7860", "MTG PMT PENFED CU") are noisy, abbreviated, and inconsistent.
- Rule-based systems fail to scale as new merchants and store formats appear.
- Solution Objective: Automate multi-class NLP categorization while surfacing ambiguous or unrecognized transactions for human review rather than misclassifying them.

Slide 3: Dataset & Leakage-Safe Pipeline
- Data Source: DoDataThings/us-bank-transaction-categories-v2 (Hugging Face, MIT License, 68,000 rows, 17 balanced categories).
- Preprocessing & Cleaning:
  1. De-duplication: 22,298 exact duplicates removed BEFORE splitting (68,000 → 45,692 unique descriptions).
  2. ID Normalization: Store #s, ZIPs, PPD IDs normalized to <num> to prevent row fingerprinting.
  3. Fit Boundary: Vectorizer fit strictly on Train split (70/15/15 stratified split); Zero description overlap across splits.

Slide 4: Model Exploration & Key Finding
- Baseline: Naive Majority Class (sklearn.DummyClassifier) → Macro-F1: 0.0094
- Candidates Evaluated on Validation Set:
  1. TF-IDF + Logistic Regression (Selected Candidate): Validation Macro-F1 = 0.9960 | Calibrated Probabilities (Required for confidence thresholding).
  2. TF-IDF + LinearSVC: Macro-F1 = 0.9971 (No probability calibration).
  3. Sentence Transformers (MiniLM Embeddings + LogReg): Macro-F1 = 0.9468 (~40x slower, heavier dependency).
- Key Technical Finding: Sparse n-gram tokens (e.g. "MTG PMT") outperform dense semantic embeddings on short structured financial strings, keeping deployment lightweight (~1.2MB).

Slide 5: Evaluation & Honest Generalization
- Protected Test Performance (Scored ONCE on frozen model):
  - Held-out Test Macro-F1: 0.9961 | Accuracy: 0.9955 | Top-3 Accuracy: 0.9990
- Honest Generalization (Unseen-Merchant Slice):
  - Test transactions from merchants NEVER seen in training (n=716): Macro-F1 = 0.9784 (~1.8% drop).
  - Demonstrates realistic performance degradation on novel live bank feeds.
- Failure Analysis & Limitations: Overlap in multi-category merchants (Groceries vs. Shopping) and sparse bag-of-words limitations on novel OOV terms.

Slide 6: Live Showcase & System Architecture
- Interface: Streamlit Web App loading committed joblib bundle (artifacts/transaction_categorizer.joblib).
- Live Demo Route:
  1. Known Input: "[debit] MTG PMT PENFED CU" → Mortgage (Confidence: ~97.4%, Top-3 options).
  2. Ambiguous/Unseen Input: "SOME UNFAMILIAR MERCHANT LLC" → Triggers "needs_review" flag (Confidence < 0.50 or zero recognized terms).
- Security & Safety: No PII exposed, lightweight footprint, reproducible pipeline.

Slide 7: Next Steps & Q&A
- Future Enhancements: Time-based split evaluation & active learning feedback loop for novel merchants.
- Statement: "Everything presented is fully reproducible from the repository. I am ready for your questions."
```

---

## ⏱️ Part 2: 5-Minute Pitch Script & Timed Flow (Aligned with EXTC4 Pitch Guide)

| Time | Block / Section | What to Say (Speaker Script) | What to Show (Visual Anchor) | Rubric Criteria |
|---|---|---|---|---|
| **0:00–0:30** | **1. Opening & Core Goal** | *"Hello mentors, my name is [Your Name]. My project is FIN-001, scenario FIN-01: Automatic Transaction Categorization. The goal of this system is to classify raw bank transaction text into 17 spending categories to help digital banking users track their spending. Importantly, it is designed as an advisory tool with confidence guards—it surfaces ambiguous transactions for human review rather than making silent, incorrect auto-categorizations."* | Slide 1 (Title) & [`README.md`](file:///Users/uzmacbook/MyStuff/For_Developer/IT_PARK_AI-ML/08_capstone/FIN-001-project/README.md) | **Criterion 1 & 8** |
| **0:30–1:15** | **2. User & ML Problem** | *"Our primary user is a digital banking app user or personal finance analytics team. Inputs are noisy, abbreviated transaction strings like `[debit] PUBLIX 7860` or `MTG PMT PENFED CU`. Rule-based regex systems fail to scale as thousands of new merchants appear. We formulate this as an NLP multi-class classification task. The expected output is a predicted category, a calibrated confidence score, top-3 alternative categories, and a binary `needs_review` flag for low-confidence predictions."* | Slide 2 & [`docs/PROJECT_BRIEF.md`](file:///Users/uzmacbook/MyStuff/For_Developer/IT_PARK_AI-ML/08_capstone/FIN-001-project/docs/PROJECT_BRIEF.md) | **Criterion 1 & 8** |
| **1:15–2:10** | **3. Data & Methodology** | *"I used the public `DoDataThings/us-bank-transaction-categories-v2` dataset (MIT license, 68,000 rows across 17 balanced categories). To prevent data leakage, I de-duplicated 22,298 exact duplicate rows BEFORE splitting, reducing to 45,692 unique descriptions. Store numbers and ZIPs were normalized to `<num>`. I established a naive majority-class baseline with a Macro-F1 of 0.0094. For modeling, I trained TF-IDF word 1–2 n-grams with Logistic Regression, which achieved a validation Macro-F1 of 0.9960. Interestingly, MiniLM sentence embeddings scored lower at 0.9468 because dense embeddings blur specific financial tokens like `MTG PMT`."* | Slide 3–4 & [`docs/data_audit.md`](file:///Users/uzmacbook/MyStuff/For_Developer/IT_PARK_AI-ML/08_capstone/FIN-001-project/docs/data_audit.md) | **Criterion 2 & 3** |
| **2:10–3:10** | **4. Results & Weakness** | *"Candidate selection was driven strictly by validation performance. The final candidate was frozen and scored ONCE on the protected test set, achieving a held-out Macro-F1 of 0.9961. However, because synthetic datasets can be optimistic, I evaluated an unseen-merchant test slice (716 rows from merchants never seen in training). The F1 score dropped by ~1.8% to 0.9784. This slice represents the honest generalization estimate. The main limitation is that bag-of-words models cannot semantically interpret completely novel merchant names, which is why confidence safeguards are essential."* | Slide 5 & [`reports/model_gate.md`](file:///Users/uzmacbook/MyStuff/For_Developer/IT_PARK_AI-ML/08_capstone/FIN-001-project/reports/model_gate.md) | **Criterion 4, 7 & 8** |
| **3:10–4:20** | **5. Live Demo Showcase** | *"Let's see the live system in action. The Streamlit app loads directly from the committed model bundle without re-training. First, I enter a standard transaction: `[debit] MTG PMT PENFED CU`. The model predicts `Mortgage` with 97.4% confidence and shows top-3 alternatives. Now, if I input an unrecognized merchant like `SOME UNFAMILIAR MERCHANT LLC`, the zero-OOV term guard kicks in, returning a `needs_review` flag with low confidence. This fulfills our business safety requirement."* | Live App (`streamlit run app.py`) or Slide 6 | **Criterion 5, 6 & 8** |
| **4:20–5:00** | **6. Conclusion & Q&A** | *"In summary, we built a lightweight (~1.2MB), highly accurate categorization service with built-in safety fallbacks. For next steps, I plan to explore time-based validation splits and active-learning human feedback. The pipeline is 100% reproducible from the repository. Thank you, and I am now ready for your questions."* | Slide 7 & [`PROJECT_STATUS.md`](file:///Users/uzmacbook/MyStuff/For_Developer/IT_PARK_AI-ML/08_capstone/FIN-001-project/PROJECT_STATUS.md) | **Criterion 8** |

---

## 💡 Part 3: Evidence-Anchored Q&A Cheat Sheet (For Mentor Defense)

If mentors ask questions during Q&A, use these exact evidence-backed answers:

1. **Q: Why did you choose Logistic Regression over Random Forest or Transformers?**
   - *Answer:* "Logistic Regression provided a strong validation Macro-F1 of 0.9960 while producing well-calibrated probabilities (`predict_proba`), which are mandatory for our confidence threshold fallback. Sentence embeddings scored lower (0.9468) and added ~400MB dependencies. See `reports/model_gate.md` §4–5."

2. **Q: How did you ensure no data leakage occurred between Train and Test?**
   - *Answer:* "First, we de-duplicated 22,298 exact duplicate rows before making the stratified 70/15/15 split. Second, the TF-IDF vectorizer was fit exclusively on the train split. Automated tests (`tests/test_data_gate.py`) explicitly verify that zero transaction strings appear in more than one partition."

3. **Q: How does your model handle an unseen merchant that wasn't in training data?**
   - *Answer:* "We evaluated an unseen-merchant test slice of 716 rows, achieving 0.9784 Macro-F1. For completely novel strings, our `src/inference.py` engine checks for recognized vocabulary terms and flags inputs with zero recognized terms as `needs_review`."
