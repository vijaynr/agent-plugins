"""Metadata discovery keeps server capabilities distinct from local knowledge."""
import pytest

from test_octane_credential_config import isolated_runtime
from test_octane_generic_entities import Response, generic_client, invoke


def entity_type(name="defect", collection="defects", methods=None):
    return {"name": name, "label": name.title(), "features": [
        {"name": "rest", "url": collection, "methods": methods or ["GET", "POST", "PUT"]}
    ]}


@pytest.mark.parametrize("fields", [[], [{"name": "severity", "entity_name": "defect", "field_type": "reference", "required": True, "editable": True, "field_type_data": {"targets": [{"type": "list_node"}], "multiple": False}}]])
def test_field_metadata_preserves_attributes_without_pagination(generic_client, monkeypatch, capsys, fields):
    client, session = generic_client
    session.responses.extend([Response({"data": [entity_type()]}), Response({"data": fields})])
    code, result, _ = invoke(client, monkeypatch, capsys, "get-entity-field-metadata", "--entity-type", "defects")
    assert code == 0 and result["data"] == {"data": fields}
    assert session.calls[-1]["url"].endswith("/metadata/fields")
    assert session.calls[-1]["params"] == {"query": '\"entity_name EQ ^defect^\"', "limit": 5000}


@pytest.mark.parametrize("body,status", [({"error_code": "denied"}, 403), ({"data": [{"name": "name", "entity_name": "story"}]}, 200), ({"data": "bad"}, 200)])
def test_field_metadata_rejects_failure_or_wrong_context(generic_client, monkeypatch, capsys, body, status):
    client, session = generic_client
    session.responses.extend([Response({"data": [entity_type()]}), Response(body, status)])
    code, result, _ = invoke(client, monkeypatch, capsys, "get-entity-field-metadata", "--entity-type", "defect")
    assert code != 0 and result["ok"] is False
    assert len(session.calls) == 2


def test_filter_metadata_separates_documented_grammar_from_live_fields(generic_client, monkeypatch, capsys):
    client, session = generic_client
    fields = [{"name": "name", "field_type": "string", "filterable": True},
              {"name": "description", "field_type": "memo", "filterable": False}]
    session.responses.extend([Response({"data": [entity_type()]}), Response({"data": fields})])
    code, result, _ = invoke(client, monkeypatch, capsys, "get-filter-metadata", "--entity-type", "defect")
    assert code == 0
    grammar = result["data"]["grammar"]
    assert grammar["source"] == "documentation" and grammar["version"] == "26.1"
    assert grammar["url"].endswith("/query_Clause.htm")
    assert grammar["operators_by_type"]["boolean"] == ["EQ"]
    assert "BK" not in grammar["operators_by_type"]["string"]
    assert result["data"]["field_metadata"] == {"source": "workspace", "data": fields}
    assert len(session.calls) == 2
    assert session.calls[-1]["url"].endswith("/metadata/fields")


def test_filter_metadata_never_claims_workspace_fields_when_read_fails(generic_client, monkeypatch, capsys):
    client, session = generic_client
    session.responses.extend([Response({"data": [entity_type()]}), Response({}, 403)])
    code, result, _ = invoke(client, monkeypatch, capsys, "get-filter-metadata", "--entity-type", "defect")
    assert code != 0 and result["status"] == 403
    assert "grammar" not in result.get("data", {})


def test_entity_types_returns_server_metadata(generic_client, monkeypatch, capsys):
    client, session = generic_client
    body = {"data": [entity_type(), entity_type("person", "people")]}
    session.responses.append(Response(body))
    code, result, _ = invoke(client, monkeypatch, capsys, "get-entity-types")
    assert code == 0 and result["data"] == body
    assert session.calls[0]["url"].endswith("/metadata/entities")
    assert session.calls[0]["params"] == {}


@pytest.mark.parametrize("name", ["person", "people"])
def test_entity_types_mapping_resolves_irregular_collection(generic_client, monkeypatch, capsys, name):
    client, session = generic_client
    session.responses.extend([Response({"data": [entity_type("person", "people")]}), Response({"id": "7"})])
    code, result, _ = invoke(client, monkeypatch, capsys, "get-entity", "--entity-type", name, "--entity-id", "7")
    assert code == 0 and result["data"]["id"] == "7"
    assert session.calls[-1]["url"].endswith("/people/7")


@pytest.mark.parametrize("collection", ["https://evil.test", "../defects", "defects/42", "defects%2F42"])
def test_entity_types_rejects_malicious_rest_mapping(generic_client, monkeypatch, capsys, collection):
    client, session = generic_client
    session.responses.append(Response({"data": [entity_type("person", collection)]}))
    code, result, _ = invoke(client, monkeypatch, capsys, "get-entity", "--entity-type", "person", "--entity-id", "7")
    assert code != 0 and result["ok"] is False
    assert len(session.calls) == 1


def test_entity_types_unknown_collection_is_not_guessed(generic_client, monkeypatch, capsys):
    client, session = generic_client
    session.responses.append(Response({"data": []}))
    code, result, _ = invoke(client, monkeypatch, capsys, "get-entity", "--entity-type", "unknown_kind", "--entity-id", "7")
    assert code != 0 and "Unknown" in result["error"]
    assert len(session.calls) == 1


def test_entity_types_unsupported_method_never_reads_record(generic_client, monkeypatch, capsys):
    client, session = generic_client
    session.responses.append(Response({"data": [entity_type("person", "people", ["POST"])]}))
    code, result, _ = invoke(client, monkeypatch, capsys, "get-entity", "--entity-type", "person", "--entity-id", "7")
    assert code != 0 and len(session.calls) == 1


@pytest.mark.parametrize("body,status", [({"data": []}, 200), ({"error_code": "denied"}, 403)])
def test_entity_types_empty_and_failure_are_distinct(generic_client, monkeypatch, capsys, body, status):
    client, session = generic_client
    session.responses.append(Response(body, status))
    code, result, _ = invoke(client, monkeypatch, capsys, "get-entity-types")
    assert (code == 0) == (status == 200)
    assert result["status"] == status
