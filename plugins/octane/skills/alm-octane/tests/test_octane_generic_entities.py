"""Generic commands through real CLI dispatch and a fake HTTP boundary."""
from __future__ import annotations

import json
import sys
from typing import Any

import pytest

from test_octane_credential_config import (
    SERVICE_NAME, SENTINEL_SECRET, isolated_runtime, load_script,
    relocated_skill, write_profile,
)


class Response:
    def __init__(self, body: Any, status: int = 200):
        self.body = body
        self.status_code = status
        self.ok = 200 <= status < 300
        self.headers = {"content-type": "application/json"}
        self.text = json.dumps(body)

    def json(self):
        return self.body


class QueueSession:
    def __init__(self):
        self.responses = []
        self.calls = []

    def request(self, **kwargs):
        self.calls.append(kwargs)
        assert self.responses, f"Unexpected HTTP request: {kwargs['method']} {kwargs['url']}"
        response = self.responses.pop(0)
        if isinstance(response, Exception):
            raise response
        return response


@pytest.fixture
def generic_client(tmp_path, monkeypatch, isolated_runtime):
    config_home, keyring = isolated_runtime
    write_profile(config_home)
    keyring.passwords[(SERVICE_NAME, "client-id")] = SENTINEL_SECRET
    client = load_script(relocated_skill(tmp_path, "generic"), "octane_client", monkeypatch)
    session = QueueSession()
    monkeypatch.setattr(client, "get_session", lambda: session)
    return client, session


def invoke(client, monkeypatch, capsys, *arguments):
    monkeypatch.setattr(sys, "argv", ["octane_client.py", *arguments])
    code = 0
    try:
        client.main()
    except SystemExit as exc:
        code = exc.code
    output = capsys.readouterr()
    return code, json.loads(output.out), output.err


def queue_metadata(session, *, name="defect", collection="defects", fields=None, methods=None):
    session.responses.extend([
        Response({"data": [{"name": name, "features": [{"name": "rest", "url": collection,
            "methods": methods or ["GET", "POST", "PUT"]}]}]}),
        Response({"data": fields if fields is not None else [{"name": "name", "field_type": "string"}]}),
    ])


@pytest.mark.parametrize("body", [{"data": [], "total_count": 0}, {"data": [{"id": "42"}], "total_count": 91, "exceeds_total_count": False}])
def test_get_entities_native_query_sort_and_page(generic_client, monkeypatch, capsys, body):
    client, session = generic_client
    queue_metadata(session)
    session.responses.append(Response(body))
    query = "name EQ ^a\\\"b^;id GT 2"
    code, result, _ = invoke(client, monkeypatch, capsys, "get-entities", "--entity-type", "defect",
        "--query", query, "--fields", "id,name", "--order-by=-name,id", "--limit", "20", "--offset", "40")
    assert code == 0 and result["data"] == body
    assert result["pagination"] == {"limit": 20, "offset": 40}
    assert session.calls[-1]["params"] == {"query": f'"{query}"', "fields": "id,name", "order_by": "-name,id", "limit": 20, "offset": 40}
    assert len(session.calls) == 3


def test_get_entities_keyword_search_uses_json_not_bk(generic_client, monkeypatch, capsys):
    client, session = generic_client
    queue_metadata(session, name="work_item", collection="work_items")
    session.responses.append(Response({"data": []}))
    text = 'login "fails" & timeout'
    code, result, _ = invoke(client, monkeypatch, capsys, "get-entities", "--entity-type", "work_items", "--search", text)
    assert code == 0
    params = session.calls[-1]["params"]
    assert json.loads(params["text_search"]) == {"type": "global", "text": text}
    assert "query" not in params and params["limit"] == 50 and params["offset"] == 0


@pytest.mark.parametrize("arguments", [("--limit", "0"), ("--offset", "-1"), ("--query", '"id EQ 2"'), ("--fields", "id,{bad}"), ("--order-by", "id?evil")])
def test_get_entities_invalid_inputs_never_call_http(generic_client, monkeypatch, capsys, arguments):
    client, session = generic_client
    code, result, _ = invoke(client, monkeypatch, capsys, "get-entities", "--entity-type", "defects", *arguments)
    assert code != 0 and result["ok"] is False and session.calls == []


def test_get_entities_rejects_search_on_other_collections(generic_client, monkeypatch, capsys):
    client, session = generic_client
    code, result, _ = invoke(client, monkeypatch, capsys, "get-entities", "--entity-type", "defects", "--search", "login")
    assert code != 0 and "work_items" in result["error"] and session.calls == []


def test_get_entities_rejects_explicitly_unsortable_field(generic_client, monkeypatch, capsys):
    client, session = generic_client
    queue_metadata(session, fields=[{"name": "name", "sortable": False}])
    code, result, _ = invoke(client, monkeypatch, capsys, "get-entities", "--entity-type", "defects", "--order-by", "name")
    assert code != 0 and len(session.calls) == 2


@pytest.mark.parametrize("text", ['[]', '{}', '{bad', '{"data":[{}]}', '{"id":"42","name":"new"}', '{"name":NaN}', '{"name":"a","name":"b"}'])
def test_create_entity_invalid_json_causes_no_http(generic_client, monkeypatch, capsys, tmp_path, text):
    client, session = generic_client
    path = tmp_path / "payload.json"
    path.write_text(text, encoding="utf-8")
    code, result, _ = invoke(client, monkeypatch, capsys, "create-entity", "--entity-type", "defect", "--data-file", str(path))
    assert code != 0 and result["ok"] is False and session.calls == []


def test_create_entity_missing_file_causes_no_http(generic_client, monkeypatch, capsys, tmp_path):
    client, session = generic_client
    code, result, _ = invoke(client, monkeypatch, capsys, "create-entity", "--entity-type", "defect", "--data-file", str(tmp_path / "absent.json"))
    assert code != 0 and session.calls == []


def test_create_entity_preserves_payload_and_verifies_relationship_identity(generic_client, monkeypatch, capsys, tmp_path):
    client, session = generic_client
    fields = {"name": "**Raw markdown**", "owner": {"type": "workspace_user", "id": "7"}}
    path = tmp_path / "payload.json"
    path.write_text(json.dumps(fields), encoding="utf-8")
    queue_metadata(session, fields=[{"name": "name", "field_type": "string"},
        {"name": "owner", "field_type": "reference", "field_type_data": {"targets": [{"type": "workspace_user"}], "multiple": False}}])
    session.responses.extend([Response({"data": [{"id": "42"}]}, 201),
        Response({"id": "42", "name": fields["name"], "owner": {"id": 7, "type": "workspace_user", "name": "Expanded"}})])
    code, result, _ = invoke(client, monkeypatch, capsys, "create-entity", "--entity-type", "defect", "--data-file", str(path))
    assert code == 0 and result["mutation"]["outcome"] == "succeeded"
    assert result["verification"]["matched"] is True
    assert session.calls[2]["json"] == {"data": [fields]}
    assert session.calls[3]["url"].endswith("/defects/42")
    assert [c["method"] for c in session.calls].count("POST") == 1


@pytest.mark.parametrize("verification", [Response({}, 403), Response({"id": "42", "name": "different"}), Response({"id": "99", "name": "new"}), Response({"id": "42"})])
def test_create_entity_verification_failure_preserves_mutation(generic_client, monkeypatch, capsys, tmp_path, verification):
    client, session = generic_client
    path = tmp_path / "payload.json"
    path.write_text('{"name":"new"}', encoding="utf-8")
    queue_metadata(session)
    session.responses.extend([Response({"data": [{"id": "42"}]}, 201), verification])
    code, result, _ = invoke(client, monkeypatch, capsys, "create-entity", "--entity-type", "defect", "--data-file", str(path))
    assert code != 0 and result["mutation"]["outcome"] == "succeeded"
    assert result["verification"]["matched"] is False
    assert "do not retry" in result["error"].lower()
    assert result["verification"]["status"] == verification.status_code
    assert result["verification"]["url"].endswith("/defects/42")
    assert [c["method"] for c in session.calls].count("POST") == 1


@pytest.mark.parametrize("mutation", [Response({"data": []}, 201), Response({"data": [{"id": "42"}]}, 200), Response({"data": [{"id": "42"}]}, 202), RuntimeError("connection lost"), Response({"error_code": "invalid"}, 400)])
def test_create_entity_uncertain_or_rejected_mutation_is_not_replayed(generic_client, monkeypatch, capsys, tmp_path, mutation):
    client, session = generic_client
    path = tmp_path / "payload.json"
    path.write_text('{"name":"new"}', encoding="utf-8")
    queue_metadata(session)
    session.responses.append(mutation)
    code, result, _ = invoke(client, monkeypatch, capsys, "create-entity", "--entity-type", "defect", "--data-file", str(path))
    assert code != 0 and result["mutation"]["outcome"] in {"unknown", "rejected"}
    assert len(session.calls) == 3


@pytest.mark.parametrize("reference", ["7", {}, {"id": True}, {"id": "a/b"}, {"id": "7", "type": "unexpected"}])
def test_create_entity_invalid_reference_blocks_post(generic_client, monkeypatch, capsys, tmp_path, reference):
    client, session = generic_client
    path = tmp_path / "payload.json"
    path.write_text(json.dumps({"owner": reference}), encoding="utf-8")
    queue_metadata(session, fields=[{"name": "owner", "field_type": "reference", "field_type_data": {"targets": [{"type": "workspace_user"}], "multiple": False}}])
    code, result, _ = invoke(client, monkeypatch, capsys, "create-entity", "--entity-type", "defect", "--data-file", str(path))
    assert code != 0 and result["ok"] is False
    assert all(call["method"] == "GET" for call in session.calls)


@pytest.mark.parametrize("actual,matched", [
    ({"data": [{"id": "7", "type": "user_tag"}]}, False),
    ([{"id": "7", "type": "user_tag"}], False),
    ({"data": [{"id": "7", "type": "user_tag"}], "total_count": 2}, False),
    ({"data": [{"id": "7", "type": "user_tag"}], "total_count": 1, "exceeds_total_count": True}, False),
    ({"data": [{"id": "7", "type": "user_tag"}], "total_count": 1}, True),
])
def test_create_entity_multi_reference_requires_complete_readback(generic_client, monkeypatch, capsys, tmp_path, actual, matched):
    client, session = generic_client
    path = tmp_path / "payload.json"
    path.write_text('{"user_tags":{"data":[{"id":"7","type":"user_tag"}]}}', encoding="utf-8")
    queue_metadata(session, fields=[{"name": "user_tags", "field_type": "reference", "field_type_data": {"targets": [{"type": "user_tag"}], "multiple": True}}])
    session.responses.extend([Response({"data": [{"id": "42"}]}, 201), Response({"id": "42", "user_tags": actual})])
    code, result, _ = invoke(client, monkeypatch, capsys, "create-entity", "--entity-type", "defect", "--data-file", str(path))
    assert (code == 0) == matched
    assert result["verification"]["matched"] is matched


@pytest.mark.parametrize("caller_stamp", [None, 2])
def test_update_entity_partial_fields_preserve_lock_intent(generic_client, monkeypatch, capsys, tmp_path, caller_stamp):
    client, session = generic_client
    fields = {"name": "changed"}
    if caller_stamp is not None:
        fields["client_lock_stamp"] = caller_stamp
    path = tmp_path / "update.json"
    path.write_text(json.dumps(fields), encoding="utf-8")
    queue_metadata(session, fields=[{"name": "name", "field_type": "string"}, {"name": "client_lock_stamp", "field_type": "integer"}])
    if caller_stamp is None:
        session.responses.append(Response({"id": "42", "client_lock_stamp": 12}))
    session.responses.extend([Response({"id": "42"}), Response({"id": "42", "name": "changed", "client_lock_stamp": 13})])
    code, result, _ = invoke(client, monkeypatch, capsys, "update-entity", "--entity-type", "defect", "--entity-id", "42", "--data-file", str(path))
    assert code == 0 and result["verification"]["matched"] is True
    put = next(call for call in session.calls if call["method"] == "PUT")
    assert put["json"] == {"name": "changed", "client_lock_stamp": 12 if caller_stamp is None else 2}
    assert result["concurrency"]["source"] == ("current" if caller_stamp is None else "caller")
    assert [call["method"] for call in session.calls].count("PUT") == 1


@pytest.mark.parametrize("entity_type,collection", [
    ("defect", "defects"), ("story", "stories"),
    ("feature", "features"), ("test", "tests"),
])
@pytest.mark.parametrize("input_key", ["security_impact", "SECURITY-IMPACT", "business_priority"])
def test_update_entity_resolves_normalized_labels_and_logical_names_from_metadata(
    generic_client, monkeypatch, capsys, tmp_path, entity_type, collection, input_key,
):
    client, session = generic_client
    path = tmp_path / "update.json"
    path.write_text(json.dumps({input_key: "changed"}), encoding="utf-8")
    queue_metadata(session, name=entity_type, collection=collection, fields=[{
        "name": "workspace_custom_17", "label": "Security Impact",
        "logical_name": "business_priority", "field_type": "string",
    }])
    session.responses.extend([
        Response({"id": "42"}), Response({"id": "42", "workspace_custom_17": "changed"}),
    ])
    code, result, _ = invoke(client, monkeypatch, capsys, "update-entity",
        "--entity-type", entity_type, "--entity-id", "42", "--data-file", str(path))
    puts = [call for call in session.calls if call["method"] == "PUT"]
    assert len(puts) == 1
    assert puts[0]["url"].endswith(f"/{collection}/42")
    assert puts[0]["json"] == {"workspace_custom_17": "changed"}
    assert code == 0 and result["verification"]["matched"] is True
    assert result["verification"]["fields"] == {"workspace_custom_17": "matched"}
    assert session.calls[-1]["params"]["fields"] == "id,workspace_custom_17"
    assert session.calls[1]["params"]["query"] == f'"entity_name EQ ^{entity_type}^"'


@pytest.mark.parametrize("alias_property", ["label", "logical_name"])
def test_update_entity_exact_api_name_wins_over_other_fields_aliases(
    generic_client, monkeypatch, capsys, tmp_path, alias_property,
):
    client, session = generic_client
    path = tmp_path / "update.json"
    path.write_text('{"priority":"changed"}', encoding="utf-8")
    queue_metadata(session, fields=[
        {"name": "other_custom_field", alias_property: "priority"},
        {"name": "priority", "field_type": "string"},
    ])
    session.responses.extend([Response({"id": "42"}), Response({"id": "42", "priority": "changed"})])
    code, result, _ = invoke(client, monkeypatch, capsys, "update-entity",
        "--entity-type", "defect", "--entity-id", "42", "--data-file", str(path))
    assert code == 0 and result["verification"]["matched"] is True
    assert next(call for call in session.calls if call["method"] == "PUT")["json"] == {"priority": "changed"}


@pytest.mark.parametrize("definitions,input_key", [
    pytest.param([], "name", id="empty-metadata"),
    pytest.param([{"name": "name"}], "missing_field", id="unknown-field"),
    pytest.param([
        {"name": "custom_a", "label": "Security Impact"},
        {"name": "custom_b", "label": "Security-Impact"},
    ], "security_impact", id="ambiguous-normalized-label"),
    pytest.param([
        {"name": "custom_a", "logical_name": "priority"},
        {"name": "custom_b", "logical_name": "priority"},
    ], "priority", id="ambiguous-logical-name"),
    pytest.param([{"name": "custom_a", "editable": False}], "custom_a", id="read-only-api-name"),
    pytest.param([
        {"name": "custom_a", "label": "Security Impact", "editable": False},
    ], "security_impact", id="read-only-label"),
])
def test_update_entity_unresolved_or_read_only_metadata_fields_block_put(
    generic_client, monkeypatch, capsys, tmp_path, definitions, input_key,
):
    client, session = generic_client
    path = tmp_path / "update.json"
    path.write_text(json.dumps({input_key: "changed"}), encoding="utf-8")
    queue_metadata(session, fields=definitions)
    # Supply successful mutation/readback responses so a forbidden PUT cannot fail accidentally.
    session.responses.extend([Response({"id": "42"}), Response({"id": "42", input_key: "changed"})])
    code, result, _ = invoke(client, monkeypatch, capsys, "update-entity",
        "--entity-type", "defect", "--entity-id", "42", "--data-file", str(path))
    assert all(call["method"] == "GET" for call in session.calls)
    assert code != 0 and result["ok"] is False


@pytest.mark.parametrize("failure", [
    Response({}, 403), RuntimeError("metadata unavailable"), Response({"data": "invalid"}),
])
def test_update_entity_field_metadata_failure_blocks_put(
    generic_client, monkeypatch, capsys, tmp_path, failure,
):
    client, session = generic_client
    path = tmp_path / "update.json"
    path.write_text('{"name":"changed"}', encoding="utf-8")
    queue_metadata(session)
    session.responses[-1] = failure
    session.responses.extend([Response({"id": "42"}), Response({"id": "42", "name": "changed"})])
    code, result, _ = invoke(client, monkeypatch, capsys, "update-entity",
        "--entity-type", "defect", "--entity-id", "42", "--data-file", str(path))
    assert all(call["method"] == "GET" for call in session.calls)
    assert code != 0 and result["ok"] is False


@pytest.mark.parametrize("stamp", [0, 2, None, True, "2", -1])
def test_update_entity_resolved_alias_still_validates_caller_lock_stamp(
    generic_client, monkeypatch, capsys, tmp_path, stamp,
):
    client, session = generic_client
    path = tmp_path / "update.json"
    path.write_text(json.dumps({"security_impact": "changed", "client_lock_stamp": stamp}), encoding="utf-8")
    queue_metadata(session, fields=[
        {"name": "custom_a", "label": "Security Impact"},
        {"name": "client_lock_stamp", "field_type": "integer", "editable": False},
    ])
    session.responses.extend([Response({"id": "42"}), Response({"id": "42", "custom_a": "changed"})])
    code, result, _ = invoke(client, monkeypatch, capsys, "update-entity",
        "--entity-type", "defect", "--entity-id", "42", "--data-file", str(path))
    puts = [call for call in session.calls if call["method"] == "PUT"]
    if type(stamp) is int and stamp >= 0:
        assert len(puts) == 1 and puts[0]["json"] == {"custom_a": "changed", "client_lock_stamp": stamp}
        assert code == 0 and result["verification"]["matched"] is True
        assert result["concurrency"] == {"protected": True, "source": "caller"}
        assert len(session.calls) == 4  # Caller stamps must not be silently refreshed.
    else:
        assert puts == [] and code != 0 and result["ok"] is False
        assert "client_lock_stamp" in result["error"]


@pytest.mark.parametrize("preread", [Response({}, 403), Response({"id": "42"}), Response({"id": "99", "client_lock_stamp": 2})])
def test_update_entity_failed_lock_read_prevents_put(generic_client, monkeypatch, capsys, tmp_path, preread):
    client, session = generic_client
    path = tmp_path / "update.json"
    path.write_text('{"name":"changed"}', encoding="utf-8")
    queue_metadata(session, fields=[{"name": "client_lock_stamp"}, {"name": "name"}])
    session.responses.append(preread)
    code, result, _ = invoke(client, monkeypatch, capsys, "update-entity", "--entity-type", "defect", "--entity-id", "42", "--data-file", str(path))
    assert code != 0 and result["mutation"]["outcome"] == "not_attempted"
    assert all(call["method"] == "GET" for call in session.calls)


@pytest.mark.parametrize("mutation", [Response({"error_code": "platform.version_conflict"}, 500), Response({"error_code": "invalid.transition"}, 409), RuntimeError("lost response"), Response({"id": "42"}, 202)])
def test_update_entity_never_refreshes_or_replays_after_failure(generic_client, monkeypatch, capsys, tmp_path, mutation):
    client, session = generic_client
    path = tmp_path / "update.json"
    path.write_text('{"name":"changed","client_lock_stamp":2}', encoding="utf-8")
    queue_metadata(session, fields=[{"name": "client_lock_stamp"}, {"name": "name"}])
    session.responses.append(mutation)
    code, result, _ = invoke(client, monkeypatch, capsys, "update-entity", "--entity-type", "defect", "--entity-id", "42", "--data-file", str(path))
    assert code != 0 and result["mutation"]["outcome"] in {"unknown", "rejected"}
    assert len(session.calls) == 3 and session.calls[-1]["json"]["client_lock_stamp"] == 2


@pytest.mark.parametrize("fields", [{"id": "99", "name": "new"}, {"id": "42"}, {"client_lock_stamp": 2}])
def test_update_entity_rejects_conflicting_or_empty_updates(generic_client, monkeypatch, capsys, tmp_path, fields):
    client, session = generic_client
    path = tmp_path / "update.json"
    path.write_text(json.dumps(fields), encoding="utf-8")
    code, result, _ = invoke(client, monkeypatch, capsys, "update-entity", "--entity-type", "defect", "--entity-id", "42", "--data-file", str(path))
    assert code != 0 and session.calls == []


@pytest.mark.parametrize("stamp", [None, True, "2", -1])
def test_update_entity_invalid_caller_stamp_never_puts(generic_client, monkeypatch, capsys, tmp_path, stamp):
    client, session = generic_client
    path = tmp_path / "update.json"
    path.write_text(json.dumps({"name": "changed", "client_lock_stamp": stamp}), encoding="utf-8")
    queue_metadata(session, fields=[{"name": "name"}, {"name": "client_lock_stamp"}])
    code, result, _ = invoke(client, monkeypatch, capsys, "update-entity", "--entity-type", "defect", "--entity-id", "42", "--data-file", str(path))
    assert code != 0 and all(call["method"] == "GET" for call in session.calls)


def test_update_entity_failed_verification_does_not_hide_successful_put(generic_client, monkeypatch, capsys, tmp_path):
    client, session = generic_client
    path = tmp_path / "update.json"
    path.write_text('{"name":"changed"}', encoding="utf-8")
    queue_metadata(session)
    session.responses.extend([Response({"id": "42"}), Response({}, 403)])
    code, result, _ = invoke(client, monkeypatch, capsys, "update-entity", "--entity-type", "defect", "--entity-id", "42", "--data-file", str(path))
    assert code != 0 and result["mutation"]["outcome"] == "succeeded"
    assert result["verification"]["status"] == 403 and result["verification"]["matched"] is False
    assert [call["method"] for call in session.calls].count("PUT") == 1


def test_update_entity_caller_stamp_without_support_is_rejected(generic_client, monkeypatch, capsys, tmp_path):
    client, session = generic_client
    path = tmp_path / "update.json"
    path.write_text('{"name":"changed","client_lock_stamp":2}', encoding="utf-8")
    queue_metadata(session)
    code, result, _ = invoke(client, monkeypatch, capsys, "update-entity", "--entity-type", "defect", "--entity-id", "42", "--data-file", str(path))
    assert code != 0 and "unavailable" in result["error"]
    assert all(call["method"] == "GET" for call in session.calls)


def test_update_entity_no_stamp_support_is_explicit(generic_client, monkeypatch, capsys, tmp_path):
    client, session = generic_client
    path = tmp_path / "update.json"
    path.write_text('{"id":"42","name":"changed"}', encoding="utf-8")
    queue_metadata(session)
    session.responses.extend([Response({"id": "42"}), Response({"id": "42", "name": "changed"})])
    code, result, _ = invoke(client, monkeypatch, capsys, "update-entity", "--entity-type", "defect", "--entity-id", "42", "--data-file", str(path))
    assert code == 0 and result["concurrency"] == {"protected": False, "source": "unavailable"}
    assert session.calls[2]["json"] == {"name": "changed"}


@pytest.mark.parametrize("failure", [
    Response({"description": SENTINEL_SECRET, "stack_trace": "internal traceback", "error_code": "platform.version_conflict"}, 500),
    RuntimeError(f"transport echoed {SENTINEL_SECRET}"),
    Response({"error_code": {"unexpected": SENTINEL_SECRET}}, 500),
])
def test_generic_errors_omit_secrets_and_stack_traces(generic_client, monkeypatch, capsys, failure):
    client, session = generic_client
    session.responses.append(failure)
    code, result, _ = invoke(client, monkeypatch, capsys, "get-entity", "--entity-type", "defects", "--entity-id", "42")
    assert code != 0
    serialized = json.dumps(result)
    assert SENTINEL_SECRET not in serialized and "stack_trace" not in serialized
    assert "internal traceback" not in serialized
    if isinstance(failure, Response):
        expected_code = "platform.version_conflict" if failure.body.get("error_code") == "platform.version_conflict" else "OCTANE_REQUEST_FAILED"
        assert result["error_code"] == expected_code


@pytest.mark.parametrize("record", [{"id": "99"}, {"data": []}, [], "not a record"])
def test_get_entity_rejects_malformed_or_wrong_target(generic_client, monkeypatch, capsys, record):
    client, session = generic_client
    session.responses.append(Response(record))
    code, result, _ = invoke(client, monkeypatch, capsys, "get-entity", "--entity-type", "defects", "--entity-id", "42")
    assert code != 0 and result["ok"] is False


def test_get_entities_rejects_nonrecord_items(generic_client, monkeypatch, capsys):
    client, session = generic_client
    queue_metadata(session)
    session.responses.append(Response({"data": [42]}))
    code, result, _ = invoke(client, monkeypatch, capsys, "get-entities", "--entity-type", "defects")
    assert code != 0 and result["ok"] is False


def test_get_entities_empty_search_is_local_failure(generic_client, monkeypatch, capsys):
    client, session = generic_client
    code, result, _ = invoke(client, monkeypatch, capsys, "get-entities", "--entity-type", "work_items", "--search", "   ")
    assert code != 0 and session.calls == []


@pytest.mark.parametrize("metadata,expected,actual,matched", [
    ({"field_type": "boolean"}, False, 0, False),
    ({"field_type": "string", "required": False}, "", None, True),
    ({"field_type": "string"}, "", None, False),
    ({"field_type": "string", "selectable": False}, "x", "x", False),
])
def test_create_entity_verification_is_type_and_capability_aware(generic_client, monkeypatch, capsys, tmp_path, metadata, expected, actual, matched):
    client, session = generic_client
    path = tmp_path / "payload.json"
    path.write_text(json.dumps({"name": expected}), encoding="utf-8")
    queue_metadata(session, fields=[{"name": "name", **metadata}])
    session.responses.extend([Response({"data": [{"id": "42"}]}, 201), Response({"id": "42", "name": actual})])
    code, result, _ = invoke(client, monkeypatch, capsys, "create-entity", "--entity-type", "defects", "--data-file", str(path))
    assert (code == 0) == matched
    assert result["verification"]["matched"] is matched


def test_create_entity_unsupported_method_never_posts(generic_client, monkeypatch, capsys, tmp_path):
    client, session = generic_client
    path = tmp_path / "payload.json"
    path.write_text('{"name":"new"}', encoding="utf-8")
    queue_metadata(session, methods=["GET"])
    code, result, _ = invoke(client, monkeypatch, capsys, "create-entity", "--entity-type", "defects", "--data-file", str(path))
    assert code != 0 and len(session.calls) == 1


def test_legacy_update_defect_keeps_phase_normalization_and_stamp(generic_client, monkeypatch, capsys):
    client, session = generic_client
    session.responses.append(Response({"id": "42", "client_lock_stamp": 3}))
    queue_metadata(session, fields=[
        {"name": "phase", "field_type": "reference", "field_type_data": {"targets": [{"type": "phase"}]}},
        {"name": "client_lock_stamp", "field_type": "integer"},
    ])
    session.responses.extend([Response({"id": "42"}),
        Response({"id": "42", "phase": {"id": "phase.defect.fixed", "type": "phase"}}),
        Response({"id": "42", "phase": {"id": "phase.defect.fixed"}})])
    code, result, _ = invoke(client, monkeypatch, capsys, "update-defect", "--entity-id", "42", "--phase", "fixed")
    assert code == 0
    assert session.calls[3]["json"] == {"phase": {"type": "phase", "id": "phase.defect.fixed"}, "client_lock_stamp": 3}
    assert result["verified"]["id"] == "42"


@pytest.mark.parametrize("non_json", [False, True])
@pytest.mark.parametrize("operation,status", [("create-entity", 201), ("update-entity", 200)])
@pytest.mark.parametrize("body", [{"raw": SENTINEL_SECRET}, SENTINEL_SECRET, {"stack_trace": SENTINEL_SECRET}])
def test_uncertain_mutation_drops_untrusted_response_body(generic_client, monkeypatch, capsys, tmp_path, operation, status, body, non_json):
    client, session = generic_client
    path = tmp_path / "payload.json"
    path.write_text('{"name":"changed"}', encoding="utf-8")
    queue_metadata(session)
    response = Response(body, status)
    if non_json:
        response.headers = {"content-type": "text/html"}
    session.responses.append(response)
    args = [operation, "--entity-type", "defects", "--data-file", str(path)]
    if operation == "update-entity":
        args.extend(["--entity-id", "42"])
    code, result, _ = invoke(client, monkeypatch, capsys, *args)
    assert code != 0 and result["mutation"]["outcome"] == "unknown"
    assert SENTINEL_SECRET not in json.dumps(result)
    assert "data" not in result
    assert len(session.calls) == 3


def test_create_entity_malformed_verification_body_is_not_exposed(generic_client, monkeypatch, capsys, tmp_path):
    client, session = generic_client
    path = tmp_path / "payload.json"
    path.write_text('{"name":"changed"}', encoding="utf-8")
    queue_metadata(session)
    session.responses.extend([Response({"data": [{"id": "42"}]}, 201), Response({"raw": SENTINEL_SECRET})])
    code, result, _ = invoke(client, monkeypatch, capsys, "create-entity", "--entity-type", "defects", "--data-file", str(path))
    assert code != 0 and result["mutation"]["outcome"] == "succeeded"
    assert SENTINEL_SECRET not in json.dumps(result)


@pytest.mark.parametrize("entity_id", ["../42", "42%2fanything", "42?query=x", "42#fragment"])
def test_reusable_update_rejects_path_ids_before_requests(generic_client, entity_id):
    client, _ = generic_client
    calls = []
    def request(*args, **kwargs):
        calls.append(args)
        return {"ok": True, "data": {"data": []}}
    api = client.octane_generic.GenericAPI("https://example.test/api/shared_spaces/1/workspaces/2", request)
    with pytest.raises(client.octane_generic.GenericError):
        api.update_entity("defects", entity_id, {"name": "changed"})
    assert calls == []


def test_get_entity_returns_record_and_preserves_fields_and_scope(generic_client, monkeypatch, capsys):
    client, session = generic_client
    session.responses.append(Response({"id": "42", "name": "Example"}))
    code, result, stderr = invoke(client, monkeypatch, capsys, "get-entity",
        "--entity-type", "defect", "--entity-id", "42", "--fields", "id,name",
        "--workspace-id", "777", "--shared-space-id", "888")
    assert code == 0 and result["data"] == {"id": "42", "name": "Example"}
    assert stderr == ""
    assert session.calls[0]["url"].endswith("/shared_spaces/888/workspaces/777/defects/42")
    assert session.calls[0]["params"] == {"fields": "id,name"}


@pytest.mark.parametrize("flag,value", [
    ("--entity-type", "../defects"), ("--entity-type", "https://evil.test"),
    ("--entity-id", ".."),
    ("--entity-id", "a/b"), ("--entity-id", "a%2fb"),
    ("--entity-id", "x?fields=secret"), ("--entity-id", " x"),
    ("--workspace-id", "../777"), ("--shared-space-id", "a#b"),
])
def test_get_entity_rejects_unsafe_target_before_http(generic_client, monkeypatch, capsys, flag, value):
    client, session = generic_client
    args = {"--entity-type": "defect", "--entity-id": "42"}
    args[flag] = value
    code, result, _ = invoke(client, monkeypatch, capsys, "get-entity",
        *(item for pair in args.items() for item in pair))
    assert code != 0 and result["ok"] is False
    assert session.calls == []


@pytest.mark.parametrize("status", [401, 403, 404, 500])
def test_get_entity_http_failure_has_nonzero_exit(generic_client, monkeypatch, capsys, status):
    client, session = generic_client
    session.responses.append(Response({"error_code": "test.failure"}, status))
    code, result, _ = invoke(client, monkeypatch, capsys, "get-entity",
        "--entity-type", "defects", "--entity-id", "42")
    assert code != 0 and result["ok"] is False and result["status"] == status


def test_get_entity_legacy_adapter_keeps_printed_contract(generic_client, monkeypatch, capsys):
    client, session = generic_client
    session.responses.append(Response({"id": "42"}))
    code, result, _ = invoke(client, monkeypatch, capsys, "get-defect", "--entity-id", "42")
    assert code == 0 and result["data"] == {"id": "42"}
    assert "security_source_udf" in session.calls[0]["params"]["fields"]
