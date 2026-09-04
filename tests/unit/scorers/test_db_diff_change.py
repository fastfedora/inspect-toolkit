from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from inspect_ai.scorer import NOANSWER, Target
from inspect_ai.solver import TaskState

from inspect_toolkit.scorers.db_diff_change import (
    _copy_and_setup_reference_repo,
    db_diff_change_scorer,
)

PKG = "inspect_toolkit.scorers.db_diff_change"


def make_state() -> TaskState:
    state = MagicMock(spec=TaskState)
    state.metadata = {}
    return state


class TestDbDiffChangeScorer:
    @pytest.mark.asyncio
    @patch(f"{PKG}._copy_and_setup_reference_repo", new_callable=AsyncMock)
    async def test_setup_failure_scores_noanswer(self, mock_setup):
        mock_setup.return_value = (None, {"status": "error"})
        score = await db_diff_change_scorer({"tables": {}})(make_state(), Target(""))
        assert score.value == NOANSWER
        assert "Failed to copy and setup" in score.explanation

    @pytest.mark.asyncio
    @patch(
        f"{PKG}._copy_and_setup_reference_repo",
        new_callable=AsyncMock,
        side_effect=RuntimeError("boom"),
    )
    async def test_exception_scores_noanswer(self, _mock_setup):
        score = await db_diff_change_scorer({"tables": {}})(make_state(), Target(""))
        assert score.value == NOANSWER
        assert "boom" in score.metadata["error"]
        assert "traceback" in score.metadata


class TestCopyAndSetupReferenceRepo:
    @pytest.mark.asyncio
    @patch(f"{PKG}.copy_dir_in_sandbox", new_callable=AsyncMock)
    @patch(f"{PKG}.resolve_repo_location", new_callable=AsyncMock)
    async def test_uses_snapshot_when_available(self, mock_resolve, mock_copy):
        mock_resolve.return_value = "/snapshots/first"
        path, err = await _copy_and_setup_reference_repo(make_state())
        assert err is None
        assert str(path).startswith("/var/tmp/reference_")
        mock_copy.assert_awaited_once()

    @pytest.mark.asyncio
    @patch(
        f"{PKG}.resolve_repo_location",
        new_callable=AsyncMock,
        side_effect=RuntimeError("nope"),
    )
    async def test_returns_error_on_exception(self, _mock_resolve):
        path, err = await _copy_and_setup_reference_repo(make_state())
        assert path is None
        assert err["status"] == "error"
        assert "nope" in err["error"]
