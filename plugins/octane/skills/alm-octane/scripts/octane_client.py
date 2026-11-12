#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = [
#   "requests>=2.28,<3",
#   "python-dotenv>=1.0,<2",
#   "keyring>=25,<26",
# ]
# ///
"""
ALM Octane CLI — a standalone REST client with generic entity operations
and workflow convenience commands. No MCP service is required.

Authentication uses Octane's cookie-based sign-in endpoint
(POST /authentication/sign_in) which is the same mechanism the
official @microfocus/alm-octane-js-rest-sdk uses under the hood.

All output is JSON so that calling agents can parse results reliably.
"""

import os
import sys
import json
import html
import argparse
import mimetypes
import octane_generic
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

try:
    import requests
except ImportError:
    print(json.dumps({"ok": False, "error": "Missing dependency: requests. Run via: uv run scripts/octane_client.py ..."}))
    sys.exit(1)

try:
    import keyring
    from keyring.errors import KeyringError
except ImportError:
    keyring = None  # type: ignore[assignment]

    class KeyringError(Exception):
        pass

from typing import NamedTuple
from credential_config import ConfigError, active_profile, config_path, migrate_legacy, named_profile, validate_endpoint

_SCRIPT_SKILL_ROOT = Path(__file__).resolve().parent.parent
_SKILL_ROOT = _SCRIPT_SKILL_ROOT
DEFAULT_SHARED_SPACE_ID = "1001"
DEFAULT_WORKSPACE_ID = "1003"
DEFAULT_TIMEOUT = 30
_CREDENTIAL_NAMES = {
    "OCTANE_BASE_URL",
    "OCTANE_CLIENT_ID",
    "OCTANE_CLIENT_SECRET",
    "OCTANE_CLIENT_SECRET_KEYRING_USER",
}
_DIRECT_CREDENTIAL_NAMES = {"OCTANE_BASE_URL", "OCTANE_CLIENT_ID", "OCTANE_CLIENT_SECRET"}
_KEYRING_CREDENTIAL_NAMES = {"OCTANE_BASE_URL", "OCTANE_CLIENT_SECRET_KEYRING_USER"}


class RuntimeConfig(NamedTuple):
    base_url: str
    client_id: str
    client_secret: str
    client_secret_keyring_user: str
    shared_space_id: str
    workspace_id: str
    timeout: int
    field_overrides: Tuple[Tuple[str, str], ...]


class _Credentials(NamedTuple):
    base_url: str
    client_id: str
    client_secret: str
    keyring_user: str


def _dotenv_values() -> Dict[str, str]:
    env_file = _SCRIPT_SKILL_ROOT / ".env"
    if not env_file.is_file():
        return {}
    try:
        from dotenv import dotenv_values
        return {name: value for name, value in dotenv_values(env_file).items() if value is not None}
    except ImportError:
        values: Dict[str, str] = {}
        with open(env_file) as source:
            for raw_line in source:
                line = raw_line.strip()
                if line and not line.startswith("#") and "=" in line:
                    name, value = line.split("=", 1)
                    values[name.strip()] = value.strip().strip('"').strip("'")
        return values


def _present_credentials(environment: Dict[str, str]) -> set[str]:
    return {name for name in _CREDENTIAL_NAMES if environment.get(name)}


def _credentials_from_environment(
    environment: Dict[str, str],
    direct: bool,
    keyring_backed: bool,
) -> _Credentials:
    base_url = environment.get("OCTANE_BASE_URL", "").rstrip("/")
    if direct:
        return _Credentials(
            base_url,
            environment["OCTANE_CLIENT_ID"],
            environment["OCTANE_CLIENT_SECRET"],
            "",
        )
    if keyring_backed:
        keyring_user = environment["OCTANE_CLIENT_SECRET_KEYRING_USER"]
        return _Credentials(base_url, keyring_user, "", keyring_user)
    return _Credentials(base_url, "", "", "")


def _load_runtime_profile(
    selected_name: Optional[str],
    process_credentials: set[str],
    dotenv_direct: bool,
) -> Dict[str, Any]:
    try:
        if selected_name == "default" and not config_path().is_file() and keyring:
            migrate_legacy(_SCRIPT_SKILL_ROOT, keyring.get_password)
        active = named_profile(selected_name) if selected_name else active_profile()
        should_attempt_migration = bool(process_credentials) or not dotenv_direct
        if active is None and should_attempt_migration:
            if keyring:
                migrate_legacy(_SCRIPT_SKILL_ROOT, keyring.get_password)
            active = named_profile(selected_name) if selected_name else active_profile()
    except ConfigError as exc:
        fail("Invalid durable Octane profile", details=str(exc))
    return active[1] if active else {}


def resolve_runtime_config(profile_name: Optional[str] = None) -> RuntimeConfig:
    """Resolve one coherent Octane configuration source after argument parsing."""
    process_env = dict(os.environ)
    dotenv_env = _dotenv_values()
    process_credentials = _present_credentials(process_env)
    process_direct = _DIRECT_CREDENTIAL_NAMES.issubset(process_credentials)
    process_keyring = _KEYRING_CREDENTIAL_NAMES.issubset(process_credentials)
    if process_direct and process_keyring:
        fail("Direct and keyring Octane credentials are mutually exclusive", error_code="OCTANE_CREDENTIAL_SOURCE_MISMATCH")
    dotenv_credentials = _present_credentials(dotenv_env)
    dotenv_direct = _DIRECT_CREDENTIAL_NAMES.issubset(dotenv_credentials)
    dotenv_keyring = _KEYRING_CREDENTIAL_NAMES.issubset(dotenv_credentials)
    if dotenv_direct and dotenv_keyring:
        fail("Direct and keyring Octane credentials are mutually exclusive", error_code="OCTANE_CREDENTIAL_SOURCE_MISMATCH")
    selected_name = profile_name or process_env.get("OCTANE_PROFILE")

    profile: Dict[str, Any] = {}
    if not (process_direct or process_keyring):
        profile = _load_runtime_profile(selected_name, process_credentials, dotenv_direct)

    if process_direct or process_keyring:
        source = process_env
        credentials = _credentials_from_environment(process_env, process_direct, process_keyring)
        settings: Dict[str, Any] = {}
        field_source = process_env
    elif profile:
        endpoint_only = process_credentials == {"OCTANE_BASE_URL"}
        endpoint_matches = endpoint_only and process_env["OCTANE_BASE_URL"].rstrip("/") == profile["endpoint"].rstrip("/")
        if process_credentials and not endpoint_matches:
            message = (
                "URL endpoint does not match the selected Octane profile"
                if endpoint_only
                else "Incoherent partial Octane credential override"
            )
            fail(message, error_code="OCTANE_CREDENTIAL_SOURCE_MISMATCH")
        source = process_env
        credentials = _Credentials(profile["endpoint"].rstrip("/"), "", "", profile["keyring_user"])
        settings = profile.get("settings", {})
        field_source = process_env
    else:
        if process_credentials:
            fail("Incoherent partial Octane credential override", error_code="OCTANE_CREDENTIAL_SOURCE_MISMATCH")
        if dotenv_credentials and not (dotenv_direct or dotenv_keyring):
            fail("Incoherent partial Octane credential override", error_code="OCTANE_CREDENTIAL_SOURCE_MISMATCH")
        source = {**dotenv_env, **process_env}
        credentials = _credentials_from_environment(dotenv_env, dotenv_direct, dotenv_keyring)
        settings = {}
        field_source = source

    def setting(environment_name: str, profile_setting: str, fallback: str) -> str:
        if environment_name in process_env:
            return process_env[environment_name]
        if profile:
            return settings.get(profile_setting, fallback)
        return source.get(environment_name, fallback)

    try:
        timeout = int(setting("OCTANE_TIMEOUT", "timeout", str(DEFAULT_TIMEOUT)))
        if timeout <= 0:
            raise ValueError
    except (TypeError, ValueError):
        fail("OCTANE_TIMEOUT must be a positive integer", error_code="OCTANE_TIMEOUT_INVALID")
    try:
        base_url = validate_endpoint(credentials.base_url) if credentials.base_url else ""
    except ConfigError as exc:
        fail(str(exc), error_code="OCTANE_ENDPOINT_UNSAFE")

    return RuntimeConfig(
        base_url,
        credentials.client_id,
        credentials.client_secret,
        credentials.keyring_user,
        setting("OCTANE_SHARED_SPACE_ID", "shared_space_id", DEFAULT_SHARED_SPACE_ID),
        setting("OCTANE_WORKSPACE_ID", "workspace_id", DEFAULT_WORKSPACE_ID),
        timeout,
        tuple(sorted({
            name: value for name, value in field_source.items()
            if name.startswith("OCTANE_") and name.endswith("_FIELD") and value
        }.items())),
    )


_runtime: Optional[RuntimeConfig] = None


def configure_runtime(runtime: RuntimeConfig) -> None:
    """Install explicitly resolved immutable runtime state for API handlers."""
    global _runtime, _session
    previous_session = _session
    _runtime = runtime
    _session = None
    if previous_session is not None and hasattr(previous_session, "close"):
        previous_session.close()


def _require_runtime() -> RuntimeConfig:
    if _runtime is None:
        fail("Octane runtime is not configured; call resolve_runtime_config() and configure_runtime()")
    return _runtime


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def fail(message: str, **extra: Any) -> None:
    """Print a JSON error envelope and exit."""
    payload: Dict[str, Any] = {"ok": False, "error": message}
    payload.update(extra)
    print(json.dumps(payload, ensure_ascii=False))
    sys.exit(1)


def _is_octane_html(value: str) -> bool:
    stripped = value.strip().lower()
    return stripped.startswith("<html") or stripped.startswith("<body")


def format_octane_comment_text(text: str) -> str:
    """Return Octane comment text in the HTML envelope used by the REST API.

    Octane returns comment text as HTML (for example:
    ``<html><body>\n<p>Comment text.</p> \n</body></html>``).  Wrap plain
    text before posting so line breaks and paragraphs render correctly in the
    Octane UI, while leaving already-HTML comments untouched.
    """
    stripped = text.strip()
    if _is_octane_html(stripped):
        return text

    paragraphs: List[str] = []
    current: List[str] = []
    for line in text.splitlines():
        if line.strip():
            current.append(html.escape(line, quote=False))
        elif current:
            paragraphs.append("<br />\n".join(current))
            current = []
    if current:
        paragraphs.append("<br />\n".join(current))

    if not paragraphs:
        paragraphs = [""]

    body = "\n".join(f"<p>{paragraph}</p>" for paragraph in paragraphs)
    return f"<html><body>\n{body} \n</body></html>"


def _inline_markdown_to_html(text: str) -> str:
    escaped = html.escape(text, quote=False)
    escaped = escaped.replace("**", "")
    escaped = escaped.replace("__", "")
    return escaped


def format_octane_description_html(description: str) -> str:
    """Return an Octane rich-text description as an HTML string.

    ALM Octane defect descriptions are rich-text HTML values inside the JSON
    payload, e.g. ``"description": "<html><body>...</body></html>"``. Convert
    common Markdown/plain-text structure to simple safe HTML so headings, lists,
    and code blocks render neatly in the Octane UI. Existing HTML is passed
    through unchanged.
    """
    if _is_octane_html(description):
        return description

    lines = description.splitlines()
    parts: List[str] = []
    paragraph: List[str] = []
    in_ul = False
    in_ol = False
    in_pre = False
    pre_lines: List[str] = []

    def flush_paragraph() -> None:
        nonlocal paragraph
        if paragraph:
            parts.append(f"<p>{'<br />'.join(paragraph)}</p>")
            paragraph = []

    def close_lists() -> None:
        nonlocal in_ul, in_ol
        if in_ul:
            parts.append("</ul>")
            in_ul = False
        if in_ol:
            parts.append("</ol>")
            in_ol = False

    def flush_pre() -> None:
        nonlocal pre_lines, in_pre
        if in_pre:
            parts.append(f"<pre>{html.escape(chr(10).join(pre_lines), quote=False)}</pre>")
            pre_lines = []
            in_pre = False

    for raw_line in lines:
        line = raw_line.rstrip()
        stripped = line.strip()

        if stripped.startswith("```"):
            if in_pre:
                flush_pre()
            else:
                flush_paragraph()
                close_lists()
                in_pre = True
                pre_lines = []
            continue

        if in_pre:
            pre_lines.append(line)
            continue

        if not stripped:
            flush_paragraph()
            close_lists()
            continue

        if stripped.startswith("### "):
            flush_paragraph(); close_lists()
            parts.append(f"<h3>{_inline_markdown_to_html(stripped[4:].strip())}</h3>")
            continue
        if stripped.startswith("## "):
            flush_paragraph(); close_lists()
            parts.append(f"<h2>{_inline_markdown_to_html(stripped[3:].strip())}</h2>")
            continue
        if stripped.startswith("# "):
            flush_paragraph(); close_lists()
            parts.append(f"<h1>{_inline_markdown_to_html(stripped[2:].strip())}</h1>")
            continue

        if stripped.startswith(("- ", "* ")):
            flush_paragraph()
            if in_ol:
                parts.append("</ol>"); in_ol = False
            if not in_ul:
                parts.append("<ul>"); in_ul = True
            parts.append(f"<li>{_inline_markdown_to_html(stripped[2:].strip())}</li>")
            continue

        numbered = stripped.split(". ", 1)
        if len(numbered) == 2 and numbered[0].isdigit():
            flush_paragraph()
            if in_ul:
                parts.append("</ul>"); in_ul = False
            if not in_ol:
                parts.append("<ol>"); in_ol = True
            parts.append(f"<li>{_inline_markdown_to_html(numbered[1].strip())}</li>")
            continue

        close_lists()
        paragraph.append(_inline_markdown_to_html(stripped))

    flush_pre()
    flush_paragraph()
    close_lists()

    body = "\n".join(parts) if parts else "<p></p>"
    return f"<html><body>\n{body}\n</body></html>"


def credential_store_secret(service: str, username: str) -> str:
    if not keyring:
        fail("keyring is not installed; set OCTANE_CLIENT_SECRET or run with uv so keyring is available")
    try:
        secret = keyring.get_password(service, username)
    except KeyringError as e:
        fail(
            "Octane keyring backend could not read the selected entry",
            error_code="OCTANE_KEYRING_BACKEND_FAILURE",
            keyring_user=username,
            details=str(e),
        )
    if not secret:
        fail(
            "Selected Octane keyring entry has no client secret",
            error_code="OCTANE_KEYRING_ENTRY_MISSING",
            keyring_user=username,
        )
    return secret


def octane_client_id() -> str:
    # In the normal keyring flow, the keyring username is the Octane API
    # client ID. OCTANE_CLIENT_ID remains an optional override, but .env does
    # not need to duplicate it when OCTANE_CLIENT_SECRET_KEYRING_USER is set.
    runtime = _require_runtime()
    return runtime.client_id or runtime.client_secret_keyring_user


def octane_client_secret() -> str:
    runtime = _require_runtime()
    if runtime.client_secret_keyring_user:
        return credential_store_secret("AgentDevelopmentToolkit:alm-octane", runtime.client_secret_keyring_user)
    return runtime.client_secret


def require_base_url() -> str:
    base_url = _require_runtime().base_url
    if not base_url:
        fail("Missing OCTANE_BASE_URL environment variable")
    return base_url


def _api_root(
    shared_space_id: Optional[str] = None,
    workspace_id: Optional[str] = None,
) -> str:
    """Return the workspace-scoped API root."""
    runtime = _require_runtime()
    base = require_base_url()
    shared_space_id = shared_space_id or runtime.shared_space_id
    workspace_id = workspace_id or runtime.workspace_id
    return f"{base}/api/shared_spaces/{shared_space_id}/workspaces/{workspace_id}"


def entity_url(
    entity_type: str,
    entity_id: Optional[str] = None,
    workspace_id: Optional[str] = None,
    shared_space_id: Optional[str] = None,
) -> str:
    root = _api_root(shared_space_id, workspace_id)
    url = f"{root}/{entity_type}"
    return f"{url}/{entity_id}" if entity_id else url


# ---------------------------------------------------------------------------
# Session-based authentication (cookie jar)
# ---------------------------------------------------------------------------
_session: Optional[requests.Session] = None


def get_session() -> requests.Session:
    """Return an authenticated requests.Session (cached)."""
    global _session
    if _session is not None:
        return _session

    client_id = octane_client_id()
    client_secret = octane_client_secret()
    if not client_id or not client_secret:
        fail(
            "Missing auth configuration",
            required=["OCTANE_CLIENT_SECRET_KEYRING_USER with stored secret, or OCTANE_CLIENT_ID + OCTANE_CLIENT_SECRET"],
        )

    base = require_base_url()
    s = requests.Session()
    s.headers.update({
        "Content-Type": "application/json",
        "Accept": "application/json",
    })

    # Octane sign-in endpoint — returns an LWSSO_COOKIE_KEY cookie
    sign_in_url = f"{base}/authentication/sign_in"
    try:
        resp = s.post(
            sign_in_url,
            json={"client_id": client_id, "client_secret": client_secret},
            timeout=_require_runtime().timeout,
            allow_redirects=False,
        )
    except requests.RequestException as e:
        fail("Authentication request failed", details=str(e), url=sign_in_url)

    if not resp.ok:
        if resp.status_code == 403:
            fail(
                "Octane authorization failed",
                error_code="OCTANE_REMOTE_AUTHORIZATION_FAILED",
                status=resp.status_code,
                url=sign_in_url,
            )
        fail(
            "Octane authentication failed",
            error_code="OCTANE_REMOTE_AUTHENTICATION_FAILED",
            status=resp.status_code,
            url=sign_in_url,
        )

    _session = s
    return s


# ---------------------------------------------------------------------------
# Generic request helper
# ---------------------------------------------------------------------------
def request_json(
    method: str,
    url: str,
    payload: Optional[Dict[str, Any]] = None,
    params: Optional[Dict[str, Any]] = None,
    exit_on_error: bool = True,
) -> Dict[str, Any]:
    """Execute an authenticated request and return a JSON envelope."""
    s = get_session()
    try:
        resp = s.request(
            method=method,
            url=url,
            json=payload,
            params=params,
            timeout=_require_runtime().timeout,
            allow_redirects=False,
        )
    except requests.RequestException as e:
        if exit_on_error:
            fail("Request failed", details=str(e), url=url)
        return {"ok": False, "error": "Request failed", "details": str(e), "url": url}

    content_type = resp.headers.get("content-type", "")
    try:
        data = resp.json() if "json" in content_type else {"raw": resp.text}
    except Exception:
        data = {"raw": resp.text}

    if not resp.ok:
        if exit_on_error:
            fail("Octane API error", status=resp.status_code, response=data, url=url)
        return {"ok": False, "error": "Octane API error", "status": resp.status_code, "response": data, "url": url}

    return {"ok": True, "status": resp.status_code, "data": data, "url": url}


def update_backlog_fields(url: str, payload: Dict[str, Any]) -> Dict[str, Any]:
    """Resolve and verify one existing-entity update; never replay a mutation."""
    root, collection, entity_id = url.rsplit("/", 2)
    try:
        return octane_generic.GenericAPI(root, request_json).update_entity(collection, entity_id, payload)
    except octane_generic.GenericError as exc:
        result = dict(exc.result or {"ok": False, "error": str(exc)})
        result.update(ok=False, mutation={"outcome": "not_attempted"})
        return result


def _fail_backlog_update(result: Dict[str, Any], **extra: Any) -> None:
    """Keep sanitized mutation and verification evidence in legacy CLI errors."""
    details = {**extra, **result}
    message = details.pop("error", "Octane update failed")
    fail(message, **details)


def request_multipart(
    url: str,
    files: Dict[str, Any],
    exit_on_error: bool = True,
) -> Dict[str, Any]:
    """POST multipart/form-data and return a JSON envelope.

    The authenticated session has a default JSON Content-Type header. Remove it
    for this one request so requests can generate the multipart boundary.
    """
    s = get_session()
    headers = {"Accept": "application/json"}
    old_content_type = s.headers.pop("Content-Type", None)
    try:
        resp = s.post(
            url,
            files=files,
            headers=headers,
            timeout=_require_runtime().timeout,
            allow_redirects=False,
        )
    except requests.RequestException as e:
        if exit_on_error:
            fail("Request failed", details=str(e), url=url)
        return {"ok": False, "error": "Request failed", "details": str(e), "url": url}
    finally:
        if old_content_type is not None:
            s.headers["Content-Type"] = old_content_type

    content_type = resp.headers.get("content-type", "")
    try:
        data = resp.json() if "json" in content_type else {"raw": resp.text}
    except Exception:
        data = {"raw": resp.text}

    if not resp.ok:
        if exit_on_error:
            fail("Octane API error", status=resp.status_code, response=data, url=url)
        return {"ok": False, "error": "Octane API error", "status": resp.status_code, "response": data, "url": url}

    return {"ok": True, "status": resp.status_code, "data": data, "url": url}


def _extract_entity(data: Dict[str, Any]) -> Dict[str, Any]:
    """Return a single entity object from an Octane GET/PUT/POST envelope."""
    inner = data.get("data") if isinstance(data, dict) else None
    if isinstance(inner, list) and inner:
        first = inner[0]
        return first if isinstance(first, dict) else {}
    if isinstance(inner, dict):
        if isinstance(inner.get("data"), list) and inner["data"]:
            first = inner["data"][0]
            return first if isinstance(first, dict) else {}
        return inner
    return {}


def _extract_entities(data: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Return entity objects from an Octane list envelope."""
    inner = data.get("data") if isinstance(data, dict) else None
    if isinstance(inner, list):
        return [item for item in inner if isinstance(item, dict)]
    if isinstance(inner, dict) and isinstance(inner.get("data"), list):
        return [item for item in inner["data"] if isinstance(item, dict)]
    return []


def _multi_value_text(values: Optional[List[str]]) -> str:
    """Format repeated CLI values as readable rich text paragraphs."""
    if not values:
        return ""
    cleaned = [v.strip() for v in values if v and v.strip()]
    if not cleaned:
        return ""
    if len(cleaned) == 1:
        return cleaned[0]
    return "\n".join(f"- {v}" for v in cleaned)


def build_story_description(description: str, acceptance_criteria: str) -> str:
    """Build a consistent story description that includes acceptance criteria."""
    desc = description.strip()
    ac = acceptance_criteria.strip()
    if not ac:
        return desc
    return f"{desc}\n\nAcceptance Criteria:\n{ac}"


def strip_rendered_acceptance_criteria(description: str) -> str:
    """Remove the CLI-rendered Acceptance Criteria section from a description."""
    marker = "\n\nAcceptance Criteria:"
    if marker in description:
        return description.split(marker, 1)[0].strip()
    return description.strip()


def _subtype_id(item: Dict[str, Any]) -> str:
    subtype = item.get("subtype", "")
    if isinstance(subtype, dict):
        return str(subtype.get("id") or subtype.get("logical_name") or subtype.get("name") or "")
    return str(subtype)


def normalize_entity_collection(entity_type: str) -> str:
    """Normalize Octane UI/singular/plural entity names to API collections."""
    value = entity_type.strip().lower().replace("-", "_")
    mapping = {
        "work_item": "work_items",
        "work_items": "work_items",
        "defect": "defects",
        "defects": "defects",
        "story": "stories",
        "stories": "stories",
        "feature": "features",
        "features": "features",
        "test": "tests",
        "tests": "tests",
    }
    return mapping.get(value, value if value.endswith("s") else f"{value}s")


def _normalize_label(value: str) -> str:
    """Normalize UI labels/logical names for loose matching."""
    return "".join(ch for ch in value.lower() if ch.isalnum())


def _metadata_entity_names(collection: str) -> List[str]:
    value = collection.strip().lower().replace("-", "_")
    if value in {"features", "feature"}:
        return ["feature", "features", "work_item", "work_items"]
    if value in {"stories", "story"}:
        return ["story", "stories", "work_item", "work_items"]
    if value in {"defects", "defect"}:
        return ["defect", "defects", "work_item", "work_items"]
    return [value.rstrip("s"), value]


def get_entity_fields_metadata(
    entity_type: str,
    workspace_id: Optional[str] = None,
    shared_space_id: Optional[str] = None,
) -> Tuple[List[Dict[str, Any]], Optional[Dict[str, Any]]]:
    """Return field metadata for an Octane entity, trying singular/plural names."""
    errors: List[Dict[str, Any]] = []
    root = _api_root(shared_space_id, workspace_id)

    # Current Octane exposes field metadata through /metadata/fields filtered by
    # entity_name. Keep the older /metadata/entities/<entity>/fields attempts as
    # fallback for compatibility with older deployments.
    for metadata_name in _metadata_entity_names(entity_type):
        url = f"{root}/metadata/fields"
        result = request_json(
            "GET",
            url,
            params={"query": f'"entity_name EQ ^{metadata_name}^"', "limit": 5000},
            exit_on_error=False,
        )
        if result.get("ok"):
            fields = _extract_entities(result)
            if fields:
                return fields, {"metadata_entity": metadata_name, "url": url, "source": "metadata/fields"}
        errors.append({"metadata_entity": metadata_name, "result": result, "source": "metadata/fields"})

    for metadata_name in _metadata_entity_names(entity_type):
        url = f"{root}/metadata/entities/{metadata_name}/fields"
        result = request_json("GET", url, params={"limit": 1000}, exit_on_error=False)
        if result.get("ok"):
            fields = _extract_entities(result)
            if fields:
                return fields, {"metadata_entity": metadata_name, "url": url, "source": "metadata/entities/*/fields"}
        errors.append({"metadata_entity": metadata_name, "result": result, "source": "metadata/entities/*/fields"})
    return [], {"errors": errors}


def _field_names(field: Dict[str, Any]) -> List[str]:
    values: List[str] = []
    for key in ("name", "label", "logical_name", "id", "title"):
        value = field.get(key)
        if value is not None:
            values.append(str(value))
    return values


def resolve_field_name(
    entity_type: str,
    label: str,
    workspace_id: str,
    shared_space_id: str,
    *,
    for_update: bool = False,
) -> Tuple[Optional[str], Optional[Dict[str, Any]], Dict[str, Any]]:
    """Resolve a UI field label (for example Security Assessment) to API name."""
    env_key = f"OCTANE_{_normalize_label(label).upper()}_FIELD"
    field_overrides = dict(_require_runtime().field_overrides)
    # Friendly explicit aliases for the threat-modelling fields.
    if _normalize_label(label) == "securityassessment":
        override = field_overrides.get("OCTANE_SECURITY_ASSESSMENT_FIELD") or field_overrides.get(env_key)
    elif _normalize_label(label) in ("securityimpact", "securityimpactlevel"):
        override = field_overrides.get("OCTANE_SECURITY_IMPACT_LEVEL_FIELD") or field_overrides.get(env_key)
    elif _normalize_label(label) == "securitysource":
        override = field_overrides.get("OCTANE_SECURITY_SOURCE_FIELD") or field_overrides.get(env_key)
    elif _normalize_label(label) == "cvssscore":
        override = field_overrides.get("OCTANE_CVSS_SCORE_FIELD") or field_overrides.get(env_key)
    elif _normalize_label(label) == "cvssvector":
        override = field_overrides.get("OCTANE_CVSS_VECTOR_FIELD") or field_overrides.get(env_key)
    elif _normalize_label(label) == "allowdelete":
        override = field_overrides.get("OCTANE_ALLOW_DELETE_FIELD") or field_overrides.get(env_key)
    else:
        override = field_overrides.get(env_key)
    if for_update:
        collection_url = entity_url(entity_type, None, workspace_id, shared_space_id)
        api = octane_generic.GenericAPI(collection_url.rsplit("/", 1)[0], request_json)
        try:
            fields = api.field_metadata(entity_type)["data"]["data"]
            mapped = octane_generic.resolve_update_fields({override or label: None}, fields)
            name = next(iter(mapped))
            definition = next(field for field in fields if field["name"] == name)
            return name, definition, {"source": "metadata", "requested": override or label}
        except octane_generic.GenericError as exc:
            result = dict(exc.result or {"ok": False, "error": str(exc)})
            result.update(ok=False, mutation={"outcome": "not_attempted"})
            _fail_backlog_update(result)
    if override:
        return override, None, {"source": "environment", "env": env_key}

    fields, meta = get_entity_fields_metadata(entity_type, workspace_id, shared_space_id)
    target = _normalize_label(label)
    for field in fields:
        for candidate in _field_names(field):
            if _normalize_label(candidate) == target:
                api_name = str(field.get("name") or field.get("logical_name") or field.get("id") or "")
                if api_name:
                    return api_name, field, {"source": "metadata", "metadata": meta}

    # Fall back to common custom-field naming conventions before failing.
    common = {
        "securityassessment": ["security_assessment_udf", "security_assessment", "udf_security_assessment"],
        # Workspace custom field logical name for the Security Impact list.
        # Keep legacy names as fallbacks for older/nonstandard workspaces.
        "securityimpact": ["security_impact_f_udf", "security_impact_level", "udf_security_impact_level", "security_impact_level_udf"],
        "securityimpactlevel": ["security_impact_f_udf", "security_impact_level", "udf_security_impact_level", "security_impact_level_udf"],
        "securitysource": ["security_source_udf", "security_source", "udf_security_source"],
        "cvssscore": ["cvss_score_udf", "cvss_score", "udf_cvss_score"],
        "cvssvector": ["cvss_vector_udf", "cvss_vector", "udf_cvss_vector"],
        "allowdelete": ["allow_delete_udf", "allow_delete", "udf_allow_delete"],
    }.get(target, [])
    if common:
        return common[0], None, {"source": "convention", "tried": common, "metadata": meta}

    candidates = [
        {"name": field.get("name"), "label": field.get("label"), "logical_name": field.get("logical_name"), "field_type": field.get("field_type") or field.get("data_type")}
        for field in fields
        if any(target in _normalize_label(str(v)) or "security" in str(v).lower() for v in _field_names(field))
    ]
    return None, None, {"metadata": meta, "field_candidates": candidates}


def _looks_like_list_field(field_meta: Optional[Dict[str, Any]], field_name: str, value: str) -> bool:
    if value.startswith("list_node."):
        return True
    if field_meta:
        joined = " ".join(str(field_meta.get(k, "")) for k in ("field_type", "data_type", "type", "subtype", "reference_type"))
        if "list" in joined.lower():
            return True
    return field_name == "security_impact_f_udf" or field_name.endswith("_level") or "impact_level" in field_name


def _resolve_list_node_id(
    value: str,
    workspace_id: Optional[str] = None,
    shared_space_id: Optional[str] = None,
) -> str:
    """Resolve a list_node ID by exact name when a raw name is supplied."""
    if value.startswith("list_node."):
        return value
    root = _api_root(shared_space_id, workspace_id)
    result = request_json(
        "GET",
        f"{root}/list_nodes",
        params={"query": f'"name EQ ^{value}^"', "fields": "id,name,logical_name,activity_level", "limit": 20},
        exit_on_error=False,
    )
    if result.get("ok"):
        nodes = _extract_entities(result)
        active = [n for n in nodes if str(n.get("name", "")).lower() == value.lower() and n.get("activity_level", 0) == 0]
        if len(active) == 1:
            return str(active[0]["id"])
        exact = [n for n in nodes if str(n.get("name", "")).lower() == value.lower()]
        if len(exact) == 1:
            return str(exact[0]["id"])
    return value


def _format_field_value(field_name: str, value: str, field_meta: Optional[Dict[str, Any]]) -> Any:
    """Format an update value for Octane. List-node IDs become references."""
    if "cvss" in field_name.lower() and "score" in field_name.lower():
        try:
            return float(value)
        except ValueError:
            return value
    if field_name == "security_source_udf":
        return {"type": "list_node", "id": _resolve_list_node_id(value)}
    if _looks_like_list_field(field_meta, field_name, value):
        node_id = value if value.startswith("list_node.") else value
        if not node_id.startswith("list_node.") and ("security_impact_level" in field_name or field_name == "security_impact_f_udf"):
            # Common Octane custom-list convention; callers should pass an exact
            # list_node ID if their workspace uses a different list logical name.
            normalized = "".join(ch if ch.isalnum() else "_" for ch in value.lower()).strip("_")
            list_name = "security_impact" if field_name == "security_impact_f_udf" else "security_impact_level"
            node_id = f"list_node.{list_name}.{normalized}"
        if node_id.startswith("list_node."):
            return {"type": "list_node", "id": node_id}
    return value


def normalize_phase_id(entity_kind: str, phase: str) -> str:
    """Accept either a full phase ID or a human shorthand such as 'fixed'."""
    value = phase.strip()
    if value.startswith("phase."):
        return value

    compact = "".join(ch for ch in value.lower() if ch.isalnum())
    aliases = {
        "open": "opened",
        "inprogress": "inprogress",
        "proposedclose": "proposedclosed",
        "proposedclosed": "proposedclosed",
    }
    logical = aliases.get(compact, compact)
    return f"phase.{entity_kind}.{logical}"


def phase_update_error_hint(entity_kind: str, phase: str) -> Dict[str, Any]:
    return {
        "phase": phase,
        "hint": (
            f"Phase changes must follow the workspace workflow and use a valid phase ID, "
            f"for example phase.{entity_kind}.fixed. Run list-phases --entity {entity_kind} "
            "to inspect available phase IDs, or move through the required intermediate phase first."
        ),
    }


# ===================================================================
# Commands — each maps 1:1 to an MCP tool from mcp-octane-server
# ===================================================================

# ---- Entity getters (defect / feature / story) --------------------
def get_entity(
    entity_type: str,
    entity_id: str,
    fields: Optional[str] = None,
    workspace_id: Optional[str] = None,
    shared_space_id: Optional[str] = None,
) -> None:
    url = entity_url(entity_type, entity_id, workspace_id, shared_space_id)
    # Keep the legacy printing adapter while generic operations return data.
    result = octane_generic.fetch_entity_record(request_json, url, fields, exit_on_error=True)
    print(json.dumps(result, ensure_ascii=False))


def get_work_item(
    entity_id: str,
    fields: str = "id,name,description,subtype,phase,owner,author,priority,severity",
    workspace_id: Optional[str] = None,
    shared_space_id: Optional[str] = None,
) -> None:
    """Fetch a generic work item without assuming defect/story subtype."""
    get_entity("work_items", entity_id, fields, workspace_id, shared_space_id)


# ---- search-all ---------------------------------------------------
def search_all(
    query: str,
    limit: int = 50,
    workspace_id: Optional[str] = None,
    shared_space_id: Optional[str] = None,
) -> None:
    """Search work items using Octane BK syntax (mirrors MCP search_all)."""
    # If the query is already in Octane query language, pass it through;
    # otherwise wrap in a BK (begins/contains) search on name + description.
    if "=" in query or " BK " in query.upper():
        query_param = query
    else:
        query_param = f"(name BK '*{query}*'||description BK '*{query}*')"

    url = entity_url("work_items", None, workspace_id, shared_space_id)
    params = {
        "query": f'"{query_param}"',
        "fields": "id,name,subtype,phase,owner",
        "limit": limit,
    }
    print(json.dumps(request_json("GET", url, params=params), ensure_ascii=False))


# ---- create-defect ------------------------------------------------
def normalize_severity_id(severity: str) -> str:
    value = severity.strip()
    if value.startswith("list_node."):
        return value
    mapping = {
        "low": "list_node.severity.low",
        "medium": "list_node.severity.medium",
        "high": "list_node.severity.high",
        "critical": "list_node.severity.critical",
    }
    return mapping.get(value.lower(), value)


def create_defect(
    name: str,
    description: str,
    severity: str,
    priority: Optional[str] = None,
    parent_feature_id: Optional[str] = None,
    security_source: Optional[str] = None,
    cvss_score: Optional[str] = None,
    cvss_vector: Optional[str] = None,
    owner_id: Optional[str] = None,
    target_release_id: Optional[str] = None,
    workspace_id: Optional[str] = None,
    shared_space_id: Optional[str] = None,
) -> None:
    url = entity_url("defects", None, workspace_id, shared_space_id)
    payload: Dict[str, Any] = {
        "data": [
            {
                "name": name,
                "description": format_octane_description_html(description),
                "severity": {"type": "list_node", "id": normalize_severity_id(severity)},
                "phase": {"type": "phase", "id": "phase.defect.new"},
            }
        ]
    }
    if priority:
        payload["data"][0]["priority"] = {"type": "list_node", "id": priority}
    if parent_feature_id:
        payload["data"][0]["parent"] = {"type": "work_item", "id": parent_feature_id}
    if owner_id:
        payload["data"][0]["owner"] = {"type": "workspace_user", "id": owner_id}
    if target_release_id:
        payload["data"][0]["release"] = {"type": "release", "id": target_release_id}
    if security_source:
        field_name, field_meta, _resolution = resolve_field_name("defect", "Security Source", workspace_id, shared_space_id)
        payload["data"][0][field_name or "security_source_udf"] = _format_field_value(field_name or "security_source_udf", security_source, field_meta)
    cvss_field_names: List[str] = []
    if cvss_score:
        field_name, field_meta, _resolution = resolve_field_name("defect", "CVSS Score", workspace_id, shared_space_id)
        if not field_name:
            fail("Could not resolve defect CVSS Score field", resolution=_resolution)
        payload["data"][0][field_name] = _format_field_value(field_name, cvss_score, field_meta)
        cvss_field_names.append(field_name)
    if cvss_vector:
        field_name, field_meta, _resolution = resolve_field_name("defect", "CVSS Vector", workspace_id, shared_space_id)
        if not field_name:
            fail("Could not resolve defect CVSS Vector field", resolution=_resolution)
        payload["data"][0][field_name] = _format_field_value(field_name, cvss_vector, field_meta)
        cvss_field_names.append(field_name)
    result = request_json("POST", url, payload=payload, exit_on_error=False)
    if result.get("ok"):
        created = _extract_entity(result)
        defect_id = str(created.get("id") or "") if created else ""
        if defect_id:
            verify_field_set = ["id", "name", "description", "severity", "phase", "owner", "author", "priority", "parent", "release", "security_source_udf"]
            for field_name in cvss_field_names:
                if field_name not in verify_field_set:
                    verify_field_set.append(field_name)
            verify_fields = ",".join(verify_field_set)
            verify = request_json("GET", entity_url("defects", defect_id, workspace_id, shared_space_id), params={"fields": verify_fields}, exit_on_error=False)
            if verify.get("ok"):
                result["verified"] = _extract_entity(verify)
    print(json.dumps(result, ensure_ascii=False))


# ---- create-feature ----------------------------------------------
def create_feature(
    name: str,
    description: str,
    parent_id: Optional[str] = None,
    owner_id: Optional[str] = None,
    workspace_id: Optional[str] = None,
    shared_space_id: Optional[str] = None,
) -> None:
    """Create a feature/backlog item."""
    url = entity_url("features", None, workspace_id, shared_space_id)
    feature: Dict[str, Any] = {
        "name": name,
        "description": description,
        "phase": {"type": "phase", "id": "phase.feature.new"},
    }
    if parent_id:
        feature["parent"] = {"type": "work_item", "id": parent_id}
    if owner_id:
        feature["owner"] = {"type": "workspace_user", "id": owner_id}

    result = request_json("POST", url, payload={"data": [feature]}, exit_on_error=False)
    if result.get("ok"):
        created = _extract_entity(result)
        feature_id = str(created.get("id") or "") if created else ""
        if feature_id:
            verify = request_json(
                "GET",
                entity_url("features", feature_id, workspace_id, shared_space_id),
                params={"fields": "id,name,description,phase,owner,parent"},
                exit_on_error=False,
            )
            if verify.get("ok"):
                result["verified"] = _extract_entity(verify)
    print(json.dumps(result, ensure_ascii=False))


# ---- update-feature ----------------------------------------------
def update_feature(
    feature_id: str,
    name: Optional[str] = None,
    description: Optional[str] = None,
    owner_id: Optional[str] = None,
    workspace_id: Optional[str] = None,
    shared_space_id: Optional[str] = None,
) -> None:
    """Update feature name, description, and/or owner."""
    fields: Dict[str, Any] = {}
    if name:
        fields["name"] = name
    if description is not None:
        fields["description"] = description
    if owner_id:
        fields["owner"] = {"type": "workspace_user", "id": owner_id}
    if not fields:
        fail("No fields provided to update (need --name, --description, and/or --owner-id)")

    url = entity_url("features", feature_id, workspace_id, shared_space_id)
    current = request_json(
        "GET",
        url,
        params={"fields": "id,client_lock_stamp"},
        exit_on_error=False,
    )
    current_entity = _extract_entity(current) if current.get("ok") else {}
    if "client_lock_stamp" in current_entity:
        fields["client_lock_stamp"] = current_entity["client_lock_stamp"]

    result = update_backlog_fields(url, fields)
    if not result.get("ok"):
        _fail_backlog_update(result)

    verify = request_json(
        "GET",
        url,
        params={"fields": "id,name,description,phase,owner,parent,client_lock_stamp"},
        exit_on_error=False,
    )
    if verify.get("ok"):
        result["verified"] = _extract_entity(verify)
    print(json.dumps(result, ensure_ascii=False))


# ---- update-defect ------------------------------------------------
def update_defect(
    defect_id: str,
    phase: Optional[str] = None,
    severity: Optional[str] = None,
    workspace_id: Optional[str] = None,
    shared_space_id: Optional[str] = None,
) -> None:
    fields: Dict[str, Any] = {}
    normalized_phase: Optional[str] = None
    if phase:
        normalized_phase = normalize_phase_id("defect", phase)
        fields["phase"] = {"type": "phase", "id": normalized_phase}
    if severity:
        fields["severity"] = {"type": "list_node", "id": normalize_severity_id(severity)}
    if not fields:
        fail("No fields provided to update (need --phase and/or --severity)")

    url = entity_url("defects", defect_id, workspace_id, shared_space_id)

    # Octane recommends sending client_lock_stamp on all PUT requests. Fetch it
    # immediately before updating so phase transitions do not fail due to stale
    # client state and conflicts are reported clearly.
    current = request_json(
        "GET",
        url,
        params={"fields": "id,phase,severity,client_lock_stamp"},
        exit_on_error=False,
    )
    current_entity = _extract_entity(current) if current.get("ok") else {}
    if "client_lock_stamp" in current_entity:
        fields["client_lock_stamp"] = current_entity["client_lock_stamp"]

    result = update_backlog_fields(url, fields)
    if not result.get("ok"):
        extra = phase_update_error_hint("defect", normalized_phase or phase) if phase else {}
        _fail_backlog_update(result, **extra)

    verify = request_json(
        "GET",
        url,
        params={"fields": "id,name,phase,severity,client_lock_stamp"},
        exit_on_error=False,
    )
    if verify.get("ok"):
        result["verified"] = _extract_entity(verify)
    print(json.dumps(result, ensure_ascii=False))


# ---- create-story -------------------------------------------------
def create_story(
    name: str,
    description: str,
    workspace_id: Optional[str] = None,
    shared_space_id: Optional[str] = None,
) -> None:
    url = entity_url("stories", None, workspace_id, shared_space_id)
    payload: Dict[str, Any] = {
        "data": [
            {
                "name": name,
                "description": description,
                "phase": {"type": "phase", "id": "phase.story.new"},
            }
        ]
    }
    print(json.dumps(request_json("POST", url, payload=payload), ensure_ascii=False))


# ---- create-story-under-feature -----------------------------------
def create_story_under_feature(
    feature_id: str,
    name: str,
    description: str,
    acceptance_criteria: Optional[List[str]] = None,
    priority: Optional[str] = None,
    owner_id: Optional[str] = None,
    workspace_id: Optional[str] = None,
    shared_space_id: Optional[str] = None,
) -> None:
    """Create a story with a feature as parent and acceptance criteria."""
    ac_text = _multi_value_text(acceptance_criteria)
    full_description = build_story_description(description, ac_text)
    url = entity_url("stories", None, workspace_id, shared_space_id)
    story: Dict[str, Any] = {
        "name": name,
        "description": full_description,
        "phase": {"type": "phase", "id": "phase.story.new"},
        "parent": {"type": "work_item", "id": feature_id},
    }
    if ac_text:
        # Keep acceptance criteria in the rich description and also populate the
        # standard field when the workspace exposes it.
        story["acceptance_criteria"] = ac_text
    if priority:
        story["priority"] = {"type": "list_node", "id": priority}
    if owner_id:
        story["owner"] = {"type": "workspace_user", "id": owner_id}

    payload = {"data": [story]}
    result = request_json("POST", url, payload=payload, exit_on_error=False)

    # Some Octane workspaces do not expose acceptance_criteria. The full text is
    # already in description, so retry without the separate field if necessary.
    warning: Optional[Dict[str, Any]] = None
    if not result.get("ok") and ac_text and "acceptance_criteria" in story:
        warning = {
            "message": "Retried without separate acceptance_criteria field; criteria remain in description.",
            "first_error": result,
        }
        story.pop("acceptance_criteria", None)
        result = request_json("POST", url, payload={"data": [story]}, exit_on_error=False)

    if not result.get("ok"):
        fail("Octane API error", status=result.get("status"), response=result.get("response"), url=url)

    created = _extract_entity(result)
    story_id = str(created.get("id", ""))
    if story_id:
        verify = request_json(
            "GET",
            entity_url("stories", story_id, workspace_id, shared_space_id),
            params={"fields": "id,name,description,acceptance_criteria,phase,owner,priority,parent,subtype"},
            exit_on_error=False,
        )
        if verify.get("ok"):
            result["verified"] = _extract_entity(verify)
    if warning:
        result["warning"] = warning
    print(json.dumps(result, ensure_ascii=False))


# ---- story parent / feature children ------------------------------
def get_story_parent_feature(
    story_id: str,
    workspace_id: Optional[str] = None,
    shared_space_id: Optional[str] = None,
) -> None:
    """Fetch a story and resolve its parent feature/work item."""
    story_result = request_json(
        "GET",
        entity_url("stories", story_id, workspace_id, shared_space_id),
        params={"fields": "id,name,description,phase,owner,parent,subtype"},
        exit_on_error=False,
    )
    if not story_result.get("ok"):
        fail("Octane API error", status=story_result.get("status"), response=story_result.get("response"), url=story_result.get("url"))

    story = _extract_entity(story_result)
    parent = story.get("parent") if isinstance(story.get("parent"), dict) else None
    output: Dict[str, Any] = {"ok": True, "data": {"story": story, "parent_feature": None}}
    if not parent or not parent.get("id"):
        output["data"]["message"] = "Story has no parent feature."
        print(json.dumps(output, ensure_ascii=False))
        return

    parent_id = str(parent["id"])
    feature_result = request_json(
        "GET",
        entity_url("features", parent_id, workspace_id, shared_space_id),
        params={"fields": "id,name,description,phase,owner,parent,subtype"},
        exit_on_error=False,
    )
    output["data"]["parent_feature"] = _extract_entity(feature_result) if feature_result.get("ok") else parent
    if not feature_result.get("ok"):
        output["data"]["parent_lookup_warning"] = feature_result
    print(json.dumps(output, ensure_ascii=False))


def list_feature_items(
    feature_id: str,
    limit: int = 100,
    workspace_id: Optional[str] = None,
    shared_space_id: Optional[str] = None,
) -> None:
    """List stories and issue/defect work items whose parent is a feature."""
    url = entity_url("work_items", None, workspace_id, shared_space_id)
    params = {
        "query": f'"parent={{id={feature_id}}}"',
        "fields": "id,name,description,phase,owner,author,subtype,priority,severity,parent",
        "limit": limit,
    }
    result = request_json("GET", url, params=params, exit_on_error=False)
    if not result.get("ok"):
        fail("Octane API error", status=result.get("status"), response=result.get("response"), url=url)
    items = _extract_entities(result)
    result["summary"] = {
        "feature_id": feature_id,
        "total": len(items),
        "stories": [item for item in items if _subtype_id(item).endswith("story")],
        "issues": [item for item in items if _subtype_id(item).endswith("defect")],
    }
    print(json.dumps(result, ensure_ascii=False))


# ---- feature security / threat-modelling fields -------------------
def update_feature_security(
    feature_id: str,
    security_assessment: Optional[str] = None,
    security_impact_level: Optional[str] = None,
    workspace_id: Optional[str] = None,
    shared_space_id: Optional[str] = None,
) -> None:
    """Read a feature, then update threat-modelling security fields."""
    if security_assessment is None and security_impact_level is None:
        fail("No fields provided to update (need --security-assessment and/or --security-impact-level)")

    url = entity_url("features", feature_id, workspace_id, shared_space_id)
    field_specs = [
        ("Security Assessment", security_assessment),
        ("Security Impact", security_impact_level),
    ]

    resolved: Dict[str, Dict[str, Any]] = {}
    read_fields = ["id", "name", "description", "phase", "owner", "client_lock_stamp"]
    for label, value in field_specs:
        if value is None:
            continue
        field_name, field_meta, resolution = resolve_field_name("features", label, workspace_id, shared_space_id, for_update=True)
        if not field_name:
            fail(f"Could not resolve Octane field for '{label}'", **resolution)
        resolved[label] = {"name": field_name, "metadata": field_meta, "resolution": resolution}
        read_fields.append(field_name)

    current = request_json(
        "GET",
        url,
        params={"fields": ",".join(dict.fromkeys(read_fields))},
        exit_on_error=False,
    )
    if not current.get("ok"):
        fail("Octane API error", status=current.get("status"), response=current.get("response"), url=url)
    current_entity = _extract_entity(current)

    payload: Dict[str, Any] = {}
    if "client_lock_stamp" in current_entity:
        payload["client_lock_stamp"] = current_entity["client_lock_stamp"]
    if security_assessment is not None:
        spec = resolved["Security Assessment"]
        payload[spec["name"]] = _format_field_value(spec["name"], security_assessment, spec.get("metadata"))
    if security_impact_level is not None:
        spec = resolved["Security Impact"]
        payload[spec["name"]] = _format_field_value(spec["name"], security_impact_level, spec.get("metadata"))

    result = update_backlog_fields(url, payload)
    if not result.get("ok"):
        _fail_backlog_update(
            result,
            resolved_fields=resolved,
            hint=(
                "If this workspace uses different custom field logical names, set "
                "OCTANE_SECURITY_ASSESSMENT_FIELD and OCTANE_SECURITY_IMPACT_LEVEL_FIELD in the skill .env. "
                "For Security Impact, pass the exact list_node ID when a plain label is rejected."
            ),
        )

    verify = request_json(
        "GET",
        url,
        params={"fields": ",".join(dict.fromkeys(read_fields))},
        exit_on_error=False,
    )
    if verify.get("ok"):
        result["verified"] = _extract_entity(verify)
    result["before"] = current_entity
    result["resolved_fields"] = resolved
    print(json.dumps(result, ensure_ascii=False))


# ---- update-story -------------------------------------------------
def update_story(
    story_id: str,
    name: Optional[str] = None,
    description: Optional[str] = None,
    acceptance_criteria: Optional[List[str]] = None,
    workspace_id: Optional[str] = None,
    shared_space_id: Optional[str] = None,
) -> None:
    """Update story name, description, and/or acceptance criteria."""
    ac_text = _multi_value_text(acceptance_criteria)
    fields: Dict[str, Any] = {}
    if name:
        fields["name"] = name
    if description is not None:
        fields["description"] = build_story_description(description, ac_text) if ac_text else description
    elif ac_text:
        current_desc_result = request_json(
            "GET",
            entity_url("stories", story_id, workspace_id, shared_space_id),
            params={"fields": "id,description"},
            exit_on_error=False,
        )
        current_story = _extract_entity(current_desc_result) if current_desc_result.get("ok") else {}
        current_desc = strip_rendered_acceptance_criteria(str(current_story.get("description") or ""))
        fields["description"] = build_story_description(current_desc, ac_text)
    if ac_text:
        fields["acceptance_criteria"] = ac_text
    if not fields:
        fail("No fields provided to update (need --name, --description, and/or --acceptance-criteria)")

    url = entity_url("stories", story_id, workspace_id, shared_space_id)
    current = request_json(
        "GET",
        url,
        params={"fields": "id,client_lock_stamp"},
        exit_on_error=False,
    )
    current_entity = _extract_entity(current) if current.get("ok") else {}
    if "client_lock_stamp" in current_entity:
        fields["client_lock_stamp"] = current_entity["client_lock_stamp"]

    result = update_backlog_fields(url, fields)
    if not result.get("ok"):
        _fail_backlog_update(result)

    verify = request_json(
        "GET",
        url,
        params={"fields": "id,name,description,acceptance_criteria,phase,owner,author,parent,client_lock_stamp"},
        exit_on_error=False,
    )
    if verify.get("ok"):
        result["verified"] = _extract_entity(verify)
    print(json.dumps(result, ensure_ascii=False))


# ---- update-story-status ------------------------------------------
def update_story_status(
    story_id: str,
    phase: str,
    workspace_id: Optional[str] = None,
    shared_space_id: Optional[str] = None,
) -> None:
    normalized_phase = normalize_phase_id("story", phase)
    url = entity_url("stories", story_id, workspace_id, shared_space_id)
    payload: Dict[str, Any] = {"phase": {"type": "phase", "id": normalized_phase}}

    current = request_json(
        "GET",
        url,
        params={"fields": "id,phase,client_lock_stamp"},
        exit_on_error=False,
    )
    current_entity = _extract_entity(current) if current.get("ok") else {}
    if "client_lock_stamp" in current_entity:
        payload["client_lock_stamp"] = current_entity["client_lock_stamp"]

    result = update_backlog_fields(url, payload)
    if not result.get("ok"):
        _fail_backlog_update(result, **phase_update_error_hint("story", normalized_phase))
    print(json.dumps(result, ensure_ascii=False))


# ---- delete-backlog-item ------------------------------------------
def delete_backlog_item(
    entity_id: str,
    entity_type: str = "work_items",
    workspace_id: Optional[str] = None,
    shared_space_id: Optional[str] = None,
) -> None:
    """Enable Allow Delete, then delete a backlog/work item.

    This workspace requires the custom boolean field labelled "Allow Delete?"
    to be updated before a backlog item can be deleted. Metadata currently
    resolves that label to ``allow_delete_udf``; resolve it dynamically anyway
    so the command remains portable across workspaces.
    """
    collection = normalize_entity_collection(entity_type)
    field_name, field_meta, resolution = resolve_field_name(collection, "Allow delete", workspace_id, shared_space_id, for_update=True)
    allow_delete_field = field_name or "allow_delete_udf"
    url = entity_url(collection, entity_id, workspace_id, shared_space_id)

    read_fields = ["id", "name", "phase", "client_lock_stamp", allow_delete_field]
    current = request_json(
        "GET",
        url,
        params={"fields": ",".join(dict.fromkeys(read_fields))},
        exit_on_error=False,
    )
    if not current.get("ok"):
        fail("Octane API error", status=current.get("status"), response=current.get("response"), url=url)
    current_entity = _extract_entity(current) or {}

    # Mandatory pre-delete update: always PUT the Allow Delete field, even if
    # it already appears true, because Octane enforces that a fresh update
    # occurs before deletion.
    payload: Dict[str, Any] = {allow_delete_field: True}
    if "client_lock_stamp" in current_entity:
        payload["client_lock_stamp"] = current_entity["client_lock_stamp"]

    update = update_backlog_fields(url, payload)
    if not update.get("ok"):
        _fail_backlog_update(
            update,
            allow_delete_field=allow_delete_field,
            field_resolution=resolution,
        )

    verified = request_json(
        "GET",
        url,
        params={"fields": ",".join(dict.fromkeys(read_fields))},
        exit_on_error=False,
    )
    verified_entity = _extract_entity(verified) if verified.get("ok") else {}
    verified_value = verified_entity.get(allow_delete_field) if verified.get("ok") else None
    if verified.get("ok") and verified_value not in (True, "true", "True", 1):
        fail(
            "Allow Delete field did not verify as true; refusing to delete",
            allow_delete_field=allow_delete_field,
            verified=verified_entity,
            field_resolution=resolution,
        )

    deleted = request_json("DELETE", url, exit_on_error=False)
    if not deleted.get("ok"):
        fail("Octane API error", status=deleted.get("status"), response=deleted.get("response"), url=url)

    print(json.dumps({
        "ok": True,
        "data": {
            "entity_type": collection,
            "entity_id": entity_id,
            "allow_delete_field": allow_delete_field,
            "allow_delete_field_metadata": field_meta,
            "field_resolution": resolution,
            "before": current_entity,
            "allow_delete_update": update,
            "verified_before_delete": verified_entity if verified.get("ok") else None,
            "delete": deleted,
        },
    }, ensure_ascii=False))


# ---- create-comment -----------------------------------------------
def create_comment(
    text: str,
    entity_id: str,
    entity_type: str,
    workspace_id: Optional[str] = None,
    shared_space_id: Optional[str] = None,
) -> None:
    url = entity_url("comments", None, workspace_id, shared_space_id)
    payload = {
        "data": [
            {
                "text": format_octane_comment_text(text),
                "owner_work_item": {"type": entity_type, "id": entity_id},
            }
        ]
    }
    print(json.dumps(request_json("POST", url, payload=payload), ensure_ascii=False))


# ---- read-comment -------------------------------------------------
def get_comments(
    backlog_id: str,
    limit: int = 100,
    workspace_id: Optional[str] = None,
    shared_space_id: Optional[str] = None,
) -> None:
    """Read comments attached to a backlog/work item by ID."""
    url = entity_url("comments", None, workspace_id, shared_space_id)
    params = {
        "query": f'"owner_work_item={{id={backlog_id}}}"',
        "fields": "id,text,creation_time,author,owner_work_item",
        "limit": limit,
    }
    print(json.dumps(request_json("GET", url, params=params), ensure_ascii=False))


# ---- attachments --------------------------------------------------
def add_attachment(
    entity_id: str,
    file_path: str,
    description: Optional[str] = None,
    name: Optional[str] = None,
    owner_field: str = "owner_work_item",
    owner_type: str = "work_item",
    workspace_id: Optional[str] = None,
    shared_space_id: Optional[str] = None,
) -> None:
    """Upload a file attachment to an Octane entity, defaulting to backlog/work items."""
    path = Path(file_path).expanduser()
    if not path.is_file():
        fail("Attachment file not found", file_path=file_path)

    attachment_name = name or path.name
    content_type = mimetypes.guess_type(attachment_name)[0] or "application/octet-stream"
    entity: Dict[str, Any] = {
        owner_field: {"type": owner_type, "id": entity_id},
        "name": attachment_name,
    }
    if description is not None:
        entity["description"] = description

    url = entity_url("attachments", None, workspace_id, shared_space_id)
    with path.open("rb") as fh:
        files = {
            "entity": (None, json.dumps(entity), "application/json; charset=UTF-8"),
            "content": (attachment_name, fh, content_type),
        }
        result = request_multipart(url, files=files, exit_on_error=False)

    if not result.get("ok"):
        fail("Octane API error", status=result.get("status"), response=result.get("response"), url=url)

    attachments = _extract_entities(result)
    result["attachment"] = attachments[0] if attachments else _extract_entity(result)
    result["owner"] = {"field": owner_field, "type": owner_type, "id": entity_id}
    result["file"] = {"path": str(path), "name": attachment_name, "content_type": content_type}
    print(json.dumps(result, ensure_ascii=False))


def list_attachments(
    entity_id: str,
    owner_field: str = "owner_work_item",
    limit: int = 100,
    workspace_id: Optional[str] = None,
    shared_space_id: Optional[str] = None,
) -> None:
    """List attachments owned by an entity, defaulting to backlog/work items."""
    url = entity_url("attachments", None, workspace_id, shared_space_id)
    params = {
        "query": f'"{owner_field}={{id={entity_id}}}"',
        "fields": f"id,name,description,creation_time,author,{owner_field}",
        "limit": limit,
    }
    print(json.dumps(request_json("GET", url, params=params), ensure_ascii=False))


def delete_attachment(
    attachment_id: Optional[str] = None,
    entity_id: Optional[str] = None,
    attachment_name: Optional[str] = None,
    owner_field: str = "owner_work_item",
    workspace_id: Optional[str] = None,
    shared_space_id: Optional[str] = None,
) -> None:
    """Delete an attachment, optionally verifying it belongs to a backlog/work item."""
    if not attachment_id and not (entity_id and attachment_name):
        fail("Need --attachment-id, or --entity-id with --attachment-name")

    attachment: Dict[str, Any] = {}
    if attachment_id:
        url = entity_url("attachments", attachment_id, workspace_id, shared_space_id)
        fields = f"id,name,description,creation_time,author,{owner_field}"
        current = request_json("GET", url, params={"fields": fields}, exit_on_error=False)
        if not current.get("ok"):
            fail("Octane API error", status=current.get("status"), response=current.get("response"), url=url)
        attachment = _extract_entity(current) or {}
        if entity_id:
            owner = attachment.get(owner_field) or {}
            if str(owner.get("id")) != str(entity_id):
                fail(
                    "Attachment does not belong to the requested backlog/work item",
                    attachment_id=attachment_id,
                    entity_id=entity_id,
                    owner_field=owner_field,
                    attachment=attachment,
                )
    else:
        url = entity_url("attachments", None, workspace_id, shared_space_id)
        params = {
            "query": f'"{owner_field}={{id={entity_id}}}"',
            "fields": f"id,name,description,creation_time,author,{owner_field}",
            "limit": 200,
        }
        listed = request_json("GET", url, params=params, exit_on_error=False)
        if not listed.get("ok"):
            fail("Octane API error", status=listed.get("status"), response=listed.get("response"), url=url)
        attachments = _extract_entities(listed)
        matches = [item for item in attachments if str(item.get("name")) == str(attachment_name)]
        if not matches:
            fail("No attachment found on backlog/work item with that name", entity_id=entity_id, attachment_name=attachment_name)
        if len(matches) > 1:
            fail("Multiple attachments matched; pass --attachment-id", matches=matches)
        attachment = matches[0]
        attachment_id = str(attachment.get("id"))

    delete_url = entity_url("attachments", str(attachment_id), workspace_id, shared_space_id)
    deleted = request_json("DELETE", delete_url, exit_on_error=False)
    if not deleted.get("ok"):
        fail("Octane API error", status=deleted.get("status"), response=deleted.get("response"), url=delete_url)

    verify = request_json("GET", delete_url, params={"fields": "id,name"}, exit_on_error=False)
    print(json.dumps({
        "ok": True,
        "data": {
            "attachment_id": attachment_id,
            "entity_id": entity_id,
            "owner_field": owner_field,
            "deleted_attachment": attachment,
            "delete": deleted,
            "verified_deleted": not verify.get("ok") and verify.get("status") in (404, 410),
            "verify": verify,
        },
    }, ensure_ascii=False))


def download_attachment(
    attachment_id: str,
    output_file: str,
    workspace_id: Optional[str] = None,
    shared_space_id: Optional[str] = None,
) -> None:
    """Download attachment binary content to a local file."""
    url = entity_url("attachments", attachment_id, workspace_id, shared_space_id) + "/content"
    out = Path(output_file).expanduser()
    out.parent.mkdir(parents=True, exist_ok=True)
    s = get_session()
    try:
        resp = s.get(url, timeout=_require_runtime().timeout, stream=True)
    except requests.RequestException as e:
        fail("Attachment download failed", details=str(e), url=url)
    if not resp.ok:
        fail("Octane API error", status=resp.status_code, response=resp.text, url=url)
    with out.open("wb") as fh:
        for chunk in resp.iter_content(chunk_size=1024 * 256):
            if chunk:
                fh.write(chunk)
    print(json.dumps({"ok": True, "status": resp.status_code, "attachment_id": attachment_id, "output_file": str(out), "url": url}, ensure_ascii=False))


# ---- get-manual-test ----------------------------------------------
def get_manual_test(
    test_id: str,
    workspace_id: Optional[str] = None,
    shared_space_id: Optional[str] = None,
) -> None:
    url = entity_url("tests", test_id, workspace_id, shared_space_id)
    params = {"fields": "id,name,script,phase,owner,subtype"}
    print(json.dumps(request_json("GET", url, params=params), ensure_ascii=False))


# ---- get-suite-runs -----------------------------------------------
def get_suite_runs(
    suite_id: str,
    limit: int = 100,
    workspace_id: Optional[str] = None,
    shared_space_id: Optional[str] = None,
) -> None:
    url = entity_url("suite_runs", None, workspace_id, shared_space_id)
    params = {
        "query": f'"test_suite={{id={suite_id}}}"',
        "fields": "id,name,status,native_status,test_suite",
        "limit": limit,
    }
    print(json.dumps(request_json("GET", url, params=params), ensure_ascii=False))


# ---- get-run-history ----------------------------------------------
def get_run_history(
    suite_run_id: Optional[str] = None,
    limit: int = 100,
    workspace_id: Optional[str] = None,
    shared_space_id: Optional[str] = None,
) -> None:
    url = entity_url("runs", None, workspace_id, shared_space_id)
    params: Dict[str, Any] = {
        "fields": "id,name,status,native_status,test",
        "limit": limit,
    }
    if suite_run_id:
        params["query"] = f'"suite_run={{id={suite_run_id}}}"'
    print(json.dumps(request_json("GET", url, params=params), ensure_ascii=False))


# ---- list-work-items ---------------------------------------------
def list_work_items(
    user_email: Optional[str] = None,
    limit: int = 100,
    retry_once: bool = False,
    workspace_id: Optional[str] = None,
    shared_space_id: Optional[str] = None,
) -> None:
    """List visible work items, optionally filtered by owner email."""
    url = entity_url("work_items", None, workspace_id, shared_space_id)
    params: Dict[str, Any] = {
        "fields": "id,name,description,phase,author,owner,subtype,priority,severity,child_tasks,tasks_number",
        "limit": limit,
    }
    if user_email:
        params["query"] = f"\"owner={{email='{user_email}'}}\""

    result = request_json("GET", url, params=params)
    items = (
        result.get("data", {}).get("data", [])
        if isinstance(result.get("data"), dict)
        else []
    )
    if retry_once and not items:
        result = request_json("GET", url, params=params)
    print(json.dumps(result, ensure_ascii=False))


# ---- list-tasks ---------------------------------------------------
def list_tasks(
    work_item_id: str,
    limit: int = 100,
    workspace_id: Optional[str] = None,
    shared_space_id: Optional[str] = None,
) -> None:
    """List tasks associated with a work item."""
    url = entity_url("tasks", None, workspace_id, shared_space_id)
    params = {
        "query": f'"story={{id EQ ^{work_item_id}^}}"',
        "fields": "id,name,phase,owner,item_type,story,invested_hours,estimated_hours",
        "limit": limit,
    }
    print(json.dumps(request_json("GET", url, params=params), ensure_ascii=False))


# ---- add-task -----------------------------------------------------
def add_task(
    work_item_id: str,
    name: str,
    owner_id: str,
    item_type: str = "list_node.task_item_type.test",
    phase: str = "phase.task.new",
    estimated_hours: Optional[float] = None,
    workspace_id: Optional[str] = None,
    shared_space_id: Optional[str] = None,
) -> None:
    """Add a task to a work item."""
    url = entity_url("tasks", None, workspace_id, shared_space_id)
    task: Dict[str, Any] = {
        "name": name,
        "item_type": {"type": "list_node", "id": item_type},
        "phase": {"type": "phase", "id": phase},
        "story": {"type": "work_item", "id": work_item_id},
        "owner": {"type": "workspace_user", "id": owner_id},
    }
    if estimated_hours is not None:
        task["estimated_hours"] = estimated_hours
    payload = {"data": [task]}
    result = request_json("POST", url, payload=payload, exit_on_error=False)
    if not result.get("ok"):
        fail("Octane API error", status=result.get("status"), response=result.get("response"), url=url)

    verify = request_json(
        "GET",
        url,
        params={
            "query": f'"story={{id EQ ^{work_item_id}^}}"',
            "fields": "id,name,phase,owner,item_type,story,invested_hours,estimated_hours",
            "limit": 100,
        },
        exit_on_error=False,
    )
    if verify.get("ok"):
        result["verified_tasks"] = verify.get("data")
    print(json.dumps(result, ensure_ascii=False))


# ---- list-tags / add-tag -----------------------------------------
def list_tags(
    query: Optional[str] = None,
    exact: bool = False,
    limit: int = 200,
    workspace_id: Optional[str] = None,
    shared_space_id: Optional[str] = None,
) -> None:
    """List/search workspace user tags."""
    url = entity_url("user_tags", None, workspace_id, shared_space_id)
    params: Dict[str, Any] = {"fields": "id,name", "limit": limit, "order_by": "name"}
    if query:
        operator = "EQ" if exact else "BK"
        value = query if exact else f"*{query}*"
        params["query"] = f'"name {operator} ^{value}^"'
    print(json.dumps(request_json("GET", url, params=params), ensure_ascii=False))


def _find_user_tag_by_name(
    tag_name: str,
    workspace_id: str,
    shared_space_id: str,
) -> Optional[Dict[str, Any]]:
    url = entity_url("user_tags", None, workspace_id, shared_space_id)
    result = request_json(
        "GET",
        url,
        params={"fields": "id,name", "query": f'"name EQ ^{tag_name}^"', "limit": 200},
        exit_on_error=False,
    )
    for tag in _extract_entities(result) if result.get("ok") else []:
        if str(tag.get("name", "")).lower() == tag_name.lower():
            return tag
    return None


def _create_user_tag(
    tag_name: str,
    workspace_id: str,
    shared_space_id: str,
) -> Dict[str, Any]:
    url = entity_url("user_tags", None, workspace_id, shared_space_id)
    result = request_json("POST", url, payload={"data": [{"name": tag_name}]}, exit_on_error=False)
    if not result.get("ok"):
        fail("Octane API error", status=result.get("status"), response=result.get("response"), url=url)
    created = _extract_entity(result)
    return created if created else {"name": tag_name}


def add_tag(
    entity_id: str,
    tag_name: str,
    entity_type: str = "work_items",
    create_if_missing: bool = True,
    workspace_id: Optional[str] = None,
    shared_space_id: Optional[str] = None,
) -> None:
    """Add a user tag to a backlog/work item while preserving existing tags."""
    collection = normalize_entity_collection(entity_type)
    tag = _find_user_tag_by_name(tag_name, workspace_id, shared_space_id)
    created_tag = False
    if not tag:
        if not create_if_missing:
            fail("Tag not found", tag=tag_name, hint="Retry without --no-create to create the workspace tag first.")
        tag = _create_user_tag(tag_name, workspace_id, shared_space_id)
        created_tag = True
    tag_id = str(tag.get("id") or "")
    if not tag_id:
        # Some create responses omit the entity body; re-read by name before failing.
        reread = _find_user_tag_by_name(tag_name, workspace_id, shared_space_id)
        tag = reread or tag
        tag_id = str(tag.get("id") or "")
    if not tag_id:
        fail("Could not resolve user tag ID after create/search", tag=tag_name, tag_response=tag)

    url = entity_url(collection, entity_id, workspace_id, shared_space_id)
    current = request_json(
        "GET",
        url,
        params={"fields": "id,name,user_tags,client_lock_stamp"},
        exit_on_error=False,
    )
    if not current.get("ok"):
        fail("Octane API error", status=current.get("status"), response=current.get("response"), url=url)
    entity = _extract_entity(current)

    existing_tags = []
    raw_tags = entity.get("user_tags")
    if isinstance(raw_tags, dict) and isinstance(raw_tags.get("data"), list):
        existing_tags = [t for t in raw_tags["data"] if isinstance(t, dict)]
    elif isinstance(raw_tags, list):
        existing_tags = [t for t in raw_tags if isinstance(t, dict)]

    seen_ids = {str(t.get("id")) for t in existing_tags if t.get("id") is not None}
    already_present = tag_id in seen_ids
    merged_tags = existing_tags if already_present else existing_tags + [{"type": "user_tag", "id": tag_id}]

    payload: Dict[str, Any] = {
        "user_tags": {"data": merged_tags},
    }
    if "client_lock_stamp" in entity:
        payload["client_lock_stamp"] = entity["client_lock_stamp"]

    result = {"ok": True, "status": 200, "data": entity, "url": url} if already_present else update_backlog_fields(url, payload)
    if not result.get("ok"):
        _fail_backlog_update(result)

    verify = request_json(
        "GET",
        url,
        params={"fields": "id,name,user_tags,client_lock_stamp"},
        exit_on_error=False,
    )
    if verify.get("ok"):
        result["verified"] = _extract_entity(verify)
    result["tag"] = {"id": tag_id, "name": tag.get("name") or tag_name, "created": created_tag}
    result["already_present"] = already_present
    print(json.dumps(result, ensure_ascii=False))


# ---- list-phases --------------------------------------------------
def list_phases(
    entity: str = "defect",
    limit: int = 100,
    workspace_id: Optional[str] = None,
    shared_space_id: Optional[str] = None,
) -> None:
    """List phase IDs for an entity workflow (defect/story/test/etc.)."""
    entity = entity.strip().lower().rstrip("s")
    url = entity_url("phases", None, workspace_id, shared_space_id)
    params = {
        "query": f'"logical_name EQ ^phase.{entity}*^"',
        "fields": "id,name,logical_name,metaphase",
        "limit": limit,
    }
    print(json.dumps(request_json("GET", url, params=params), ensure_ascii=False))



# ===================================================================
# CLI argument parser
# ===================================================================
def main() -> None:
    parser = argparse.ArgumentParser(
        description="ALM Octane CLI — generic entity operations and workflow commands"
    )
    parser.add_argument("--profile", help="Named durable credential profile")
    sub = parser.add_subparsers(dest="command", required=True)

    # -- shared args helper --
    def add_common(p: argparse.ArgumentParser) -> None:
        p.add_argument("--workspace-id", default=None)
        p.add_argument("--shared-space-id", default=None)

    # -- get-work-item ----------------------------------------------
    p_wi = sub.add_parser("get-work-item", help="Fetch a single work item by ID")
    p_wi.add_argument("--entity-id", dest="entity_id", required=True, help="ID of the work item")
    p_wi.add_argument(
        "--fields",
        default="id,name,description,subtype,phase,owner,author,priority,severity",
        help="Comma-separated fields",
    )
    add_common(p_wi)

    # -- get-defect / get-feature / get-story -----------------------
    entity_commands = {
        "get-defect": ("defects", "id,name,description,severity,phase,owner,author,priority,parent,security_source_udf,comments"),
        "get-feature": ("features", "id,name,description,phase,owner,parent"),
        "get-story": ("stories", "id,name,description,acceptance_criteria,phase,owner,author,parent"),
    }
    for cmd_name, (etype, default_fields) in entity_commands.items():
        label = etype.rstrip('s') if etype != 'stories' else 'story'
        p = sub.add_parser(cmd_name, help=f"Fetch a single {label} by ID")
        p.add_argument("--entity-id", dest="entity_id", required=True, help=f"ID of the {etype[:-1]}")
        p.add_argument("--fields", default=default_fields, help="Comma-separated fields")
        add_common(p)
        p.set_defaults(_entity_type=etype)

    # -- search-all -------------------------------------------------
    p_search = sub.add_parser("search-all", help="Full-text search across work items")
    p_search.add_argument("--query", required=True, help="Search text or Octane query")
    p_search.add_argument("--limit", type=int, default=50)
    add_common(p_search)

    # -- create-feature ---------------------------------------------
    p_cf = sub.add_parser("create-feature", help="Create a new feature")
    p_cf.add_argument("--name", required=True, help="Feature name/summary")
    p_cf.add_argument("--description", required=True, help="Feature description")
    p_cf.add_argument("--parent-id", default=None, help="Parent work item ID (optional)")
    p_cf.add_argument("--owner-id", default=None, help="Workspace user ID for feature owner (optional)")
    add_common(p_cf)

    # -- update-feature ---------------------------------------------
    p_uf = sub.add_parser("update-feature", help="Update feature name, description, and/or owner")
    p_uf.add_argument("--entity-id", dest="feature_id", required=True, help="Feature ID")
    p_uf.add_argument("--name", default=None, help="New feature name/summary")
    p_uf.add_argument("--description", default=None, help="New feature description")
    p_uf.add_argument("--owner-id", default=None, help="Workspace user ID for feature owner (optional)")
    add_common(p_uf)

    # -- create-defect ----------------------------------------------
    p_cd = sub.add_parser("create-defect", help="Create a new defect")
    p_cd.add_argument("--name", required=True, help="Defect name/summary")
    p_cd.add_argument("--description", required=True, help="Detailed description")
    p_cd.add_argument("--severity", required=True, help="Severity name or list_node ID (e.g. High or list_node.severity.high)")
    p_cd.add_argument("--priority", default=None, help="Priority list_node ID (optional)")
    p_cd.add_argument("--parent-feature-id", default=None, help="Parent feature/work item ID for the defect (optional)")
    p_cd.add_argument("--security-source", default=None, help="Security Source list_node ID or exact name, e.g. 'Threat Model'")
    p_cd.add_argument("--cvss-score", default=None, help="CVSS base score to set on the defect, resolving the CVSS Score field")
    p_cd.add_argument("--cvss-vector", default=None, help="CVSS vector to set on the defect, resolving the CVSS Vector field")
    p_cd.add_argument("--owner-id", default=None, help="Workspace user ID for defect owner")
    p_cd.add_argument("--target-release-id", dest="target_release_id", default=None, help="Release ID to set as the defect target release")
    add_common(p_cd)

    # -- update-defect ----------------------------------------------
    p_ud = sub.add_parser("update-defect", help="Update a defect phase and/or severity")
    p_ud.add_argument("--entity-id", dest="defect_id", required=True, help="Defect ID")
    p_ud.add_argument("--phase", default=None, help="Phase ID or shorthand (e.g. phase.defect.fixed or fixed)")
    p_ud.add_argument("--severity", default=None, help="Severity name or list_node ID")
    add_common(p_ud)

    # -- create-story -----------------------------------------------
    p_cs = sub.add_parser("create-story", help="Create a new user story")
    p_cs.add_argument("--name", required=True, help="Story name/summary")
    p_cs.add_argument("--description", required=True, help="Detailed description")
    add_common(p_cs)

    # -- update-story -----------------------------------------------
    p_ustory = sub.add_parser("update-story", help="Update story name, description, and/or acceptance criteria")
    p_ustory.add_argument("--entity-id", dest="story_id", required=True, help="Story ID")
    p_ustory.add_argument("--name", default=None, help="New story name/summary")
    p_ustory.add_argument("--description", default=None, help="New story description/problem statement")
    p_ustory.add_argument(
        "--acceptance-criteria",
        action="append",
        default=None,
        help="Acceptance criterion. Repeat for multiple criteria, or pass one multiline value.",
    )
    add_common(p_ustory)

    # -- create-story-under-feature ---------------------------------
    p_csf = sub.add_parser("create-story-under-feature", help="Create a story under a feature with acceptance criteria")
    p_csf.add_argument("--entity-id", dest="feature_id", required=True, help="Parent feature ID")
    p_csf.add_argument("--name", required=True, help="Story name/summary")
    p_csf.add_argument("--description", required=True, help="Story description/problem statement")
    p_csf.add_argument(
        "--acceptance-criteria",
        action="append",
        default=None,
        help="Acceptance criterion. Repeat for multiple criteria, or pass one multiline value.",
    )
    p_csf.add_argument("--priority", default=None, help="Priority list_node ID (optional)")
    p_csf.add_argument("--owner-id", default=None, help="Workspace user ID for story owner (optional)")
    add_common(p_csf)

    # -- get-story-parent-feature -----------------------------------
    p_gspf = sub.add_parser("get-story-parent-feature", help="Identify the parent feature of a story")
    p_gspf.add_argument("--entity-id", dest="story_id", required=True, help="Story ID")
    add_common(p_gspf)

    # -- list-feature-items -----------------------------------------
    p_lfi = sub.add_parser("list-feature-items", help="List stories and issues/defects under a feature")
    p_lfi.add_argument("--entity-id", dest="feature_id", required=True, help="Feature ID")
    p_lfi.add_argument("--limit", type=int, default=100)
    add_common(p_lfi)

    # -- update-feature-security ------------------------------------
    p_ufs = sub.add_parser("update-feature-security", help="Read a feature and update threat-modelling security fields")
    p_ufs.add_argument("--entity-id", dest="feature_id", required=True, help="Feature ID")
    p_ufs.add_argument("--security-assessment", default=None, help="Value for the Security Assessment field (security_assessment_udf)")
    p_ufs.add_argument("--security-impact-level", default=None, help="Value or list_node ID for the Security Impact field (security_impact_f_udf)")
    add_common(p_ufs)

    # -- update-story-status ----------------------------------------
    p_us = sub.add_parser("update-story-status", help="Update user story phase")
    p_us.add_argument("--entity-id", dest="story_id", required=True, help="Story ID")
    p_us.add_argument("--phase", required=True, help="Phase ID or shorthand (e.g. phase.story.inprogress or inprogress)")
    add_common(p_us)

    # -- delete-backlog-item ----------------------------------------
    p_del = sub.add_parser("delete-backlog-item", help="Enable Allow Delete, then delete a backlog/work item")
    p_del.add_argument("--entity-id", required=True, help="Backlog/work item ID")
    p_del.add_argument("--entity-type", default="work_items", help="Entity type/collection, e.g. work_item, story, defect, feature")
    add_common(p_del)

    # -- create-comment ---------------------------------------------
    p_cc = sub.add_parser("create-comment", help="Add a comment to an entity")
    p_cc.add_argument("--entity-id", dest="entity_id", required=True, help="Entity ID")
    p_cc.add_argument("--entity-type", required=True, help="Entity type: defect, story, etc.")
    p_cc.add_argument("--text", required=True, help="Comment body text")
    add_common(p_cc)

    # -- read-comment -----------------------------------------------
    p_rc = sub.add_parser("read-comment", help="Read comments from a backlog/work item")
    p_rc.add_argument("--entity-id", dest="backlog_id", required=True, help="Backlog/work item ID")
    p_rc.add_argument("--limit", type=int, default=100)
    add_common(p_rc)

    # -- add-attachment ---------------------------------------------
    p_aa = sub.add_parser("add-attachment", help="Upload a file attachment to a backlog/work item")
    p_aa.add_argument("--entity-id", required=True, help="Backlog/work item ID")
    p_aa.add_argument("--file", dest="file_path", required=True, help="Path to the file to upload")
    p_aa.add_argument("--name", default=None, help="Attachment name in Octane; defaults to the file basename")
    p_aa.add_argument("--description", default=None, help="Attachment description")
    p_aa.add_argument("--owner-field", default="owner_work_item", help="Attachment owner field, e.g. owner_work_item or owner_test")
    p_aa.add_argument("--owner-type", default="work_item", help="Owner entity type, e.g. work_item or test")
    add_common(p_aa)

    # -- list-attachments -------------------------------------------
    p_la = sub.add_parser("list-attachments", help="List attachments for a backlog/work item")
    p_la.add_argument("--entity-id", required=True, help="Backlog/work item ID")
    p_la.add_argument("--owner-field", default="owner_work_item", help="Attachment owner field, e.g. owner_work_item or owner_test")
    p_la.add_argument("--limit", type=int, default=100)
    add_common(p_la)

    # -- delete-attachment -----------------------------------------
    p_dela = sub.add_parser("delete-attachment", help="Delete an attachment, optionally verifying backlog/work item ownership")
    p_dela.add_argument("--attachment-id", default=None, help="Attachment ID")
    p_dela.add_argument("--entity-id", default=None, help="Backlog/work item ID used to find or verify the attachment")
    p_dela.add_argument("--attachment-name", default=None, help="Exact attachment name to delete from the backlog/work item")
    p_dela.add_argument("--owner-field", default="owner_work_item", help="Attachment owner field, e.g. owner_work_item or owner_test")
    add_common(p_dela)

    # -- download-attachment ---------------------------------------
    p_da = sub.add_parser("download-attachment", help="Download attachment content to a local file")
    p_da.add_argument("--attachment-id", required=True, help="Attachment ID")
    p_da.add_argument("--output-file", required=True, help="Local output path")
    add_common(p_da)

    # -- get-manual-test --------------------------------------------
    p_mt = sub.add_parser("get-manual-test", help="Fetch a manual test by ID")
    p_mt.add_argument("--entity-id", dest="test_id", required=True, help="Manual test ID")
    add_common(p_mt)

    # -- get-suite-runs ---------------------------------------------
    p_sr = sub.add_parser("get-suite-runs", help="List runs for a test suite")
    p_sr.add_argument("--entity-id", dest="suite_id", required=True, help="Test suite ID")
    p_sr.add_argument("--limit", type=int, default=100)
    add_common(p_sr)

    # -- get-run-history --------------------------------------------
    p_rh = sub.add_parser("get-run-history", help="List run results for a suite run")
    p_rh.add_argument("--entity-id", dest="suite_run_id", default=None, help="Suite run ID (optional)")
    p_rh.add_argument("--limit", type=int, default=100)
    add_common(p_rh)

    # -- list-work-items --------------------------------------------
    p_lwi = sub.add_parser("list-work-items", help="List visible work items, optionally filtered by owner email")
    p_lwi.add_argument("--user-email", default=None, help="Filter by owner email")
    p_lwi.add_argument("--limit", type=int, default=100)
    p_lwi.add_argument("--retry-on-empty", action="store_true")
    add_common(p_lwi)

    # -- list-tasks --------------------------------------------------
    p_lt = sub.add_parser("list-tasks", help="List tasks for a work item")
    p_lt.add_argument("--entity-id", dest="work_item_id", required=True, help="Work item ID")
    p_lt.add_argument("--limit", type=int, default=100)
    add_common(p_lt)

    # -- add-task ----------------------------------------------------
    p_at = sub.add_parser("add-task", help="Add a task to a work item")
    p_at.add_argument("--entity-id", dest="work_item_id", required=True, help="Work item ID")
    p_at.add_argument("--name", required=True, help="Task name")
    p_at.add_argument("--owner-id", required=True, help="Workspace user ID for task owner")
    p_at.add_argument("--item-type", default="list_node.task_item_type.test", help="Task type list_node ID")
    p_at.add_argument("--phase", default="phase.task.new", help="Task phase ID")
    p_at.add_argument("--estimated-hours", type=float, default=None)
    add_common(p_at)

    # -- list-tags --------------------------------------------------
    p_ltags = sub.add_parser("list-tags", help="List/search workspace user tags")
    p_ltags.add_argument("--query", default=None, help="Tag name search")
    p_ltags.add_argument("--exact", action="store_true", help="Exact tag name match")
    p_ltags.add_argument("--limit", type=int, default=200)
    add_common(p_ltags)

    # -- add-tag ----------------------------------------------------
    p_addtag = sub.add_parser("add-tag", help="Add a user tag to a backlog/work item")
    p_addtag.add_argument("--entity-id", required=True, help="Backlog/work item ID")
    p_addtag.add_argument("--tag", required=True, help="Tag name to add")
    p_addtag.add_argument("--entity-type", default="work_items", help="Entity type/collection, e.g. work_item, defect, story")
    p_addtag.add_argument("--no-create", action="store_true", help="Fail if the tag does not already exist")
    add_common(p_addtag)

    # -- list-phases ------------------------------------------------
    p_lp = sub.add_parser("list-phases", help="List valid phase IDs for an entity workflow")
    p_lp.add_argument("--entity", default="defect", help="Entity name, e.g. defect, story, test")
    p_lp.add_argument("--limit", type=int, default=100)
    add_common(p_lp)

    octane_generic.register_commands(sub, add_common)

    # -- Parse and dispatch -----------------------------------------
    args = parser.parse_args()
    if args.command in octane_generic.COMMANDS:
        raise SystemExit(octane_generic.run_cli(args, sys.modules[__name__]))
    runtime = resolve_runtime_config(args.profile)
    configure_runtime(runtime)
    if hasattr(args, "workspace_id"):
        args.workspace_id = args.workspace_id or runtime.workspace_id
        args.shared_space_id = args.shared_space_id or runtime.shared_space_id
    cmd = args.command

    if cmd == "get-work-item":
        get_work_item(
            args.entity_id,
            fields=args.fields,
            workspace_id=args.workspace_id,
            shared_space_id=args.shared_space_id,
        )
    elif cmd in entity_commands:
        get_entity(
            args._entity_type,
            args.entity_id,
            fields=args.fields,
            workspace_id=args.workspace_id,
            shared_space_id=args.shared_space_id,
        )
    elif cmd == "search-all":
        search_all(args.query, args.limit, args.workspace_id, args.shared_space_id)
    elif cmd == "create-feature":
        create_feature(
            args.name, args.description, args.parent_id, args.owner_id,
            args.workspace_id, args.shared_space_id,
        )
    elif cmd == "update-feature":
        update_feature(
            args.feature_id, args.name, args.description, args.owner_id,
            args.workspace_id, args.shared_space_id,
        )
    elif cmd == "create-defect":
        create_defect(
            args.name, args.description, args.severity, args.priority, args.parent_feature_id,
            args.security_source, args.cvss_score, args.cvss_vector,
            args.owner_id, args.target_release_id,
            args.workspace_id, args.shared_space_id,
        )
    elif cmd == "update-defect":
        update_defect(
            args.defect_id, args.phase, args.severity,
            args.workspace_id, args.shared_space_id,
        )
    elif cmd == "create-story":
        create_story(
            args.name, args.description,
            args.workspace_id, args.shared_space_id,
        )
    elif cmd == "update-story":
        update_story(
            args.story_id, args.name, args.description, args.acceptance_criteria,
            args.workspace_id, args.shared_space_id,
        )
    elif cmd == "create-story-under-feature":
        create_story_under_feature(
            args.feature_id, args.name, args.description, args.acceptance_criteria,
            args.priority, args.owner_id, args.workspace_id, args.shared_space_id,
        )
    elif cmd == "get-story-parent-feature":
        get_story_parent_feature(args.story_id, args.workspace_id, args.shared_space_id)
    elif cmd == "list-feature-items":
        list_feature_items(args.feature_id, args.limit, args.workspace_id, args.shared_space_id)
    elif cmd == "update-feature-security":
        update_feature_security(
            args.feature_id, args.security_assessment, args.security_impact_level,
            args.workspace_id, args.shared_space_id,
        )
    elif cmd == "update-story-status":
        update_story_status(
            args.story_id, args.phase,
            args.workspace_id, args.shared_space_id,
        )
    elif cmd == "delete-backlog-item":
        delete_backlog_item(
            args.entity_id, args.entity_type,
            args.workspace_id, args.shared_space_id,
        )
    elif cmd == "create-comment":
        create_comment(
            args.text, args.entity_id, args.entity_type,
            args.workspace_id, args.shared_space_id,
        )
    elif cmd == "read-comment":
        get_comments(
            args.backlog_id, args.limit,
            args.workspace_id, args.shared_space_id,
        )
    elif cmd == "add-attachment":
        add_attachment(
            args.entity_id, args.file_path, args.description, args.name,
            args.owner_field, args.owner_type, args.workspace_id, args.shared_space_id,
        )
    elif cmd == "list-attachments":
        list_attachments(
            args.entity_id, args.owner_field, args.limit,
            args.workspace_id, args.shared_space_id,
        )
    elif cmd == "delete-attachment":
        delete_attachment(
            args.attachment_id, args.entity_id, args.attachment_name, args.owner_field,
            args.workspace_id, args.shared_space_id,
        )
    elif cmd == "download-attachment":
        download_attachment(
            args.attachment_id, args.output_file,
            args.workspace_id, args.shared_space_id,
        )
    elif cmd == "get-manual-test":
        get_manual_test(args.test_id, args.workspace_id, args.shared_space_id)
    elif cmd == "get-suite-runs":
        get_suite_runs(
            args.suite_id, args.limit, args.workspace_id, args.shared_space_id,
        )
    elif cmd == "get-run-history":
        get_run_history(
            args.suite_run_id, args.limit, args.workspace_id, args.shared_space_id,
        )
    elif cmd == "list-work-items":
        list_work_items(
            args.user_email, args.limit, args.retry_on_empty,
            args.workspace_id, args.shared_space_id,
        )
    elif cmd == "list-tasks":
        list_tasks(args.work_item_id, args.limit, args.workspace_id, args.shared_space_id)
    elif cmd == "add-task":
        add_task(
            args.work_item_id, args.name, args.owner_id, args.item_type, args.phase,
            args.estimated_hours, args.workspace_id, args.shared_space_id,
        )
    elif cmd == "list-tags":
        list_tags(args.query, args.exact, args.limit, args.workspace_id, args.shared_space_id)
    elif cmd == "add-tag":
        add_tag(
            args.entity_id, args.tag, args.entity_type, not args.no_create,
            args.workspace_id, args.shared_space_id,
        )
    elif cmd == "list-phases":
        list_phases(args.entity, args.limit, args.workspace_id, args.shared_space_id)
    else:
        fail(f"Unknown command: {cmd}")


if __name__ == "__main__":
    main()
