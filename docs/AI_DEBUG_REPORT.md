# AI Debug Report — FIN-001

- **Date/time:** 2026-08-12 (afternoon, local).
- **Project behavior investigated:** the documented main entry point / user flow —
  `streamlit run app.py`, the transaction-categorization demo (rubric criterion 5,
  End-to-End Implementation & Delivery).

## Problem and root cause

The Streamlit app read `bundle['test_macro_f1']` directly at module load
(`app.py`, header line). That key is written by `src/finalize.py`, but it is **not** part
of the bundle contract validated by `src/inference.py:load_bundle` — whose `REQUIRED_KEYS`
are `{pipeline, classes, target, model_version, low_confidence_threshold}`.

Consequence: a bundle that `load_bundle()` accepts as *valid* can still lack
`test_macro_f1`, and the app then crashes with `KeyError` on startup. Because the unit tests
only exercised the `src.inference` library and nothing exercised `app.py`, this failure path
was invisible — `pytest` stayed fully green while the actual demo could break.

## Files changed

- `app.py` — one line: `bundle['test_macro_f1']` → `bundle.get('test_macro_f1', '—')`.
  (`model_version` and `classes` on the same line are left as direct reads because they
  *are* in the validated contract.)

## Automated checks created

- `tests/test_app.py` (new) — three tests using Streamlit's built-in `AppTest` harness
  (already in the pinned `streamlit==1.61.1`; no new dependency, no server, no network,
  uses the committed artifact only):
  1. `test_app_renders_known_good_prediction` — normal flow renders a category (Mortgage).
  2. `test_app_handles_empty_input_without_crashing` — empty input → warning, no crash.
  3. `test_app_survives_contract_valid_bundle_missing_metric` — the regression test: a
     bundle that `load_bundle` accepts but lacks `test_macro_f1` must not crash the app.

## Commands executed

```bash
python -m pytest tests/test_app.py -v      # targeted check
python -m pytest -q                        # full suite
python smoke_test.py                       # inference smoke test
streamlit run app.py                       # live entry point (health check)
```

## Real before/after results

| Check | Before fix | After fix |
|---|---|---|
| `pytest tests/test_app.py` | **1 failed**, 2 passed (`KeyError: 'test_macro_f1'` at `app.py:53`) | **3 passed** |
| `pytest -q` (full suite) | 13 passed (app path untested) | **16 passed** |
| `smoke_test.py` | PASSED | PASSED |
| `streamlit run app.py` | HTTP 200 with a complete bundle; KeyError with an incomplete one | HTTP 200; tolerant of a metric-less bundle |

## Remaining limitations / unverified areas

- Minimal fix chosen. A deeper option (not taken, to keep scope narrow): add
  `test_macro_f1` to `REQUIRED_KEYS` so `load_bundle` rejects incomplete bundles up front.
- `test_app.py` covers render, empty input, and the bundle-contract edge; it does not
  assert every widget branch (e.g. the "How the model saw this input" expander, each preset).
- The model was not retrained; train/validation/test separation is unchanged.

## Plain-language explanation of the fix

The app showed a small "test macro-F1" figure in its header, taken from the saved model
file. That figure is an optional extra — the code that checks a model file is valid does not
require it. So a valid model without that figure would make the whole app fall over before
it drew anything. The fix makes the app ask for that figure *politely*: if it is there, show
it; if not, show a dash and carry on. The new automated test opens the app the way a user
would, clicks Categorize, and confirms it both works normally and no longer crashes on a
valid-but-slimmer model file.
