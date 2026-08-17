import sys
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.enum.shapes import MSO_SHAPE

def create_deck():
    prs = Presentation()
    # 16:9 widescreen layout
    prs.slide_width = Inches(13.333)
    prs.slide_height = Inches(7.5)

    # Color Palette (Modern Dark FinTech Theme)
    BG_COLOR = RGBColor(15, 23, 42)        # Deep Navy Slate (#0F172A)
    CARD_BG = RGBColor(30, 41, 59)        # Slate 800 (#1E293B)
    CARD_BORDER = RGBColor(51, 65, 85)    # Slate 700 (#334155)
    TEXT_WHITE = RGBColor(248, 250, 252)  # Slate 50 (#F8FAFC)
    TEXT_MUTED = RGBColor(148, 163, 184)  # Slate 400 (#94A3B8)
    TEXT_LIGHT = RGBColor(226, 232, 240)  # Slate 200 (#E2E8F0)
    ACCENT_CYAN = RGBColor(56, 189, 248)  # Cyan 400 (#38BDF8)
    ACCENT_GREEN = RGBColor(16, 185, 129) # Emerald 500 (#10B981)
    ACCENT_AMBER = RGBColor(245, 158, 11) # Amber 500 (#F59E0B)
    ACCENT_PURPLE = RGBColor(168, 85, 247)# Purple 500 (#A855F7)

    blank_layout = prs.slide_layouts[6] # Blank slide

    def set_background(slide):
        bg = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0, prs.slide_width, prs.slide_height)
        bg.fill.solid()
        bg.fill.fore_color.rgb = BG_COLOR
        bg.line.fill.background() # no line
        return bg

    def add_header(slide, title_text, category="FIN-001 CAPSTONE DEFENSE", rubric_tag=""):
        # Category / Tag
        tag_box = slide.shapes.add_textbox(Inches(0.8), Inches(0.45), Inches(10), Inches(0.3))
        tf_tag = tag_box.text_frame
        tf_tag.word_wrap = True
        tf_tag.margin_left = tf_tag.margin_top = tf_tag.margin_right = tf_tag.margin_bottom = 0
        p_tag = tf_tag.paragraphs[0]
        p_tag.text = category.upper()
        p_tag.font.size = Pt(11)
        p_tag.font.bold = True
        p_tag.font.color.rgb = ACCENT_CYAN

        # Title
        title_box = slide.shapes.add_textbox(Inches(0.8), Inches(0.75), Inches(9.5), Inches(0.7))
        tf_t = title_box.text_frame
        tf_t.word_wrap = True
        tf_t.margin_left = tf_t.margin_top = tf_t.margin_right = tf_t.margin_bottom = 0
        p_t = tf_t.paragraphs[0]
        p_t.text = title_text
        p_t.font.size = Pt(24)
        p_t.font.bold = True
        p_t.font.color.rgb = TEXT_WHITE

        # Rubric badge on top right
        if rubric_tag:
            rb_shape = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(10.5), Inches(0.55), Inches(2.0), Inches(0.45))
            rb_shape.fill.solid()
            rb_shape.fill.fore_color.rgb = CARD_BG
            rb_shape.line.color.rgb = ACCENT_CYAN
            rb_shape.line.width = Pt(1)
            tf_rb = rb_shape.text_frame
            tf_rb.vertical_anchor = MSO_ANCHOR.MIDDLE
            p_rb = tf_rb.paragraphs[0]
            p_rb.text = rubric_tag
            p_rb.alignment = PP_ALIGN.CENTER
            p_rb.font.size = Pt(11)
            p_rb.font.bold = True
            p_rb.font.color.rgb = ACCENT_CYAN

    def add_card(slide, left, top, width, height, title, items, badge="", accent=ACCENT_CYAN):
        shape = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(left), Inches(top), Inches(width), Inches(height))
        shape.fill.solid()
        shape.fill.fore_color.rgb = CARD_BG
        shape.line.color.rgb = CARD_BORDER
        shape.line.width = Pt(1)

        tf = shape.text_frame
        tf.word_wrap = True
        tf.margin_left = Inches(0.25)
        tf.margin_top = Inches(0.25)
        tf.margin_right = Inches(0.25)
        tf.margin_bottom = Inches(0.2)

        # Title
        p0 = tf.paragraphs[0]
        p0.text = title
        p0.font.size = Pt(16)
        p0.font.bold = True
        p0.font.color.rgb = accent
        p0.space_after = Pt(10)

        # Items
        for item in items:
            p = tf.add_paragraph()
            p.text = "• " + item if not item.startswith(" ") else item
            p.font.size = Pt(12)
            p.font.color.rgb = TEXT_LIGHT
            p.space_after = Pt(6)

        return shape

    # =========================================================================
    # SLIDE 1: Title Slide (Opening: 0:00 - 0:30)
    # =========================================================================
    s1 = prs.slides.add_slide(blank_layout)
    set_background(s1)

    # Accent decorative bar
    bar = s1.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(0.8), Inches(1.8), Inches(0.12), Inches(3.8))
    bar.fill.solid()
    bar.fill.fore_color.rgb = ACCENT_CYAN
    bar.line.fill.background()

    # Title & Subtitle box
    tbox = s1.shapes.add_textbox(Inches(1.2), Inches(1.8), Inches(11.0), Inches(3.8))
    tf = tbox.text_frame
    tf.word_wrap = True

    p0 = tf.paragraphs[0]
    p0.text = "FIN-001: AUTOMATIC TRANSACTION CATEGORIZATION"
    p0.font.size = Pt(32)
    p0.font.bold = True
    p0.font.color.rgb = TEXT_WHITE
    p0.space_after = Pt(12)

    p1 = tf.add_paragraph()
    p1.text = "Scalable NLP Multi-Class Categorization for Digital Banking with Confidence Fallback"
    p1.font.size = Pt(18)
    p1.font.color.rgb = ACCENT_CYAN
    p1.space_after = Pt(24)

    p2 = tf.add_paragraph()
    p2.text = "IT Park / World Bank AI-ML Capstone • Scenario FIN-01\nPresenter: Student Defense Presentation • Format: 5-Minute Pitch"
    p2.font.size = Pt(13)
    p2.font.color.rgb = TEXT_MUTED

    # Bottom metric cards preview
    c1 = s1.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(1.2), Inches(5.6), Inches(3.4), Inches(1.2))
    c1.fill.solid()
    c1.fill.fore_color.rgb = CARD_BG
    c1.line.color.rgb = CARD_BORDER
    tf_c1 = c1.text_frame
    tf_c1.margin_top = Inches(0.15)
    tf_c1.margin_left = Inches(0.2)
    p_c1_0 = tf_c1.paragraphs[0]
    p_c1_0.text = "0.9961"
    p_c1_0.font.size = Pt(22)
    p_c1_0.font.bold = True
    p_c1_0.font.color.rgb = ACCENT_GREEN
    p_c1_1 = tf_c1.add_paragraph()
    p_c1_1.text = "Protected Test Macro-F1 (17 Classes)"
    p_c1_1.font.size = Pt(11)
    p_c1_1.font.color.rgb = TEXT_MUTED

    c2 = s1.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(4.9), Inches(5.6), Inches(3.4), Inches(1.2))
    c2.fill.solid()
    c2.fill.fore_color.rgb = CARD_BG
    c2.line.color.rgb = CARD_BORDER
    tf_c2 = c2.text_frame
    tf_c2.margin_top = Inches(0.15)
    tf_c2.margin_left = Inches(0.2)
    p_c2_0 = tf_c2.paragraphs[0]
    p_c2_0.text = "0.9784"
    p_c2_0.font.size = Pt(22)
    p_c2_0.font.bold = True
    p_c2_0.font.color.rgb = ACCENT_AMBER
    p_c2_1 = tf_c2.add_paragraph()
    p_c2_1.text = "Unseen-Merchant Slice Macro-F1"
    p_c2_1.font.size = Pt(11)
    p_c2_1.font.color.rgb = TEXT_MUTED

    c3 = s1.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(8.6), Inches(5.6), Inches(3.8), Inches(1.2))
    c3.fill.solid()
    c3.fill.fore_color.rgb = CARD_BG
    c3.line.color.rgb = CARD_BORDER
    tf_c3 = c3.text_frame
    tf_c3.margin_top = Inches(0.15)
    tf_c3.margin_left = Inches(0.2)
    p_c3_0 = tf_c3.paragraphs[0]
    p_c3_0.text = "1.2 MB & <1ms"
    p_c3_0.font.size = Pt(22)
    p_c3_0.font.bold = True
    p_c3_0.font.color.rgb = ACCENT_CYAN
    p_c3_1 = tf_c3.add_paragraph()
    p_c3_1.text = "Lightweight Bundle + OOV Fallback"
    p_c3_1.font.size = Pt(11)
    p_c3_1.font.color.rgb = TEXT_MUTED

    s1.notes_slide.notes_text_frame.text = (
        "SPEAKER SCRIPT (0:00-0:30):\n"
        "\"Hello mentors, my name is [Your Name]. My project is FIN-001, scenario FIN-01: Automatic Transaction Categorization. "
        "The goal is to classify raw bank transaction text into 17 spending categories to power spending analytics in digital banking. "
        "Importantly, it is designed as an advisory tool with confidence guards—it surfaces ambiguous transactions for human review rather than making silent, incorrect auto-categorizations.\""
    )

    # =========================================================================
    # SLIDE 2: Business Problem & Target User (0:30 - 1:15)
    # =========================================================================
    s2 = prs.slides.add_slide(blank_layout)
    set_background(s2)
    add_header(s2, "Business Problem & ML Formulation", "Problem Discovery", "Rubric 1 & 8")

    add_card(s2, 0.8, 1.6, 3.6, 5.2, "The Real-World Problem", [
        "Digital banking apps display thousands of daily transactions.",
        "Descriptions are noisy, cryptic, & abbreviated (e.g. '[debit] PUBLIX 7860', 'MTG PMT PENFED CU').",
        "Rule-based regex tables break down rapidly as new merchants and formats appear.",
        "Manual tagging is costly, slow, and does not scale."
    ], accent=ACCENT_AMBER)

    add_card(s2, 4.8, 1.6, 3.6, 5.2, "User & ML Task Formulation", [
        "Primary User: Digital banking app users & personal finance analytics teams.",
        "ML Task: Supervised multi-class text classification.",
        "Input: Raw transaction description text string + optional [debit]/[credit] flag.",
        "Output: 1 of 17 discrete categories + calibrated confidence + top-3 alternatives.",
        "Safety Requirement: Ambiguous/OOV inputs flagged 'needs_review'."
    ], accent=ACCENT_CYAN)

    add_card(s2, 8.8, 1.6, 3.7, 5.2, "17-Category Balanced Taxonomy", [
        "Core Living: Groceries, Mortgage, Utilities, Gas/Automotive.",
        "Discretionary: Restaurants, Shopping, Entertainment, Travel.",
        "Financial: Income, Transfer, Fees, Financial Services, Subscriptions.",
        "Well-being: Healthcare, Education, Services, Charity.",
        "Equal Business Importance: Every category is critical to personal budgeting."
    ], accent=ACCENT_GREEN)

    s2.notes_slide.notes_text_frame.text = (
        "SPEAKER SCRIPT (0:30-1:15):\n"
        "\"Our primary user is a digital banking app user or personal finance analytics team. "
        "Inputs are noisy, abbreviated transaction strings like '[debit] PUBLIX 7860' or 'MTG PMT PENFED CU'. "
        "Rule-based regex systems fail to scale as thousands of new merchants appear. "
        "We formulate this as an NLP multi-class classification task over 17 balanced categories. "
        "The expected output is a predicted category, a calibrated confidence score, top-3 alternative categories, "
        "and a binary 'needs_review' flag for low-confidence or unfamiliar inputs.\""
    )

    # =========================================================================
    # SLIDE 3: Dataset & Leakage Control (1:15 - 1:45)
    # =========================================================================
    s3 = prs.slides.add_slide(blank_layout)
    set_background(s3)
    add_header(s3, "Dataset Provenance & Leakage-Proof Pipeline", "Data Gate", "Rubric 2 & 3")

    add_card(s3, 0.8, 1.6, 5.6, 5.2, "Dataset Architecture & Cleaning", [
        "Source: DoDataThings/us-bank-transaction-categories-v2 (Hugging Face, MIT License).",
        "Volume: 68,000 raw rows across 17 perfectly balanced categories.",
        "De-Duplication (DQ-01): 22,298 exact duplicate rows (32.8%) removed BEFORE splitting (reduced to 45,692 unique descriptions).",
        "Ambiguity Resolution (DQ-02): 5 descriptions with conflicting labels dropped.",
        "Identifier Normalization (DQ-03): Store #s, ZIPs, PPD IDs converted to <num>."
    ], accent=ACCENT_CYAN)

    add_card(s3, 6.8, 1.6, 5.7, 5.2, "Leakage Controls & Fit Boundary", [
        "Stratified Partition: 70% Train (31,984), 15% Valid (6,854), 15% Test (6,854).",
        "Strict Fit Boundary: TF-IDF vectorizer vocabulary & IDF weights fit ONLY on Train split.",
        "Zero Boundary Crossings: Verified via tests/test_data_gate.py — 0 identical descriptions appear across partitions.",
        "Protected Test Set: Held-out test split accessed exactly ONCE in src/finalize.py after candidate model freeze.",
        "Zero Post-Outcome Leakage: No balances, accounts, or future fields used."
    ], accent=ACCENT_GREEN)

    s3.notes_slide.notes_text_frame.text = (
        "SPEAKER SCRIPT (1:15-1:45):\n"
        "\"I used the public DoDataThings dataset (MIT license, 68,000 rows across 17 balanced categories). "
        "To prevent data leakage, I de-duplicated 22,298 exact duplicate rows BEFORE splitting, reducing to 45,692 unique descriptions. "
        "Store numbers and ZIPs were normalized to <num> so the model learns merchant semantics, not random numbers. "
        "The TF-IDF vectorizer was fit strictly on the train split, and automated unit tests verify that zero strings cross the split boundary.\""
    )

    # =========================================================================
    # SLIDE 4: Model Exploration & Key Finding (1:45 - 2:20)
    # =========================================================================
    s4 = prs.slides.add_slide(blank_layout)
    set_background(s4)
    add_header(s4, "Model Sweep & Key Empirical Finding", "Model Exploration", "Rubric 3 & 4")

    # Table comparing models
    table_shape = s4.shapes.add_table(5, 5, Inches(0.8), Inches(1.6), Inches(11.7), Inches(2.5))
    table = table_shape.table
    table.columns[0].width = Inches(3.2)
    table.columns[1].width = Inches(2.2)
    table.columns[2].width = Inches(1.8)
    table.columns[3].width = Inches(2.3)
    table.columns[4].width = Inches(2.2)

    headers = ["Model / Architecture", "Feature Setup", "Val Macro-F1", "Calibrated Proba", "Status"]
    for col_idx, h in enumerate(headers):
        cell = table.cell(0, col_idx)
        cell.fill.solid()
        cell.fill.fore_color.rgb = RGBColor(51, 65, 85)
        p = cell.text_frame.paragraphs[0]
        p.text = h
        p.font.bold = True
        p.font.size = Pt(12)
        p.font.color.rgb = TEXT_WHITE
        p.alignment = PP_ALIGN.CENTER

    data = [
        ["Naive Dummy Classifier", "Most Frequent", "0.0094", "No", "Baseline Floor"],
        ["TF-IDF + Logistic Regression", "Word 1-2 n-grams", "0.9960", "Yes (predict_proba)", "SELECTED WINNER"],
        ["TF-IDF + LinearSVC", "Char_wb 3-5 n-grams", "0.9971", "No (No Proba)", "Rejected (No Proba)"],
        ["Sentence Transformers (MiniLM)", "384-dim Embeddings", "0.9468", "Yes", "Rejected (Worse & 40x slow)"]
    ]

    for row_idx, row_data in enumerate(data):
        for col_idx, text in enumerate(row_data):
            cell = table.cell(row_idx + 1, col_idx)
            cell.fill.solid()
            cell.fill.fore_color.rgb = CARD_BG
            p = cell.text_frame.paragraphs[0]
            p.text = text
            p.font.size = Pt(11)
            if col_idx == 4 and "SELECTED" in text:
                p.font.color.rgb = ACCENT_GREEN
                p.font.bold = True
            elif col_idx == 4 and "Rejected" in text:
                p.font.color.rgb = ACCENT_AMBER
            elif col_idx == 2:
                p.font.bold = True
                p.font.color.rgb = ACCENT_CYAN
            else:
                p.font.color.rgb = TEXT_LIGHT
            if col_idx in [1, 2, 3, 4]:
                p.alignment = PP_ALIGN.CENTER

    add_card(s4, 0.8, 4.4, 11.7, 2.4, "Key Technical Finding: Why Bag-of-Words Beat Transformers", [
        "In short, structured financial strings, discriminative signal lives in specific lexical tokens ('MTG PMT', 'DIR DEP', 'PUBLIX').",
        "Dense semantic embeddings (MiniLM) blur these exact token boundaries, dropping macro-F1 to 0.9468.",
        "Logistic Regression provides calibrated probabilities (essential for confidence thresholds) at only 0.0011 F1 difference from SVM.",
        "Production Impact: 1.2 MB artifact, <1ms CPU inference, zero GPU requirement, perfectly suited for Streamlit Cloud."
    ], accent=ACCENT_CYAN)

    s4.notes_slide.notes_text_frame.text = (
        "SPEAKER SCRIPT (1:45-2:20):\n"
        "\"We established a naive baseline with Macro-F1 of 0.0094. "
        "TF-IDF word 1–2 n-grams with Logistic Regression achieved 0.9960 on validation. "
        "A char-SVM scored slightly higher at 0.9971, but produces no probabilities, which are required for our confidence threshold fallback. "
        "Crucially, MiniLM sentence embeddings scored lower at 0.9468 and ran 40x slower because dense embeddings blur specific tokens like 'MTG PMT'. "
        "This empirical finding justified shipping the lightweight 1.2MB TF-IDF + LogReg pipeline.\""
    )

    # =========================================================================
    # SLIDE 5: Results & Honest Generalization (2:20 - 3:10)
    # =========================================================================
    s5 = prs.slides.add_slide(blank_layout)
    set_background(s5)
    add_header(s5, "Test Results & Honest Generalization Slice", "Model Evaluation", "Rubric 4, 7 & 8")

    add_card(s5, 0.8, 1.6, 5.6, 5.2, "Protected Test Evaluation (Scored Once)", [
        "Candidate frozen on validation, evaluated ONCE on test (n=6,854):",
        "  • Test Macro-F1: 0.9961",
        "  • Test Accuracy: 0.9955",
        "  • Test Top-3 Accuracy: 0.9990",
        "Lift over Majority Baseline: >100x improvement.",
        "Per-Class Performance: High F1 across all 17 classes (lowest: Shopping @ 0.984, Groceries @ 0.986).",
        "Top Confusion: Big-box retailers shared across Groceries and Shopping (mitigated by top-3 candidates)."
    ], accent=ACCENT_GREEN)

    add_card(s5, 6.8, 1.6, 5.7, 5.2, "The Honest Generalization Slice (Crucial Insight)", [
        "Synthetic format data produces optimistic in-distribution scores.",
        "Unseen-Merchant Test Slice (n=716 rows from merchants NEVER present in training set):",
        "  • Unseen Slice Macro-F1: 0.9784 (vs 0.9962 on seen)",
        "  • ~1.8% Realistic Drop: The honest estimate of production degradation on novel live bank feeds.",
        "Mitigation Strategy: Sparse bag-of-words cannot guess novel merchants, so our inference engine includes an OOV terms check that triggers 'needs_review'."
    ], accent=ACCENT_AMBER)

    s5.notes_slide.notes_text_frame.text = (
        "SPEAKER SCRIPT (2:20-3:10):\n"
        "\"The candidate was frozen and scored ONCE on the protected test set, achieving a Macro-F1 of 0.9961 and top-3 accuracy of 0.9990. "
        "However, because synthetic datasets can be optimistic, I evaluated an unseen-merchant test slice of 716 rows whose merchants never appeared in training. "
        "The Macro-F1 dropped by ~1.8% to 0.9784. This slice is our honest generalization metric for live bank feeds. "
        "The main limitation is that bag-of-words cannot semantically interpret completely novel merchant names, which is why our confidence fallback is critical.\""
    )

    # =========================================================================
    # SLIDE 6: Live Showcase & Inference System (3:10 - 4:20)
    # =========================================================================
    s6 = prs.slides.add_slide(blank_layout)
    set_background(s6)
    add_header(s6, "Inference Architecture & Live Demo Route", "Showcase & Deployment", "Rubric 5 & 6")

    add_card(s6, 0.8, 1.6, 5.6, 5.2, "Production Inference Architecture", [
        "Self-Contained Artifact: artifacts/transaction_categorizer.joblib (1.2 MB).",
        "Zero-Data Inference: Loads only the bundle — no data dependencies, no training code.",
        "Dual-Guard Safety Engine (src/inference.py):",
        "  1. Confidence Guard: Flags predictions where top confidence < 0.50.",
        "  2. OOV Guard: Flags inputs with 0 recognized merchant vocabulary terms.",
        "Automated Verification: 16/16 pytest suite (test_app.py, test_data_gate.py, test_inference.py)."
    ], accent=ACCENT_CYAN)

    add_card(s6, 6.8, 1.6, 5.7, 5.2, "Live Demo Interactive Route", [
        "Live Interface: Streamlit Web App (app.py).",
        "Route 1: High-Confidence Known Transaction:",
        "  • Input: '[debit] MTG PMT PENFED CU'",
        "  • Result: Mortgage (Confidence: 97.4%, Top-3 shown).",
        "Route 2: Ambiguous / Novel Transaction:",
        "  • Input: 'SOME UNFAMILIAR MERCHANT LLC'",
        "  • Result: 'needs_review' Flag Triggered (Zero recognized terms).",
        "Advisory Safety: Prevents silent miscategorization in customer budgets."
    ], accent=ACCENT_GREEN)

    s6.notes_slide.notes_text_frame.text = (
        "SPEAKER SCRIPT (3:10-4:20):\n"
        "\"Let's see the live system in action. The Streamlit app loads directly from the committed model bundle without re-training. "
        "First, I enter a standard transaction: '[debit] MTG PMT PENFED CU'. The model predicts Mortgage with 97.4% confidence and shows top-3 alternatives. "
        "Now, if I input an unrecognized merchant like 'SOME UNFAMILIAR MERCHANT LLC', the zero-OOV term guard kicks in, returning a 'needs_review' flag with low confidence. "
        "This directly satisfies our business safety requirement.\""
    )

    # =========================================================================
    # SLIDE 7: Limitations, Next Steps & Conclusion (4:20 - 5:00)
    # =========================================================================
    s7 = prs.slides.add_slide(blank_layout)
    set_background(s7)
    add_header(s7, "Limitations, Responsible AI & Next Steps", "Finalization & Defense", "Rubric 7 & 8")

    add_card(s7, 0.8, 1.6, 3.6, 5.2, "Known Limitations", [
        "Synthetic Formatting: Real bank data has higher abbreviation variability.",
        "Fixed Taxonomy: Fixed to 17 categories; unlisted spending mapped to nearest class.",
        "Lexical Sparsity: Pure bag-of-words flags unknown merchants but cannot infer novel semantics.",
        "No PII: Model does not process real card numbers or private credentials."
    ], accent=ACCENT_AMBER)

    add_card(s7, 4.8, 1.6, 3.6, 5.2, "Recommended Next Steps", [
        "Time-Based Splits: Test on temporal transaction streams across seasons.",
        "Active Learning Feedback: User corrections feed back to expand merchant vocabulary.",
        "Hybrid Cascade: Lightweight TF-IDF for 95% high-confidence transactions + LLM fallback for OOV cases.",
        "Sub-Category Taxonomy: Expanding to hierarchal merchant tagging."
    ], accent=ACCENT_CYAN)

    add_card(s7, 8.8, 1.6, 3.7, 5.2, "Capstone Deliverables Complete", [
        "Gates C2-C4: GREEN (Data & Model gates).",
        "Gate C5: LOCAL-VERIFIED (Streamlit app + smoke test pass).",
        "Gate C6: GREEN (Evidence matrix, reproduction guide, defense pack).",
        "Artifact Size: 1.2 MB bundle.",
        "Reproducibility: 100% reproducible via scripts."
    ], accent=ACCENT_GREEN)

    s7.notes_slide.notes_text_frame.text = (
        "SPEAKER SCRIPT (4:20-5:00):\n"
        "\"In summary, we built a lightweight (~1.2MB), highly accurate categorization service with built-in safety fallbacks. "
        "For next steps, I recommend testing time-based splits and creating an active-learning feedback loop. "
        "The entire pipeline and all gates are 100% reproducible from the repository. "
        "Thank you, and I am now ready for your questions.\""
    )

    # =========================================================================
    # SLIDE 8: Backup Slide - Defense Q&A Bank
    # =========================================================================
    s8 = prs.slides.add_slide(blank_layout)
    set_background(s8)
    add_header(s8, "Mentor Q&A Defense Bank (Backup)", "Evidence Reference", "Rubric 8")

    add_card(s8, 0.8, 1.6, 3.6, 5.2, "Q1: Why Logistic Regression?", [
        "Delivers strong validation Macro-F1 (0.9960).",
        "Provides calibrated probabilities (predict_proba) required for confidence thresholds.",
        "MiniLM embeddings scored lower (0.9468) and added 400MB dependencies.",
        "LinearSVC scored 0.9971 but has no probability calibration."
    ], accent=ACCENT_CYAN)

    add_card(s8, 4.8, 1.6, 3.6, 5.2, "Q2: Zero Data Leakage Proof?", [
        "22,298 exact duplicates dropped BEFORE splitting.",
        "TF-IDF vectorizer fit strictly on Train split.",
        "tests/test_data_gate.py explicitly asserts 0 shared descriptions across splits.",
        "Protected test set accessed once in src/finalize.py."
    ], accent=ACCENT_GREEN)

    add_card(s8, 8.8, 1.6, 3.7, 5.2, "Q3: Handling Unseen Merchants?", [
        "Unseen-merchant test slice (n=716) achieved 0.9784 Macro-F1.",
        "Dual guard in src/inference.py checks for recognized terms.",
        "Inputs with zero recognized vocabulary terms trigger a 'needs_review' flag.",
        "Prevents false confident predictions."
    ], accent=ACCENT_AMBER)

    s8.notes_slide.notes_text_frame.text = (
        "BACKUP SLIDE NOTES (Q&A Anchor):\n"
        "Use this slide if mentors ask for deep technical justification regarding model choice, data leakage controls, or unseen merchant handling."
    )

    output_path = "presentation/FIN_001_Capstone_Presentation.pptx"
    prs.save(output_path)
    print(f"Presentation saved successfully to {output_path}")

if __name__ == "__main__":
    create_deck()
