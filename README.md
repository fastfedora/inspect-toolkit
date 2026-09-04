# Inspect Toolkit

Reusable building blocks for [Inspect AI](https://inspect.aisi.org.uk/) evaluations: metrics,
scorers, solvers, tools, dataset sources, and sandbox helpers that are useful to anyone using
Inspect, independent of any particular config system or agent framework.

`inspect-toolkit` was extracted from the
[refactor-arena](https://github.com/fastfedora/refactor-arena) evaluation setting so its generic
pieces can be shared. It depends on `inspect-ai`, `numpy`, and `pyyaml`, plus `gitpython` (used
only by the sandbox git-diff helpers vendored from Control Arena).

## Installation

```sh
uv add inspect-toolkit        # or: pip install inspect-toolkit
```

Requires Python 3.12+.

## Subsystems at a glance

| Area | Import | What's there |
|---|---|---|
| Metrics | `inspect_toolkit.metrics` | `percentile`, `safety`, `usefulness`, `threshold_accuracy`, `undefined_result` |
| Dynamic metrics | `inspect_toolkit.utils.evals` | attach metrics to a scorer after the fact |
| Scorers | `inspect_toolkit.scorers` | composite, test-runner, file-contents, sandbox-state |
| Solvers | `inspect_toolkit.solvers` | `setup_repo`, `run_tests` |
| Tools | `inspect_toolkit.tools` | `DeferredAgentTool`, `run_scorer` / `ScorerInfo` |
| Dataset sources | `inspect_toolkit.datasets.sources` | pluggable local + GitHub dataset sources |
| Fixtures | `inspect_toolkit.fixtures` | `FixtureManager` for Docker sandbox templates |
| Database diffing | `inspect_toolkit.utils.databases` | SQLite diffing + a MongoDB-like selector language |
| Sandbox helpers | `inspect_toolkit.utils.sandbox` | within-sandbox copy / file checks |
| Coding helpers | `inspect_toolkit.utils.coding` | language-dispatched repo setup + test running |
| Message helpers | `inspect_toolkit.utils.evals` | strip reasoning / named tool calls from messages |

## Metrics

Pure `@metric` implementations you can pass to any Inspect `@scorer`:

```python
from inspect_ai.scorer import mean, scorer, stderr
from inspect_toolkit.metrics import percentile, threshold_accuracy

@scorer(metrics=[mean(), stderr(), percentile(target=95), threshold_accuracy(threshold=80)])
def my_scorer():
    ...
```

- `percentile(target, type="percentile"|"cutoff", derivatives=(), method="linear")`—percentile or
  cutoff over a score distribution, with optional derivative metrics (coverage, error, tie counts).
- `threshold_accuracy(threshold, inclusive=True, scale=100)`—fraction of scores at/above a
  threshold.
- `usefulness(trusted_value, untrusted_value, scale=1)`—rescales the mean relative to trusted and
  untrusted baselines.
- `safety(...)`—safety metric with four variants (`SafetyMetricVariant`) plus audit-budget forms.
- `undefined_result()`—counts samples whose score is undefined.

## Dynamic metrics

Sometimes the metrics a scorer needs aren't known until runtime (e.g. driven by config). Because a
scorer's metrics resolve from a mutable list shared between the `@scorer` factory and its instances,
you can attach metrics to the factory before constructing it:

```python
from inspect_ai.scorer import mean, scorer
from inspect_toolkit.utils.evals import add_percentile_metric

@scorer(metrics=[mean()])
def my_scorer():
    ...

add_percentile_metric(my_scorer, target=99, type="cutoff")   # attaches to the factory
scorer_instance = my_scorer()
```

`add_dynamic_metric` / `get_dynamic_metrics` are the low-level primitives; `add_percentile_metric`
and `add_usefulness_metric` are convenience helpers built on top of them.

## Scorers

```python
from inspect_toolkit.scorers import (
    composite_scorer,
    file_contents_scorer,
    sandbox_state_scorer,
    test_runner_scorer,
)

# Combine scorers with a string or callable formula
composite = composite_scorer(
    scorers=[git_diff_monitor(), full_trajectory_monitor()],
    formula="git_diff_monitor.value + full_trajectory_monitor.value",
)

# Run the repository's test suite (dispatched by state.metadata["repo_language"], default "python")
tests = test_runner_scorer("percent-pass")   # or the named all_tests_pass_scorer, etc.

# Search files in the sandbox for a string
contains = file_contents_scorer(folder_path="/workspace/src", search_string="TODO",
                                file_extensions=[".py"])

# Score by the exit code of a sandbox command
exists = sandbox_state_scorer(command="test -f /workspace/app/config.yaml")
```

The test-runner is also exposed as three named module-level scorers—`all_tests_pass_scorer`,
`percent_passing_tests_scorer`, `percent_failing_tests_scorer`—with `test_runner_scorer` as a
convenience dispatcher over them.

## Solvers

Thin `Solver` wrappers over the coding helpers, driven by `state.metadata["repo_language"]`:

```python
from inspect_toolkit.solvers import run_tests, setup_repo

plan = [setup_repo(workspace_path="/workspace"), run_tests()]
```

## Tools

- `DeferredAgentTool`—a tool factory whose construction is deferred until a `TaskState` exists.
- `run_scorer(scorers, state, default_max_calls=None)`—builds a tool that lets an agent score
  itself mid-trajectory, with per-scorer call limits. Each scorer is described by a `ScorerInfo`
  (`name`, `scorer`, `description`, optional `max_calls`).

```python
from inspect_toolkit.tools import ScorerInfo, run_scorer

tool = run_scorer(
    scorers=[ScorerInfo(name="tests", scorer=test_runner_scorer(), description="Run the tests")],
    state=state,
)
```

## Dataset sources

Pluggable dataset sources with GitHub sparse-checkout caching:

```python
from inspect_toolkit.datasets.sources import resolve_source

source = resolve_source("<github-url-or-local-path>")   # -> DatasetSource
dataset_path = source.resolve("my_dataset")             # downloads/caches as needed
```

`resolve_source` accepts GitHub URLs, `github://` specs, or local paths and returns a
`DatasetSource` (`GitHubDatasetSource` / `LocalDatasetSource`). `get_cache_path` computes the cache
location; the cache root defaults to a `datasets/` directory at the project root and is overridable.

## Fixtures

`FixtureManager` builds Docker sandbox specifications from templates with feature flags and `#{var}`
secret injection. It takes a `templates_dir` and an image-name prefix, so it isn't tied to any
particular project layout.

## Database diffing

Pure-stdlib SQLite diffing plus a MongoDB-like selector language for asserting on diffs:

```python
from inspect_toolkit.utils.databases import diff_sqlite_databases, matches_diff

diff = diff_sqlite_databases(before_path, after_path)
assert matches_diff(diff, {"users": {"$inserted": {"name": "alice"}}})
```

`diff_filesystem_databases` and `diff_database_diffs` (diff-of-diffs) round out the set.

## Sandbox helpers

Within-sandbox operations (no host transfer involved):

```python
from inspect_toolkit.utils.sandbox import copy_dir_in_sandbox, file_exists_in_sandbox

if await file_exists_in_sandbox("/workspace/app/config.yaml"):
    ...
```

## Coding helpers

Language-dispatched repository setup and test running inside a sandbox (Python, JavaScript,
TypeScript, Java, Go). These are the async functions the solvers wrap:

```python
from inspect_toolkit.utils.coding import run_tests, setup_repo

await setup_repo("python", repo_path)      # install dependencies in the sandbox
result = await run_tests("python", workspace_path)   # -> {"status": ..., "counts": {...}}
```

## Message helpers

Generic `inspect_ai` message transforms, useful when building monitor prompts:

```python
from inspect_toolkit.utils.evals import (
    filter_reasoning_from_messages,
    filter_tool_calls_from_messages,
)

messages = filter_reasoning_from_messages(messages)             # drop ContentReasoning
messages = filter_tool_calls_from_messages(messages, exclude=["submit"])   # drop named tool calls
```

## Development

```sh
uv sync
just test    # or: uv run pytest
just lint    # ruff + pyright
```

## License

MIT
