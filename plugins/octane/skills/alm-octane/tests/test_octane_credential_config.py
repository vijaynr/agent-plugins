"""RED contract tests for Octane's durable default-profile credential path.

All plugin roots, configuration, keyring state, and HTTP sessions are test-local.
The production implementation is intentionally not imported from the repository
root so relocation and replacement behavior can be exercised safely.
"""
from __future__ import annotations

import importlib.util
import json
import os
import shutil
import sys
import types
import uuid
from pathlib import Path
from typing import Any

import pytest


SKILL_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS_ROOT = SKILL_ROOT / "scripts"
SERVICE_NAME = "AgentDevelopmentToolkit:alm-octane"
SENTINEL_SECRET = "test-secret-MUST-NOT-BE-SERIALIZED"


class FakeKeyringError(Exception):
    pass


class FakePasswordDeleteError(FakeKeyringError):
    pass


class FakeKeyring:
    def __init__(self) -> None:
        self.passwords: dict[tuple[str, str], str] = {}
        self.fail_set = False
        self.get_calls: list[tuple[str, str]] = []

    def get_password(self, service: str, username: str) -> str | None:
        self.get_calls.append((service, username))
        return self.passwords.get((service, username))

    def set_password(self, service: str, username: str, password: str) -> None:
        if self.fail_set:
            raise FakeKeyringError("injected keyring write failure")
        self.passwords[(service, username)] = password

    def delete_password(self, service: str, username: str) -> None:
        try:
            del self.passwords[(service, username)]
        except KeyError as exc:
            raise FakePasswordDeleteError("missing test credential") from exc


class FakeResponse:
    ok = True
    status_code = 200
    text = '{"data": []}'
    headers = {"content-type": "application/json"}

    def json(self) -> dict[str, list[Any]]:
        return {"data": []}


class FakeSession:
    instances: list["FakeSession"] = []

    def __init__(self) -> None:
        self.headers: dict[str, str] = {}
        self.posts: list[dict[str, Any]] = []
        self.requests: list[dict[str, Any]] = []
        self.__class__.instances.append(self)

    def post(self, url: str, **kwargs: Any) -> FakeResponse:
        self.posts.append({"url": url, **kwargs})
        return FakeResponse()

    def request(self, method: str, url: str, **kwargs: Any) -> FakeResponse:
        self.requests.append({"method": method, "url": url, **kwargs})
        return FakeResponse()


@pytest.fixture
def isolated_runtime(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> tuple[Path, FakeKeyring]:
    config_home = tmp_path / "durable-config"
    home = tmp_path / "home"
    home.mkdir()

    for name in list(sys.modules):
        if name == "credential_config" or name.startswith("octane_test_"):
            monkeypatch.delitem(sys.modules, name, raising=False)

    for name in list(__import__("os").environ):
        if name.startswith("OCTANE_") or name in {
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

    def dotenv_values(path: Path, *_args: object, **_kwargs: object) -> dict[str, str]:
        values: dict[str, str] = {}
        for raw_line in Path(path).read_text(encoding="utf-8").splitlines():
            if raw_line and not raw_line.startswith("#") and "=" in raw_line:
                key, value = raw_line.split("=", 1)
                values[key.strip()] = value.strip()
        return values

    dotenv_module.dotenv_values = dotenv_values  # type: ignore[attr-defined]
    monkeypatch.setitem(sys.modules, "dotenv", dotenv_module)
    FakeSession.instances.clear()
    return config_home, fake_keyring


def relocated_skill(tmp_path: Path, name: str) -> Path:
    """Create a clean installed-skill image with no plugin-local .env."""
    root = tmp_path / name / "alm-octane"
    scripts = root / "scripts"
    scripts.mkdir(parents=True)
    (root / "SKILL.md").write_text("---\nname: alm-octane\n---\n", encoding="utf-8")
    for source in SCRIPTS_ROOT.glob("*.py"):
        shutil.copy2(source, scripts / source.name)
    return root


def load_script(skill_root: Path, script_name: str, monkeypatch: pytest.MonkeyPatch) -> types.ModuleType:
    """Load one relocated script while allowing adjacent plugin-local imports."""
    module_name = f"octane_test_{script_name}_{uuid.uuid4().hex}"
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
    endpoint: str = "https://octane.example.test",
    keyring_user: str = "client-id",
    shared_space_id: str = "131002",
    workspace_id: str = "1003",
    timeout: str = "17",
) -> dict[str, Any]:
    return {
        "schema_version": 1,
        "active_profile": "default",
        "profiles": {
            "default": {
                "keyring_user": keyring_user,
                "endpoint": endpoint,
                "settings": {
                    "shared_space_id": shared_space_id,
                    "workspace_id": workspace_id,
                    "timeout": timeout,
                },
            }
        },
    }


def write_profile(config_home: Path, document: dict[str, Any] | None = None) -> Path:
    config_home.mkdir(parents=True, exist_ok=True)
    path = config_home / "octane.json"
    path.write_text(json.dumps(document or profile_document()), encoding="utf-8")
    return path


def login_with_defaults(token: types.ModuleType, *, skip_test: bool = True) -> int:
    return token.login(
        username="client-id",
        secret_arg=SENTINEL_SECRET,
        base_url_arg="https://octane.example.test/",
        shared_space_id_arg="131002",
        workspace_id_arg="1003",
        timeout_arg="17",
        skip_test=skip_test,
    )


def assert_no_secret_keys(value: Any) -> None:
    if isinstance(value, dict):
        forbidden = {"secret", "client_secret", "password", "token", "api_token"}
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
    token = load_script(skill_root, "octane_token", monkeypatch)

    result = login_with_defaults(token)

    assert result == 0
    assert (config_home / "octane.json").is_file()
    assert not (skill_root / ".env").exists()


def test_login_serializes_secret_free_default_profile_json(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    isolated_runtime: tuple[Path, FakeKeyring],
) -> None:
    config_home, _ = isolated_runtime
    token = load_script(relocated_skill(tmp_path, "install-a"), "octane_token", monkeypatch)

    assert login_with_defaults(token) == 0
    serialized = (config_home / "octane.json").read_text(encoding="utf-8")
    document = json.loads(serialized)

    assert document == profile_document()
    assert SENTINEL_SECRET not in serialized
    assert_no_secret_keys(document)


def test_client_resolves_complete_active_profile_without_dotenv(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    isolated_runtime: tuple[Path, FakeKeyring],
) -> None:
    config_home, fake_keyring = isolated_runtime
    write_profile(config_home)
    fake_keyring.passwords[(SERVICE_NAME, "client-id")] = SENTINEL_SECRET
    skill_root = relocated_skill(tmp_path, "clean-install")
    assert not (skill_root / ".env").exists()

    client = load_script(skill_root, "octane_client", monkeypatch)
    client.configure_runtime(client.resolve_runtime_config())
    session = client.get_session()
    entity_url = client.entity_url("work_items")

    assert session.posts == [
        {
            "url": "https://octane.example.test/authentication/sign_in",
            "json": {"client_id": "client-id", "client_secret": SENTINEL_SECRET},
            "timeout": 17,
            "allow_redirects": False,
        }
    ]
    assert entity_url == "https://octane.example.test/api/shared_spaces/131002/workspaces/1003/work_items"
    assert fake_keyring.get_calls == [(SERVICE_NAME, "client-id")]


def test_runtime_reconfiguration_does_not_reuse_an_authenticated_session(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    isolated_runtime: tuple[Path, FakeKeyring],
) -> None:
    config_home, fake_keyring = isolated_runtime
    write_profile(config_home)
    fake_keyring.passwords[(SERVICE_NAME, "client-id")] = SENTINEL_SECRET
    client = load_script(relocated_skill(tmp_path, "runtime-reset"), "octane_client", monkeypatch)
    first_runtime = client.resolve_runtime_config()
    client.configure_runtime(first_runtime)
    first_session = client.get_session()

    client.configure_runtime(first_runtime._replace(base_url="https://replacement.example.test"))
    second_session = client.get_session()

    assert second_session is not first_session
    assert first_session.posts[0]["url"] == "https://octane.example.test/authentication/sign_in"
    assert second_session.posts[0]["url"] == "https://replacement.example.test/authentication/sign_in"


def test_stable_profile_survives_plugin_relocation_and_replacement(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    isolated_runtime: tuple[Path, FakeKeyring],
) -> None:
    config_home, fake_keyring = isolated_runtime
    write_profile(config_home)
    fake_keyring.passwords[(SERVICE_NAME, "client-id")] = SENTINEL_SECRET

    first_root = relocated_skill(tmp_path, "old-install")
    first_client = load_script(first_root, "octane_client", monkeypatch)
    first_client.configure_runtime(first_client.resolve_runtime_config())
    first_client.get_session()
    shutil.rmtree(first_root)

    second_root = relocated_skill(tmp_path, "replacement-install")
    second_client = load_script(second_root, "octane_client", monkeypatch)
    second_client.configure_runtime(second_client.resolve_runtime_config())
    second_client.get_session()

    assert [instance.posts[0]["url"] for instance in FakeSession.instances] == [
        "https://octane.example.test/authentication/sign_in",
        "https://octane.example.test/authentication/sign_in",
    ]
    assert (config_home / "octane.json").is_file()
    assert not (second_root / ".env").exists()


def test_remote_verification_targets_written_profile_without_legacy_or_process_overrides(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    isolated_runtime: tuple[Path, FakeKeyring],
) -> None:
    _, _ = isolated_runtime
    skill_root = relocated_skill(tmp_path, "verification-profile")
    (skill_root / ".env").write_text(
        "OCTANE_BASE_URL=https://legacy.example\nOCTANE_CLIENT_ID=legacy\nOCTANE_CLIENT_SECRET=legacy-secret\n",
        encoding="utf-8",
    )
    monkeypatch.setenv("OCTANE_BASE_URL", "https://process.example")
    monkeypatch.setenv("OCTANE_CLIENT_ID", "process")
    monkeypatch.setenv("OCTANE_CLIENT_SECRET", "process-secret")
    token = load_script(skill_root, "octane_token", monkeypatch)
    captured: dict[str, Any] = {}

    def fake_run(command: list[str], **kwargs: Any) -> Any:
        captured["command"] = command
        captured["env"] = kwargs["env"]
        captured["timeout"] = kwargs["timeout"]
        return type("Result", (), {"returncode": 0, "stdout": '{"ok": true}', "stderr": ""})()

    monkeypatch.setattr(token.subprocess, "run", fake_run)

    assert token.test_octane_credentials("staging") == 0
    assert captured["command"][-5:] == ["--profile", "staging", "list-work-items", "--limit", "1"]
    assert not any(name.startswith("OCTANE_") for name in captured["env"])
    assert captured["timeout"] == token.VERIFICATION_TIMEOUT_SECONDS


def test_successful_verification_rejects_a_concurrently_replaced_keyring_secret(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    isolated_runtime: tuple[Path, FakeKeyring],
    capsys: pytest.CaptureFixture[str],
) -> None:
    _, fake_keyring = isolated_runtime
    token = load_script(relocated_skill(tmp_path, "superseded-secret"), "octane_token", monkeypatch)

    def replace_secret(_profile: str = "default") -> int:
        fake_keyring.set_password(SERVICE_NAME, "client-id", "newer-secret")
        return 0

    monkeypatch.setattr(token, "test_octane_credentials", replace_secret)

    assert login_with_defaults(token, skip_test=False) != 0
    assert fake_keyring.passwords[(SERVICE_NAME, "client-id")] == "newer-secret"
    assert "superseded" in capsys.readouterr().err.lower()


@pytest.mark.parametrize("failure_stage", ["keyring_write", "json_write", "remote_verification"])
def test_failed_login_restores_prior_profile_active_selection_and_secret(
    failure_stage: str,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    isolated_runtime: tuple[Path, FakeKeyring],
) -> None:
    config_home, fake_keyring = isolated_runtime
    prior_document = profile_document(endpoint="https://prior.example.test")
    config_path = write_profile(config_home, prior_document)
    prior_bytes = config_path.read_bytes()
    fake_keyring.passwords[(SERVICE_NAME, "client-id")] = "prior-secret"

    skill_root = relocated_skill(tmp_path, f"failed-{failure_stage}")
    token = load_script(skill_root, "octane_token", monkeypatch)
    if failure_stage == "keyring_write":
        fake_keyring.fail_set = True
    elif failure_stage == "json_write":
        real_replace = os.replace

        def fail_profile_replace(source: Any, destination: Any) -> None:
            if Path(destination) == config_path:
                raise OSError("injected atomic profile replacement failure")
            real_replace(source, destination)

        monkeypatch.setattr(os, "replace", fail_profile_replace)
    else:
        monkeypatch.setattr(token, "test_octane_credentials", lambda _profile="default": 1)

    result = login_with_defaults(token, skip_test=failure_stage != "remote_verification")

    assert result != 0
    assert config_path.read_bytes() == prior_bytes
    assert json.loads(config_path.read_text(encoding="utf-8"))["active_profile"] == "default"
    assert fake_keyring.passwords[(SERVICE_NAME, "client-id")] == "prior-secret"
    assert not (skill_root / ".env").exists()


def test_verification_runs_without_profile_lock_and_failed_rollback_preserves_concurrent_metadata(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    isolated_runtime: tuple[Path, FakeKeyring],
) -> None:
    config_home, fake_keyring = isolated_runtime
    prior_document = profile_document(endpoint="https://prior.example.test")
    prior_document["profiles"]["zulu"] = {
        "keyring_user": "zulu-client",
        "endpoint": "https://zulu.example.test",
        "settings": {"shared_space_id": "1", "workspace_id": "2", "timeout": "30"},
    }
    config_path = write_profile(config_home, prior_document)
    fake_keyring.passwords[(SERVICE_NAME, "client-id")] = "prior-secret"
    token = load_script(relocated_skill(tmp_path, "unlocked-verification"), "octane_token", monkeypatch)

    def concurrent_selection(_profile: str = "default") -> int:
        token.select_profile("zulu")
        return 1

    monkeypatch.setattr(token, "test_octane_credentials", concurrent_selection)

    result = login_with_defaults(token, skip_test=False)

    stored = json.loads(config_path.read_text(encoding="utf-8"))
    assert result == 1
    assert stored["active_profile"] == "zulu"
    assert stored["profiles"]["default"]["endpoint"] == "https://octane.example.test"
    assert fake_keyring.passwords[(SERVICE_NAME, "client-id")] == "prior-secret"
