"""
Copy a directory within the local filesystem via a tar round-trip (for behavioural parity with the
host<->sandbox transfer helpers).

Vendored from Control Arena (`control_arena.utils._sandbox_utils`, MIT License) so that
inspect-toolkit carries no dependency on control-arena. Source:
https://github.com/UKGovernmentBEIS/control-arena
"""

import fnmatch
import tarfile
from collections.abc import Callable
from io import BytesIO
from pathlib import Path


def _get_tar_pattern_filter(
    exclude: list[str],
) -> Callable[[tarfile.TarInfo], tarfile.TarInfo | None] | None:
    def pattern_filter(tarinfo: tarfile.TarInfo) -> tarfile.TarInfo | None:
        relative_path = tarinfo.name
        if exclude:
            for pattern in exclude:
                if not pattern.startswith("./"):
                    pattern = "./" + pattern
                if fnmatch.fnmatch(relative_path, pattern):
                    return None
        return tarinfo

    return pattern_filter if exclude else None


def copy_dir(
    source_path: Path,
    destination_path: Path,
    exclude: list[str] | None = None,
    include: list[str] | None = None,
) -> None:
    """
    Copy a directory in the local filesystem, using a tar round-trip for consistent behaviour with
    `copy_dir_to_sandbox` and `copy_dir_from_sandbox`.

    Args:
        source_path: The source directory.
        destination_path: The destination directory.
        exclude: Patterns to exclude when copying. If None, nothing is excluded.
        include: Patterns to include when copying (these override the exclude patterns). If None, no
            additional includes are added.
    """
    buffer = BytesIO()
    with tarfile.open(fileobj=buffer, mode="w:gz") as archive:
        if include:
            for p in include:
                archive.add(source_path / p, arcname=f"./{p}")
        archive.add(
            source_path,
            arcname=".",
            filter=_get_tar_pattern_filter(exclude) if exclude else None,
        )
    buffer.seek(0)
    with tarfile.open(fileobj=buffer, mode="r:gz") as archive:
        archive.extractall(path=destination_path, filter="data")
