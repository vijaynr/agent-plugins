from __future__ import annotations

import json
import shutil
import subprocess
import sys
from pathlib import Path

import pytest


@pytest.fixture
def standalone_cli(tmp_path: Path) -> Path:
    source_skill = Path(__file__).parents[1] / "skills" / "okf-toolkit"
    installed_skill = tmp_path / "installed-skill"
    shutil.copytree(source_skill, installed_skill, ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
    return installed_skill / "scripts" / "okf_cli.py"


def run_cli(cli: Path, repository: Path, *arguments: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(cli), *arguments],
        cwd=repository,
        text=True,
        capture_output=True,
        check=False,
    )


def write_valid_bundle(repository: Path) -> Path:
    docs = repository / "docs"
    docs.mkdir()
    (docs / "index.md").write_text("# Catalog\n", encoding="utf-8")
    (docs / "system.md").write_text("---\ntype: Architecture\n---\nSystem.\n", encoding="utf-8")
    return docs


def test_standalone_skill_initializes_target_repository(tmp_path, standalone_cli):
    repository = tmp_path / "target"
    repository.mkdir()

    result = run_cli(
        standalone_cli,
        repository,
        "init",
        "--repo-root", ".",
        "--docs-root", "docs",
    )

    assert result.returncode == 0, result.stderr
    assert (repository / "docs/architecture/system.md").is_file()


def test_standalone_skill_ingests_into_target_repository(tmp_path, standalone_cli):
    repository = tmp_path / "target"
    repository.mkdir()
    write_valid_bundle(repository)

    result = run_cli(
        standalone_cli,
        repository,
        "ingest",
        "--repo-root", ".",
        "--docs-root", "docs",
        "--text", "We decided to keep the skill portable.",
    )

    assert result.returncode == 0, result.stderr
    assert (repository / "docs/decisions/conversation.md").is_file()


def test_standalone_skill_validates_target_repository(tmp_path, standalone_cli):
    repository = tmp_path / "target"
    repository.mkdir()
    write_valid_bundle(repository)

    result = run_cli(standalone_cli, repository, "validate", "--docs-root", "docs", "--format", "json")

    assert result.returncode == 0, result.stderr
    assert json.loads(result.stdout)["ok"] is True


def test_standalone_skill_exports_target_repository(tmp_path, standalone_cli):
    repository = tmp_path / "target"
    repository.mkdir()
    write_valid_bundle(repository)

    result = run_cli(standalone_cli, repository, "export", "--docs-root", "docs", "--format", "json")

    assert result.returncode == 0, result.stderr
    assert json.loads(result.stdout)["concepts"][0]["id"] == "system"
