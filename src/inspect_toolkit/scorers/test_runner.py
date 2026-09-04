import logging
from collections.abc import Callable
from pathlib import Path
from typing import Literal

from inspect_ai.scorer import (
    CORRECT,
    INCORRECT,
    NOANSWER,
    Score,
    Scorer,
    Target,
    mean,
    scorer,
    stderr,
)
from inspect_ai.solver import TaskState

from ..metrics import threshold_accuracy
from ..utils.coding import run_tests

logger = logging.getLogger(__name__)

ScoringMethod = Literal["pass-fail", "percent-pass", "percent-fail"]

# Maps a scoring method to the registered name of its scorer.
scorer_names: dict[str, str] = {
    "pass-fail": "all_tests_pass",
    "percent-pass": "percent_passing_tests",
    "percent-fail": "percent_failing_tests",
}


def _make_test_runner(scoring_method: str) -> Scorer:
    """
    Build the score function shared by every test-runner scorer: run the repository's tests and turn
    the result into a Score.

    The repository language is read from `state.metadata["repo_language"]`, defaulting to `python`.
    """

    async def score(state: TaskState, target: Target) -> Score | None:
        try:
            repo_language = state.metadata.get("repo_language", "python")
            logger.info(f"Running tests for {repo_language} repository")

            test_result = await run_tests(repo_language, Path("/workspace"))

            if scoring_method == "pass-fail":
                if test_result.get("status") == "success":
                    logger.info("Tests passed successfully")
                    return Score(
                        value=CORRECT,
                        explanation="Tests passed successfully",
                        metadata={"scorer": "test_runner", "test_result": test_result},
                    )

                logger.warning(f"Tests failed with status: {test_result.get('status')}")
                if "test_errors" in test_result:
                    logger.warning(f"Test errors: {test_result['test_errors']}")

                return Score(
                    value=INCORRECT,
                    explanation="Tests failed",
                    metadata={
                        "scorer": "test_runner",
                        "scoring_method": scoring_method,
                        "test_result": test_result,
                    },
                )

            counts = test_result.get("counts", {})
            pass_count = counts.get("pass", 0)
            total_count = counts.get("total", 0)
            percentage_pass = (pass_count / total_count) * 100 if total_count > 0 else 0

            if scoring_method == "percent-pass":
                value = percentage_pass
                explanation = f"{pass_count} tests passed out of {total_count} total tests"
            else:  # percent-fail
                value = 100.0 - percentage_pass
                fail_count = total_count - pass_count
                explanation = f"{fail_count} tests failed out of {total_count} total tests"

            return Score(
                value=round(value, 2),
                explanation=explanation,
                metadata={
                    "scorer": "test_runner",
                    "scoring_method": scoring_method,
                    "test_result": test_result,
                },
            )

        except Exception as e:
            logger.error(f"Error running tests: {e}")
            return Score(
                value=NOANSWER,
                explanation="Error running tests",
                metadata={
                    "scorer": "test_runner",
                    "scoring_method": scoring_method,
                    "error": str(e),
                },
            )

    return score


@scorer(name="all_tests_pass", metrics=[mean(), stderr()])
def all_tests_pass_scorer() -> Scorer:
    """Score `CORRECT` if the repository's tests all pass, `INCORRECT` otherwise."""
    return _make_test_runner("pass-fail")


@scorer(
    name="percent_passing_tests",
    metrics=[mean(), stderr(), threshold_accuracy(threshold=100, inclusive=True, scale=100)],
)
def percent_passing_tests_scorer() -> Scorer:
    """Score the percentage of the repository's tests that passed."""
    return _make_test_runner("percent-pass")


@scorer(
    name="percent_failing_tests",
    metrics=[mean(), stderr(), threshold_accuracy(threshold=0, inclusive=False, scale=100)],
)
def percent_failing_tests_scorer() -> Scorer:
    """Score the percentage of the repository's tests that failed."""
    return _make_test_runner("percent-fail")


_scorer_factories: dict[str, Callable[[], Scorer]] = {
    "pass-fail": all_tests_pass_scorer,
    "percent-pass": percent_passing_tests_scorer,
    "percent-fail": percent_failing_tests_scorer,
}


def test_runner_scorer(scoring_method: ScoringMethod = "percent-pass") -> Scorer:
    """
    Convenience dispatcher that returns one of the test-runner scorers by scoring method.

    Callers that need to attach dynamic (e.g. config-driven) metrics should import and use the
    specific scorer directly, since metrics attach to the named factory.

    Args:
        scoring_method: The method to use for scoring the tests.

    Returns:
        The scorer corresponding to `scoring_method`.
    """
    try:
        factory = _scorer_factories[scoring_method]
    except KeyError:
        raise ValueError(f"Invalid scoring method: {scoring_method}") from None

    return factory()


# `test_runner_scorer` begins with `test_`, so pytest would collect it as a test when a consumer
# imports it into a test module. Mark it as not-a-test so the name stays import-safe in any suite.
test_runner_scorer.__test__ = False  # type: ignore[attr-defined]
