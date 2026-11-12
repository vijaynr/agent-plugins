#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = [
#   "keyring>=25,<26",
# ]
# ///
"""Manage ALM Octane client secrets in the OS credential store.

Secrets are stored under service name ``AgentDevelopmentToolkit:alm-octane``. The
username should be the Octane API client ID, matching
OCTANE_CLIENT_SECRET_KEYRING_USER in .env.
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

SERVICE_NAME = "AgentDevelopmentToolkit:alm-octane"
VERIFICATION_TIMEOUT_SECONDS = 120
SKILL_ROOT = Path(__file__).resolve().parent.parent
ENV_FILE = SKILL_ROOT / ".env"
ENV_EXAMPLE_FILE = SKILL_ROOT / ".env.example"


def keyring_module():
    try:
        import keyring
        from keyring.errors import KeyringError, PasswordDeleteError
    except ImportError:
        print("Error: missing dependency 'keyring'. Run with: uv run scripts/octane_token.py ...", file=sys.stderr)
        raise SystemExit(1)
    return keyring, KeyringError, PasswordDeleteError


def save_secret(username: str, secret: str) -> int:
    keyring, KeyringError, _ = keyring_module()
    try:
        keyring.set_password(SERVICE_NAME, username, secret)
    except KeyringError as exc:
        print(f"Error: failed to save Octane client secret: {exc}", file=sys.stderr)
        return 1
    print(f"Success: Octane client secret saved for {username}.")
    return 0


def get_secret(username: str, show: bool = False) -> int:
    keyring, KeyringError, _ = keyring_module()
    try:
        secret = keyring.get_password(SERVICE_NAME, username)
    except KeyringError as exc:
        print(f"Error: failed to retrieve Octane client secret: {exc}", file=sys.stderr)
        return 1
    if secret:
        print("Success: Octane client secret retrieved.")
        if show:
            print(secret)
        return 0
    print("Error: No Octane client secret found for this user.", file=sys.stderr)
    return 1


def delete_secret(username: str) -> int:
    keyring, KeyringError, PasswordDeleteError = keyring_module()
    try:
        keyring.delete_password(SERVICE_NAME, username)
    except PasswordDeleteError:
        print("Error: Octane client secret not found.", file=sys.stderr)
        return 1
    except KeyringError as exc:
        print(f"Error: failed to delete Octane client secret: {exc}", file=sys.stderr)
        return 1
    print(f"Success: Octane client secret deleted for {username}.")
    return 0


def secret_exists(username: str) -> bool:
    keyring, KeyringError, _ = keyring_module()
    try:
        return bool(keyring.get_password(SERVICE_NAME, username))
    except KeyringError as exc:
        print(f"Warning: failed to check Octane client secret in keyring: {exc}", file=sys.stderr)
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
    """Return non-secret login defaults that may be shown in UI prompts."""
    keys = ["OCTANE_BASE_URL", "OCTANE_SHARED_SPACE_ID", "OCTANE_WORKSPACE_ID", "OCTANE_TIMEOUT"]
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


def setup_secret(
    username: str | None = None,
    secret_arg: str | None = None,
    secret_env: str = "OCTANE_LOGIN_SECRET",
    base_url_arg: str | None = None,
    shared_space_id_arg: str | None = None,
    workspace_id_arg: str | None = None,
    timeout_arg: str | None = None,
    write_secret_to_env: bool = False,
) -> int:
    existing = read_env()
    base_url = (base_url_arg or existing.get("OCTANE_BASE_URL") or os.getenv("OCTANE_BASE_URL", "")).rstrip("/")
    client_id = username or existing.get("OCTANE_CLIENT_SECRET_KEYRING_USER") or existing.get("OCTANE_CLIENT_ID") or os.getenv("OCTANE_CLIENT_ID", "")
    shared_space_id = shared_space_id_arg or existing.get("OCTANE_SHARED_SPACE_ID") or os.getenv("OCTANE_SHARED_SPACE_ID", "1001")
    workspace_id = workspace_id_arg or existing.get("OCTANE_WORKSPACE_ID") or os.getenv("OCTANE_WORKSPACE_ID", "1003")
    timeout = timeout_arg or existing.get("OCTANE_TIMEOUT") or os.getenv("OCTANE_TIMEOUT", "30")
    secret = secret_arg or os.getenv(secret_env, "")

    missing = []
    if not base_url:
        missing.append("--base-url or OCTANE_BASE_URL")
    if not client_id:
        missing.append("--user or OCTANE_CLIENT_SECRET_KEYRING_USER/OCTANE_CLIENT_ID")
    if not secret:
        missing.append(f"--secret or {secret_env}")
    if missing:
        print("Error: setup is non-interactive; missing required values:", file=sys.stderr)
        for item in missing:
            print(f"  - {item}", file=sys.stderr)
        return 1
    try:
        base_url = validate_endpoint(base_url)
    except ConfigError as exc:
        print(f"Error: invalid Octane endpoint: {exc}", file=sys.stderr)
        return 1
    if write_secret_to_env:
        write_env({
            "OCTANE_BASE_URL": base_url,
            "OCTANE_CLIENT_ID": client_id,
            "OCTANE_CLIENT_SECRET": secret,
            "OCTANE_CLIENT_SECRET_KEYRING_USER": "",
            "OCTANE_SHARED_SPACE_ID": shared_space_id,
            "OCTANE_WORKSPACE_ID": workspace_id,
            "OCTANE_TIMEOUT": timeout,
        })
        print(f"Success: wrote direct-secret config to {ENV_FILE}.")
        return 0
    result = save_secret(client_id, secret)
    if result != 0:
        return result
    write_env({
        "OCTANE_BASE_URL": base_url,
        "OCTANE_CLIENT_ID": "",
        "OCTANE_CLIENT_SECRET": "",
        "OCTANE_CLIENT_SECRET_KEYRING_USER": client_id,
        "OCTANE_SHARED_SPACE_ID": shared_space_id,
        "OCTANE_WORKSPACE_ID": workspace_id,
        "OCTANE_TIMEOUT": timeout,
    })
    print(f"Success: wrote keyring-backed config to {ENV_FILE}.")
    return 0


def test_octane_credentials(profile_name: str = "default") -> int:
    """Run a minimal Octane CLI read against the named durable profile."""
    client_script = SKILL_ROOT / "scripts" / "octane_client.py"
    cmd = ["uv", "run", str(client_script), "--profile", profile_name, "list-work-items", "--limit", "1"]
    env = os.environ.copy()
    for name in list(env):
        if name.startswith("OCTANE_"):
            del env[name]
    try:
        result = subprocess.run(
            cmd, cwd=SKILL_ROOT, capture_output=True, text=True, env=env,
            timeout=VERIFICATION_TIMEOUT_SECONDS,
        )
    except FileNotFoundError:
        print("Error: uv is required and must be installed on PATH to test Octane credentials.", file=sys.stderr)
        return 1
    except subprocess.TimeoutExpired:
        print(f"Error: Octane credential test timed out after {VERIFICATION_TIMEOUT_SECONDS} seconds.", file=sys.stderr)
        return 1

    output = result.stdout.strip() or result.stderr.strip()
    try:
        payload = json.loads(output)
    except json.JSONDecodeError:
        print("Error: Octane credential test returned non-JSON output.", file=sys.stderr)
        if output:
            print(output, file=sys.stderr)
        return 1

    if result.returncode == 0 and payload.get("ok") is True:
        print("Success: Octane credentials verified with list-work-items --limit 1.")
        return 0

    print("Error: Octane credential test failed.", file=sys.stderr)
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
    secret_arg: str | None = None,
    secret_env: str = "OCTANE_LOGIN_SECRET",
    base_url_arg: str | None = None,
    shared_space_id_arg: str | None = None,
    workspace_id_arg: str | None = None,
    timeout_arg: str | None = None,
    skip_test: bool = False,
    profile_name: str | None = None,
    activate: bool = True,
) -> int:
    """Non-interactive keyring-backed login/setup flow.

    Reads values from CLI flags/environment/legacy .env defaults, stores the
    supplied secret in the OS keyring and non-secret metadata in a durable
    profile, then verifies that named profile with the main Octane CLI. User
    interaction must be handled by the caller before invoking this command.
    """
    existing = read_env()
    document = read_document()
    resolved_profile_name = profile_name or document["active_profile"] or "default"
    existing_profile = document["profiles"].get(resolved_profile_name, {})
    profile_settings = existing_profile.get("settings", {})

    base_url = _login_value(
        base_url_arg, "OCTANE_BASE_URL", existing_profile.get("endpoint"), existing.get("OCTANE_BASE_URL")
    ).rstrip("/")
    client_id = _login_value(
        username, "OCTANE_LOGIN_CLIENT_ID", existing_profile.get("keyring_user"), None
    )
    shared_space_id = _login_value(
        shared_space_id_arg, "OCTANE_SHARED_SPACE_ID", profile_settings.get("shared_space_id"),
        existing.get("OCTANE_SHARED_SPACE_ID"), "1001",
    )
    workspace_id = _login_value(
        workspace_id_arg, "OCTANE_WORKSPACE_ID", profile_settings.get("workspace_id"),
        existing.get("OCTANE_WORKSPACE_ID"), "1003",
    )
    timeout = _login_value(
        timeout_arg, "OCTANE_TIMEOUT", profile_settings.get("timeout"), existing.get("OCTANE_TIMEOUT"), "30"
    )
    secret = _login_value(secret_arg, secret_env, None, None)

    missing = []
    if not base_url:
        missing.append("--base-url or OCTANE_BASE_URL")
    if not client_id:
        missing.append("--user or OCTANE_LOGIN_CLIENT_ID")
    if not shared_space_id:
        missing.append("--shared-space-id or OCTANE_SHARED_SPACE_ID")
    if not workspace_id:
        missing.append("--workspace-id or OCTANE_WORKSPACE_ID")
    if not secret:
        missing.append(f"--secret or {secret_env}")
    if missing:
        print("Error: login is non-interactive; missing required values:", file=sys.stderr)
        for item in missing:
            print(f"  - {item}", file=sys.stderr)
        return 1

    keyring, KeyringError, PasswordDeleteError = keyring_module()
    rollback_failed = False
    try:
        profile = default_profile(base_url, client_id, {
            "shared_space_id": shared_space_id,
            "workspace_id": workspace_id,
            "timeout": timeout,
        })
        with profile_lock():
            prior_snapshot = snapshot()
            prior_secret = keyring.get_password(SERVICE_NAME, client_id)
            document = document_with_profile(resolved_profile_name, profile, activate)
            try:
                keyring.set_password(SERVICE_NAME, client_id, secret)
                write_document(document)
                written_snapshot = snapshot()
            except (KeyringError, ConfigError) as write_error:
                try:
                    restore(prior_snapshot)
                except ConfigError as exc:
                    rollback_failed = True
                    print(f"Error: failed to roll back Octane profile metadata: {exc}", file=sys.stderr)
                try:
                    if prior_secret is None:
                        keyring.delete_password(SERVICE_NAME, client_id)
                    else:
                        keyring.set_password(SERVICE_NAME, client_id, prior_secret)
                except PasswordDeleteError:
                    if prior_secret is not None:
                        rollback_failed = True
                except KeyringError as exc:
                    rollback_failed = True
                    print(f"Error: failed to roll back Octane keyring secret: {exc}", file=sys.stderr)
                raise RuntimeError(str(write_error)) from write_error
    except (KeyringError, ConfigError, RuntimeError) as exc:
        print(f"Error: Octane login failed: {exc}", file=sys.stderr)
        if rollback_failed:
            print("Error: Octane login failed and rollback was incomplete; manual recovery is required.", file=sys.stderr)
        return 1

    verification = 0 if skip_test else test_octane_credentials(resolved_profile_name)
    if verification != 0:
        try:
            with profile_lock():
                if snapshot() == written_snapshot:
                    try:
                        restore(prior_snapshot)
                    except ConfigError as exc:
                        rollback_failed = True
                        print(f"Error: failed to roll back Octane profile metadata: {exc}", file=sys.stderr)
                else:
                    rollback_failed = True
                    print("Error: Octane profile changed during verification; newer metadata was preserved.", file=sys.stderr)
                try:
                    if keyring.get_password(SERVICE_NAME, client_id) == secret:
                        if prior_secret is None:
                            keyring.delete_password(SERVICE_NAME, client_id)
                        else:
                            keyring.set_password(SERVICE_NAME, client_id, prior_secret)
                except PasswordDeleteError:
                    if prior_secret is not None:
                        rollback_failed = True
                except KeyringError as exc:
                    rollback_failed = True
                    print(f"Error: failed to roll back Octane keyring secret: {exc}", file=sys.stderr)
        except ConfigError as exc:
            rollback_failed = True
            print(f"Error: failed to reacquire Octane profile lock for rollback: {exc}", file=sys.stderr)
        print("Error: Octane login failed: remote credential verification failed", file=sys.stderr)
        if rollback_failed:
            print("Error: Octane login failed and rollback was incomplete; manual recovery is required.", file=sys.stderr)
        return 1

    try:
        with profile_lock():
            current = read_document()
            transaction_current = (
                current["profiles"].get(resolved_profile_name) == profile
                and keyring.get_password(SERVICE_NAME, client_id) == secret
            )
    except (ConfigError, KeyringError) as exc:
        print(f"Error: Octane login could not confirm committed credentials: {exc}", file=sys.stderr)
        return 1
    if not transaction_current:
        print("Error: Octane login was superseded by a concurrent credential update.", file=sys.stderr)
        return 1

    if skip_test:
        print("Info: skipped Octane credential test.")
    else:
        print("Success: wrote durable keyring-backed Octane profile.")
    return 0


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
    parser = argparse.ArgumentParser(description="Manage Octane client secret in the OS credential store")
    parser.add_argument("action", choices=["defaults", "login", "save", "get", "delete", "setup", "profiles", "use-profile", "delete-profile"])
    parser.add_argument("--user", help="OS keyring username, normally the Octane API client ID")
    parser.add_argument("--secret", help="Client secret for login/save/setup; for login prefer --secret-env to avoid command-line exposure")
    parser.add_argument("--secret-env", default="OCTANE_LOGIN_SECRET", help="Environment variable containing the client secret for login/save/setup")
    parser.add_argument("--base-url", help="Octane instance base URL for login/setup")
    parser.add_argument("--shared-space-id", help="Octane shared space ID for login/setup")
    parser.add_argument("--workspace-id", help="Octane workspace ID for login/setup")
    parser.add_argument("--timeout", help="Octane request timeout for login/setup")
    parser.add_argument("--show", action="store_true", help="Print retrieved secret for get (off by default)")
    parser.add_argument("--write-secret-to-env", action="store_true", help="For setup only: write client secret directly to .env instead of keyring")
    parser.add_argument("--skip-test", action="store_true", help="For login only: skip the post-login Octane CLI credential test")
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
            "secret_arg": args.secret,
            "secret_env": args.secret_env,
            "base_url_arg": args.base_url,
            "shared_space_id_arg": args.shared_space_id,
            "workspace_id_arg": args.workspace_id,
            "timeout_arg": args.timeout,
            "skip_test": args.skip_test,
        }
        if args.profile is not None:
            login_kwargs["profile_name"] = args.profile
        if args.no_activate:
            login_kwargs["activate"] = False
        return login(**login_kwargs)
    if args.action == "setup":
        return setup_secret(
            username=args.user,
            secret_arg=args.secret,
            secret_env=args.secret_env,
            base_url_arg=args.base_url,
            shared_space_id_arg=args.shared_space_id,
            workspace_id_arg=args.workspace_id,
            timeout_arg=args.timeout,
            write_secret_to_env=args.write_secret_to_env,
        )
    if not args.user:
        print(f"Error: --user is required for {args.action} action.", file=sys.stderr)
        return 1
    if args.action == "save":
        secret = args.secret or os.getenv(args.secret_env, "")
        if not secret:
            print(f"Error: save is non-interactive; provide --secret or {args.secret_env}.", file=sys.stderr)
            return 1
        return save_secret(args.user, secret)
    if args.action == "get":
        return get_secret(args.user, args.show)
    return delete_secret(args.user)


if __name__ == "__main__":
    raise SystemExit(main())
