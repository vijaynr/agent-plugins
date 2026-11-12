"""RED tests for Task 3: actionable, secret-safe Octane authentication errors."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from test_octane_credential_config import (
    SENTINEL_SECRET,
    SERVICE_NAME,
    FakeKeyring,
    FakeKeyringError,
    FakeSession,
    isolated_runtime,
    load_script,
    relocated_skill,
    write_profile,
)


def _load_profile_client(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    isolated_runtime: tuple[Path, FakeKeyring],
    install_name: str,
) -> tuple[Any, FakeKeyring]:
    config_home, fake_keyring = isolated_runtime
    write_profile(config_home)
    client = load_script(relocated_skill(tmp_path, install_name), "octane_client", monkeypatch)
    client.configure_runtime(client.resolve_runtime_config())
    return client, fake_keyring


def _error_payload(capsys: pytest.CaptureFixture[str]) -> dict[str, Any]:
    output = capsys.readouterr()
    assert output.err == ""
    return json.loads(output.out)


@pytest.mark.parametrize("timeout", ["invalid", "0", "-1"])
def test_direct_credentials_reject_invalid_timeout_before_http(
    timeout: str,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    isolated_runtime: tuple[Path, FakeKeyring],
    capsys: pytest.CaptureFixture[str],
) -> None:
    _, fake_keyring = isolated_runtime
    monkeypatch.setenv("OCTANE_BASE_URL", "https://octane.example.test")
    monkeypatch.setenv("OCTANE_CLIENT_ID", "direct-client")
    monkeypatch.setenv("OCTANE_CLIENT_SECRET", "direct-secret")
    monkeypatch.setenv("OCTANE_TIMEOUT", timeout)
    client = load_script(relocated_skill(tmp_path, f"invalid-timeout-{timeout}"), "octane_client", monkeypatch)

    with pytest.raises(SystemExit):
        client.resolve_runtime_config()

    assert _error_payload(capsys)["error_code"] == "OCTANE_TIMEOUT_INVALID"
    assert fake_keyring.get_calls == []
    assert FakeSession.instances == []


def test_direct_credentials_reject_unsafe_endpoint_before_http(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    isolated_runtime: tuple[Path, FakeKeyring],
    capsys: pytest.CaptureFixture[str],
) -> None:
    _, fake_keyring = isolated_runtime
    monkeypatch.setenv("OCTANE_BASE_URL", "http://octane.example.test")
    monkeypatch.setenv("OCTANE_CLIENT_ID", "direct-client")
    monkeypatch.setenv("OCTANE_CLIENT_SECRET", "direct-secret")
    client = load_script(relocated_skill(tmp_path, "unsafe-endpoint"), "octane_client", monkeypatch)

    with pytest.raises(SystemExit):
        client.resolve_runtime_config()

    assert _error_payload(capsys)["error_code"] == "OCTANE_ENDPOINT_UNSAFE"
    assert fake_keyring.get_calls == []
    assert FakeSession.instances == []


def test_authentication_refuses_redirects_before_sending_credentials(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    isolated_runtime: tuple[Path, FakeKeyring],
) -> None:
    client, fake_keyring = _load_profile_client(
        tmp_path, monkeypatch, isolated_runtime, "authentication-redirect"
    )
    fake_keyring.passwords[(SERVICE_NAME, "client-id")] = SENTINEL_SECRET

    class RedirectResponse:
        ok = False
        status_code = 307
        headers = {"location": "https://attacker.example.test/sign-in"}
        text = "redirect"

    monkeypatch.setattr(
        FakeSession,
        "post",
        lambda session, url, **kwargs: (
            session.posts.append({"url": url, **kwargs}) or RedirectResponse()
        ),
    )

    with pytest.raises(SystemExit):
        client.get_session()

    assert FakeSession.instances[-1].posts[0]["allow_redirects"] is False


def test_authenticated_json_and_multipart_requests_refuse_redirects(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    isolated_runtime: tuple[Path, FakeKeyring],
) -> None:
    client, fake_keyring = _load_profile_client(
        tmp_path, monkeypatch, isolated_runtime, "authenticated-redirects"
    )
    fake_keyring.passwords[(SERVICE_NAME, "client-id")] = SENTINEL_SECRET

    client.request_json("GET", "https://octane.example.test/api/items")
    client.request_multipart("https://octane.example.test/api/attachments", {"file": object()})

    session = FakeSession.instances[-1]
    assert session.requests[0]["allow_redirects"] is False
    assert session.posts[1]["allow_redirects"] is False


def test_missing_selected_keyring_entry_fails_before_http_with_specific_machine_error(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    isolated_runtime: tuple[Path, FakeKeyring],
    capsys: pytest.CaptureFixture[str],
) -> None:
    client, fake_keyring = _load_profile_client(
        tmp_path, monkeypatch, isolated_runtime, "missing-keyring-entry"
    )

    with pytest.raises(SystemExit) as exc_info:
        client.get_session()

    payload = _error_payload(capsys)
    assert exc_info.value.code != 0
    assert payload["error_code"] == "OCTANE_KEYRING_ENTRY_MISSING"
    assert payload["error"] == "Selected Octane keyring entry has no client secret"
    assert payload["keyring_user"] == "client-id"
    assert fake_keyring.get_calls == [(SERVICE_NAME, "client-id")]
    assert FakeSession.instances == []


def test_keyring_backend_failure_fails_before_http_with_distinct_machine_error(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    isolated_runtime: tuple[Path, FakeKeyring],
    capsys: pytest.CaptureFixture[str],
) -> None:
    client, fake_keyring = _load_profile_client(
        tmp_path, monkeypatch, isolated_runtime, "keyring-backend-failure"
    )

    def fail_get_password(service: str, username: str) -> str:
        fake_keyring.get_calls.append((service, username))
        raise FakeKeyringError("injected backend diagnostic")

    monkeypatch.setattr(client.keyring, "get_password", fail_get_password)

    with pytest.raises(SystemExit) as exc_info:
        client.get_session()

    payload = _error_payload(capsys)
    assert exc_info.value.code != 0
    assert payload["error_code"] == "OCTANE_KEYRING_BACKEND_FAILURE"
    assert payload["error"] == "Octane keyring backend could not read the selected entry"
    assert payload["keyring_user"] == "client-id"
    assert payload["details"] == "injected backend diagnostic"
    assert fake_keyring.get_calls == [(SERVICE_NAME, "client-id")]
    assert FakeSession.instances == []


@pytest.mark.parametrize(
    ("status_code", "error_code", "message"),
    [
        (401, "OCTANE_REMOTE_AUTHENTICATION_FAILED", "Octane authentication failed"),
        (403, "OCTANE_REMOTE_AUTHORIZATION_FAILED", "Octane authorization failed"),
    ],
)
def test_authentication_http_401_and_403_have_distinct_secret_safe_classifications(
    status_code: int,
    error_code: str,
    message: str,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    isolated_runtime: tuple[Path, FakeKeyring],
    capsys: pytest.CaptureFixture[str],
) -> None:
    client, fake_keyring = _load_profile_client(
        tmp_path, monkeypatch, isolated_runtime, f"remote-auth-{status_code}"
    )
    fake_keyring.passwords[(SERVICE_NAME, "client-id")] = SENTINEL_SECRET

    class AuthenticationFailureResponse:
        ok = False
        headers = {"content-type": "application/json"}
        text = json.dumps({"diagnostic": f"rejected {SENTINEL_SECRET}"})

        def __init__(self) -> None:
            self.status_code = status_code

        def json(self) -> dict[str, str]:
            return {"diagnostic": f"rejected {SENTINEL_SECRET}"}

    monkeypatch.setattr(
        FakeSession,
        "post",
        lambda session, url, **kwargs: (
            session.posts.append({"url": url, **kwargs}) or AuthenticationFailureResponse()
        ),
    )

    with pytest.raises(SystemExit) as exc_info:
        client.get_session()

    payload = _error_payload(capsys)
    serialized = json.dumps(payload)
    assert exc_info.value.code != 0
    assert payload["error_code"] == error_code
    assert payload["error"] == message
    assert payload["status"] == status_code
    assert payload["url"] == "https://octane.example.test/authentication/sign_in"
    assert "response" not in payload
    assert SENTINEL_SECRET not in serialized
    assert fake_keyring.get_calls == [(SERVICE_NAME, "client-id")]
    assert len(FakeSession.instances) == 1
    assert len(FakeSession.instances[0].posts) == 1
    assert FakeSession.instances[0].requests == []
