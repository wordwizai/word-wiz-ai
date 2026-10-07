# Test Suite Structure

This folder contains all test cases for the phoneme assistant app. See each subfolder for details:

- `system/` — End-to-end system test cases (audio + sentence)
- `analysis/` — Analysis system test cases (extracted words/phonemes + sentence)
- `extraction/` — Extraction-only test cases (audio + sentence)
- `gpt/` — GPT prompt/response test cases (fully analyzed data)
- `regression/` — Scoring regression harness: determinism, client/server path agreement,
  and PER drift against pinned baselines
- `benchmark/` — Accuracy benchmark against expert labels from speechocean762 (precision-first
  word-level F0.5, with a paired acceptance rule)

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

## Accuracy benchmark

`benchmark/` scores the server pipeline against expert labels from speechocean762, a public
dataset of children and adults reading English. The regression harness tells you whether
numbers moved. The benchmark tells you whether they got better, using a paired comparison with
confidence intervals and a fixed acceptance rule.

```bash
# from backend/
PYTHONIOENCODING=utf-8 venv/Scripts/python.exe -m tests.benchmark.run --name candidate
PYTHONIOENCODING=utf-8 venv/Scripts/python.exe -m tests.benchmark.compare <baseline.json> <candidate.json>
```

Once its caches are built, a run replays recorded model outputs through the real production
scoring code, so it needs no network and no models. The cache is checked against a hash of the
exact model input, and a front-end change that would feed the models different audio stops the
run with exit code 3 and asks for a new cache. The dataset's test half is sealed behind an
unlock variable and a committed log.

Setup, every command, how the caches stay honest, the acceptance rule and an honest list of
limitations are in [`benchmark/README.md`](benchmark/README.md). A scoring change might be
worth running through both this and the regression harness before merging.
