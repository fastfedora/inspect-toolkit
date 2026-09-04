from pathlib import Path

from inspect_toolkit.utils.filesystem import ensure_extension


class TestEnsureExtension:
    def test_adds_first_extension_when_missing(self):
        assert ensure_extension("config", ["yaml", "yml"]) == "config.yaml"

    def test_keeps_path_that_already_has_a_listed_extension(self):
        assert ensure_extension("config.yml", ["yaml", "yml"]) == "config.yml"

    def test_accepts_a_single_string_extension(self):
        assert ensure_extension("data", "json") == "data.json"

    def test_path_input_gets_suffixed_and_stays_a_path(self):
        result = ensure_extension(Path("config"), ["yaml"])

        assert result == Path("config.yaml")
        assert isinstance(result, Path)

    def test_path_input_with_matching_extension_is_unchanged(self):
        path = Path("config.yaml")

        assert ensure_extension(path, ["yaml", "yml"]) == path
