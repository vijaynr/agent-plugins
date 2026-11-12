#!/usr/bin/env python3
# /// script
# requires-python = ">=3.9"
# dependencies = []
# ///
"""
Parse an ALM Octane UI URL and delegate to octane_client.py.

URL format:
  https://<host>/ui/entity-navigation?p=<shared_space>/<workspace>&entityType=<type>&id=<id>

Examples:
  uv run scripts/octane_url.py "https://octane.example.com/ui/entity-navigation?p=1001/1002&entityType=work_item&id=42"
  uv run scripts/octane_url.py --action update-defect --phase phase.defect.fixed "https://...&id=1013024"
  uv run scripts/octane_url.py URL1 URL2 URL3          # batch fetch
"""

import os
import re
import sys
import json
import subprocess
from pathlib import Path
from urllib.parse import urlparse, parse_qs
from typing import Any, Dict, List, Optional

SCRIPT_DIR = Path(__file__).resolve().parent
_SCRIPT_SKILL_ROOT = SCRIPT_DIR.parent
CLIENT_SCRIPT = SCRIPT_DIR / "octane_client.py"

# Entity-type in the URL → octane_client.py subcommand for fetching
_FETCH_COMMANDS = {
    "favorite":  "list-favorite-items",
    "work_item": "get-work-item",
    "defect":    "get-defect",
    "story":     "get-story",
    "feature":   "get-feature",
    "test":      "get-manual-test",
}

# Allowed actions the user can request (beyond plain fetch)
_ACTIONS = {
    "get-favorite", "list-favorite-items",
    "get-work-item", "get-defect", "get-story", "get-feature", "get-manual-test",
    "create-story-under-feature", "get-story-parent-feature", "list-feature-items",
    "update-feature", "update-feature-security", "update-defect", "update-story", "update-story-status",
    "delete-backlog-item", "create-comment", "read-comment", "add-attachment", "list-attachments", "delete-attachment",
    "list-tasks", "add-task", "add-tag",
}


def fail(msg: str, **extra: Any) -> None:
    payload: Dict[str, Any] = {"ok": False, "error": msg}
    payload.update(extra)
    print(json.dumps(payload, ensure_ascii=False))
    sys.exit(1)


def parse_octane_url(url: str) -> Dict[str, str]:
    """
    Decompose an Octane UI URL into its components.

    Returns dict with keys:
        base_url, shared_space_id, workspace_id, entity_type, entity_id
    """
    parsed = urlparse(url)
    if not parsed.scheme or not parsed.hostname:
        fail("Invalid URL — expected https://<host>/ui/entity-navigation?...", url=url)

    base_url = f"{parsed.scheme}://{parsed.netloc}"

    qs = parse_qs(parsed.query)

    # --- p=<shared_space>/<workspace> ---
    p_values = qs.get("p", [])
    if not p_values:
        fail("Missing 'p' query parameter (shared_space/workspace)", url=url)
    p = p_values[0]
    if "/" not in p:
        fail("'p' parameter must be <shared_space_id>/<workspace_id>", url=url, p=p)
    shared_space_id, workspace_id = p.split("/", 1)

    if parsed.path.startswith("/ui/favorites/"):
        match = re.fullmatch(r"/ui/favorites/([0-9]+)/?", parsed.path)
        if not match or not re.fullmatch(r"[0-9]+/[0-9]+", p) or len(p_values) != 1 or "id" in qs or "entityType" in qs:
            fail("Invalid or ambiguous favorite URL; expected /ui/favorites/<numeric-id>?p=<space>/<workspace>")
        return {"base_url": base_url, "shared_space_id": shared_space_id,
            "workspace_id": workspace_id, "entity_type": "favorite", "entity_id": match.group(1)}

    # --- entityType ---
    entity_type = qs.get("entityType", ["work_item"])[0]

    # --- id ---
    entity_ids = qs.get("id", [])
    if not entity_ids:
        fail("Missing 'id' query parameter", url=url)
    entity_id = entity_ids[0]

    return {
        "base_url": base_url,
        "shared_space_id": shared_space_id,
        "workspace_id": workspace_id,
        "entity_type": entity_type,
        "entity_id": entity_id,
    }


def build_client_cmd(
    parts: Dict[str, str],
    action: Optional[str],
    extra_args: List[str],
    profile: Optional[str] = None,
) -> List[str]:
    """Build the full octane_client.py command list."""
    favorite_actions = {"get-favorite", "list-favorite-items"}
    if parts["entity_type"] == "favorite":
        if action and action not in favorite_actions:
            fail("Favorite URLs support only read-only favorite actions")
    elif action in favorite_actions:
        fail("Favorite actions require a favorite URL")
    # Decide which subcommand to run
    if action:
        subcommand = action
    else:
        subcommand = _FETCH_COMMANDS.get(parts["entity_type"], "get-defect")

    cmd = ["uv", "run", str(CLIENT_SCRIPT)]
    if profile:
        cmd += ["--profile", profile]
    cmd.append(subcommand)

    # All octane_client.py commands use a uniform --entity-id flag.
    cmd += ["--entity-id", parts["entity_id"]]

    # Workspace / shared-space from the URL (overrides .env defaults)
    cmd += [
        "--workspace-id", parts["workspace_id"],
        "--shared-space-id", parts["shared_space_id"],
    ]

    # Pass OCTANE_BASE_URL from the URL into the child process env
    # (handled in run_client_cmd)

    # Append any extra flags the user supplied (e.g. --phase, --severity, --text)
    cmd += extra_args

    return cmd


def run_client_cmd(cmd: List[str], base_url: str) -> Dict[str, Any]:
    """Run octane_client.py without pairing credentials with an untrusted URL host."""
    if urlparse(base_url).scheme.lower() != "https":
        return {"ok": False, "error_code": "OCTANE_URL_ENDPOINT_UNSAFE", "error": "Octane URL delegation requires HTTPS"}

    env = os.environ.copy()
    credential_override = any(env.get(name) for name in (
        "OCTANE_CLIENT_ID", "OCTANE_CLIENT_SECRET", "OCTANE_CLIENT_SECRET_KEYRING_USER"
    ))
    configured_endpoint = env.get("OCTANE_BASE_URL", "").rstrip("/")
    if credential_override and configured_endpoint != base_url.rstrip("/"):
        return {
            "ok": False,
            "error_code": "OCTANE_CREDENTIAL_SOURCE_MISMATCH",
            "error": "URL endpoint does not match the configured Octane credential endpoint",
        }
    env["OCTANE_BASE_URL"] = base_url

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, env=env)
    except FileNotFoundError:
        return {"ok": False, "error": "uv is required and must be installed on PATH"}
    output = result.stdout.strip() or result.stderr.strip()

    try:
        return json.loads(output)
    except json.JSONDecodeError:
        return {"ok": False, "error": "Unexpected output from octane_client.py", "raw": output}


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(
        description="Parse Octane UI URLs and delegate to octane_client.py",
    )
    parser.add_argument(
        "urls", nargs="+", metavar="URL",
        help="One or more Octane UI URLs",
    )
    parser.add_argument(
        "--profile", default=None,
        help="Named durable credential profile to forward to octane_client.py",
    )
    parser.add_argument(
        "--action", default=None, choices=sorted(_ACTIONS),
        help="Override the default fetch action (e.g. update-feature, update-story, list-feature-items, create-story-under-feature, update-defect, delete-backlog-item, delete-attachment, add-tag, add-attachment)",
    )
    parser.add_argument(
        "--phase", default=None,
        help="Phase ID for update-defect / update-story-status",
    )
    parser.add_argument(
        "--severity", default=None,
        help="Severity list_node ID for update-defect",
    )
    parser.add_argument(
        "--security-assessment", default=None,
        help="Value for update-feature-security Security Assessment field (security_assessment_udf)",
    )
    parser.add_argument(
        "--security-impact-level", default=None,
        help="Value or list_node ID for update-feature-security Security Impact field (security_impact_f_udf)",
    )
    parser.add_argument(
        "--text", default=None,
        help="Comment text for create-comment",
    )
    parser.add_argument(
        "--description", default=None,
        help="Description for update-feature/create-story-under-feature, or attachment description for add-attachment",
    )
    parser.add_argument(
        "--acceptance-criteria", action="append", default=None,
        help="Acceptance criterion for create-story-under-feature; repeat for multiple criteria",
    )
    parser.add_argument(
        "--priority", default=None,
        help="Priority list_node ID for create-story-under-feature",
    )
    parser.add_argument("--fields", default=None, help="Comma-separated item fields for list-favorite-items")
    parser.add_argument("--page-size", type=int, default=None, help="Page size for list-favorite-items")
    parser.add_argument("--max-items", type=int, default=None, help="Safety cap for list-favorite-items")
    parser.add_argument(
        "--limit", type=int, default=None,
        help="Limit for list-feature-items",
    )
    parser.add_argument(
        "--name", default=None,
        help="Feature/task/story name, or attachment name for add-attachment",
    )
    parser.add_argument(
        "--owner-id", default=None,
        help="Workspace user ID for add-task",
    )
    parser.add_argument(
        "--item-type", default=None,
        help="Task type list_node ID for add-task",
    )
    parser.add_argument(
        "--estimated-hours", type=float, default=None,
        help="Estimated hours for add-task",
    )
    parser.add_argument(
        "--tag", default=None,
        help="Tag name for add-tag",
    )
    parser.add_argument(
        "--no-create", action="store_true",
        help="For add-tag: fail if the tag does not already exist",
    )
    parser.add_argument(
        "--file", dest="file_path", default=None,
        help="File path for add-attachment",
    )
    parser.add_argument(
        "--attachment-id", default=None,
        help="Attachment ID for delete-attachment",
    )
    parser.add_argument(
        "--attachment-name", default=None,
        help="Exact attachment name for delete-attachment",
    )
    parser.add_argument(
        "--owner-field", default=None,
        help="Attachment owner field for add-attachment/list-attachments, default owner_work_item",
    )
    parser.add_argument(
        "--owner-type", default=None,
        help="Attachment owner entity type for add-attachment, default work_item",
    )
    parser.add_argument(
        "--entity-type", default=None, dest="comment_entity_type",
        help="Entity type for create-comment or delete-backlog-item (e.g. work_item, defect, story)",
    )
    parser.add_argument(
        "--parse-only", action="store_true",
        help="Only decompose the URL(s) — don't call octane_client.py",
    )

    args = parser.parse_args()

    # Build extra flags from optional args
    extra_args: List[str] = []
    for flag in ("fields", "page_size", "max_items"):
        value = getattr(args, flag)
        if value is not None:
            extra_args += ["--" + flag.replace("_", "-"), str(value)]
    if args.phase:
        extra_args += ["--phase", args.phase]
    if args.severity:
        extra_args += ["--severity", args.severity]
    if args.security_assessment:
        extra_args += ["--security-assessment", args.security_assessment]
    if args.security_impact_level:
        extra_args += ["--security-impact-level", args.security_impact_level]
    if args.text:
        extra_args += ["--text", args.text]
    if args.description:
        extra_args += ["--description", args.description]
    if args.acceptance_criteria:
        for criterion in args.acceptance_criteria:
            extra_args += ["--acceptance-criteria", criterion]
    if args.priority:
        extra_args += ["--priority", args.priority]
    if args.limit is not None:
        extra_args += ["--limit", str(args.limit)]
    if args.name:
        extra_args += ["--name", args.name]
    if args.owner_id:
        extra_args += ["--owner-id", args.owner_id]
    if args.item_type:
        extra_args += ["--item-type", args.item_type]
    if args.estimated_hours is not None:
        extra_args += ["--estimated-hours", str(args.estimated_hours)]
    if args.tag:
        extra_args += ["--tag", args.tag]
    if args.no_create:
        extra_args += ["--no-create"]
    if args.file_path:
        extra_args += ["--file", args.file_path]
    if args.attachment_id:
        extra_args += ["--attachment-id", args.attachment_id]
    if args.attachment_name:
        extra_args += ["--attachment-name", args.attachment_name]
    if args.owner_field:
        extra_args += ["--owner-field", args.owner_field]
    if args.owner_type:
        extra_args += ["--owner-type", args.owner_type]
    if args.comment_entity_type:
        extra_args += ["--entity-type", args.comment_entity_type]

    results: List[Dict[str, Any]] = []

    for url in args.urls:
        parts = parse_octane_url(url)

        if args.parse_only:
            results.append({"ok": True, "parsed": parts, "url": url})
            continue

        per_url_extra_args = list(extra_args)
        if args.action == "delete-backlog-item" and not args.comment_entity_type:
            per_url_extra_args += ["--entity-type", parts["entity_type"]]

        cmd = build_client_cmd(parts, args.action, per_url_extra_args, args.profile)
        resp = run_client_cmd(cmd, parts["base_url"])
        results.append({
            "url": url,
            "parsed": parts,
            "result": resp,
        })

    # Single URL → flat output; multiple → array
    output = results[0] if len(results) == 1 else results
    print(json.dumps(output, ensure_ascii=False, indent=2))
    if any(not entry.get("ok", entry.get("result", {}).get("ok", False)) for entry in results):
        raise SystemExit(1)


if __name__ == "__main__":
    main()
