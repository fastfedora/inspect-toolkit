from contextlib import asynccontextmanager
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from inspect_ai.solver import TaskState
from inspect_ai.util import Store

from inspect_toolkit.solvers.diffs.diff_databases import diff_databases

PKG = "inspect_toolkit.solvers.diffs.diff_databases"


@asynccontextmanager
async def fake_repo_dir(*args, **kwargs):
    yield Path("/fake/repo")


def make_state() -> TaskState:
    state = MagicMock(spec=TaskState)
    state.store = Store()
    state.metadata = {}
    return state


class TestDiffDatabases:
    """The `diff_databases` solver stores its result under `db_diff` in the store."""

    @pytest.mark.asyncio
    @patch(f"{PKG}.diff_filesystem_databases")
    @patch(f"{PKG}.local_repo_dir", new=fake_repo_dir)
    async def test_stores_successful_diff(self, mock_diff):
        mock_diff.return_value = {"status": "success", "databases": {}}
        state = make_state()

        result = await diff_databases()(state, None)

        assert result is state
        assert state.store.get("db_diff") == {"status": "success", "databases": {}}
        mock_diff.assert_called_once()

    @pytest.mark.asyncio
    @patch(f"{PKG}.diff_filesystem_databases", side_effect=RuntimeError("boom"))
    @patch(f"{PKG}.local_repo_dir", new=fake_repo_dir)
    async def test_stores_error_on_failure(self, _mock_diff):
        state = make_state()

        await diff_databases()(state, None)

        stored = state.store.get("db_diff")
        assert stored["status"] == "error"
        assert "boom" in stored["error"]
        assert "traceback" in stored

    @pytest.mark.asyncio
    @patch(f"{PKG}.diff_filesystem_databases")
    @patch(f"{PKG}.local_repo_dir", new=fake_repo_dir)
    async def test_forwards_diff_options(self, mock_diff):
        mock_diff.return_value = {"status": "success"}
        state = make_state()

        await diff_databases(db_patterns=["*.duckdb"], max_rows=5, include_data=False)(state, None)

        kwargs = mock_diff.call_args.kwargs
        assert kwargs["db_patterns"] == ["*.duckdb"]
        assert kwargs["max_rows"] == 5
        assert kwargs["include_data"] is False
