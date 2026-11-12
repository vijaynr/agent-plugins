"""RED tests for Task 5b: GitLab profile selection and credential provenance.

Migration, locking, and HTTP error taxonomy are intentionally outside this
file's scope.
"""
from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

import pytest

from .test_gitlab_credential_config import (
    SERVICE_NAME,
    FakeKeyring,
    FakeRequests,
    isolated_runtime,
    load_script,
    relocated_skill,
    write_profile,
)
from .test_gitlab_profiles import multiple_profile_document


def run_list_projects(
    skill_root: Path,
    monkeypatch: pytest.MonkeyPatch,
    profile: str | None = None,
) -> tuple[Any | None, int]:
    arguments = ["gitlab_cli.py"]
    if profile is not None:
        arguments.extend(("--profile", profile))
    arguments.append("get_project")
    monkeypatch.setattr(sys, "argv", arguments)

    client = None
    with pytest.raises(SystemExit) as exc_info:
        client = load_script(skill_root, "gitlab_cli", monkeypatch)
        client.main()
    if client is not None and exc_info.value.code == 0:
        client.runtime = client.resolve_runtime_config(profile)
    return client, int(exc_info.value.code)


@pytest.mark.parametrize(
    ("cli_profile", "environment_profile", "expected_profile"),
    [
        ("zulu", "alpha", "zulu"),
        (None, "alpha", "alpha"),
        (None, None, "production"),
    ],
)
def test_cli_profile_then_environment_profile_then_active_profile_selects_one_coherent_configuration(
    cli_profile: str | None,
    environment_profile: str | None,
    expected_profile: str,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    isolated_runtime: tuple[Path, FakeKeyring, FakeRequests],
) -> None:
    config_home, fake_keyring, fake_requests = isolated_runtime
    document = multiple_profile_document()
    write_profile(config_home, document)
    for name, profile in document["profiles"].items():
        fake_keyring.passwords[(SERVICE_NAME, profile["keyring_user"])] = f"{name}-token"
    if environment_profile is not None:
        monkeypatch.setenv("GITLAB_PROFILE", environment_profile)

    client, exit_code = run_list_projects(
        relocated_skill(tmp_path, f"selection-{expected_profile}"),
        monkeypatch,
        cli_profile,
    )

    selected = document["profiles"][expected_profile]
    settings = selected["settings"]
    assert exit_code == 0
    assert client is not None
    assert client.runtime.base_url == selected["endpoint"]
    assert client.runtime.default_project_id == settings["project_id"]
    assert client.runtime.allowed_project_ids == set(settings["allowed_project_ids"].split(","))
    assert client.runtime.read_only is (settings["read_only_mode"] == "true")
    assert client.runtime.timeout == int(settings["timeout"])
    assert fake_keyring.get_calls == [(SERVICE_NAME, selected["keyring_user"])]
    assert fake_requests.calls == [{
        "method": "GET",
        "url": f"{selected['endpoint']}/projects/{settings['project_id']}",
        "headers": {"PRIVATE-TOKEN": f"{expected_profile}-token", "Accept": "application/json"},
        "params": {},
        "json": None,
        "files": None,
        "timeout": int(settings["timeout"]),
        "allow_redirects": False,
    }]


def test_selected_profile_ignores_conflicting_legacy_dotenv_credentials_and_safety_settings(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    isolated_runtime: tuple[Path, FakeKeyring, FakeRequests],
) -> None:
    config_home, fake_keyring, fake_requests = isolated_runtime
    document = multiple_profile_document()
    write_profile(config_home, document)
    selected = document["profiles"]["production"]
    fake_keyring.passwords[(SERVICE_NAME, selected["keyring_user"])] = "production-token"
    skill_root = relocated_skill(tmp_path, "conflicting-dotenv")
    (skill_root / ".env").write_text(
        "GITLAB_API_URL=https://wrong-host.example/api/v4\n"
        "GITLAB_TOKEN_KEYRING_USER=wrong-user\n"
        "GITLAB_READ_ONLY_MODE=false\n"
        "GITLAB_ALLOWED_PROJECT_IDS=999\n",
        encoding="utf-8",
    )

    client, exit_code = run_list_projects(skill_root, monkeypatch)

    assert exit_code == 0
    assert client.runtime.base_url == selected["endpoint"]
    assert client.runtime.token_keyring_user == selected["keyring_user"]
    assert client.runtime.read_only is True
    assert client.runtime.allowed_project_ids == set(selected["settings"]["allowed_project_ids"].split(","))
    assert fake_keyring.get_calls == [(SERVICE_NAME, selected["keyring_user"])]
    assert fake_requests.calls[0]["url"] == f"{selected['endpoint']}/projects/{selected['settings']['project_id']}"


def test_complete_direct_endpoint_and_token_use_only_process_settings_and_defaults(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    isolated_runtime: tuple[Path, FakeKeyring, FakeRequests],
) -> None:
    config_home, fake_keyring, fake_requests = isolated_runtime
    document = multiple_profile_document()
    write_profile(config_home, document)
    fake_keyring.passwords[(SERVICE_NAME, "production-user")] = "production-token"
    monkeypatch.setenv("GITLAB_API_URL", "https://ci-gitlab.example.test/api/v4/")
    monkeypatch.setenv("GITLAB_PERSONAL_ACCESS_TOKEN", "glpat-direct-ci-token")
    monkeypatch.setenv("GITLAB_PROJECT_ID", "99")
    monkeypatch.setenv("GITLAB_TIMEOUT", "9")

    client, exit_code = run_list_projects(
        relocated_skill(tmp_path, "complete-direct-override"),
        monkeypatch,
    )

    assert exit_code == 0
    assert client is not None
    assert client.runtime.base_url == "https://ci-gitlab.example.test/api/v4"
    assert client.runtime.default_project_id == "99"
    assert client.runtime.allowed_project_ids == set()
    assert client.runtime.read_only is False
    assert client.runtime.timeout == 9
    assert fake_keyring.get_calls == []
    assert fake_requests.calls[0]["headers"]["PRIVATE-TOKEN"] == "glpat-direct-ci-token"
    assert fake_requests.calls[0]["url"] == "https://ci-gitlab.example.test/api/v4/projects/99"


def test_complete_process_credentials_bypass_malformed_durable_metadata(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    isolated_runtime: tuple[Path, FakeKeyring, FakeRequests],
) -> None:
    config_home, fake_keyring, fake_requests = isolated_runtime
    config_home.mkdir(parents=True, exist_ok=True)
    (config_home / "gitlab.json").write_text("{malformed", encoding="utf-8")
    monkeypatch.setenv("GITLAB_API_URL", "https://ci-gitlab.example.test/api/v4")
    monkeypatch.setenv("GITLAB_PERSONAL_ACCESS_TOKEN", "glpat-ci-token")
    monkeypatch.setenv("GITLAB_PROJECT_ID", "42")

    client, exit_code = run_list_projects(relocated_skill(tmp_path, "malformed-bypass"), monkeypatch)

    assert exit_code == 0
    assert client is not None
    assert client.runtime.allowed_project_ids == set()
    assert fake_keyring.get_calls == []
    assert fake_requests.calls[0]["url"] == "https://ci-gitlab.example.test/api/v4/projects/42"


@pytest.mark.parametrize("process_value", ["endpoint", "token"])
def test_partial_process_credentials_never_pair_with_complementary_dotenv_credentials(
    process_value: str,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    isolated_runtime: tuple[Path, FakeKeyring, FakeRequests],
) -> None:
    _, fake_keyring, fake_requests = isolated_runtime
    root = relocated_skill(tmp_path, f"mixed-source-{process_value}")
    if process_value == "endpoint":
        (root / ".env").write_text(
            "GITLAB_API_URL=https://dotenv.example.test/api/v4\nGITLAB_PERSONAL_ACCESS_TOKEN=dotenv-token\n",
            encoding="utf-8",
        )
        monkeypatch.setenv("GITLAB_API_URL", "https://process.example.test/api/v4")
    else:
        (root / ".env").write_text("GITLAB_API_URL=https://dotenv.example.test/api/v4\n", encoding="utf-8")
        monkeypatch.setenv("GITLAB_PERSONAL_ACCESS_TOKEN", "process-token")

    with pytest.raises(SystemExit):
        load_script(root, "gitlab_cli", monkeypatch).resolve_runtime_config()

    assert fake_keyring.get_calls == []
    assert fake_requests.calls == []


@pytest.mark.parametrize("profile_source", ["active", "environment", "command-line"])
@pytest.mark.parametrize(
    ("override_name", "override_value"),
    [
        ("GITLAB_API_URL", "https://partial-endpoint.example.test/api/v4"),
        ("GITLAB_TOKEN_KEYRING_USER", "override-user"),
        ("GITLAB_PERSONAL_ACCESS_TOKEN", "glpat-token-only-override"),
    ],
)
def test_partial_endpoint_keyring_user_or_token_override_against_a_profile_is_rejected_before_keyring_or_network(
    profile_source: str,
    override_name: str,
    override_value: str,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    isolated_runtime: tuple[Path, FakeKeyring, FakeRequests],
) -> None:
    config_home, fake_keyring, fake_requests = isolated_runtime
    document = multiple_profile_document()
    write_profile(config_home, document)
    for name, profile in document["profiles"].items():
        fake_keyring.passwords[(SERVICE_NAME, profile["keyring_user"])] = f"{name}-token"
    fake_keyring.passwords[(SERVICE_NAME, "override-user")] = "override-token"
    monkeypatch.setenv(override_name, override_value)

    cli_profile = None
    if profile_source == "environment":
        monkeypatch.setenv("GITLAB_PROFILE", "alpha")
    elif profile_source == "command-line":
        cli_profile = "zulu"

    _, exit_code = run_list_projects(
        relocated_skill(tmp_path, f"partial-{profile_source}-{override_name.lower()}"),
        monkeypatch,
        cli_profile,
    )

    captured = capsys.readouterr()
    output = captured.out + captured.err
    assert exit_code != 0
    assert "incoherent" in output.lower()
    assert fake_keyring.get_calls == []
    assert fake_requests.calls == []


@pytest.mark.parametrize("profile_source", ["environment", "command-line"])
def test_selecting_a_missing_profile_fails_without_mutation_keyring_or_network(
    profile_source: str,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    isolated_runtime: tuple[Path, FakeKeyring, FakeRequests],
) -> None:
    config_home, fake_keyring, fake_requests = isolated_runtime
    config_path = write_profile(config_home, multiple_profile_document())
    before = config_path.read_bytes()
    cli_profile = None
    if profile_source == "environment":
        monkeypatch.setenv("GITLAB_PROFILE", "does-not-exist")
    else:
        cli_profile = "does-not-exist"

    _, exit_code = run_list_projects(
        relocated_skill(tmp_path, f"missing-{profile_source}-profile"),
        monkeypatch,
        cli_profile,
    )

    captured = capsys.readouterr()
    output = captured.out + captured.err
    assert exit_code != 0
    assert "credential profile not found: does-not-exist" in output
    assert config_path.read_bytes() == before
    assert fake_keyring.get_calls == []
    assert fake_requests.calls == []


@pytest.mark.parametrize(
    ("line", "keyring_user"),
    [
        ("GITLAB_PERSONAL_ACCESS_TOKEN=dotenv-token", None),
        ("GITLAB_TOKEN_KEYRING_USER=dotenv-self-hosted-user", "dotenv-self-hosted-user"),
    ],
)
def test_legacy_dotenv_credential_without_endpoint_is_rejected_before_keyring_or_default_host(
    line: str,
    keyring_user: str | None,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    isolated_runtime: tuple[Path, FakeKeyring, FakeRequests],
) -> None:
    _, fake_keyring, fake_requests = isolated_runtime
    if keyring_user:
        fake_keyring.passwords[(SERVICE_NAME, keyring_user)] = "must-not-leak"
    skill_root = relocated_skill(tmp_path, "orphan-dotenv")
    (skill_root / ".env").write_text(line + "\n", encoding="utf-8")

    client, exit_code = run_list_projects(skill_root, monkeypatch)

    assert client is not None
    assert exit_code != 0
    assert "GITLAB_CREDENTIAL_SOURCE_MISMATCH" in capsys.readouterr().out
    assert fake_keyring.get_calls == []
    assert fake_requests.calls == []


def test_self_hosted_keyring_credential_without_its_endpoint_is_never_sent_to_gitlab_com_fallback(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    isolated_runtime: tuple[Path, FakeKeyring, FakeRequests],
) -> None:
    _, fake_keyring, fake_requests = isolated_runtime
    self_hosted_user = "self-hosted-user"
    sentinel = "glpat-self-hosted-never-fallback"
    fake_keyring.passwords[(SERVICE_NAME, self_hosted_user)] = sentinel
    monkeypatch.setenv("GITLAB_TOKEN_KEYRING_USER", self_hosted_user)

    _, exit_code = run_list_projects(
        relocated_skill(tmp_path, "no-fallback-host"),
        monkeypatch,
    )

    assert exit_code != 0
    assert fake_keyring.get_calls == []
    assert fake_requests.calls == []
    assert all(
        urlparse(call["url"]).hostname != "gitlab.com"
        or call.get("headers", {}).get("PRIVATE-TOKEN") != sentinel
        for call in fake_requests.calls
    )
