"""RED tests for Task 2d: Octane profile locking and write durability.

These tests intentionally exclude migration, profile selection precedence, and
Octane API behavior.  Cross-process tests exercise the token helper as the
public mutation boundary; filesystem fault injection is limited to observable
OS write boundaries.
"""
from __future__ import annotations

import json
import os
import stat
import subprocess
import sys
import time
from pathlib import Path
from typing import Any

import pytest

from test_octane_credential_config import (
    FakeKeyring,
    isolated_runtime,
    load_script,
    profile_document,
    relocated_skill,
    write_profile,
)


def _profile(name: str) -> dict[str, Any]:
    return {
        "keyring_user": f"{name}-client",
        "endpoint": f"https://{name}.example.test",
        "settings": {"shared_space_id": "1", "workspace_id": "2", "timeout": "3"},
    }


def _document_with_two_profiles() -> dict[str, Any]:
    document = profile_document()
    document["profiles"]["zulu"] = _profile("zulu")
    return document


def _lock_path(config_home: Path) -> Path:
    return config_home / "octane.json.lock"


def _write_fake_keyring(fake_modules: Path) -> None:
    package = fake_modules / "keyring"
    package.mkdir(parents=True)
    (package / "__init__.py").write_text(
        "import json, os\n"
        "from pathlib import Path\n"
        "def _path(): return Path(os.environ['FAKE_KEYRING_PATH'])\n"
        "def _read(): return json.loads(_path().read_text()) if _path().is_file() else {}\n"
        "def get_password(service, username): return _read().get(service + '|' + username)\n"
        "def set_password(service, username, password):\n"
        "    values = _read(); values[service + '|' + username] = password; _path().write_text(json.dumps(values))\n"
        "def delete_password(service, username):\n"
        "    values = _read(); values.pop(service + '|' + username, None); _path().write_text(json.dumps(values))\n",
        encoding="utf-8",
    )
    (package / "errors.py").write_text(
        "class KeyringError(Exception): pass\n"
        "class PasswordDeleteError(KeyringError): pass\n",
        encoding="utf-8",
    )


def _subprocess_env(config_home: Path, fake_modules: Path) -> dict[str, str]:
    env = os.environ.copy()
    env["AGENT_DEVELOPMENT_TOOLKIT_CONFIG_HOME"] = str(config_home)
    env["FAKE_KEYRING_PATH"] = str(fake_modules / "fake-keyring.json")
    env["PYTHONPATH"] = os.pathsep.join(
        part for part in (str(fake_modules), env.get("PYTHONPATH", "")) if part
    )
    for name in list(env):
        if name.startswith("OCTANE_"):
            del env[name]
    return env


def _login_command(skill_root: Path, profile_name: str) -> list[str]:
    return [
        sys.executable,
        str(skill_root / "scripts" / "octane_token.py"),
        "login",
        "--profile",
        profile_name,
        "--user",
        f"{profile_name}-client",
        "--secret",
        "process-local-test-secret",
        "--base-url",
        f"https://{profile_name}.example.test",
        "--shared-space-id",
        "1",
        "--workspace-id",
        "2",
        "--timeout",
        "3",
        "--skip-test",
    ]


def _config_artifacts(config_home: Path) -> list[Path]:
    if not config_home.exists():
        return []
    return sorted(path for path in config_home.iterdir() if path.name != "octane.json")


def test_cross_process_lock_contention_times_out_without_mutating_prior_bytes(
    tmp_path: Path,
    isolated_runtime: tuple[Path, FakeKeyring],
) -> None:
    config_home, _ = isolated_runtime
    config_path = write_profile(config_home, _document_with_two_profiles())
    prior_bytes = config_path.read_bytes()
    skill_root = relocated_skill(tmp_path, "contended-install")
    lock_path = _lock_path(config_home)
    ready = tmp_path / "lock-ready"
    release = tmp_path / "lock-release"
    holder_code = """
import os, sys, time
from pathlib import Path
lock, ready, release = map(Path, sys.argv[1:])
fd = os.open(str(lock), os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
try:
    ready.write_text('ready', encoding='utf-8')
    deadline = time.monotonic() + 10
    while not release.exists() and time.monotonic() < deadline:
        time.sleep(0.01)
finally:
    os.close(fd)
    lock.unlink(missing_ok=True)
"""
    holder = subprocess.Popen(
        [sys.executable, "-c", holder_code, str(lock_path), str(ready), str(release)]
    )
    try:
        deadline = time.monotonic() + 2
        while not ready.exists() and time.monotonic() < deadline:
            time.sleep(0.01)
        assert ready.exists(), "lock-holder process did not become ready"

        started = time.monotonic()
        result = subprocess.run(
            [
                sys.executable,
                str(skill_root / "scripts" / "octane_token.py"),
                "use-profile",
                "--profile",
                "zulu",
            ],
            env=_subprocess_env(config_home, tmp_path / "unused-modules"),
            capture_output=True,
            text=True,
            timeout=3,
        )
        elapsed = time.monotonic() - started

        assert result.returncode != 0
        assert elapsed < 3
        assert config_path.read_bytes() == prior_bytes
        assert [path for path in _config_artifacts(config_home) if path != lock_path] == []
        assert lock_path.exists(), "a contender must not remove another process's lock"
    finally:
        release.touch()
        holder.wait(timeout=2)

    assert _config_artifacts(config_home) == []


def test_successful_profile_mutations_release_the_cross_process_lock(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    isolated_runtime: tuple[Path, FakeKeyring],
) -> None:
    config_home, _ = isolated_runtime
    write_profile(config_home, _document_with_two_profiles())
    token = load_script(relocated_skill(tmp_path, "successful-mutations"), "octane_token", monkeypatch)

    monkeypatch.setattr(sys, "argv", ["octane_token.py", "use-profile", "--profile", "zulu"])
    assert token.main() == 0
    monkeypatch.setattr(sys, "argv", ["octane_token.py", "delete-profile", "--profile", "default"])
    assert token.main() == 0

    assert _config_artifacts(config_home) == []


def test_concurrent_successful_logins_do_not_lose_either_profile(
    tmp_path: Path,
    isolated_runtime: tuple[Path, FakeKeyring],
) -> None:
    config_home, _ = isolated_runtime
    write_profile(config_home)
    skill_root = relocated_skill(tmp_path, "concurrent-install")
    fake_modules = tmp_path / "fake-modules"
    _write_fake_keyring(fake_modules)
    env = _subprocess_env(config_home, fake_modules)
    first_at_replace = tmp_path / "first-at-replace"

    first_worker = """
import os, runpy, sys, time
from pathlib import Path
script, config_path, marker, *arguments = sys.argv[1:]
sys.path.insert(0, str(Path(script).parent))
real_replace = os.replace
def delayed_replace(source, destination):
    if Path(destination) == Path(config_path):
        marker_path = Path(marker)
        if not marker_path.exists():
            marker_path.write_text('ready', encoding='utf-8')
            time.sleep(0.4)
    return real_replace(source, destination)
os.replace = delayed_replace
sys.argv = [script, *arguments]
runpy.run_path(script, run_name='__main__')
"""
    first = subprocess.Popen(
        [
            sys.executable,
            "-c",
            first_worker,
            str(skill_root / "scripts" / "octane_token.py"),
            str(config_home / "octane.json"),
            str(first_at_replace),
            *_login_command(skill_root, "alpha")[2:],
        ],
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    try:
        deadline = time.monotonic() + 2
        while not first_at_replace.exists() and time.monotonic() < deadline:
            time.sleep(0.01)
        assert first_at_replace.exists(), "first mutation did not reach atomic replacement"
        second = subprocess.run(
            _login_command(skill_root, "bravo"),
            env=env,
            capture_output=True,
            text=True,
            timeout=3,
        )
        first_stdout, first_stderr = first.communicate(timeout=3)
    finally:
        if first.poll() is None:
            first.kill()
            first.wait()

    assert first.returncode == 0, first_stderr or first_stdout
    assert second.returncode == 0, second.stderr or second.stdout
    stored = json.loads((config_home / "octane.json").read_text(encoding="utf-8"))
    assert {"default", "alpha", "bravo"} <= set(stored["profiles"])
    assert _config_artifacts(config_home) == []


def test_failed_atomic_replace_preserves_exact_prior_bytes_and_cleans_artifacts(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    isolated_runtime: tuple[Path, FakeKeyring],
) -> None:
    config_home, _ = isolated_runtime
    config_path = write_profile(config_home, _document_with_two_profiles())
    prior_bytes = config_path.read_bytes()
    config = load_script(relocated_skill(tmp_path, "replace-failure"), "credential_config", monkeypatch)
    real_replace = config.os.replace

    def fail_target_replace(source: Any, destination: Any) -> None:
        if Path(destination) == config_path:
            raise OSError("injected replacement failure")
        real_replace(source, destination)

    monkeypatch.setattr(config.os, "replace", fail_target_replace)

    with pytest.raises(config.ConfigError, match="write"):
        config.select_profile("zulu")

    assert config_path.read_bytes() == prior_bytes
    assert _config_artifacts(config_home) == []


def test_write_document_uses_utf8_fsync_and_atomic_sibling_replacement(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    isolated_runtime: tuple[Path, FakeKeyring],
) -> None:
    config_home, _ = isolated_runtime
    config = load_script(relocated_skill(tmp_path, "observable-write"), "credential_config", monkeypatch)
    document = profile_document(endpoint="https://例え.example.test", keyring_user="développeur")
    fsync_calls: list[int] = []
    replacements: list[tuple[Path, Path]] = []
    real_fsync = config.os.fsync
    real_replace = config.os.replace

    def observed_fsync(fd: int) -> None:
        fsync_calls.append(fd)
        real_fsync(fd)

    def observed_replace(source: Any, destination: Any) -> None:
        replacements.append((Path(source), Path(destination)))
        real_replace(source, destination)

    monkeypatch.setattr(config.os, "fsync", observed_fsync)
    monkeypatch.setattr(config.os, "replace", observed_replace)

    config.write_document(document)

    config_path = config_home / "octane.json"
    raw = config_path.read_bytes()
    assert json.loads(raw.decode("utf-8")) == document
    assert "例え" in raw.decode("utf-8")
    assert "développeur" in raw.decode("utf-8")
    assert fsync_calls
    assert replacements == [(replacements[0][0], config_path)]
    assert replacements[0][0].parent == config_path.parent
    assert replacements[0][0] != config_path
    assert not replacements[0][0].exists()
    assert _config_artifacts(config_home) == []


@pytest.mark.skipif(os.name == "nt", reason="POSIX permission bits are not supported on Windows")
def test_successful_profile_write_has_user_only_posix_permissions(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    isolated_runtime: tuple[Path, FakeKeyring],
) -> None:
    config_home, _ = isolated_runtime
    config = load_script(relocated_skill(tmp_path, "private-mode"), "credential_config", monkeypatch)

    config.write_document(profile_document())

    mode = stat.S_IMODE((config_home / "octane.json").stat().st_mode)
    assert mode == 0o600
