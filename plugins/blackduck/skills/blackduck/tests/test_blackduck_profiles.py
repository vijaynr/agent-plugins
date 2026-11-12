"""RED tests for Task 8: Black Duck profile lifecycle and validation."""
from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

import pytest

from test_blackduck_credential_config import (
    BLACKDUCK_URL, KEYRING_USER, SENTINEL_TOKEN, SERVICE_NAME,
    FakeKeyring, isolated_runtime, load_script, profile_document,
    relocated_skill, write_profile,
)


def run_token(token: Any, monkeypatch: pytest.MonkeyPatch, *args: str) -> int:
    monkeypatch.setattr(sys, "argv", ["blackduck_token.py", *args])
    return token.main()


def login_args(profile: str, *extra: str) -> tuple[str, ...]:
    return (
        "login", "--profile", profile, "--user", f"{profile}-user",
        "--token", SENTINEL_TOKEN, "--url", f"https://{profile}.example.test/",
        "--verify-ssl", "false", "--skip-test", *extra,
    )


def profiles_document(active: str | None = "production") -> dict[str, Any]:
    return {
        "schema_version": 1,
        "active_profile": active,
        "profiles": {
            name: {
                "keyring_user": f"{name}-user",
                "endpoint": f"https://{name}.example.test",
                "settings": {"verify_ssl": verify},
            }
            for name, verify in (("zulu", "true"), ("production", "false"), ("alpha", "true"))
        },
    }


def test_named_login_preserves_profiles_and_activates_new_profile(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, isolated_runtime: tuple[Path, FakeKeyring]) -> None:
    config_home, keyring = isolated_runtime
    original = profile_document()
    write_profile(config_home, original)
    token = load_script(relocated_skill(tmp_path, "named"), "blackduck_token", monkeypatch)

    assert run_token(token, monkeypatch, *login_args("production")) == 0

    stored = json.loads((config_home / "blackduck.json").read_text(encoding="utf-8"))
    assert stored["active_profile"] == "production"
    assert stored["profiles"]["default"] == original["profiles"]["default"]
    assert stored["profiles"]["production"] == {
        "keyring_user": "production-user", "endpoint": "https://production.example.test",
        "settings": {"verify_ssl": "false"},
    }
    assert keyring.passwords[(SERVICE_NAME, "production-user")] == SENTINEL_TOKEN


def test_login_without_profile_updates_active_profile_and_process_values_override_legacy_env(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    isolated_runtime: tuple[Path, FakeKeyring],
) -> None:
    config_home, keyring = isolated_runtime
    write_profile(config_home, profiles_document())
    skill_root = relocated_skill(tmp_path, "active-login-precedence")
    (skill_root / ".env").write_text(
        "BLACKDUCK_URL=https://legacy.example.test\nBLACKDUCK_VERIFY_SSL=true\n",
        encoding="utf-8",
    )
    monkeypatch.setenv("BLACKDUCK_URL", "https://process.example.test/")
    token = load_script(skill_root, "blackduck_token", monkeypatch)

    assert run_token(token, monkeypatch, "login", "--token", SENTINEL_TOKEN, "--skip-test") == 0

    stored = json.loads((config_home / "blackduck.json").read_text(encoding="utf-8"))
    assert stored["active_profile"] == "production"
    assert stored["profiles"]["production"] == {
        "keyring_user": "production-user",
        "endpoint": "https://process.example.test",
        "settings": {"verify_ssl": "false"},
    }
    assert keyring.passwords[(SERVICE_NAME, "production-user")] == SENTINEL_TOKEN


def test_profiles_lists_sorted_names_and_active_without_reading_keyring(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str], isolated_runtime: tuple[Path, FakeKeyring]) -> None:
    config_home, keyring = isolated_runtime
    write_profile(config_home, profiles_document())
    token = load_script(relocated_skill(tmp_path, "list"), "blackduck_token", monkeypatch)

    assert run_token(token, monkeypatch, "profiles") == 0

    assert json.loads(capsys.readouterr().out) == {
        "ok": True, "data": {"active_profile": "production", "profiles": ["alpha", "production", "zulu"]}
    }
    assert keyring.get_calls == []


def test_use_profile_changes_only_active_selection(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, isolated_runtime: tuple[Path, FakeKeyring]) -> None:
    config_home, _ = isolated_runtime
    path = write_profile(config_home, profiles_document())
    before = json.loads(path.read_text(encoding="utf-8"))
    token = load_script(relocated_skill(tmp_path, "use"), "blackduck_token", monkeypatch)

    assert run_token(token, monkeypatch, "use-profile", "--profile", "zulu") == 0
    after = json.loads(path.read_text(encoding="utf-8"))
    assert after["active_profile"] == "zulu"
    assert after["profiles"] == before["profiles"]


@pytest.mark.parametrize("prior_active", ["default", None])
def test_no_activate_preserves_existing_active_selection(prior_active: str | None, tmp_path: Path, monkeypatch: pytest.MonkeyPatch, isolated_runtime: tuple[Path, FakeKeyring]) -> None:
    config_home, _ = isolated_runtime
    document = profile_document()
    document["active_profile"] = prior_active
    write_profile(config_home, document)
    token = load_script(relocated_skill(tmp_path, f"no-active-{prior_active}"), "blackduck_token", monkeypatch)

    assert run_token(token, monkeypatch, *login_args("staging", "--no-activate")) == 0
    stored = json.loads((config_home / "blackduck.json").read_text(encoding="utf-8"))
    assert stored["active_profile"] == prior_active
    assert "staging" in stored["profiles"]


def test_first_no_activate_login_leaves_active_unset(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, isolated_runtime: tuple[Path, FakeKeyring]) -> None:
    config_home, _ = isolated_runtime
    token = load_script(relocated_skill(tmp_path, "first-no-active"), "blackduck_token", monkeypatch)
    assert run_token(token, monkeypatch, *login_args("staging", "--no-activate")) == 0
    stored = json.loads((config_home / "blackduck.json").read_text(encoding="utf-8"))
    assert stored == {
        "schema_version": 1, "active_profile": None,
        "profiles": {"staging": {"keyring_user": "staging-user", "endpoint": "https://staging.example.test", "settings": {"verify_ssl": "false"}}},
    }


@pytest.mark.parametrize(
    ("deleted", "expected_active", "remaining"),
    [("zulu", "production", {"production", "alpha"}), ("production", "alpha", {"alpha", "zulu"})],
)
def test_delete_profile_removes_only_metadata_and_selects_active_lexically(deleted: str, expected_active: str, remaining: set[str], tmp_path: Path, monkeypatch: pytest.MonkeyPatch, isolated_runtime: tuple[Path, FakeKeyring]) -> None:
    config_home, keyring = isolated_runtime
    document = profiles_document()
    write_profile(config_home, document)
    user = document["profiles"][deleted]["keyring_user"]
    keyring.passwords[(SERVICE_NAME, user)] = SENTINEL_TOKEN
    token = load_script(relocated_skill(tmp_path, f"delete-{deleted}"), "blackduck_token", monkeypatch)

    assert run_token(token, monkeypatch, "delete-profile", "--profile", deleted) == 0
    stored = json.loads((config_home / "blackduck.json").read_text(encoding="utf-8"))
    assert stored["active_profile"] == expected_active
    assert set(stored["profiles"]) == remaining
    assert keyring.passwords[(SERVICE_NAME, user)] == SENTINEL_TOKEN
    assert keyring.delete_calls == []


def test_delete_final_profile_leaves_empty_document_and_never_deletes_keyring(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, isolated_runtime: tuple[Path, FakeKeyring]) -> None:
    config_home, keyring = isolated_runtime
    write_profile(config_home)
    keyring.passwords[(SERVICE_NAME, KEYRING_USER)] = SENTINEL_TOKEN
    token = load_script(relocated_skill(tmp_path, "delete-final"), "blackduck_token", monkeypatch)

    assert run_token(token, monkeypatch, "delete-profile", "--profile", "default") == 0
    assert json.loads((config_home / "blackduck.json").read_text()) == {"schema_version": 1, "active_profile": None, "profiles": {}}
    assert keyring.passwords[(SERVICE_NAME, KEYRING_USER)] == SENTINEL_TOKEN
    assert keyring.delete_calls == []


@pytest.mark.parametrize("name", ["", " leading", "trailing ", ".hidden", "slash/name", "back\\slash", "name!", "a" * 65])
def test_unsafe_profile_names_are_rejected(name: str, tmp_path: Path, monkeypatch: pytest.MonkeyPatch, isolated_runtime: tuple[Path, FakeKeyring]) -> None:
    config = load_script(relocated_skill(tmp_path, "invalid-name"), "credential_config", monkeypatch)
    document = profile_document()
    document["profiles"] = {name: document["profiles"]["default"]}
    document["active_profile"] = name
    with pytest.raises(config.ConfigError, match="profile"):
        config.validate_document(document)


@pytest.mark.parametrize("document", [
    {},
    {"schema_version": 2, "active_profile": None, "profiles": {}},
    {"schema_version": 1, "active_profile": "missing", "profiles": {}},
    {"schema_version": 1, "active_profile": None, "profiles": []},
    {"schema_version": 1, "active_profile": "default", "profiles": {"default": None}},
    {"schema_version": 1, "active_profile": "default", "profiles": {"default": {"keyring_user": KEYRING_USER, "settings": {"verify_ssl": "true"}}}},
    {"schema_version": 1, "active_profile": "default", "profiles": {"default": {"endpoint": BLACKDUCK_URL, "settings": {"verify_ssl": "true"}}}},
])
def test_invalid_documents_fail_closed_without_mutation(document: dict[str, Any], tmp_path: Path, monkeypatch: pytest.MonkeyPatch, isolated_runtime: tuple[Path, FakeKeyring]) -> None:
    config_home, _ = isolated_runtime
    config_home.mkdir(parents=True, exist_ok=True)
    path = config_home / "blackduck.json"
    path.write_text(json.dumps(document), encoding="utf-8")
    before = path.read_bytes()
    token = load_script(relocated_skill(tmp_path, "invalid-document"), "blackduck_token", monkeypatch)
    assert run_token(token, monkeypatch, "use-profile", "--profile", "default") != 0
    assert path.read_bytes() == before


@pytest.mark.parametrize("raw", [b"", b"{not-json"])
def test_empty_or_malformed_documents_fail_without_mutation(raw: bytes, tmp_path: Path, monkeypatch: pytest.MonkeyPatch, isolated_runtime: tuple[Path, FakeKeyring]) -> None:
    config_home, _ = isolated_runtime
    config_home.mkdir(parents=True, exist_ok=True)
    path = config_home / "blackduck.json"
    path.write_bytes(raw)
    token = load_script(relocated_skill(tmp_path, "malformed"), "blackduck_token", monkeypatch)
    assert run_token(token, monkeypatch, "delete-profile", "--profile", "default") != 0
    assert path.read_bytes() == raw


@pytest.mark.parametrize("settings", [None, [], {}, {"verify_ssl": True}, {"verify_ssl": "TRUE"}, {"verify_ssl": "yes"}, {"verify_ssl": "false", "unknown": "x"}])
def test_verify_ssl_settings_are_strictly_validated(settings: Any, tmp_path: Path, monkeypatch: pytest.MonkeyPatch, isolated_runtime: tuple[Path, FakeKeyring]) -> None:
    config = load_script(relocated_skill(tmp_path, "invalid-settings"), "credential_config", monkeypatch)
    document = profile_document()
    document["profiles"]["default"]["settings"] = settings
    with pytest.raises(config.ConfigError, match="settings|verify_ssl"):
        config.validate_document(document)


@pytest.mark.parametrize("verify", ["true", "false"])
def test_lowercase_verify_ssl_literals_are_valid(verify: str, tmp_path: Path, monkeypatch: pytest.MonkeyPatch, isolated_runtime: tuple[Path, FakeKeyring]) -> None:
    config = load_script(relocated_skill(tmp_path, f"valid-{verify}"), "credential_config", monkeypatch)
    document = profile_document(verify_ssl=verify)
    assert config.validate_document(document) == document


@pytest.mark.parametrize("action", ["use-profile", "delete-profile"])
def test_missing_profile_fails_without_mutation(action: str, tmp_path: Path, monkeypatch: pytest.MonkeyPatch, isolated_runtime: tuple[Path, FakeKeyring]) -> None:
    config_home, _ = isolated_runtime
    path = write_profile(config_home)
    before = path.read_bytes()
    token = load_script(relocated_skill(tmp_path, f"missing-{action}"), "blackduck_token", monkeypatch)
    assert run_token(token, monkeypatch, action, "--profile", "missing") != 0
    assert path.read_bytes() == before


def test_retained_defaults_save_get_delete_and_setup_dispatch(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, isolated_runtime: tuple[Path, FakeKeyring]) -> None:
    token = load_script(relocated_skill(tmp_path, "compat"), "blackduck_token", monkeypatch)
    calls: list[Any] = []
    monkeypatch.setattr(token, "print_login_defaults", lambda: 21)
    assert run_token(token, monkeypatch, "defaults") == 21
    monkeypatch.setattr(token, "save_token", lambda user, value: calls.append(("save", user, value)) or 22)
    assert run_token(token, monkeypatch, "save", "--user", "user", "--token", "value", "--token-env", "CUSTOM") == 22
    monkeypatch.setattr(token, "get_token", lambda user, show: calls.append(("get", user, show)) or 23)
    assert run_token(token, monkeypatch, "get", "--user", "user", "--show") == 23
    monkeypatch.setattr(token, "delete_token", lambda user: calls.append(("delete", user)) or 24)
    assert run_token(token, monkeypatch, "delete", "--user", "user") == 24
    monkeypatch.setattr(token, "setup_token", lambda *args: calls.append(("setup", *args)) or 25)
    assert run_token(token, monkeypatch, "setup", "--user", "user", "--token", "value", "--token-env", "CUSTOM", "--url", BLACKDUCK_URL, "--verify-ssl", "false", "--write-secret-to-env") == 25
    assert calls == [
        ("save", "user", "value"), ("get", "user", True), ("delete", "user"),
        ("setup", "user", "value", "CUSTOM", BLACKDUCK_URL, "false", True),
    ]


def test_login_parser_forwards_profile_no_activate_and_retained_flags(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, isolated_runtime: tuple[Path, FakeKeyring]) -> None:
    token = load_script(relocated_skill(tmp_path, "flags"), "blackduck_token", monkeypatch)
    calls: list[dict[str, Any]] = []
    monkeypatch.setattr(token, "login", lambda **kwargs: calls.append(kwargs) or 29)
    assert run_token(token, monkeypatch, *login_args("staging", "--no-activate")) == 29
    assert calls == [{
        "username": "staging-user", "token_arg": SENTINEL_TOKEN, "token_env": "BLACKDUCK_LOGIN_TOKEN",
        "url_arg": "https://staging.example.test/", "verify_ssl_arg": "false", "skip_test": True,
        "profile_name": "staging", "activate": False,
    }]
