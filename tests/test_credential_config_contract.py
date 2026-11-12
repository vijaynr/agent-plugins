"""Observable credential-configuration contract shared by standalone plugins.

The subprocess checks inject file-backed keyring and HTTP fakes through
``PYTHONPATH``.  They therefore exercise real CLI process boundaries without
using an OS credential store or network.
"""
from __future__ import annotations

import importlib.util
import json
import os
import shutil
import subprocess
import sys
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
from types import ModuleType
from typing import Any

import pytest


@dataclass(frozen=True)
class PluginContract:
    name: str
    skill: str
    service: str
    token_script: str
    api_script: str
    secret_flag: str
    endpoint_flag: str
    endpoint_env: str
    secret_env: str
    keyring_env: str
    mismatch_code: str
    missing_code: str
    backend_code: str
    endpoint: str
    settings: dict[str, str]
    login_extra: tuple[str, ...]
    api_args: tuple[str, ...]
    write_args: tuple[str, ...]
    legacy_lines: tuple[str, ...]

    @property
    def keyring_user(self) -> str:
        return f"{self.name}-contract-user"


CONTRACTS = (
    PluginContract(
        "octane", "alm-octane", "AgentDevelopmentToolkit:alm-octane",
        "octane_token.py", "octane_client.py", "--secret", "--base-url",
        "OCTANE_BASE_URL", "OCTANE_CLIENT_SECRET", "OCTANE_CLIENT_SECRET_KEYRING_USER",
        "OCTANE_CREDENTIAL_SOURCE_MISMATCH", "OCTANE_KEYRING_ENTRY_MISSING",
        "OCTANE_KEYRING_BACKEND_FAILURE", "https://octane.contract.test",
        {"shared_space_id": "11", "workspace_id": "22", "timeout": "7"},
        ("--shared-space-id", "11", "--workspace-id", "22", "--timeout", "7"),
        ("list-work-items", "--limit", "1"),
        ("create-story", "--name", "Contract story", "--description", "Contract write"),
        ("OCTANE_BASE_URL=https://octane.contract.test/",  "OCTANE_CLIENT_SECRET_KEYRING_USER=octane-contract-user", "OCTANE_SHARED_SPACE_ID=11", "OCTANE_WORKSPACE_ID=22", "OCTANE_TIMEOUT=7"),
    ),
    PluginContract(
        "gitlab", "gitlab", "AgentDevelopmentToolkit:gitlab",
        "gitlab_token.py", "gitlab_cli.py", "--token", "--api-url",
        "GITLAB_API_URL", "GITLAB_PERSONAL_ACCESS_TOKEN", "GITLAB_TOKEN_KEYRING_USER",
        "GITLAB_CREDENTIAL_SOURCE_MISMATCH", "GITLAB_KEYRING_ENTRY_MISSING",
        "GITLAB_KEYRING_BACKEND_FAILURE", "https://gitlab.contract.test/api/v4",
        {"project_id": "", "allowed_project_ids": "", "read_only_mode": "false", "timeout": "7"},
        ("--project-id", "", "--allowed-project-ids", "", "--read-only-mode", "false", "--timeout", "7"),
        ("list_projects",),
        ("create_issue", "--param", "project_id=42", "--param", "title=Contract issue"),
        ("GITLAB_API_URL=https://gitlab.contract.test/api/v4/",  "GITLAB_TOKEN_KEYRING_USER=gitlab-contract-user", "GITLAB_PROJECT_ID=", "GITLAB_ALLOWED_PROJECT_IDS=", "GITLAB_READ_ONLY_MODE=false", "GITLAB_TIMEOUT=7"),
    ),
    PluginContract(
        "blackduck", "blackduck", "AgentDevelopmentToolkit:blackduck",
        "blackduck_token.py", "blackduck_vulnerabilities.py", "--token", "--url",
        "BLACKDUCK_URL", "BLACKDUCK_TOKEN", "BLACKDUCK_TOKEN_KEYRING_USER",
        "BLACKDUCK_CREDENTIAL_SOURCE_MISMATCH", "BLACKDUCK_KEYRING_ENTRY_MISSING",
        "BLACKDUCK_KEYRING_BACKEND_FAILURE", "https://blackduck.contract.test",
        {"verify_ssl": "false"}, ("--verify-ssl", "false"),
        ("list-projects", "--limit", "1"),
        ("comment-vulnerability", "--project", "contract-project", "--version", "contract-version", "--vuln-id", "CVE-CONTRACT", "--comment", "Contract write"),
        ("BLACKDUCK_URL=https://blackduck.contract.test/",  "BLACKDUCK_TOKEN_KEYRING_USER=blackduck-contract-user", "BLACKDUCK_VERIFY_SSL=false"),
    ),
)


def _scripts(repo_root: Path, contract: PluginContract) -> Path:
    return repo_root / "plugins" / contract.name / "skills" / contract.skill / "scripts"


def _load_config(repo_root: Path, contract: PluginContract) -> ModuleType:
    path = _scripts(repo_root, contract) / "credential_config.py"
    name = f"contract_{contract.name}_credential_config_{id(path)}"
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.mark.parametrize("contract", CONTRACTS, ids=lambda contract: contract.name)
@pytest.mark.parametrize("endpoint", [
    "http://service.example.test",
    "https://user:secret@service.example.test",
    "https://service.example.test?redirect=attacker",
    "https://service.example.test/#fragment",
])
def test_credential_endpoints_require_plain_https_origins(
    repo_root: Path,
    contract: PluginContract,
    endpoint: str,
) -> None:
    config = _load_config(repo_root, contract)

    with pytest.raises(config.ConfigError):
        config.default_profile(endpoint, contract.keyring_user, contract.settings)


def _profile(contract: PluginContract, name: str = "default") -> dict[str, Any]:
    return {
        "endpoint": contract.endpoint if name == "default" else f"https://{name}.{contract.name}.test",
        "keyring_user": contract.keyring_user if name == "default" else f"{name}-user",
        "settings": dict(contract.settings),
    }


@pytest.mark.parametrize("contract", CONTRACTS, ids=lambda item: item.name)
def test_lock_cleanup_retries_transient_permission_errors(
    repo_root: Path,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    contract: PluginContract,
) -> None:
    config = _load_config(repo_root, contract)
    lock_path = tmp_path / "profile.lock"
    lock_path.write_text("owned", encoding="utf-8")
    identity = config._lock_identity(lock_path)
    real_unlink = config.Path.unlink
    attempts = 0

    def transient_unlink(path: Path, *args: Any, **kwargs: Any) -> None:
        nonlocal attempts
        attempts += 1
        if attempts == 1:
            raise PermissionError("temporarily open")
        real_unlink(path, *args, **kwargs)

    monkeypatch.setattr(config.Path, "unlink", transient_unlink)
    monkeypatch.setattr(config.time, "sleep", lambda _seconds: None)

    assert config._unlink_if_unchanged(lock_path, identity) is True
    assert attempts == 2
    assert not lock_path.exists()


@pytest.mark.parametrize("contract", CONTRACTS, ids=lambda item: item.name)
def test_lock_cleanup_preserves_changed_or_persistently_open_lock(
    repo_root: Path,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    contract: PluginContract,
) -> None:
    config = _load_config(repo_root, contract)
    lock_path = tmp_path / "profile.lock"
    lock_path.write_text("original", encoding="utf-8")
    original_identity = config._lock_identity(lock_path)
    lock_path.write_text("replacement-owner", encoding="utf-8")
    assert config._unlink_if_unchanged(lock_path, original_identity) is False

    current_identity = config._lock_identity(lock_path)
    monkeypatch.setattr(
        config.Path,
        "unlink",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(PermissionError("open")),
    )
    monkeypatch.setattr(config.time, "sleep", lambda _seconds: None)
    assert config._unlink_if_unchanged(lock_path, current_identity) is False
    assert lock_path.exists()


@pytest.mark.parametrize("contract", CONTRACTS, ids=lambda item: item.name)
def test_parent_directory_is_synced_after_atomic_replace_on_posix(
    repo_root: Path,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    contract: PluginContract,
) -> None:
    config = _load_config(repo_root, contract)
    calls: list[tuple[str, Any]] = []
    monkeypatch.setattr(config.os, "name", "posix")
    monkeypatch.setattr(config.os, "open", lambda path, flags: calls.append(("open", path)) or 7)
    monkeypatch.setattr(config.os, "fsync", lambda fd: calls.append(("fsync", fd)))
    monkeypatch.setattr(config.os, "close", lambda fd: calls.append(("close", fd)))

    config._sync_parent_directory(tmp_path / "config.json")

    assert calls == [("open", str(tmp_path)), ("fsync", 7), ("close", 7)]


@pytest.mark.parametrize("contract", CONTRACTS, ids=lambda item: item.name)
@pytest.mark.parametrize(
    ("platform", "environment", "home_suffix"),
    (
        ("win32", {"APPDATA": "{base}/roaming"}, "roaming/AgentDevelopmentToolkit"),
        ("darwin", {}, "home/Library/Application Support/AgentDevelopmentToolkit"),
        ("linux", {"XDG_CONFIG_HOME": "{base}/xdg"}, "xdg/agent-development-toolkit"),
        ("linux", {"AGENT_DEVELOPMENT_TOOLKIT_CONFIG_HOME": "{base}/override"}, "override"),
    ),
    ids=("windows", "macos", "linux-xdg", "explicit-override"),
)
def test_platform_config_paths_are_identical_except_for_service_filename(
    repo_root: Path,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    contract: PluginContract,
    platform: str,
    environment: dict[str, str],
    home_suffix: str,
) -> None:
    config = _load_config(repo_root, contract)
    home = tmp_path / "home"
    monkeypatch.setattr(config.sys, "platform", platform)
    monkeypatch.setattr(config.Path, "home", classmethod(lambda _cls: home))
    env = {key: value.format(base=tmp_path.as_posix()) for key, value in environment.items()}

    assert config.config_path(env) == tmp_path / home_suffix / f"{contract.name}.json"


@pytest.mark.parametrize("contract", CONTRACTS, ids=lambda item: item.name)
def test_profile_lifecycle_rollback_and_lock_cleanup_have_observable_parity(
    repo_root: Path,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    contract: PluginContract,
) -> None:
    config_home = tmp_path / "config"
    monkeypatch.setenv("AGENT_DEVELOPMENT_TOOLKIT_CONFIG_HOME", str(config_home))
    config = _load_config(repo_root, contract)
    default = _profile(contract)
    alpha = _profile(contract, "alpha")

    config.write_document(config.document_with_profile("default", default))
    original = config.snapshot()
    config.write_document(config.document_with_profile("alpha", alpha, activate=False))
    assert config.read_document()["active_profile"] == "default"
    config.select_profile("alpha")
    assert config.read_document()["active_profile"] == "alpha"
    config.restore(original)
    assert config.snapshot() == original

    lock_path = config.config_path().with_suffix(".json.lock")
    with config.profile_lock():
        assert lock_path.is_file()
    assert not lock_path.exists()

    config.write_document(config.document_with_profile("alpha", alpha))
    config.remove_profile("alpha")
    assert config.read_document()["active_profile"] == "default"
    config.remove_profile("default")
    assert config.read_document() == config.empty_document()


@pytest.mark.parametrize("contract", CONTRACTS, ids=lambda item: item.name)
def test_contended_lock_and_failed_replace_preserve_prior_bytes_and_artifacts(
    repo_root: Path,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    contract: PluginContract,
) -> None:
    config_home = tmp_path / "config"
    monkeypatch.setenv("AGENT_DEVELOPMENT_TOOLKIT_CONFIG_HOME", str(config_home))
    config = _load_config(repo_root, contract)
    config.write_document(config.document_with_profile("default", _profile(contract)))
    target = config.config_path()
    prior = target.read_bytes()
    lock = target.with_suffix(".json.lock")
    lock.touch()
    with pytest.raises(config.ConfigError, match="timed out"):
        with config.profile_lock(timeout=0.01):
            pass
    assert target.read_bytes() == prior and lock.exists()
    lock.unlink()

    def fail_replace(_source: object, _target: object) -> None:
        raise OSError("injected replacement failure")

    monkeypatch.setattr(config.os, "replace", fail_replace)
    with pytest.raises(config.ConfigError, match="failed to write"):
        config.write_document(config.empty_document())
    assert target.read_bytes() == prior
    assert list(config_home.glob(f".{contract.name}.json.*.tmp")) == []


@pytest.mark.parametrize("contract", CONTRACTS, ids=lambda item: item.name)
def test_profile_lock_recovers_crashed_owner_and_old_legacy_sentinel(
    repo_root: Path,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    contract: PluginContract,
) -> None:
    config_home = tmp_path / "config"
    monkeypatch.setenv("AGENT_DEVELOPMENT_TOOLKIT_CONFIG_HOME", str(config_home))
    config = _load_config(repo_root, contract)
    lock = config.config_path().with_suffix(".json.lock")
    lock.parent.mkdir(parents=True)

    with config.profile_lock():
        with pytest.raises(config.ConfigError, match="timed out"):
            with config.profile_lock(timeout=0.01):
                pass
        assert json.loads(lock.read_text(encoding="utf-8"))["pid"] == os.getpid()

    exited_pid = int(subprocess.check_output(
        [sys.executable, "-c", "import os; print(os.getpid())"], text=True
    ).strip())
    lock.write_text(json.dumps({"pid": exited_pid, "created": 1}), encoding="utf-8")
    with config.profile_lock(timeout=0.1):
        assert lock.is_file()
    assert not lock.exists()

    lock.touch()
    old = 1
    os.utime(lock, (old, old))
    with config.profile_lock(timeout=0.1):
        assert lock.is_file()
    assert not lock.exists()


@pytest.mark.parametrize("contract", CONTRACTS, ids=lambda item: item.name)
@pytest.mark.parametrize("root_name", ("executing", "copilot", "agents"))
def test_exact_legacy_roots_migrate_without_modifying_dotenv(
    repo_root: Path,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    contract: PluginContract,
    root_name: str,
) -> None:
    home = tmp_path / "home"
    config_home = tmp_path / "config"
    monkeypatch.setenv("HOME", str(home))
    monkeypatch.setenv("USERPROFILE", str(home))
    monkeypatch.setenv("AGENT_DEVELOPMENT_TOOLKIT_CONFIG_HOME", str(config_home))
    config = _load_config(repo_root, contract)
    executing = tmp_path / "relocated" / contract.skill
    roots = {
        "executing": executing,
        "copilot": home / ".copilot" / "skills" / contract.skill,
        "agents": home / ".agents" / "skills" / contract.skill,
    }
    source = roots[root_name] / ".env"
    source.parent.mkdir(parents=True, exist_ok=True)
    source_bytes = ("\r\n".join(contract.legacy_lines) + "\r\n").encode()
    source.write_bytes(source_bytes)

    assert config.migrate_legacy(executing, lambda service, user: "available" if (service, user) == (contract.service, contract.keyring_user) else None)
    document = config.read_document()
    assert document["profiles"]["default"] == _profile(contract)
    assert source.read_bytes() == source_bytes


@pytest.mark.parametrize("contract", CONTRACTS, ids=lambda item: item.name)
def test_migration_ignores_conflicting_metadata_without_a_keyring_entry(
    repo_root: Path,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    contract: PluginContract,
) -> None:
    home = tmp_path / "home"
    config_home = tmp_path / "config"
    monkeypatch.setattr(Path, "home", classmethod(lambda _cls: home))
    monkeypatch.setenv("AGENT_DEVELOPMENT_TOOLKIT_CONFIG_HOME", str(config_home))
    config = _load_config(repo_root, contract)
    executing = tmp_path / "relocated" / contract.skill
    valid_source = executing / ".env"
    valid_source.parent.mkdir(parents=True)
    valid_source.write_text("\n".join(contract.legacy_lines) + "\n", encoding="utf-8")
    stale_source = home / ".copilot" / "skills" / contract.skill / ".env"
    stale_source.parent.mkdir(parents=True)
    stale_lines = [
        line.replace(contract.endpoint, f"https://stale.{contract.name}.test").replace(contract.keyring_user, "stale-user")
        for line in contract.legacy_lines
    ]
    stale_source.write_text("\n".join(stale_lines) + "\n", encoding="utf-8")

    assert config.migrate_legacy(
        executing,
        lambda service, user: "available" if (service, user) == (contract.service, contract.keyring_user) else None,
    )
    assert config.read_document()["profiles"]["default"] == _profile(contract)


@pytest.mark.parametrize("contract", CONTRACTS, ids=lambda item: item.name)
def test_concurrent_migration_never_overwrites_a_different_winner(
    repo_root: Path,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    contract: PluginContract,
) -> None:
    config_home = tmp_path / "config"
    monkeypatch.setenv("AGENT_DEVELOPMENT_TOOLKIT_CONFIG_HOME", str(config_home))
    monkeypatch.setattr(Path, "home", classmethod(lambda _cls: tmp_path / "home"))
    config = _load_config(repo_root, contract)
    executing = tmp_path / "relocated" / contract.skill
    source = executing / ".env"
    source.parent.mkdir(parents=True)
    source.write_text("\n".join(contract.legacy_lines) + "\n", encoding="utf-8")
    winner = _profile(contract, "winner")

    @contextmanager
    def competing_lock():
        config.write_document({"schema_version": 1, "active_profile": "default", "profiles": {"default": winner}})
        yield

    monkeypatch.setattr(config, "profile_lock", competing_lock)

    with pytest.raises(config.ConfigError, match="concurrent.*conflict"):
        config.migrate_legacy(executing, lambda _service, _user: "available")
    assert config.read_document()["profiles"]["default"] == winner


@pytest.mark.parametrize("contract", CONTRACTS, ids=lambda item: item.name)
def test_canonical_legacy_root_alias_is_deduplicated(
    repo_root: Path,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    contract: PluginContract,
) -> None:
    home = tmp_path / "home"
    config_home = tmp_path / "config"
    monkeypatch.setenv("HOME", str(home))
    monkeypatch.setenv("USERPROFILE", str(home))
    monkeypatch.setenv("AGENT_DEVELOPMENT_TOOLKIT_CONFIG_HOME", str(config_home))
    config = _load_config(repo_root, contract)
    executing = tmp_path / "relocated" / contract.skill
    executing.mkdir(parents=True)
    source = executing / ".env"
    source.write_text("\n".join(contract.legacy_lines) + "\n", encoding="utf-8")
    alias = home / ".copilot" / "skills" / contract.skill
    alias.parent.mkdir(parents=True)
    try:
        alias.symlink_to(executing, target_is_directory=True)
    except OSError as symlink_error:
        if os.name != "nt":
            pytest.skip(f"directory aliases are unavailable: {symlink_error}")
        junction = subprocess.run(
            ["cmd", "/c", "mklink", "/J", str(alias), str(executing)],
            capture_output=True,
            text=True,
        )
        if junction.returncode != 0:
            pytest.skip(f"directory aliases are unavailable: {junction.stderr.strip()}")
    calls: list[tuple[str, str]] = []

    assert config.migrate_legacy(executing, lambda service, user: calls.append((service, user)) or "available")
    assert calls == [(contract.service, contract.keyring_user)]


@pytest.fixture
def fake_backends(tmp_path: Path) -> Path:
    root = tmp_path / "fake-backends"
    keyring = root / "keyring"
    keyring.mkdir(parents=True)
    (keyring / "errors.py").write_text(
        "class KeyringError(Exception): pass\nclass PasswordDeleteError(KeyringError): pass\n",
        encoding="utf-8",
    )
    (keyring / "__init__.py").write_text(
        """import json, os
from pathlib import Path
from .errors import KeyringError, PasswordDeleteError

def _path(): return Path(os.environ['FAKE_KEYRING_FILE'])
def _read(): return json.loads(_path().read_text()) if _path().is_file() else {}
def _key(service, user): return service + '\\0' + user
def get_password(service, user):
    if os.environ.get('FAKE_KEYRING_MODE') == 'backend': raise KeyringError('injected backend failure')
    return _read().get(_key(service, user))
def set_password(service, user, password):
    if os.environ.get('FAKE_KEYRING_MODE') == 'backend': raise KeyringError('injected backend failure')
    data = _read(); data[_key(service, user)] = password
    _path().write_text(json.dumps(data), encoding='utf-8')
def delete_password(service, user):
    data = _read(); key = _key(service, user)
    if key not in data: raise PasswordDeleteError('missing')
    del data[key]; _path().write_text(json.dumps(data), encoding='utf-8')
""",
        encoding="utf-8",
    )
    dotenv = root / "dotenv"
    dotenv.mkdir()
    (dotenv / "__init__.py").write_text("def load_dotenv(*args, **kwargs): return False\n", encoding="utf-8")
    requests = root / "requests"
    requests.mkdir()
    (requests / "__init__.py").write_text(
        """import json, os
from pathlib import Path
class RequestException(Exception): pass

def _log(url, method):
    path = Path(os.environ['FAKE_HTTP_LOG'])
    with path.open('a', encoding='utf-8') as stream: stream.write(json.dumps({'url': url, 'method': method}) + '\\n')
class Response:
    def __init__(self, data=None, status=200):
        self._data = {} if data is None else data; self.status_code = status; self.ok = 200 <= status < 300
        self.headers = {'content-type': 'application/json', 'X-CSRF-TOKEN': 'fake-csrf'}; self.text = json.dumps(self._data); self.content = self.text.encode()
    def json(self): return self._data
class Session:
    def __init__(self): self.headers = {}; self.verify = True
    def post(self, url, **kwargs):
        _log(url, 'POST')
        data = {'bearerToken': 'fake-bearer', 'expiresInMilliseconds': 7200000} if url.endswith('/api/tokens/authenticate') else {}
        return Response(data)
    def request(self, method, url, **kwargs): _log(url, method); return Response({'data': []})
    def get(self, url, **kwargs):
        _log(url, 'GET')
        if url.endswith('/api/projects'):
            return Response({'items': [{'name': 'contract-project', '_meta': {'href': 'https://blackduck.contract.test/api/projects/project-id', 'links': [{'rel': 'versions', 'href': 'https://blackduck.contract.test/api/projects/project-id/versions'}]}}], 'totalCount': 1})
        if url.endswith('/versions'):
            return Response({'items': [{'versionName': 'contract-version', '_meta': {'href': 'https://blackduck.contract.test/api/projects/project-id/versions/version-id'}}], 'totalCount': 1})
        if url.endswith('/vulnerable-bom-components'):
            return Response({'items': [{'vulnerabilityWithRemediation': {'vulnerabilityName': 'CVE-CONTRACT'}, '_meta': {'href': 'https://blackduck.contract.test/api/bom/item-id'}}], 'totalCount': 1})
        return Response({'items': [], 'totalCount': 0})
    def put(self, url, **kwargs): _log(url, 'PUT'); return Response({})
def request(method, url, **kwargs): _log(url, method); return Response([])
def get(url, **kwargs): _log(url, 'GET'); return Response({})
""",
        encoding="utf-8",
    )
    return root


def _isolated_subprocess_env(tmp_path: Path, fake_backends: Path, contract: PluginContract) -> dict[str, str]:
    env = os.environ.copy()
    for name in list(env):
        if name.startswith(("OCTANE_", "GITLAB_", "BLACKDUCK_")) or name in {"AGENT_DEVELOPMENT_TOOLKIT_CONFIG_HOME", "XDG_CONFIG_HOME"}:
            env.pop(name)
    env.update({
        "AGENT_DEVELOPMENT_TOOLKIT_CONFIG_HOME": str(tmp_path / "config"),
        "HOME": str(tmp_path / "home"),
        "USERPROFILE": str(tmp_path / "home"),
        "FAKE_KEYRING_FILE": str(tmp_path / "keyring.json"),
        "FAKE_HTTP_LOG": str(tmp_path / "http.jsonl"),
        "PYTHONPATH": os.pathsep.join(filter(None, (str(fake_backends), env.get("PYTHONPATH", "")))),
    })
    return env


def _relocated_skill(repo_root: Path, tmp_path: Path, contract: PluginContract) -> Path:
    root = tmp_path / "replacement" / contract.skill
    shutil.copytree(_scripts(repo_root, contract), root / "scripts")
    (root / "SKILL.md").write_text("# relocated contract fixture\n", encoding="utf-8")
    assert not (root / ".env").exists()
    return root


def _run(script: Path, arguments: tuple[str, ...] | list[str], env: dict[str, str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run([sys.executable, str(script), *arguments], env=env, text=True, capture_output=True, timeout=10)


def _login_arguments(contract: PluginContract, profile: str = "default", no_activate: bool = False) -> tuple[str, ...]:
    values = (
        "login", "--profile", profile, "--user", contract.keyring_user if profile == "default" else f"{profile}-user",
        contract.secret_flag, "contract-secret", contract.endpoint_flag,
        contract.endpoint if profile == "default" else f"https://{profile}.{contract.name}.test",
        *contract.login_extra, "--skip-test",
    )
    return (*values, "--no-activate") if no_activate else values


@pytest.mark.parametrize("contract", CONTRACTS, ids=lambda item: item.name)
def test_subprocess_login_profiles_and_relocated_api_operation_need_no_dotenv_or_real_backends(
    repo_root: Path,
    tmp_path: Path,
    fake_backends: Path,
    contract: PluginContract,
) -> None:
    root = _relocated_skill(repo_root, tmp_path, contract)
    env = _isolated_subprocess_env(tmp_path, fake_backends, contract)
    token = root / "scripts" / contract.token_script
    api = root / "scripts" / contract.api_script

    login = _run(token, _login_arguments(contract), env)
    assert login.returncode == 0, login.stdout + login.stderr
    second = _run(token, _login_arguments(contract, "staging", no_activate=True), env)
    assert second.returncode == 0, second.stdout + second.stderr
    profiles = _run(token, ("profiles",), env)
    assert profiles.returncode == 0, profiles.stdout + profiles.stderr
    payload = json.loads(profiles.stdout)
    assert payload["data"] == {"active_profile": "default", "profiles": ["default", "staging"]}

    operation = _run(api, contract.api_args, env)
    assert operation.returncode == 0, operation.stdout + operation.stderr
    urls = [json.loads(line)["url"] for line in (tmp_path / "http.jsonl").read_text().splitlines()]
    assert urls and all(url.startswith(contract.endpoint) for url in urls)
    assert "contract-secret" not in operation.stdout + operation.stderr


@pytest.mark.parametrize("contract", CONTRACTS, ids=lambda item: item.name)
def test_subprocess_mutation_uses_selected_profile_without_exposing_secret(
    repo_root: Path,
    tmp_path: Path,
    fake_backends: Path,
    contract: PluginContract,
) -> None:
    root = _relocated_skill(repo_root, tmp_path, contract)
    env = _isolated_subprocess_env(tmp_path, fake_backends, contract)
    login = _run(root / "scripts" / contract.token_script, _login_arguments(contract), env)
    assert login.returncode == 0, login.stdout + login.stderr
    (tmp_path / "http.jsonl").unlink(missing_ok=True)

    mutation = _run(root / "scripts" / contract.api_script, contract.write_args, env)

    assert mutation.returncode == 0, mutation.stdout + mutation.stderr
    calls = [json.loads(line) for line in (tmp_path / "http.jsonl").read_text().splitlines()]
    writes = [
        call for call in calls
        if call["method"] in {"POST", "PUT"} and not call["url"].endswith("/api/tokens/authenticate")
    ]
    assert writes and all(call["url"].startswith(contract.endpoint) for call in writes)
    assert "contract-secret" not in mutation.stdout + mutation.stderr + json.dumps(calls)


@pytest.mark.parametrize("contract", CONTRACTS, ids=lambda item: item.name)
@pytest.mark.parametrize("unsafe_endpoint", [
    "http://service.example.test",
    "https://user:secret@service.example.test",
    "https://service.example.test?query=value",
    "https://service.example.test/#fragment",
])
def test_subprocess_login_rejects_unsafe_endpoint_without_traceback_or_mutation(
    repo_root: Path,
    tmp_path: Path,
    fake_backends: Path,
    contract: PluginContract,
    unsafe_endpoint: str,
) -> None:
    root = _relocated_skill(repo_root, tmp_path, contract)
    env = _isolated_subprocess_env(tmp_path, fake_backends, contract)
    arguments = list(_login_arguments(contract))
    arguments[arguments.index(contract.endpoint)] = unsafe_endpoint

    result = _run(root / "scripts" / contract.token_script, arguments, env)

    assert result.returncode == 1
    assert "Traceback" not in result.stdout + result.stderr
    assert not (tmp_path / "keyring.json").exists()
    assert not (tmp_path / "config" / f"{contract.name}.json").exists()


@pytest.mark.parametrize("contract", CONTRACTS, ids=lambda item: item.name)
def test_subprocess_legacy_setup_rejects_unsafe_endpoint_without_mutation(
    repo_root: Path,
    tmp_path: Path,
    fake_backends: Path,
    contract: PluginContract,
) -> None:
    root = _relocated_skill(repo_root, tmp_path, contract)
    env = _isolated_subprocess_env(tmp_path, fake_backends, contract)
    arguments = (
        "setup", "--user", contract.keyring_user,
        contract.secret_flag, "contract-secret",
        contract.endpoint_flag, "http://unsafe.example.test",
        "--write-secret-to-env",
    )

    result = _run(root / "scripts" / contract.token_script, arguments, env)

    assert result.returncode == 1
    assert not (tmp_path / "keyring.json").exists()
    assert not (root / ".env").exists()


@pytest.mark.parametrize("contract", CONTRACTS, ids=lambda item: item.name)
def test_subprocess_failed_login_verification_rolls_back_exact_profile_and_keyring_state(
    repo_root: Path,
    tmp_path: Path,
    fake_backends: Path,
    contract: PluginContract,
) -> None:
    root = _relocated_skill(repo_root, tmp_path, contract)
    env = _isolated_subprocess_env(tmp_path, fake_backends, contract)
    token = root / "scripts" / contract.token_script
    first = _run(token, _login_arguments(contract), env)
    assert first.returncode == 0, first.stdout + first.stderr
    config_path = tmp_path / "config" / f"{contract.name}.json"
    prior_config = config_path.read_bytes()
    prior_keyring = json.loads((tmp_path / "keyring.json").read_text(encoding="utf-8"))

    # Credential verification is deliberately made unavailable.  This drives
    # the public login transaction's failure/rollback path without HTTP.
    env["PATH"] = str(tmp_path / "empty-path")
    replacement = list(_login_arguments(contract))
    replacement.remove("--skip-test")
    replacement[replacement.index("contract-secret")] = "replacement-secret"
    replacement[replacement.index(contract.endpoint)] = f"https://replacement.{contract.name}.test"
    failed = _run(token, replacement, env)

    assert failed.returncode == 1
    assert config_path.read_bytes() == prior_config
    assert json.loads((tmp_path / "keyring.json").read_text(encoding="utf-8")) == prior_keyring
    assert "replacement-secret" not in failed.stdout + failed.stderr


@pytest.mark.parametrize("contract", CONTRACTS, ids=lambda item: item.name)
@pytest.mark.parametrize("failure", ("missing", "backend"))
def test_subprocess_api_keyring_failures_are_local_distinct_and_have_exit_code_one(
    repo_root: Path,
    tmp_path: Path,
    fake_backends: Path,
    contract: PluginContract,
    failure: str,
) -> None:
    root = _relocated_skill(repo_root, tmp_path, contract)
    env = _isolated_subprocess_env(tmp_path, fake_backends, contract)
    login = _run(root / "scripts" / contract.token_script, _login_arguments(contract), env)
    assert login.returncode == 0, login.stdout + login.stderr
    (tmp_path / "http.jsonl").unlink(missing_ok=True)
    if failure == "missing":
        (tmp_path / "keyring.json").write_text("{}", encoding="utf-8")
        expected = contract.missing_code
    else:
        env["FAKE_KEYRING_MODE"] = "backend"
        expected = contract.backend_code

    result = _run(root / "scripts" / contract.api_script, contract.api_args, env)
    assert result.returncode == 1
    assert expected in result.stdout + result.stderr
    assert not (tmp_path / "http.jsonl").exists()


@pytest.mark.parametrize("contract", CONTRACTS, ids=lambda item: item.name)
def test_subprocess_rejects_simultaneous_direct_and_keyring_credentials(
    repo_root: Path,
    tmp_path: Path,
    fake_backends: Path,
    contract: PluginContract,
) -> None:
    root = _relocated_skill(repo_root, tmp_path, contract)
    env = _isolated_subprocess_env(tmp_path, fake_backends, contract)
    env[contract.endpoint_env] = contract.endpoint
    env[contract.secret_env] = "direct-secret"
    env[contract.keyring_env] = contract.keyring_user
    if contract.name == "octane":
        env["OCTANE_CLIENT_ID"] = contract.keyring_user

    result = _run(root / "scripts" / contract.api_script, contract.api_args, env)

    assert result.returncode == 1
    assert contract.mismatch_code in result.stdout + result.stderr
    assert not (tmp_path / "http.jsonl").exists()


@pytest.mark.parametrize("contract", CONTRACTS, ids=lambda item: item.name)
@pytest.mark.parametrize("override_kind", ("endpoint", "keyring", "direct-secret"))
def test_subprocess_partial_credential_overrides_reject_profile_pairing_before_keyring_or_http(
    repo_root: Path,
    tmp_path: Path,
    fake_backends: Path,
    contract: PluginContract,
    override_kind: str,
) -> None:
    root = _relocated_skill(repo_root, tmp_path, contract)
    env = _isolated_subprocess_env(tmp_path, fake_backends, contract)
    login = _run(root / "scripts" / contract.token_script, _login_arguments(contract), env)
    assert login.returncode == 0, login.stdout + login.stderr
    (tmp_path / "http.jsonl").unlink(missing_ok=True)
    override = {
        "endpoint": (contract.endpoint_env, "https://wrong-endpoint.contract.test"),
        "keyring": (contract.keyring_env, "wrong-keyring-user"),
        "direct-secret": (contract.secret_env, "wrong-direct-secret"),
    }[override_kind]
    env[override[0]] = override[1]

    result = _run(root / "scripts" / contract.api_script, contract.api_args, env)
    assert result.returncode == 1
    assert contract.mismatch_code in result.stdout + result.stderr
    assert not (tmp_path / "http.jsonl").exists()
