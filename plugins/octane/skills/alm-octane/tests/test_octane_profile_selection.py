"""RED tests for Task 2b: Octane profile selection and credential provenance.

Migration, locking, URL delegation, and HTTP error taxonomy are intentionally
outside this file's scope.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

import pytest

from test_octane_credential_config import (
    SERVICE_NAME,
    FakeKeyring,
    FakeSession,
    isolated_runtime,
    load_script,
    relocated_skill,
    write_profile,
)


def profile_selection_document(active_profile: str = "active") -> dict[str, Any]:
    profiles: dict[str, Any] = {}
    for name, ordinal in (("active", 1), ("environment", 2), ("command-line", 3)):
        profiles[name] = {
            "keyring_user": f"{name}-client",
            "endpoint": f"https://{name}.example.test",
            "settings": {
                "shared_space_id": f"{ordinal}01",
                "workspace_id": f"{ordinal}02",
                "timeout": str(10 + ordinal),
            },
        }
    return {"schema_version": 1, "active_profile": active_profile, "profiles": profiles}


def run_list_work_items(
    skill_root: Path,
    monkeypatch: pytest.MonkeyPatch,
    profile: str | None = None,
) -> None:
    arguments = ["octane_client.py"]
    if profile is not None:
        arguments.extend(("--profile", profile))
    arguments.extend(("list-work-items", "--limit", "1"))
    monkeypatch.setattr(sys, "argv", arguments)
    client = load_script(skill_root, "octane_client", monkeypatch)
    client.main()


@pytest.mark.parametrize(
    ("cli_profile", "environment_profile", "expected_profile"),
    [
        ("command-line", "environment", "command-line"),
        (None, "environment", "environment"),
        (None, None, "active"),
    ],
)
def test_cli_profile_then_environment_profile_then_active_profile_selects_one_coherent_configuration(
    cli_profile: str | None,
    environment_profile: str | None,
    expected_profile: str,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    isolated_runtime: tuple[Path, FakeKeyring],
) -> None:
    config_home, fake_keyring = isolated_runtime
    document = profile_selection_document()
    write_profile(config_home, document)
    for name, profile in document["profiles"].items():
        fake_keyring.passwords[(SERVICE_NAME, profile["keyring_user"])] = f"{name}-secret"
    if environment_profile is not None:
        monkeypatch.setenv("OCTANE_PROFILE", environment_profile)

    run_list_work_items(
        relocated_skill(tmp_path, f"selection-{expected_profile}"),
        monkeypatch,
        cli_profile,
    )

    selected = document["profiles"][expected_profile]
    settings = selected["settings"]
    session = FakeSession.instances[-1]
    assert session.posts == [{
        "url": f"{selected['endpoint']}/authentication/sign_in",
        "json": {
            "client_id": selected["keyring_user"],
            "client_secret": f"{expected_profile}-secret",
        },
        "timeout": int(settings["timeout"]),
        "allow_redirects": False,
    }]
    assert session.requests[0]["url"].startswith(
        f"{selected['endpoint']}/api/shared_spaces/{settings['shared_space_id']}"
        f"/workspaces/{settings['workspace_id']}/work_items"
    )
    assert session.requests[0]["timeout"] == int(settings["timeout"])
    assert fake_keyring.get_calls == [(SERVICE_NAME, selected["keyring_user"])]


def test_complete_direct_environment_credentials_and_endpoint_take_precedence_over_selected_profile(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    isolated_runtime: tuple[Path, FakeKeyring],
) -> None:
    config_home, fake_keyring = isolated_runtime
    write_profile(config_home, profile_selection_document())
    fake_keyring.passwords[(SERVICE_NAME, "active-client")] = "profile-secret"
    monkeypatch.setenv("OCTANE_BASE_URL", "https://ci.example.test/")
    monkeypatch.setenv("OCTANE_CLIENT_ID", "ci-client")
    monkeypatch.setenv("OCTANE_CLIENT_SECRET", "ci-direct-secret")
    monkeypatch.setenv("OCTANE_SHARED_SPACE_ID", "901")
    monkeypatch.setenv("OCTANE_WORKSPACE_ID", "902")
    monkeypatch.setenv("OCTANE_TIMEOUT", "19")

    run_list_work_items(relocated_skill(tmp_path, "direct-environment"), monkeypatch)

    session = FakeSession.instances[-1]
    assert session.posts == [{
        "url": "https://ci.example.test/authentication/sign_in",
        "json": {"client_id": "ci-client", "client_secret": "ci-direct-secret"},
        "timeout": 19,
        "allow_redirects": False,
    }]
    assert session.requests[0]["url"].startswith(
        "https://ci.example.test/api/shared_spaces/901/workspaces/902/work_items"
    )
    assert fake_keyring.get_calls == []


def test_complete_direct_credentials_do_not_inherit_active_profile_tenant_settings(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    isolated_runtime: tuple[Path, FakeKeyring],
) -> None:
    config_home, fake_keyring = isolated_runtime
    write_profile(config_home, profile_selection_document())
    monkeypatch.setenv("OCTANE_BASE_URL", "https://ci.example.test")
    monkeypatch.setenv("OCTANE_CLIENT_ID", "ci-client")
    monkeypatch.setenv("OCTANE_CLIENT_SECRET", "ci-secret")

    run_list_work_items(relocated_skill(tmp_path, "direct-defaults"), monkeypatch)

    session = FakeSession.instances[-1]
    assert session.posts[0]["timeout"] == 30
    assert session.requests[0]["url"].startswith(
        "https://ci.example.test/api/shared_spaces/1001/workspaces/1003/work_items"
    )
    assert fake_keyring.get_calls == []


def test_complete_process_keyring_credentials_ignore_conflicting_dotenv_identity_and_settings(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    isolated_runtime: tuple[Path, FakeKeyring],
) -> None:
    _, fake_keyring = isolated_runtime
    fake_keyring.passwords[(SERVICE_NAME, "process-client")] = "process-secret"
    monkeypatch.setenv("OCTANE_BASE_URL", "https://process.example.test")
    monkeypatch.setenv("OCTANE_CLIENT_SECRET_KEYRING_USER", "process-client")
    skill_root = relocated_skill(tmp_path, "keyring-source-isolation")
    (skill_root / ".env").write_text(
        "OCTANE_CLIENT_ID=wrong-dotenv-client\n"
        "OCTANE_SHARED_SPACE_ID=999\n"
        "OCTANE_WORKSPACE_ID=998\n"
        "OCTANE_TIMEOUT=3\n",
        encoding="utf-8",
    )

    run_list_work_items(skill_root, monkeypatch)

    session = FakeSession.instances[-1]
    assert session.posts[0]["json"] == {"client_id": "process-client", "client_secret": "process-secret"}
    assert session.posts[0]["timeout"] == 30
    assert session.requests[0]["url"].startswith(
        "https://process.example.test/api/shared_spaces/1001/workspaces/1003/work_items"
    )


def test_complete_process_credentials_bypass_malformed_durable_metadata(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    isolated_runtime: tuple[Path, FakeKeyring],
) -> None:
    config_home, _ = isolated_runtime
    config_home.mkdir(parents=True, exist_ok=True)
    (config_home / "octane.json").write_text("{malformed", encoding="utf-8")
    monkeypatch.setenv("OCTANE_BASE_URL", "https://ci.example.test")
    monkeypatch.setenv("OCTANE_CLIENT_ID", "ci-client")
    monkeypatch.setenv("OCTANE_CLIENT_SECRET", "ci-secret")

    run_list_work_items(relocated_skill(tmp_path, "malformed-bypass"), monkeypatch)

    assert FakeSession.instances[-1].posts[0]["url"] == "https://ci.example.test/authentication/sign_in"


@pytest.mark.parametrize("profile_source", ["active", "environment"])
@pytest.mark.parametrize(
    ("override_name", "override_value"),
    [
        ("OCTANE_BASE_URL", "https://partial-endpoint.example.test"),
        ("OCTANE_CLIENT_SECRET_KEYRING_USER", "override-client"),
        ("OCTANE_CLIENT_SECRET", "direct-secret-without-direct-client-id"),
    ],
)
def test_partial_endpoint_or_credential_override_against_a_profile_is_rejected_before_keyring_or_network(
    profile_source: str,
    override_name: str,
    override_value: str,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    isolated_runtime: tuple[Path, FakeKeyring],
) -> None:
    config_home, fake_keyring = isolated_runtime
    document = profile_selection_document()
    write_profile(config_home, document)
    fake_keyring.passwords[(SERVICE_NAME, "active-client")] = "active-secret"
    fake_keyring.passwords[(SERVICE_NAME, "environment-client")] = "environment-secret"
    fake_keyring.passwords[(SERVICE_NAME, "command-line-client")] = "command-line-secret"
    fake_keyring.passwords[(SERVICE_NAME, "override-client")] = "override-secret"
    monkeypatch.setenv(override_name, override_value)

    cli_profile = None
    if profile_source == "environment":
        monkeypatch.setenv("OCTANE_PROFILE", "environment")

    with pytest.raises(SystemExit) as exc_info:
        run_list_work_items(
            relocated_skill(tmp_path, f"partial-{profile_source}-{override_name}"),
            monkeypatch,
            cli_profile,
        )

    assert exc_info.value.code != 0
    assert fake_keyring.get_calls == []
    assert FakeSession.instances == []


def test_selecting_a_missing_profile_fails_without_mutation_keyring_or_network(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    isolated_runtime: tuple[Path, FakeKeyring],
) -> None:
    config_home, fake_keyring = isolated_runtime
    config_path = write_profile(config_home, profile_selection_document())
    before = config_path.read_bytes()
    monkeypatch.setenv("OCTANE_PROFILE", "does-not-exist")

    with pytest.raises(SystemExit) as exc_info:
        run_list_work_items(
            relocated_skill(tmp_path, "missing-environment-profile"),
            monkeypatch,
        )

    assert exc_info.value.code != 0
    assert config_path.read_bytes() == before
    assert fake_keyring.get_calls == []
    assert FakeSession.instances == []
