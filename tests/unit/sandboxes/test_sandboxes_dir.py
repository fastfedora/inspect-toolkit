from inspect_toolkit.sandboxes import sandboxes_dir

DEFAULT_FEATURES = [
    "python",
    "node",
    "go",
    "java",
    "claude-code",
    "human-agent",
    "killable-process",
    "web-proxy",
    "pytest-db-reset-plugin",
    "pytest-fixed-salt-plugin",
]


def test_sandboxes_dir_returns_the_templates_root():
    root = sandboxes_dir()
    assert root.is_dir()
    assert (root / "default" / "compose.yaml").is_file()
    assert (root / "default" / "Dockerfile").is_file()
    assert (root / "default" / "scripts" / "install-features.sh").is_file()


def test_default_template_ships_all_features():
    features = sandboxes_dir() / "default" / "features"
    for name in DEFAULT_FEATURES:
        assert (features / name / "install.sh").is_file(), name
