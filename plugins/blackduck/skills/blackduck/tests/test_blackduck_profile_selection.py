"""RED tests for Task 8: Black Duck profile selection and provenance."""
from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Any

import pytest

from test_blackduck_credential_config import (
    SERVICE_NAME, FakeKeyring, FakeSession, isolated_runtime, load_script,
    relocated_skill, write_profile,
)
from test_blackduck_profiles import profiles_document


def run_list_projects(root: Path, monkeypatch: pytest.MonkeyPatch, profile: str | None = None) -> Any:
    arguments = ["blackduck_vulnerabilities.py"]
    if profile is not None:
        arguments.extend(("--profile", profile))
    arguments.extend(("list-projects", "--limit", "1"))
    monkeypatch.setattr(sys, "argv", arguments)
    client = load_script(root, "blackduck_vulnerabilities", monkeypatch)
    client.main()
    return client


@pytest.mark.parametrize(("cli", "environment", "expected"), [
    ("zulu", "alpha", "zulu"), (None, "alpha", "alpha"), (None, None, "production"),
])
def test_cli_then_environment_then_active_selects_coherent_url_keyring_and_verify_ssl(cli: str | None, environment: str | None, expected: str, tmp_path: Path, monkeypatch: pytest.MonkeyPatch, isolated_runtime: tuple[Path, FakeKeyring]) -> None:
    config_home, keyring = isolated_runtime
    document = profiles_document()
    write_profile(config_home, document)
    for name, profile in document["profiles"].items():
        keyring.passwords[(SERVICE_NAME, profile["keyring_user"])] = f"{name}-token"
    if environment:
        monkeypatch.setenv("BLACKDUCK_PROFILE", environment)

    run_list_projects(relocated_skill(tmp_path, f"select-{expected}"), monkeypatch, cli)

    selected = document["profiles"][expected]
    session = FakeSession.instances[-1]
    assert keyring.get_calls == [(SERVICE_NAME, selected["keyring_user"])]
    assert session.verify is (selected["settings"]["verify_ssl"] == "true")
    assert session.posts[0]["url"] == f"{selected['endpoint']}/api/tokens/authenticate"
    assert session.posts[0]["headers"]["Authorization"] == f"token {expected}-token"
    assert session.gets[0]["url"] == f"{selected['endpoint']}/api/projects"


def test_selected_profile_ignores_conflicting_complete_legacy_dotenv_credentials_and_ssl(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    isolated_runtime: tuple[Path, FakeKeyring],
) -> None:
    config_home, keyring = isolated_runtime
    document = profiles_document()
    write_profile(config_home, document)
    selected = document["profiles"]["production"]
    keyring.passwords[(SERVICE_NAME, selected["keyring_user"])] = "production-token"
    root = relocated_skill(tmp_path, "conflicting-dotenv")
    (root / ".env").write_text(
        "BLACKDUCK_URL=https://wrong-host.example.test\n"
        "BLACKDUCK_TOKEN=wrong-direct-token\n"
        "BLACKDUCK_VERIFY_SSL=true\n",
        encoding="utf-8",
    )

    def load_test_dotenv(path: str | Path, *_args: object, **_kwargs: object) -> bool:
        for line in Path(path).read_text(encoding="utf-8").splitlines():
            key, value = line.split("=", 1)
            os.environ.setdefault(key, value)
        return True

    monkeypatch.setattr(sys.modules["dotenv"], "load_dotenv", load_test_dotenv)
    client = run_list_projects(root, monkeypatch)

    session = FakeSession.instances[-1]
    assert session.verify is False
    assert session.posts[0]["url"] == f"{selected['endpoint']}/api/tokens/authenticate"
    assert session.posts[0]["headers"]["Authorization"] == "token production-token"
    assert keyring.get_calls == [(SERVICE_NAME, selected["keyring_user"])]


@pytest.mark.parametrize(
    ("line", "keyring_user"),
    [
        ("BLACKDUCK_TOKEN=dotenv-token", None),
        ("BLACKDUCK_TOKEN_KEYRING_USER=dotenv-user", "dotenv-user"),
    ],
)
def test_legacy_dotenv_credential_without_url_is_rejected_before_keyring_or_http(
    line: str,
    keyring_user: str | None,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    isolated_runtime: tuple[Path, FakeKeyring],
) -> None:
    _, keyring = isolated_runtime
    if keyring_user:
        keyring.passwords[(SERVICE_NAME, keyring_user)] = "must-not-leak"
    root = relocated_skill(tmp_path, "orphan-dotenv")
    (root / ".env").write_text(line + "\n", encoding="utf-8")

    def load_test_dotenv(path: str | Path, *_args: object, **_kwargs: object) -> bool:
        key, value = Path(path).read_text(encoding="utf-8").strip().split("=", 1)
        os.environ.setdefault(key, value)
        return True

    monkeypatch.setattr(sys.modules["dotenv"], "load_dotenv", load_test_dotenv)
    with pytest.raises(SystemExit):
        run_list_projects(root, monkeypatch)

    assert keyring.get_calls == []
    assert FakeSession.instances == []


def test_complete_direct_url_token_and_verify_override_selected_profile(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, isolated_runtime: tuple[Path, FakeKeyring]) -> None:
    config_home, keyring = isolated_runtime
    write_profile(config_home, profiles_document())
    keyring.passwords[(SERVICE_NAME, "production-user")] = "profile-token"
    monkeypatch.setenv("BLACKDUCK_URL", "https://ci-blackduck.example.test/")
    monkeypatch.setenv("BLACKDUCK_TOKEN", "direct-ci-token")
    monkeypatch.setenv("BLACKDUCK_VERIFY_SSL", "true")

    run_list_projects(relocated_skill(tmp_path, "direct"), monkeypatch)

    session = FakeSession.instances[-1]
    assert keyring.get_calls == []
    assert session.verify is True
    assert session.posts[0]["url"] == "https://ci-blackduck.example.test/api/tokens/authenticate"
    assert session.posts[0]["headers"]["Authorization"] == "token direct-ci-token"
    assert session.gets[0]["url"] == "https://ci-blackduck.example.test/api/projects"


def test_complete_process_credentials_bypass_malformed_durable_metadata(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    isolated_runtime: tuple[Path, FakeKeyring],
) -> None:
    config_home, keyring = isolated_runtime
    config_home.mkdir(parents=True, exist_ok=True)
    (config_home / "blackduck.json").write_text("{malformed", encoding="utf-8")
    monkeypatch.setenv("BLACKDUCK_URL", "https://ci-blackduck.example.test")
    monkeypatch.setenv("BLACKDUCK_TOKEN", "direct-token")

    run_list_projects(relocated_skill(tmp_path, "malformed-bypass"), monkeypatch)

    session = FakeSession.instances[-1]
    assert session.posts[0]["url"] == "https://ci-blackduck.example.test/api/tokens/authenticate"
    assert keyring.get_calls == []


def test_repeated_dotenv_resolution_is_deterministic_without_environment_mutation(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    isolated_runtime: tuple[Path, FakeKeyring],
) -> None:
    _, keyring = isolated_runtime
    root = relocated_skill(tmp_path, "dotenv-idempotence")
    (root / ".env").write_text(
        "BLACKDUCK_URL=https://dotenv-blackduck.example.test\n"
        "BLACKDUCK_TOKEN=dotenv-token\n"
        "BLACKDUCK_VERIFY_SSL=false\n",
        encoding="utf-8",
    )
    client = load_script(root, "blackduck_vulnerabilities", monkeypatch)

    first = client.resolve_runtime_config()
    second = client.resolve_runtime_config()

    assert first == second
    assert "BLACKDUCK_URL" not in os.environ
    assert "BLACKDUCK_TOKEN" not in os.environ
    assert keyring.get_calls == []


@pytest.mark.parametrize("profile_source", ["active", "environment", "command-line"])
@pytest.mark.parametrize(("override", "value"), [
    ("BLACKDUCK_URL", "https://partial.example.test"),
    ("BLACKDUCK_TOKEN_KEYRING_USER", "override-user"),
    ("BLACKDUCK_TOKEN", "token-only-override"),
])
def test_partial_url_or_credential_override_is_rejected_before_keyring_and_http(profile_source: str, override: str, value: str, tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str], isolated_runtime: tuple[Path, FakeKeyring]) -> None:
    config_home, keyring = isolated_runtime
    document = profiles_document()
    path = write_profile(config_home, document)
    before = path.read_bytes()
    for name, profile in document["profiles"].items():
        keyring.passwords[(SERVICE_NAME, profile["keyring_user"])] = f"{name}-token"
    keyring.passwords[(SERVICE_NAME, "override-user")] = "override-token"
    monkeypatch.setenv(override, value)
    cli = None
    if profile_source == "environment":
        monkeypatch.setenv("BLACKDUCK_PROFILE", "alpha")
    elif profile_source == "command-line":
        cli = "zulu"

    with pytest.raises(SystemExit) as exc:
        run_list_projects(relocated_skill(tmp_path, f"partial-{profile_source}-{override}"), monkeypatch, cli)

    assert exc.value.code != 0
    captured = capsys.readouterr()
    assert "incoherent" in (captured.out + captured.err).lower()
    assert path.read_bytes() == before
    assert keyring.get_calls == []
    assert FakeSession.instances == []


@pytest.mark.parametrize("source", ["environment", "command-line"])
def test_missing_explicit_profile_fails_early_without_mutation_keyring_or_http(source: str, tmp_path: Path, monkeypatch: pytest.MonkeyPatch, isolated_runtime: tuple[Path, FakeKeyring]) -> None:
    config_home, keyring = isolated_runtime
    path = write_profile(config_home, profiles_document())
    before = path.read_bytes()
    cli = None
    if source == "environment":
        monkeypatch.setenv("BLACKDUCK_PROFILE", "missing")
    else:
        cli = "missing"

    with pytest.raises(SystemExit) as exc:
        run_list_projects(relocated_skill(tmp_path, f"missing-{source}"), monkeypatch, cli)

    assert exc.value.code != 0
    assert path.read_bytes() == before
    assert keyring.get_calls == []
    assert FakeSession.instances == []


def test_keyring_locator_without_url_is_rejected_before_read_or_default_host_http(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, isolated_runtime: tuple[Path, FakeKeyring]) -> None:
    _, keyring = isolated_runtime
    keyring.passwords[(SERVICE_NAME, "self-hosted-user")] = "must-not-leak"
    monkeypatch.setenv("BLACKDUCK_TOKEN_KEYRING_USER", "self-hosted-user")

    with pytest.raises(SystemExit):
        run_list_projects(relocated_skill(tmp_path, "no-default-host"), monkeypatch)

    assert keyring.get_calls == []
    assert FakeSession.instances == []
