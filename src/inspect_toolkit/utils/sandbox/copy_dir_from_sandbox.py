"""
Copy a directory from the sandbox into the host filesystem.

Vendored from Control Arena (`control_arena.utils._sandbox_utils`, MIT License) so that
inspect-toolkit carries no dependency on control-arena. Source:
https://github.com/UKGovernmentBEIS/control-arena
"""

import logging
import os
import tarfile
import tempfile
from io import BytesIO
from pathlib import Path

from inspect_ai.util import sandbox

logger = logging.getLogger(__name__)


async def copy_dir_from_sandbox(
    src: Path,
    dst: Path,
    exclude: list[str] | None = None,
    include: list[str] | None = None,
) -> None:
    """
    Copy a directory from the sandbox environment to the local filesystem.

    Args:
        src: The source directory in the sandbox.
        dst: The destination directory on the local filesystem.
        exclude: Patterns to exclude when copying. If None, nothing is excluded.
        include: Patterns to include when copying (these override the exclude patterns). If None, no
            additional includes are added.
    """
    active_sandbox = sandbox()

    result = await active_sandbox.exec(["test", "-d", src.as_posix()])
    if not result.success:
        logger.warning(f"Directory {src} does not exist in the sandbox")
        raise NotADirectoryError(f"Directory {src} does not exist in the sandbox")

    sandbox_temp_path_result = await active_sandbox.exec(
        ["mktemp", "-p", "/tmp", "sandbox_archive_XXXXXX.tar.gz"]
    )
    if not sandbox_temp_path_result.success:
        raise RuntimeError(
            f"Failed to create temporary path in sandbox: {sandbox_temp_path_result.stderr}"
        )

    sandbox_temp_path = sandbox_temp_path_result.stdout.strip()

    with tempfile.NamedTemporaryFile(suffix=".tar.gz", delete=False) as local_temp:
        local_temp_path = local_temp.name

    try:
        dst.mkdir(parents=True, exist_ok=True)

        tar_args = ["tar", "-C", src.as_posix(), "--ignore-failed-read", "-czf", sandbox_temp_path]
        # Include patterns come first so they take priority over the excludes that follow.
        if include:
            tar_args += [f"./{pattern}" for pattern in include]
        if exclude:
            tar_args += [f"--exclude=./{pattern}" for pattern in exclude]
        tar_args.append(".")

        result = await active_sandbox.exec(tar_args)
        if not result.success:
            raise RuntimeError(f"Failed to create archive in sandbox: {result.stderr}")

        file_contents = await active_sandbox.read_file(sandbox_temp_path, text=False)
        await active_sandbox.exec(["rm", sandbox_temp_path])

        with tarfile.open(fileobj=BytesIO(file_contents), mode="r:gz") as archive:
            archive.extractall(path=dst, filter="data")
    finally:
        if os.path.exists(local_temp_path):
            os.remove(local_temp_path)
