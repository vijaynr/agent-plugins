from __future__ import annotations

import subprocess
from collections.abc import Callable, Sequence
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture(scope="session")
def repo_root() -> Path:
    """Repository root for tests, independent of the current working directory."""
    return ROOT


@pytest.fixture(scope="session")
def relpath(repo_root: Path) -> Callable[[Path], str]:
    """Format a path relative to the repository root with POSIX separators."""

    def _relpath(path: Path) -> str:
        resolved = path if path.is_absolute() else repo_root / path
        return resolved.relative_to(repo_root).as_posix()

    return _relpath


@pytest.fixture
def run_command(repo_root: Path) -> Callable[..., subprocess.CompletedProcess[str]]:
    """Run a command from the repository root and capture text output."""

    def _run_command(
        command: Sequence[str],
        *,
        cwd: Path | None = None,
        input: str | None = None,
        env: dict[str, str] | None = None,
        check: bool = True,
    ) -> subprocess.CompletedProcess[str]:
        result = subprocess.run(
            list(command),
            cwd=cwd or repo_root,
            input=input,
            env=env,
            text=True,
            capture_output=True,
            check=False,
        )
        if check and result.returncode != 0:
            pytest.fail(
                "command failed with exit code "
                f"{result.returncode}: {' '.join(command)}\n"
                f"stdout:\n{result.stdout}\n"
                f"stderr:\n{result.stderr}"
            )
        return result

    return _run_command
