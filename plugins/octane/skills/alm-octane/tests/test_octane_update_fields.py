"""Convenience updates must use metadata resolution and verified, single writes."""
import json

import pytest

from test_octane_generic_entities import Response, generic_client
from test_octane_credential_config import SENTINEL_SECRET, isolated_runtime


COMMANDS = [
    ("update_feature", {"feature_id": "42", "name": "changed"}, "features", "name", "changed"),
    ("update_defect", {"defect_id": "42", "phase": "fixed"}, "defects", "phase", {"type": "phase", "id": "phase.defect.fixed"}),
    ("update_story", {"story_id": "42", "name": "changed"}, "stories", "name", "changed"),
    ("update_story_status", {"story_id": "42", "phase": "done"}, "stories", "phase", {"type": "phase", "id": "phase.story.done"}),
    ("update_feature_security", {"feature_id": "42", "security_assessment": "changed"}, "features", "security_assessment_udf", "changed"),
    ("delete_backlog_item", {"entity_id": "42"}, "work_items", "allow_delete_udf", True),
    ("add_tag", {"entity_id": "42", "tag_name": "tag"}, "work_items", "user_tags", {"data": [{"type": "user_tag", "id": "7"}]}),
]


def install_http(client, session, monkeypatch, collection, definitions, *, reject=False, mismatch=False):
    labels = {"security_assessment_udf": "Security Assessment", "allow_delete_udf": "Allow delete"}
    definitions = [dict(field) for field in definitions]
    for field in definitions:
        if field["name"] in labels:
            field.setdefault("label", labels[field["name"]])
    state = {"id": "42", "client_lock_stamp": 3}
    def request(**call):
        session.calls.append(call)
        method, url = call["method"], call["url"]
        if url.endswith("/metadata/entities"):
            return Response({"data": [{"name": collection.rstrip("s"), "features": [
                {"name": "rest", "url": collection, "methods": ["GET", "PUT"]}]}]})
        if "/metadata/" in url:
            return Response({"data": definitions})
        if url.endswith("/user_tags"):
            return Response({"data": [{"id": "7", "name": "tag"}]})
        if method == "PUT":
            if reject:
                return Response({"error_code": "required.acceptance_criteria", "stack_trace": "private"}, 400)
            state.update(call["json"])
            return Response({"id": "42"})
        if method == "DELETE":
            return Response({})
        assert method == "GET", call
        snapshot = dict(state)
        if mismatch and any(c["method"] == "PUT" for c in session.calls):
            snapshot = {"id": "42", "client_lock_stamp": 4}
        if isinstance(snapshot.get("user_tags"), dict):
            snapshot["user_tags"] = {**snapshot["user_tags"], "total_count": len(snapshot["user_tags"]["data"])}
        return Response(snapshot)
    monkeypatch.setattr(session, "request", request)
    client.configure_runtime(client.resolve_runtime_config())


def run_handler(client, capsys, handler, kwargs):
    try:
        getattr(client, handler)(**kwargs)
    except SystemExit as exc:
        assert exc.code == 1
    return json.loads(capsys.readouterr().out)


@pytest.mark.parametrize("handler,kwargs,collection,key,value", COMMANDS)
def test_missing_metadata_fields_block_every_convenience_put(generic_client, monkeypatch, capsys, handler, kwargs, collection, key, value):
    client, session = generic_client
    install_http(client, session, monkeypatch, collection, [{"name": "client_lock_stamp"}])
    result = run_handler(client, capsys, handler, kwargs)
    assert not any(call["method"] in {"PUT", "DELETE"} for call in session.calls)
    assert result["ok"] is False
    assert result["mutation"]["outcome"] == "not_attempted"


@pytest.mark.parametrize("handler,kwargs,collection,key,value", COMMANDS)
def test_convenience_updates_verify_internally_without_replay(generic_client, monkeypatch, capsys, handler, kwargs, collection, key, value):
    client, session = generic_client
    definitions = [{"name": key}, {"name": "client_lock_stamp", "field_type": "integer"}]
    if key == "user_tags":
        definitions[0].update(field_type="reference", field_type_data={"multiple": True, "targets": [{"type": "user_tag"}]})
    install_http(client, session, monkeypatch, collection, definitions, mismatch=True)
    result = run_handler(client, capsys, handler, kwargs)
    puts = [call for call in session.calls if call["method"] == "PUT"]
    assert len(puts) == 1 and puts[0]["json"][key] == value
    assert result["ok"] is False
    assert result["mutation"]["outcome"] == "succeeded"
    assert result["verification"]["matched"] is False
    assert not any(call["method"] == "DELETE" for call in session.calls)


@pytest.mark.parametrize("handler,id_key,collection", [("update_feature", "feature_id", "features"), ("update_story", "story_id", "stories")])
def test_convenience_name_alias_maps_to_actual_api_field(generic_client, monkeypatch, capsys, handler, id_key, collection):
    client, session = generic_client
    install_http(client, session, monkeypatch, collection, [
        {"name": "custom_name", "label": "Name"}, {"name": "client_lock_stamp"}])
    result = run_handler(client, capsys, handler, {id_key: "42", "name": "changed"})
    puts = [call for call in session.calls if call["method"] == "PUT"]
    assert len(puts) == 1
    assert puts[0]["json"] == {"custom_name": "changed", "client_lock_stamp": 3}
    assert result["ok"] is True and result["verification"]["matched"] is True


def test_metadata_http_failure_preserves_sanitized_error_without_mutation(generic_client):
    client, session = generic_client
    client.configure_runtime(client.resolve_runtime_config())
    session.responses.append(Response({"error_code": "platform.entity_not_found",
        "stack_trace": SENTINEL_SECRET}, 404))
    url = "https://example.test/api/shared_spaces/888/workspaces/777/features/42"
    result = client.update_backlog_fields(url, {"name": "changed"})
    assert result["ok"] is False
    assert result["mutation"]["outcome"] == "not_attempted"
    assert result["error_code"] == "platform.entity_not_found"
    assert result["status"] == 404
    assert session.calls[0]["url"].startswith(url.rsplit("/", 2)[0] + "/metadata/")
    assert all(call["method"] == "GET" for call in session.calls)
    assert SENTINEL_SECRET not in json.dumps(result)


@pytest.mark.parametrize("handler,kwargs,collection,label", [
    ("update_feature_security", {"feature_id": "42", "security_assessment": "changed"}, "features", "Security Assessment"),
    ("delete_backlog_item", {"entity_id": "42"}, "work_items", "Allow Delete?"),
])
def test_initial_convenience_resolution_rejects_ambiguous_labels(generic_client, monkeypatch, capsys, handler, kwargs, collection, label):
    client, session = generic_client
    install_http(client, session, monkeypatch, collection, [
        {"name": "custom_a", "label": label}, {"name": "custom_b", "label": label},
        {"name": "client_lock_stamp"}])
    result = run_handler(client, capsys, handler, kwargs)
    assert result["ok"] is False
    assert not any(call["method"] in {"PUT", "DELETE"} for call in session.calls)


def test_initial_convenience_resolution_stops_on_metadata_authorization_failure(generic_client, monkeypatch, capsys):
    client, session = generic_client
    install_http(client, session, monkeypatch, "features", [
        {"name": "custom_a", "label": "Security Assessment"}, {"name": "client_lock_stamp"}])
    request = session.request
    failed = False
    def with_first_failure(**call):
        nonlocal failed
        if "/metadata/" in call["url"] and not failed:
            failed = True
            session.calls.append(call)
            return Response({}, 403)
        return request(**call)
    monkeypatch.setattr(session, "request", with_first_failure)
    result = run_handler(client, capsys, "update_feature_security", {
        "feature_id": "42", "security_assessment": "changed"})
    assert result["ok"] is False
    assert not any(call["method"] == "PUT" for call in session.calls)


@pytest.mark.parametrize("total,exceeds", [(2, False), (1, True)])
def test_partial_field_metadata_blocks_update(generic_client, monkeypatch, total, exceeds):
    client, session = generic_client
    install_http(client, session, monkeypatch, "features", [{"name": "name"}])
    request = session.request
    def partial(**call):
        response = request(**call)
        if call["url"].endswith("/metadata/fields"):
            response.body.update(total_count=total, exceeds_total_count=exceeds)
        return response
    monkeypatch.setattr(session, "request", partial)
    url = "https://example.test/api/shared_spaces/888/workspaces/777/features/42"
    result = client.update_backlog_fields(url, {"name": "changed"})
    assert result["ok"] is False
    assert result["mutation"]["outcome"] == "not_attempted"
    assert not any(call["method"] == "PUT" for call in session.calls)


def test_required_acceptance_criteria_rejection_is_never_replayed(generic_client, monkeypatch, capsys):
    client, session = generic_client
    install_http(client, session, monkeypatch, "stories", [
        {"name": key} for key in ("description", "acceptance_criteria", "client_lock_stamp")], reject=True)
    result = run_handler(client, capsys, "update_story", {
        "story_id": "42", "description": "body", "acceptance_criteria": ["required"]})
    puts = [call for call in session.calls if call["method"] == "PUT"]
    assert len(puts) == 1
    assert puts[0]["json"]["acceptance_criteria"] == "required"
    assert result["ok"] is False and result["mutation"]["outcome"] == "rejected"
    assert result["error_code"] == "OCTANE_REQUEST_FAILED"
    assert result["status"] == 400
    assert "private" not in json.dumps(result)
