from __future__ import annotations

import json
import os
import shutil
import subprocess
from pathlib import Path

import pytest


HELPER = Path(__file__).resolve().parents[1] / "plugins/sdlc/skills/init-workspace/scripts/init-git-worktree.sh"
BASH = shutil.which("bash")
GIT_ENV = {
    "GIT_AUTHOR_NAME": "Test",
    "GIT_AUTHOR_EMAIL": "test@example.invalid",
    "GIT_COMMITTER_NAME": "Test",
    "GIT_COMMITTER_EMAIL": "test@example.invalid",
}
pytestmark = pytest.mark.skipif(not BASH or not shutil.which("git"), reason="Bash and git are required")


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


def run_helper(cwd: Path, *args: str) -> tuple[int, dict]:
    result = subprocess.run(
        [BASH, str(HELPER), *args],
        cwd=cwd,
        env={**os.environ, **GIT_ENV},
        capture_output=True,
        text=True,
        timeout=30,
    )
    start = result.stdout.find("{")
    assert start >= 0, f"no JSON output: stdout={result.stdout!r} stderr={result.stderr!r}"
    return result.returncode, json.loads(result.stdout[start:])


def test_existing_worktree_with_different_branch_is_rejected(work_repo: Path, tmp_path: Path) -> None:
    existing_path = tmp_path / "unrelated-worktree"
    git(work_repo, "worktree", "add", "-q", "-b", "unrelated-branch", str(existing_path), "main")

    code, payload = run_helper(
        work_repo,
        "expected-feature",
        "--branch", "expected-branch",
        "--worktree-path", str(existing_path),
        "--base", "main",
    )

    assert code != 0
    assert payload["ok"] is False
    assert "branch" in payload["error"].lower()
    assert git(existing_path, "branch", "--show-current") == "unrelated-branch"


def test_fetch_failure_is_reported_before_creating_worktree(work_repo: Path, tmp_path: Path) -> None:
    worktree_path = tmp_path / "fetch-failure"

    code, payload = run_helper(
        work_repo,
        "fetch-failure",
        "--worktree-path", str(worktree_path),
        "--remote", "missing-remote",
    )

    assert code != 0
    assert payload["ok"] is False
    assert "fetch" in payload["error"].lower()
    assert not worktree_path.exists()


def test_dry_run_rejects_unknown_base(work_repo: Path) -> None:
    code, payload = run_helper(work_repo, "dry-feature", "--base", "missing-base", "--dry-run")

    assert code != 0
    assert payload["ok"] is False
    assert "base" in payload["error"].lower()
    assert not Path(payload["worktreePath"]).exists()
