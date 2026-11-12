from okf_core.ingestion import ingest_text


def test_ingest_text_writes_decision_concept_and_catalog_updates(tmp_path):
    docs = tmp_path / "docs"
    docs.mkdir()
    (docs / "index.md").write_text("# Catalog\n", encoding="utf-8")

    result = ingest_text(
        docs,
        "We decided to use repository-local OKF files because they are portable.",
        source_label="conversation",
    )

    assert "decisions/conversation.md" in result.files
    concept = (docs / "decisions/conversation.md").read_text(encoding="utf-8")
    assert "type: Architecture Decision" in concept
    assert "source_trust: untrusted" in concept
    assert "```text" in concept
    assert "portable" in concept
    assert "decisions/conversation.md" in (docs / "index.md").read_text(encoding="utf-8")
    assert result.conflicts == []


def test_ingest_text_warns_for_likely_duplicate(tmp_path):
    docs = tmp_path / "docs"
    docs.mkdir()
    (docs / "decisions").mkdir()
    (docs / "decisions" / "conversation.md").write_text(
        "---\ntype: Architecture Decision\ntitle: Conversation\n---\n", encoding="utf-8"
    )

    result = ingest_text(docs, "We decided to use this approach.", source_label="conversation")

    assert any("duplicate" in warning.lower() for warning in result.warnings)
