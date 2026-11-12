"""RED contract tests for GitLab's durable default-profile credential path.

All plugin roots, process configuration, keyring state, and HTTP requests are
isolated.  These tests never import the repository scripts directly, allowing
plugin relocation/replacement to be exercised without a plugin-local .env.
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
from urllib.parse import urlparse

import pytest


SKILL_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS_ROOT = SKILL_ROOT / "scripts"
SERVICE_NAME = "AgentDevelopmentToolkit:gitlab"
SENTINEL_TOKEN = "glpat-test-MUST-NOT-BE-SERIALIZED"
SELF_HOSTED_API = "https://gitlab.internal.example/api/v4"
KEYRING_USER = "self-hosted-gitlab-user"


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
    text = "[]"
    content = b"[]"
    headers = {"content-type": "application/json"}

    def json(self) -> list[Any]:
        return []


class FakeRequests:
    def __init__(self) -> None:
        self.calls: list[dict[str, Any]] = []

    def request(self, method: str, url: str, **kwargs: Any) -> FakeResponse:
        self.calls.append({"method": method, "url": url, **kwargs})
        return FakeResponse()

    def get(self, url: str, **kwargs: Any) -> FakeResponse:
        self.calls.append({"method": "GET", "url": url, **kwargs})
        return FakeResponse()


@pytest.fixture
def isolated_runtime(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> tuple[Path, FakeKeyring, FakeRequests]:
    """Override the suite's autouse direct-token fixture and all I/O boundaries."""
    config_home = tmp_path / "durable-config"
    home = tmp_path / "home"
    home.mkdir()

    for name in list(sys.modules):
        if name == "credential_config" or name.startswith("gitlab_config_test_"):
            monkeypatch.delitem(sys.modules, name, raising=False)

    # conftest.py injects GITLAB_* values for legacy tests.  These contract tests
    # deliberately start from an empty service environment.
    for name in list(os.environ):
        if name.startswith("GITLAB_") or name in {
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

    fake_requests = FakeRequests()
    requests_module = types.ModuleType("requests")
    requests_module.request = fake_requests.request  # type: ignore[attr-defined]
    requests_module.get = fake_requests.get  # type: ignore[attr-defined]
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
    return config_home, fake_keyring, fake_requests


def relocated_skill(tmp_path: Path, name: str) -> Path:
    """Create an installed-skill image containing scripts but no .env."""
    root = tmp_path / name / "gitlab"
    scripts = root / "scripts"
    scripts.mkdir(parents=True)
    (root / "SKILL.md").write_text("---\nname: gitlab\n---\n", encoding="utf-8")
    for source in SCRIPTS_ROOT.glob("*.py"):
        shutil.copy2(source, scripts / source.name)
    return root


def load_script(
    skill_root: Path,
    script_name: str,
    monkeypatch: pytest.MonkeyPatch,
) -> types.ModuleType:
    """Load a relocated script while allowing only its adjacent local imports."""
    module_name = f"gitlab_config_test_{script_name}_{uuid.uuid4().hex}"
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
    endpoint: str = SELF_HOSTED_API,
    keyring_user: str = KEYRING_USER,
) -> dict[str, Any]:
    return {
        "schema_version": 1,
        "active_profile": "default",
        "profiles": {
            "default": {
                "keyring_user": keyring_user,
                "endpoint": endpoint,
                "settings": {
                    "project_id": "42",
                    "allowed_project_ids": "42,84",
                    "read_only_mode": "true",
                    "timeout": "17",
                },
            }
        },
    }


def write_profile(config_home: Path, document: dict[str, Any] | None = None) -> Path:
    config_home.mkdir(parents=True, exist_ok=True)
    path = config_home / "gitlab.json"
    path.write_text(json.dumps(document or profile_document()), encoding="utf-8")
    return path


def login_with_defaults(token_module: types.ModuleType, *, skip_test: bool = True) -> int:
    return token_module.login(
        username=KEYRING_USER,
        token_arg=SENTINEL_TOKEN,
        api_url_arg=f"{SELF_HOSTED_API}/",
        project_id_arg="42",
        allowed_project_ids_arg="42,84",
        read_only_mode_arg="true",
        timeout_arg="17",
        skip_test=skip_test,
    )


def assert_no_secret_keys(value: Any) -> None:
    if isinstance(value, dict):
        forbidden = {"secret", "client_secret", "password", "token", "api_token", "personal_access_token"}
        assert forbidden.isdisjoint(key.lower() for key in value)
        for child in value.values():
            assert_no_secret_keys(child)
    elif isinstance(value, list):
        for child in value:
            assert_no_secret_keys(child)


def invoke_list_projects(client: types.ModuleType) -> None:
    # Successful CLI requests terminate through the JSON-output helper.
    runtime = client.resolve_runtime_config()
    tool = "get_project" if runtime.default_project_id else "list_projects"
    params = {} if runtime.default_project_id else {"per_page": "1"}
    with pytest.raises(SystemExit) as exit_info:
        client.request(tool, params, runtime=runtime)
    assert exit_info.value.code == 0


def test_login_honors_stable_config_home_override(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    isolated_runtime: tuple[Path, FakeKeyring, FakeRequests],
) -> None:
    config_home, _, _ = isolated_runtime
    skill_root = relocated_skill(tmp_path, "install-a")
    token_module = load_script(skill_root, "gitlab_token", monkeypatch)

    result = login_with_defaults(token_module)

    assert result == 0
    assert (config_home / "gitlab.json").is_file()
    assert not (skill_root / ".env").exists()


def test_login_writes_secret_free_default_profile_with_all_safety_settings(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    isolated_runtime: tuple[Path, FakeKeyring, FakeRequests],
) -> None:
    config_home, fake_keyring, _ = isolated_runtime
    token_module = load_script(relocated_skill(tmp_path, "install-a"), "gitlab_token", monkeypatch)

    assert login_with_defaults(token_module) == 0
    serialized = (config_home / "gitlab.json").read_text(encoding="utf-8")
    document = json.loads(serialized)

    assert document == profile_document()
    assert SENTINEL_TOKEN not in serialized
    assert_no_secret_keys(document)
    assert fake_keyring.passwords[(SERVICE_NAME, KEYRING_USER)] == SENTINEL_TOKEN


def test_cli_uses_self_hosted_stable_profile_after_plugin_replacement_without_dotenv(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    isolated_runtime: tuple[Path, FakeKeyring, FakeRequests],
) -> None:
    config_home, fake_keyring, fake_requests = isolated_runtime
    write_profile(config_home)
    fake_keyring.passwords[(SERVICE_NAME, KEYRING_USER)] = SENTINEL_TOKEN

    old_root = relocated_skill(tmp_path, "old-install")
    old_client = load_script(old_root, "gitlab_cli", monkeypatch)
    invoke_list_projects(old_client)
    shutil.rmtree(old_root)

    replacement_root = relocated_skill(tmp_path, "replacement-install")
    assert not (replacement_root / ".env").exists()
    replacement_client = load_script(replacement_root, "gitlab_cli", monkeypatch)
    invoke_list_projects(replacement_client)

    runtime = replacement_client.resolve_runtime_config()
    assert runtime.default_project_id == "42"
    assert runtime.allowed_project_ids == {"42", "84"}
    assert runtime.read_only is True
    assert runtime.timeout == 17
    assert fake_keyring.get_calls == [
        (SERVICE_NAME, KEYRING_USER),
        (SERVICE_NAME, KEYRING_USER),
    ]
    assert len(fake_requests.calls) == 2
    for call in fake_requests.calls:
        assert call["url"] == f"{SELF_HOSTED_API}/projects/42"
        assert urlparse(call["url"]).hostname == "gitlab.internal.example"
        assert urlparse(call["url"]).hostname != "gitlab.com"
        assert call["headers"]["PRIVATE-TOKEN"] == SENTINEL_TOKEN
        assert call["timeout"] == 17


def test_direct_token_environment_remains_available_for_ci_without_a_profile(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    isolated_runtime: tuple[Path, FakeKeyring, FakeRequests],
) -> None:
    config_home, fake_keyring, fake_requests = isolated_runtime
    ci_api = "https://ci-gitlab.example/api/v4"
    monkeypatch.setenv("GITLAB_PERSONAL_ACCESS_TOKEN", "glpat-ci-direct-token")
    monkeypatch.setenv("GITLAB_API_URL", ci_api)
    monkeypatch.setenv("GITLAB_TIMEOUT", "9")
    client = load_script(relocated_skill(tmp_path, "ci-install"), "gitlab_cli", monkeypatch)

    invoke_list_projects(client)

    assert not (config_home / "gitlab.json").exists()
    assert fake_keyring.get_calls == []
    assert fake_requests.calls == [{
        "method": "GET",
        "url": f"{ci_api}/projects",
        "headers": {"PRIVATE-TOKEN": "glpat-ci-direct-token", "Accept": "application/json"},
        "params": {"per_page": "1"},
        "json": None,
        "files": None,
        "timeout": 9,
        "allow_redirects": False,
    }]


def test_remote_verification_targets_written_profile_without_legacy_or_process_overrides(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    isolated_runtime: tuple[Path, FakeKeyring, FakeRequests],
) -> None:
    _, _, _ = isolated_runtime
    skill_root = relocated_skill(tmp_path, "verification-profile")
    (skill_root / ".env").write_text(
        "GITLAB_API_URL=https://legacy.example/api/v4\n"
        "GITLAB_PERSONAL_ACCESS_TOKEN=legacy-token\n",
        encoding="utf-8",
    )
    monkeypatch.setenv("GITLAB_API_URL", "https://process.example/api/v4")
    monkeypatch.setenv("GITLAB_PERSONAL_ACCESS_TOKEN", "process-token")
    token_module = load_script(skill_root, "gitlab_token", monkeypatch)
    captured: dict[str, Any] = {}

    def fake_run(command: list[str], **kwargs: Any) -> Any:
        captured["command"] = command
        captured["env"] = kwargs["env"]
        captured["timeout"] = kwargs["timeout"]
        return type("Result", (), {"returncode": 0, "stdout": '{"ok": true}', "stderr": ""})()

    monkeypatch.setattr(token_module.subprocess, "run", fake_run)

    assert token_module.test_gitlab_credentials("staging") == 0
    assert captured["command"][-5:] == ["--profile", "staging", "list_projects", "--param", "per_page=1"]
    assert not any(name.startswith("GITLAB_") for name in captured["env"])
    assert captured["timeout"] == token_module.VERIFICATION_TIMEOUT_SECONDS


def test_successful_verification_rejects_a_concurrently_replaced_keyring_token(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    isolated_runtime: tuple[Path, FakeKeyring, FakeRequests],
    capsys: pytest.CaptureFixture[str],
) -> None:
    _, fake_keyring, _ = isolated_runtime
    token_module = load_script(relocated_skill(tmp_path, "superseded-secret"), "gitlab_token", monkeypatch)

    def replace_secret(_profile: str = "default") -> int:
        fake_keyring.set_password(SERVICE_NAME, KEYRING_USER, "newer-token")
        return 0

    monkeypatch.setattr(token_module, "test_gitlab_credentials", replace_secret)

    assert login_with_defaults(token_module, skip_test=False) != 0
    assert fake_keyring.passwords[(SERVICE_NAME, KEYRING_USER)] == "newer-token"
    assert "superseded" in capsys.readouterr().err.lower()


@pytest.mark.parametrize("failure_stage", ["keyring_write", "metadata_write", "remote_verification"])
def test_failed_login_restores_exact_prior_profile_active_selection_and_token(
    failure_stage: str,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    isolated_runtime: tuple[Path, FakeKeyring, FakeRequests],
) -> None:
    config_home, fake_keyring, fake_requests = isolated_runtime
    prior_document = profile_document(endpoint="https://prior-gitlab.example/api/v4")
    config_path = write_profile(config_home, prior_document)
    prior_bytes = config_path.read_bytes()
    fake_keyring.passwords[(SERVICE_NAME, KEYRING_USER)] = "glpat-exact-prior-token"

    skill_root = relocated_skill(tmp_path, f"failed-{failure_stage}")
    token_module = load_script(skill_root, "gitlab_token", monkeypatch)
    if failure_stage == "keyring_write":
        fake_keyring.fail_set = True
    elif failure_stage == "metadata_write":
        real_replace = os.replace
        failed_once = False

        def fail_profile_replace(source: Any, destination: Any) -> None:
            nonlocal failed_once
            if Path(destination) == config_path and not failed_once:
                failed_once = True
                raise OSError("injected atomic profile replacement failure")
            real_replace(source, destination)

        monkeypatch.setattr(os, "replace", fail_profile_replace)
    else:
        monkeypatch.setattr(token_module, "test_gitlab_credentials", lambda _profile="default": 1)

    result = login_with_defaults(
        token_module,
        skip_test=failure_stage != "remote_verification",
    )

    assert result != 0
    assert config_path.read_bytes() == prior_bytes
    assert json.loads(config_path.read_text(encoding="utf-8")) == prior_document
    assert fake_keyring.passwords[(SERVICE_NAME, KEYRING_USER)] == "glpat-exact-prior-token"
    assert fake_requests.calls == []
    assert not (skill_root / ".env").exists()


def test_verification_releases_lock_and_failed_rollback_preserves_concurrent_selection(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    isolated_runtime: tuple[Path, FakeKeyring, FakeRequests],
) -> None:
    config_home, fake_keyring, _ = isolated_runtime
    prior_document = profile_document(endpoint="https://prior-gitlab.example/api/v4")
    prior_document["profiles"]["zulu"] = {
        "keyring_user": "zulu-user",
        "endpoint": "https://zulu.example/api/v4",
        "settings": {"project_id": "2", "allowed_project_ids": "2", "read_only_mode": "true", "timeout": "30"},
    }
    config_path = write_profile(config_home, prior_document)
    fake_keyring.passwords[(SERVICE_NAME, KEYRING_USER)] = "glpat-exact-prior-token"
    token = load_script(relocated_skill(tmp_path, "unlocked-verification"), "gitlab_token", monkeypatch)

    def concurrent_selection(_profile: str = "default") -> int:
        token.select_profile("zulu")
        return 1

    monkeypatch.setattr(token, "test_gitlab_credentials", concurrent_selection)

    result = login_with_defaults(token, skip_test=False)

    stored = json.loads(config_path.read_text(encoding="utf-8"))
    assert result == 1
    assert stored["active_profile"] == "zulu"
    assert stored["profiles"]["default"]["endpoint"] == SELF_HOSTED_API
    assert fake_keyring.passwords[(SERVICE_NAME, KEYRING_USER)] == "glpat-exact-prior-token"
