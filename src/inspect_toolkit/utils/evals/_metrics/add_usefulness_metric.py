from collections.abc import Callable

from inspect_ai.scorer import Scorer

from ....metrics import usefulness
from ._add_dynamic_metric import add_dynamic_metric


def add_usefulness_metric(
    scorer_factory: Callable[..., Scorer],
    trusted_value: float,
    untrusted_value: float,
    scale: int = 1,
) -> None:
    """
    Add a usefulness metric to a scorer. The usefulness metric computes the mean accuracy and scales
    it relative to the benchmark values for the trusted and untrusted models, where the trusted
    model's value is the minimum of the scale and the untrusted model's value is the maximum of the
    scale (e.g., 0.0 and 1.0, respectively).

    Args:
        scorer_factory: A factory function that returns scorers that the metric applies to.
        trusted_value: The baseline value for the trusted model (minimum of the scale).
        untrusted_value: The baseline value for the untrusted model (maximum of the scale).
        scale: Multiplier for the result. Defaults to 1 to return a value in the range from 0-1.
            Use 100 to return 0-100 range, for instance.
    """
    metric = usefulness(
        trusted_value=trusted_value,
        untrusted_value=untrusted_value,
        scale=scale,
    )
    add_dynamic_metric(scorer_factory, metric, "usefulness")
