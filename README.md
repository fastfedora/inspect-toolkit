# Inspect Toolkit

Reusable building blocks for [Inspect AI](https://inspect.aisi.org.uk/) evaluations: metrics,
scorers, solvers, tools, dataset sources, and sandbox helpers that are useful to anyone using
Inspect, independent of any particular config system or agent framework.

Features include:

- Metrics for score distributions, threshold accuracy, and AI control safety and usefulness, usable
  with any scorer
- Scorers for running a repository's tests, searching sandbox files, checking sandbox state and
  asserting on database changes
- Solvers for repo setup, test running, snapshots, code and database diffs, and eval export/import
- Tools that defer construction until task state exists, and that let an agent score itself
  mid-trajectory
- Pluggable local and GitHub dataset sources with sparse-checkout caching
- A `FixtureManager` and a ready-to-use default Docker sandbox with composable features
- SQLite diffing with a MongoDB-like selector language for asserting on database changes

It depends only on `inspect-ai`, `numpy` and `pyyaml` (plus `gitpython`, used by the git-diff
helpers vendored from Control Arena), and was extracted from the
[refactor-arena](https://github.com/fastfedora/refactor-arena) evaluation setting.

## Documentation

Full documentation, including a user guide and API reference, is available at
[fastfedora.github.io/inspect-toolkit](https://fastfedora.github.io/inspect-toolkit/).

## Install

```bash
pip install inspect-toolkit
```

Requires Python 3.12+.

## Quick Start

Everything is a plain Inspect component: pass the metrics to any `@scorer`, and drop the scorers,
solvers and tools into a `Task`.

```python
from inspect_ai.scorer import mean, scorer, stderr
from inspect_toolkit.metrics import percentile, threshold_accuracy
from inspect_toolkit.scorers import test_runner_scorer

@scorer(metrics=[mean(), stderr(), percentile(target=95), threshold_accuracy(threshold=80)])
def my_scorer():
    ...

tests = test_runner_scorer("percent-pass")   # run the repo's test suite in the sandbox
```

See the [documentation](https://fastfedora.github.io/inspect-toolkit/) for the full guide and API
reference.

## Development

```bash
uv sync
just test      # run the test suite
just lint      # ruff + pyright
just docs      # preview the docs (Quarto)
```

## License

MIT License. See [LICENSE](LICENSE).
