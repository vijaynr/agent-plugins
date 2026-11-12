"""Read-only favorite adapter for the captured release-quality feature grid.

Favorites are an internal UI contract (observed UI 27.1.8.47), not a documented
public entity API. Never guess unknown filter semantics or replay UI writes.
Transport, error sanitization and credentials belong to the owning client.
"""
from __future__ import annotations

import json
import re
from types import SimpleNamespace
from typing import Any

from octane_generic import GenericError

STATE = "platform-tree-module-release-quality-details-feature-grid"
FAVORITE_FIELDS = "id,name,params,state_name,module_root_state"
# These only affect presentation/selection in the captured state. selectedEntities
# selects the tree/detail item, NOT the grid's membership (verified in capture).
PRESENTATION = {
    "selectedEntities", "treeVisibleNodes", "colorRules", "groupBy", "columns",
    "sorting", "isSlimMode", "isGridTimelineMode", "timelineLegendVisibleIndicators",
    "navFilterCustomization", "uiVersion",
}


def numeric_id(value: Any) -> str:
    if type(value) not in (str, int) or not re.fullmatch(r"[0-9]+", str(value)):
        raise GenericError("Favorite adapter requires numeric, non-relative IDs")
    return str(value)


def json_object(value: Any, label: str) -> dict[str, Any]:
    def unique(pairs):
        obj = {}
        for key, val in pairs:
            if key in obj:
                raise ValueError("duplicate key")
            obj[key] = val
        return obj

    try:
        obj = json.loads(value, object_pairs_hook=unique) if isinstance(value, str) else value
    except (ValueError, RecursionError):
        raise GenericError(f"Invalid favorite {label} JSON") from None
    if not isinstance(obj, dict):
        raise GenericError(f"Favorite {label} must be an object")
    return obj


def read_favorite(api, entity_id: str) -> dict[str, Any]:
    target = numeric_id(entity_id)
    # Captured UI uses a filtered collection GET; the single-resource endpoint
    # is not assumed to exist or accept API-client authentication.
    result = api.request("GET", f"{api.root}/favorites", params={
        "fields": FAVORITE_FIELDS, "query": f"\"(id='{target}')\""}, exit_on_error=False)
    if not result.get("ok"):
        raise GenericError("Favorite read failed", result)
    body = result.get("data")
    rows = body.get("data") if isinstance(body, dict) else None
    if rows == []:
        raise GenericError("Favorite not accessible or not found for the current API identity")
    if (not isinstance(rows, list) or len(rows) != 1 or not isinstance(rows[0], dict)
            or numeric_id(rows[0].get("id")) != target
            or type(body.get("total_count")) is not int or body["total_count"] != 1
            or body.get("exceeds_total_count") is True or body.get("total_error_count", 0) != 0):
        raise GenericError("Invalid or incomplete favorite collection response")
    return {"ok": True, "data": rows[0], "source": "internal-ui-favorites-collection"}


def resolve_favorite(record: dict[str, Any]) -> dict[str, Any]:
    if record.get("state_name") != STATE:
        raise GenericError("Unsupported favorite state; capture its grid request before adding an adapter")
    params = json_object(record.get("params"), "params")
    neutral = {
        "limitTreeToVisibleNodes": "", "showSharedOnly": "", "contentFilter": [{}],
        "searchFields": "", "searchText": "", "searchType": "text",
        "includeChildren": "true", "ap_includeFeaturesNotDirectlyInContextFilter": False,
    }
    if set(params) - (PRESENTATION | set(neutral) | {"filter", "navFilter"}):
        raise GenericError("Unknown favorite parameters; refusing to omit possible scope constraints")
    for key, expected in neutral.items():
        if key not in params or type(params[key]) is not type(expected) or params[key] != expected:
            raise GenericError(f"Unsupported favorite scope parameter: {key}")
    expression = params.get("filter")
    if (not isinstance(expression, dict) or set(expression) != {"operator", "lExpression", "rExpression"}
            or expression.get("operator") != "IN"
            or expression.get("lExpression") != {"operator": "PROPERTY", "value": "release"}
            or not isinstance(expression.get("rExpression"), list) or not expression["rExpression"]):
        raise GenericError("Unsupported favorite filter; expected release IN reference literals")
    release_ids = []
    for literal in expression["rExpression"]:
        if (not isinstance(literal, dict) or set(literal) != {"operator", "value"}
                or literal.get("operator") != "LITERAL" or not isinstance(literal.get("value"), dict)
                or literal["value"].get("$entityType") != "release"):
            raise GenericError("Unsupported favorite reference literal")
        release_ids.append(numeric_id(literal["value"].get("id")))
    nav = json_object(params.get("navFilter"), "navFilter")
    if set(nav) != {"feature"} or not isinstance(nav["feature"], dict) or set(nav["feature"]) != {"product_entity_udf"}:
        raise GenericError("Unsupported favorite navigation filter")
    products = nav["feature"]["product_entity_udf"]
    if not isinstance(products, dict) or not products or any(v != "i" for v in products.values()):
        raise GenericError("Unsupported favorite navigation selection (only captured inclusion mode is supported)")
    product_ids = [numeric_id(key) for key in products]
    query = (f"(product_entity_udf EQ {{id IN {','.join(product_ids)}}};subtype EQ ^feature^);"
             f"(release EQ {{id IN {','.join(release_ids)}}})")
    return {"entity_type": "work_items", "query": query,
        "filter_fields": ["release", "subtype", "product_entity_udf"],
        "adapter": "release-quality-feature-grid-v1", "observed_ui_version": "27.1.8.47",
        "warnings": ["Internal UI favorite format; only the captured filter shape is supported",
                     "Membership only; sorted by id, not the favorite's display order",
                     "Paged reads are not a transactional snapshot; concurrent changes may require a rerun"]}


def list_favorite_items(api, args) -> dict[str, Any]:
    record = read_favorite(api, args.entity_id)["data"]
    plan = resolve_favorite(record)
    fields = {field["name"]: field for field in api.field_metadata("work_items")["data"]["data"]}
    for name in plan["filter_fields"]:
        if name not in fields or fields[name].get("filterable") is False:
            raise GenericError(f"Favorite filter field missing or not filterable: {name}")
    requested_fields = list(dict.fromkeys(["id"] + args.fields.split(",")))
    result = {"ok": False, "complete": False, "favorite": {
        "id": record["id"], "name": record.get("name")}, "resolution": plan,
        "data": [], "total_count": None, "pages_read": 0}

    def incomplete(message, failure=None):
        result["error"] = message
        result["error_code"] = "OCTANE_FAVORITE_INCOMPLETE"
        if failure:
            result["failure"] = failure
        return result

    seen = set()
    while len(result["data"]) < args.max_items:
        page_args = SimpleNamespace(entity_type="work_items", fields=",".join(requested_fields),
            query=plan["query"], search=None, order_by="id", offset=len(result["data"]),
            limit=min(args.page_size, args.max_items - len(result["data"])))
        try:
            page = api.get_entities(page_args)
        except GenericError as exc:
            return incomplete("Favorite page read failed", exc.result)
        if not page.get("ok"):
            return incomplete("Favorite page read failed", page)
        result["pages_read"] += 1
        body = page.get("data", {})
        rows, total = body.get("data"), body.get("total_count")
        if (not isinstance(rows, list) or type(total) is not int or total < 0
                or body.get("exceeds_total_count") is True or body.get("total_error_count", 0) != 0):
            return incomplete("Invalid, capped, or incomplete collection totals")
        if result["total_count"] is None:
            result["total_count"] = total
        if result["total_count"] != total:
            return incomplete("Collection total changed during pagination; rerun the read")
        if len(rows) > page_args.limit or len(result["data"]) + len(rows) > total:
            return incomplete("Collection page exceeds requested bounds or reported total")
        page_ids = []
        for row in rows:
            try:
                identity = numeric_id(row.get("id")) if isinstance(row, dict) else numeric_id(None)
            except GenericError:
                return incomplete("Collection page contains an invalid item identity")
            if identity in seen or identity in page_ids:
                return incomplete("Collection returned duplicate IDs during pagination; rerun the read")
            page_ids.append(identity)
        seen.update(page_ids)
        result["data"].extend(rows)
        if len(result["data"]) == total:
            result.update(ok=True, complete=True)
            return result
        if not rows:
            return incomplete("Collection ended before the reported total")
    return incomplete("Item safety cap reached; increase --max-items to retrieve all matches")
