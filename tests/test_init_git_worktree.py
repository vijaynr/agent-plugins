from __future__ import annotations

import json
import os
import shutil
import subprocess
from pathlib import Path

import pytest


HELPER = Path(__file__).resolve().parents[1] / "plugins/sdlc/skills/init-workspace/scripts/init-git-worktree.ps1"
PREPARE_HELPER = Path(__file__).resolve().parents[1] / "plugins/sdlc/skills/init-workspace/scripts/prepare-init-workspace.ps1"
SHELLS = [name for name in ("powershell", "pwsh") if shutil.which(name)]
EXPECTED_KEYS = {
    "ok", "error", "repoRoot", "worktreePath", "feature", "featureSlug",
    "branch", "base", "branchCreated", "worktreeCreated", "worktreeExisted", "dryRun",
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
def test_default_worktree_path_and_branch(shell: str, work_repo: Path) -> None:
    code, payload = run_helper(shell, work_repo, "-Feature", "retention-policy")

    assert code == 0, payload
    assert set(payload) == EXPECTED_KEYS
    assert payload["ok"] is True
    assert payload["feature"] == "retention-policy"
    assert payload["featureSlug"] == "retention-policy"
    assert payload["branch"] == "retention-policy"
    assert payload["branchCreated"] is True
    assert payload["worktreeCreated"] is True
    assert payload["worktreeExisted"] is False
    assert payload["dryRun"] is False

    expected_path = (work_repo.parent / "work.worktrees" / "retention-policy").resolve().as_posix()
    assert payload["worktreePath"].lower() == expected_path.lower()
    assert Path(payload["worktreePath"]).is_dir()

    # Verify worktree has the branch checked out
    wt_branch = git(Path(payload["worktreePath"]), "branch", "--show-current")
    assert wt_branch == "retention-policy"

    # Verify main repo remains on main
    main_branch = git(work_repo, "branch", "--show-current")
    assert main_branch == "main"


@pytest.mark.parametrize("shell", SHELLS)
def test_custom_branch_and_worktree_path(shell: str, work_repo: Path) -> None:
    custom_path = (work_repo.parent / "custom-wt").resolve().as_posix()
    code, payload = run_helper(
        shell,
        work_repo,
        "-Feature", "my-feature",
        "-Branch", "feat-custom-branch",
        "-WorktreePath", custom_path,
        "-Base", "main",
    )

    assert code == 0, payload
    assert payload["ok"] is True
    assert payload["branch"] == "feat-custom-branch"
    assert payload["worktreePath"].lower() == custom_path.lower()
    assert Path(custom_path).is_dir()
    assert git(Path(custom_path), "branch", "--show-current") == "feat-custom-branch"


@pytest.mark.parametrize("shell", SHELLS)
def test_reuse_existing_worktree(shell: str, work_repo: Path) -> None:
    # First creation
    code1, payload1 = run_helper(shell, work_repo, "-Feature", "reuse-test")
    assert code1 == 0 and payload1["worktreeCreated"] is True

    # Second invocation should detect existing worktree
    code2, payload2 = run_helper(shell, work_repo, "-Feature", "reuse-test")
    assert code2 == 0
    assert payload2["ok"] is True
    assert payload2["worktreeExisted"] is True
    assert payload2["worktreeCreated"] is False


@pytest.mark.parametrize("shell", SHELLS)
def test_dry_run_does_not_create_directory(shell: str, work_repo: Path) -> None:
    code, payload = run_helper(shell, work_repo, "-Feature", "dry-feature", "-DryRun")

    assert code == 0, payload
    assert payload["ok"] is True
    assert payload["dryRun"] is True
    assert payload["worktreeCreated"] is False
    assert not Path(payload["worktreePath"]).exists()


@pytest.mark.parametrize("shell", SHELLS)
def test_existing_worktree_with_different_branch_is_rejected(shell: str, work_repo: Path, tmp_path: Path) -> None:
    existing_path = tmp_path / "unrelated-worktree"
    git(work_repo, "worktree", "add", "-q", "-b", "unrelated-branch", str(existing_path), "main")

    code, payload = run_helper(
        shell,
        work_repo,
        "-Feature", "expected-feature",
        "-Branch", "expected-branch",
        "-WorktreePath", str(existing_path),
        "-Base", "main",
    )

    assert code != 0
    assert payload["ok"] is False
    assert "branch" in payload["error"].lower()
    assert git(existing_path, "branch", "--show-current") == "unrelated-branch"


@pytest.mark.parametrize("shell", SHELLS)
def test_fetch_failure_is_reported_before_creating_worktree(shell: str, work_repo: Path, tmp_path: Path) -> None:
    worktree_path = tmp_path / "fetch-failure"

    code, payload = run_helper(
        shell, work_repo, "-Feature", "fetch-failure", "-WorktreePath", str(worktree_path), "-Remote", "missing-remote"
    )

    assert code != 0
    assert payload["ok"] is False
    assert "fetch" in payload["error"].lower()
    assert not worktree_path.exists()


@pytest.mark.parametrize("shell", SHELLS)
def test_dry_run_rejects_unknown_base(shell: str, work_repo: Path) -> None:
    code, payload = run_helper(shell, work_repo, "-Feature", "dry-feature", "-Base", "missing-base", "-DryRun")

    assert code != 0
    assert payload["ok"] is False
    assert "base" in payload["error"].lower()
    assert not Path(payload["worktreePath"]).exists()


@pytest.mark.parametrize("shell", SHELLS)
def test_existing_branch_attached_without_error(shell: str, work_repo: Path) -> None:
    # Pre-create branch without checking out
    git(work_repo, "branch", "existing-feat", "main")

    code, payload = run_helper(shell, work_repo, "-Feature", "existing-feat")

    assert code == 0, payload
    assert payload["ok"] is True
    assert payload["branchCreated"] is False
    assert payload["worktreeCreated"] is True
    assert git(Path(payload["worktreePath"]), "branch", "--show-current") == "existing-feat"


@pytest.mark.parametrize("shell", SHELLS)
def test_prepare_init_workspace_in_worktree(shell: str, work_repo: Path) -> None:
    code_wt, payload_wt = run_helper(shell, work_repo, "-Feature", "e2e-worktree")
    assert code_wt == 0
    wt_path = Path(payload_wt["worktreePath"])

    # Run prepare-init-workspace targeting the worktree root
    result = subprocess.run(
        [shell, "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", str(PREPARE_HELPER), "e2e-worktree", "-Root", str(wt_path)],
        cwd=work_repo,
        env={**os.environ, **GIT_ENV},
        capture_output=True,
        text=True,
        timeout=120,
    )
    assert result.returncode == 0
    start = result.stdout.find("{")
    assert start >= 0
    payload_prep = json.loads(result.stdout[start:])

    assert payload_prep["ok"] is True
    status_file = wt_path / ".features" / "e2e-worktree" / "status.json"
    assert status_file.is_file()

