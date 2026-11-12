"""RED tests for Task 8: non-destructive Black Duck legacy migration."""
from __future__ import annotations

import io
import json
import os
import subprocess
import sys
from contextlib import redirect_stdout
from pathlib import Path

import pytest

from test_blackduck_credential_config import (
    SERVICE_NAME, SENTINEL_TOKEN, FakeKeyring, FakeKeyringError, FakeSession,
    isolated_runtime, load_script, profile_document, relocated_skill, write_profile,
)


def legacy_keyring_env(*, endpoint: str = "https://legacy-blackduck.example.test/", user: str = "legacy-user", verify: str = "false") -> bytes:
    return (
        "# retained legacy Black Duck configuration\r\n"
        f"BLACKDUCK_URL={endpoint}\r\n"
        f"BLACKDUCK_TOKEN_KEYRING_USER={user}\r\n"
        f"BLACKDUCK_VERIFY_SSL={verify}\r\n"
    ).encode("utf-8")


def write_env(root: Path, content: bytes) -> Path:
    root.mkdir(parents=True, exist_ok=True)
    path = root / ".env"
    path.write_bytes(content)
    return path


def roots(skill_root: Path, home: Path) -> dict[str, Path]:
    return {
        "executing": skill_root,
        "copilot": home / ".copilot" / "skills" / "blackduck",
        "agents": home / ".agents" / "skills" / "blackduck",
    }


def arrange_home(config_home: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    home = config_home.parent / "migration-home"
    monkeypatch.setenv("HOME", str(home))
    monkeypatch.setenv("USERPROFILE", str(home))
    return home


@pytest.mark.parametrize("root_name", ["executing", "copilot", "agents"])
def test_every_exact_legacy_root_migrates_usable_keyring_metadata_without_source_mutation(root_name: str, tmp_path: Path, monkeypatch: pytest.MonkeyPatch, isolated_runtime: tuple[Path, FakeKeyring]) -> None:
    config_home, keyring = isolated_runtime
    home = arrange_home(config_home, monkeypatch)
    skill_root = relocated_skill(tmp_path, f"exact-{root_name}")
    source_bytes = legacy_keyring_env()
    source = write_env(roots(skill_root, home)[root_name], source_bytes)
    keyring.passwords[(SERVICE_NAME, "legacy-user")] = SENTINEL_TOKEN

    load_script(skill_root, "blackduck_vulnerabilities", monkeypatch).resolve_runtime_config()

    assert json.loads((config_home / "blackduck.json").read_text(encoding="utf-8")) == profile_document(
        endpoint="https://legacy-blackduck.example.test", keyring_user="legacy-user", verify_ssl="false"
    )
    assert keyring.get_calls == [(SERVICE_NAME, "legacy-user")]
    assert source.read_bytes() == source_bytes
    assert FakeSession.instances == []


def test_equivalent_candidates_migrate_once_and_are_not_rechecked_after_stable_metadata(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, isolated_runtime: tuple[Path, FakeKeyring]) -> None:
    config_home, keyring = isolated_runtime
    home = arrange_home(config_home, monkeypatch)
    skill_root = relocated_skill(tmp_path, "equivalent")
    source_bytes = legacy_keyring_env()
    sources = [write_env(root, source_bytes) for root in roots(skill_root, home).values()]
    keyring.passwords[(SERVICE_NAME, "legacy-user")] = SENTINEL_TOKEN

    load_script(skill_root, "blackduck_vulnerabilities", monkeypatch).resolve_runtime_config()
    path = config_home / "blackduck.json"
    migrated = path.read_bytes()
    keyring.get_calls.clear()
    load_script(skill_root, "blackduck_vulnerabilities", monkeypatch).resolve_runtime_config()

    assert path.read_bytes() == migrated
    assert list(json.loads(migrated)["profiles"]) == ["default"]
    assert keyring.get_calls == []
    assert all(source.read_bytes() == source_bytes for source in sources)
    assert FakeSession.instances == []


def test_canonical_path_alias_is_deduplicated_not_treated_as_conflict(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, isolated_runtime: tuple[Path, FakeKeyring]) -> None:
    config_home, keyring = isolated_runtime
    home = arrange_home(config_home, monkeypatch)
    skill_root = relocated_skill(tmp_path, "alias")
    source_bytes = legacy_keyring_env()
    source = write_env(skill_root, source_bytes)
    alias = roots(skill_root, home)["copilot"]
    alias.parent.mkdir(parents=True, exist_ok=True)
    try:
        alias.symlink_to(skill_root, target_is_directory=True)
    except (NotImplementedError, OSError) as error:
        if os.name != "nt":
            pytest.skip(f"directory aliases unavailable: {error}")
        result = subprocess.run(["cmd", "/c", "mklink", "/J", str(alias), str(skill_root)], capture_output=True, text=True)
        if result.returncode:
            pytest.skip(f"directory aliases unavailable: {error}; {result.stderr}")
    keyring.passwords[(SERVICE_NAME, "legacy-user")] = SENTINEL_TOKEN

    load_script(skill_root, "blackduck_vulnerabilities", monkeypatch).resolve_runtime_config()

    assert (config_home / "blackduck.json").is_file()
    assert keyring.get_calls == [(SERVICE_NAME, "legacy-user")]
    assert source.read_bytes() == source_bytes


def test_conflicting_candidates_fail_with_non_secret_paths_and_fields_and_preserve_bytes(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str], isolated_runtime: tuple[Path, FakeKeyring]) -> None:
    config_home, keyring = isolated_runtime
    home = arrange_home(config_home, monkeypatch)
    skill_root = relocated_skill(tmp_path, "conflict")
    candidates = roots(skill_root, home)
    first_bytes = legacy_keyring_env(endpoint="https://first.example.test/")
    second_bytes = legacy_keyring_env(endpoint="https://second.example.test/")
    first = write_env(candidates["executing"], first_bytes)
    second = write_env(candidates["copilot"], second_bytes)
    keyring.passwords[(SERVICE_NAME, "legacy-user")] = SENTINEL_TOKEN

    with pytest.raises(SystemExit) as exc:
        load_script(skill_root, "blackduck_vulnerabilities", monkeypatch).resolve_runtime_config()

    captured = capsys.readouterr()
    output = captured.out + captured.err
    assert exc.value.code != 0
    assert str(first) in output and str(second) in output and "endpoint" in output
    assert SENTINEL_TOKEN not in output
    assert not (config_home / "blackduck.json").exists()
    assert first.read_bytes() == first_bytes and second.read_bytes() == second_bytes
    assert FakeSession.instances == []


@pytest.mark.parametrize("keyring_result", ["missing", "backend-failure"])
def test_unusable_keyring_candidate_fails_without_stable_or_source_mutation_or_http(keyring_result: str, tmp_path: Path, monkeypatch: pytest.MonkeyPatch, isolated_runtime: tuple[Path, FakeKeyring]) -> None:
    config_home, keyring = isolated_runtime
    home = arrange_home(config_home, monkeypatch)
    skill_root = relocated_skill(tmp_path, f"unusable-{keyring_result}")
    source_bytes = legacy_keyring_env()
    source = write_env(roots(skill_root, home)["agents"], source_bytes)
    if keyring_result == "backend-failure":
        def fail(service: str, user: str) -> str | None:
            keyring.get_calls.append((service, user))
            raise FakeKeyringError("injected backend failure")
        monkeypatch.setattr(sys.modules["keyring"], "get_password", fail)

    with pytest.raises(SystemExit) as exc:
        load_script(skill_root, "blackduck_vulnerabilities", monkeypatch).resolve_runtime_config()

    assert exc.value.code != 0
    assert keyring.get_calls == [(SERVICE_NAME, "legacy-user")]
    assert not (config_home / "blackduck.json").exists()
    assert source.read_bytes() == source_bytes
    assert FakeSession.instances == []


def test_direct_token_file_remains_usable_but_is_never_migrated(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, isolated_runtime: tuple[Path, FakeKeyring]) -> None:
    config_home, keyring = isolated_runtime
    arrange_home(config_home, monkeypatch)
    skill_root = relocated_skill(tmp_path, "direct")
    source_bytes = (
        "# direct token remains in legacy source only\n"
        "BLACKDUCK_URL=https://direct-blackduck.example.test/\n"
        f"BLACKDUCK_TOKEN={SENTINEL_TOKEN}\n"
        "BLACKDUCK_VERIFY_SSL=false\n"
    ).encode("utf-8")
    source = write_env(skill_root, source_bytes)

    def load_test_dotenv(path: str | Path, *_args: object, **_kwargs: object) -> bool:
        for line in Path(path).read_text(encoding="utf-8").splitlines():
            if line and not line.startswith("#") and "=" in line:
                key, value = line.split("=", 1)
                os.environ.setdefault(key, value)
        return True
    monkeypatch.setattr(sys.modules["dotenv"], "load_dotenv", load_test_dotenv)

    client = load_script(skill_root, "blackduck_vulnerabilities", monkeypatch)
    with redirect_stdout(io.StringIO()):
        client.main(["list-projects", "--limit", "1"])

    session = FakeSession.instances[-1]
    assert session.verify is False
    assert session.posts[0]["url"] == "https://direct-blackduck.example.test/api/tokens/authenticate"
    assert session.posts[0]["headers"]["Authorization"] == f"token {SENTINEL_TOKEN}"
    assert keyring.get_calls == []
    assert not (config_home / "blackduck.json").exists()
    assert source.read_bytes() == source_bytes


def test_existing_stable_metadata_skips_discovery_and_preserves_stable_and_source_bytes(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, isolated_runtime: tuple[Path, FakeKeyring]) -> None:
    config_home, keyring = isolated_runtime
    home = arrange_home(config_home, monkeypatch)
    path = write_profile(config_home)
    stable_bytes = path.read_bytes()
    skill_root = relocated_skill(tmp_path, "stable")
    source_bytes = legacy_keyring_env(endpoint="https://ignored.example.test/")
    source = write_env(roots(skill_root, home)["copilot"], source_bytes)

    load_script(skill_root, "blackduck_vulnerabilities", monkeypatch).resolve_runtime_config()

    assert path.read_bytes() == stable_bytes
    assert source.read_bytes() == source_bytes
    assert keyring.get_calls == []
    assert FakeSession.instances == []


def test_import_has_no_configuration_migration_keyring_or_http_side_effects(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    isolated_runtime: tuple[Path, FakeKeyring],
) -> None:
    config_home, keyring = isolated_runtime
    home = arrange_home(config_home, monkeypatch)
    skill_root = relocated_skill(tmp_path, "side-effect-free-import")
    source_bytes = legacy_keyring_env()
    source = write_env(roots(skill_root, home)["executing"], source_bytes)
    keyring.passwords[(SERVICE_NAME, "legacy-user")] = SENTINEL_TOKEN

    load_script(skill_root, "blackduck_vulnerabilities", monkeypatch)

    assert not (config_home / "blackduck.json").exists()
    assert source.read_bytes() == source_bytes
    assert keyring.get_calls == []
    assert FakeSession.instances == []


def test_help_skips_migration_keyring_and_http_and_preserves_source(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, isolated_runtime: tuple[Path, FakeKeyring]) -> None:
    config_home, keyring = isolated_runtime
    home = arrange_home(config_home, monkeypatch)
    skill_root = relocated_skill(tmp_path, "help")
    source_bytes = legacy_keyring_env()
    source = write_env(roots(skill_root, home)["executing"], source_bytes)
    keyring.passwords[(SERVICE_NAME, "legacy-user")] = SENTINEL_TOKEN
    monkeypatch.setattr(sys, "argv", ["blackduck_vulnerabilities.py", "--help"])

    client = load_script(skill_root, "blackduck_vulnerabilities", monkeypatch)
    with pytest.raises(SystemExit) as exc:
        client.main()

    assert exc.value.code == 0
    assert not (config_home / "blackduck.json").exists()
    assert source.read_bytes() == source_bytes
    assert keyring.get_calls == []
    assert FakeSession.instances == []
