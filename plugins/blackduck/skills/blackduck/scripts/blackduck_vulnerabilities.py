# /// script
# requires-python = ">=3.10"
# dependencies = [
#   "requests>=2.28,<3",
#   "python-dotenv>=1.0,<2",
#   "keyring>=25,<26",
# ]
# ///
"""Minimal Black Duck agent skill CLI.

Structured JSON is printed to stdout; diagnostics/errors go to stderr/stdout JSON.
"""
from __future__ import annotations

import argparse
import base64
import json
import logging
import os
import re
import sys
import time
from pathlib import Path
from urllib.parse import urlparse
from typing import Any, Dict, Iterable, Iterator, List, NamedTuple, Optional, Set

import requests

try:
    import keyring
    from keyring.errors import KeyringError
except ImportError:  # Environment variables still work without keyring installed.
    keyring = None  # type: ignore[assignment]

    class KeyringError(Exception):
        pass

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
SKILL_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, ".."))
if SCRIPT_DIR not in sys.path:
    sys.path.insert(0, SCRIPT_DIR)
from credential_config import ConfigError, active_profile, config_path, migrate_legacy, named_profile, normalize_verify_ssl, validate_endpoint


class RuntimeConfig(NamedTuple):
    base_url: str
    token_value: str
    token_keyring_user: str
    verify_ssl: bool

logging.basicConfig(level=logging.WARNING, format="%(levelname)s: %(message)s", stream=sys.stderr)
log = logging.getLogger("blackduck")
logging.getLogger("urllib3").setLevel(logging.ERROR)

# Values cross-checked against Black Duck remediation docs and Reporting DB docs.
DOCUMENTED_STATUSES = [
    "NEW", "NEEDS_REVIEW", "AFFECTED", "NOT_AFFECTED", "UNDER_INVESTIGATION",
    "REMEDIATION_REQUIRED", "REMEDIATION_COMPLETE", "MITIGATED", "PATCHED",
    "IGNORED", "DUPLICATE",
]
# Backward-compatible alias seen in some integrations; normalized to NOT_AFFECTED.
VALID_STATUSES = DOCUMENTED_STATUSES + ["NOT_VULNERABLE"]
VALID_STATUS_JUSTIFICATIONS = [
    "COMPONENT_NOT_PRESENT",
    "VULNERABLE_CODE_NOT_PRESENT",
    "VULNERABLE_CODE_CANNOT_BE_CONTROLLED_BY_ADVERSARY",
    "VULNERABLE_CODE_NOT_IN_EXECUTE_PATH",
    "INLINE_MITIGATIONS_ALREADY_EXIST",
]
VALID_REMEDIATIONS = ["MITIGATION", "NO_FIX_PLANNED", "NONE_AVAILABLE", "VENDOR_FIX", "WORKAROUND"]
# Backward-compatible aliases from earlier versions of this skill.
REQUEST_TIMEOUT_SECONDS = 60

VALID_REMEDIATION_ALIASES = {"WILL_NOT_FIX": "NO_FIX_PLANNED", "NONE": "NONE_AVAILABLE"}
VALID_JUSTIFICATIONS = VALID_STATUS_JUSTIFICATIONS
SEVERITY_ORDER = {"CRITICAL": 0, "HIGH": 1, "MEDIUM": 2, "LOW": 3, "OK": 4, "UNKNOWN": 5}

Json = Dict[str, Any]


def emit(data: Any) -> None:
    print(json.dumps(data, indent=2, default=str))


def die(data: Json, code: int = 1) -> None:
    emit(data)
    raise SystemExit(code)


def _dotenv_values() -> Json:
    env_path = Path(SKILL_ROOT) / ".env"
    if not env_path.is_file():
        return {}
    try:
        from dotenv import dotenv_values
        return {name: value for name, value in dotenv_values(env_path).items() if value is not None}
    except ImportError:
        values: Json = {}
        for raw_line in env_path.read_text(encoding="utf-8").splitlines():
            line = raw_line.strip()
            if line and not line.startswith("#") and "=" in line:
                name, value = line.split("=", 1)
                values[name.strip()] = value.strip().strip('"').strip("'")
        return values


def resolve_runtime_config(profile_name: Optional[str] = None) -> RuntimeConfig:
    """Resolve one coherent Black Duck configuration source explicitly."""
    process_env = dict(os.environ)
    dotenv_env = _dotenv_values()
    credential_names = {"BLACKDUCK_URL", "BLACKDUCK_TOKEN", "BLACKDUCK_TOKEN_KEYRING_USER"}
    process_credentials = {name for name in credential_names if process_env.get(name)}
    process_direct = {"BLACKDUCK_URL", "BLACKDUCK_TOKEN"}.issubset(process_credentials)
    process_keyring = {"BLACKDUCK_URL", "BLACKDUCK_TOKEN_KEYRING_USER"}.issubset(process_credentials)
    if process_direct and process_keyring:
        die({"error_code": "BLACKDUCK_CREDENTIAL_SOURCE_MISMATCH", "error": "Direct and keyring Black Duck credentials are mutually exclusive"})

    active = None
    if not (process_direct or process_keyring):
        try:
            if keyring:
                migrate_legacy(Path(SKILL_ROOT), keyring.get_password)
            selected_name = profile_name or process_env.get("BLACKDUCK_PROFILE")
            active = named_profile(selected_name) if selected_name else active_profile()
        except ConfigError as exc:
            print(f"Error: {exc}", file=sys.stderr)
            die({"error": "Invalid durable Black Duck profile", "details": str(exc)})
    profile = active[1] if active else {}

    if process_direct or process_keyring:
        base_url = process_env["BLACKDUCK_URL"]
        token_value = process_env.get("BLACKDUCK_TOKEN", "") if process_direct else ""
        token_keyring_user = "" if process_direct else process_env["BLACKDUCK_TOKEN_KEYRING_USER"]
        verify_value = process_env.get("BLACKDUCK_VERIFY_SSL", "true")
    elif profile:
        if process_credentials:
            die({"error_code": "BLACKDUCK_CREDENTIAL_SOURCE_MISMATCH", "error": "Incoherent partial Black Duck credential override"})
        base_url = profile["endpoint"]
        token_value = ""
        token_keyring_user = profile["keyring_user"]
        verify_value = process_env.get(
            "BLACKDUCK_VERIFY_SSL",
            profile.get("settings", {}).get("verify_ssl", "true"),
        )
    else:
        dotenv_credentials = {name for name in credential_names if dotenv_env.get(name)}
        dotenv_direct = {"BLACKDUCK_URL", "BLACKDUCK_TOKEN"}.issubset(dotenv_credentials)
        dotenv_keyring = {"BLACKDUCK_URL", "BLACKDUCK_TOKEN_KEYRING_USER"}.issubset(dotenv_credentials)
        if dotenv_direct and dotenv_keyring:
            die({"error_code": "BLACKDUCK_CREDENTIAL_SOURCE_MISMATCH", "error": "Direct and keyring Black Duck credentials are mutually exclusive"})
        if process_credentials or (dotenv_credentials and not (dotenv_direct or dotenv_keyring)):
            die({"error_code": "BLACKDUCK_CREDENTIAL_SOURCE_MISMATCH", "error": "Incoherent partial Black Duck credential override"})
        base_url = dotenv_env.get("BLACKDUCK_URL", "")
        token_value = dotenv_env.get("BLACKDUCK_TOKEN", "") if dotenv_direct else ""
        token_keyring_user = "" if dotenv_direct else dotenv_env.get("BLACKDUCK_TOKEN_KEYRING_USER", "")
        verify_value = process_env.get("BLACKDUCK_VERIFY_SSL", dotenv_env.get("BLACKDUCK_VERIFY_SSL", "true"))

    try:
        normalized_url = validate_endpoint(base_url) if base_url else ""
    except ConfigError as exc:
        die({"error_code": "BLACKDUCK_ENDPOINT_UNSAFE", "error": str(exc)})
    return RuntimeConfig(normalized_url, token_value, token_keyring_user, parse_verify_ssl(verify_value))


def normalize_status(status: str) -> str:
    value = status.upper()
    return "NOT_AFFECTED" if value == "NOT_VULNERABLE" else value


def normalize_remediation(remediation: str) -> str:
    value = remediation.upper()
    return VALID_REMEDIATION_ALIASES.get(value, value)


class BlackDuckSession:
    def __init__(self, base_url: str, token: str, verify_ssl: bool = True) -> None:
        self.base_url = base_url.rstrip("/")
        self.token = token
        self.session = requests.Session()
        self.session.verify = verify_ssl
        self.bearer = ""
        self.csrf_token = ""
        self.expires_at = 0.0
        self.authenticate()

    def authenticate(self) -> None:
        authentication_url = f"{self.base_url}/api/tokens/authenticate"
        resp = self.session.post(
            authentication_url,
            headers={
                "Authorization": f"token {self.token}",
                "Accept": "application/vnd.blackducksoftware.user-4+json",
            },
            allow_redirects=False,
            timeout=REQUEST_TIMEOUT_SECONDS,
        )
        if resp.status_code != 200:
            try:
                response = resp.json() if "json" in resp.headers.get("content-type", "") else {"message": "Authentication request failed"}
            except Exception:
                response = {"message": "Authentication request failed"}
            def sanitize(value: Any) -> Any:
                if isinstance(value, dict):
                    blocked = {"token", "password", "secret", "access_token", "bearer_token"}
                    return {key: sanitize(item) for key, item in value.items() if key.lower() not in blocked}
                if isinstance(value, list):
                    return [sanitize(item) for item in value]
                return value

            response = sanitize(response)
            payload = {
                "error": "Black Duck authentication request failed",
                "error_code": "BLACKDUCK_REMOTE_AUTHENTICATION_REQUEST_FAILED",
                "status": resp.status_code,
                "url": authentication_url,
                "response": response,
            }
            if resp.status_code == 401:
                payload.update({"error": "Black Duck authentication failed", "error_code": "BLACKDUCK_REMOTE_AUTHENTICATION_FAILED"})
            elif resp.status_code == 403:
                payload.update({"error": "Black Duck authorization failed", "error_code": "BLACKDUCK_REMOTE_AUTHORIZATION_FAILED"})
            die(payload)
        data = resp.json()
        self.bearer = data["bearerToken"]
        self.csrf_token = resp.headers.get("X-CSRF-TOKEN", "")
        self.expires_at = time.time() + int(data.get("expiresInMilliseconds", 7200000)) / 1000 - 120

    def headers(self, accept: str = "application/json") -> Json:
        if time.time() >= self.expires_at:
            self.authenticate()
        headers = {"Authorization": f"Bearer {self.bearer}", "Accept": accept}
        if self.csrf_token:
            headers["X-CSRF-TOKEN"] = self.csrf_token
        return headers

    def url(self, path_or_url: str) -> str:
        if not path_or_url.startswith("http"):
            return f"{self.base_url}{path_or_url}"
        configured = urlparse(self.base_url)
        candidate = urlparse(path_or_url)
        if candidate.scheme.lower() != "https" or candidate.netloc.lower() != configured.netloc.lower():
            die({
                "error_code": "BLACKDUCK_RESOURCE_ORIGIN_MISMATCH",
                "error": "Black Duck resource URL does not match the configured origin",
            })
        return path_or_url

    def get(self, path_or_url: str, params: Optional[Json] = None, accept: str = "application/json") -> requests.Response:
        return self.session.get(
            self.url(path_or_url), headers=self.headers(accept), params=params,
            timeout=REQUEST_TIMEOUT_SECONDS,
            allow_redirects=False,
        )

    def put(self, path_or_url: str, data: Json, accept: Optional[str] = "application/json", content_type: str = "application/json") -> requests.Response:
        headers = self.headers(accept) if accept else self.headers("application/json")
        if not accept:
            headers.pop("Accept", None)
        headers["Content-Type"] = content_type
        return self.session.put(
            self.url(path_or_url), headers=headers, json=data,
            timeout=REQUEST_TIMEOUT_SECONDS,
            allow_redirects=False,
        )

    def paged(self, path_or_url: str, params: Optional[Json] = None, accept: str = "application/json", page_size: int = 250) -> Iterator[Json]:
        offset = 0
        base_params = dict(params or {})
        while True:
            page_params = dict(base_params)
            page_params.update({"offset": offset, "limit": page_size})
            resp = self.get(path_or_url, page_params, accept)
            if resp.status_code != 200:
                die({"error": f"GET {path_or_url} failed", "httpStatus": resp.status_code, "body": resp.text[:500]})
            body = resp.json()
            items = body.get("items", [])
            for item in items:
                yield item
            offset += len(items)
            if not items or offset >= int(body.get("totalCount", 0)):
                break


def credential_store_secret(service: str, username: str) -> str:
    if not keyring:
        die({"error": "keyring is not installed; set BLACKDUCK_TOKEN or run with uv so keyring is available"})
    try:
        secret = keyring.get_password(service, username)
    except KeyringError as exc:
        die({
            "error_code": "BLACKDUCK_KEYRING_BACKEND_FAILURE",
            "error": "Black Duck keyring backend could not read the selected entry",
            "keyring_user": username,
            "details": str(exc),
        })
    if not secret:
        die({
            "error_code": "BLACKDUCK_KEYRING_ENTRY_MISSING",
            "error": "Selected Black Duck keyring entry has no token",
            "keyring_user": username,
        })
    return secret


def parse_verify_ssl(value: Any) -> bool:
    try:
        return normalize_verify_ssl(value) == "true"
    except ConfigError:
        die({
            "error_code": "BLACKDUCK_SSL_CONFIGURATION_INVALID",
            "error": "BLACKDUCK_VERIFY_SSL must be a recognized boolean value",
        })


def session(runtime: RuntimeConfig) -> BlackDuckSession:
    token = runtime.token_value
    if runtime.token_keyring_user and not token:
        token = credential_store_secret("AgentDevelopmentToolkit:blackduck", runtime.token_keyring_user)
    if not runtime.base_url or not token:
        die({
            "error_code": "BLACKDUCK_PROFILE_METADATA_MISSING",
            "error": "Black Duck profile metadata is missing",
            "config_path": str(config_path()),
        })
    return BlackDuckSession(runtime.base_url, token, runtime.verify_ssl)


def link(resource: Json, rel: str) -> Optional[str]:
    for item in resource.get("_meta", {}).get("links", []):
        if item.get("rel") == rel:
            return item.get("href")
    return None


def href(resource: Json) -> str:
    return resource.get("_meta", {}).get("href", "")


def find_project(bd: BlackDuckSession, name: str) -> Json:
    for project in bd.paged("/api/projects", accept="application/vnd.blackducksoftware.project-detail-4+json"):
        if project.get("name") == name:
            return project
    die({"error": f"Project not found: {name}"})


def find_version(bd: BlackDuckSession, project: Json, name: str) -> Json:
    versions_url = link(project, "versions")
    if not versions_url:
        die({"error": "Project response has no versions link", "project": project.get("name")})
    for version in bd.paged(versions_url, accept="application/vnd.blackducksoftware.project-detail-5+json"):
        if version.get("versionName") == name:
            return version
    die({"error": f"Version not found: {name}", "project": project.get("name")})


def version_url(project: Json, version: Json) -> str:
    return href(version) or f"{href(project)}/versions/{version.get('versionId', '')}"


def query_params(query: Optional[str], field: str, filters: Optional[List[str]] = None) -> Json:
    params: Json = {}
    if query:
        params["q"] = [f"{field}:{query}"]
    if filters:
        params["filter"] = filters
    return params


def limited(items: Iterable[Json], limit: Optional[int]) -> Iterator[Json]:
    for idx, item in enumerate(items):
        if limit is not None and idx >= limit:
            break
        yield item


def summarize_project(project: Json) -> Json:
    return {
        "name": project.get("name"),
        "description": project.get("description", ""),
        "projectOwner": project.get("projectOwner"),
        "createdAt": project.get("createdAt"),
        "updatedAt": project.get("updatedAt"),
        "_meta": {"href": href(project)},
    }


def summarize_version(version: Json) -> Json:
    return {
        "versionName": version.get("versionName"),
        "nickname": version.get("nickname"),
        "phase": version.get("phase"),
        "distribution": version.get("distribution"),
        "createdAt": version.get("createdAt"),
        "releasedOn": version.get("releasedOn"),
        "_meta": {"href": href(version)},
    }


def summarize_license(item: Json) -> Json:
    return {
        "name": item.get("name"),
        "licenseFamily": item.get("licenseFamily"),
        "licenseStatus": item.get("licenseStatus"),
        "ownership": item.get("ownership"),
        "spdxId": item.get("spdxId") or item.get("spdxID"),
        "codeSharing": item.get("codeSharing"),
        "_meta": {"href": href(item), "links": item.get("_meta", {}).get("links", [])},
    }


def summarize_component(item: Json) -> Json:
    licenses = item.get("licenses") or []
    return {
        "componentName": item.get("componentName"),
        "componentVersionName": item.get("componentVersionName"),
        "component": item.get("component"),
        "componentVersion": item.get("componentVersion"),
        "packageUrl": item.get("packageUrl") or item.get("purl"),
        "matchTypes": item.get("matchTypes", []),
        "usages": item.get("usages", []),
        "licenseDisplay": licenses[0].get("licenseDisplay", "Unknown") if licenses else "Unknown",
        "reviewStatus": item.get("reviewStatus"),
        "policyStatus": item.get("policyStatus"),
        "licenseRiskProfile": item.get("licenseRiskProfile"),
        "operationalRiskProfile": item.get("operationalRiskProfile"),
        "securityRiskProfile": item.get("securityRiskProfile"),
        "_meta": {"href": href(item), "links": item.get("_meta", {}).get("links", [])},
    }


def code_location_hints(item: Json) -> List[Json]:
    return [{"field": k, "value": v} for k, v in item.items() if "codelocation" in k.lower()]


def safe_paged(bd: BlackDuckSession, url: str, accept: str = "application/json") -> Iterator[Json]:
    """Page through a resource URL silently returning an empty iterator on any HTTP error.

    Unlike BlackDuckSession.paged(), this never calls die() — callers use it to probe
    optional or version-gated endpoints without aborting the whole command.
    """
    offset = 0
    page_size = 250
    while True:
        resp = bd.get(url, {"offset": offset, "limit": page_size}, accept)
        if resp.status_code != 200:
            return
        body = resp.json()
        items = body.get("items", [])
        for item in items:
            yield item
        offset += len(items)
        if not items or offset >= int(body.get("totalCount", 0)):
            break


def code_locations(bd: BlackDuckSession, version: Json, limit: Optional[int]) -> List[Json]:
    url = link(version, "codelocations") or f"{href(version)}/codelocations"
    rows = []
    for cl in limited(bd.paged(url, accept="application/vnd.blackducksoftware.scan-4+json"), limit):
        rows.append({
            "name": cl.get("name"),
            "url": cl.get("url"),
            "createdAt": cl.get("createdAt"),
            "updatedAt": cl.get("updatedAt"),
            "mappedProjectVersion": cl.get("mappedProjectVersion"),
            "status": cl.get("status"),
            "_meta": {"href": href(cl)},
        })
    return rows


def component_filter(bd: BlackDuckSession, component: Optional[str]) -> List[str]:
    if not component:
        return []
    component_url = component if component.startswith("http") else f"{bd.base_url}/api/components/{component}"
    return ["bomComponents:" + base64.b64encode(component_url.encode()).decode()]


def normalize_filter_value(value: str) -> str:
    return re.sub(r"[\s-]+", "_", value.strip()).upper()


def values_match(actual: Any, wanted: Optional[List[str]]) -> bool:
    if not wanted:
        return True
    wanted_set = {normalize_filter_value(v) for v in wanted}
    actual_values = set()
    if isinstance(actual, list):
        actual_values.update(normalize_filter_value(str(v)) for v in actual)
    elif actual is not None:
        actual_values.add(normalize_filter_value(str(actual)))
    return bool(actual_values & wanted_set)


def risk_profile_levels(profile: Any) -> Set[str]:
    levels: Set[str] = set()
    if isinstance(profile, str):
        levels.add(normalize_filter_value(profile))
    elif isinstance(profile, dict):
        for key in ("risk", "riskLevel", "severity", "status", "countType", "name"):
            if profile.get(key):
                levels.add(normalize_filter_value(str(profile[key])))
        for count in profile.get("counts", []) or []:
            try:
                has_risk = int(count.get("count", 0)) > 0
            except (TypeError, ValueError):
                has_risk = bool(count.get("count"))
            if has_risk and count.get("countType"):
                levels.add(normalize_filter_value(str(count["countType"])))
    elif isinstance(profile, list):
        for entry in profile:
            levels.update(risk_profile_levels(entry))
    return levels


def risk_matches(profile: Any, wanted: Optional[List[str]]) -> bool:
    if not wanted:
        return True
    wanted_set = {normalize_filter_value(v) for v in wanted}
    return bool(risk_profile_levels(profile) & wanted_set)


def component_matches_filters(item: Json, args: argparse.Namespace) -> bool:
    if args.policy_status and normalize_filter_value(str(item.get("policyStatus", ""))) != normalize_filter_value(args.policy_status):
        return False
    if not values_match(item.get("reviewStatus"), getattr(args, "review_status", None)):
        return False
    if not risk_matches(item.get("licenseRiskProfile"), getattr(args, "license_risk", None)):
        return False
    if not risk_matches(item.get("operationalRiskProfile"), getattr(args, "operational_risk", None)):
        return False
    if not risk_matches(item.get("securityRiskProfile"), getattr(args, "security_risk", None)):
        return False
    return True


def limit_reached(count: int, limit: Optional[int], all_items: bool = False) -> bool:
    return not all_items and limit is not None and limit > 0 and count >= limit


def vulnerable_bom_items(bd: BlackDuckSession, ver_url: str, filters: Optional[List[str]] = None) -> Iterator[Json]:
    yield from bd.paged(
        f"{ver_url}/vulnerable-bom-components",
        params={"filter": filters} if filters else None,
        accept="application/vnd.blackducksoftware.bill-of-materials-6+json",
    )


def vuln_matches(vuln: Json, severity: Optional[str], status: Optional[str], query: Optional[str]) -> bool:
    if severity and str(vuln.get("severity", "")).upper() != severity.upper():
        return False
    if status and str(vuln.get("remediationStatus", "")).upper() != status.upper():
        return False
    if query:
        text = json.dumps(vuln, default=str).lower()
        return query.lower() in text
    return True


def extract_component_ids(url: str) -> tuple[Optional[str], Optional[str]]:
    match = re.search(r"/components/([^/]+)/versions/([^/?#]+)", url or "")
    if match:
        return match.group(1), match.group(2)
    match = re.search(r"/components/([^/?#]+)", url or "")
    return (match.group(1), None) if match else (None, None)


def matched_files(bd: BlackDuckSession, ver_url: str, item: Json, limit: int) -> List[Json]:
    """Return all matched files for a BOM component, using full pagination across all available endpoints.

    Strategy (highest to lowest fidelity):
    1. Per-origin matched-files links embedded in the BOM item's origins[]
       (rel=matched-files in each origin's _meta.links — project-scoped, origin-level URL).
    2. Top-level BOM item matched-files link (link(item, 'matched-files') from _meta.links).
       On this instance this is already origin-level, but we include it as a fallback/secondary.
    3. Constructed component-version-level URL (.../components/{id}/versions/{id}/matched-files).
    4. Constructed component-level URL (.../components/{id}/matched-files).

    All sources use safe_paged() for proper pagination (no 250-item truncation).
    Results are deduplicated by (archiveContext, path).
    """
    comp_id, comp_ver_id = extract_component_ids(
        href(item) or item.get("componentVersion") or item.get("component") or ""
    )
    seen: Set[str] = set()
    files: List[Json] = []

    def collect(url: str) -> None:
        for mf in safe_paged(bd, url):
            if len(files) >= limit:
                return
            archive_ctx = mf.get("archiveContext") or ""
            path = mf.get("uri") or mf.get("filePath") or mf.get("path") or mf.get("name") or ""
            dedup_key = f"{archive_ctx}!{path}" if archive_ctx else path
            if dedup_key and dedup_key not in seen:
                seen.add(dedup_key)
                files.append({
                    "path": path,
                    "archiveContext": archive_ctx or None,
                    "fullPath": f"{archive_ctx}!{path}" if archive_ctx else path,
                    "uri": mf.get("uri"),
                    "matchType": mf.get("matchType") or mf.get("matchTypeName"),
                    "codeLocation": mf.get("codeLocation") or mf.get("codeLocationName"),
                    "_meta": {"href": href(mf)},
                })

    # 1. Per-origin matched-files (most granular; project-scoped)
    for origin in item.get("origins") or []:
        origin_mf_url = link(origin, "matched-files")
        if origin_mf_url and len(files) < limit:
            collect(origin_mf_url)

    # 2. Top-level BOM item matched-files link (often same as #1, but catches edge cases)
    top_mf_link = link(item, "matched-files")
    if top_mf_link and len(files) < limit:
        collect(top_mf_link)

    # 3. Constructed component-version level
    if comp_id and comp_ver_id and len(files) < limit:
        collect(f"{ver_url}/components/{comp_id}/versions/{comp_ver_id}/matched-files")

    # 4. Constructed component level
    if comp_id and len(files) < limit:
        collect(f"{ver_url}/components/{comp_id}/matched-files")

    return files[:limit]


def detection_note(item: Json, matched_file_count: int) -> Optional[str]:
    """Return a human-readable note explaining why matched-files may be empty."""
    match_types = item.get("matchTypes") or []
    total_file_match_count = item.get("totalFileMatchCount", 0) or 0
    if matched_file_count > 0:
        return None
    if "MANUAL_BOM_COMPONENT" in match_types:
        return (
            "Component was added manually (MANUAL_BOM_COMPONENT). "
            "No scan-based file evidence is available."
        )
    pkg_manager_types = {"FILE_DEPENDENCY_DIRECT", "FILE_DEPENDENCY_TRANSITIVE"}
    if match_types and all(mt in pkg_manager_types for mt in match_types):
        return (
            f"Component was detected via package-manager manifest scanning ({', '.join(match_types)}). "
            f"totalFileMatchCount={total_file_match_count} counts manifest-file occurrences (e.g. pom.xml, "
            f"package.json), not binary/source signature matches. "
            "Use get-dependency-paths to see the dependency-graph resolution path instead."
        )
    if total_file_match_count > 0:
        return (
            f"totalFileMatchCount={total_file_match_count} but matched-files API returned 0. "
            "The file match data may not be accessible via this API endpoint for the scan type used."
        )
    return "No file matches found. The component may not have been detected via file-content scanning."


def dependency_paths(bd: BlackDuckSession, ver_url: str, item: Json, limit: int) -> List[Json]:
    """Fetch dependency-graph resolution paths for a BOM component via its origin-level endpoints.

    The dependency-paths endpoint (added in Black Duck 2021.2) shows whether a package-manager-
    detected component is a DIRECT or TRANSITIVE dependency and the resolution chain that pulled
    it in. Returns an empty list if the endpoint is not supported by the server.

    URL pattern:
        {ver_url}/components/{compId}/versions/{compVerId}/origins/{originId}/dependency-paths
    """
    results: List[Json] = []
    for origin in item.get("origins") or []:
        if len(results) >= limit:
            break
        # Derive dependency-paths URL from the origin's matched-files link
        # (same base path, swap the suffix)
        origin_mf_url = link(origin, "matched-files")
        if origin_mf_url and "/matched-files" in origin_mf_url:
            dep_url = origin_mf_url.replace("/matched-files", "/dependency-paths")
        else:
            # Fall back to constructing from the origin href
            origin_href_val = href(origin)
            match = re.search(
                r"/components/([^/]+)/versions/([^/]+)/origins/([^/?#]+)",
                origin_href_val or "",
            )
            if not match:
                continue
            comp_id, comp_ver_id, origin_id = match.group(1), match.group(2), match.group(3)
            dep_url = (
                f"{ver_url}/components/{comp_id}/versions/{comp_ver_id}"
                f"/origins/{origin_id}/dependency-paths"
            )
        for dp in safe_paged(bd, dep_url):
            if len(results) >= limit:
                break
            results.append({
                "origin": origin.get("name") or origin.get("externalId"),
                "externalNamespace": origin.get("externalNamespace"),
                "externalId": origin.get("externalId"),
                "type": dp.get("type"),
                "pathNodes": dp.get("path") or dp.get("pathNodes") or [],
                "_meta": {"href": href(dp)},
            })
    return results


def affected_components(bd: BlackDuckSession, ver_url: str, vuln_id: str, related_id: Optional[str] = None) -> List[Json]:
    wanted = {vuln_id.upper()}
    if related_id:
        wanted.add(related_id.upper())
    out = []
    for item in vulnerable_bom_items(bd, ver_url):
        vuln = item.get("vulnerabilityWithRemediation") or {}
        ids = {str(vuln.get("vulnerabilityName", "")).upper()}
        rv = str(vuln.get("relatedVulnerability", "")).upper()
        if rv:
            ids.add(rv.rsplit("/", 1)[-1])
        if ids & wanted:
            out.append({"component": summarize_component(item), "vulnerability": vuln, "codeLocationHints": code_location_hints(item)})
    return out


def component_relation(bd: BlackDuckSession, item: Json, vuln: Json, fallback_vuln_id: str) -> Optional[Json]:
    comp_id, comp_ver_id = extract_component_ids(href(item) or item.get("componentVersion") or "")
    if not (comp_id and comp_ver_id):
        return None
    relation = {
        "vulnerability": f"{bd.base_url}/api/vulnerabilities/{vuln.get('vulnerabilityName') or fallback_vuln_id}",
        "component": f"{bd.base_url}/api/components/{comp_id}/versions/{comp_ver_id}",
    }
    if vuln.get("relatedVulnerability"):
        relation["relatedVulnerability"] = vuln["relatedVulnerability"]
    return relation


def resolve_license(bd: BlackDuckSession, value: str) -> Json:
    if value.startswith("http"):
        return {"input": value, "href": value, "name": None}
    if re.fullmatch(r"[0-9a-fA-F-]{16,}", value):
        return {"input": value, "href": f"{bd.base_url}/api/licenses/{value}", "name": None}
    for lic in bd.paged("/api/licenses", query_params(value, "name"), "application/vnd.blackducksoftware.component-detail-5+json"):
        if lic.get("name", "").lower() == value.lower():
            return {"input": value, "href": href(lic), "name": lic.get("name")}
    die({"error": f"License not found: {value}", "hint": "Pass a license name, license UUID, or full /api/licenses/{id} URL."})


def component_update_payloads(item: Json, update: Json, license_info: Optional[Json]) -> List[tuple[Json, str]]:
    payloads: List[tuple[Json, str]] = []
    payloads.append((dict(update), "partial-json"))
    payloads.append(({**item, **update}, "full-item-json"))
    if license_info:
        license_href = license_info["href"]
        license_update = dict(update)
        license_update.pop("licenses", None)
        license_update["license"] = license_href
        payloads.append((license_update, "partial-license-json"))
        payloads.append(({**item, **license_update}, "full-item-license-json"))
    return payloads


# Commands

def cmd_list_projects(args: argparse.Namespace) -> None:
    bd = session(args.runtime_config)
    projects = []
    for p in bd.paged("/api/projects", query_params(args.query, "name"), "application/vnd.blackducksoftware.project-detail-4+json"):
        if args.query and args.exact and p.get("name", "").lower() != args.query.lower():
            continue
        projects.append(summarize_project(p))
        if len(projects) >= args.limit:
            break
    emit({"totalProjects": len(projects), "query": args.query, "exact": args.exact, "projects": projects})


def cmd_list_versions(args: argparse.Namespace) -> None:
    bd = session(args.runtime_config)
    project = find_project(bd, args.project)
    versions = []
    for v in bd.paged(link(project, "versions"), query_params(args.query, "versionName"), "application/vnd.blackducksoftware.project-detail-5+json"):
        if args.query and args.exact and v.get("versionName", "").lower() != args.query.lower():
            continue
        versions.append(summarize_version(v))
        if len(versions) >= args.limit:
            break
    emit({"project": args.project, "totalVersions": len(versions), "query": args.query, "exact": args.exact, "versions": versions})


def cmd_list_licenses(args: argparse.Namespace) -> None:
    bd = session(args.runtime_config)
    rows = []
    for lic in bd.paged("/api/licenses", query_params(args.query, "name"), "application/vnd.blackducksoftware.component-detail-5+json"):
        name = lic.get("name", "")
        if args.query and args.exact and name.lower() != args.query.lower():
            continue
        rows.append(summarize_license(lic))
        if limit_reached(len(rows), args.limit, args.all):
            break
    emit({
        "totalLicenses": len(rows),
        "filters": {"query": args.query, "exact": args.exact, "limit": None if args.all else args.limit},
        "licenses": rows,
    })


def cmd_list_components(args: argparse.Namespace) -> None:
    bd = session(args.runtime_config)
    project = find_project(bd, args.project)
    version = find_version(bd, project, args.version)
    url = link(version, "components") or f"{version_url(project, version)}/components"
    rows = []
    for item in bd.paged(url, query_params(args.query, "componentName", args.filter), "application/vnd.blackducksoftware.bill-of-materials-6+json"):
        name = item.get("componentName", "")
        if args.query and args.exact and name.lower() != args.query.lower():
            continue
        if not component_matches_filters(item, args):
            continue
        rows.append(summarize_component(item))
        if limit_reached(len(rows), args.limit, args.all):
            break
    emit({
        "project": args.project,
        "version": args.version,
        "totalComponents": len(rows),
        "filters": {
            "name": args.query,
            "exact": args.exact,
            "filter": args.filter,
            "reviewStatus": args.review_status,
            "licenseRisk": args.license_risk,
            "operationalRisk": args.operational_risk,
            "securityRisk": args.security_risk,
            "policyStatus": args.policy_status,
            "limit": None if args.all else args.limit,
        },
        "components": rows,
    })


def cmd_list_vulnerabilities(args: argparse.Namespace) -> None:
    bd = session(args.runtime_config)
    project = find_project(bd, args.project)
    version = find_version(bd, project, args.version)
    filters = list(args.filter or []) + component_filter(bd, args.component)
    vulns = []
    seen = set()
    for item in vulnerable_bom_items(bd, version_url(project, version), filters or None):
        vuln = item.get("vulnerabilityWithRemediation") or {}
        if not vuln_matches(vuln, args.severity, args.status, args.query):
            continue
        key = (vuln.get("vulnerabilityName"), vuln.get("relatedVulnerability"), href(item))
        if key in seen:
            continue
        seen.add(key)
        row = dict(vuln)
        row["affectedComponent"] = summarize_component(item)
        vulns.append(row)
        if args.limit and len(vulns) >= args.limit:
            break
    vulns.sort(key=lambda v: SEVERITY_ORDER.get(str(v.get("severity", "UNKNOWN")).upper(), 99))
    emit({"project": args.project, "version": args.version, "totalVulnerabilities": len(vulns), "filters": {"severity": args.severity, "status": args.status, "component": args.component, "query": args.query, "filter": args.filter}, "vulnerabilities": vulns})


def cmd_get_vulnerability_details(args: argparse.Namespace) -> None:
    bd = session(args.runtime_config)
    project = find_project(bd, args.project)
    version = find_version(bd, project, args.version)
    ver_url = version_url(project, version)
    vuln_resp = bd.get(f"/api/vulnerabilities/{args.vuln_id}")
    vuln_details = vuln_resp.json() if vuln_resp.status_code == 200 else None
    components = affected_components(bd, ver_url, args.vuln_id, args.related_id)
    if vuln_details is None and not components:
        die({"error": f"Vulnerability not found: {args.vuln_id}", "httpStatus": vuln_resp.status_code, "body": vuln_resp.text[:500]})
    emit({"project": args.project, "version": args.version, "vulnerabilityId": args.vuln_id, "relatedVulnerabilityId": args.related_id, "details": vuln_details, "affectedComponents": components})


def find_component_matches(bd: BlackDuckSession, version: Json, ver_url: str, args: argparse.Namespace) -> List[Json]:
    components_url = link(version, "components") or f"{ver_url}/components"
    matches = []
    needle = args.component.lower()
    for item in bd.paged(components_url, query_params(None if args.component_id else args.component, "componentName", getattr(args, "filter", None)), "application/vnd.blackducksoftware.bill-of-materials-6+json"):
        text_fields = [item.get("componentName", ""), item.get("component", ""), item.get("componentVersion", ""), href(item)]
        if args.component_id:
            ok = any(needle in str(field).lower() for field in text_fields)
        else:
            ok = item.get("componentName", "").lower() == needle if args.exact else needle in item.get("componentName", "").lower()
        if not ok:
            continue
        matches.append(item)
        if len(matches) >= args.limit:
            break
    return matches


def cmd_get_code_location(args: argparse.Namespace) -> None:
    bd = session(args.runtime_config)
    project = find_project(bd, args.project)
    version = find_version(bd, project, args.version)
    ver_url = version_url(project, version)
    matches = []
    for item in find_component_matches(bd, version, ver_url, args):
        files = matched_files(bd, ver_url, item, args.matched_file_limit)
        matches.append({
            "component": summarize_component(item),
            "matchTypes": item.get("matchTypes", []),
            "totalFileMatchCount": item.get("totalFileMatchCount"),
            "codeLocationHints": code_location_hints(item),
            "matchedFiles": files,
            "matchedFilesNote": detection_note(item, len(files)),
        })
    emit({
        "project": args.project,
        "version": args.version,
        "component": args.component,
        "totalMatches": len(matches),
        "versionCodeLocations": code_locations(bd, version, args.code_location_limit),
        "matches": matches,
    })


def cmd_get_matched_files(args: argparse.Namespace) -> None:
    bd = session(args.runtime_config)
    project = find_project(bd, args.project)
    version = find_version(bd, project, args.version)
    ver_url = version_url(project, version)
    matches = []
    for item in find_component_matches(bd, version, ver_url, args):
        files = matched_files(bd, ver_url, item, args.matched_file_limit)
        note = detection_note(item, len(files))
        matches.append({
            "component": summarize_component(item),
            "matchTypes": item.get("matchTypes", []),
            "totalFileMatchCount": item.get("totalFileMatchCount"),
            "origins": [
                {
                    "name": o.get("name"),
                    "externalNamespace": o.get("externalNamespace"),
                    "externalId": o.get("externalId"),
                    "packageUrl": o.get("packageUrl"),
                }
                for o in (item.get("origins") or [])
            ],
            "totalMatchedFiles": len(files),
            "matchedFiles": files,
            "note": note,
        })
    emit({
        "project": args.project,
        "version": args.version,
        "component": args.component,
        "totalComponents": len(matches),
        "matches": matches,
    })


def cmd_get_dependency_paths(args: argparse.Namespace) -> None:
    """Show the dependency-graph resolution path for package-manager-detected components.

    Uses the origin-level dependency-paths endpoint (available in Black Duck 2021.2+):
        .../components/{compId}/versions/{compVerId}/origins/{originId}/dependency-paths

    Returns DIRECT or TRANSITIVE classification plus the resolution chain for each origin.
    Returns an empty dependencyPaths list (not an error) when the endpoint returns 404 —
    either the Black Duck instance is older than 2021.2, the component was not detected
    via package-manager scanning, or no dependency graph data is available for this scan.
    """
    bd = session(args.runtime_config)
    project = find_project(bd, args.project)
    version = find_version(bd, project, args.version)
    ver_url = version_url(project, version)
    matches = []
    for item in find_component_matches(bd, version, ver_url, args):
        paths = dependency_paths(bd, ver_url, item, args.limit)
        match_types = item.get("matchTypes", [])
        origins_summary = [
            {
                "name": o.get("name"),
                "externalNamespace": o.get("externalNamespace"),
                "externalId": o.get("externalId"),
                "packageUrl": o.get("packageUrl"),
            }
            for o in (item.get("origins") or [])
        ]
        note = None
        if not paths:
            pkg_types = {"FILE_DEPENDENCY_DIRECT", "FILE_DEPENDENCY_TRANSITIVE"}
            if all(mt in pkg_types for mt in match_types) and match_types:
                note = (
                    "dependency-paths returned no data. The endpoint may not be supported on this "
                    "Black Duck version (requires 2021.2+), or dependency graph data was not captured "
                    "for this scan. Consider re-scanning with Black Duck Detect's dependency resolution enabled."
                )
            else:
                note = (
                    f"dependency-paths is primarily meaningful for FILE_DEPENDENCY_* match types. "
                    f"This component has matchTypes={match_types}. "
                    "Use get-matched-files for file-content/signature-detected components."
                )
        matches.append({
            "component": summarize_component(item),
            "matchTypes": match_types,
            "totalFileMatchCount": item.get("totalFileMatchCount"),
            "origins": origins_summary,
            "totalDependencyPaths": len(paths),
            "dependencyPaths": paths,
            "note": note,
        })
    emit({
        "project": args.project,
        "version": args.version,
        "component": args.component,
        "totalComponents": len(matches),
        "hint": (
            "dependency-paths shows the package-manager dependency graph path (DIRECT vs TRANSITIVE). "
            "For file-content/signature matches use get-matched-files instead."
        ),
        "matches": matches,
    })


def cmd_update_component(args: argparse.Namespace) -> None:
    if not (args.review_status or args.license or args.usage or args.comment):
        die({"error": "At least one of --review-status, --license, --usage, or --comment is required"})
    bd = session(args.runtime_config)
    project = find_project(bd, args.project)
    version = find_version(bd, project, args.version)
    ver_url = version_url(project, version)
    license_info = resolve_license(bd, args.license) if args.license else None

    update: Json = {}
    if args.review_status:
        update["reviewStatus"] = normalize_filter_value(args.review_status)
    if args.usage:
        update["usages"] = [normalize_filter_value(u) for u in args.usage]
    if license_info:
        update["licenses"] = [{"license": license_info["href"]}]
    if args.comment:
        update["comment"] = args.comment

    results = []
    media_type = "application/vnd.blackducksoftware.bill-of-materials-6+json"
    for item in find_component_matches(bd, version, ver_url, args):
        item_url = href(item)
        if not item_url:
            results.append({"component": summarize_component(item), "ok": False, "error": "Component has no _meta.href"})
            continue
        attempts = []
        last_resp = None
        for payload, label in component_update_payloads(item, update, license_info):
            for accept, content_type, media_label in (
                ("application/json", "application/json", "json"),
                (media_type, media_type, "bom-v6"),
            ):
                resp = bd.put(item_url, payload, accept=accept, content_type=content_type)
                last_resp = resp
                attempts.append({"label": f"{label}-{media_label}", "httpStatus": resp.status_code, "body": resp.text[:500] if resp.status_code not in (200, 202, 204) else ""})
                if resp.status_code in (200, 202, 204):
                    break
            if last_resp and last_resp.status_code in (200, 202, 204):
                break
        ok = bool(last_resp and last_resp.status_code in (200, 202, 204))
        results.append({
            "component": summarize_component(item),
            "requestedUpdate": update,
            "httpStatus": last_resp.status_code if last_resp else None,
            "ok": ok,
            "responseBody": last_resp.text[:1000] if last_resp and not ok else "",
            "attempts": attempts,
        })
        if limit_reached(len(results), args.limit, False):
            break

    if not results:
        die({"error": f"No matching components found: {args.component}"})
    ok = all(r.get("ok") for r in results)
    emit({
        "project": args.project,
        "version": args.version,
        "component": args.component,
        "requestedReviewStatus": update.get("reviewStatus"),
        "requestedLicense": license_info,
        "requestedUsages": update.get("usages"),
        "componentsUpdated": sum(1 for r in results if r.get("ok")),
        "ok": ok,
        "results": results,
    })


def cmd_update_vulnerability(args: argparse.Namespace) -> None:
    bd = session(args.runtime_config)
    project = find_project(bd, args.project)
    version = find_version(bd, project, args.version)
    ver_url = version_url(project, version)
    wanted = {args.vuln_id.upper()}
    if args.related_id:
        wanted.add(args.related_id.upper())

    update = {"remediationStatus": normalize_status(args.status)}
    if args.justification:
        update["remediationJustification"] = args.justification.upper()
    if args.remediation:
        update["remediation"] = normalize_remediation(args.remediation)

    results = []
    media_type = "application/vnd.blackducksoftware.bill-of-materials-6+json"
    for item in vulnerable_bom_items(bd, ver_url):
        vuln = item.get("vulnerabilityWithRemediation") or {}
        ids = {str(vuln.get("vulnerabilityName", "")).upper(), str(vuln.get("relatedVulnerability", "")).upper().rsplit("/", 1)[-1]}
        if not (ids & wanted):
            continue
        item_url = href(item)
        if not item_url:
            continue
        attempts = []
        for payload, accept, content_type, label in (
            # Matches the official hub-rest-api-python batch-remediation helper.
            (update, "application/json", "application/json", "partial-json"),
            # Matches the official update_vuln_status.py example more closely.
            ({**item, **update}, "application/json", "application/json", "full-item-json"),
            # Compatibility fallback for older BOM v6 vulnerable component payloads.
            (update, media_type, media_type, "partial-bom-v6"),
            ({**item, **update}, media_type, media_type, "full-item-bom-v6"),
        ):
            resp = bd.put(item_url, payload, accept=accept, content_type=content_type)
            attempts.append({"label": label, "httpStatus": resp.status_code, "body": resp.text[:500] if resp.status_code not in (200, 202, 204) else ""})
            if resp.status_code in (200, 202, 204):
                break
            if resp.status_code != 406:
                break
        results.append({
            "component": summarize_component(item),
            "httpStatus": resp.status_code,
            "ok": resp.status_code in (200, 202, 204),
            "responseBody": resp.text[:1000] if resp.status_code not in (200, 202, 204) else "",
            "attempts": attempts,
        })

    if not results:
        die({"error": f"No affected components found for vulnerability: {args.vuln_id}"})
    ok = all(r["ok"] for r in results)
    emit({"project": args.project, "version": args.version, "vulnerabilityId": args.vuln_id, "relatedVulnerabilityId": args.related_id, "requestedStatus": normalize_status(args.status), "requestedJustification": args.justification, "requestedRemediation": normalize_remediation(args.remediation) if args.remediation else None, "componentsUpdated": sum(1 for r in results if r["ok"]), "ok": ok, "results": results})


def cmd_list_remediation_values(args: argparse.Namespace) -> None:
    emit({
        "remediationStatuses": DOCUMENTED_STATUSES,
        "statusAliases": {"NOT_VULNERABLE": "NOT_AFFECTED"},
        "statusJustifications": VALID_STATUS_JUSTIFICATIONS,
        "remediations": VALID_REMEDIATIONS,
        "remediationAliases": VALID_REMEDIATION_ALIASES,
        "notes": [
            "Status Justification is required by the UI/docs when status is Known Not Affected (NOT_AFFECTED).",
            "Remediation is required by the UI/docs when status is Known Affected (AFFECTED).",
            "Exact writable API field support can vary by Black Duck version; verify against /api-doc/openapi3-public.json on your instance.",
        ],
        "sources": [
            "https://abb.app.blackduck.com/doc/Risk/RemediateRisk.html",
            "https://abb.app.blackduck.com/doc/ReleaseNotes/2025.1.x/newAndChangedFeatures_2025_1_0.html",
            "https://documentation.blackduck.com/bundle/bd-hub/page/ReportingDatabase/componentVulnerabilityTable.html",
        ],
    })


def cmd_comment_vulnerability(args: argparse.Namespace) -> None:
    bd = session(args.runtime_config)
    project = find_project(bd, args.project)
    version = find_version(bd, project, args.version)
    ver_url = version_url(project, version)
    wanted = {args.vuln_id.upper()}
    if args.related_id:
        wanted.add(args.related_id.upper())

    update = {"comment": args.comment}
    results = []
    media_type = "application/vnd.blackducksoftware.bill-of-materials-6+json"
    for item in vulnerable_bom_items(bd, ver_url):
        vuln = item.get("vulnerabilityWithRemediation") or {}
        ids = {str(vuln.get("vulnerabilityName", "")).upper(), str(vuln.get("relatedVulnerability", "")).upper().rsplit("/", 1)[-1]}
        if not (ids & wanted):
            continue
        item_url = href(item)
        if not item_url:
            continue
        attempts = []
        for payload, accept, content_type, label in (
            (update, "application/json", "application/json", "comment-json"),
            ({**item, **update}, "application/json", "application/json", "full-item-comment-json"),
            (update, media_type, media_type, "comment-bom-v6"),
            ({**item, **update}, media_type, media_type, "full-item-comment-bom-v6"),
        ):
            resp = bd.put(item_url, payload, accept=accept, content_type=content_type)
            attempts.append({"label": label, "httpStatus": resp.status_code, "body": resp.text[:500] if resp.status_code not in (200, 202, 204) else ""})
            if resp.status_code in (200, 202, 204):
                break
            if resp.status_code != 406:
                break
        results.append({
            "component": summarize_component(item),
            "httpStatus": resp.status_code,
            "ok": resp.status_code in (200, 202, 204),
            "responseBody": resp.text[:1000] if resp.status_code not in (200, 202, 204) else "",
            "attempts": attempts,
        })

    if not results:
        die({"error": f"No affected components found for vulnerability: {args.vuln_id}"})
    ok = all(r["ok"] for r in results)
    emit({"project": args.project, "version": args.version, "vulnerabilityId": args.vuln_id, "relatedVulnerabilityId": args.related_id, "componentsCommented": sum(1 for r in results if r["ok"]), "ok": ok, "results": results})


def add_common_project_version(p: argparse.ArgumentParser) -> None:
    p.add_argument("--project", required=True)
    p.add_argument("--version", required=True)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Minimal Black Duck agent skill CLI")
    parser.add_argument("--profile", help="Named durable credential profile")
    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("list-remediation-values", help="List documented remediation status, justification, and remediation values")
    p.set_defaults(func=cmd_list_remediation_values)

    p = sub.add_parser("list-projects", help="List/search Black Duck projects")
    p.add_argument("--query")
    p.add_argument("--exact", action="store_true")
    p.add_argument("--limit", type=int, default=50)
    p.set_defaults(func=cmd_list_projects)

    p = sub.add_parser("list-versions", help="List/search project versions")
    p.add_argument("--project", required=True)
    p.add_argument("--query")
    p.add_argument("--exact", action="store_true")
    p.add_argument("--limit", type=int, default=50)
    p.set_defaults(func=cmd_list_versions)

    p = sub.add_parser("list-licenses", help="List/search available Black Duck licenses")
    p.add_argument("--query", help="License name search")
    p.add_argument("--exact", action="store_true")
    p.add_argument("--limit", type=int, default=100)
    p.add_argument("--all", action="store_true", help="Return all matching licenses instead of stopping at --limit")
    p.set_defaults(func=cmd_list_licenses)

    p = sub.add_parser("list-components", help="List/search BOM components")
    add_common_project_version(p)
    p.add_argument("--query", "--name", dest="query", help="Component name search; --name is a friendly alias")
    p.add_argument("--exact", action="store_true")
    p.add_argument("--filter", action="append", help="Raw Black Duck API filter; repeatable")
    p.add_argument("--review-status", action="append", help="Client-side Review Status filter; repeatable")
    p.add_argument("--license-risk", action="append", help="Client-side License Risk filter (CRITICAL/HIGH/MEDIUM/LOW/OK/UNKNOWN); repeatable")
    p.add_argument("--operational-risk", action="append", help="Client-side Operational Risk filter (CRITICAL/HIGH/MEDIUM/LOW/OK/UNKNOWN); repeatable")
    p.add_argument("--security-risk", action="append", help="Client-side Security Risk filter (CRITICAL/HIGH/MEDIUM/LOW/OK/UNKNOWN); repeatable")
    p.add_argument("--policy-status", dest="policy_status")
    p.add_argument("--limit", type=int, default=50)
    p.add_argument("--all", action="store_true", help="Return all matching components instead of stopping at --limit")
    p.set_defaults(func=cmd_list_components)

    for name in ("list-vulnerabilities", "list-vulnerablities"):
        p = sub.add_parser(name, help="List/search vulnerabilities")
        add_common_project_version(p)
        p.add_argument("--severity", choices=["CRITICAL", "HIGH", "MEDIUM", "LOW"])
        p.add_argument("--status", choices=VALID_STATUSES)
        p.add_argument("--component", help="Component UUID or URL")
        p.add_argument("--query", help="Client-side text search over vulnerability JSON")
        p.add_argument("--filter", action="append", help="Raw Black Duck API filter; repeatable")
        p.add_argument("--limit", type=int)
        p.set_defaults(func=cmd_list_vulnerabilities)

    p = sub.add_parser("get-vulnerability-details", help="Get vulnerability details and affected components")
    add_common_project_version(p)
    p.add_argument("--vuln-id", required=True)
    p.add_argument("--related-id")
    p.set_defaults(func=cmd_get_vulnerability_details)

    p = sub.add_parser("get-code-location", help="Get code location evidence for a component")
    add_common_project_version(p)
    p.add_argument("--component", required=True, help="Component name, UUID, or URL")
    p.add_argument("--component-id", action="store_true", help="Treat --component as an ID/URL instead of a name")
    p.add_argument("--exact", action="store_true", help="Exact name match when not using --component-id")
    p.add_argument("--filter", action="append", help="Raw Black Duck API filter for BOM components; repeatable")
    p.add_argument("--limit", type=int, default=10)
    p.add_argument("--code-location-limit", type=int, default=25)
    p.add_argument("--matched-file-limit", type=int, default=25)
    p.set_defaults(func=cmd_get_code_location)

    p = sub.add_parser("get-matched-files", help="Get matched files for a component (fully paginated, with origins traversal)")
    add_common_project_version(p)
    p.add_argument("--component", required=True, help="Component name, UUID, or URL")
    p.add_argument("--component-id", action="store_true", help="Treat --component as an ID/URL instead of a name")
    p.add_argument("--exact", action="store_true", help="Exact name match when not using --component-id")
    p.add_argument("--filter", action="append", help="Raw Black Duck API filter for BOM components; repeatable")
    p.add_argument("--limit", type=int, default=10, help="Max matching BOM components")
    p.add_argument("--matched-file-limit", type=int, default=500, help="Max matched files per component (fully paginated)")
    p.set_defaults(func=cmd_get_matched_files)

    p = sub.add_parser("get-dependency-paths", help="Show dependency-graph resolution path for a component (requires BD 2021.2+)")
    add_common_project_version(p)
    p.add_argument("--component", required=True, help="Component name, UUID, or URL")
    p.add_argument("--component-id", action="store_true", help="Treat --component as an ID/URL instead of a name")
    p.add_argument("--exact", action="store_true", help="Exact name match when not using --component-id")
    p.add_argument("--filter", action="append", help="Raw Black Duck API filter for BOM components; repeatable")
    p.add_argument("--limit", type=int, default=100, help="Max dependency paths to return")
    p.set_defaults(func=cmd_get_dependency_paths)

    p = sub.add_parser("update-component", help="Update a BOM component's review status, license, and/or usage")
    add_common_project_version(p)
    p.add_argument("--component", required=True, help="Component name, UUID, or URL")
    p.add_argument("--component-id", action="store_true", help="Treat --component as an ID/URL instead of a name")
    p.add_argument("--exact", action="store_true", help="Exact name match when not using --component-id")
    p.add_argument("--filter", action="append", help="Raw Black Duck API filter for BOM components; repeatable")
    p.add_argument("--limit", type=int, default=10, help="Max matching BOM components to update")
    p.add_argument("--review-status", help="Review status to set, for example REVIEWED or NOT_REVIEWED")
    p.add_argument("--license", help="License name, UUID, or full /api/licenses/{id} URL to set")
    p.add_argument("--usage", action="append", help="Component usage to set; repeatable for multiple usages")
    p.add_argument("--comment", help="Free-text BOM component comment/note to set when supported by the Black Duck instance")
    p.set_defaults(func=cmd_update_component)

    p = sub.add_parser("update-vulnerability", help="Update vulnerability remediation status/justification only")
    add_common_project_version(p)
    p.add_argument("--vuln-id", required=True)
    p.add_argument("--related-id")
    p.add_argument("--status", required=True, choices=VALID_STATUSES)
    p.add_argument("--justification", choices=VALID_JUSTIFICATIONS, help="Status justification for NOT_AFFECTED/Known Not Affected")
    p.add_argument("--remediation", choices=VALID_REMEDIATIONS + list(VALID_REMEDIATION_ALIASES), help="Remediation option for AFFECTED/Known Affected")
    p.set_defaults(func=cmd_update_vulnerability)

    p = sub.add_parser("comment-vulnerability", help="Update vulnerability remediation comment only")
    add_common_project_version(p)
    p.add_argument("--vuln-id", required=True)
    p.add_argument("--related-id")
    p.add_argument("--comment", required=True)
    p.set_defaults(func=cmd_comment_vulnerability)
    return parser


def main(argv: Optional[List[str]] = None) -> None:
    args = build_parser().parse_args(argv)
    args.runtime_config = resolve_runtime_config(args.profile)
    args.func(args)


if __name__ == "__main__":
    main()
