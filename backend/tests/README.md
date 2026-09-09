# Test Suite Structure

This folder contains all test cases for the phoneme assistant app. See each subfolder for details:

- `system/` — End-to-end system test cases (audio + sentence)
- `analysis/` — Analysis system test cases (extracted words/phonemes + sentence)
- `extraction/` — Extraction-only test cases (audio + sentence)
- `gpt/` — GPT prompt/response test cases (fully analyzed data)
- `regression/` — Scoring regression harness: determinism, client/server path agreement,
  and PER drift against pinned baselines

See each subfolder's README for the required file formats and examples.

## Regression harness

`regression/` is the suite to run before merging anything that touches scoring. Unlike the
other folders it pins expected outputs, so it can tell an improvement from a regression.

```bash
# from backend/
PYTHONIOENCODING=utf-8 venv/Scripts/python.exe -m unittest tests.regression.test_regression -v
PYTHONIOENCODING=utf-8 venv/Scripts/python.exe -m tests.regression.run_regression
```

It needs no network and loads no models by default — cases carry a `fixture.json` with
recorded acoustic output — and it skips rather than fails when the environment cannot
support it. It also guards `core/model_registry.py`, the single place where every model id
and pinned revision is declared for both backend and frontend.

Full details, configuration and an honest list of what it does *not* cover:
[`regression/README.md`](regression/README.md).
