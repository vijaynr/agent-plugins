"""RED contract tests for Black Duck's durable default-profile credential path.

All plugin roots, process configuration, keyring state, and HTTP sessions are
isolated. The tests load relocated script copies with no plugin-local .env and
never access the real network or operating-system credential store.
"""
from __future__ import annotations

import importlib.util
import io
import json
import os
import shutil
import sys
import types
import uuid
from contextlib import redirect_stdout
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

import pytest


SKILL_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS_ROOT = SKILL_ROOT / "scripts"
SERVICE_NAME = "AgentDevelopmentToolkit:blackduck"
SENTINEL_TOKEN = "blackduck-test-token-MUST-NOT-BE-SERIALIZED"
BLACKDUCK_URL = "https://blackduck.internal.example"
KEYRING_USER = "blackduck-default-credential"


class FakeKeyringError(Exception):
    pass


class FakePasswordDeleteError(FakeKeyringError):
    pass


class FakeKeyring:
    def __init__(self) -> None:
        self.passwords: dict[tuple[str, str], str] = {}
        self.fail_set = False
        self.get_calls: list[tuple[str, str]] = []
        self.delete_calls: list[tuple[str, str]] = []

    def get_password(self, service: str, username: str) -> str | None:
        self.get_calls.append((service, username))
        return self.passwords.get((service, username))

    def set_password(self, service: str, username: str, password: str) -> None:
        if self.fail_set:
            raise FakeKeyringError("injected keyring write failure")
        self.passwords[(service, username)] = password

    def delete_password(self, service: str, username: str) -> None:
        self.delete_calls.append((service, username))
        try:
            del self.passwords[(service, username)]
        except KeyError as exc:
            raise FakePasswordDeleteError("missing test credential") from exc


class FakeResponse:
    def __init__(
        self,
        data: dict[str, Any] | None = None,
        *,
        headers: dict[str, str] | None = None,
        status_code: int = 200,
    ) -> None:
        self.status_code = status_code
        self._data = data or {}
        self.headers = headers or {}
        self.text = json.dumps(self._data)

    def json(self) -> dict[str, Any]:
        return self._data


class FakeSession:
    instances: list["FakeSession"] = []

    def __init__(self) -> None:
        self.verify = True
        self.posts: list[dict[str, Any]] = []
        self.gets: list[dict[str, Any]] = []
        self.__class__.instances.append(self)

    def post(self, url: str, **kwargs: Any) -> FakeResponse:
        self.posts.append({"url": url, **kwargs})
        return FakeResponse(
            {"bearerToken": "fake-bearer", "expiresInMilliseconds": 7200000},
            headers={"X-CSRF-TOKEN": "fake-csrf"},
        )

    def get(self, url: str, **kwargs: Any) -> FakeResponse:
        self.gets.append({"url": url, **kwargs})
        return FakeResponse({"totalCount": 0, "items": []})


@pytest.fixture
def isolated_runtime(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> tuple[Path, FakeKeyring]:
    config_home = tmp_path / "durable-config"
    home = tmp_path / "home"
    home.mkdir()

    for name in list(sys.modules):
        if name == "credential_config" or name.startswith("blackduck_config_test_"):
            monkeypatch.delitem(sys.modules, name, raising=False)

    for name in list(os.environ):
        if name.startswith("BLACKDUCK_") or name in {
            "AGENT_DEVELOPMENT_TOOLKIT_CONFIG_HOME",
            "APPDATA",
            "XDG_CONFIG_HOME",
        }:
            monkeypatch.delenv(name, raising=False)
    monkeypatch.setenv("AGENT_DEVELOPMENT_TOOLKIT_CONFIG_HOME", str(config_home))
    monkeypatch.setenv("HOME", str(home))

    fake_keyring = FakeKeyring()
    keyring_module = types.ModuleType("keyring")
    keyring_module.get_password = fake_keyring.get_password  # type: ignore[attr-defined]
    keyring_module.set_password = fake_keyring.set_password  # type: ignore[attr-defined]
    keyring_module.delete_password = fake_keyring.delete_password  # type: ignore[attr-defined]
    errors_module = types.ModuleType("keyring.errors")
    errors_module.KeyringError = FakeKeyringError  # type: ignore[attr-defined]
    errors_module.PasswordDeleteError = FakePasswordDeleteError  # type: ignore[attr-defined]
    monkeypatch.setitem(sys.modules, "keyring", keyring_module)
    monkeypatch.setitem(sys.modules, "keyring.errors", errors_module)

    requests_module = types.ModuleType("requests")
    requests_module.Session = FakeSession  # type: ignore[attr-defined]
    requests_module.RequestException = RuntimeError  # type: ignore[attr-defined]
    monkeypatch.setitem(sys.modules, "requests", requests_module)

    dotenv_module = types.ModuleType("dotenv")
    dotenv_module.load_dotenv = lambda *_args, **_kwargs: False  # type: ignore[attr-defined]
    monkeypatch.setitem(sys.modules, "dotenv", dotenv_module)
    FakeSession.instances.clear()
    return config_home, fake_keyring


def relocated_skill(tmp_path: Path, name: str) -> Path:
    """Create an installed-skill image containing scripts but no .env."""
    root = tmp_path / name / "blackduck"
    scripts = root / "scripts"
    scripts.mkdir(parents=True)
    (root / "SKILL.md").write_text("---\nname: blackduck\n---\n", encoding="utf-8")
    for source in SCRIPTS_ROOT.glob("*.py"):
        shutil.copy2(source, scripts / source.name)
    return root


def load_script(
    skill_root: Path,
    script_name: str,
    monkeypatch: pytest.MonkeyPatch,
) -> types.ModuleType:
    """Load a relocated script while allowing only its adjacent local imports."""
    module_name = f"blackduck_config_test_{script_name}_{uuid.uuid4().hex}"
    script_path = skill_root / "scripts" / f"{script_name}.py"
    monkeypatch.syspath_prepend(str(script_path.parent))
    sys.modules.pop("credential_config", None)
    spec = importlib.util.spec_from_file_location(module_name, script_path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


def profile_document(
    endpoint: str = BLACKDUCK_URL,
    keyring_user: str = KEYRING_USER,
    verify_ssl: str = "false",
) -> dict[str, Any]:
    return {
        "schema_version": 1,
        "active_profile": "default",
        "profiles": {
            "default": {
                "keyring_user": keyring_user,
                "endpoint": endpoint,
                "settings": {"verify_ssl": verify_ssl},
            }
        },
    }


def write_profile(config_home: Path, document: dict[str, Any] | None = None) -> Path:
    config_home.mkdir(parents=True, exist_ok=True)
    path = config_home / "blackduck.json"
    path.write_text(json.dumps(document or profile_document()), encoding="utf-8")
    return path


def login_with_defaults(token_module: types.ModuleType, *, skip_test: bool = True) -> int:
    return token_module.login(
        username=KEYRING_USER,
        token_arg=SENTINEL_TOKEN,
        url_arg=f"{BLACKDUCK_URL}/",
        verify_ssl_arg="false",
        skip_test=skip_test,
    )


def invoke_list_projects(client: types.ModuleType) -> None:
    with redirect_stdout(io.StringIO()):
        client.main(["list-projects", "--limit", "1"])


def assert_no_secret_keys(value: Any) -> None:
    if isinstance(value, dict):
        forbidden = {"secret", "client_secret", "password", "token", "api_token", "access_token"}
        assert forbidden.isdisjoint(key.lower() for key in value)
        for child in value.values():
            assert_no_secret_keys(child)
    elif isinstance(value, list):
        for child in value:
            assert_no_secret_keys(child)


def test_login_honors_stable_config_home_override(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    isolated_runtime: tuple[Path, FakeKeyring],
) -> None:
    config_home, _ = isolated_runtime
    skill_root = relocated_skill(tmp_path, "install-a")
    token_module = load_script(skill_root, "blackduck_token", monkeypatch)

    result = login_with_defaults(token_module)

    assert result == 0
    assert (config_home / "blackduck.json").is_file()
    assert not (skill_root / ".env").exists()


def test_login_writes_secret_free_default_profile_with_ssl_setting(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    isolated_runtime: tuple[Path, FakeKeyring],
) -> None:
    config_home, fake_keyring = isolated_runtime
    token_module = load_script(relocated_skill(tmp_path, "install-a"), "blackduck_token", monkeypatch)

    assert login_with_defaults(token_module) == 0
    serialized = (config_home / "blackduck.json").read_text(encoding="utf-8")
    document = json.loads(serialized)

    assert document == profile_document()
    assert SENTINEL_TOKEN not in serialized
    assert_no_secret_keys(document)
    assert fake_keyring.passwords[(SERVICE_NAME, KEYRING_USER)] == SENTINEL_TOKEN


@pytest.mark.parametrize(
    ("raw", "expected"),
    [("true", "true"), ("1", "true"), ("YES", "true"), ("false", "false"), ("0", "false"), ("No", "false")],
)
def test_ssl_boolean_aliases_normalize_to_canonical_profile_values(
    raw: str,
    expected: str,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    isolated_runtime: tuple[Path, FakeKeyring],
) -> None:
    config = load_script(relocated_skill(tmp_path, f"ssl-{raw}"), "credential_config", monkeypatch)
    assert config.normalize_verify_ssl(raw) == expected


def test_relocated_list_projects_uses_matching_profile_host_token_and_ssl_without_dotenv(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    isolated_runtime: tuple[Path, FakeKeyring],
) -> None:
    config_home, fake_keyring = isolated_runtime
    write_profile(config_home)
    fake_keyring.passwords[(SERVICE_NAME, KEYRING_USER)] = SENTINEL_TOKEN
    skill_root = relocated_skill(tmp_path, "replacement-install")
    assert not (skill_root / ".env").exists()
    client = load_script(skill_root, "blackduck_vulnerabilities", monkeypatch)

    invoke_list_projects(client)

    assert fake_keyring.get_calls == [(SERVICE_NAME, KEYRING_USER)]
    assert len(FakeSession.instances) == 1
    session = FakeSession.instances[0]
    assert session.verify is False
    assert session.posts == [{
        "url": f"{BLACKDUCK_URL}/api/tokens/authenticate",
        "headers": {
            "Authorization": f"token {SENTINEL_TOKEN}",
            "Accept": "application/vnd.blackducksoftware.user-4+json",
        },
        "allow_redirects": False,
        "timeout": client.REQUEST_TIMEOUT_SECONDS,
    }]
    assert urlparse(session.posts[0]["url"]).hostname == "blackduck.internal.example"
    assert session.gets[0]["url"] == f"{BLACKDUCK_URL}/api/projects"


def test_direct_url_and_token_environment_remain_available_without_a_profile(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    isolated_runtime: tuple[Path, FakeKeyring],
) -> None:
    config_home, fake_keyring = isolated_runtime
    direct_url = "https://blackduck-ci.example"
    direct_token = "blackduck-ci-direct-token"
    monkeypatch.setenv("BLACKDUCK_URL", direct_url)
    monkeypatch.setenv("BLACKDUCK_TOKEN", direct_token)
    monkeypatch.setenv("BLACKDUCK_VERIFY_SSL", "true")
    client = load_script(relocated_skill(tmp_path, "ci-install"), "blackduck_vulnerabilities", monkeypatch)

    invoke_list_projects(client)

    assert not (config_home / "blackduck.json").exists()
    assert fake_keyring.get_calls == []
    session = FakeSession.instances[0]
    assert session.verify is True
    assert session.posts[0]["url"] == f"{direct_url}/api/tokens/authenticate"
    assert session.posts[0]["headers"]["Authorization"] == f"token {direct_token}"
    assert session.gets[0]["url"] == f"{direct_url}/api/projects"


def test_remote_verification_targets_written_profile_without_legacy_or_process_overrides(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    isolated_runtime: tuple[Path, FakeKeyring],
) -> None:
    _, _ = isolated_runtime
    skill_root = relocated_skill(tmp_path, "verification-profile")
    (skill_root / ".env").write_text(
        "BLACKDUCK_URL=https://legacy.example\nBLACKDUCK_TOKEN=legacy-token\n",
        encoding="utf-8",
    )
    monkeypatch.setenv("BLACKDUCK_URL", "https://process.example")
    monkeypatch.setenv("BLACKDUCK_TOKEN", "process-token")
    token_module = load_script(skill_root, "blackduck_token", monkeypatch)
    captured: dict[str, Any] = {}

    def fake_run(command: list[str], **kwargs: Any) -> Any:
        captured["command"] = command
        captured["env"] = kwargs["env"]
        captured["timeout"] = kwargs["timeout"]
        return type("Result", (), {"returncode": 0, "stdout": "{}", "stderr": ""})()

    monkeypatch.setattr(token_module.subprocess, "run", fake_run)

    assert token_module.test_blackduck_credentials("staging") == 0
    assert captured["command"][-5:] == ["--profile", "staging", "list-projects", "--limit", "1"]
    assert not any(name.startswith("BLACKDUCK_") for name in captured["env"])
    assert captured["timeout"] == token_module.VERIFICATION_TIMEOUT_SECONDS


def test_successful_verification_rejects_a_concurrently_replaced_keyring_token(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    isolated_runtime: tuple[Path, FakeKeyring],
    capsys: pytest.CaptureFixture[str],
) -> None:
    _, fake_keyring = isolated_runtime
    token_module = load_script(relocated_skill(tmp_path, "superseded-secret"), "blackduck_token", monkeypatch)

    def replace_secret(_profile: str = "default") -> int:
        fake_keyring.set_password(SERVICE_NAME, KEYRING_USER, "newer-token")
        return 0

    monkeypatch.setattr(token_module, "test_blackduck_credentials", replace_secret)

    assert login_with_defaults(token_module, skip_test=False) != 0
    assert fake_keyring.passwords[(SERVICE_NAME, KEYRING_USER)] == "newer-token"
    assert "superseded" in capsys.readouterr().err.lower()


@pytest.mark.parametrize("failure_stage", ["keyring_write", "metadata_write", "remote_verification"])
def test_failed_login_restores_exact_prior_metadata_and_keyring_token(
    failure_stage: str,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    isolated_runtime: tuple[Path, FakeKeyring],
) -> None:
    config_home, fake_keyring = isolated_runtime
    prior_document = profile_document(endpoint="https://prior-blackduck.example", verify_ssl="true")
    config_path = write_profile(config_home, prior_document)
    prior_bytes = config_path.read_bytes()
    prior_token = "blackduck-exact-prior-token"
    fake_keyring.passwords[(SERVICE_NAME, KEYRING_USER)] = prior_token

    skill_root = relocated_skill(tmp_path, f"failed-{failure_stage}")
    token_module = load_script(skill_root, "blackduck_token", monkeypatch)
    if failure_stage == "keyring_write":
        fake_keyring.fail_set = True
    elif failure_stage == "metadata_write":
        real_replace = os.replace
        failed_once = False

        def fail_profile_replace(source: Any, destination: Any) -> None:
            nonlocal failed_once
            if Path(destination) == config_path and not failed_once:
                failed_once = True
                raise OSError("injected atomic metadata replacement failure")
            real_replace(source, destination)

        monkeypatch.setattr(os, "replace", fail_profile_replace)
    else:
        monkeypatch.setattr(token_module, "test_blackduck_credentials", lambda _profile="default": 1)

    result = login_with_defaults(
        token_module,
        skip_test=failure_stage != "remote_verification",
    )

    assert result != 0
    assert config_path.read_bytes() == prior_bytes
    assert json.loads(config_path.read_text(encoding="utf-8")) == prior_document
    assert fake_keyring.passwords[(SERVICE_NAME, KEYRING_USER)] == prior_token
    assert FakeSession.instances == []
    assert not (skill_root / ".env").exists()


def test_failed_verification_attempts_keyring_rollback_when_metadata_rollback_fails(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    isolated_runtime: tuple[Path, FakeKeyring],
) -> None:
    config_home, fake_keyring = isolated_runtime
    write_profile(config_home, profile_document(endpoint="https://prior-blackduck.example"))
    prior_token = "blackduck-exact-prior-token"
    fake_keyring.passwords[(SERVICE_NAME, KEYRING_USER)] = prior_token
    token_module = load_script(relocated_skill(tmp_path, "metadata-rollback-failure"), "blackduck_token", monkeypatch)
    monkeypatch.setattr(token_module, "test_blackduck_credentials", lambda _profile="default": 1)

    def fail_restore(_snapshot: bytes | None) -> None:
        raise token_module.ConfigError("injected metadata rollback failure")

    monkeypatch.setattr(token_module, "restore", fail_restore)

    assert login_with_defaults(token_module, skip_test=False) == 1
    assert fake_keyring.passwords[(SERVICE_NAME, KEYRING_USER)] == prior_token
    assert "rollback was incomplete" in capsys.readouterr().err


def test_failed_verification_restores_metadata_when_keyring_rollback_fails(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    isolated_runtime: tuple[Path, FakeKeyring],
) -> None:
    config_home, fake_keyring = isolated_runtime
    prior_document = profile_document(endpoint="https://prior-blackduck.example")
    config_path = write_profile(config_home, prior_document)
    prior_token = "blackduck-exact-prior-token"
    fake_keyring.passwords[(SERVICE_NAME, KEYRING_USER)] = prior_token
    token_module = load_script(relocated_skill(tmp_path, "keyring-rollback-failure"), "blackduck_token", monkeypatch)
    monkeypatch.setattr(token_module, "test_blackduck_credentials", lambda _profile="default": 1)
    real_set = fake_keyring.set_password

    def fail_prior_restore(service: str, username: str, password: str) -> None:
        if password == prior_token:
            raise FakeKeyringError("injected keyring rollback failure")
        real_set(service, username, password)

    monkeypatch.setattr(sys.modules["keyring"], "set_password", fail_prior_restore)

    assert login_with_defaults(token_module, skip_test=False) == 1
    assert json.loads(config_path.read_text(encoding="utf-8")) == prior_document
    assert fake_keyring.passwords[(SERVICE_NAME, KEYRING_USER)] == SENTINEL_TOKEN
    assert "rollback was incomplete" in capsys.readouterr().err


def test_verification_releases_lock_and_failed_rollback_preserves_concurrent_selection(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    isolated_runtime: tuple[Path, FakeKeyring],
) -> None:
    config_home, fake_keyring = isolated_runtime
    prior_document = profile_document(endpoint="https://prior-blackduck.example", verify_ssl="true")
    prior_document["profiles"]["zulu"] = {
        "keyring_user": "zulu-user",
        "endpoint": "https://zulu.example",
        "settings": {"verify_ssl": "true"},
    }
    config_path = write_profile(config_home, prior_document)
    prior_token = "blackduck-exact-prior-token"
    fake_keyring.passwords[(SERVICE_NAME, KEYRING_USER)] = prior_token
    token_module = load_script(relocated_skill(tmp_path, "unlocked-verification"), "blackduck_token", monkeypatch)

    def concurrent_selection(_profile: str = "default") -> int:
        token_module.select_profile("zulu")
        return 1

    monkeypatch.setattr(token_module, "test_blackduck_credentials", concurrent_selection)

    result = login_with_defaults(token_module, skip_test=False)

    stored = json.loads(config_path.read_text(encoding="utf-8"))
    assert result == 1
    assert stored["active_profile"] == "zulu"
    assert stored["profiles"]["default"]["endpoint"] == BLACKDUCK_URL
    assert fake_keyring.passwords[(SERVICE_NAME, KEYRING_USER)] == prior_token
