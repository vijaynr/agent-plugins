import json

from okf_core.export import export_bundle


def test_export_bundle_contains_concepts_metadata_and_links(tmp_path):
    (tmp_path / "architecture").mkdir()
    (tmp_path / "architecture" / "system.md").write_text(
        "---\ntype: Architecture\ntitle: System\ncustom: retained\n---\nSee [decision](/decisions/choice.md).\n",
        encoding="utf-8",
    )
    (tmp_path / "decisions").mkdir()
    (tmp_path / "decisions" / "choice.md").write_text("---\ntype: Architecture Decision\n---\n", encoding="utf-8")
    (tmp_path / "index.md").write_text("# Catalog\n", encoding="utf-8")

    result = export_bundle(tmp_path)
    payload = json.loads(json.dumps(result))

    assert [item["id"] for item in payload["concepts"]] == ["architecture/system", "decisions/choice"]
    assert payload["concepts"][0]["metadata"]["custom"] == "retained"
    assert payload["concepts"][0]["links"] == ["/decisions/choice.md"]
    assert payload["warnings"] == []
