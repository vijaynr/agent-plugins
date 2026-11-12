"""Durable, non-secret profile metadata for the GitLab skill."""
# Shared infrastructure is structurally contract-locked across plugins; only
# service schema, migration fields, and diagnostics should intentionally differ.
from __future__ import annotations

import json
import os
import re
import sys
import tempfile
import time
from contextlib import contextmanager
from pathlib import Path
from urllib.parse import urlparse
from typing import Any, Mapping

SCHEMA_VERSION = 1
SERVICE = "gitlab"
PROFILE_NAME = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,63}$")
GITLAB_SETTINGS = {"project_id", "allowed_project_ids", "read_only_mode", "timeout"}


class ConfigError(ValueError):
    """Raised when durable profile metadata is invalid or cannot be written."""


def validate_endpoint(endpoint: Any) -> str:
    if not isinstance(endpoint, str) or not endpoint.strip():
        raise ConfigError("credential endpoint must be a non-empty HTTPS URL")
    normalized = endpoint.strip().rstrip("/")
    parsed = urlparse(normalized)
    if (
        parsed.scheme.lower() != "https"
        or not parsed.hostname
        or parsed.username is not None
        or parsed.password is not None
        or parsed.query
        or parsed.fragment
    ):
        raise ConfigError("credential endpoint must be an HTTPS URL without userinfo, query, or fragment")
    return normalized


def config_home(environ: Mapping[str, str] | None = None) -> Path:
    env = os.environ if environ is None else environ
    override = env.get("AGENT_DEVELOPMENT_TOOLKIT_CONFIG_HOME", "").strip()
    if override:
        return Path(override).expanduser()
    if sys.platform == "win32":
        appdata = env.get("APPDATA", "").strip()
        return Path(appdata).expanduser() / "AgentDevelopmentToolkit" if appdata else Path.home() / "AppData" / "Roaming" / "AgentDevelopmentToolkit"
    if sys.platform == "darwin":
        return Path.home() / "Library" / "Application Support" / "AgentDevelopmentToolkit"
    xdg = env.get("XDG_CONFIG_HOME", "").strip()
    return (Path(xdg).expanduser() if xdg else Path.home() / ".config") / "agent-development-toolkit"


def config_path(environ: Mapping[str, str] | None = None) -> Path:
    return config_home(environ) / f"{SERVICE}.json"


STALE_LEGACY_LOCK_SECONDS = 300


def _process_exists(pid: int) -> bool:
    if pid <= 0:
        return False
    if pid == os.getpid():
        return True
    if sys.platform == "win32":
        import ctypes
        from ctypes import wintypes

        kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
        kernel32.OpenProcess.argtypes = (wintypes.DWORD, wintypes.BOOL, wintypes.DWORD)
        kernel32.OpenProcess.restype = wintypes.HANDLE
        kernel32.CloseHandle.argtypes = (wintypes.HANDLE,)
        kernel32.CloseHandle.restype = wintypes.BOOL
        handle = kernel32.OpenProcess(0x1000, False, pid)
        if handle:
            kernel32.CloseHandle(handle)
            return True
        return ctypes.get_last_error() == 5
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    return True


def _lock_identity(path: Path) -> tuple[int, int, int, int]:
    status = path.stat()
    return status.st_dev, status.st_ino, status.st_mtime_ns, status.st_size


def _unlink_if_unchanged(path: Path, identity: tuple[int, int, int, int]) -> bool:
    for attempt in range(50):
        try:
            if _lock_identity(path) != identity:
                return False
            path.unlink()
            return True
        except FileNotFoundError:
            return False
        except PermissionError:
            if attempt == 49:
                return False
            time.sleep(0.02)
    return False


def _discard_stale_lock(path: Path) -> bool:
    try:
        identity = _lock_identity(path)
        raw = path.read_text(encoding="utf-8")
    except (FileNotFoundError, OSError):
        return False
    try:
        owner = json.loads(raw)
        pid = int(owner["pid"])
    except (ValueError, TypeError, KeyError, json.JSONDecodeError):
        age = time.time() - identity[2] / 1_000_000_000
        return age >= STALE_LEGACY_LOCK_SECONDS and _unlink_if_unchanged(path, identity)
    return not _process_exists(pid) and _unlink_if_unchanged(path, identity)


@contextmanager
def profile_lock(timeout: float = 1.0):
    lock_path = config_path().with_suffix(".json.lock")
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    deadline = time.monotonic() + timeout
    fd: int | None = None
    owned_identity: tuple[int, int, int, int] | None = None
    while fd is None:
        try:
            fd = os.open(str(lock_path), os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
            metadata = json.dumps({"pid": os.getpid(), "created": time.time()}).encode("utf-8")
            os.write(fd, metadata)
            os.fsync(fd)
            owned_identity = _lock_identity(lock_path)
        except FileExistsError:
            if _discard_stale_lock(lock_path):
                continue
            if time.monotonic() >= deadline:
                raise ConfigError(f"timed out waiting for credential profile lock: {lock_path}")
            time.sleep(0.02)
        except OSError:
            if fd is not None:
                status = os.fstat(fd)
                owned_identity = status.st_dev, status.st_ino, status.st_mtime_ns, status.st_size
                os.close(fd)
                fd = None
            if owned_identity is not None:
                _unlink_if_unchanged(lock_path, owned_identity)
            raise
    try:
        yield
    finally:
        os.close(fd)
        if owned_identity is not None:
            _unlink_if_unchanged(lock_path, owned_identity)


def empty_document() -> dict[str, Any]:
    return {"schema_version": SCHEMA_VERSION, "active_profile": None, "profiles": {}}


def validate_document(value: Any) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ConfigError("credential profile document must be a JSON object")
    if value.get("schema_version") != SCHEMA_VERSION:
        raise ConfigError(f"unsupported credential profile schema: {value.get('schema_version')!r}")
    profiles = value.get("profiles")
    active = value.get("active_profile")
    if not isinstance(profiles, dict):
        raise ConfigError("credential profile 'profiles' must be an object")
    if active is not None and (not isinstance(active, str) or active not in profiles):
        raise ConfigError("credential profile has an invalid active_profile")
    for name, profile in profiles.items():
        if not isinstance(name, str) or not PROFILE_NAME.fullmatch(name) or not isinstance(profile, dict):
            raise ConfigError("credential profile names and values must be valid objects")
        try:
            validate_endpoint(profile.get("endpoint"))
        except ConfigError as exc:
            raise ConfigError(f"credential profile {name!r} has invalid endpoint: {exc}") from exc
        if not isinstance(profile.get("keyring_user"), str) or not profile["keyring_user"].strip():
            raise ConfigError(f"credential profile {name!r} has no keyring_user")
        settings = profile.get("settings")
        if not isinstance(settings, dict) or set(settings) != GITLAB_SETTINGS:
            raise ConfigError(f"credential profile {name!r} has invalid GitLab settings")
        for key in ("project_id", "allowed_project_ids"):
            if not isinstance(settings.get(key), str):
                raise ConfigError(f"credential profile {name!r} has invalid {key}")
        if settings.get("read_only_mode") not in {"true", "false"}:
            raise ConfigError(f"credential profile {name!r} has invalid read_only_mode")
        timeout = settings.get("timeout")
        if not isinstance(timeout, str) or not timeout.isdigit() or int(timeout) <= 0:
            raise ConfigError(f"credential profile {name!r} has invalid timeout")
    return value


def read_document(path: Path | None = None) -> dict[str, Any]:
    target = path or config_path()
    if not target.is_file():
        return empty_document()
    try:
        return validate_document(json.loads(target.read_text(encoding="utf-8")))
    except (OSError, json.JSONDecodeError) as exc:
        raise ConfigError(f"failed to read credential profiles: {exc}") from exc


def _sync_parent_directory(target: Path) -> None:
    if os.name == "nt":
        return
    directory_fd = os.open(str(target.parent), os.O_RDONLY)
    try:
        os.fsync(directory_fd)
    finally:
        os.close(directory_fd)


def _replace_bytes(target: Path, data: bytes) -> None:
    target.parent.mkdir(parents=True, exist_ok=True)
    temporary: Path | None = None
    try:
        fd, name = tempfile.mkstemp(prefix=f".{target.name}.", suffix=".tmp", dir=target.parent)
        temporary = Path(name)
        with os.fdopen(fd, "wb") as stream:
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
        if os.name != "nt":
            os.chmod(temporary, 0o600)
        os.replace(temporary, target)
        temporary = None
        _sync_parent_directory(target)
    except OSError as exc:
        raise ConfigError(f"failed to write credential profiles: {exc}") from exc
    finally:
        if temporary is not None:
            try:
                temporary.unlink(missing_ok=True)
            except OSError:
                pass


def write_document(document: dict[str, Any], path: Path | None = None) -> None:
    target = path or config_path()
    validate_document(document)
    serialized = (json.dumps(document, indent=2, ensure_ascii=False) + "\n").encode("utf-8")
    _replace_bytes(target, serialized)


def snapshot(path: Path | None = None) -> bytes | None:
    target = path or config_path()
    return target.read_bytes() if target.is_file() else None


def restore(snapshot_bytes: bytes | None, path: Path | None = None) -> None:
    target = path or config_path()
    if snapshot_bytes is None:
        try:
            target.unlink(missing_ok=True)
        except OSError as exc:
            raise ConfigError(f"failed to remove credential profiles during rollback: {exc}") from exc
    else:
        _replace_bytes(target, snapshot_bytes)


def named_profile(profile_name: str, path: Path | None = None) -> tuple[str, dict[str, Any]]:
    document = read_document(path)
    if profile_name not in document["profiles"]:
        raise ConfigError(f"credential profile not found: {profile_name}")
    return profile_name, document["profiles"][profile_name]


def active_profile(path: Path | None = None) -> tuple[str, dict[str, Any]] | None:
    document = read_document(path)
    name = document.get("active_profile")
    if not name:
        return None
    return name, document["profiles"][name]


def _read_legacy_env(path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if stripped and not stripped.startswith("#") and "=" in stripped:
            key, value = stripped.split("=", 1)
            values[key.strip()] = value.strip().strip('"').strip("'")
    return values


def migrate_legacy(skill_root: Path, credential_lookup: Any) -> bool:
    """Migrate one unambiguous keyring-backed legacy configuration."""
    if config_path().is_file():
        return False
    roots = [
        skill_root,
        Path.home() / ".copilot" / "skills" / "gitlab",
        Path.home() / ".agents" / "skills" / "gitlab",
    ]
    seen: set[Path] = set()
    candidates: list[tuple[Path, dict[str, Any]]] = []
    for root in roots:
        canonical = root.resolve()
        if canonical in seen:
            continue
        seen.add(canonical)
        env_path = root / ".env"
        if not env_path.is_file():
            continue
        values = _read_legacy_env(env_path)
        endpoint = values.get("GITLAB_API_URL", "").rstrip("/")
        keyring_user = values.get("GITLAB_TOKEN_KEYRING_USER", "")
        if not endpoint or not keyring_user:
            continue
        profile = default_profile(endpoint, keyring_user, {
            "project_id": values.get("GITLAB_PROJECT_ID", ""),
            "allowed_project_ids": values.get("GITLAB_ALLOWED_PROJECT_IDS", ""),
            "read_only_mode": values.get("GITLAB_READ_ONLY_MODE", "false").lower(),
            "timeout": values.get("GITLAB_TIMEOUT", "60"),
        })
        candidates.append((env_path, profile))
    if not candidates:
        return False
    availability: dict[str, bool] = {}
    usable: list[tuple[Path, dict[str, Any]]] = []
    for path, profile in candidates:
        user = profile["keyring_user"]
        if user not in availability:
            try:
                availability[user] = bool(credential_lookup("AgentDevelopmentToolkit:gitlab", user))
            except Exception as exc:
                raise ConfigError(f"failed to check legacy GitLab keyring entry from {path}: {exc}") from exc
        if availability[user]:
            usable.append((path, profile))
    if not usable:
        paths = ", ".join(str(path) for path, _profile in candidates)
        raise ConfigError(f"legacy GitLab keyring entries are missing for candidate paths: {paths}")
    first_path, first = usable[0]
    conflicts = [path for path, profile in usable[1:] if profile != first]
    if conflicts:
        paths = ", ".join(str(path) for path in [first_path, *conflicts])
        raise ConfigError(f"conflicting legacy GitLab profile metadata (endpoint/settings/keyring_user): {paths}")
    migrated = {"schema_version": SCHEMA_VERSION, "active_profile": "default", "profiles": {"default": first}}
    with profile_lock():
        if config_path().is_file():
            if read_document()["profiles"].get("default") == first:
                return False
            raise ConfigError("concurrent legacy GitLab migration conflict; existing profile was preserved")
        write_document(migrated)
    return True


def default_profile(endpoint: str, keyring_user: str, settings: Mapping[str, str]) -> dict[str, Any]:
    return {
        "keyring_user": keyring_user,
        "endpoint": validate_endpoint(endpoint),
        "settings": dict(settings),
    }


def document_with_profile(profile_name: str, profile: dict[str, Any], activate: bool = True) -> dict[str, Any]:
    if not PROFILE_NAME.fullmatch(profile_name):
        raise ConfigError(f"invalid credential profile name: {profile_name!r}")
    document = read_document()
    profiles = dict(document["profiles"])
    profiles[profile_name] = profile
    active = profile_name if activate else document["active_profile"]
    result = {"schema_version": SCHEMA_VERSION, "active_profile": active, "profiles": profiles}
    return validate_document(result)


def document_with_default(profile: dict[str, Any]) -> dict[str, Any]:
    return document_with_profile("default", profile)


def upsert_profile(profile_name: str, profile: dict[str, Any], activate: bool = True) -> bytes | None:
    with profile_lock():
        previous = snapshot()
        write_document(document_with_profile(profile_name, profile, activate))
        return previous


def select_profile(profile_name: str) -> None:
    with profile_lock():
        document = read_document()
        if profile_name not in document["profiles"]:
            raise ConfigError(f"credential profile not found: {profile_name}")
        document["active_profile"] = profile_name
        write_document(document)


def remove_profile(profile_name: str) -> None:
    with profile_lock():
        document = read_document()
        if profile_name not in document["profiles"]:
            raise ConfigError(f"credential profile not found: {profile_name}")
        profiles = dict(document["profiles"])
        del profiles[profile_name]
        active = document["active_profile"]
        if active == profile_name:
            active = sorted(profiles)[0] if profiles else None
        write_document({"schema_version": SCHEMA_VERSION, "active_profile": active, "profiles": profiles})
