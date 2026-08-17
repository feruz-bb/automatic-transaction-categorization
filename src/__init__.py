"""FIN-001 — Automatic Transaction Categorization.

Pipeline modules, in the order they run:

    features.py      text normalization + the feature contract (what the model sees)
    preprocessing.py load, clean, stratified train/valid/test split (fit boundary lives here)
    experiments.py   Model-Gate sweep: baseline -> TF-IDF models -> embedding run
    evaluate.py      metrics, per-class report, confusion matrix, unseen-merchant slice
    finalize.py      refit the frozen candidate, score the protected test set ONCE, save bundle
    inference.py     load artifacts/ and categorize one transaction (no refitting, no data/)

The deployed app (app.py) and smoke_test.py depend on inference.py ONLY.
"""

__version__ = "1.0.0"
