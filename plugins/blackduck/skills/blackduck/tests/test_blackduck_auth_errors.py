"""RED tests for Task 9: Black Duck credential and authorization errors.

Profile lifecycle, migration, and locking are intentionally outside this file's
scope. All credential-store and HTTP boundaries reuse the Task 7 fakes.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

import pytest

from test_blackduck_credential_config import (
    BLACKDUCK_URL,
    KEYRING_USER,
    SENTINEL_TOKEN,
    SERVICE_NAME,
    FakeKeyring,
    FakeKeyringError,
    FakeResponse,
    FakeSession,
    isolated_runtime,
    load_script,
    relocated_skill,
    write_profile,
)

ALTERNATE_URL = "https://alternate-host.invalid/api/tokens/authenticate"


def _load_profile_client(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    isolated_runtime: tuple[Path, FakeKeyring],
    install_name: str,
) -> tuple[Any, Path, FakeKeyring]:
    config_home, fake_keyring = isolated_runtime
    write_profile(config_home)
    skill_root = relocated_skill(tmp_path, install_name)
    assert not (skill_root / ".env").exists()
    client = load_script(skill_root, "blackduck_vulnerabilities", monkeypatch)
    return client, config_home, fake_keyring


def _invoke_list_projects(client: Any) -> int:
    with pytest.raises(SystemExit) as exc_info:
        client.main(["list-projects", "--limit", "1"])
    return int(exc_info.value.code)


def _error_payload(capsys: pytest.CaptureFixture[str]) -> dict[str, Any]:
    captured = capsys.readouterr()
    assert captured.err == ""
    return json.loads(captured.out)


def _assert_no_secret_in_json_or_temp_metadata(
    payload: dict[str, Any],
    tmp_path: Path,
) -> None:
    assert SENTINEL_TOKEN not in json.dumps(payload)
    for path in tmp_path.rglob("*"):
        if path.is_file() and (path.suffix in {".json", ".tmp"} or path.name.endswith(".json.lock")):
            assert SENTINEL_TOKEN.encode() not in path.read_bytes(), path


def test_direct_credentials_reject_unsafe_endpoint_before_session(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    isolated_runtime: tuple[Path, FakeKeyring],
    capsys: pytest.CaptureFixture[str],
) -> None:
    _, fake_keyring = isolated_runtime
    monkeypatch.setenv("BLACKDUCK_URL", "http://blackduck.example.test")
    monkeypatch.setenv("BLACKDUCK_TOKEN", "direct-token")
    client = load_script(relocated_skill(tmp_path, "unsafe-endpoint"), "blackduck_vulnerabilities", monkeypatch)

    with pytest.raises(SystemExit):
        client.resolve_runtime_config()

    assert _error_payload(capsys)["error_code"] == "BLACKDUCK_ENDPOINT_UNSAFE"
    assert fake_keyring.get_calls == []
    assert FakeSession.instances == []


def test_authenticated_requests_refuse_redirects_and_off_origin_links(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    isolated_runtime: tuple[Path, FakeKeyring],
) -> None:
    client, _, fake_keyring = _load_profile_client(
        tmp_path, monkeypatch, isolated_runtime, "authenticated-origin"
    )
    fake_keyring.passwords[(SERVICE_NAME, KEYRING_USER)] = SENTINEL_TOKEN
    bd = client.session(client.resolve_runtime_config())

    bd.get("/api/projects")
    with pytest.raises(SystemExit):
        bd.url("https://attacker.example.test/api/projects")

    assert FakeSession.instances[-1].gets[0]["allow_redirects"] is False
    assert len(FakeSession.instances[-1].gets) == 1


def test_missing_profile_metadata_has_specific_machine_error_before_keyring_or_session(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    isolated_runtime: tuple[Path, FakeKeyring],
    capsys: pytest.CaptureFixture[str],
) -> None:
    config_home, fake_keyring = isolated_runtime
    client = load_script(
        relocated_skill(tmp_path, "missing-profile-metadata"),
        "blackduck_vulnerabilities",
        monkeypatch,
    )

    exit_code = _invoke_list_projects(client)

    payload = _error_payload(capsys)
    assert exit_code != 0
    assert payload["error_code"] == "BLACKDUCK_PROFILE_METADATA_MISSING"
    assert payload["error"] == "Black Duck profile metadata is missing"
    assert payload["config_path"] == str(config_home / "blackduck.json")
    assert fake_keyring.get_calls == []
    assert FakeSession.instances == []
    _assert_no_secret_in_json_or_temp_metadata(payload, tmp_path)


def test_malformed_ssl_value_fails_before_keyring_or_session(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    isolated_runtime: tuple[Path, FakeKeyring],
    capsys: pytest.CaptureFixture[str],
) -> None:
    _, fake_keyring = isolated_runtime
    monkeypatch.setenv("BLACKDUCK_URL", BLACKDUCK_URL)
    monkeypatch.setenv("BLACKDUCK_TOKEN_KEYRING_USER", KEYRING_USER)
    monkeypatch.setenv("BLACKDUCK_VERIFY_SSL", "treu")
    client = load_script(
        relocated_skill(tmp_path, "malformed-ssl"),
        "blackduck_vulnerabilities",
        monkeypatch,
    )

    exit_code = _invoke_list_projects(client)

    payload = _error_payload(capsys)
    assert exit_code != 0
    assert payload["error_code"] == "BLACKDUCK_SSL_CONFIGURATION_INVALID"
    assert payload["error"] == "BLACKDUCK_VERIFY_SSL must be a recognized boolean value"
    assert fake_keyring.get_calls == []
    assert FakeSession.instances == []


def test_missing_selected_keyring_token_has_specific_machine_error_before_session_without_fallback(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    isolated_runtime: tuple[Path, FakeKeyring],
    capsys: pytest.CaptureFixture[str],
) -> None:
    client, _, fake_keyring = _load_profile_client(
        tmp_path, monkeypatch, isolated_runtime, "missing-selected-keyring-token"
    )

    exit_code = _invoke_list_projects(client)

    payload = _error_payload(capsys)
    serialized = json.dumps(payload)
    assert exit_code != 0
    assert payload["error_code"] == "BLACKDUCK_KEYRING_ENTRY_MISSING"
    assert payload["error"] == "Selected Black Duck keyring entry has no token"
    assert payload["keyring_user"] == KEYRING_USER
    assert fake_keyring.get_calls == [(SERVICE_NAME, KEYRING_USER)]
    assert FakeSession.instances == []
    assert "alternate-host.invalid" not in serialized
    _assert_no_secret_in_json_or_temp_metadata(payload, tmp_path)


def test_keyring_backend_read_failure_has_distinct_machine_error_before_session_without_fallback(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    isolated_runtime: tuple[Path, FakeKeyring],
    capsys: pytest.CaptureFixture[str],
) -> None:
    client, _, fake_keyring = _load_profile_client(
        tmp_path, monkeypatch, isolated_runtime, "keyring-backend-read-failure"
    )

    def fail_get_password(service: str, username: str) -> str:
        fake_keyring.get_calls.append((service, username))
        raise FakeKeyringError("injected backend diagnostic")

    monkeypatch.setattr(client.keyring, "get_password", fail_get_password)
    exit_code = _invoke_list_projects(client)

    payload = _error_payload(capsys)
    assert exit_code != 0
    assert payload["error_code"] == "BLACKDUCK_KEYRING_BACKEND_FAILURE"
    assert payload["error"] == "Black Duck keyring backend could not read the selected entry"
    assert payload["keyring_user"] == KEYRING_USER
    assert payload["details"] == "injected backend diagnostic"
    assert fake_keyring.get_calls == [(SERVICE_NAME, KEYRING_USER)]
    assert FakeSession.instances == []
    _assert_no_secret_in_json_or_temp_metadata(payload, tmp_path)


@pytest.mark.parametrize(
    ("status_code", "error_code", "message", "remote_message"),
    [
        (
            401,
            "BLACKDUCK_REMOTE_AUTHENTICATION_FAILED",
            "Black Duck authentication failed",
            "401 Unauthorized",
        ),
        (
            403,
            "BLACKDUCK_REMOTE_AUTHORIZATION_FAILED",
            "Black Duck authorization failed",
            "403 Forbidden",
        ),
    ],
)
def test_authentication_401_and_403_have_distinct_codes_and_secret_safe_response_context(
    status_code: int,
    error_code: str,
    message: str,
    remote_message: str,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    isolated_runtime: tuple[Path, FakeKeyring],
    capsys: pytest.CaptureFixture[str],
) -> None:
    client, _, fake_keyring = _load_profile_client(
        tmp_path, monkeypatch, isolated_runtime, f"remote-auth-{status_code}"
    )
    fake_keyring.passwords[(SERVICE_NAME, KEYRING_USER)] = SENTINEL_TOKEN

    def reject_authentication(session: FakeSession, url: str, **kwargs: Any) -> FakeResponse:
        session.posts.append({"url": url, **kwargs})
        return FakeResponse(
            {"message": remote_message, "token": SENTINEL_TOKEN},
            headers={"content-type": "application/json"},
            status_code=status_code,
        )

    monkeypatch.setattr(FakeSession, "post", reject_authentication)
    exit_code = _invoke_list_projects(client)

    payload = _error_payload(capsys)
    assert exit_code != 0
    assert payload["error_code"] == error_code
    assert payload["error"] == message
    assert payload["status"] == status_code
    assert payload["url"] == f"{BLACKDUCK_URL}/api/tokens/authenticate"
    assert payload["response"]["message"] == remote_message
    assert "token" not in payload["response"]
    assert fake_keyring.get_calls == [(SERVICE_NAME, KEYRING_USER)]
    assert len(FakeSession.instances) == 1
    assert len(FakeSession.instances[0].posts) == 1
    assert FakeSession.instances[0].gets == []
    _assert_no_secret_in_json_or_temp_metadata(payload, tmp_path)


def test_authentication_refuses_redirect_and_never_sends_profile_token_to_alternate_host(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    isolated_runtime: tuple[Path, FakeKeyring],
    capsys: pytest.CaptureFixture[str],
) -> None:
    client, _, fake_keyring = _load_profile_client(
        tmp_path, monkeypatch, isolated_runtime, "alternate-host-redirect"
    )
    fake_keyring.passwords[(SERVICE_NAME, KEYRING_USER)] = SENTINEL_TOKEN

    def redirect_authentication(session: FakeSession, url: str, **kwargs: Any) -> FakeResponse:
        session.posts.append({"url": url, **kwargs})
        if kwargs.get("allow_redirects", True):
            session.posts.append({"url": ALTERNATE_URL, **kwargs})
        return FakeResponse(
            {"message": "redirect refused"},
            headers={"content-type": "application/json", "location": ALTERNATE_URL},
            status_code=302,
        )

    monkeypatch.setattr(FakeSession, "post", redirect_authentication)
    exit_code = _invoke_list_projects(client)

    payload = _error_payload(capsys)
    assert exit_code != 0
    assert len(FakeSession.instances) == 1
    session = FakeSession.instances[0]
    assert len(session.posts) == 1
    call = session.posts[0]
    assert urlparse(call["url"]).hostname == "blackduck.internal.example"
    assert call["allow_redirects"] is False
    assert all(urlparse(item["url"]).hostname != "alternate-host.invalid" for item in session.posts)
    assert session.gets == []
    assert fake_keyring.get_calls == [(SERVICE_NAME, KEYRING_USER)]
    _assert_no_secret_in_json_or_temp_metadata(payload, tmp_path)
