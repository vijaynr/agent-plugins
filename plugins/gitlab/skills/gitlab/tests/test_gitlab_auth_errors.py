"""RED tests for Task 6: GitLab safety preservation and error taxonomy.

Profile lifecycle, migration, and locking are intentionally outside this file's
scope. All credential-store and HTTP boundaries use the shared fakes.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

import pytest

from .test_gitlab_credential_config import (
    KEYRING_USER,
    SELF_HOSTED_API,
    SENTINEL_TOKEN,
    SERVICE_NAME,
    FakeKeyring,
    FakeKeyringError,
    FakeRequests,
    isolated_runtime,
    load_script,
    profile_document,
    relocated_skill,
    write_profile,
)


def _load_restricted_client(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    isolated_runtime: tuple[Path, FakeKeyring, FakeRequests],
    install_name: str,
) -> tuple[Any, FakeKeyring, FakeRequests]:
    config_home, fake_keyring, fake_requests = isolated_runtime
    write_profile(config_home, profile_document())
    skill_root = relocated_skill(tmp_path, install_name)
    assert not (skill_root / ".env").exists()
    client = load_script(skill_root, "gitlab_cli", monkeypatch)
    return client, fake_keyring, fake_requests


def _invoke(client: Any, tool: str, params: dict[str, str]) -> int:
    with pytest.raises(SystemExit) as exc_info:
        client.request(tool, params, runtime=client.resolve_runtime_config())
    return int(exc_info.value.code)


def _error_payload(capsys: pytest.CaptureFixture[str]) -> dict[str, Any]:
    captured = capsys.readouterr()
    assert captured.err == ""
    return json.loads(captured.out)


@pytest.mark.parametrize("timeout", ["invalid", "0", "-1"])
def test_direct_credentials_reject_invalid_timeout_before_http(
    timeout: str,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    isolated_runtime: tuple[Path, FakeKeyring, FakeRequests],
    capsys: pytest.CaptureFixture[str],
) -> None:
    _, fake_keyring, fake_requests = isolated_runtime
    monkeypatch.setenv("GITLAB_API_URL", "https://gitlab.example.test/api/v4")
    monkeypatch.setenv("GITLAB_PERSONAL_ACCESS_TOKEN", "direct-token")
    monkeypatch.setenv("GITLAB_TIMEOUT", timeout)
    client = load_script(relocated_skill(tmp_path, f"invalid-timeout-{timeout}"), "gitlab_cli", monkeypatch)

    with pytest.raises(SystemExit):
        client.resolve_runtime_config()

    assert _error_payload(capsys)["error_code"] == "GITLAB_TIMEOUT_INVALID"
    assert fake_keyring.get_calls == []
    assert fake_requests.calls == []


def test_direct_credentials_reject_unsafe_endpoint_before_http(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    isolated_runtime: tuple[Path, FakeKeyring, FakeRequests],
    capsys: pytest.CaptureFixture[str],
) -> None:
    _, fake_keyring, fake_requests = isolated_runtime
    monkeypatch.setenv("GITLAB_API_URL", "http://gitlab.example.test/api/v4")
    monkeypatch.setenv("GITLAB_PERSONAL_ACCESS_TOKEN", "direct-token")
    client = load_script(relocated_skill(tmp_path, "unsafe-endpoint"), "gitlab_cli", monkeypatch)

    with pytest.raises(SystemExit):
        client.resolve_runtime_config()

    assert _error_payload(capsys)["error_code"] == "GITLAB_ENDPOINT_UNSAFE"
    assert fake_keyring.get_calls == []
    assert fake_requests.calls == []


@pytest.mark.parametrize("tool", ["list_issues", "list_projects", "create_repository"])
def test_selected_profile_allowlist_rejects_global_tools_before_credentials_or_http(
    tool: str,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    isolated_runtime: tuple[Path, FakeKeyring, FakeRequests],
    capsys: pytest.CaptureFixture[str],
) -> None:
    client, fake_keyring, fake_requests = _load_restricted_client(
        tmp_path, monkeypatch, isolated_runtime, f"restricted-global-{tool}"
    )

    exit_code = _invoke(client, tool, {"name": "blocked"} if tool == "create_repository" else {})

    payload = _error_payload(capsys)
    assert exit_code != 0
    assert payload["error_code"] == "GITLAB_PROJECT_SCOPE_REQUIRED"
    assert fake_keyring.get_calls == []
    assert fake_requests.calls == []


def test_selected_profile_read_only_setting_survives_no_dotenv_relocation_and_blocks_write_before_credentials_or_http(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    isolated_runtime: tuple[Path, FakeKeyring, FakeRequests],
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.setenv("GITLAB_READ_ONLY_MODE", "false")
    client, fake_keyring, fake_requests = _load_restricted_client(
        tmp_path, monkeypatch, isolated_runtime, "relocated-read-only"
    )

    exit_code = _invoke(client, "create_issue", {"project_id": "42", "title": "blocked"})

    payload = _error_payload(capsys)
    assert exit_code != 0
    assert client.resolve_runtime_config().read_only is True
    assert payload["error"] == "Tool 'create_issue' blocked by GITLAB_READ_ONLY_MODE"
    assert fake_keyring.get_calls == []
    assert fake_requests.calls == []


def test_selected_profile_allowlist_survives_no_dotenv_relocation_and_rejects_project_before_credentials_or_http(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    isolated_runtime: tuple[Path, FakeKeyring, FakeRequests],
    capsys: pytest.CaptureFixture[str],
) -> None:
    client, fake_keyring, fake_requests = _load_restricted_client(
        tmp_path, monkeypatch, isolated_runtime, "relocated-allowlist"
    )

    exit_code = _invoke(client, "get_project", {"project_id": "999"})

    payload = _error_payload(capsys)
    assert exit_code != 0
    assert client.resolve_runtime_config().allowed_project_ids == {"42", "84"}
    assert payload["error"] == "Project 999 not in GITLAB_ALLOWED_PROJECT_IDS"
    assert fake_keyring.get_calls == []
    assert fake_requests.calls == []


def test_missing_selected_keyring_entry_has_specific_machine_error_before_http_without_fallback(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    isolated_runtime: tuple[Path, FakeKeyring, FakeRequests],
    capsys: pytest.CaptureFixture[str],
) -> None:
    client, fake_keyring, fake_requests = _load_restricted_client(
        tmp_path, monkeypatch, isolated_runtime, "missing-keyring-entry"
    )

    exit_code = _invoke(client, "get_project", {"project_id": "42"})

    payload = _error_payload(capsys)
    serialized = json.dumps(payload)
    assert exit_code != 0
    assert payload["error_code"] == "GITLAB_KEYRING_ENTRY_MISSING"
    assert payload["error"] == "Selected GitLab keyring entry has no token"
    assert payload["keyring_user"] == KEYRING_USER
    assert fake_keyring.get_calls == [(SERVICE_NAME, KEYRING_USER)]
    assert fake_requests.calls == []
    assert "gitlab.com" not in serialized
    assert SENTINEL_TOKEN not in serialized


def test_keyring_backend_failure_has_distinct_machine_error_before_http_without_fallback(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    isolated_runtime: tuple[Path, FakeKeyring, FakeRequests],
    capsys: pytest.CaptureFixture[str],
) -> None:
    client, fake_keyring, fake_requests = _load_restricted_client(
        tmp_path, monkeypatch, isolated_runtime, "keyring-backend-failure"
    )

    def fail_get_password(service: str, username: str) -> str:
        fake_keyring.get_calls.append((service, username))
        raise FakeKeyringError("injected backend diagnostic")

    monkeypatch.setattr(client.keyring, "get_password", fail_get_password)
    exit_code = _invoke(client, "get_project", {"project_id": "42"})

    payload = _error_payload(capsys)
    assert exit_code != 0
    assert payload["error_code"] == "GITLAB_KEYRING_BACKEND_FAILURE"
    assert payload["error"] == "GitLab keyring backend could not read the selected entry"
    assert payload["keyring_user"] == KEYRING_USER
    assert payload["details"] == "injected backend diagnostic"
    assert fake_keyring.get_calls == [(SERVICE_NAME, KEYRING_USER)]
    assert fake_requests.calls == []


@pytest.mark.parametrize(
    ("status_code", "error_code", "message", "remote_message"),
    [
        (401, "GITLAB_REMOTE_AUTHENTICATION_FAILED", "GitLab authentication failed", "401 Unauthorized"),
        (403, "GITLAB_REMOTE_AUTHORIZATION_FAILED", "GitLab authorization failed", "403 Forbidden"),
    ],
)
def test_http_401_and_403_have_distinct_machine_codes_and_secret_safe_body_context(
    status_code: int,
    error_code: str,
    message: str,
    remote_message: str,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    isolated_runtime: tuple[Path, FakeKeyring, FakeRequests],
    capsys: pytest.CaptureFixture[str],
) -> None:
    client, fake_keyring, fake_requests = _load_restricted_client(
        tmp_path, monkeypatch, isolated_runtime, f"remote-{status_code}"
    )
    fake_keyring.passwords[(SERVICE_NAME, KEYRING_USER)] = SENTINEL_TOKEN

    class RejectedResponse:
        ok = False
        headers = {"content-type": "application/json"}
        text = json.dumps({"message": remote_message, "token": SENTINEL_TOKEN})
        content = text.encode()

        def __init__(self) -> None:
            self.status_code = status_code

        def json(self) -> dict[str, str]:
            return {"message": remote_message, "token": SENTINEL_TOKEN}

    def reject(method: str, url: str, **kwargs: Any) -> RejectedResponse:
        fake_requests.calls.append({"method": method, "url": url, **kwargs})
        return RejectedResponse()

    monkeypatch.setattr(client.requests, "request", reject)
    exit_code = _invoke(client, "get_project", {"project_id": "42"})

    payload = _error_payload(capsys)
    serialized = json.dumps(payload)
    assert exit_code != 0
    assert payload["error_code"] == error_code
    assert payload["error"] == message
    assert payload["status"] == status_code
    assert payload["response"]["message"] == remote_message
    assert SENTINEL_TOKEN not in serialized
    assert fake_keyring.get_calls == [(SERVICE_NAME, KEYRING_USER)]
    assert len(fake_requests.calls) == 1
    assert fake_requests.calls[0]["url"] == f"{SELF_HOSTED_API}/projects/42"


def test_profile_token_is_not_forwarded_to_an_alternate_host_redirect(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    isolated_runtime: tuple[Path, FakeKeyring, FakeRequests],
    capsys: pytest.CaptureFixture[str],
) -> None:
    client, fake_keyring, fake_requests = _load_restricted_client(
        tmp_path, monkeypatch, isolated_runtime, "alternate-host-redirect"
    )
    fake_keyring.passwords[(SERVICE_NAME, KEYRING_USER)] = SENTINEL_TOKEN
    alternate_url = "https://attacker.example/api/v4/projects"

    class RedirectResponse:
        ok = False
        status_code = 302
        headers = {"content-type": "application/json", "location": alternate_url}
        text = '{"message":"redirect refused"}'
        content = text.encode()

        def json(self) -> dict[str, str]:
            return {"message": "redirect refused"}

    def redirect(method: str, url: str, **kwargs: Any) -> RedirectResponse:
        fake_requests.calls.append({"method": method, "url": url, **kwargs})
        return RedirectResponse()

    monkeypatch.setattr(client.requests, "request", redirect)
    exit_code = _invoke(client, "get_project", {"project_id": "42"})

    payload = _error_payload(capsys)
    assert exit_code != 0
    assert len(fake_requests.calls) == 1
    call = fake_requests.calls[0]
    assert urlparse(call["url"]).hostname == "gitlab.internal.example"
    assert call["allow_redirects"] is False
    assert SENTINEL_TOKEN not in json.dumps(payload)
    assert fake_keyring.get_calls == [(SERVICE_NAME, KEYRING_USER)]
