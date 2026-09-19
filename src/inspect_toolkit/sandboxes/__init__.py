from pathlib import Path


def sandboxes_dir() -> Path:
    """
    Return the directory containing the packaged sandbox templates.

    Each subdirectory is a sandbox template (currently just ``default``) suitable for use as a
    `FixtureManager`'s ``templates_dir``. A fixture's ``sandbox.name`` selects a template by folder
    name, e.g. ``name: default`` resolves to ``sandboxes_dir() / "default"``.
    """
    return Path(__file__).resolve().parent


__all__ = ["sandboxes_dir"]
