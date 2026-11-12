#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = [
#   "requests>=2.28,<3",
#   "python-dotenv>=1.0,<2",
#   "keyring>=25,<26",
# ]
# ///
import argparse
import json
import os
import re
import sys
from pathlib import Path
from urllib.parse import quote, quote_plus, unquote, urlparse

try:
    import requests
except ImportError:
    print(json.dumps({"ok": False, "error": "Missing dependency: requests. Run via: uv run scripts/gitlab_cli.py ..."}))
    sys.exit(1)

def _load_dotenv():
    """Read legacy dotenv values without mutating the process environment."""
    try:
        from dotenv import dotenv_values
    except ImportError:
        return {}
    skill_env = script_skill_root / ".env"
    if not skill_env.is_file():
        return {}
    return {name: value for name, value in dotenv_values(skill_env).items() if value is not None}


try:
    import keyring
    from keyring.errors import KeyringError
except ImportError:
    keyring = None  # type: ignore[assignment]

    class KeyringError(Exception):
        pass

from typing import NamedTuple, Optional
from credential_config import ConfigError, active_profile, migrate_legacy, named_profile, validate_endpoint

script_skill_root = Path(__file__).resolve().parent.parent
_CREDENTIAL_NAMES = {"GITLAB_API_URL", "GITLAB_PERSONAL_ACCESS_TOKEN", "GITLAB_TOKEN_KEYRING_USER"}
_DIRECT_CREDENTIAL_NAMES = {"GITLAB_API_URL", "GITLAB_PERSONAL_ACCESS_TOKEN"}
_KEYRING_CREDENTIAL_NAMES = {"GITLAB_API_URL", "GITLAB_TOKEN_KEYRING_USER"}
_SECRET_CREDENTIAL_NAMES = {"GITLAB_PERSONAL_ACCESS_TOKEN", "GITLAB_TOKEN_KEYRING_USER"}


class RuntimeConfig(NamedTuple):
    base_url: str
    token_value: str
    token_keyring_user: str
    default_project_id: str
    allowed_project_ids: frozenset[str]
    read_only: bool
    timeout: int


def _project_ids(value):
    return {project_id.strip() for project_id in value.split(",") if project_id.strip()}


def _apply_profile_safety(settings, process_env, allowed_project_ids):
    profile_allowed = _project_ids(settings.get("allowed_project_ids", ""))
    if "GITLAB_ALLOWED_PROJECT_IDS" in process_env:
        requested = _project_ids(process_env["GITLAB_ALLOWED_PROJECT_IDS"])
        if profile_allowed and (not requested or not requested.issubset(profile_allowed)):
            out({"ok": False, "error_code": "GITLAB_SAFETY_OVERRIDE_REJECTED", "error": "GitLab project allowlist override would weaken the selected profile"}, 1)
        allowed_project_ids = requested
    read_only = settings.get("read_only_mode", "false") == "true" or process_env.get("GITLAB_READ_ONLY_MODE", "").lower() == "true"
    return allowed_project_ids, read_only


def resolve_runtime_config(profile_name: Optional[str] = None) -> RuntimeConfig:
    """Resolve GitLab configuration explicitly after argument parsing."""
    process_env = dict(os.environ)
    dotenv_env = _load_dotenv()

    def environment_value(name, fallback=""):
        return process_env.get(name, dotenv_env.get(name, fallback))

    overrides = {name for name in _CREDENTIAL_NAMES if process_env.get(name)}
    complete_direct = _DIRECT_CREDENTIAL_NAMES.issubset(overrides)
    complete_keyring = _KEYRING_CREDENTIAL_NAMES.issubset(overrides)
    if complete_direct and complete_keyring:
        out({"ok": False, "error_code": "GITLAB_CREDENTIAL_SOURCE_MISMATCH", "error": "Direct and keyring GitLab credentials are mutually exclusive"}, 1)
    if overrides and not (complete_direct or complete_keyring):
        out({"ok": False, "error_code": "GITLAB_CREDENTIAL_SOURCE_MISMATCH", "error": "Incoherent partial GitLab credential override"}, 1)
    active = None
    if not (complete_direct or complete_keyring):
        try:
            if keyring:
                migrate_legacy(script_skill_root, keyring.get_password)
            selected_name = profile_name or process_env.get("GITLAB_PROFILE")
            active = named_profile(selected_name) if selected_name else active_profile()
        except ConfigError as exc:
            out({"ok": False, "error": "Invalid durable GitLab profile", "details": str(exc)}, 1)

    profile = active[1] if active else {}
    settings = profile.get("settings", {})
    effective_values = {name for name in _CREDENTIAL_NAMES if environment_value(name)}
    orphan = (
        not profile
        and bool(effective_values & _SECRET_CREDENTIAL_NAMES)
        and "GITLAB_API_URL" not in effective_values
    )
    if orphan:
        out({"ok": False, "error_code": "GITLAB_CREDENTIAL_SOURCE_MISMATCH", "error": "Incoherent partial GitLab credential override"}, 1)

    using_profile = bool(profile and not (complete_direct or complete_keyring))
    if using_profile:
        base_url = profile["endpoint"].rstrip("/")
        token_value = ""
        token_keyring_user = profile["keyring_user"]
    else:
        base_url = environment_value("GITLAB_API_URL").rstrip("/")
        token_value = environment_value("GITLAB_PERSONAL_ACCESS_TOKEN")
        token_keyring_user = "" if complete_direct else environment_value("GITLAB_TOKEN_KEYRING_USER")

    def setting(environment_name, profile_name, fallback):
        if environment_name in process_env:
            return process_env[environment_name]
        if profile:
            return settings.get(profile_name, fallback)
        if complete_direct or complete_keyring:
            return fallback
        return environment_value(environment_name, fallback)

    default_project_id = setting("GITLAB_PROJECT_ID", "project_id", "")
    allowed = _project_ids(setting("GITLAB_ALLOWED_PROJECT_IDS", "allowed_project_ids", ""))
    read_only = setting("GITLAB_READ_ONLY_MODE", "read_only_mode", "false").lower() == "true"
    if using_profile:
        allowed, read_only = _apply_profile_safety(settings, process_env, allowed)
    try:
        timeout = int(setting("GITLAB_TIMEOUT", "timeout", "60"))
        if timeout <= 0:
            raise ValueError
    except (TypeError, ValueError):
        out({"ok": False, "error_code": "GITLAB_TIMEOUT_INVALID", "error": "GITLAB_TIMEOUT must be a positive integer"}, 1)
    try:
        base_url = validate_endpoint(base_url)
    except ConfigError as exc:
        out({"ok": False, "error_code": "GITLAB_ENDPOINT_UNSAFE", "error": str(exc)}, 1)
    return RuntimeConfig(base_url, token_value, token_keyring_user, default_project_id, frozenset(allowed), read_only, timeout)

WRITE_COMMANDS = {
    'merge_merge_request','create_or_update_file','create_repository','push_files','create_issue','create_merge_request',
    'fork_repository','create_branch','update_merge_request','set_mr_reviewers','set_mr_assignees',
    'create_note','create_merge_request_thread',
    'update_merge_request_note','create_merge_request_note','create_draft_note','update_draft_note','delete_draft_note',
    'publish_draft_note','bulk_publish_draft_notes','update_issue_note','create_issue_note','update_issue','delete_issue',
    'create_issue_link','delete_issue_link','create_label','update_label','delete_label','create_wiki_page',
    'update_wiki_page','delete_wiki_page','create_pipeline','retry_pipeline','cancel_pipeline','create_milestone',
    'edit_milestone','delete_milestone','promote_milestone','upload_markdown'
}

TOOL_MAP = {
    'search_repositories': ('GET', '/search', 'search GitLab projects'),
    'create_repository': ('POST', '/projects', 'create GitLab project'),
    'get_project': ('GET', '/projects/{project_id}', 'get project'),
    'list_projects': ('GET', '/projects', 'list projects'),
    'list_project_members': ('GET', '/projects/{project_id}/members/all', 'list project members'),
    'list_group_projects': ('GET', '/groups/{group_id}/projects', 'list group projects'),
    'fork_repository': ('POST', '/projects/{project_id}/fork', 'fork project'),
    'create_branch': ('POST', '/projects/{project_id}/repository/branches', 'create branch'),
    'get_repository_tree': ('GET', '/projects/{project_id}/repository/tree', 'get repository tree'),
    'get_file_contents': ('GET', '/projects/{project_id}/repository/files/{file_path}', 'get file contents'),
    'create_or_update_file': ('POST', '/projects/{project_id}/repository/files/{file_path}', 'create or update file'),
    'push_files': ('POST', '/projects/{project_id}/repository/commits', 'push multiple files'),
    'list_commits': ('GET', '/projects/{project_id}/repository/commits', 'list commits'),
    'get_commit': ('GET', '/projects/{project_id}/repository/commits/{commit_sha}', 'get commit'),
    'get_commit_diff': ('GET', '/projects/{project_id}/repository/commits/{commit_sha}/diff', 'get commit diff'),
    'list_merge_requests': ('GET', '/projects/{project_id}/merge_requests', 'list merge requests'),
    'get_merge_request': ('GET', '/projects/{project_id}/merge_requests/{merge_request_iid}', 'get merge request'),
    'get_merge_request_diffs': ('GET', '/projects/{project_id}/merge_requests/{merge_request_iid}/changes', 'get merge request diffs'),
    'list_merge_request_diffs': ('GET', '/projects/{project_id}/merge_requests/{merge_request_iid}/versions', 'list merge request diffs'),
    'create_merge_request': ('POST', '/projects/{project_id}/merge_requests', 'create merge request'),
    'update_merge_request': ('PUT', '/projects/{project_id}/merge_requests/{merge_request_iid}', 'update merge request'),
    'set_mr_reviewers': ('PUT', '/projects/{project_id}/merge_requests/{merge_request_iid}', 'set reviewers on a merge request (comma-separated reviewer_ids)'),
    'set_mr_assignees': ('PUT', '/projects/{project_id}/merge_requests/{merge_request_iid}', 'set assignees on a merge request (comma-separated assignee_ids)'),
    'merge_merge_request': ('PUT', '/projects/{project_id}/merge_requests/{merge_request_iid}/merge', 'merge merge request'),
    'mr_discussions': ('GET', '/projects/{project_id}/merge_requests/{merge_request_iid}/discussions', 'list mr discussions'),
    'create_merge_request_thread': ('POST', '/projects/{project_id}/merge_requests/{merge_request_iid}/discussions', 'create mr thread'),
    'create_merge_request_note': ('POST', '/projects/{project_id}/merge_requests/{merge_request_iid}/discussions/{discussion_id}/notes', 'create mr note'),
    'update_merge_request_note': ('PUT', '/projects/{project_id}/merge_requests/{merge_request_iid}/discussions/{discussion_id}/notes/{note_id}', 'update mr note'),
    'create_note': ('POST', '/projects/{project_id}/{note_target}/{target_id}/notes', 'create note'),
    'list_issues': ('GET', '/issues', 'list issues'),
    'my_issues': ('GET', '/issues', 'my issues'),
    'get_issue': ('GET', '/projects/{project_id}/issues/{issue_iid}', 'get issue'),
    'create_issue': ('POST', '/projects/{project_id}/issues', 'create issue'),
    'update_issue': ('PUT', '/projects/{project_id}/issues/{issue_iid}', 'update issue'),
    'delete_issue': ('DELETE', '/projects/{project_id}/issues/{issue_iid}', 'delete issue'),
    'list_issue_discussions': ('GET', '/projects/{project_id}/issues/{issue_iid}/discussions', 'list issue discussions'),
    'create_issue_note': ('POST', '/projects/{project_id}/issues/{issue_iid}/discussions/{discussion_id}/notes', 'create issue note'),
    'update_issue_note': ('PUT', '/projects/{project_id}/issues/{issue_iid}/discussions/{discussion_id}/notes/{note_id}', 'update issue note'),
    'list_issue_links': ('GET', '/projects/{project_id}/issues/{issue_iid}/links', 'list issue links'),
    'get_issue_link': ('GET', '/projects/{project_id}/issues/{issue_iid}/links/{issue_link_id}', 'get issue link'),
    'create_issue_link': ('POST', '/projects/{project_id}/issues/{issue_iid}/links', 'create issue link'),
    'delete_issue_link': ('DELETE', '/projects/{project_id}/issues/{issue_iid}/links/{issue_link_id}', 'delete issue link'),
    'list_namespaces': ('GET', '/namespaces', 'list namespaces'),
    'get_namespace': ('GET', '/namespaces/{namespace_id}', 'get namespace'),
    'verify_namespace': ('GET', '/namespaces/{namespace_id}', 'verify namespace'),
    'list_labels': ('GET', '/projects/{project_id}/labels', 'list labels'),
    'get_label': ('GET', '/projects/{project_id}/labels/{label_id}', 'get label'),
    'create_label': ('POST', '/projects/{project_id}/labels', 'create label'),
    'update_label': ('PUT', '/projects/{project_id}/labels/{label_id}', 'update label'),
    'delete_label': ('DELETE', '/projects/{project_id}/labels/{label_id}', 'delete label'),
    'list_wiki_pages': ('GET', '/projects/{project_id}/wikis', 'list wiki pages'),
    'get_wiki_page': ('GET', '/projects/{project_id}/wikis/{slug}', 'get wiki page'),
    'create_wiki_page': ('POST', '/projects/{project_id}/wikis', 'create wiki page'),
    'update_wiki_page': ('PUT', '/projects/{project_id}/wikis/{slug}', 'update wiki page'),
    'delete_wiki_page': ('DELETE', '/projects/{project_id}/wikis/{slug}', 'delete wiki page'),
    'list_pipelines': ('GET', '/projects/{project_id}/pipelines', 'list pipelines'),
    'get_pipeline': ('GET', '/projects/{project_id}/pipelines/{pipeline_id}', 'get pipeline'),
    'list_pipeline_jobs': ('GET', '/projects/{project_id}/pipelines/{pipeline_id}/jobs', 'list pipeline jobs'),
    'list_pipeline_trigger_jobs': ('GET', '/projects/{project_id}/pipelines/{pipeline_id}/bridges', 'list trigger jobs'),
    'get_pipeline_job': ('GET', '/projects/{project_id}/jobs/{job_id}', 'get pipeline job'),
    'get_pipeline_job_output': ('GET', '/projects/{project_id}/jobs/{job_id}/trace', 'get job output'),
    'create_pipeline': ('POST', '/projects/{project_id}/pipeline', 'create pipeline'),
    'retry_pipeline': ('POST', '/projects/{project_id}/pipelines/{pipeline_id}/retry', 'retry pipeline'),
    'cancel_pipeline': ('POST', '/projects/{project_id}/pipelines/{pipeline_id}/cancel', 'cancel pipeline'),
    'list_milestones': ('GET', '/projects/{project_id}/milestones', 'list milestones'),
    'get_milestone': ('GET', '/projects/{project_id}/milestones/{milestone_id}', 'get milestone'),
    'create_milestone': ('POST', '/projects/{project_id}/milestones', 'create milestone'),
    'edit_milestone': ('PUT', '/projects/{project_id}/milestones/{milestone_id}', 'edit milestone'),
    'delete_milestone': ('DELETE', '/projects/{project_id}/milestones/{milestone_id}', 'delete milestone'),
    'get_milestone_issue': ('GET', '/projects/{project_id}/milestones/{milestone_id}/issues', 'get milestone issues'),
    'get_milestone_merge_requests': ('GET', '/projects/{project_id}/milestones/{milestone_id}/merge_requests', 'get milestone merge requests'),
    'promote_milestone': ('POST', '/projects/{project_id}/milestones/{milestone_id}/promote', 'promote milestone'),
    'get_milestone_burndown_events': ('GET', '/projects/{project_id}/milestones/{milestone_id}/burndown_events', 'get milestone burndown'),
    'get_users': ('GET', '/users', 'get users'),
    'list_group_iterations': ('GET', '/groups/{group_id}/iterations', 'list group iterations'),
    'upload_markdown': ('POST', '/projects/{project_id}/uploads', 'upload markdown'),
    'download_attachment': ('GET', '/projects/{project_id}/uploads/{secret}/{filename}', 'download attachment'),
    'get_mr_pipelines': ('GET', '/projects/{project_id}/merge_requests/{merge_request_iid}/pipelines', 'list pipelines for an MR'),
    'get_mr_code_quality': ('GET', '/projects/{project_id}/merge_requests/{merge_request_iid}/codequality_mr_diff_reports', 'get code quality violations introduced by an MR (GitLab EE/Ultimate)'),
    'get_mr_code_quality_attachment_report': ('COMPOSITE', '', 'find and download the MR code-quality report from uploaded MR attachments'),
    'parse_mr_url': ('LOCAL', '', 'parse a GitLab MR URL into project_id and merge_request_iid'),
    'get_branch_diffs': ('GET', '/projects/{project_id}/repository/compare', 'get branch diffs'),
    'get_draft_note': ('GET', '/projects/{project_id}/merge_requests/{merge_request_iid}/draft_notes/{note_id}', 'get draft note'),
    'list_draft_notes': ('GET', '/projects/{project_id}/merge_requests/{merge_request_iid}/draft_notes', 'list draft notes'),
    'create_draft_note': ('POST', '/projects/{project_id}/merge_requests/{merge_request_iid}/draft_notes', 'create draft note'),
    'update_draft_note': ('PUT', '/projects/{project_id}/merge_requests/{merge_request_iid}/draft_notes/{note_id}', 'update draft note'),
    'delete_draft_note': ('DELETE', '/projects/{project_id}/merge_requests/{merge_request_iid}/draft_notes/{note_id}', 'delete draft note'),
    'publish_draft_note': ('POST', '/projects/{project_id}/merge_requests/{merge_request_iid}/draft_notes/{note_id}/publish', 'publish draft note'),
    'bulk_publish_draft_notes': ('POST', '/projects/{project_id}/merge_requests/{merge_request_iid}/draft_notes/bulk_publish', 'bulk publish draft notes')
}

ALIASES = {'mergeRequestIid': 'merge_request_iid', 'merge_request_iid': 'merge_request_iid', 'mergeRequestIID': 'merge_request_iid', 'issueIid': 'issue_iid', 'projectId': 'project_id', 'groupId': 'group_id', 'namespaceId': 'namespace_id', 'milestoneId': 'milestone_id', 'pipelineId': 'pipeline_id', 'jobId': 'job_id', 'noteId': 'note_id', 'discussionId': 'discussion_id', 'issueLinkId': 'issue_link_id', 'targetId': 'target_id', 'noteTarget': 'note_target', 'commitSha': 'commit_sha', 'filePath': 'file_path'}


def parse_mr_url_local(params, runtime):
    """Parse a GitLab MR URL locally — no auth or HTTP required."""
    raw = (params.get('url') or '').strip()
    if not raw:
        out({"ok": False, "error": "parse_mr_url requires --param url=<MR URL>"}, 1)

    parsed = urlparse(raw)
    host = parsed.netloc
    path = parsed.path.rstrip('/')

    # Strip common view suffixes that appear after the IID
    _VIEW_SUFFIXES = ('/diffs', '/commits', '/pipelines', '/changes',
                      '/dependencies', '/metrics', '/reports')
    for sfx in _VIEW_SUFFIXES:
        if path.endswith(sfx):
            path = path[: -len(sfx)]
            break

    sep = '/-/merge_requests/'
    if sep not in path:
        out({"ok": False, "error": f"URL does not contain '/-/merge_requests/': {raw!r}"}, 1)

    project_path, _, rest = path.partition(sep)
    project_path = project_path.lstrip('/')

    iid_str = rest.split('/')[0]
    if not iid_str.isdigit():
        out({"ok": False, "error": f"Cannot parse merge request IID from URL: {raw!r}"}, 1)

    project_id = quote(project_path, safe='')

    result = {
        "host": host,
        "project_path": project_path,
        "project_id": project_id,
        "merge_request_iid": iid_str,
    }

    configured_host = urlparse(runtime.base_url).netloc
    if configured_host and host != configured_host:
        result["warning"] = (
            f"URL host '{host}' differs from configured GITLAB_API_URL host "
            f"'{configured_host}'. Subsequent API calls will use the configured URL."
        )

    out({"ok": True, "data": result})


def out(obj, code=0):
    print(json.dumps(obj, ensure_ascii=False, indent=2))
    sys.exit(code)


def canonicalize(params):
    result = {}
    for k, v in params.items():
        key = ALIASES.get(k, k)
        result[key] = v
    return result


def credential_store_secret(service, username):
    if not keyring:
        out({"ok": False, "error": "keyring is not installed; set GITLAB_PERSONAL_ACCESS_TOKEN or run with uv so keyring is available"}, 1)
    try:
        secret = keyring.get_password(service, username)
    except KeyringError as exc:
        out({
            "ok": False,
            "error_code": "GITLAB_KEYRING_BACKEND_FAILURE",
            "error": "GitLab keyring backend could not read the selected entry",
            "keyring_user": username,
            "details": str(exc),
        }, 1)
    if not secret:
        out({
            "ok": False,
            "error_code": "GITLAB_KEYRING_ENTRY_MISSING",
            "error": "Selected GitLab keyring entry has no token",
            "keyring_user": username,
        }, 1)
    return secret


def token(runtime):
    if runtime.token_keyring_user:
        return credential_store_secret('AgentDevelopmentToolkit:gitlab', runtime.token_keyring_user)
    return runtime.token_value


def require_token(runtime):
    auth_token = token(runtime)
    if not auth_token:
        out({"ok": False, "error": "Missing GITLAB_PERSONAL_ACCESS_TOKEN or GITLAB_TOKEN_KEYRING_USER"}, 1)
    return auth_token


def check_write(tool, runtime):
    if runtime.read_only and tool in WRITE_COMMANDS:
        out({"ok": False, "error": f"Tool '{tool}' blocked by GITLAB_READ_ONLY_MODE"}, 1)


def resolve_project(project_id, runtime):
    pid = str(project_id or runtime.default_project_id or '').strip()
    if not pid:
        return ''
    if runtime.allowed_project_ids and pid not in runtime.allowed_project_ids:
        out({"ok": False, "error": f"Project {pid} not in GITLAB_ALLOWED_PROJECT_IDS"}, 1)
    return pid


def headers(auth_token, extra=None):
    h = {'PRIVATE-TOKEN': auth_token, 'Accept': 'application/json'}
    if extra:
        h.update(extra)
    return h


def fill_path(path, params):
    used = set()
    for key in ['project_id','group_id','namespace_id','merge_request_iid','issue_iid','milestone_id','pipeline_id','job_id','note_id','discussion_id','issue_link_id','target_id','note_target','commit_sha','file_path','slug','secret','filename','label_id']:
        token = '{' + key + '}'
        if token in path:
            val = params.get(key)
            if val in [None, '']:
                out({"ok": False, "error": f"Missing required parameter: {key}"}, 1)
            path = path.replace(token, quote_plus(str(val), safe=''))
            used.add(key)
    return path, used


def _api_project_id(project_id):
    return quote(unquote(str(project_id)), safe='')


def _extract_upload_links(markdown):
    """Return uploaded attachment links from GitLab markdown/note text."""
    if not markdown:
        return []
    results = []
    seen = set()

    # Handles relative links like /uploads/<secret>/<filename>, project-qualified
    # links like /group/project/uploads/<secret>/<filename>, and absolute URLs.
    upload_re = re.compile(r'(?P<url>(?:https?://[^\s\)\]"\']*?)?(?:/[^\s\)\]"\']*?)?/uploads/(?P<secret>[0-9a-fA-F]{32})/(?P<filename>[^\s\)\]"\']+))')
    for match in upload_re.finditer(markdown):
        secret = match.group('secret')
        filename = match.group('filename')
        key = (secret, filename)
        if key in seen:
            continue
        seen.add(key)
        results.append({"url": match.group('url'), "secret": secret, "filename": filename})
    return results


def _get_all_mr_discussions(project_id, merge_request_iid, runtime, auth_token):
    discussions_url = f"{runtime.base_url}/projects/{_api_project_id(project_id)}/merge_requests/{quote_plus(str(merge_request_iid), safe='')}/discussions"
    discussions = []
    page = 1

    while page:
        resp = requests.get(
            discussions_url,
            headers=headers(auth_token),
            params={"per_page": 100, "page": page},
            timeout=runtime.timeout,
            allow_redirects=False,
        )
        try:
            page_body = resp.json()
        except Exception:
            page_body = {"raw": resp.text}
        if not resp.ok:
            out({"ok": False, "status": resp.status_code, "tool": "get_mr_code_quality_attachment_report", "url": discussions_url, "response": page_body}, 1)
        if not isinstance(page_body, list):
            out({
                "ok": False,
                "status": resp.status_code,
                "tool": "get_mr_code_quality_attachment_report",
                "url": discussions_url,
                "error": "Unexpected discussions response shape",
                "details": "Expected a JSON array of discussions",
                "response": page_body,
            }, 1)
        discussions.extend(page_body)
        page = resp.headers.get('X-Next-Page') or ''

    return discussions_url, discussions


def get_mr_code_quality_attachment_report(params, runtime):
    """Find and download the MR code-quality report uploaded as an MR attachment."""
    auth_token = require_token(runtime)
    params = canonicalize(params)
    project_id = resolve_project(params.get('project_id'), runtime)
    merge_request_iid = params.get('merge_request_iid')
    if not project_id:
        out({"ok": False, "error": "Missing required parameter: project_id"}, 1)
    if not merge_request_iid:
        out({"ok": False, "error": "Missing required parameter: merge_request_iid"}, 1)

    filename_regex = params.get('filename_regex') or r'(?i)(code[-_ ]?quality|codequality|gl-code-quality-report|quality).*\.(json|md|txt|html)$'
    text_regex = params.get('text_regex') or r'(?i)(code[-_ ]?quality|codequality|gl-code-quality-report|quality report)'
    try:
        compiled_filename = re.compile(filename_regex)
    except re.error as exc:
        out({"ok": False, "error": "Invalid filename_regex", "details": str(exc)}, 1)
    try:
        compiled_text = re.compile(text_regex)
    except re.error as exc:
        out({"ok": False, "error": "Invalid text_regex", "details": str(exc)}, 1)

    discussions_url, discussions = _get_all_mr_discussions(project_id, merge_request_iid, runtime, auth_token)

    candidates = []
    for discussion in discussions:
        for note in discussion.get('notes', []):
            body = note.get('body') or ''
            for link in _extract_upload_links(body):
                filename = link['filename']
                if compiled_filename.search(filename) or compiled_text.search(body):
                    candidates.append({
                        **link,
                        "discussion_id": discussion.get('id'),
                        "note_id": note.get('id'),
                        "created_at": note.get('created_at'),
                        "note_excerpt": body[:500],
                    })

    if not candidates:
        out({
            "ok": False,
            "status": 404,
            "tool": "get_mr_code_quality_attachment_report",
            "error": "No matching code-quality attachment found in MR discussions",
            "searched": {"filename_regex": filename_regex, "text_regex": text_regex},
            "discussions_url": discussions_url,
        }, 1)

    # Prefer the latest matching upload because bots commonly attach a fresh report
    # on every pipeline run. created_at is ISO-ish and sorts lexicographically.
    candidates.sort(key=lambda c: c.get('created_at') or '')
    selected = candidates[-1]
    download_url = f"{runtime.base_url}/projects/{_api_project_id(project_id)}/uploads/{selected['secret']}/{quote(str(selected['filename']), safe='')}"
    try:
        max_report_bytes = int(params.get('max_report_bytes') or 5 * 1024 * 1024)
        if max_report_bytes <= 0:
            raise ValueError("must be positive")
    except (TypeError, ValueError):
        out({
            "ok": False,
            "tool": "get_mr_code_quality_attachment_report",
            "error": "Invalid max_report_bytes",
            "details": "Expected a positive integer byte limit",
        }, 1)
    download_resp = requests.get(download_url, headers=headers(auth_token), timeout=runtime.timeout, allow_redirects=False)
    content_length = download_resp.headers.get('content-length')
    if content_length and int(content_length) > max_report_bytes:
        out({
            "ok": False,
            "status": download_resp.status_code,
            "tool": "get_mr_code_quality_attachment_report",
            "download_url": download_url,
            "selected": selected,
            "error": "Code-quality attachment exceeds max_report_bytes",
            "content_length": int(content_length),
            "max_report_bytes": max_report_bytes,
        }, 1)
    content_type = download_resp.headers.get('content-type', '')
    content = download_resp.text if 'text' in content_type or 'json' in content_type else download_resp.content.decode('utf-8', errors='replace')
    if len(content.encode('utf-8')) > max_report_bytes:
        out({
            "ok": False,
            "status": download_resp.status_code,
            "tool": "get_mr_code_quality_attachment_report",
            "download_url": download_url,
            "selected": selected,
            "error": "Code-quality attachment exceeds max_report_bytes",
            "content_length": len(content.encode('utf-8')),
            "max_report_bytes": max_report_bytes,
        }, 1)
    parsed = None
    if 'json' in content_type or selected['filename'].lower().endswith('.json'):
        try:
            parsed = json.loads(content)
        except Exception:
            parsed = None

    out({
        "ok": download_resp.ok,
        "status": download_resp.status_code,
        "tool": "get_mr_code_quality_attachment_report",
        "description": TOOL_MAP['get_mr_code_quality_attachment_report'][2],
        "discussions_url": discussions_url,
        "download_url": download_url,
        "selected": selected,
        "candidate_count": len(candidates),
        "content_type": content_type,
        "report": parsed if parsed is not None else content,
    }, 0 if download_resp.ok else 1)


def request(tool, params, raw_body=None, *, runtime):
    method, path_tmpl, desc = TOOL_MAP[tool]
    if method == 'LOCAL':
        out({"ok": False, "error": f"Tool '{tool}' is local-only and should be handled before request()"}, 1)
    params = canonicalize(params)
    project_scoped = '{project_id}' in path_tmpl
    if runtime.allowed_project_ids and not project_scoped:
        out({
            "ok": False,
            "error_code": "GITLAB_PROJECT_SCOPE_REQUIRED",
            "error": f"Tool '{tool}' is unavailable when GITLAB_ALLOWED_PROJECT_IDS is configured",
        }, 1)
    check_write(tool, runtime)
    if project_scoped:
        params['project_id'] = resolve_project(params.get('project_id'), runtime)
    auth_token = require_token(runtime)
    path, used = fill_path(path_tmpl, params)
    url = runtime.base_url + path
    remaining = {k: v for k, v in params.items() if k not in used and v is not None}

    if tool == 'search_repositories':
        remaining.setdefault('scope', 'projects')
    if tool == 'my_issues':
        remaining.setdefault('scope', 'assigned_to_me')
        remaining.setdefault('state', 'opened')
    if tool == 'get_file_contents' and 'ref' not in remaining:
        remaining['ref'] = params.get('ref', 'main')
    if tool == 'get_branch_diffs':
        remaining = {'from': params.get('from'), 'to': params.get('to'), 'straight': params.get('straight', 'false')}
    if tool == 'create_or_update_file':
        method = 'PUT' if params.get('update', 'true').lower() == 'true' else 'POST'
        remaining = {k: v for k, v in remaining.items() if k not in {'update'}}
    if tool == 'download_attachment':
        resp = requests.get(url, headers=headers(auth_token), timeout=runtime.timeout, allow_redirects=False)
        content = resp.text if 'text' in resp.headers.get('content-type','') else resp.content.decode('utf-8', errors='replace')
        out({"ok": resp.ok, "status": resp.status_code, "tool": tool, "description": desc, "url": url, "content": content})

    # Coerce reviewer_ids / assignee_ids from a scalar or comma-separated string into
    # a list of ints.  GitLab silently ignores these fields when they are strings.
    for id_field in ('reviewer_ids', 'assignee_ids'):
        if id_field in remaining:
            raw_ids = remaining[id_field]
            if isinstance(raw_ids, str):
                raw_ids = [i.strip() for i in raw_ids.split(',') if i.strip()]
            elif not isinstance(raw_ids, list):
                raw_ids = [raw_ids]
            remaining[id_field] = [int(i) for i in raw_ids]

    # For set_mr_reviewers / set_mr_assignees keep only the relevant id field
    # so we don't accidentally clobber other MR fields.
    if tool == 'set_mr_reviewers':
        remaining = {'reviewer_ids': remaining.get('reviewer_ids', [])}
    elif tool == 'set_mr_assignees':
        remaining = {'assignee_ids': remaining.get('assignee_ids', [])}

    data = None
    files = None
    req_headers = headers(auth_token)

    if tool == 'upload_markdown':
        file_path = params.get('upload_file')
        if not file_path or not os.path.exists(file_path):
            out({"ok": False, "error": "upload_markdown requires existing --param upload_file=/path/to/file"}, 1)
        files = {'file': open(file_path, 'rb')}
        req_headers = {'PRIVATE-TOKEN': auth_token}
    elif method in {'POST', 'PUT', 'PATCH', 'DELETE'}:
        data = raw_body if raw_body is not None else remaining
    
    try:
        resp = requests.request(method, url, headers=req_headers, params=None if data is not None and method in {'POST','PUT','PATCH','DELETE'} else remaining, json=data if files is None else None, files=files, timeout=runtime.timeout, allow_redirects=False)
    finally:
        if files:
            files['file'].close()

    content_type = resp.headers.get('content-type', '')
    try:
        body = resp.json() if 'json' in content_type else {'raw': resp.text}
    except Exception:
        body = {'raw': resp.text}

    def sanitize(value):
        if isinstance(value, dict):
            blocked = {'token', 'private_token', 'access_token', 'password', 'secret'}
            return {key: sanitize(item) for key, item in value.items() if key.lower() not in blocked}
        if isinstance(value, list):
            return [sanitize(item) for item in value]
        return value

    payload = {"ok": resp.ok, "status": resp.status_code, "tool": tool, "description": desc, "url": url, "response": sanitize(body)}
    if resp.status_code == 401:
        payload.update({"error_code": "GITLAB_REMOTE_AUTHENTICATION_FAILED", "error": "GitLab authentication failed"})
    elif resp.status_code == 403:
        payload.update({"error_code": "GITLAB_REMOTE_AUTHORIZATION_FAILED", "error": "GitLab authorization failed"})
    out(payload, 0 if resp.ok else 1)


def main():
    parser = argparse.ArgumentParser(description='GitLab CLI replacement for MCP server')
    parser.add_argument('--profile', help='Named durable credential profile')
    parser.add_argument('tool', nargs='?', choices=sorted(TOOL_MAP.keys()))
    parser.add_argument('--param', action='append', default=[], help='key=value parameter; repeatable')
    parser.add_argument('--body-file', help='JSON file with request body, optional')
    parser.add_argument('--list-tools', action='store_true', help='List available tools and exit')
    args = parser.parse_args()

    if args.list_tools:
        out({"ok": True, "tools": sorted(TOOL_MAP.keys())})

    if not args.tool:
        parser.error("the following arguments are required: tool (unless --list-tools is used)")

    runtime = resolve_runtime_config(args.profile)
    params = {}
    for item in args.param:
        if '=' not in item:
            out({"ok": False, "error": f"Invalid --param '{item}', expected key=value"}, 1)
        k, v = item.split('=', 1)
        params[k] = v

    # Dispatch LOCAL/COMPOSITE tools before the generic one-request plumbing.
    if TOOL_MAP[args.tool][0] == 'LOCAL':
        if args.tool == 'parse_mr_url':
            parse_mr_url_local(params, runtime)
        out({"ok": False, "error": f"No local handler for tool '{args.tool}'"}, 1)
    if TOOL_MAP[args.tool][0] == 'COMPOSITE':
        if args.tool == 'get_mr_code_quality_attachment_report':
            get_mr_code_quality_attachment_report(params, runtime)
        out({"ok": False, "error": f"No composite handler for tool '{args.tool}'"}, 1)

    raw_body = None
    if args.body_file:
        with open(args.body_file, 'r', encoding='utf-8') as f:
            raw_body = json.load(f)

    request(args.tool, params, raw_body, runtime=runtime)


if __name__ == '__main__':
    main()
