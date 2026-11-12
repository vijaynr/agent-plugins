"""Capture-backed favorite reads; synthetic fixtures, no HAR credentials or live calls."""
import copy
import importlib
import json
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
favorites = importlib.import_module("octane_favorites")
from octane_generic import GenericError
from test_octane_credential_config import isolated_runtime
from test_octane_generic_entities import generic_client, invoke, queue_metadata, Response


def favorite():
    return {"id": "42", "name": "Synthetic favorite", "state_name":
        "platform-tree-module-release-quality-details-feature-grid", "params": json.dumps({
        "filter": {"operator": "IN", "lExpression": {"operator": "PROPERTY", "value": "release"},
            "rExpression": [{"operator": "LITERAL", "value": {"id": "11", "$entityType": "release"}}]},
        "navFilter": json.dumps({"feature": {"product_entity_udf": {"21": "i", "22": "i"}}}),
        "includeChildren": "true", "selectedEntities": '["99"]',
        "treeVisibleNodes": "", "limitTreeToVisibleNodes": "", "showSharedOnly": "",
        "contentFilter": [{}], "searchText": "", "searchFields": "", "searchType": "text",
        "ap_includeFeaturesNotDirectlyInContextFilter": False,
        "sorting": '"{rank[ASC]}"', "uiVersion": "27.1.8.47"})}


class FakeAPI:
    root = "https://octane.example.test/api/shared_spaces/1/workspaces/2"

    def __init__(self, pages=None, record=None):
        self.record = record or favorite()
        self.pages = pages or [{"data": [{"id": "1"}, {"id": "2"}], "total_count": 3},
                               {"data": [{"id": "3"}], "total_count": 3}]
        self.calls = []

    def request(self, method, url, **kwargs):
        self.calls.append((method, url, kwargs))
        return {"ok": True, "data": {"data": [self.record], "total_count": 1,
                                      "exceeds_total_count": False}}

    def field_metadata(self, name):
        return {"ok": True, "data": {"data": [
            {"name": f, "filterable": True} for f in ("release", "subtype", "product_entity_udf")]}}

    def get_entities(self, args):
        self.calls.append(copy.copy(args))
        return {"ok": True, "data": self.pages.pop(0)}


def args(**overrides):
    return SimpleNamespace(entity_id="42", fields="id,name", page_size=2, max_items=100, **overrides)


def test_reads_favorite_via_filtered_collection_only():
    api = FakeAPI()
    result = favorites.read_favorite(api, "42")
    assert result["data"]["id"] == "42"
    method, url, kw = api.calls[0]
    assert method == "GET" and url == api.root + "/favorites"
    assert kw["params"]["query"] == "\"(id='42')\""
    assert "params" in kw["params"]["fields"].split(",")


def test_resolves_full_membership_not_selected_tree_item():
    plan = favorites.resolve_favorite(favorite())
    assert plan["entity_type"] == "work_items"
    assert plan["query"] == "(product_entity_udf EQ {id IN 21,22};subtype EQ ^feature^);(release EQ {id IN 11})"
    assert "99" not in plan["query"]
    assert set(plan["filter_fields"]) == {"release", "subtype", "product_entity_udf"}


@pytest.mark.parametrize("change", [
    {"navFilter": '{"feature":{"product_entity_udf":{"21":"x"}}}'},
    {"navFilter": '{"defect":{"product_entity_udf":{"21":"i"}}}'},
    {"filter": {}}, {"searchText": "sensitive"}, {"showSharedOnly": True},
    {"limitTreeToVisibleNodes": True}, {"includeChildren": "false"},
    {"contentFilter": [{"something": 1}]}, {"newScope": "unknown"},
    {"ap_includeFeaturesNotDirectlyInContextFilter": True}, {"filter": None},
])
def test_unknown_scope_fails_instead_of_broadening_query(change):
    record = favorite()
    params = json.loads(record["params"])
    params.update(change)
    record["params"] = json.dumps(params)
    with pytest.raises(GenericError):
        favorites.resolve_favorite(record)


@pytest.mark.parametrize("bad_id", ["../42", "42;id GT 0", "[current_user]", True, 1.5, ""])
def test_rejects_unsafe_or_user_relative_reference_ids(bad_id):
    record = favorite()
    params = json.loads(record["params"])
    params["filter"]["rExpression"][0]["value"]["id"] = bad_id
    record["params"] = json.dumps(params)
    with pytest.raises(GenericError):
        favorites.resolve_favorite(record)


def test_reads_every_page_and_reports_completeness():
    api = FakeAPI()
    result = favorites.list_favorite_items(api, args())
    assert result["ok"] and result["complete"]
    assert result["total_count"] == 3
    assert [x["id"] for x in result["data"]] == ["1", "2", "3"]
    calls = [c for c in api.calls if isinstance(c, SimpleNamespace)]
    assert [c.offset for c in calls] == [0, 2]
    assert all(c.order_by == "id" and c.entity_type == "work_items" for c in calls)


@pytest.mark.parametrize("pages", [
    [{"data": [], "total_count": 2}],
    [{"data": [{"id": "1"}], "total_count": 2}, {"data": [{"id": "1"}], "total_count": 2}],
    [{"data": [{"id": "1"}], "total_count": 2}, {"data": [{"id": "2"}], "total_count": 3}],
    [{"data": [{"id": "1"}], "total_count": 1, "exceeds_total_count": True}],
    [{"data": [{"id": "1"}]}],
])
def test_inconsistent_or_truncated_pages_never_claim_complete(pages):
    result = favorites.list_favorite_items(FakeAPI(pages), args())
    assert not result["ok"] and not result["complete"]


def test_item_cap_reports_partial_failure():
    a = args()
    a.max_items = 2
    result = favorites.list_favorite_items(FakeAPI(), a)
    assert not result["ok"] and not result["complete"]
    assert len(result["data"]) == 2


def test_missing_favorite_is_not_empty_success():
    api = FakeAPI()
    api.request = lambda *a, **kw: {"ok": True, "data": {"data": [], "total_count": 0}}
    with pytest.raises(GenericError, match="not accessible"):
        favorites.read_favorite(api, "42")


@pytest.mark.parametrize("body", [
    {"data": [{"id": "42"}], "total_count": True},
    {"data": [{"id": "42"}], "total_count": 1, "total_error_count": 1},
    {"data": [{"id": "42"}], "total_count": 1, "exceeds_total_count": True},
    {"data": [{"id": "43"}], "total_count": 1},
])
def test_invalid_favorite_read_never_succeeds(body):
    api = FakeAPI()
    api.request = lambda *a, **kw: {"ok": True, "data": body}
    with pytest.raises(GenericError):
        favorites.read_favorite(api, "42")


def test_403_stops_without_retry():
    api = FakeAPI()
    failure = {"ok": False, "status": 403, "error_code": "OCTANE_REMOTE_AUTHORIZATION_FAILED"}
    api.request = lambda *a, **kw: failure
    with pytest.raises(GenericError) as exc:
        favorites.read_favorite(api, "42")
    assert exc.value.result == failure


def test_unfilterable_live_field_blocks_item_read():
    api = FakeAPI()
    api.field_metadata = lambda name: {"data": {"data": [{"name": "release", "filterable": False}]}}
    with pytest.raises(GenericError):
        favorites.list_favorite_items(api, args())
    assert len(api.calls) == 1


def test_favorite_commands_through_real_cli(generic_client, monkeypatch, capsys):
    client, session = generic_client
    session.responses.append(Response({"data": [favorite()], "total_count": 1}))
    queue_metadata(session, name="work_item", collection="work_items", fields=[
        {"name": name} for name in ("id", "release", "subtype", "product_entity_udf")])
    session.responses.extend([Response({"data": [{"id": "1"}], "total_count": 2}),
                              Response({"data": [{"id": "2"}], "total_count": 2})])
    code, result, _ = invoke(client, monkeypatch, capsys, "list-favorite-items", "--entity-id", "42",
                            "--page-size", "1", "--workspace-id", "5", "--shared-space-id", "6")
    assert code == 0 and result["complete"] and len(result["data"]) == 2
    assert all(call["method"] == "GET" for call in session.calls)
    assert all("/shared_spaces/6/workspaces/5/" in call["url"] for call in session.calls)
    assert session.responses == []


@pytest.mark.parametrize("command,flags", [
    ("get-favorite", ["--entity-id", "../42"]),
    ("list-favorite-items", ["--entity-id", "42", "--max-items", "0"]),
    ("list-favorite-items", ["--entity-id", "42", "--page-size", "0"]),
    ("list-favorite-items", ["--entity-id", "42", "--fields", "id,{bad}"]),
])
def test_invalid_cli_arguments_do_not_resolve_credentials(generic_client, monkeypatch, capsys, command, flags):
    client, session = generic_client
    monkeypatch.setattr(client, "resolve_runtime_config", lambda *_: pytest.fail("runtime accessed"))
    code, result, _ = invoke(client, monkeypatch, capsys, command, *flags)
    assert code != 0 and not result["ok"] and not session.calls


def test_get_favorite_cli_avoids_entity_metadata(generic_client, monkeypatch, capsys):
    client, session = generic_client
    session.responses.append(Response({"data": [favorite()], "total_count": 1}))
    code, result, _ = invoke(client, monkeypatch, capsys, "get-favorite", "--entity-id", "42")
    assert code == 0 and result["data"]["id"] == "42"
    assert len(session.calls) == 1 and session.calls[0]["url"].endswith("/favorites")
