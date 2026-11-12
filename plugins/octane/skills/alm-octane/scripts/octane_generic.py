"""Generic Octane operations; transport/authentication stay in the owning client.

Standard-library-only helper, not a standalone CLI. Use octane_client.py.
"""
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Callable

COMMANDS = {"get-favorite", "list-favorite-items", "get-entity", "get-entity-types", "get-entity-field-metadata", "get-filter-metadata", "get-entities", "create-entity", "update-entity"}
FILTER_GRAMMAR = {
    "source": "documentation", "version": "26.1",
    "url": "https://admhelp.microfocus.com/octane/en/26.1/Online/Content/API/query_Clause.htm",
    "operators_by_type": {
        "integer": ["EQ", "LT", "GT", "LE", "GE", "IN", "BTW"],
        "boolean": ["EQ"],
        "date_time": ["EQ", "LT", "GT", "LE", "GE", "IN", "BTW"],
        "string": ["EQ", "IN"], "memo": [], "reference": ["EQ", "IN"],
    },
    "logical_operators": {";": "AND", "||": "OR", "!": "NOT"},
    "value_formats": {"string": "^text^ (escape special characters per source)",
        "reference": "{id EQ 1234}", "boolean": "true or false", "wildcard": "*"},
    "examples": ["id EQ 1234", "name EQ ^login*^", "owner EQ {id EQ 1001}"],
    "limitations": ["Rules are documented, not server-discovered operators",
        "Field metadata supports AND, not OR; missing field capabilities remain unknown"],
}
ALIASES = {
    "work_item": "work_items", "work_items": "work_items",
    "defect": "defects", "defects": "defects",
    "story": "stories", "stories": "stories",
    "feature": "features", "features": "features",
    "test": "tests", "tests": "tests",
}


class GenericError(ValueError):
    """An actionable local contract failure, safe to render as JSON."""

    def __init__(self, message: str, result: dict[str, Any] | None = None):
        super().__init__(message)
        self.result = result


def resolve_update_fields(fields: dict[str, Any], metadata: list[dict[str, Any]]) -> dict[str, Any]:
    """Resolve every requested field against live metadata before any mutation.

    Exact API names take precedence over friendly labels. No convention-based
    fallback is safe for writes; aliases must identify exactly one field.
    Missing capability flags remain unknown, not evidence of writability.
    """
    def normalized(value: str) -> str:
        return re.sub(r"[^a-z0-9]", "", value.lower())

    resolved = {}
    for requested, value in fields.items():
        exact = [field for field in metadata if field.get("name") == requested]
        candidates = exact or [field for field in metadata if any(
            isinstance(field.get(key), str) and normalized(field[key]) == normalized(requested)
            for key in ("name", "label", "logical_name"))]
        if len(candidates) != 1:
            raise GenericError(f"Unknown or ambiguous update field: {requested}; inspect field metadata")
        definition = candidates[0]
        name = segment(definition["name"], "resolved field name")
        if name != "client_lock_stamp" and (
            definition.get("editable") is False or definition.get("updatable") is False
            or definition.get("read_only") is True
        ):
            raise GenericError(f"Update field is read-only: {name}")
        if name in resolved:
            raise GenericError(f"Multiple requested fields resolve to the same API field: {name}")
        resolved[name] = value
    return resolved


def segment(value: str, label: str) -> str:
    if not isinstance(value, str) or not re.fullmatch(r"[A-Za-z0-9_][A-Za-z0-9_.-]*", value):
        raise GenericError(f"Invalid {label}: use a single safe API path segment")
    return value


def register_commands(subparsers, add_common: Callable) -> None:
    for command in ("get-favorite", "list-favorite-items"):
        parser = subparsers.add_parser(command, help="Read an internal UI favorite" if command == "get-favorite"
            else "Resolve a supported favorite and read all matching items (read-only)")
        parser.add_argument("--entity-id", required=True, help="Numeric favorite ID")
        if command == "list-favorite-items":
            parser.add_argument("--fields", default="id,name,subtype,phase,owner")
            parser.add_argument("--page-size", type=int, default=100)
            parser.add_argument("--max-items", type=int, default=10000, help="Safety cap; hitting it is incomplete, not success")
        add_common(parser)
    parser = subparsers.add_parser("get-entity", help="Fetch an entity from a supported collection")
    parser.add_argument("--entity-type", required=True)
    parser.add_argument("--entity-id", required=True)
    parser.add_argument("--fields", default=None)
    add_common(parser)
    parser = subparsers.add_parser("get-entity-types", help="Discover workspace entity types and REST collections")
    add_common(parser)
    for command, help_text in (
        ("get-entity-field-metadata", "Read exact entity field definitions"),
        ("get-filter-metadata", "Show documented filter syntax and workspace field capabilities"),
    ):
        parser = subparsers.add_parser(command, help=help_text)
        parser.add_argument("--entity-type", required=True)
        add_common(parser)
    parser = subparsers.add_parser("get-entities", help="Read one filtered/sorted page of entities")
    parser.add_argument("--entity-type", required=True)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--query", help="Native expression without outer double quotes")
    mode.add_argument("--search", help="Keyword text (work_items only; server support required)")
    parser.add_argument("--fields", default=None)
    parser.add_argument("--order-by", default="id")
    parser.add_argument("--limit", type=int, default=50)
    parser.add_argument("--offset", type=int, default=0)
    add_common(parser)
    for command, help_text in (
        ("create-entity", "Create one entity from JSON and verify it"),
        ("update-entity", "Update selected fields with lock protection and verification"),
    ):
        parser = subparsers.add_parser(command, help=help_text)
        parser.add_argument("--entity-type", required=True)
        if command == "update-entity":
            parser.add_argument("--entity-id", required=True)
        parser.add_argument("--data-file", required=True, help="UTF-8 JSON field object, not a data envelope")
        add_common(parser)


def load_fields(path: str, operation: str, entity_id: str | None = None) -> dict[str, Any]:
    def unique_object(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise GenericError("Duplicate JSON keys are not allowed")
            result[key] = value
        return result

    def reject_constant(value):
        raise GenericError("Nonstandard JSON constants are not allowed")

    try:
        fields = json.loads(Path(path).read_text(encoding="utf-8"),
            object_pairs_hook=unique_object, parse_constant=reject_constant)
    except (OSError, UnicodeError, ValueError, RecursionError):
        raise GenericError("Cannot read payload: use a valid UTF-8 JSON field object") from None
    if not isinstance(fields, dict) or not fields or "data" in fields:
        raise GenericError("Payload must be one nonempty field object, not an array or data envelope")
    for key in fields:
        segment(key, "payload field")
    if "id" in fields:
        if operation == "create-entity" or fields["id"] != entity_id:
            raise GenericError("Payload ID conflicts with explicit targeting or server-assigned creation")
        del fields["id"]
    if not fields or set(fields) <= {"client_lock_stamp"}:
        raise GenericError("Supply at least one field to change")
    return fields


def validate_arguments(args) -> None:
    if args.command in {"get-favorite", "list-favorite-items"}:
        from octane_favorites import numeric_id
        numeric_id(args.entity_id)
        if args.command == "list-favorite-items" and (args.page_size <= 0 or args.max_items <= 0):
            raise GenericError("page-size and max-items must be positive")
    for attribute in ("entity_type", "entity_id", "workspace_id", "shared_space_id"):
        value = getattr(args, attribute, None)
        if value is not None:
            segment(value, attribute)
    fields = getattr(args, "fields", None)
    if fields is not None:
        for field in fields.split(","):
            segment(field, "field name")
    if args.command == "get-entities":
        if args.limit <= 0 or args.offset < 0:
            raise GenericError("limit must be positive and offset nonnegative")
        if args.query is not None and (not args.query.strip() or args.query.startswith('"') or args.query.endswith('"')):
            raise GenericError("Pass a nonempty native query without outer double quotes")
        if args.search is not None:
            if not args.search.strip():
                raise GenericError("Keyword search requires nonempty text")
            if ALIASES.get(args.entity_type, args.entity_type) != "work_items":
                raise GenericError("Keyword search is supported only on work_items")
        for field in args.order_by.split(","):
            segment(field[1:] if field.startswith("-") else field, "sort field")


def fetch_entity_record(
    request: Callable, url: str, fields: str | None = None, *, exit_on_error: bool = False,
) -> dict[str, Any]:
    params = {"fields": fields} if fields else {}
    return request("GET", url, params=params, exit_on_error=exit_on_error)


def single_record(result: dict[str, Any]) -> dict[str, Any]:
    body = result.get("data")
    if not isinstance(body, dict):
        return {}
    if "data" not in body:
        return body
    records = body["data"]
    if not isinstance(records, list) or len(records) != 1 or not isinstance(records[0], dict):
        return {}
    return records[0]


def matches_entity_id(actual_id: Any, entity_id: str) -> bool:
    """Compare a server ID to a target without accepting booleans or floats."""
    return type(actual_id) in (str, int) and str(actual_id) == entity_id


def unknown_mutation(result: dict[str, Any], message: str) -> dict[str, Any]:
    # Preserve outcome evidence, not an untrusted diagnostic body masquerading as data.
    safe = {key: result[key] for key in ("status", "url", "concurrency") if key in result}
    safe.update(ok=False, error=f"{message}; write may have succeeded; do not retry blindly",
        mutation={"outcome": "unknown"})
    return safe


def same_json(expected: Any, actual: Any) -> bool:
    if type(expected) is not type(actual):
        return False
    if isinstance(expected, dict):
        return expected.keys() == actual.keys() and all(same_json(v, actual[k]) for k, v in expected.items())
    if isinstance(expected, list):
        return len(expected) == len(actual) and all(same_json(a, b) for a, b in zip(expected, actual))
    return expected == actual


def field_matches(expected: Any, actual: Any, metadata: dict[str, Any]) -> bool:
    if metadata.get("field_type") == "string" and metadata.get("required") is False and expected == "" and actual is None:
        return True
    if metadata.get("field_type") != "reference" or expected is None or actual is None:
        return same_json(expected, actual)
    details = metadata.get("field_type_data")
    details = details if isinstance(details, dict) else {}
    targets = details.get("targets", [])
    target = targets[0].get("type") if isinstance(targets, list) and len(targets) == 1 and isinstance(targets[0], dict) else None

    def identity(value):
        if not isinstance(value, dict) or type(value.get("id")) not in (str, int):
            return None
        kind = value.get("type", target)
        return (kind, str(value["id"])) if isinstance(kind, str) else None

    if details.get("multiple") is True:
        # A bare list or a page without totals cannot prove a complete read-back.
        if not isinstance(actual, dict) or "total_count" not in actual or actual.get("exceeds_total_count") is True:
            return False
        def identities(value):
            if isinstance(value, dict):
                items = value.get("data")
                count = value.get("total_count")
                if count is not None and (type(count) is not int or not isinstance(items, list) or count != len(items)):
                    return None
            else:
                items = value
            if not isinstance(items, list):
                return None
            keys = [identity(item) for item in items]
            if any(key is None for key in keys) or len(set(keys)) != len(keys):
                return None
            return set(keys)
        expected_ids, actual_ids = identities(expected), identities(actual)
        return expected_ids is not None and expected_ids == actual_ids
    expected_id = identity(expected)
    return expected_id is not None and expected_id == identity(actual)


class GenericAPI:
    def __init__(self, root: str, request: Callable):
        self.root = root
        self._request = request
        self._types: dict[str, Any] | None = None
        self._fields: dict[str, dict[str, Any]] = {}

    def request(self, method: str, url: str, **kwargs) -> dict[str, Any]:
        result = self._request(method, url, **kwargs)
        if result.get("ok"):
            return result
        # Server bodies/transport diagnostics can echo credentials or stack traces.
        # Preserve only documented, recognized error codes; never log raw failures.
        response = result.get("response")
        code = response.get("error_code") if isinstance(response, dict) else None
        known_codes = {"platform.version_conflict", "platform.entity_not_found"}
        status = result.get("status")
        if not isinstance(code, str) or code not in known_codes:
            code = {
                401: "OCTANE_REMOTE_AUTHENTICATION_FAILED",
                403: "OCTANE_REMOTE_AUTHORIZATION_FAILED",
            }.get(status, "OCTANE_REQUEST_FAILED")
        public = {"ok": False, "error": "Octane API request failed", "url": url,
            "error_code": code}
        if status is not None:
            public["status"] = status
        return public

    def entity_types(self) -> dict[str, Any]:
        if self._types is None:
            result = self.request("GET", f"{self.root}/metadata/entities", params={}, exit_on_error=False)
            if not result.get("ok"):
                raise GenericError("Entity discovery failed", result)
            entries = result.get("data", {}).get("data") if isinstance(result.get("data"), dict) else None
            if not isinstance(entries, list) or any(not isinstance(entry, dict) for entry in entries):
                raise GenericError("Invalid entity metadata response")
            for entry in entries:
                segment(entry.get("name"), "metadata entity name")
                features = entry.get("features", [])
                if not isinstance(features, list) or any(not isinstance(feature, dict) for feature in features):
                    raise GenericError("Invalid entity features")
                for feature in features:
                    if feature.get("name") == "rest":
                        segment(feature.get("url"), "metadata collection")
                        if not isinstance(feature.get("methods"), list):
                            raise GenericError("Invalid REST methods metadata")
            self._types = result
        return self._types

    def describe(self, name: str, method: str = "GET") -> tuple[str, str]:
        segment(name, "entity type")
        matches = []
        for entry in self.entity_types()["data"]["data"]:
            for feature in entry.get("features", []):
                if feature.get("name") != "rest":
                    continue
                collection = feature["url"]
                if name in {entry["name"], collection} or ALIASES.get(name) == collection:
                    matches.append((entry["name"], collection, feature["methods"]))
        if len(matches) != 1:
            raise GenericError("Unknown or ambiguous entity type; use get-entity-types")
        metadata_name, collection, methods = matches[0]
        if method not in methods:
            raise GenericError(f"Entity collection does not support {method}")
        return metadata_name, collection

    def field_metadata(self, name: str) -> dict[str, Any]:
        metadata_name, _ = self.describe(name)
        if metadata_name not in self._fields:
            result = self.request("GET", f"{self.root}/metadata/fields",
                params={"query": f'"entity_name EQ ^{metadata_name}^"', "limit": 5000}, exit_on_error=False)
            if not result.get("ok"):
                raise GenericError("Field discovery failed", result)
            fields = result.get("data", {}).get("data") if isinstance(result.get("data"), dict) else None
            if not isinstance(fields, list) or any(not isinstance(field, dict) for field in fields):
                raise GenericError("Invalid field metadata response")
            body = result["data"]
            total = body.get("total_count")
            if body.get("exceeds_total_count") is True or (
                total is not None and (type(total) is not int or total != len(fields))
            ):
                raise GenericError("Incomplete field metadata; update field resolution requires the complete field set")
            for field in fields:
                segment(field.get("name"), "field name")
                if field.get("entity_name", metadata_name) != metadata_name:
                    raise GenericError("Field metadata contains a different entity context")
            self._fields[metadata_name] = result
        return self._fields[metadata_name]

    def filter_metadata(self, name: str) -> dict[str, Any]:
        fields = self.field_metadata(name)
        return {"ok": True, "data": {"grammar": FILTER_GRAMMAR,
            "field_metadata": {"source": "workspace", "data": fields["data"]["data"]}}}

    def collection(self, name: str) -> str:
        segment(name, "entity type")
        # Stable legacy aliases need no extra metadata request for simple reads.
        return ALIASES[name] if name in ALIASES else self.describe(name)[1]

    def validate_references(self, fields: dict[str, Any], metadata: list[dict[str, Any]]) -> None:
        for definition in metadata:
            name = definition["name"]
            value = fields.get(name)
            if name not in fields or value is None or definition.get("field_type") != "reference":
                continue
            details = definition.get("field_type_data")
            details = details if isinstance(details, dict) else {}
            targets = details.get("targets", [])
            kinds = {target["type"] for target in targets if isinstance(target, dict) and isinstance(target.get("type"), str)} if isinstance(targets, list) else set()
            if details.get("multiple") is True:
                values = value.get("data") if isinstance(value, dict) else value
                if not isinstance(values, list):
                    raise GenericError("Multi-reference fields require an array or a data array object")
            else:
                values = [value]
            for reference in values:
                if not isinstance(reference, dict) or type(reference.get("id")) not in (str, int):
                    raise GenericError("References require an object with a string or integer ID")
                segment(str(reference["id"]), "reference ID")
                kind = reference.get("type")
                if kind is not None:
                    segment(kind, "reference type")
                    if kinds and kind not in kinds:
                        raise GenericError("Reference type does not match field metadata")
                elif len(kinds) > 1:
                    raise GenericError("Polymorphic references require an explicit type")

    def verify_write(self, result: dict[str, Any], collection: str, entity_id: str,
                     fields: dict[str, Any], metadata: list[dict[str, Any]]) -> dict[str, Any]:
        result["mutation"] = {"outcome": "succeeded", "entity_id": entity_id}
        definitions = {field["name"]: field for field in metadata}
        changed = {key: value for key, value in fields.items() if key not in {"id", "client_lock_stamp"}}
        readable = [key for key in changed if definitions.get(key, {}).get("selectable") is not False]
        read = fetch_entity_record(self.request, f"{self.root}/{collection}/{entity_id}", ",".join(["id", *readable]))
        snapshot = single_record(read) if read.get("ok") else {}
        identity_ok = matches_entity_id(snapshot.get("id"), entity_id)
        if not identity_ok:
            snapshot = {}
        checks = {}
        for key, expected in changed.items():
            if key not in readable:
                checks[key] = "unreadable"
            elif key not in snapshot:
                checks[key] = "missing"
            else:
                checks[key] = "matched" if field_matches(expected, snapshot[key], definitions.get(key, {})) else "mismatch"
        matched = bool(read.get("ok")) and identity_ok and all(value == "matched" for value in checks.values())
        result["verification"] = {"read_ok": bool(read.get("ok")), "matched": matched,
            "fields": checks, "snapshot": snapshot,
            "url": read.get("url"), "status": read.get("status")}
        if not read.get("ok"):
            result["verification"]["error"] = "Verification read failed"
            if "error_code" in read:
                result["verification"]["error_code"] = read["error_code"]
        if not matched:
            result["ok"] = False
            result["error"] = "Write may have succeeded but could not be verified; do not retry blindly"
        return result

    def create_entity(self, name: str, fields: dict[str, Any]) -> dict[str, Any]:
        _, collection = self.describe(name, "POST")
        metadata = self.field_metadata(name)["data"]["data"]
        self.validate_references(fields, metadata)
        result = self.request("POST", f"{self.root}/{collection}", payload={"data": [fields]}, exit_on_error=False)
        if not result.get("ok"):
            result["mutation"] = {"outcome": "rejected" if result.get("status") else "unknown"}
            result["recovery"] = "Check mutation outcome before retrying; no automatic retry was attempted"
            return result
        if result.get("status") != 201:
            return unknown_mutation(result, "Unexpected create status")
        entity_id = single_record(result).get("id")
        try:
            if type(entity_id) not in (str, int):
                raise GenericError("Missing create ID")
            entity_id = segment(str(entity_id), "created entity ID")
        except GenericError:
            return unknown_mutation(result, "Create response lacks one safe entity ID")
        return self.verify_write(result, collection, entity_id, fields, metadata)

    def update_entity(self, name: str, entity_id: str, fields: dict[str, Any]) -> dict[str, Any]:
        segment(entity_id, "entity ID")
        _, collection = self.describe(name, "PUT")
        metadata = self.field_metadata(name)["data"]["data"]
        if "client_lock_stamp" in fields and not any(field["name"] == "client_lock_stamp" for field in metadata):
            raise GenericError("Stamp protection is unavailable for this entity; remove the caller stamp only if an unprotected update is intended")
        fields = resolve_update_fields(fields, metadata)
        self.validate_references(fields, metadata)
        supports_stamp = any(field["name"] == "client_lock_stamp" for field in metadata)
        fields = dict(fields)
        concurrency: dict[str, Any] = {"protected": False, "source": "unavailable"}
        url = f"{self.root}/{collection}/{entity_id}"
        if "client_lock_stamp" in fields:
            if not supports_stamp:
                raise GenericError("Stamp protection is unavailable for this entity; remove the caller stamp only if an unprotected update is intended")
            if type(fields["client_lock_stamp"]) is not int or fields["client_lock_stamp"] < 0:
                raise GenericError("client_lock_stamp must be a nonnegative integer")
            concurrency = {"protected": supports_stamp, "source": "caller"}
        elif supports_stamp:
            current = fetch_entity_record(self.request, url, "id,client_lock_stamp")
            record = single_record(current) if current.get("ok") else {}
            if (
                not matches_entity_id(record.get("id"), entity_id)
                or type(record.get("client_lock_stamp")) is not int
                or record["client_lock_stamp"] < 0
            ):
                current.update(ok=False, error="Cannot read current lock stamp for the target; update not attempted",
                    mutation={"outcome": "not_attempted"})
                return current
            fields["client_lock_stamp"] = record["client_lock_stamp"]
            concurrency = {"protected": True, "source": "current"}
        result = self.request("PUT", url, payload=fields, exit_on_error=False)
        result["concurrency"] = concurrency
        if not result.get("ok"):
            result["mutation"] = {"outcome": "rejected" if result.get("status") else "unknown"}
            result["recovery"] = "Do not replay automatically; inspect the conflict or mutation outcome first"
            return result
        returned_id = single_record(result).get("id")
        if result.get("status") != 200 or not matches_entity_id(returned_id, entity_id):
            return unknown_mutation(result, "Unexpected update response")
        return self.verify_write(result, collection, entity_id, fields, metadata)

    def get_entities(self, args) -> dict[str, Any]:
        _, collection = self.describe(args.entity_type)
        fields = self.field_metadata(args.entity_type)["data"]["data"]
        capabilities = {field["name"]: field for field in fields}
        for sort_field in args.order_by.split(","):
            if capabilities.get(sort_field.lstrip("-"), {}).get("sortable") is False:
                raise GenericError("Requested field is not sortable")
        params: dict[str, Any] = {"limit": args.limit, "offset": args.offset, "order_by": args.order_by}
        if args.fields:
            params["fields"] = args.fields
        if args.query is not None:
            params["query"] = f'"{args.query}"'
        if args.search is not None:
            params["text_search"] = json.dumps({"type": "global", "text": args.search}, ensure_ascii=False)
        result = self.request("GET", f"{self.root}/{collection}", params=params, exit_on_error=False)
        if result.get("ok"):
            body = result.get("data")
            if not isinstance(body, dict) or not isinstance(body.get("data"), list) or any(not isinstance(item, dict) for item in body["data"]):
                raise GenericError("Invalid entity collection response")
            result["pagination"] = {"limit": args.limit, "offset": args.offset}
        elif args.search is not None and result.get("status") == 400:
            result["recovery"] = "Verify text_search support for your server version; no query fallback was attempted"
        return result

    def get_entity(self, name: str, entity_id: str, fields: str | None = None) -> dict[str, Any]:
        segment(entity_id, "entity ID")
        collection = self.collection(name)
        result = fetch_entity_record(self.request, f"{self.root}/{collection}/{entity_id}", fields)
        if result.get("ok"):
            record = single_record(result)
            if not matches_entity_id(record.get("id"), entity_id):
                raise GenericError("Entity read returned no matching target record")
        return result


def run_cli(args, client) -> int:
    """Validate before configuration, execute one operation, render exactly once."""
    try:
        validate_arguments(args)
        payload = load_fields(args.data_file, args.command, getattr(args, "entity_id", None)) if args.command in {"create-entity", "update-entity"} else None
        runtime = client.resolve_runtime_config(args.profile)
        workspace = segment(args.workspace_id or runtime.workspace_id, "workspace ID")
        space = segment(args.shared_space_id or runtime.shared_space_id, "shared-space ID")
        client.configure_runtime(runtime)
        api = GenericAPI(client._api_root(space, workspace), client.request_json)
        if args.command in {"get-favorite", "list-favorite-items"}:
            from octane_favorites import read_favorite, list_favorite_items
            result = read_favorite(api, args.entity_id) if args.command == "get-favorite" else list_favorite_items(api, args)
        elif args.command == "get-entity-types":
            result = api.entity_types()
        elif args.command == "get-entity-field-metadata":
            result = api.field_metadata(args.entity_type)
        elif args.command == "get-filter-metadata":
            result = api.filter_metadata(args.entity_type)
        elif args.command == "get-entities":
            result = api.get_entities(args)
        elif args.command == "create-entity":
            result = api.create_entity(args.entity_type, payload)
        elif args.command == "update-entity":
            result = api.update_entity(args.entity_type, args.entity_id, payload)
        else:
            result = api.get_entity(args.entity_type, args.entity_id, args.fields)
    except GenericError as exc:
        result = exc.result or {"ok": False, "error": str(exc)}
    print(json.dumps(result, ensure_ascii=False))
    return 0 if result.get("ok") else 1
