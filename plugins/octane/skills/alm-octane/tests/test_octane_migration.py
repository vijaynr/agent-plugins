"""RED tests for Task 2c: non-destructive Octane legacy migration.

Profile lifecycle, profile selection, locking, and profile durability are covered
by their own focused test files and are intentionally out of scope here.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

from test_octane_credential_config import (
    SERVICE_NAME,
    SENTINEL_SECRET,
    FakeKeyring,
    FakeKeyringError,
    FakeSession,
    isolated_runtime,
    load_script,
    profile_document,
    relocated_skill,
)


def legacy_keyring_env(
    *,
    endpoint: str = "https://legacy-octane.example.test/",
    keyring_user: str = "legacy-client",
    workspace_id: str = "1003",
) -> bytes:
    return (
        "# retained legacy configuration\r\n"
        f"OCTANE_BASE_URL={endpoint}\r\n"
        f"OCTANE_CLIENT_SECRET_KEYRING_USER={keyring_user}\r\n"
        "OCTANE_SHARED_SPACE_ID=131002\r\n"
        f"OCTANE_WORKSPACE_ID={workspace_id}\r\n"
        "OCTANE_TIMEOUT=17\r\n"
    ).encode("utf-8")


def write_legacy_env(skill_root: Path, content: bytes) -> Path:
    skill_root.mkdir(parents=True, exist_ok=True)
    path = skill_root / ".env"
    path.write_bytes(content)
    return path


def legacy_roots(skill_root: Path, home: Path) -> dict[str, Path]:
    return {
        "executing-root": skill_root,
        "copilot-root": home / ".copilot" / "skills" / "alm-octane",
        "agents-root": home / ".agents" / "skills" / "alm-octane",
    }


def arrange_home(config_home: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    home = config_home.parent / "home"
    monkeypatch.setenv("HOME", str(home))
    monkeypatch.setenv("USERPROFILE", str(home))
    return home


def test_complete_process_credentials_skip_unrelated_legacy_migration(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    isolated_runtime: tuple[Path, FakeKeyring],
) -> None:
    config_home, fake_keyring = isolated_runtime
    home = arrange_home(config_home, monkeypatch)
    skill_root = relocated_skill(tmp_path, "direct-skips-migration")
    source = write_legacy_env(legacy_roots(skill_root, home)["agents-root"], legacy_keyring_env())
    monkeypatch.setenv("OCTANE_BASE_URL", "https://ci.example.test")
    monkeypatch.setenv("OCTANE_CLIENT_ID", "ci-client")
    monkeypatch.setenv("OCTANE_CLIENT_SECRET", "ci-secret")

    client = load_script(skill_root, "octane_client", monkeypatch)
    runtime = client.resolve_runtime_config()

    assert runtime.base_url == "https://ci.example.test"
    assert fake_keyring.get_calls == []
    assert not (config_home / "octane.json").exists()
    assert source.is_file()


def test_dotenv_field_override_is_snapshotted_without_environment_mutation(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    isolated_runtime: tuple[Path, FakeKeyring],
) -> None:
    config_home, fake_keyring = isolated_runtime
    arrange_home(config_home, monkeypatch)
    skill_root = relocated_skill(tmp_path, "dotenv-field")
    (skill_root / ".env").write_text(
        "OCTANE_BASE_URL=https://dotenv.example.test\n"
        "OCTANE_CLIENT_ID=dotenv-client\n"
        "OCTANE_CLIENT_SECRET=dotenv-secret\n"
        "OCTANE_SECURITY_ASSESSMENT_FIELD=custom_security_field\n",
        encoding="utf-8",
    )
    client = load_script(skill_root, "octane_client", monkeypatch)
    client.configure_runtime(client.resolve_runtime_config())

    field_name, _, metadata = client.resolve_field_name("feature", "Security Assessment", "1003", "1001")

    assert field_name == "custom_security_field"
    assert metadata["source"] == "environment"
    assert "OCTANE_SECURITY_ASSESSMENT_FIELD" not in os.environ
    assert fake_keyring.get_calls == []


def test_import_does_not_process_legacy_configuration(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    isolated_runtime: tuple[Path, FakeKeyring],
) -> None:
    config_home, fake_keyring = isolated_runtime
    home = arrange_home(config_home, monkeypatch)
    skill_root = relocated_skill(tmp_path, "side-effect-free-import")
    source = write_legacy_env(legacy_roots(skill_root, home)["executing-root"], legacy_keyring_env())
    fake_keyring.passwords[(SERVICE_NAME, "legacy-client")] = SENTINEL_SECRET

    load_script(skill_root, "octane_client", monkeypatch)

    assert not (config_home / "octane.json").exists()
    assert fake_keyring.get_calls == []
    assert source.is_file()


@pytest.mark.parametrize("selection_source", ["argument", "environment"])
def test_requested_default_profile_can_be_selected_during_legacy_migration(
    selection_source: str,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    isolated_runtime: tuple[Path, FakeKeyring],
) -> None:
    config_home, fake_keyring = isolated_runtime
    home = arrange_home(config_home, monkeypatch)
    skill_root = relocated_skill(tmp_path, f"selected-default-{selection_source}")
    write_legacy_env(legacy_roots(skill_root, home)["executing-root"], legacy_keyring_env())
    fake_keyring.passwords[(SERVICE_NAME, "legacy-client")] = SENTINEL_SECRET
    client = load_script(skill_root, "octane_client", monkeypatch)
    if selection_source == "environment":
        monkeypatch.setenv("OCTANE_PROFILE", "default")
        runtime = client.resolve_runtime_config()
    else:
        runtime = client.resolve_runtime_config("default")

    assert runtime.base_url == "https://legacy-octane.example.test"
    assert (config_home / "octane.json").is_file()


def test_unknown_selected_profile_does_not_trigger_default_legacy_migration(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    isolated_runtime: tuple[Path, FakeKeyring],
) -> None:
    config_home, fake_keyring = isolated_runtime
    home = arrange_home(config_home, monkeypatch)
    skill_root = relocated_skill(tmp_path, "unknown-selected-profile")
    source = write_legacy_env(legacy_roots(skill_root, home)["executing-root"], legacy_keyring_env())
    fake_keyring.passwords[(SERVICE_NAME, "legacy-client")] = SENTINEL_SECRET
    client = load_script(skill_root, "octane_client", monkeypatch)

    with pytest.raises(SystemExit):
        client.resolve_runtime_config("production")

    assert fake_keyring.get_calls == []
    assert not (config_home / "octane.json").exists()
    assert source.is_file()


@pytest.mark.parametrize("root_name", ["executing-root", "copilot-root", "agents-root"])
def test_each_exact_legacy_root_migrates_usable_keyring_metadata_without_touching_source(
    root_name: str,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    isolated_runtime: tuple[Path, FakeKeyring],
) -> None:
    config_home, fake_keyring = isolated_runtime
    home = arrange_home(config_home, monkeypatch)
    skill_root = relocated_skill(tmp_path, f"exact-{root_name}")
    source_bytes = legacy_keyring_env()
    source = write_legacy_env(legacy_roots(skill_root, home)[root_name], source_bytes)
    fake_keyring.passwords[(SERVICE_NAME, "legacy-client")] = SENTINEL_SECRET

    load_script(skill_root, "octane_client", monkeypatch).resolve_runtime_config()

    assert json.loads((config_home / "octane.json").read_text(encoding="utf-8")) == profile_document(
        endpoint="https://legacy-octane.example.test",
        keyring_user="legacy-client",
        shared_space_id="131002",
        workspace_id="1003",
        timeout="17",
    )
    assert fake_keyring.get_calls == [(SERVICE_NAME, "legacy-client")]
    assert FakeSession.instances == []
    assert source.read_bytes() == source_bytes


def test_equivalent_candidates_are_migrated_once_and_not_rechecked_after_stable_profile_exists(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    isolated_runtime: tuple[Path, FakeKeyring],
) -> None:
    config_home, fake_keyring = isolated_runtime
    home = arrange_home(config_home, monkeypatch)
    skill_root = relocated_skill(tmp_path, "equivalent-candidates")
    source_bytes = legacy_keyring_env()
    sources = [
        write_legacy_env(root, source_bytes)
        for root in legacy_roots(skill_root, home).values()
    ]
    fake_keyring.passwords[(SERVICE_NAME, "legacy-client")] = SENTINEL_SECRET

    load_script(skill_root, "octane_client", monkeypatch).resolve_runtime_config()
    config_path = config_home / "octane.json"
    migrated_bytes = config_path.read_bytes()
    assert list(json.loads(migrated_bytes)["profiles"]) == ["default"]
    assert fake_keyring.get_calls == [(SERVICE_NAME, "legacy-client")]

    fake_keyring.get_calls.clear()
    load_script(skill_root, "octane_client", monkeypatch).resolve_runtime_config()

    assert config_path.read_bytes() == migrated_bytes
    assert fake_keyring.get_calls == []
    assert all(source.read_bytes() == source_bytes for source in sources)
    assert FakeSession.instances == []


def test_canonical_alias_of_a_candidate_root_does_not_create_a_false_conflict(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    isolated_runtime: tuple[Path, FakeKeyring],
) -> None:
    config_home, fake_keyring = isolated_runtime
    home = arrange_home(config_home, monkeypatch)
    skill_root = relocated_skill(tmp_path, "canonical-source")
    source_bytes = legacy_keyring_env()
    source = write_legacy_env(skill_root, source_bytes)
    copilot_root = legacy_roots(skill_root, home)["copilot-root"]
    copilot_root.parent.mkdir(parents=True, exist_ok=True)
    try:
        copilot_root.symlink_to(skill_root, target_is_directory=True)
    except (NotImplementedError, OSError) as symlink_error:
        if os.name != "nt":
            pytest.skip(f"directory aliases are unavailable on this platform: {symlink_error}")
        junction = subprocess.run(
            ["cmd", "/c", "mklink", "/J", str(copilot_root), str(skill_root)],
            capture_output=True,
            text=True,
        )
        if junction.returncode != 0:
            pytest.skip(
                "directory aliases are unavailable on this platform: "
                f"{symlink_error}; {junction.stderr.strip()}"
            )
    fake_keyring.passwords[(SERVICE_NAME, "legacy-client")] = SENTINEL_SECRET

    load_script(skill_root, "octane_client", monkeypatch).resolve_runtime_config()

    assert (config_home / "octane.json").is_file()
    assert fake_keyring.get_calls == [(SERVICE_NAME, "legacy-client")]
    assert source.read_bytes() == source_bytes
    assert FakeSession.instances == []


def test_conflicting_non_secret_metadata_fails_with_paths_and_field_names_but_no_secrets(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    isolated_runtime: tuple[Path, FakeKeyring],
) -> None:
    config_home, fake_keyring = isolated_runtime
    home = arrange_home(config_home, monkeypatch)
    skill_root = relocated_skill(tmp_path, "conflicting-candidates")
    roots = legacy_roots(skill_root, home)
    first_bytes = legacy_keyring_env(endpoint="https://first.example.test/")
    second_bytes = legacy_keyring_env(endpoint="https://second.example.test/")
    first = write_legacy_env(roots["executing-root"], first_bytes)
    second = write_legacy_env(roots["copilot-root"], second_bytes)
    fake_keyring.passwords[(SERVICE_NAME, "legacy-client")] = SENTINEL_SECRET

    with pytest.raises(SystemExit) as exc_info:
        load_script(skill_root, "octane_client", monkeypatch).resolve_runtime_config()

    captured = capsys.readouterr()
    output = captured.out + captured.err
    details = json.loads(captured.out)["details"]
    assert exc_info.value.code != 0
    assert str(first) in details
    assert str(second) in details
    assert "endpoint" in details
    assert SENTINEL_SECRET not in output
    assert not (config_home / "octane.json").exists()
    assert first.read_bytes() == first_bytes
    assert second.read_bytes() == second_bytes
    assert FakeSession.instances == []


@pytest.mark.parametrize("keyring_result", ["missing", "backend-failure"])
def test_unusable_keyring_candidate_does_not_migrate_or_call_network(
    keyring_result: str,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    isolated_runtime: tuple[Path, FakeKeyring],
) -> None:
    config_home, fake_keyring = isolated_runtime
    home = arrange_home(config_home, monkeypatch)
    skill_root = relocated_skill(tmp_path, f"unusable-{keyring_result}")
    source_bytes = legacy_keyring_env()
    source = write_legacy_env(legacy_roots(skill_root, home)["agents-root"], source_bytes)
    if keyring_result == "backend-failure":
        def fail_get_password(_service: str, _username: str) -> str | None:
            fake_keyring.get_calls.append((_service, _username))
            raise FakeKeyringError("injected keyring backend failure")

        monkeypatch.setattr(sys.modules["keyring"], "get_password", fail_get_password)

    with pytest.raises(SystemExit) as exc_info:
        load_script(skill_root, "octane_client", monkeypatch).resolve_runtime_config()

    assert exc_info.value.code != 0
    assert fake_keyring.get_calls == [(SERVICE_NAME, "legacy-client")]
    assert not (config_home / "octane.json").exists()
    assert source.read_bytes() == source_bytes
    assert FakeSession.instances == []


def test_direct_secret_only_legacy_env_remains_usable_fallback_and_is_not_migrated(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    isolated_runtime: tuple[Path, FakeKeyring],
) -> None:
    config_home, fake_keyring = isolated_runtime
    arrange_home(config_home, monkeypatch)
    skill_root = relocated_skill(tmp_path, "direct-secret-fallback")
    source_bytes = (
        "# direct secret is retained only in the legacy source\n"
        "OCTANE_BASE_URL=https://direct.example.test/\n"
        "OCTANE_CLIENT_ID=direct-client\n"
        f"OCTANE_CLIENT_SECRET={SENTINEL_SECRET}\n"
        "OCTANE_SHARED_SPACE_ID=501\n"
        "OCTANE_WORKSPACE_ID=502\n"
        "OCTANE_TIMEOUT=19\n"
    ).encode("utf-8")
    source = write_legacy_env(skill_root, source_bytes)

    client = load_script(skill_root, "octane_client", monkeypatch)
    client.configure_runtime(client.resolve_runtime_config())
    session = client.get_session()

    assert session.posts == [{
        "url": "https://direct.example.test/authentication/sign_in",
        "json": {"client_id": "direct-client", "client_secret": SENTINEL_SECRET},
        "timeout": 19,
        "allow_redirects": False,
    }]
    assert fake_keyring.get_calls == []
    assert not (config_home / "octane.json").exists()
    assert source.read_bytes() == source_bytes
