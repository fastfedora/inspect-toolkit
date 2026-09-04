import re
from pathlib import Path


def get_cache_path(
    source_type: str,
    identifier: str,
    ref: str | None = None,
    cache_root: Path | None = None,
) -> Path:
    """
    Get the cache path for a dataset source.

    Args:
        source_type: Type of source (e.g., "github", "huggingface")
        identifier: Unique identifier for the source (e.g., "owner/repo/path")
        ref: Optional reference (branch, tag, or commit) for versioning
        cache_root: Root directory under which datasets are cached. Defaults to a `datasets`
            directory at the project root, discovered by walking up from the current directory to
            the nearest `pyproject.toml`.

    Returns:
        Path to the cached dataset directory
    """
    safe_ref = _sanitize_for_path(ref) if ref else "main"
    root = cache_root if cache_root is not None else _get_cache_root()

    return root / source_type / _sanitize_for_path(identifier) / safe_ref


def _get_cache_root() -> Path:
    """
    Get the root directory for cached datasets.

    Returns:
        Path to the datasets cache directory at the project root
    """
    # Find project root by looking for pyproject.toml
    current = Path.cwd()
    while current != current.parent:
        if (current / "pyproject.toml").exists():
            return current / "datasets"
        current = current.parent

    # Fallback to current directory if project root not found
    return Path.cwd() / "datasets"


def _sanitize_for_path(value: str) -> str:
    """
    Sanitize a string so it can be safely used as part of a filesystem path.

    Replaces disallowed characters with dashes and collapses multiple dashes.
    """
    safe_value = re.sub(r"[^\w\-.]", "-", value)
    return re.sub(r"-+", "-", safe_value)
