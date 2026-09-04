import logging
import shutil

import pytest
from unittest.mock import AsyncMock, MagicMock, patch, mock_open
from pathlib import Path
from inspect import iscoroutinefunction
from inspect_ai.solver import TaskState
from inspect_ai.util import Store

from inspect_toolkit.solvers.exports.export_store import export_store


class TestExportStore:
    """Test cases for the export_store solver."""

    def teardown_method(self):
        """Clean up test_exports directory if it was created."""
        test_exports_path = Path("test_exports")
        if test_exports_path.exists():
            shutil.rmtree(test_exports_path)

    def setup_method(self):
        """Set up test fixtures."""
        self.mock_state = MagicMock(spec=TaskState)
        self.mock_state.store = Store(
            {
                "key1": "value1",
                "key2": {"nested": "data"},
                "key3": [1, 2, 3],
                "multiline": "Line 1\nLine 2\nLine 3",
                "exclude_me": "should be excluded",
            }
        )
        self.mock_state.sample_id = "test_sample_123"
        self.mock_state.metadata = {"test": "metadata", "eval_id": "test_eval_456"}
        self.mock_generate = AsyncMock()

    @pytest.mark.asyncio
    async def test_export_store_warns_and_falls_back_when_eval_id_missing(self, caplog):
        """When metadata has no `eval_id`, a warning is logged and the export still proceeds."""
        self.mock_state.metadata = {"test": "metadata"}  # no eval_id

        with (
            patch("inspect_toolkit.solvers.exports.export_store.Path.mkdir"),
            patch(
                "inspect_toolkit.solvers.exports.export_store.format_as_yaml",
                return_value="yaml_content",
            ),
            patch("builtins.open", mock_open()),
        ):
            solver = export_store(export_path="test_exports", output_folder="store", format="yaml")
            with caplog.at_level(logging.WARNING):
                await solver(self.mock_state, self.mock_generate)

        assert "No 'eval_id' in sample metadata" in caplog.text

    @pytest.mark.asyncio
    async def test_export_store_yaml_format(self):
        """Test successful export of store data in YAML format."""
        with (
            patch("inspect_toolkit.solvers.exports.export_store.Path.mkdir") as mock_mkdir,
            patch("inspect_toolkit.solvers.exports.export_store.format_as_yaml") as mock_format_yaml,
            patch("builtins.open", mock_open()) as mock_file,
        ):
            mock_format_yaml.return_value = "yaml_content"
            store_data = dict(self.mock_state.store.items())

            solver = export_store(
                export_path="test_exports",
                output_folder="store",
                format="yaml",
            )

            result = await solver(self.mock_state, self.mock_generate)


            # Verify directory was created
            expected_path = Path("test_exports") / "test_eval_456" / "test_sample_123" / "store"
            mock_mkdir.assert_called_once_with(parents=True, exist_ok=True)

            # Verify format_as_yaml was called with store data
            mock_format_yaml.assert_called_once()
            call_args = mock_format_yaml.call_args
            assert call_args[0][0] == store_data

            # Verify YAML file was written
            mock_file.assert_called_once()
            call_args = mock_file.call_args
            assert str(call_args[0][0]).endswith("store_data.yaml")
            assert call_args[0][1] == "w"
            assert call_args[1]["encoding"] == "utf-8"

            # Verify store was updated with success
            export_result = self.mock_state.store.get("export.store")
            assert export_result is not None
            assert export_result["status"] == "success"
            assert export_result["format"] == "yaml"
            assert export_result["destination"] == str(expected_path / "store_data.yaml")

            # Verify result is the state
            assert result == self.mock_state

    @pytest.mark.asyncio
    async def test_export_store_json_format(self):
        """Test successful export of store data in JSON format."""
        with (
            patch("inspect_toolkit.solvers.exports.export_store.Path.mkdir") as mock_mkdir,
            patch("builtins.open", mock_open()) as mock_file,
        ):

            solver = export_store(
                export_path="test_exports",
                output_folder="store",
                format="json",
            )

            result = await solver(self.mock_state, self.mock_generate)

            # Verify directory was created
            mock_mkdir.assert_called_once_with(parents=True, exist_ok=True)

            # Verify JSON file was written
            mock_file.assert_called_once()
            call_args = mock_file.call_args
            assert str(call_args[0][0]).endswith("store_data.json")
            assert call_args[0][1] == "w"
            assert call_args[1]["encoding"] == "utf-8"

            # Verify store was updated with success
            export_result = self.mock_state.store.get("export.store")
            assert export_result is not None
            assert export_result["status"] == "success"
            assert export_result["format"] == "json"
            assert export_result["destination"].endswith("store_data.json")

            # Verify result is the state
            assert result == self.mock_state

    @pytest.mark.asyncio
    async def test_export_store_with_include_keys(self):
        """Test export with specific keys included."""
        with (
            patch("inspect_toolkit.solvers.exports.export_store.Path.mkdir"),
            patch("inspect_toolkit.solvers.exports.export_store.format_as_yaml") as mock_format_yaml,
            patch("builtins.open", mock_open()),
        ):
            mock_format_yaml.return_value = "yaml_content"

            solver = export_store(
                export_path="test_exports",
                output_folder="store",
                format="yaml",
                include_keys=["key1", "key2"],
            )

            result = await solver(self.mock_state, self.mock_generate)

            # Verify format_as_yaml was called with filtered data
            mock_format_yaml.assert_called_once()
            call_args = mock_format_yaml.call_args
            filtered_data = call_args[0][0]
            assert "key1" in filtered_data
            assert "key2" in filtered_data
            assert "key3" not in filtered_data
            assert "exclude_me" not in filtered_data

            # Verify result is the state
            assert result == self.mock_state

    @pytest.mark.asyncio
    async def test_export_store_with_exclude_keys(self):
        """Test export with specific keys excluded."""
        with (
            patch("inspect_toolkit.solvers.exports.export_store.Path.mkdir"),
            patch("inspect_toolkit.solvers.exports.export_store.format_as_yaml") as mock_format_yaml,
            patch("builtins.open", mock_open()),
        ):
            mock_format_yaml.return_value = "yaml_content"

            solver = export_store(
                export_path="test_exports",
                output_folder="store",
                format="yaml",
                exclude_keys=["exclude_me", "key3"],
            )

            result = await solver(self.mock_state, self.mock_generate)

            # Verify format_as_yaml was called with filtered data
            mock_format_yaml.assert_called_once()
            call_args = mock_format_yaml.call_args
            filtered_data = call_args[0][0]
            assert "key1" in filtered_data
            assert "key2" in filtered_data
            assert "key3" not in filtered_data
            assert "exclude_me" not in filtered_data

            # Verify result is the state
            assert result == self.mock_state

    @pytest.mark.asyncio
    async def test_export_store_with_both_include_and_exclude(self):
        """Test export with both include and exclude keys (include takes precedence)."""
        with (
            patch("inspect_toolkit.solvers.exports.export_store.Path.mkdir"),
            patch("inspect_toolkit.solvers.exports.export_store.format_as_yaml") as mock_format_yaml,
            patch("builtins.open", mock_open()),
        ):
            mock_format_yaml.return_value = "yaml_content"

            solver = export_store(
                export_path="test_exports",
                output_folder="store",
                format="yaml",
                include_keys=["key1", "key2"],
                exclude_keys=[
                    "key2",
                    "key3",
                ],  # key2 should be excluded, even though it's in include_keys
            )

            result = await solver(self.mock_state, self.mock_generate)

            # Verify format_as_yaml was called with include-filtered data
            mock_format_yaml.assert_called_once()
            call_args = mock_format_yaml.call_args
            filtered_data = call_args[0][0]
            assert "key1" in filtered_data
            assert "key2" not in filtered_data  # exclude_keys takes precedence
            assert "key3" not in filtered_data
            assert "exclude_me" not in filtered_data

            # Verify result is the state
            assert result == self.mock_state

    @pytest.mark.asyncio
    async def test_export_store_error_handling(self):
        """Test error handling in export_store."""
        with (
            patch("inspect_toolkit.solvers.exports.export_store.Path.mkdir"),
            patch("builtins.open", side_effect=OSError("Permission denied")),
        ):

            solver = export_store(
                export_path="test_exports",
                output_folder="store",
                format="yaml",
            )

            result = await solver(self.mock_state, self.mock_generate)

            # Verify error was stored
            export_result = self.mock_state.store.get("export.store")
            assert export_result is not None
            assert export_result["status"] == "error"
            assert "Permission denied" in export_result["error"]
            assert "traceback" in export_result

            # Verify result is still the state
            assert result == self.mock_state

    @pytest.mark.asyncio
    async def test_export_store_custom_parameters(self):
        """Test export_store with custom parameters."""
        with (
            patch("inspect_toolkit.solvers.exports.export_store.Path.mkdir") as mock_mkdir,
            patch("inspect_toolkit.solvers.exports.export_store.format_as_yaml") as mock_format_yaml,
            patch("builtins.open", mock_open()) as mock_file,
        ):
            mock_format_yaml.return_value = "yaml_content"

            solver = export_store(
                export_path="custom_exports",
                output_folder="custom_store",
                format="yaml",
                include_keys=["key1"],
            )

            result = await solver(self.mock_state, self.mock_generate)

            # Verify custom path was used
            mock_mkdir.assert_called_once_with(parents=True, exist_ok=True)

            # Verify custom output folder in file path
            call_args = mock_file.call_args
            assert "custom_store" in str(call_args[0][0])

            # Verify result is the state
            assert result == self.mock_state

    @pytest.mark.asyncio
    async def test_export_store_empty_store_data(self):
        """Test export with empty store data."""
        # Create a new store with empty data
        self.mock_state.store = Store({})

        with (
            patch("inspect_toolkit.solvers.exports.export_store.Path.mkdir"),
            patch("inspect_toolkit.solvers.exports.export_store.format_as_yaml") as mock_format_yaml,
            patch("builtins.open", mock_open()),
        ):
            mock_format_yaml.return_value = "yaml_content"

            solver = export_store(
                export_path="test_exports",
                output_folder="store",
                format="yaml",
            )

            result = await solver(self.mock_state, self.mock_generate)

            # Verify format_as_yaml was called with empty dict
            mock_format_yaml.assert_called_once()
            call_args = mock_format_yaml.call_args
            assert call_args[0][0] == {}

            # Verify store was updated with success
            export_result = self.mock_state.store.get("export.store")
            assert export_result["status"] == "success"

            # Verify result is the state
            assert result == self.mock_state

    def test_export_store_solver_creation(self):
        """Test that export_store returns a proper solver function."""
        solver = export_store(
            export_path="test_exports",
            output_folder="store",
            format="yaml",
        )

        # Verify it's a callable
        assert callable(solver)

        # Verify it's an async function
        assert iscoroutinefunction(solver)
