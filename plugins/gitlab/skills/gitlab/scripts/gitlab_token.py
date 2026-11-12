#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = [
#   "keyring>=25,<26",
# ]
# ///
"""Manage GitLab personal access tokens in the OS credential store.

Secrets are stored under service name ``AgentDevelopmentToolkit:gitlab``. The username is referenced by non-secret durable profile metadata and is
normally the matching GitLab API URL.
"""
from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

from credential_config import (
    ConfigError, default_profile, document_with_profile, profile_lock,
    read_document, remove_profile, restore, select_profile, snapshot, validate_endpoint, write_document,
)

SERVICE_NAME = "AgentDevelopmentToolkit:gitlab"
VERIFICATION_TIMEOUT_SECONDS = 120
SKILL_ROOT = Path(__file__).resolve().parent.parent
ENV_FILE = SKILL_ROOT / ".env"
ENV_EXAMPLE_FILE = SKILL_ROOT / ".env.example"


def keyring_module():
    try:
        import keyring
        from keyring.errors import KeyringError, PasswordDeleteError
    except ImportError:
        print("Error: missing dependency 'keyring'. Run with: uv run scripts/gitlab_token.py ...", file=sys.stderr)
        raise SystemExit(1)
    return keyring, KeyringError, PasswordDeleteError


def save_token(username: str, token: str) -> int:
    keyring, KeyringError, _ = keyring_module()
    try:
        keyring.set_password(SERVICE_NAME, username, token)
    except KeyringError as exc:
        print(f"Error: failed to save GitLab token: {exc}", file=sys.stderr)
        return 1
    print(f"Success: GitLab token saved for {username}.")
    return 0


def get_token(username: str, show: bool = False) -> int:
    keyring, KeyringError, _ = keyring_module()
    try:
        token = keyring.get_password(SERVICE_NAME, username)
    except KeyringError as exc:
        print(f"Error: failed to retrieve GitLab token: {exc}", file=sys.stderr)
        return 1
    if token:
        print("Success: GitLab token retrieved.")
        if show:
            print(token)
        return 0
    print("Error: No GitLab token found for this user.", file=sys.stderr)
    return 1


def delete_token(username: str) -> int:
    keyring, KeyringError, PasswordDeleteError = keyring_module()
    try:
        keyring.delete_password(SERVICE_NAME, username)
    except PasswordDeleteError:
        print("Error: GitLab token not found.", file=sys.stderr)
        return 1
    except KeyringError as exc:
        print(f"Error: failed to delete GitLab token: {exc}", file=sys.stderr)
        return 1
    print(f"Success: GitLab token deleted for {username}.")
    return 0


def token_exists(username: str) -> bool:
    keyring, KeyringError, _ = keyring_module()
    try:
        return bool(keyring.get_password(SERVICE_NAME, username))
    except KeyringError as exc:
        print(f"Warning: failed to check GitLab token in keyring: {exc}", file=sys.stderr)
        return False


def read_env_file(path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    if not path.is_file():
        return values
    for line in path.read_text().splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=" not in stripped:
            continue
        key, value = stripped.split("=", 1)
        values[key.strip()] = value.strip().strip('"').strip("'")
    return values


def read_env() -> dict[str, str]:
    return read_env_file(ENV_FILE)


def login_defaults() -> dict[str, str]:
    keys = ["GITLAB_API_URL", "GITLAB_PROJECT_ID", "GITLAB_ALLOWED_PROJECT_IDS", "GITLAB_READ_ONLY_MODE", "GITLAB_TIMEOUT"]
    example = read_env_file(ENV_EXAMPLE_FILE)
    current = read_env()
    return {key: current.get(key) or example.get(key, "") for key in keys}


def print_login_defaults() -> int:
    print(json.dumps({"ok": True, "data": login_defaults()}, indent=2, ensure_ascii=False))
    return 0


def ensure_env_file() -> None:
    if ENV_FILE.is_file():
        return
    if ENV_EXAMPLE_FILE.is_file():
        shutil.copyfile(ENV_EXAMPLE_FILE, ENV_FILE)
        print(f"Success: created {ENV_FILE} from {ENV_EXAMPLE_FILE.name}.")
        return
    ENV_FILE.touch()
    print(f"Success: created empty {ENV_FILE}.")


def write_env(values: dict[str, str]) -> None:
    lines = ENV_FILE.read_text().splitlines() if ENV_FILE.is_file() else []
    seen: set[str] = set()
    output: list[str] = []
    for line in lines:
        key = line.split("=", 1)[0].strip() if "=" in line and not line.lstrip().startswith("#") else ""
        if key in values:
            output.append(f"{key}={values[key]}")
            seen.add(key)
        else:
            output.append(line)
    if output and output[-1].strip():
        output.append("")
    for key, value in values.items():
        if key not in seen:
            output.append(f"{key}={value}")
    ENV_FILE.write_text("\n".join(output) + "\n")


def test_gitlab_credentials(profile_name: str = "default") -> int:
    cli_script = SKILL_ROOT / "scripts" / "gitlab_cli.py"
    cmd = ["uv", "run", str(cli_script), "--profile", profile_name, "list_projects", "--param", "per_page=1"]
    env = os.environ.copy()
    for name in list(env):
        if name.startswith("GITLAB_"):
            del env[name]
    try:
        result = subprocess.run(
            cmd, cwd=SKILL_ROOT, capture_output=True, text=True, env=env,
            timeout=VERIFICATION_TIMEOUT_SECONDS,
        )
    except FileNotFoundError:
        print("Error: uv is required and must be installed on PATH to test GitLab credentials.", file=sys.stderr)
        return 1
    except subprocess.TimeoutExpired:
        print(f"Error: GitLab credential test timed out after {VERIFICATION_TIMEOUT_SECONDS} seconds.", file=sys.stderr)
        return 1

    output = result.stdout.strip() or result.stderr.strip()
    try:
        payload = json.loads(output)
    except json.JSONDecodeError:
        print("Error: GitLab credential test returned non-JSON output.", file=sys.stderr)
        if output:
            print(output, file=sys.stderr)
        return 1

    if result.returncode == 0 and payload.get("ok") is True:
        print("Success: GitLab credentials verified with list_projects per_page=1.")
        return 0

    print("Error: GitLab credential test failed.", file=sys.stderr)
    print(json.dumps(payload, indent=2, ensure_ascii=False), file=sys.stderr)
    return 1


def _login_value(explicit: str | None, environment_name: str, profile_value: str | None, legacy_value: str | None, fallback: str = "") -> str:
    """Resolve one login value without allowing legacy .env to mask process input."""
    if explicit is not None:
        return explicit
    if environment_name in os.environ:
        return os.environ[environment_name]
    if profile_value is not None:
        return profile_value
    if legacy_value is not None:
        return legacy_value
    return fallback


def login(
    username: str | None = None,
    token_arg: str | None = None,
    token_env: str = "GITLAB_LOGIN_TOKEN",
    api_url_arg: str | None = None,
    project_id_arg: str | None = None,
    allowed_project_ids_arg: str | None = None,
    read_only_mode_arg: str | None = None,
    timeout_arg: str | None = None,
    skip_test: bool = False,
    profile_name: str | None = None,
    activate: bool = True,
) -> int:
    """Non-interactive keyring-backed login/setup flow."""
    existing = read_env()
    document = read_document()
    resolved_profile_name = profile_name or document["active_profile"] or "default"
    existing_profile = document["profiles"].get(resolved_profile_name, {})
    profile_settings = existing_profile.get("settings", {})

    api_url = _login_value(
        api_url_arg, "GITLAB_API_URL", existing_profile.get("endpoint"), existing.get("GITLAB_API_URL"),
    ).rstrip("/")
    keyring_user = _login_value(
        username, "GITLAB_LOGIN_USER", existing_profile.get("keyring_user"), None, api_url
    )
    project_id = _login_value(
        project_id_arg, "GITLAB_PROJECT_ID", profile_settings.get("project_id"), existing.get("GITLAB_PROJECT_ID")
    )
    allowed_project_ids = _login_value(
        allowed_project_ids_arg, "GITLAB_ALLOWED_PROJECT_IDS", profile_settings.get("allowed_project_ids"),
        existing.get("GITLAB_ALLOWED_PROJECT_IDS"),
    )
    read_only_mode = _login_value(
        read_only_mode_arg, "GITLAB_READ_ONLY_MODE", profile_settings.get("read_only_mode"),
        existing.get("GITLAB_READ_ONLY_MODE"), "false",
    )
    timeout = _login_value(
        timeout_arg, "GITLAB_TIMEOUT", profile_settings.get("timeout"), existing.get("GITLAB_TIMEOUT"), "60"
    )
    token = _login_value(token_arg, token_env, None, None)

    missing = []
    if not api_url:
        missing.append("--api-url or GITLAB_API_URL")
    if not keyring_user:
        missing.append("--user or GITLAB_LOGIN_USER")
    if not token:
        missing.append(f"--token or {token_env}")
    if missing:
        print("Error: login is non-interactive; missing required values:", file=sys.stderr)
        for item in missing:
            print(f"  - {item}", file=sys.stderr)
        return 1

    keyring, KeyringError, PasswordDeleteError = keyring_module()
    rollback_failed = False
    try:
        profile = default_profile(api_url, keyring_user, {
            "project_id": project_id,
            "allowed_project_ids": allowed_project_ids,
            "read_only_mode": read_only_mode.lower(),
            "timeout": timeout,
        })
        with profile_lock():
            prior_snapshot = snapshot()
            prior_token = keyring.get_password(SERVICE_NAME, keyring_user)
            document = document_with_profile(resolved_profile_name, profile, activate)
            try:
                keyring.set_password(SERVICE_NAME, keyring_user, token)
                write_document(document)
                written_snapshot = snapshot()
            except (KeyringError, ConfigError) as write_error:
                try:
                    restore(prior_snapshot)
                except ConfigError as exc:
                    rollback_failed = True
                    print(f"Error: failed to roll back GitLab profile metadata: {exc}", file=sys.stderr)
                try:
                    if prior_token is None:
                        keyring.delete_password(SERVICE_NAME, keyring_user)
                    else:
                        keyring.set_password(SERVICE_NAME, keyring_user, prior_token)
                except PasswordDeleteError:
                    if prior_token is not None:
                        rollback_failed = True
                except KeyringError as exc:
                    rollback_failed = True
                    print(f"Error: failed to roll back GitLab keyring token: {exc}", file=sys.stderr)
                raise RuntimeError(str(write_error)) from write_error
    except (KeyringError, ConfigError, RuntimeError) as exc:
        print(f"Error: GitLab login failed: {exc}", file=sys.stderr)
        if rollback_failed:
            print("Error: GitLab login rollback was incomplete; manual recovery is required.", file=sys.stderr)
        return 1

    verification = 0 if skip_test else test_gitlab_credentials(resolved_profile_name)
    if verification != 0:
        try:
            with profile_lock():
                if snapshot() == written_snapshot:
                    try:
                        restore(prior_snapshot)
                    except ConfigError as exc:
                        rollback_failed = True
                        print(f"Error: failed to roll back GitLab profile metadata: {exc}", file=sys.stderr)
                else:
                    rollback_failed = True
                    print("Error: GitLab profile changed during verification; newer metadata was preserved.", file=sys.stderr)
                try:
                    if keyring.get_password(SERVICE_NAME, keyring_user) == token:
                        if prior_token is None:
                            keyring.delete_password(SERVICE_NAME, keyring_user)
                        else:
                            keyring.set_password(SERVICE_NAME, keyring_user, prior_token)
                except PasswordDeleteError:
                    if prior_token is not None:
                        rollback_failed = True
                except KeyringError as exc:
                    rollback_failed = True
                    print(f"Error: failed to roll back GitLab keyring token: {exc}", file=sys.stderr)
        except ConfigError as exc:
            rollback_failed = True
            print(f"Error: failed to reacquire GitLab profile lock for rollback: {exc}", file=sys.stderr)
        print("Error: GitLab login failed: remote credential verification failed", file=sys.stderr)
        if rollback_failed:
            print("Error: GitLab login rollback was incomplete; manual recovery is required.", file=sys.stderr)
        return 1

    try:
        with profile_lock():
            current = read_document()
            transaction_current = (
                current["profiles"].get(resolved_profile_name) == profile
                and keyring.get_password(SERVICE_NAME, keyring_user) == token
            )
    except (ConfigError, KeyringError) as exc:
        print(f"Error: GitLab login could not confirm committed credentials: {exc}", file=sys.stderr)
        return 1
    if not transaction_current:
        print("Error: GitLab login was superseded by a concurrent credential update.", file=sys.stderr)
        return 1

    if skip_test:
        print("Info: skipped GitLab credential test.")
    return 0


def setup_token(
    username: str | None = None,
    token_arg: str | None = None,
    token_env: str = "GITLAB_LOGIN_TOKEN",
    api_url_arg: str | None = None,
    write_secret_to_env: bool = False,
) -> int:
    existing = read_env()
    api_url = (api_url_arg or os.getenv("GITLAB_API_URL") or existing.get("GITLAB_API_URL") or "").rstrip("/")
    token = token_arg or os.getenv(token_env, "")
    if not token:
        print(f"Error: setup is non-interactive; provide --token or {token_env}.", file=sys.stderr)
        return 1
    try:
        api_url = validate_endpoint(api_url)
    except ConfigError as exc:
        print(f"Error: invalid GitLab endpoint: {exc}", file=sys.stderr)
        return 1
    if write_secret_to_env:
        ensure_env_file()
        write_env({
            "GITLAB_API_URL": api_url,
            "GITLAB_PERSONAL_ACCESS_TOKEN": token,
            "GITLAB_TOKEN_KEYRING_USER": "",
        })
        print(f"Success: wrote direct-token config to {ENV_FILE}.")
        return 0
    return login(username=username, token_arg=token, token_env=token_env, api_url_arg=api_url, skip_test=True)


def _profile_action(action: str, profile_name: str | None) -> int:
    try:
        if action == "profiles":
            document = read_document()
            print(json.dumps({"ok": True, "data": {
                "active_profile": document["active_profile"],
                "profiles": sorted(document["profiles"]),
            }}, ensure_ascii=False))
        elif action == "use-profile":
            select_profile(profile_name or "")
        else:
            remove_profile(profile_name or "")
        return 0
    except ConfigError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1


def main() -> int:
    parser = argparse.ArgumentParser(description="Manage GitLab token in the OS credential store")
    parser.add_argument("action", choices=["defaults", "login", "save", "get", "delete", "setup", "profiles", "use-profile", "delete-profile"])
    parser.add_argument("--user", help="OS keyring username, normally the GitLab API URL")
    parser.add_argument("--token", help="Token for login/save/setup; prefer --token-env to avoid command-line exposure")
    parser.add_argument("--token-env", default="GITLAB_LOGIN_TOKEN", help="Environment variable containing the token for login/save/setup")
    parser.add_argument("--api-url", help="GitLab API URL for login/setup")
    parser.add_argument("--project-id", help="Default GitLab project ID")
    parser.add_argument("--allowed-project-ids", help="Comma-separated allowed GitLab project IDs")
    parser.add_argument("--read-only-mode", help="GITLAB_READ_ONLY_MODE value")
    parser.add_argument("--timeout", help="GITLAB_TIMEOUT value")
    parser.add_argument("--show", action="store_true", help="Print retrieved token for get (off by default)")
    parser.add_argument("--write-secret-to-env", action="store_true", help="For setup only: write token directly to .env instead of keyring")
    parser.add_argument("--skip-test", action="store_true", help="For login only: skip the post-login GitLab CLI credential test")
    parser.add_argument("--profile", help="Named durable profile; defaults to the active profile or default")
    parser.add_argument("--no-activate", action="store_true", help="Create/update the login profile without making it active")
    args = parser.parse_args()

    if args.action in {"use-profile", "delete-profile"} and args.profile is None:
        parser.error(f"--profile is required for {args.action}")
    if args.action in {"profiles", "use-profile", "delete-profile"}:
        return _profile_action(args.action, args.profile)
    if args.action == "defaults":
        return print_login_defaults()
    if args.action == "login":
        login_kwargs = {
            "username": args.user,
            "token_arg": args.token,
            "token_env": args.token_env,
            "api_url_arg": args.api_url,
            "project_id_arg": args.project_id,
            "allowed_project_ids_arg": args.allowed_project_ids,
            "read_only_mode_arg": args.read_only_mode,
            "timeout_arg": args.timeout,
            "skip_test": args.skip_test,
        }
        if args.profile is not None:
            login_kwargs["profile_name"] = args.profile
        if args.no_activate:
            login_kwargs["activate"] = False
        return login(**login_kwargs)
    if args.action == "setup":
        return setup_token(args.user, args.token, args.token_env, args.api_url, args.write_secret_to_env)
    if not args.user:
        print(f"Error: --user is required for {args.action} action.", file=sys.stderr)
        return 1
    if args.action == "save":
        token = args.token or os.getenv(args.token_env, "")
        if not token:
            print(f"Error: save is non-interactive; provide --token or {args.token_env}.", file=sys.stderr)
            return 1
        return save_token(args.user, token)
    if args.action == "get":
        return get_token(args.user, args.show)
    return delete_token(args.user)


if __name__ == "__main__":
    raise SystemExit(main())
