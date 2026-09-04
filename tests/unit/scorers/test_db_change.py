from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from inspect_ai.scorer import CORRECT, INCORRECT, NOANSWER, Target
from inspect_ai.solver import TaskState

from inspect_toolkit.scorers.db_change import db_change_scorer

PKG = "inspect_toolkit.scorers.db_change"


def make_state(db_diff=None) -> TaskState:
    state = MagicMock(spec=TaskState)
    store = MagicMock()
    store.get.return_value = db_diff
    state.store = store
    state.metadata = {}
    return state


class TestDbChangeScorer:
    @pytest.mark.asyncio
    @patch(f"{PKG}.matches_diff", return_value=True)
    async def test_match_scores_correct(self, _matches):
        score = await db_change_scorer({"tables": {}})(make_state({"status": "success"}), Target(""))
        assert score.value == CORRECT
        assert score.metadata["matches"] is True

    @pytest.mark.asyncio
    @patch(f"{PKG}.matches_diff", return_value=False)
    async def test_no_match_scores_incorrect(self, _matches):
        score = await db_change_scorer({"tables": {}})(make_state({"status": "success"}), Target(""))
        assert score.value == INCORRECT
        assert score.metadata["matches"] is False

    @pytest.mark.asyncio
    @patch(f"{PKG}.get_solver_results", new_callable=AsyncMock)
    async def test_missing_diff_results_scores_incorrect(self, mock_results):
        state = make_state(None)
        mock_results.return_value = (state, {})  # solver produced no db_diff
        score = await db_change_scorer({"tables": {}})(state, Target(""))
        assert score.value == INCORRECT
        assert score.metadata["error"] == "no_db_diff_results"

    @pytest.mark.asyncio
    async def test_failed_diff_scores_incorrect(self):
        state = make_state({"status": "error", "error": "locked"})
        score = await db_change_scorer({"tables": {}})(state, Target(""))
        assert score.value == INCORRECT
        assert score.metadata["error"] == "db_diff_failed"

    @pytest.mark.asyncio
    @patch(f"{PKG}.matches_diff", side_effect=RuntimeError("boom"))
    async def test_exception_scores_noanswer(self, _matches):
        score = await db_change_scorer({"tables": {}})(make_state({"status": "success"}), Target(""))
        assert score.value == NOANSWER
        assert "boom" in score.metadata["error"]

    @pytest.mark.asyncio
    @patch(f"{PKG}.matches_diff", return_value=True)
    @patch(f"{PKG}.get_solver_results", new_callable=AsyncMock)
    async def test_interim_score_bypasses_store(self, mock_results, _matches):
        state = make_state({"status": "success"})  # store would report success...
        mock_results.return_value = (state, {"db_diff": {"status": "success"}})
        score = await db_change_scorer({"tables": {}}, interim_score=True)(state, Target(""))
        assert score.value == CORRECT
        mock_results.assert_awaited_once()  # ...but the solver was run instead
        state.store.get.assert_not_called()
