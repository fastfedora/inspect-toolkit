from collections.abc import Callable

from inspect_ai.scorer import Metric, Scorer
from inspect_ai.util import registry_info


def _metric_name(metric: Metric) -> str | None:
    """Return a metric's registered name, or None if it isn't a registry object."""
    try:
        return registry_info(metric).name
    except Exception:
        return None


def add_dynamic_metric(
    scorer_factory: Callable[..., Scorer],
    metric: Metric,
    category: str | None = None,
) -> None:
    """
    Add a dynamic metric to a scorer.

    Adding is idempotent by metric name: if a metric with the same registered name is already
    attached to the factory, it is not added again. Metric names are derived from their parameters,
    so a name collision means the same metric. This makes it safe to attach metrics from within a
    scorer factory that may be invoked more than once, since the factory's metric list is shared
    across every scorer it builds.

    Args:
        scorer_factory: A factory function that returns scorers that the metric applies to.
        metric: The metric to add.
        category: The category of the metric. Defaults to the module name of the metric.
    """
    if category is None:
        category = metric.__module__.split(".")[-1]

    info = registry_info(scorer_factory)
    metrics = info.metadata["metrics"]

    name = _metric_name(metric)
    if name is not None and any(_metric_name(existing) == name for existing in metrics):
        return

    metrics.append(metric)
    info.metadata.setdefault("dynamic_metrics", {}).setdefault(category, []).append(metric)
