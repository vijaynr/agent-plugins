"""RED tests for Task 5a: GitLab profile lifecycle and validation.

API profile selection, legacy migration, and profile locking are intentionally
excluded; those behaviors belong to Tasks 5b, 5c, and 5d.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

import pytest

from .test_gitlab_credential_config import (
    KEYRING_USER,
    SELF_HOSTED_API,
    SENTINEL_TOKEN,
    SERVICE_NAME,
    FakeKeyring,
    FakeRequests,
    isolated_runtime,
    load_script,
    profile_document,
    relocated_skill,
    write_profile,
)


def run_token(token: Any, monkeypatch: pytest.MonkeyPatch, *arguments: str) -> int:
    monkeypatch.setattr(sys, "argv", ["gitlab_token.py", *arguments])
    return token.main()


def login_arguments(profile: str, *extra: str) -> tuple[str, ...]:
    return (
        "login",
        "--profile",
        profile,
        "--user",
        f"{profile}-user",
        "--token",
        SENTINEL_TOKEN,
        "--api-url",
        f"https://{profile}.example.test/api/v4/",
        "--project-id",
        "42",
        "--allowed-project-ids",
        "42,84",
        "--read-only-mode",
        "true",
        "--timeout",
        "17",
        "--skip-test",
        *extra,
    )


def multiple_profile_document(active_profile: str | None = "production") -> dict[str, Any]:
    def profile(name: str, project_id: str, timeout: str) -> dict[str, Any]:
        return {
            "keyring_user": f"{name}-user",
            "endpoint": f"https://{name}.example.test/api/v4",
            "settings": {
                "project_id": project_id,
                "allowed_project_ids": f"{project_id},{int(project_id) + 1}",
                "read_only_mode": "true" if name == "production" else "false",
                "timeout": timeout,
            },
        }

    return {
        "schema_version": 1,
        "active_profile": active_profile,
        "profiles": {
            "zulu": profile("zulu", "30", "30"),
            "production": profile("production", "20", "20"),
            "alpha": profile("alpha", "10", "10"),
        },
    }


def test_named_profile_login_preserves_existing_profiles_and_activates_new_profile(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    isolated_runtime: tuple[Path, FakeKeyring, FakeRequests],
) -> None:
    config_home, fake_keyring, _ = isolated_runtime
    original = profile_document(endpoint="https://default.example.test/api/v4", keyring_user=KEYRING_USER)
    write_profile(config_home, original)
    token = load_script(relocated_skill(tmp_path, "named-login"), "gitlab_token", monkeypatch)

    result = run_token(token, monkeypatch, *login_arguments("production"))

    document = json.loads((config_home / "gitlab.json").read_text(encoding="utf-8"))
    assert result == 0
    assert document["active_profile"] == "production"
    assert document["profiles"]["default"] == original["profiles"]["default"]
    assert document["profiles"]["production"] == {
        "keyring_user": "production-user",
        "endpoint": "https://production.example.test/api/v4",
        "settings": {
            "project_id": "42",
            "allowed_project_ids": "42,84",
            "read_only_mode": "true",
            "timeout": "17",
        },
    }
    assert fake_keyring.passwords[(SERVICE_NAME, "production-user")] == SENTINEL_TOKEN


def test_login_without_profile_updates_active_profile_and_process_values_override_legacy_env(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    isolated_runtime: tuple[Path, FakeKeyring, FakeRequests],
) -> None:
    config_home, fake_keyring, _ = isolated_runtime
    write_profile(config_home, multiple_profile_document())
    skill_root = relocated_skill(tmp_path, "active-login-precedence")
    (skill_root / ".env").write_text(
        "GITLAB_API_URL=https://legacy.example.test/api/v4\nGITLAB_PROJECT_ID=99\n",
        encoding="utf-8",
    )
    monkeypatch.setenv("GITLAB_API_URL", "https://process.example.test/api/v4/")
    monkeypatch.setenv("GITLAB_PROJECT_ID", "41")
    token = load_script(skill_root, "gitlab_token", monkeypatch)

    result = run_token(token, monkeypatch, "login", "--token", SENTINEL_TOKEN, "--skip-test")

    stored = json.loads((config_home / "gitlab.json").read_text(encoding="utf-8"))
    assert result == 0
    assert stored["active_profile"] == "production"
    assert stored["profiles"]["production"] == {
        "keyring_user": "production-user",
        "endpoint": "https://process.example.test/api/v4",
        "settings": {
            "project_id": "41",
            "allowed_project_ids": "20,21",
            "read_only_mode": "true",
            "timeout": "20",
        },
    }
    assert fake_keyring.passwords[(SERVICE_NAME, "production-user")] == SENTINEL_TOKEN


def test_profiles_lists_names_sorted_and_marks_active_without_reading_secrets(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    isolated_runtime: tuple[Path, FakeKeyring, FakeRequests],
) -> None:
    config_home, fake_keyring, _ = isolated_runtime
    write_profile(config_home, multiple_profile_document())
    fake_keyring.passwords[(SERVICE_NAME, "production-user")] = SENTINEL_TOKEN
    token = load_script(relocated_skill(tmp_path, "list-profiles"), "gitlab_token", monkeypatch)

    result = run_token(token, monkeypatch, "profiles")

    payload = json.loads(capsys.readouterr().out)
    assert result == 0
    assert payload == {
        "ok": True,
        "data": {"active_profile": "production", "profiles": ["alpha", "production", "zulu"]},
    }
    assert fake_keyring.get_calls == []
    assert SENTINEL_TOKEN not in json.dumps(payload)


def test_use_profile_changes_only_the_active_profile(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    isolated_runtime: tuple[Path, FakeKeyring, FakeRequests],
) -> None:
    config_home, _, _ = isolated_runtime
    config_path = write_profile(config_home, multiple_profile_document())
    before = json.loads(config_path.read_text(encoding="utf-8"))
    token = load_script(relocated_skill(tmp_path, "use-profile"), "gitlab_token", monkeypatch)

    result = run_token(token, monkeypatch, "use-profile", "--profile", "zulu")

    after = json.loads(config_path.read_text(encoding="utf-8"))
    assert result == 0
    assert after["active_profile"] == "zulu"
    assert after["profiles"] == before["profiles"]


@pytest.mark.parametrize("prior_active", ["default", None])
def test_no_activate_login_preserves_prior_active_selection(
    prior_active: str | None,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    isolated_runtime: tuple[Path, FakeKeyring, FakeRequests],
) -> None:
    config_home, _, _ = isolated_runtime
    document = profile_document()
    document["active_profile"] = prior_active
    write_profile(config_home, document)
    token = load_script(relocated_skill(tmp_path, f"no-activate-{prior_active}"), "gitlab_token", monkeypatch)

    result = run_token(token, monkeypatch, *login_arguments("staging", "--no-activate"))

    stored = json.loads((config_home / "gitlab.json").read_text(encoding="utf-8"))
    assert result == 0
    assert stored["active_profile"] == prior_active
    assert "staging" in stored["profiles"]


def test_no_activate_login_without_existing_document_leaves_active_profile_unset(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    isolated_runtime: tuple[Path, FakeKeyring, FakeRequests],
) -> None:
    config_home, _, _ = isolated_runtime
    token = load_script(relocated_skill(tmp_path, "first-no-activate"), "gitlab_token", monkeypatch)

    result = run_token(token, monkeypatch, *login_arguments("staging", "--no-activate"))

    stored = json.loads((config_home / "gitlab.json").read_text(encoding="utf-8"))
    assert result == 0
    assert stored["active_profile"] is None
    assert list(stored["profiles"]) == ["staging"]


def test_deleting_non_active_profile_removes_only_metadata(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    isolated_runtime: tuple[Path, FakeKeyring, FakeRequests],
) -> None:
    config_home, fake_keyring, _ = isolated_runtime
    write_profile(config_home, multiple_profile_document())
    fake_keyring.passwords[(SERVICE_NAME, "zulu-user")] = SENTINEL_TOKEN
    token = load_script(relocated_skill(tmp_path, "delete-inactive"), "gitlab_token", monkeypatch)

    result = run_token(token, monkeypatch, "delete-profile", "--profile", "zulu")

    stored = json.loads((config_home / "gitlab.json").read_text(encoding="utf-8"))
    assert result == 0
    assert stored["active_profile"] == "production"
    assert "zulu" not in stored["profiles"]
    assert fake_keyring.passwords[(SERVICE_NAME, "zulu-user")] == SENTINEL_TOKEN


def test_deleting_active_profile_activates_lexically_first_remaining_profile_without_deleting_secret(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    isolated_runtime: tuple[Path, FakeKeyring, FakeRequests],
) -> None:
    config_home, fake_keyring, _ = isolated_runtime
    write_profile(config_home, multiple_profile_document())
    fake_keyring.passwords[(SERVICE_NAME, "production-user")] = SENTINEL_TOKEN
    token = load_script(relocated_skill(tmp_path, "delete-active"), "gitlab_token", monkeypatch)

    result = run_token(token, monkeypatch, "delete-profile", "--profile", "production")

    stored = json.loads((config_home / "gitlab.json").read_text(encoding="utf-8"))
    assert result == 0
    assert stored["active_profile"] == "alpha"
    assert set(stored["profiles"]) == {"alpha", "zulu"}
    assert fake_keyring.passwords[(SERVICE_NAME, "production-user")] == SENTINEL_TOKEN


def test_deleting_final_profile_keeps_empty_document_and_keyring_secret(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    isolated_runtime: tuple[Path, FakeKeyring, FakeRequests],
) -> None:
    config_home, fake_keyring, _ = isolated_runtime
    write_profile(config_home)
    fake_keyring.passwords[(SERVICE_NAME, KEYRING_USER)] = SENTINEL_TOKEN
    token = load_script(relocated_skill(tmp_path, "delete-final"), "gitlab_token", monkeypatch)

    result = run_token(token, monkeypatch, "delete-profile", "--profile", "default")

    stored = json.loads((config_home / "gitlab.json").read_text(encoding="utf-8"))
    assert result == 0
    assert stored == {"schema_version": 1, "active_profile": None, "profiles": {}}
    assert fake_keyring.passwords[(SERVICE_NAME, KEYRING_USER)] == SENTINEL_TOKEN


@pytest.mark.parametrize(
    "profile_name",
    ["", " leading", "trailing ", ".hidden", "slash/name", "back\\slash", "name!", "a" * 65],
)
def test_profile_documents_reject_unsafe_profile_names(
    profile_name: str,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    isolated_runtime: tuple[Path, FakeKeyring, FakeRequests],
) -> None:
    config = load_script(relocated_skill(tmp_path, "invalid-name"), "credential_config", monkeypatch)
    document = profile_document()
    document["profiles"] = {profile_name: document["profiles"]["default"]}
    document["active_profile"] = profile_name

    with pytest.raises(config.ConfigError, match="profile"):
        config.validate_document(document)


@pytest.mark.parametrize(
    "document",
    [
        {},
        {"schema_version": 2, "active_profile": None, "profiles": {}},
        {"schema_version": 1, "active_profile": "missing", "profiles": {}},
        {"schema_version": 1, "active_profile": None, "profiles": []},
        {"schema_version": 1, "active_profile": None, "profiles": {"default": None}},
        {
            "schema_version": 1,
            "active_profile": "default",
            "profiles": {"default": {"keyring_user": KEYRING_USER, "settings": profile_document()["profiles"]["default"]["settings"]}},
        },
        {
            "schema_version": 1,
            "active_profile": "default",
            "profiles": {"default": {"endpoint": SELF_HOSTED_API, "settings": profile_document()["profiles"]["default"]["settings"]}},
        },
    ],
)
def test_profile_operations_fail_closed_on_invalid_documents_without_mutation(
    document: dict[str, Any],
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    isolated_runtime: tuple[Path, FakeKeyring, FakeRequests],
) -> None:
    config_home, _, _ = isolated_runtime
    config_home.mkdir(parents=True, exist_ok=True)
    config_path = config_home / "gitlab.json"
    config_path.write_text(json.dumps(document), encoding="utf-8")
    before = config_path.read_bytes()
    token = load_script(relocated_skill(tmp_path, "invalid-document"), "gitlab_token", monkeypatch)

    result = run_token(token, monkeypatch, "use-profile", "--profile", "default")

    assert result != 0
    assert config_path.read_bytes() == before


@pytest.mark.parametrize("invalid_bytes", [b"", b"{not-json"])
def test_profile_operations_fail_closed_on_empty_or_malformed_json_without_mutation(
    invalid_bytes: bytes,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    isolated_runtime: tuple[Path, FakeKeyring, FakeRequests],
) -> None:
    config_home, _, _ = isolated_runtime
    config_home.mkdir(parents=True, exist_ok=True)
    config_path = config_home / "gitlab.json"
    config_path.write_bytes(invalid_bytes)
    before = config_path.read_bytes()
    token = load_script(relocated_skill(tmp_path, "malformed-document"), "gitlab_token", monkeypatch)

    result = run_token(token, monkeypatch, "delete-profile", "--profile", "default")

    assert result != 0
    assert config_path.read_bytes() == before


@pytest.mark.parametrize(
    "settings",
    [
        None,
        [],
        {},
        {"project_id": "42", "allowed_project_ids": "42", "read_only_mode": "true"},
        {"project_id": 42, "allowed_project_ids": "42,84", "read_only_mode": "true", "timeout": "30"},
        {"project_id": "42", "allowed_project_ids": ["42", "84"], "read_only_mode": "true", "timeout": "30"},
        {"project_id": "42", "allowed_project_ids": "42,84", "read_only_mode": True, "timeout": "30"},
        {"project_id": "42", "allowed_project_ids": "42,84", "read_only_mode": "TRUE", "timeout": "30"},
        {"project_id": "42", "allowed_project_ids": "42,84", "read_only_mode": "yes", "timeout": "30"},
        {"project_id": "42", "allowed_project_ids": "42,84", "read_only_mode": "true", "timeout": "not-a-number"},
        {"project_id": "42", "allowed_project_ids": "42,84", "read_only_mode": "false", "timeout": "0"},
        {"project_id": "42", "allowed_project_ids": "42,84", "read_only_mode": "false", "timeout": "-1"},
        {"project_id": "42", "allowed_project_ids": "42,84", "read_only_mode": "false", "timeout": True},
        {"project_id": "42", "allowed_project_ids": "42,84", "read_only_mode": "false", "timeout": 30},
        {"project_id": "42", "allowed_project_ids": "42,84", "read_only_mode": "false", "timeout": "30", "unknown": "value"},
    ],
)
def test_profile_documents_reject_invalid_gitlab_settings(
    settings: Any,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    isolated_runtime: tuple[Path, FakeKeyring, FakeRequests],
) -> None:
    config = load_script(relocated_skill(tmp_path, "invalid-settings"), "credential_config", monkeypatch)
    document = profile_document()
    document["profiles"]["default"]["settings"] = settings

    with pytest.raises(config.ConfigError, match="settings|project_id|allowed_project_ids|read_only_mode|timeout"):
        config.validate_document(document)


@pytest.mark.parametrize("read_only_mode", ["true", "false"])
def test_profile_documents_accept_string_ids_boolean_literals_and_positive_timeout(
    read_only_mode: str,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    isolated_runtime: tuple[Path, FakeKeyring, FakeRequests],
) -> None:
    config = load_script(relocated_skill(tmp_path, f"valid-settings-{read_only_mode}"), "credential_config", monkeypatch)
    document = profile_document()
    document["profiles"]["default"]["settings"] = {
        "project_id": "",
        "allowed_project_ids": "",
        "read_only_mode": read_only_mode,
        "timeout": "1",
    }

    assert config.validate_document(document) == document


@pytest.mark.parametrize("action", ["use-profile", "delete-profile"])
def test_missing_profile_fails_without_creating_or_mutating_configuration(
    action: str,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    isolated_runtime: tuple[Path, FakeKeyring, FakeRequests],
) -> None:
    config_home, _, _ = isolated_runtime
    config_path = write_profile(config_home)
    before = config_path.read_bytes()
    token = load_script(relocated_skill(tmp_path, f"missing-{action}"), "gitlab_token", monkeypatch)

    result = run_token(token, monkeypatch, action, "--profile", "does-not-exist")

    assert result != 0
    assert config_path.read_bytes() == before


@pytest.mark.parametrize("action", ["use-profile", "delete-profile"])
def test_profile_mutations_require_profile_name_without_mutating_configuration(
    action: str,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    isolated_runtime: tuple[Path, FakeKeyring, FakeRequests],
) -> None:
    config_home, _, _ = isolated_runtime
    config_path = write_profile(config_home)
    before = config_path.read_bytes()
    token = load_script(relocated_skill(tmp_path, f"name-required-{action}"), "gitlab_token", monkeypatch)

    with pytest.raises(SystemExit) as exc_info:
        run_token(token, monkeypatch, action)

    assert exc_info.value.code == 2
    assert config_path.read_bytes() == before


def test_retained_defaults_action_parser_dispatches(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    isolated_runtime: tuple[Path, FakeKeyring, FakeRequests],
) -> None:
    token = load_script(relocated_skill(tmp_path, "compat-defaults"), "gitlab_token", monkeypatch)
    monkeypatch.setattr(token, "print_login_defaults", lambda: 23)
    assert run_token(token, monkeypatch, "defaults") == 23


def test_retained_save_action_parser_accepts_token_flags(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    isolated_runtime: tuple[Path, FakeKeyring, FakeRequests],
) -> None:
    token = load_script(relocated_skill(tmp_path, "compat-save"), "gitlab_token", monkeypatch)
    calls: list[tuple[str, str]] = []
    monkeypatch.setattr(token, "save_token", lambda user, value: calls.append((user, value)) or 24)
    assert run_token(token, monkeypatch, "save", "--user", "gitlab-user", "--token", "value", "--token-env", "CUSTOM_TOKEN") == 24
    assert calls == [("gitlab-user", "value")]


def test_retained_get_and_delete_action_parsers_accept_existing_flags(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    isolated_runtime: tuple[Path, FakeKeyring, FakeRequests],
) -> None:
    token = load_script(relocated_skill(tmp_path, "compat-get-delete"), "gitlab_token", monkeypatch)
    calls: list[tuple[Any, ...]] = []
    monkeypatch.setattr(token, "get_token", lambda user, show: calls.append(("get", user, show)) or 25)
    monkeypatch.setattr(token, "delete_token", lambda user: calls.append(("delete", user)) or 26)
    assert run_token(token, monkeypatch, "get", "--user", "gitlab-user", "--show") == 25
    assert run_token(token, monkeypatch, "delete", "--user", "gitlab-user") == 26
    assert calls == [("get", "gitlab-user", True), ("delete", "gitlab-user")]


def test_retained_setup_parser_accepts_write_secret_to_env_and_connection_flags(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    isolated_runtime: tuple[Path, FakeKeyring, FakeRequests],
) -> None:
    token = load_script(relocated_skill(tmp_path, "compat-setup"), "gitlab_token", monkeypatch)
    calls: list[tuple[Any, ...]] = []
    monkeypatch.setattr(token, "setup_token", lambda *args: calls.append(args) or 27)
    result = run_token(
        token,
        monkeypatch,
        "setup",
        "--user", "gitlab-user",
        "--token", "value",
        "--token-env", "CUSTOM_TOKEN",
        "--api-url", SELF_HOSTED_API,
        "--write-secret-to-env",
    )
    assert result == 27
    assert calls == [("gitlab-user", "value", "CUSTOM_TOKEN", SELF_HOSTED_API, True)]


def test_retained_login_parser_accepts_skip_test_and_gitlab_setting_flags(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    isolated_runtime: tuple[Path, FakeKeyring, FakeRequests],
) -> None:
    token = load_script(relocated_skill(tmp_path, "compat-login"), "gitlab_token", monkeypatch)
    calls: list[dict[str, Any]] = []
    monkeypatch.setattr(token, "login", lambda **kwargs: calls.append(kwargs) or 28)
    result = run_token(
        token,
        monkeypatch,
        "login",
        "--user", "gitlab-user",
        "--token", "value",
        "--token-env", "CUSTOM_TOKEN",
        "--api-url", SELF_HOSTED_API,
        "--project-id", "42",
        "--allowed-project-ids", "42,84",
        "--read-only-mode", "false",
        "--timeout", "17",
        "--skip-test",
    )
    assert result == 28
    assert calls == [{
        "username": "gitlab-user",
        "token_arg": "value",
        "token_env": "CUSTOM_TOKEN",
        "api_url_arg": SELF_HOSTED_API,
        "project_id_arg": "42",
        "allowed_project_ids_arg": "42,84",
        "read_only_mode_arg": "false",
        "timeout_arg": "17",
        "skip_test": True,
    }]


def test_login_parser_forwards_named_profile_and_no_activate_flags(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    isolated_runtime: tuple[Path, FakeKeyring, FakeRequests],
) -> None:
    token = load_script(relocated_skill(tmp_path, "profile-login-flags"), "gitlab_token", monkeypatch)
    calls: list[dict[str, Any]] = []
    monkeypatch.setattr(token, "login", lambda **kwargs: calls.append(kwargs) or 29)

    result = run_token(token, monkeypatch, *login_arguments("staging", "--no-activate"))

    assert result == 29
    assert calls == [{
        "username": "staging-user",
        "token_arg": SENTINEL_TOKEN,
        "token_env": "GITLAB_LOGIN_TOKEN",
        "api_url_arg": "https://staging.example.test/api/v4/",
        "project_id_arg": "42",
        "allowed_project_ids_arg": "42,84",
        "read_only_mode_arg": "true",
        "timeout_arg": "17",
        "skip_test": True,
        "profile_name": "staging",
        "activate": False,
    }]
