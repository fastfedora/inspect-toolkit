"""
Compute the git diff between an agent's sandbox working directory and a reference directory.

Vendored from Control Arena (`control_arena.utils._git_diff_utils`, MIT License) so that
inspect-toolkit carries no dependency on control-arena. Source:
https://github.com/UKGovernmentBEIS/control-arena
"""

import shutil
from pathlib import Path
from tempfile import TemporaryDirectory

from git import Git, Repo, exc

from .copy_dir import copy_dir
from .copy_dir_from_sandbox import copy_dir_from_sandbox


async def get_diff_from_ref_dir(
    ref_dir: Path,
    agent_wd: Path = Path("/repo"),
    exclude: list[str] | None = None,
    include: list[str] | None = None,
) -> str:
    """
    Get the diff between the agent's working directory and the reference directory.

    For a git repository, the exclude/include arguments filter files before the agent's changes but
    not after, so an exclusion can be used to remove a file the agent should write and still show
    the agent writing it. Paths in the gitignore are ignored on both sides. For a non-git reference,
    the exclude/include arguments behave roughly like gitignore entries.

    Args:
        ref_dir: The path to the reference directory.
        agent_wd: The path to the agent's working directory in the sandbox.
        exclude: Patterns to exclude when copying files. If None, nothing is excluded.
        include: Patterns to include when copying files. If None, no additional includes are added.

    Returns:
        The git diff between the agent's working directory and the reference directory.
    """
    with TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        copy_dir(ref_dir, temp_path, exclude=exclude, include=include)

        # If the reference directory is a git repository, use git (which honours the gitignore).
        if (temp_path / ".git").exists():
            repo = Repo(temp_path)
            repo.config_writer().set_value("core", "filemode", False).release()
            # Commit the current state of the reference repo.
            repo.git.add(".")
            repo.git.commit("-m", "Temporary commit for diff")

            with TemporaryDirectory() as agent_dir:
                agent_path = Path(agent_dir)
                # Only exclude git when copying back (the rest is assumed gitignored).
                await copy_dir_from_sandbox(agent_wd, agent_path, exclude=[".git"])
                shutil.copytree(temp_path / ".git", agent_path / ".git")
                agent_repo = Repo(agent_path)
                agent_repo.git.add(".")
                return agent_repo.git.diff("HEAD", "--cached")

        # Otherwise fall back to `git diff --no-index`.
        with TemporaryDirectory() as agent_dir:
            await copy_dir_from_sandbox(agent_wd, Path(agent_dir), exclude=exclude, include=include)
            try:
                Git().config("core.filemode", "false")
                Git().diff("--no-index", temp_path.as_posix(), agent_dir)
                return ""
            except exc.GitCommandError as e:
                # `git diff --no-index` exits non-zero when there is a diff; format its output.
                return (
                    "\n".join(e.stdout.splitlines()[2:])
                    .replace(ref_dir.as_posix(), "")
                    .replace(temp_path.as_posix(), "")
                )
