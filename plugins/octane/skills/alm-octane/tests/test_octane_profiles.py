"""RED tests for Task 2a: Octane profile lifecycle and validation.

Profile selection in API clients, legacy migration, and profile locking belong to
future tasks and are intentionally not covered here.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

import pytest

from test_octane_credential_config import (
    SERVICE_NAME,
    SENTINEL_SECRET,
    FakeKeyring,
    isolated_runtime,
    load_script,
    profile_document,
    relocated_skill,
    write_profile,
)


def run_token(token: Any, monkeypatch: pytest.MonkeyPatch, *arguments: str) -> int:
    monkeypatch.setattr(sys, "argv", ["octane_token.py", *arguments])
    return token.main()


def login_arguments(profile: str, *extra: str) -> tuple[str, ...]:
    return (
        "login",
        "--profile",
        profile,
        "--user",
        f"{profile}-client",
        "--secret",
        SENTINEL_SECRET,
        "--base-url",
        f"https://{profile}.example.test/",
        "--shared-space-id",
        "131002",
        "--workspace-id",
        "1003",
        "--timeout",
        "17",
        "--skip-test",
        *extra,
    )


def multiple_profile_document(active_profile: str | None = "production") -> dict[str, Any]:
    return {
        "schema_version": 1,
        "active_profile": active_profile,
        "profiles": {
            "zulu": {
                "keyring_user": "zulu-client",
                "endpoint": "https://zulu.example.test",
                "settings": {"shared_space_id": "3", "workspace_id": "30", "timeout": "30"},
            },
            "production": {
                "keyring_user": "production-client",
                "endpoint": "https://production.example.test",
                "settings": {"shared_space_id": "2", "workspace_id": "20", "timeout": "20"},
            },
            "alpha": {
                "keyring_user": "alpha-client",
                "endpoint": "https://alpha.example.test",
                "settings": {"shared_space_id": "1", "workspace_id": "10", "timeout": "10"},
            },
        },
    }


def test_named_profile_login_preserves_existing_profiles_and_activates_new_profile(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    isolated_runtime: tuple[Path, FakeKeyring],
) -> None:
    config_home, fake_keyring = isolated_runtime
    original = profile_document(endpoint="https://default.example.test", keyring_user="default-client")
    write_profile(config_home, original)
    token = load_script(relocated_skill(tmp_path, "named-login"), "octane_token", monkeypatch)

    result = run_token(token, monkeypatch, *login_arguments("production"))

    document = json.loads((config_home / "octane.json").read_text(encoding="utf-8"))
    assert result == 0
    assert document["active_profile"] == "production"
    assert document["profiles"]["default"] == original["profiles"]["default"]
    assert document["profiles"]["production"] == {
        "keyring_user": "production-client",
        "endpoint": "https://production.example.test",
        "settings": {"shared_space_id": "131002", "workspace_id": "1003", "timeout": "17"},
    }
    assert fake_keyring.passwords[(SERVICE_NAME, "production-client")] == SENTINEL_SECRET


def test_login_without_profile_updates_active_profile_and_process_values_override_legacy_env(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    isolated_runtime: tuple[Path, FakeKeyring],
) -> None:
    config_home, fake_keyring = isolated_runtime
    write_profile(config_home, multiple_profile_document())
    skill_root = relocated_skill(tmp_path, "active-login-precedence")
    (skill_root / ".env").write_text(
        "OCTANE_BASE_URL=https://legacy.example.test\nOCTANE_TIMEOUT=99\n",
        encoding="utf-8",
    )
    monkeypatch.setenv("OCTANE_BASE_URL", "https://process.example.test/")
    monkeypatch.setenv("OCTANE_TIMEOUT", "41")
    token = load_script(skill_root, "octane_token", monkeypatch)

    result = run_token(token, monkeypatch, "login", "--secret", SENTINEL_SECRET, "--skip-test")

    stored = json.loads((config_home / "octane.json").read_text(encoding="utf-8"))
    assert result == 0
    assert stored["active_profile"] == "production"
    assert stored["profiles"]["production"] == {
        "keyring_user": "production-client",
        "endpoint": "https://process.example.test",
        "settings": {"shared_space_id": "2", "workspace_id": "20", "timeout": "41"},
    }
    assert fake_keyring.passwords[(SERVICE_NAME, "production-client")] == SENTINEL_SECRET


def test_profiles_lists_names_in_lexical_order_and_marks_active_without_reading_secrets(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    isolated_runtime: tuple[Path, FakeKeyring],
) -> None:
    config_home, fake_keyring = isolated_runtime
    write_profile(config_home, multiple_profile_document())
    fake_keyring.passwords[(SERVICE_NAME, "production-client")] = SENTINEL_SECRET
    token = load_script(relocated_skill(tmp_path, "list-profiles"), "octane_token", monkeypatch)

    result = run_token(token, monkeypatch, "profiles")

    payload = json.loads(capsys.readouterr().out)
    assert result == 0
    assert payload == {
        "ok": True,
        "data": {"active_profile": "production", "profiles": ["alpha", "production", "zulu"]},
    }
    assert fake_keyring.get_calls == []
    assert SENTINEL_SECRET not in json.dumps(payload)


def test_use_profile_changes_only_the_active_profile(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    isolated_runtime: tuple[Path, FakeKeyring],
) -> None:
    config_home, _ = isolated_runtime
    config_path = write_profile(config_home, multiple_profile_document())
    before = json.loads(config_path.read_text(encoding="utf-8"))
    token = load_script(relocated_skill(tmp_path, "use-profile"), "octane_token", monkeypatch)

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
    isolated_runtime: tuple[Path, FakeKeyring],
) -> None:
    config_home, _ = isolated_runtime
    document = profile_document()
    document["active_profile"] = prior_active
    write_profile(config_home, document)
    token = load_script(relocated_skill(tmp_path, f"no-activate-{prior_active}"), "octane_token", monkeypatch)

    result = run_token(token, monkeypatch, *login_arguments("staging", "--no-activate"))

    stored = json.loads((config_home / "octane.json").read_text(encoding="utf-8"))
    assert result == 0
    assert stored["active_profile"] == prior_active
    assert "staging" in stored["profiles"]


def test_no_activate_login_without_an_existing_document_leaves_active_profile_unset(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    isolated_runtime: tuple[Path, FakeKeyring],
) -> None:
    config_home, _ = isolated_runtime
    token = load_script(relocated_skill(tmp_path, "first-no-activate"), "octane_token", monkeypatch)

    result = run_token(token, monkeypatch, *login_arguments("staging", "--no-activate"))

    stored = json.loads((config_home / "octane.json").read_text(encoding="utf-8"))
    assert result == 0
    assert stored["active_profile"] is None
    assert list(stored["profiles"]) == ["staging"]


def test_deleting_a_non_active_profile_removes_metadata_but_not_its_keyring_secret(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    isolated_runtime: tuple[Path, FakeKeyring],
) -> None:
    config_home, fake_keyring = isolated_runtime
    write_profile(config_home, multiple_profile_document())
    fake_keyring.passwords[(SERVICE_NAME, "zulu-client")] = SENTINEL_SECRET
    token = load_script(relocated_skill(tmp_path, "delete-inactive"), "octane_token", monkeypatch)

    result = run_token(token, monkeypatch, "delete-profile", "--profile", "zulu")

    stored = json.loads((config_home / "octane.json").read_text(encoding="utf-8"))
    assert result == 0
    assert stored["active_profile"] == "production"
    assert "zulu" not in stored["profiles"]
    assert fake_keyring.passwords[(SERVICE_NAME, "zulu-client")] == SENTINEL_SECRET


def test_deleting_the_active_profile_activates_lexically_first_remaining_profile(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    isolated_runtime: tuple[Path, FakeKeyring],
) -> None:
    config_home, fake_keyring = isolated_runtime
    write_profile(config_home, multiple_profile_document())
    fake_keyring.passwords[(SERVICE_NAME, "production-client")] = SENTINEL_SECRET
    token = load_script(relocated_skill(tmp_path, "delete-active"), "octane_token", monkeypatch)

    result = run_token(token, monkeypatch, "delete-profile", "--profile", "production")

    stored = json.loads((config_home / "octane.json").read_text(encoding="utf-8"))
    assert result == 0
    assert stored["active_profile"] == "alpha"
    assert set(stored["profiles"]) == {"alpha", "zulu"}
    assert fake_keyring.passwords[(SERVICE_NAME, "production-client")] == SENTINEL_SECRET


def test_deleting_the_final_profile_keeps_an_empty_metadata_document_and_keyring_secret(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    isolated_runtime: tuple[Path, FakeKeyring],
) -> None:
    config_home, fake_keyring = isolated_runtime
    write_profile(config_home)
    fake_keyring.passwords[(SERVICE_NAME, "client-id")] = SENTINEL_SECRET
    token = load_script(relocated_skill(tmp_path, "delete-final"), "octane_token", monkeypatch)

    result = run_token(token, monkeypatch, "delete-profile", "--profile", "default")

    stored = json.loads((config_home / "octane.json").read_text(encoding="utf-8"))
    assert result == 0
    assert stored == {"schema_version": 1, "active_profile": None, "profiles": {}}
    assert fake_keyring.passwords[(SERVICE_NAME, "client-id")] == SENTINEL_SECRET


@pytest.mark.parametrize(
    "profile_name",
    ["", " leading", "trailing ", ".hidden", "slash/name", "back\\slash", "name!", "a" * 65],
)
def test_profile_documents_reject_unsafe_profile_names(
    profile_name: str,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    isolated_runtime: tuple[Path, FakeKeyring],
) -> None:
    _, _ = isolated_runtime
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
    ],
)
def test_profile_operations_fail_closed_on_invalid_documents_without_mutation(
    document: dict[str, Any],
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    isolated_runtime: tuple[Path, FakeKeyring],
) -> None:
    config_home, _ = isolated_runtime
    config_home.mkdir(parents=True, exist_ok=True)
    config_path = config_home / "octane.json"
    config_path.write_text(json.dumps(document), encoding="utf-8")
    before = config_path.read_bytes()
    token = load_script(relocated_skill(tmp_path, "invalid-document"), "octane_token", monkeypatch)

    result = run_token(token, monkeypatch, "use-profile", "--profile", "default")

    assert result != 0
    assert config_path.read_bytes() == before


@pytest.mark.parametrize("invalid_bytes", [b"", b"{not-json"])
def test_profile_operations_fail_closed_on_empty_or_malformed_json_without_mutation(
    invalid_bytes: bytes,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    isolated_runtime: tuple[Path, FakeKeyring],
) -> None:
    config_home, _ = isolated_runtime
    config_home.mkdir(parents=True, exist_ok=True)
    config_path = config_home / "octane.json"
    config_path.write_bytes(invalid_bytes)
    before = config_path.read_bytes()
    token = load_script(relocated_skill(tmp_path, "malformed-document"), "octane_token", monkeypatch)

    result = run_token(token, monkeypatch, "delete-profile", "--profile", "default")

    assert result != 0
    assert config_path.read_bytes() == before


@pytest.mark.parametrize(
    "settings",
    [
        None,
        [],
        {},
        {"shared_space_id": "1001", "workspace_id": "1003"},
        {"shared_space_id": 1001, "workspace_id": "1003", "timeout": "30"},
        {"shared_space_id": "", "workspace_id": "1003", "timeout": "30"},
        {"shared_space_id": "1001", "workspace_id": None, "timeout": "30"},
        {"shared_space_id": "1001", "workspace_id": "1003", "timeout": "not-a-number"},
        {"shared_space_id": "1001", "workspace_id": "1003", "timeout": "0"},
        {"shared_space_id": "1001", "workspace_id": "1003", "timeout": True},
        {"shared_space_id": "1001", "workspace_id": "1003", "timeout": "30", "unknown": "value"},
    ],
)
def test_profile_documents_reject_invalid_octane_settings(
    settings: Any,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    isolated_runtime: tuple[Path, FakeKeyring],
) -> None:
    _, _ = isolated_runtime
    config = load_script(relocated_skill(tmp_path, "invalid-settings"), "credential_config", monkeypatch)
    document = profile_document()
    document["profiles"]["default"]["settings"] = settings

    with pytest.raises(config.ConfigError, match="settings|shared_space_id|workspace_id|timeout"):
        config.validate_document(document)


@pytest.mark.parametrize("action", ["use-profile", "delete-profile"])
def test_missing_profile_fails_without_creating_or_mutating_configuration(
    action: str,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    isolated_runtime: tuple[Path, FakeKeyring],
) -> None:
    config_home, _ = isolated_runtime
    config_path = write_profile(config_home)
    before = config_path.read_bytes()
    token = load_script(relocated_skill(tmp_path, f"missing-{action}"), "octane_token", monkeypatch)

    result = run_token(token, monkeypatch, action, "--profile", "does-not-exist")

    assert result != 0
    assert config_path.read_bytes() == before


@pytest.mark.parametrize("action", ["use-profile", "delete-profile"])
def test_profile_mutations_require_a_profile_name(
    action: str,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    isolated_runtime: tuple[Path, FakeKeyring],
) -> None:
    config_home, _ = isolated_runtime
    config_path = write_profile(config_home)
    before = config_path.read_bytes()
    token = load_script(relocated_skill(tmp_path, f"name-required-{action}"), "octane_token", monkeypatch)

    with pytest.raises(SystemExit) as exc_info:
        run_token(token, monkeypatch, action)

    assert exc_info.value.code == 2
    assert config_path.read_bytes() == before


def test_retained_defaults_action_parser_dispatches(monkeypatch: pytest.MonkeyPatch, tmp_path: Path, isolated_runtime: tuple[Path, FakeKeyring]) -> None:
    token = load_script(relocated_skill(tmp_path, "compat-defaults"), "octane_token", monkeypatch)
    monkeypatch.setattr(token, "print_login_defaults", lambda: 23)
    assert run_token(token, monkeypatch, "defaults") == 23


def test_retained_save_action_parser_accepts_secret_flags(monkeypatch: pytest.MonkeyPatch, tmp_path: Path, isolated_runtime: tuple[Path, FakeKeyring]) -> None:
    token = load_script(relocated_skill(tmp_path, "compat-save"), "octane_token", monkeypatch)
    calls: list[tuple[str, str]] = []
    monkeypatch.setattr(token, "save_secret", lambda user, secret: calls.append((user, secret)) or 24)
    assert run_token(token, monkeypatch, "save", "--user", "client", "--secret", "value", "--secret-env", "CUSTOM_SECRET") == 24
    assert calls == [("client", "value")]


def test_retained_get_and_delete_action_parsers_accept_existing_flags(monkeypatch: pytest.MonkeyPatch, tmp_path: Path, isolated_runtime: tuple[Path, FakeKeyring]) -> None:
    token = load_script(relocated_skill(tmp_path, "compat-get-delete"), "octane_token", monkeypatch)
    calls: list[tuple[Any, ...]] = []
    monkeypatch.setattr(token, "get_secret", lambda user, show: calls.append(("get", user, show)) or 25)
    monkeypatch.setattr(token, "delete_secret", lambda user: calls.append(("delete", user)) or 26)
    assert run_token(token, monkeypatch, "get", "--user", "client", "--show") == 25
    assert run_token(token, monkeypatch, "delete", "--user", "client") == 26
    assert calls == [("get", "client", True), ("delete", "client")]


def test_retained_setup_parser_accepts_write_secret_to_env_and_connection_flags(monkeypatch: pytest.MonkeyPatch, tmp_path: Path, isolated_runtime: tuple[Path, FakeKeyring]) -> None:
    token = load_script(relocated_skill(tmp_path, "compat-setup"), "octane_token", monkeypatch)
    calls: list[dict[str, Any]] = []
    monkeypatch.setattr(token, "setup_secret", lambda **kwargs: calls.append(kwargs) or 27)
    result = run_token(
        token,
        monkeypatch,
        "setup",
        "--user", "client",
        "--secret", "value",
        "--secret-env", "CUSTOM_SECRET",
        "--base-url", "https://octane.example.test",
        "--shared-space-id", "1",
        "--workspace-id", "2",
        "--timeout", "3",
        "--write-secret-to-env",
    )
    assert result == 27
    assert calls == [{
        "username": "client",
        "secret_arg": "value",
        "secret_env": "CUSTOM_SECRET",
        "base_url_arg": "https://octane.example.test",
        "shared_space_id_arg": "1",
        "workspace_id_arg": "2",
        "timeout_arg": "3",
        "write_secret_to_env": True,
    }]


def test_retained_login_parser_accepts_skip_test_and_connection_flags(monkeypatch: pytest.MonkeyPatch, tmp_path: Path, isolated_runtime: tuple[Path, FakeKeyring]) -> None:
    token = load_script(relocated_skill(tmp_path, "compat-login"), "octane_token", monkeypatch)
    calls: list[dict[str, Any]] = []
    monkeypatch.setattr(token, "login", lambda **kwargs: calls.append(kwargs) or 28)
    result = run_token(
        token,
        monkeypatch,
        "login",
        "--user", "client",
        "--secret", "value",
        "--secret-env", "CUSTOM_SECRET",
        "--base-url", "https://octane.example.test",
        "--shared-space-id", "1",
        "--workspace-id", "2",
        "--timeout", "3",
        "--skip-test",
    )
    assert result == 28
    assert calls == [{
        "username": "client",
        "secret_arg": "value",
        "secret_env": "CUSTOM_SECRET",
        "base_url_arg": "https://octane.example.test",
        "shared_space_id_arg": "1",
        "workspace_id_arg": "2",
        "timeout_arg": "3",
        "skip_test": True,
    }]
