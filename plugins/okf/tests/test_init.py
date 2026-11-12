from pathlib import Path

import pytest

from okf_core.initialization import initialize_bundle


def test_initialize_bundle_writes_architecture_decision_and_gotcha_concepts(tmp_path):
    (tmp_path / "pyproject.toml").write_text("[project]\nname = 'demo'\n", encoding="utf-8")
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "main.py").write_text("print('hello')\n", encoding="utf-8")
    docs = tmp_path / "docs"

    result = initialize_bundle(tmp_path, docs)

    assert set(result.files) >= {
        "index.md",
        "log.md",
        "architecture/system.md",
        "decisions/initial-conventions.md",
        "gotchas/repository-workflow.md",
    }
    assert (docs / "architecture/system.md").is_file()
    assert "pyproject.toml" in (docs / "architecture/system.md").read_text(encoding="utf-8")


def test_initialize_bundle_rejects_docs_outside_repository(tmp_path):
    with pytest.raises(ValueError, match="inside"):
        initialize_bundle(tmp_path, tmp_path.parent / "docs")


def test_initialize_bundle_preserves_existing_docs_and_reports_conflicts(tmp_path):
    docs = tmp_path / "docs"
    docs.mkdir()
    (docs / "index.md").write_text("# Existing docs\n", encoding="utf-8")

    result = initialize_bundle(tmp_path, docs)

    assert "index.md" in result.conflicts
    assert (docs / "index.md").read_text(encoding="utf-8") == "# Existing docs\n"


def test_initialize_bundle_rejects_symlinked_target_directory(tmp_path):
    docs = tmp_path / "docs"
    docs.mkdir()
    outside = tmp_path / "outside"
    outside.mkdir()
    try:
        (docs / "architecture").symlink_to(outside, target_is_directory=True)
    except (OSError, NotImplementedError):
        pytest.skip("symlinks are unavailable")

    with pytest.raises(ValueError, match="symlink"):
        initialize_bundle(tmp_path, docs)
