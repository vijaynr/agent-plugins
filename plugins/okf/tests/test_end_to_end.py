from okf_core.export import export_bundle
from okf_core.initialization import initialize_bundle
from okf_core.validation import validate_bundle


def test_init_catalog_validates_and_exports(tmp_path):
    (tmp_path / "pyproject.toml").write_text("[project]\nname = 'demo'\n", encoding="utf-8")
    docs = tmp_path / "docs"

    proposal = initialize_bundle(tmp_path, docs)
    assert proposal.conflicts == []

    validation = validate_bundle(docs)
    assert validation.errors == []

    exported = export_bundle(docs)
    assert exported["concepts"]
    assert any(item["id"] == "architecture/system" for item in exported["concepts"])
