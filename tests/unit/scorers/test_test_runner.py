from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from inspect_ai.scorer import CORRECT, INCORRECT, NOANSWER, Target
from inspect_ai.solver import TaskState
from inspect_ai.util import registry_info

from inspect_toolkit.scorers.test_runner import (
    all_tests_pass_scorer,
    percent_failing_tests_scorer,
    percent_passing_tests_scorer,
    test_runner_scorer,
)


def registered_name(scorer) -> str:
    """Return the bare (unqualified) registry name of a scorer instance."""
    return registry_info(scorer).name.rsplit("/", 1)[-1]


def make_state(metadata: dict | None = None) -> TaskState:
    state = MagicMock(spec=TaskState)
    state.metadata = metadata or {}
    return state


class TestScorerNames:
    """Each named scorer registers under its own name."""

    def test_each_scorer_registers_its_own_name(self):
        assert registered_name(all_tests_pass_scorer) == "all_tests_pass"
        assert registered_name(percent_passing_tests_scorer) == "percent_passing_tests"
        assert registered_name(percent_failing_tests_scorer) == "percent_failing_tests"


class TestTestRunnerDispatcher:
    """The `test_runner_scorer` dispatcher returns the scorer for a scoring method."""

    def test_dispatches_to_the_named_scorer(self):
        assert registered_name(test_runner_scorer("pass-fail")) == "all_tests_pass"
        assert registered_name(test_runner_scorer("percent-pass")) == "percent_passing_tests"
        assert registered_name(test_runner_scorer("percent-fail")) == "percent_failing_tests"

    def test_defaults_to_percent_pass(self):
        assert registered_name(test_runner_scorer()) == "percent_passing_tests"

    def test_invalid_scoring_method_raises(self):
        with pytest.raises(ValueError, match="Invalid scoring method"):
            test_runner_scorer("nonsense")  # type: ignore[arg-type]

    def test_is_not_collected_as_a_test(self):
        assert test_runner_scorer.__test__ is False


class TestScoring:
    """The scorers turn a `run_tests` result into a Score."""

    @pytest.mark.asyncio
    @patch("inspect_toolkit.scorers.test_runner.run_tests", new_callable=AsyncMock)
    async def test_pass_fail_success(self, mock_run_tests):
        mock_run_tests.return_value = {"status": "success"}
        score = await all_tests_pass_scorer()(make_state(), Target(""))
        assert score.value == CORRECT

    @pytest.mark.asyncio
    @patch("inspect_toolkit.scorers.test_runner.run_tests", new_callable=AsyncMock)
    async def test_pass_fail_failure(self, mock_run_tests):
        mock_run_tests.return_value = {"status": "failure"}
        score = await all_tests_pass_scorer()(make_state(), Target(""))
        assert score.value == INCORRECT

    @pytest.mark.asyncio
    @patch("inspect_toolkit.scorers.test_runner.run_tests", new_callable=AsyncMock)
    async def test_percent_passing(self, mock_run_tests):
        mock_run_tests.return_value = {"counts": {"pass": 3, "total": 4}}
        score = await percent_passing_tests_scorer()(make_state(), Target(""))
        assert score.value == 75.0

    @pytest.mark.asyncio
    @patch("inspect_toolkit.scorers.test_runner.run_tests", new_callable=AsyncMock)
    async def test_percent_failing(self, mock_run_tests):
        mock_run_tests.return_value = {"counts": {"pass": 3, "total": 4}}
        score = await percent_failing_tests_scorer()(make_state(), Target(""))
        assert score.value == 25.0

    @pytest.mark.asyncio
    @patch("inspect_toolkit.scorers.test_runner.run_tests", new_callable=AsyncMock)
    async def test_percent_passing_no_tests_scores_zero(self, mock_run_tests):
        mock_run_tests.return_value = {"counts": {"pass": 0, "total": 0}}
        score = await percent_passing_tests_scorer()(make_state(), Target(""))
        assert score.value == 0

    @pytest.mark.asyncio
    @patch("inspect_toolkit.scorers.test_runner.run_tests", new_callable=AsyncMock)
    async def test_error_scores_noanswer(self, mock_run_tests):
        mock_run_tests.side_effect = RuntimeError("boom")
        score = await percent_passing_tests_scorer()(make_state(), Target(""))
        assert score.value == NOANSWER
        assert "boom" in score.metadata["error"]
