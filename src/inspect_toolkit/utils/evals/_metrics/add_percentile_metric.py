from collections.abc import Callable, Sequence
from typing import Literal

from inspect_ai.scorer import Scorer

from ....metrics.percentile import PercentileDerivatives, PercentileMethod, percentile
from ._add_dynamic_metric import add_dynamic_metric


def add_percentile_metric(
    scorer_factory: Callable[..., Scorer],
    target: float,
    type: Literal["percentile", "cutoff"] = "percentile",
    derivatives: Sequence[PercentileDerivatives] = (),
    method: PercentileMethod = "linear",
) -> None:
    """
    Add a percentile metric to a scorer.

    Args:
        scorer_factory: A factory function that returns scorers that the metric applies to.
        target: The target percentile or cutoff between 0 and 100 (e.g., 80 for 80th percentile or
            1 for 1% cutoff).
        type: Whether to calculate a percentile or a cutoff threshold. Defaults to "percentile".
        derivatives: List of additional metrics to calculate along with the target percentile or
            cutoff threshold. Defaults to an empty list.
        method: The method to use for calculating the percentile or cutoff threshold. Defaults to
            "linear".
    """
    metric = percentile(
        target=target,
        type=type,
        derivatives=derivatives,
        method=method,
    )
    add_dynamic_metric(scorer_factory, metric, "percentile")
