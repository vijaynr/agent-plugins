"""RED tests for Task 5c: non-destructive GitLab legacy migration.

Locking, profile lifecycle, and HTTP error taxonomy are intentionally outside
this focused migration suite.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

from .test_gitlab_credential_config import (
    SERVICE_NAME,
    SENTINEL_TOKEN,
    FakeKeyring,
    FakeKeyringError,
    FakeRequests,
    isolated_runtime,
    load_script,
    profile_document,
    relocated_skill,
    write_profile,
)


def legacy_keyring_env(
    *,
    endpoint: str = "https://legacy-gitlab.example.test/api/v4/",
    keyring_user: str = "legacy-gitlab-user",
    project_id: str = "42",
) -> bytes:
    return (
        "# retained legacy GitLab configuration\r\n"
        f"GITLAB_API_URL={endpoint}\r\n"
        f"GITLAB_TOKEN_KEYRING_USER={keyring_user}\r\n"
        f"GITLAB_PROJECT_ID={project_id}\r\n"
        "GITLAB_ALLOWED_PROJECT_IDS=42,84\r\n"
        "GITLAB_READ_ONLY_MODE=true\r\n"
        "GITLAB_TIMEOUT=17\r\n"
    ).encode("utf-8")


def write_legacy_env(skill_root: Path, content: bytes) -> Path:
    skill_root.mkdir(parents=True, exist_ok=True)
    path = skill_root / ".env"
    path.write_bytes(content)
    return path


def legacy_roots(skill_root: Path, home: Path) -> dict[str, Path]:
    return {
        "executing-root": skill_root,
        "copilot-root": home / ".copilot" / "skills" / "gitlab",
        "agents-root": home / ".agents" / "skills" / "gitlab",
    }


def arrange_home(config_home: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    home = config_home.parent / "migration-home"
    monkeypatch.setenv("HOME", str(home))
    monkeypatch.setenv("USERPROFILE", str(home))
    return home


def test_complete_process_credentials_skip_unrelated_legacy_migration(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    isolated_runtime: tuple[Path, FakeKeyring, FakeRequests],
) -> None:
    config_home, fake_keyring, fake_requests = isolated_runtime
    home = arrange_home(config_home, monkeypatch)
    skill_root = relocated_skill(tmp_path, "direct-skips-migration")
    source = write_legacy_env(legacy_roots(skill_root, home)["agents-root"], legacy_keyring_env())
    monkeypatch.setenv("GITLAB_API_URL", "https://ci-gitlab.example.test/api/v4")
    monkeypatch.setenv("GITLAB_PERSONAL_ACCESS_TOKEN", "glpat-ci-token")

    client = load_script(skill_root, "gitlab_cli", monkeypatch)
    runtime = client.resolve_runtime_config()

    assert runtime.base_url == "https://ci-gitlab.example.test/api/v4"
    assert fake_keyring.get_calls == []
    assert fake_requests.calls == []
    assert not (config_home / "gitlab.json").exists()
    assert source.is_file()


@pytest.mark.parametrize("root_name", ["executing-root", "copilot-root", "agents-root"])
def test_each_exact_legacy_root_migrates_keyring_backed_metadata_once_without_touching_source(
    root_name: str,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    isolated_runtime: tuple[Path, FakeKeyring, FakeRequests],
) -> None:
    config_home, fake_keyring, fake_requests = isolated_runtime
    home = arrange_home(config_home, monkeypatch)
    skill_root = relocated_skill(tmp_path, f"exact-{root_name}")
    source_bytes = legacy_keyring_env()
    source = write_legacy_env(legacy_roots(skill_root, home)[root_name], source_bytes)
    fake_keyring.passwords[(SERVICE_NAME, "legacy-gitlab-user")] = SENTINEL_TOKEN

    load_script(skill_root, "gitlab_cli", monkeypatch).resolve_runtime_config()

    assert json.loads((config_home / "gitlab.json").read_text(encoding="utf-8")) == profile_document(
        endpoint="https://legacy-gitlab.example.test/api/v4",
        keyring_user="legacy-gitlab-user",
    )
    assert fake_keyring.get_calls == [(SERVICE_NAME, "legacy-gitlab-user")]
    assert fake_requests.calls == []
    assert source.read_bytes() == source_bytes


def test_equivalent_candidates_migrate_once_and_are_not_rechecked_after_stable_metadata_exists(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    isolated_runtime: tuple[Path, FakeKeyring, FakeRequests],
) -> None:
    config_home, fake_keyring, fake_requests = isolated_runtime
    home = arrange_home(config_home, monkeypatch)
    skill_root = relocated_skill(tmp_path, "equivalent-candidates")
    source_bytes = legacy_keyring_env()
    sources = [write_legacy_env(root, source_bytes) for root in legacy_roots(skill_root, home).values()]
    fake_keyring.passwords[(SERVICE_NAME, "legacy-gitlab-user")] = SENTINEL_TOKEN

    load_script(skill_root, "gitlab_cli", monkeypatch).resolve_runtime_config()
    config_path = config_home / "gitlab.json"
    migrated_bytes = config_path.read_bytes()
    assert list(json.loads(migrated_bytes)["profiles"]) == ["default"]
    assert fake_keyring.get_calls == [(SERVICE_NAME, "legacy-gitlab-user")]

    fake_keyring.get_calls.clear()
    load_script(skill_root, "gitlab_cli", monkeypatch).resolve_runtime_config()

    assert config_path.read_bytes() == migrated_bytes
    assert fake_keyring.get_calls == []
    assert fake_requests.calls == []
    assert all(source.read_bytes() == source_bytes for source in sources)


def test_canonical_alias_of_a_candidate_root_is_deduplicated_and_migrates_once(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    isolated_runtime: tuple[Path, FakeKeyring, FakeRequests],
) -> None:
    config_home, fake_keyring, fake_requests = isolated_runtime
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
    fake_keyring.passwords[(SERVICE_NAME, "legacy-gitlab-user")] = SENTINEL_TOKEN

    load_script(skill_root, "gitlab_cli", monkeypatch).resolve_runtime_config()

    assert (config_home / "gitlab.json").is_file()
    assert fake_keyring.get_calls == [(SERVICE_NAME, "legacy-gitlab-user")]
    assert fake_requests.calls == []
    assert source.read_bytes() == source_bytes


def test_conflicting_candidates_report_source_paths_and_non_secret_fields_without_token(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    isolated_runtime: tuple[Path, FakeKeyring, FakeRequests],
) -> None:
    config_home, fake_keyring, fake_requests = isolated_runtime
    home = arrange_home(config_home, monkeypatch)
    skill_root = relocated_skill(tmp_path, "conflicting-candidates")
    roots = legacy_roots(skill_root, home)
    first_bytes = legacy_keyring_env(endpoint="https://first.example.test/api/v4/")
    second_bytes = legacy_keyring_env(endpoint="https://second.example.test/api/v4/")
    first = write_legacy_env(roots["executing-root"], first_bytes)
    second = write_legacy_env(roots["copilot-root"], second_bytes)
    fake_keyring.passwords[(SERVICE_NAME, "legacy-gitlab-user")] = SENTINEL_TOKEN

    with pytest.raises(SystemExit) as exc_info:
        load_script(skill_root, "gitlab_cli", monkeypatch).resolve_runtime_config()

    captured = capsys.readouterr()
    output = captured.out + captured.err
    details = json.loads(captured.out)["details"]
    assert exc_info.value.code != 0
    assert str(first) in details
    assert str(second) in details
    assert "endpoint" in details
    assert SENTINEL_TOKEN not in output
    assert not (config_home / "gitlab.json").exists()
    assert first.read_bytes() == first_bytes
    assert second.read_bytes() == second_bytes
    assert fake_requests.calls == []


@pytest.mark.parametrize("keyring_result", ["missing", "backend-failure"])
def test_unusable_keyring_candidate_fails_without_stable_mutation_source_mutation_or_network(
    keyring_result: str,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    isolated_runtime: tuple[Path, FakeKeyring, FakeRequests],
) -> None:
    config_home, fake_keyring, fake_requests = isolated_runtime
    home = arrange_home(config_home, monkeypatch)
    skill_root = relocated_skill(tmp_path, f"unusable-{keyring_result}")
    source_bytes = legacy_keyring_env()
    source = write_legacy_env(legacy_roots(skill_root, home)["agents-root"], source_bytes)
    if keyring_result == "backend-failure":
        def fail_get_password(service: str, username: str) -> str | None:
            fake_keyring.get_calls.append((service, username))
            raise FakeKeyringError("injected keyring backend failure")

        monkeypatch.setattr(sys.modules["keyring"], "get_password", fail_get_password)

    with pytest.raises(SystemExit) as exc_info:
        load_script(skill_root, "gitlab_cli", monkeypatch).resolve_runtime_config()

    assert exc_info.value.code != 0
    assert fake_keyring.get_calls == [(SERVICE_NAME, "legacy-gitlab-user")]
    assert not (config_home / "gitlab.json").exists()
    assert source.read_bytes() == source_bytes
    assert fake_requests.calls == []


def test_direct_token_legacy_env_remains_usable_fallback_and_is_not_migrated(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    isolated_runtime: tuple[Path, FakeKeyring, FakeRequests],
) -> None:
    config_home, fake_keyring, fake_requests = isolated_runtime
    arrange_home(config_home, monkeypatch)
    skill_root = relocated_skill(tmp_path, "direct-token-fallback")
    source_bytes = (
        "# direct token remains only in this legacy file\n"
        "GITLAB_API_URL=https://direct-gitlab.example.test/api/v4/\n"
        f"GITLAB_PERSONAL_ACCESS_TOKEN={SENTINEL_TOKEN}\n"
        "GITLAB_PROJECT_ID=42\n"
        "GITLAB_ALLOWED_PROJECT_IDS=42,84\n"
        "GITLAB_READ_ONLY_MODE=true\n"
        "GITLAB_TIMEOUT=19\n"
    ).encode("utf-8")
    source = write_legacy_env(skill_root, source_bytes)

    client = load_script(skill_root, "gitlab_cli", monkeypatch)
    with pytest.raises(SystemExit) as exc_info:
        client.request("get_project", {}, runtime=client.resolve_runtime_config())

    assert exc_info.value.code == 0
    assert fake_keyring.get_calls == []
    assert fake_requests.calls[0]["url"] == "https://direct-gitlab.example.test/api/v4/projects/42"
    assert fake_requests.calls[0]["headers"]["PRIVATE-TOKEN"] == SENTINEL_TOKEN
    assert not (config_home / "gitlab.json").exists()
    assert source.read_bytes() == source_bytes


def test_existing_stable_metadata_skips_legacy_discovery_and_preserves_all_bytes(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    isolated_runtime: tuple[Path, FakeKeyring, FakeRequests],
) -> None:
    config_home, fake_keyring, fake_requests = isolated_runtime
    home = arrange_home(config_home, monkeypatch)
    config_path = write_profile(config_home)
    stable_bytes = config_path.read_bytes()
    skill_root = relocated_skill(tmp_path, "stable-exists")
    source_bytes = legacy_keyring_env(endpoint="https://ignored.example.test/api/v4/")
    source = write_legacy_env(legacy_roots(skill_root, home)["copilot-root"], source_bytes)

    load_script(skill_root, "gitlab_cli", monkeypatch).resolve_runtime_config()

    assert config_path.read_bytes() == stable_bytes
    assert source.read_bytes() == source_bytes
    assert fake_keyring.get_calls == []
    assert fake_requests.calls == []


def test_help_skips_migration_without_keyring_network_or_file_mutation(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    isolated_runtime: tuple[Path, FakeKeyring, FakeRequests],
) -> None:
    config_home, fake_keyring, fake_requests = isolated_runtime
    home = arrange_home(config_home, monkeypatch)
    skill_root = relocated_skill(tmp_path, "help")
    source_bytes = legacy_keyring_env()
    source = write_legacy_env(legacy_roots(skill_root, home)["executing-root"], source_bytes)
    fake_keyring.passwords[(SERVICE_NAME, "legacy-gitlab-user")] = SENTINEL_TOKEN
    monkeypatch.setattr(sys, "argv", ["gitlab_cli.py", "--help"])

    client = load_script(skill_root, "gitlab_cli", monkeypatch)
    with pytest.raises(SystemExit) as exc_info:
        client.main()

    assert exc_info.value.code == 0
    assert not (config_home / "gitlab.json").exists()
    assert source.read_bytes() == source_bytes
    assert fake_keyring.get_calls == []
    assert fake_requests.calls == []
