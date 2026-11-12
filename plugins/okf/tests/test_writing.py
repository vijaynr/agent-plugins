import pytest

from okf_core.writing import write_files


def test_write_files_reports_conflicts_without_partial_writes(tmp_path):
    docs = tmp_path / "docs"
    docs.mkdir()
    (docs / "existing.md").write_text("old\n", encoding="utf-8")

    result = write_files(docs, {"existing.md": "new\n", "new.md": "new\n"})

    assert result.conflicts == ["existing.md"]
    assert (docs / "existing.md").read_text(encoding="utf-8") == "old\n"
    assert not (docs / "new.md").exists()


def test_write_files_rejects_symlinked_target_directory(tmp_path):
    docs = tmp_path / "docs"
    docs.mkdir()
    outside = tmp_path / "outside"
    outside.mkdir()
    try:
        (docs / "links").symlink_to(outside, target_is_directory=True)
    except (OSError, NotImplementedError):
        pytest.skip("symlinks are unavailable")

    with pytest.raises(ValueError, match="symlink"):
        write_files(docs, {"links/escape.md": "escape\n"})
