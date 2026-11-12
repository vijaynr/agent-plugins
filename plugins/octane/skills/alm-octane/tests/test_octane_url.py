"""RED tests for Task 3: Octane URL delegation and coherent URL overrides."""
from __future__ import annotations

import json
import subprocess
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
from test_octane_profile_selection import profile_selection_document


FAVORITE_URL = "https://command-line.example.test/ui/favorites/42?p=777/888"


def test_favorite_url_parsing_and_read_only_delegation(tmp_path, monkeypatch, isolated_runtime):
    wrapper = load_script(relocated_skill(tmp_path, "favorite-url"), "octane_url", monkeypatch)
    parts = wrapper.parse_octane_url(FAVORITE_URL)
    assert parts == {"base_url": "https://command-line.example.test", "shared_space_id": "777",
                     "workspace_id": "888", "entity_type": "favorite", "entity_id": "42"}
    cmd = wrapper.build_client_cmd(parts, None, ["--page-size", "20"], "selected")
    assert cmd[3:] == ["--profile", "selected", "list-favorite-items", "--entity-id", "42",
                       "--workspace-id", "888", "--shared-space-id", "777", "--page-size", "20"]
    with pytest.raises(SystemExit):
        wrapper.build_client_cmd(parts, "update-feature", [], None)
    with pytest.raises(SystemExit):
        wrapper.build_client_cmd(wrapper.parse_octane_url(OCTANE_UI_URL), "get-favorite", [], None)


@pytest.mark.parametrize("path", ["../42", "42/extra", "%2e%2e", "42%2fextra"])
def test_favorite_path_requires_numeric_id(tmp_path, monkeypatch, isolated_runtime, path):
    wrapper = load_script(relocated_skill(tmp_path, "bad-favorite-url"), "octane_url", monkeypatch)
    with pytest.raises(SystemExit):
        wrapper.parse_octane_url("https://command-line.example.test/ui/favorites/" + path + "?p=777/888")


OCTANE_UI_URL = (
    "https://command-line.example.test/ui/entity-navigation"
    "?p=777/888&entityType=defect&id=42"
)


def test_relocated_url_wrapper_always_delegates_to_its_adjacent_client(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    isolated_runtime: tuple[Path, FakeKeyring],
) -> None:
    config_home, _ = isolated_runtime
    monkeypatch.setenv("USERPROFILE", str(config_home.parent / "home"))
    unrelated_root = Path.home() / ".copilot" / "skills" / "alm-octane"
    (unrelated_root / "scripts").mkdir(parents=True)
    (unrelated_root / "SKILL.md").write_text("---\nname: alm-octane\n---\n", encoding="utf-8")
    (unrelated_root / "scripts" / "octane_client.py").write_text(
        "raise AssertionError('unrelated installed client must not be selected')\n",
        encoding="utf-8",
    )
    relocated_root = relocated_skill(tmp_path, "relocated-url-wrapper")

    url_wrapper = load_script(relocated_root, "octane_url", monkeypatch)

    assert Path(url_wrapper.CLIENT_SCRIPT) == relocated_root / "scripts" / "octane_client.py"


def test_profile_is_forwarded_before_the_delegated_client_subcommand(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    isolated_runtime: tuple[Path, FakeKeyring],
    capsys: pytest.CaptureFixture[str],
) -> None:
    _, _ = isolated_runtime
    relocated_root = relocated_skill(tmp_path, "profile-forwarding")
    url_wrapper = load_script(relocated_root, "octane_url", monkeypatch)
    calls: list[dict[str, Any]] = []

    def fake_run(command: list[str], **kwargs: Any) -> subprocess.CompletedProcess[str]:
        calls.append({"command": command, **kwargs})
        return subprocess.CompletedProcess(command, 0, stdout='{"ok": true}', stderr="")

    monkeypatch.setattr(url_wrapper.subprocess, "run", fake_run)
    monkeypatch.setattr(
        sys,
        "argv",
        ["octane_url.py", "--profile", "command-line", OCTANE_UI_URL],
    )

    url_wrapper.main()

    delegated = calls[0]
    assert delegated["command"][:6] == [
        "uv",
        "run",
        str(relocated_root / "scripts" / "octane_client.py"),
        "--profile",
        "command-line",
        "get-defect",
    ]
    assert delegated["command"][6:] == [
        "--entity-id",
        "42",
        "--workspace-id",
        "888",
        "--shared-space-id",
        "777",
    ]
    assert delegated["env"]["OCTANE_BASE_URL"] == "https://command-line.example.test"
    assert json.loads(capsys.readouterr().out)["result"] == {"ok": True}


def test_url_wrapper_rejects_mismatched_direct_credential_endpoint_before_subprocess(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    isolated_runtime: tuple[Path, FakeKeyring],
) -> None:
    _, _ = isolated_runtime
    wrapper = load_script(relocated_skill(tmp_path, "direct-url-mismatch"), "octane_url", monkeypatch)
    monkeypatch.setenv("OCTANE_BASE_URL", "https://configured.example.test")
    monkeypatch.setenv("OCTANE_CLIENT_ID", "direct-client")
    monkeypatch.setenv("OCTANE_CLIENT_SECRET", "direct-secret")
    monkeypatch.setattr(wrapper.subprocess, "run", lambda *_args, **_kwargs: pytest.fail("must not launch subprocess"))

    result = wrapper.run_client_cmd(["unused"], "https://attacker.example.test")

    assert result["error_code"] == "OCTANE_CREDENTIAL_SOURCE_MISMATCH"


def test_url_wrapper_rejects_insecure_http_before_subprocess(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    isolated_runtime: tuple[Path, FakeKeyring],
) -> None:
    _, _ = isolated_runtime
    wrapper = load_script(relocated_skill(tmp_path, "insecure-url"), "octane_url", monkeypatch)
    monkeypatch.setattr(wrapper.subprocess, "run", lambda *_args, **_kwargs: pytest.fail("must not launch subprocess"))

    result = wrapper.run_client_cmd(["unused"], "http://octane.example.test")

    assert result["error_code"] == "OCTANE_URL_ENDPOINT_UNSAFE"


def test_url_endpoint_matching_selected_profile_can_override_url_tenant_ids_coherently(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    isolated_runtime: tuple[Path, FakeKeyring],
) -> None:
    config_home, fake_keyring = isolated_runtime
    document = profile_selection_document()
    write_profile(config_home, document)
    fake_keyring.passwords[(SERVICE_NAME, "command-line-client")] = "command-line-secret"
    monkeypatch.setenv("OCTANE_BASE_URL", "https://command-line.example.test")
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "octane_client.py",
            "--profile",
            "command-line",
            "get-defect",
            "--entity-id",
            "42",
            "--workspace-id",
            "888",
            "--shared-space-id",
            "777",
        ],
    )

    client = load_script(relocated_skill(tmp_path, "coherent-url-profile"), "octane_client", monkeypatch)
    client.main()

    session = FakeSession.instances[-1]
    assert session.posts[0]["url"] == "https://command-line.example.test/authentication/sign_in"
    assert session.posts[0]["json"] == {
        "client_id": "command-line-client",
        "client_secret": "command-line-secret",
    }
    assert session.requests[0]["url"].startswith(
        "https://command-line.example.test/api/shared_spaces/777/workspaces/888/defects/42"
    )
    assert fake_keyring.get_calls == [(SERVICE_NAME, "command-line-client")]


def test_url_endpoint_cannot_pair_with_an_unrelated_selected_profile_credential(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    isolated_runtime: tuple[Path, FakeKeyring],
    capsys: pytest.CaptureFixture[str],
) -> None:
    config_home, fake_keyring = isolated_runtime
    write_profile(config_home, profile_selection_document())
    fake_keyring.passwords[(SERVICE_NAME, "active-client")] = "active-secret"
    monkeypatch.setenv("OCTANE_BASE_URL", "https://command-line.example.test")
    monkeypatch.setattr(
        sys,
        "argv",
        ["octane_client.py", "--profile", "active", "get-defect", "--entity-id", "42"],
    )

    client = load_script(relocated_skill(tmp_path, "mismatched-url-profile"), "octane_client", monkeypatch)
    with pytest.raises(SystemExit) as exc_info:
        client.main()

    payload = json.loads(capsys.readouterr().out)
    assert exc_info.value.code != 0
    assert payload["error_code"] == "OCTANE_CREDENTIAL_SOURCE_MISMATCH"
    assert payload["error"] == "URL endpoint does not match the selected Octane profile"
    assert fake_keyring.get_calls == []
    assert FakeSession.instances == []
