from __future__ import annotations

import json
import os
import shutil
import subprocess
from pathlib import Path

import pytest


HELPER = Path(__file__).resolve().parents[1] / "plugins/sdlc/skills/init-workspace/scripts/init-git-branch.ps1"
SHELLS = [name for name in ("powershell", "pwsh") if shutil.which(name)]
EXPECTED_KEYS = {
    "ok", "error", "gitRoot", "currentBranch", "requestedBranch", "base", "remote", "dirty",
    "requiresStashApproval", "stashApproved", "stashCreated", "stashRef", "branchCreated",
    "checkedOut", "dryRun",
}
GIT_ENV = {
    "GIT_AUTHOR_NAME": "Test",
    "GIT_AUTHOR_EMAIL": "test@example.invalid",
    "GIT_COMMITTER_NAME": "Test",
    "GIT_COMMITTER_EMAIL": "test@example.invalid",
}

pytestmark = pytest.mark.skipif(not SHELLS or not shutil.which("git"), reason="PowerShell and git are required")


def git(cwd: Path, *args: str) -> str:
    result = subprocess.run(
        ["git", *args], cwd=cwd, env={**os.environ, **GIT_ENV}, capture_output=True, text=True, check=True
    )
    return result.stdout.strip()


@pytest.fixture
def work_repo(tmp_path: Path) -> Path:
    remote = tmp_path / "remote"
    remote.mkdir()
    git(remote, "init", "-q", "-b", "main")
    git(remote, "commit", "-q", "--allow-empty", "-m", "init")
    git(tmp_path, "clone", "-q", str(remote), "work")
    return tmp_path / "work"


def run_helper(shell: str, cwd: Path, *args: str, env: dict[str, str] | None = None) -> tuple[int, dict]:
    result = subprocess.run(
        [shell, "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", str(HELPER), *args],
        cwd=cwd,
        env={**os.environ, **GIT_ENV, **(env or {})},
        capture_output=True,
        text=True,
        timeout=120,
    )
    start = result.stdout.find("{")
    assert start >= 0, f"no JSON output: stdout={result.stdout!r} stderr={result.stderr!r}"
    return result.returncode, json.loads(result.stdout[start:])


@pytest.mark.parametrize("shell", SHELLS)
def test_fetch_warning_on_stderr_does_not_fail(shell: str, work_repo: Path) -> None:
    git(work_repo, "config", "remote.origin.uploadpack", 'echo "** WARNING: test warning" >&2; git-upload-pack')

    code, payload = run_helper(shell, work_repo, "-Branch", "feat-warning", "-Base", "main")

    assert code == 0, payload
    assert payload["ok"] is True and payload["branchCreated"] is True and payload["checkedOut"] is True
    assert set(payload) == EXPECTED_KEYS
    assert git(work_repo, "branch", "--show-current") == "feat-warning"


@pytest.mark.parametrize("shell", SHELLS)
def test_failed_fetch_does_not_stop_branch_creation(shell: str, work_repo: Path) -> None:
    git(work_repo, "remote", "set-url", "origin", str(work_repo.parent / "missing-remote"))

    code, payload = run_helper(shell, work_repo, "-Branch", "feat-offline", "-Base", "main")

    assert code == 0, payload
    assert payload["ok"] is True and payload["branchCreated"] is True
    assert git(work_repo, "branch", "--show-current") == "feat-offline"


@pytest.mark.parametrize("shell", SHELLS)
def test_approved_stash_runs_before_branch_creation(shell: str, work_repo: Path) -> None:
    (work_repo / "draft.txt").write_text("draft", encoding="utf-8")

    code, payload = run_helper(shell, work_repo, "-Branch", "feat-stash", "-Base", "main", "-StashApproved")

    assert code == 0, payload
    assert payload["stashCreated"] is True and payload["stashRef"] == "stash@{0}"
    assert payload["branchCreated"] is True
    assert not (work_repo / "draft.txt").exists()


def stderr_git_wrapper(tmp_path: Path) -> dict[str, str]:
    """Put a git wrapper first on PATH. It writes a warning to stderr and then runs the real git."""
    real_git = shutil.which("git")
    bin_dir = tmp_path / "wrapper-bin"
    bin_dir.mkdir()
    if os.name == "nt":
        (bin_dir / "git.cmd").write_text(f'@echo warning: test wrapper 1>&2\r\n@"{real_git}" %*\r\n', encoding="utf-8")
    else:
        wrapper = bin_dir / "git"
        wrapper.write_text(f'#!/bin/sh\necho "warning: test wrapper" >&2\nexec "{real_git}" "$@"\n', encoding="utf-8")
        wrapper.chmod(0o755)
    return {"PATH": f"{bin_dir}{os.pathsep}{os.environ['PATH']}"}


@pytest.mark.parametrize("shell", SHELLS)
def test_stderr_from_data_commands_is_not_read_as_data(shell: str, work_repo: Path, tmp_path: Path) -> None:
    code, payload = run_helper(
        shell, work_repo, "-Branch", "feat-quiet", "-Base", "main", env=stderr_git_wrapper(tmp_path)
    )

    assert code == 0, payload
    assert payload["ok"] is True and payload["dirty"] is False
    assert payload["requiresStashApproval"] is False
    assert payload["currentBranch"] == "main"
    assert Path(payload["gitRoot"]).resolve() == work_repo.resolve()


@pytest.mark.parametrize("shell", SHELLS)
def test_failed_stash_returns_error(shell: str, work_repo: Path) -> None:
    (work_repo / "draft.txt").write_text("draft", encoding="utf-8")
    (work_repo / ".git" / "index.lock").write_text("", encoding="utf-8")

    code, payload = run_helper(shell, work_repo, "-Branch", "feat-locked", "-Base", "main", "-StashApproved")

    assert code == 1
    assert payload["ok"] is False and payload["stashCreated"] is False and payload["branchCreated"] is False
    assert "git stash push" in payload["error"]
    assert git(work_repo, "branch", "--show-current") == "main"


@pytest.mark.parametrize("shell", SHELLS)
def test_failed_switch_returns_error(shell: str, work_repo: Path) -> None:
    code, payload = run_helper(shell, work_repo, "-Branch", "feat-bad-base", "-Base", "no-such-ref")

    assert code == 1
    assert payload["ok"] is False and payload["branchCreated"] is False and payload["checkedOut"] is False
    assert "git switch" in payload["error"]
    assert git(work_repo, "branch", "--show-current") == "main"


@pytest.mark.parametrize("shell", SHELLS)
def test_failed_switch_after_stash_names_the_stash(shell: str, work_repo: Path) -> None:
    (work_repo / "draft.txt").write_text("draft", encoding="utf-8")

    code, payload = run_helper(shell, work_repo, "-Branch", "feat-x", "-Base", "no-such-ref", "-StashApproved")

    assert code == 1
    assert payload["ok"] is False and payload["stashCreated"] is True
    assert "stash@{0}" in payload["error"] and "git stash pop" in payload["error"]
