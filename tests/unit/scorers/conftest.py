import pytest
from inspect_ai.util import registry_info

from inspect_toolkit.scorers.composite import composite_scorer

SCORER_FACTORIES = [composite_scorer]


@pytest.fixture(autouse=True)
def restore_scorer_registry_metrics():
    """
    Snapshot and restore the registry metadata for scorer factories.

    Calling a scorer factory registers dynamic metrics by mutating the global registry entry for
    the factory (see `add_dynamic_metric`), so tests that construct scorers must not leak metrics
    into other tests.
    """
    snapshots = []
    for factory in SCORER_FACTORIES:
        info = registry_info(factory)
        snapshots.append(
            (
                info,
                list(info.metadata.get("metrics", [])),
                {
                    category: list(metrics)
                    for category, metrics in info.metadata.get("dynamic_metrics", {}).items()
                },
                "dynamic_metrics" in info.metadata,
            )
        )

    yield

    for info, metrics, dynamic_metrics, had_dynamic_metrics in snapshots:
        info.metadata["metrics"] = metrics
        if had_dynamic_metrics:
            info.metadata["dynamic_metrics"] = dynamic_metrics
        else:
            info.metadata.pop("dynamic_metrics", None)
