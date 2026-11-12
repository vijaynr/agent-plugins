from pathlib import Path

from okf_core.parser import parse_document
from okf_core.validation import validate_bundle


def test_parse_document_preserves_frontmatter_and_body():
    document = parse_document(
        Path("architecture/system.md"),
        """---
type: Architecture
title: System
 tags: [backend, api]
---

# Overview

The service handles requests.
""".replace(" tags:", "tags:")
    )

    assert document.frontmatter["type"] == "Architecture"
    assert document.frontmatter["tags"] == ["backend", "api"]
    assert "# Overview" in document.body


def test_parse_document_supports_block_lists_and_multiline_values():
    document = parse_document(
        Path("concept.md"),
        "---\ntype: Reference\ntags:\n  - architecture\n  - api\ndescription: |\n  first line\n  second line\n---\nbody\n",
    )

    assert document.frontmatter["tags"] == ["architecture", "api"]
    assert document.frontmatter["description"] == "first line\nsecond line\n"


def test_validate_bundle_accepts_reserved_files_and_reports_broken_links(tmp_path):
    (tmp_path / "index.md").write_text(
        "# Architecture\n\n* [System](architecture/system.md) - Main system\n",
        encoding="utf-8",
    )
    (tmp_path / "log.md").write_text("# Directory Update Log\n", encoding="utf-8")
    (tmp_path / "architecture").mkdir()
    (tmp_path / "architecture" / "system.md").write_text(
        "---\ntype: Architecture\n---\nSee [missing](/architecture/missing.md).\n",
        encoding="utf-8",
    )

    result = validate_bundle(tmp_path)

    assert result.errors == []
    assert any("missing.md" in warning for warning in result.warnings)


def test_validate_bundle_warns_for_links_outside_bundle(tmp_path):
    (tmp_path / "concept.md").write_text(
        "---\ntype: Reference\n---\nSee [outside](../outside.md).\n", encoding="utf-8"
    )

    result = validate_bundle(tmp_path)

    assert result.errors == []
    assert any("outside" in warning for warning in result.warnings)


def test_validate_bundle_rejects_concept_without_type(tmp_path):
    (tmp_path / "broken.md").write_text("---\ntitle: Broken\n---\n", encoding="utf-8")

    result = validate_bundle(tmp_path)

    assert any("type" in error for error in result.errors)
