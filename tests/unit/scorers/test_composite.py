import logging
from unittest.mock import MagicMock

import pytest
from inspect_ai.scorer import NOANSWER, Score, Scorer, Target, mean, scorer
from inspect_ai.solver import TaskState

from inspect_toolkit.scorers.composite import _get_scorer_name, composite_scorer


@scorer(name="alpha_stub", metrics=[mean()])
def alpha_stub(value: float = 2.0) -> Scorer:
    async def score(state: TaskState, target: Target) -> Score:
        return Score(value=value)

    return score


@scorer(name="beta_stub", metrics=[mean()])
def beta_stub(value: float = 3.0) -> Scorer:
    async def score(state: TaskState, target: Target) -> Score:
        return Score(value=value)

    return score


@scorer(name="raising_stub", metrics=[mean()])
def raising_stub() -> Scorer:
    async def score(state: TaskState, target: Target) -> Score:
        raise RuntimeError("scorer failed")

    return score


def make_state(scores: dict[str, Score] | None = None) -> TaskState:
    state = MagicMock(spec=TaskState)
    state.scores = scores
    return state


class TestCompositeScorer:
    @pytest.mark.asyncio
    async def test_string_formula_combines_scores(self):
        score_fn = composite_scorer(
            scorers=[alpha_stub(2.0), beta_stub(3.0)],
            formula="alpha_stub.value + beta_stub.value",
        )

        score = await score_fn(make_state(), Target(""))

        assert score.value == 5.0
        assert score.explanation == "Composite score computed from 2 scorer(s)"
        assert score.metadata["formula"] == "alpha_stub.value + beta_stub.value"
        assert set(score.metadata["scores"].keys()) == {"alpha_stub", "beta_stub"}

    @pytest.mark.asyncio
    async def test_string_formula_supports_builtin_functions(self):
        score_fn = composite_scorer(
            scorers=[alpha_stub(2.0), beta_stub(3.0)],
            formula="max(alpha_stub.value, beta_stub.value)",
        )

        score = await score_fn(make_state(), Target(""))

        assert score.value == 3.0

    @pytest.mark.asyncio
    async def test_callable_formula(self):
        score_fn = composite_scorer(
            scorers=[alpha_stub(2.0)],
            formula=lambda scores: scores["alpha_stub"].value * 10,
        )

        score = await score_fn(make_state(), Target(""))

        assert score.value == 20.0
        assert "formula" not in score.metadata

    @pytest.mark.asyncio
    async def test_reuses_existing_scores_from_state(self):
        # `raising_stub` raises if run, so a successful score proves the state score was reused
        score_fn = composite_scorer(
            scorers=[raising_stub()],
            formula="raising_stub.value",
        )
        state = make_state(scores={"raising_stub": Score(value=7.0)})

        score = await score_fn(state, Target(""))

        assert score.value == 7.0

    @pytest.mark.asyncio
    async def test_invalid_formula_returns_noanswer(self):
        score_fn = composite_scorer(
            scorers=[alpha_stub(2.0)],
            formula="undefined_scorer.value + 1",
        )

        score = await score_fn(make_state(), Target(""))

        assert score.value == NOANSWER
        assert "error" in score.metadata

    @pytest.mark.asyncio
    async def test_failing_scorer_returns_noanswer_and_logs_error(self, caplog):
        score_fn = composite_scorer(
            scorers=[raising_stub()],
            formula="raising_stub.value",
        )

        with caplog.at_level(logging.ERROR):
            score = await score_fn(make_state(), Target(""))

        assert score.value == NOANSWER
        assert "scorer failed" in score.metadata["error"]
        assert any(
            "Error in composite_scorer" in record.message
            for record in caplog.records
            if record.levelno == logging.ERROR
        )


class TestGetScorerName:
    def test_returns_registered_name(self):
        assert _get_scorer_name(alpha_stub(1.0)) == "alpha_stub"

    def test_unregistered_scorer_falls_back_to_str(self):
        async def plain_scorer(state: TaskState, target: Target) -> Score:
            return Score(value=1.0)

        assert _get_scorer_name(plain_scorer) == str(plain_scorer)
