"""
Copy a directory from the host filesystem into the sandbox.

Vendored from Control Arena (`control_arena.utils._sandbox_utils`, MIT License) so that
inspect-toolkit carries no dependency on control-arena. Source:
https://github.com/UKGovernmentBEIS/control-arena
"""

import fnmatch
import tarfile
import tempfile
from collections.abc import Callable
from contextlib import contextmanager
from pathlib import Path

from inspect_ai.util import sandbox


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


@contextmanager
def _temp_tarfile(
    source_path: Path,
    exclude: list[str] | None = None,
    include: list[str] | None = None,
):
    with tempfile.NamedTemporaryFile(suffix=".tar.gz") as local_temp:
        with tarfile.open(fileobj=local_temp, mode="w:gz") as archive:
            if include:
                for p in include:
                    archive.add(source_path / p, arcname=f"./{p}")
            archive.add(
                source_path,
                arcname=".",
                filter=_get_tar_pattern_filter(exclude) if exclude else None,
            )
        yield local_temp


async def copy_dir_to_sandbox(
    src: Path,
    dst: Path,
    exclude: list[str] | None = None,
    include: list[str] | None = None,
) -> None:
    """
    Copy a directory from the local filesystem to the sandbox environment.

    Args:
        src: The source directory on the local filesystem.
        dst: The destination directory in the sandbox.
        exclude: Patterns to exclude when copying. If None, nothing is excluded.
        include: Patterns to include when copying (these override the exclude patterns). If None, no
            additional includes are added.
    """
    active_sandbox = sandbox()

    if not src.exists() or not src.is_dir():
        raise NotADirectoryError(f"Source directory {src} does not exist or is not a directory")

    with _temp_tarfile(src, exclude=exclude, include=include) as tarfile_contents:
        sandbox_temp_path_result = await active_sandbox.exec(
            ["mktemp", "-p", "/tmp", "sandbox_archive_XXXXXX.tar.gz"]
        )
        if not sandbox_temp_path_result.success:
            raise RuntimeError(
                f"Failed to create temporary path in sandbox: {sandbox_temp_path_result.stderr}"
            )

        sandbox_temp_path = sandbox_temp_path_result.stdout.strip()

        try:
            tarfile_contents.seek(0)
            await active_sandbox.write_file(sandbox_temp_path, tarfile_contents.read())
            await active_sandbox.exec(["mkdir", "-p", dst.as_posix()])
            result = await active_sandbox.exec(
                ["tar", "-C", dst.as_posix(), "-xzf", sandbox_temp_path]
            )
            if not result.success:
                raise RuntimeError(f"Failed to extract archive in sandbox: {result.stderr}")
        finally:
            await active_sandbox.exec(["rm", "-f", sandbox_temp_path])
