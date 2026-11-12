"""Help and parsing must not require runtime credentials or network."""
import json
import sys

import pytest

from test_octane_credential_config import isolated_runtime, load_script, relocated_skill
from test_octane_generic_entities import generic_client, invoke

LEGACY_COMMANDS = """get-work-item get-defect get-feature get-story search-all
create-feature update-feature create-defect update-defect create-story update-story
create-story-under-feature get-story-parent-feature list-feature-items
update-feature-security update-story-status delete-backlog-item create-comment
read-comment add-attachment list-attachments delete-attachment download-attachment
get-manual-test get-suite-runs get-run-history list-work-items list-tasks add-task
list-tags add-tag list-phases""".split()
GENERIC_COMMANDS = """get-entity get-entity-types get-entity-field-metadata
get-filter-metadata get-entities create-entity update-entity get-favorite list-favorite-items""".split()


@pytest.mark.parametrize("arguments", [("--help",), *((command, "--help") for command in LEGACY_COMMANDS + GENERIC_COMMANDS)])
def test_generic_help_without_runtime(tmp_path, monkeypatch, isolated_runtime, capsys, arguments):
    client = load_script(relocated_skill(tmp_path, "help"), "octane_client", monkeypatch)
    monkeypatch.setattr(client, "resolve_runtime_config", lambda *_: pytest.fail("runtime accessed for help"))
    monkeypatch.setattr(sys, "argv", ["octane_client.py", *arguments])
    with pytest.raises(SystemExit) as exc:
        client.main()
    assert exc.value.code == 0
    output = capsys.readouterr().out
    assert (arguments[0] if arguments[0] != "--help" else "get-entity") in output
    if arguments == ("--help",):
        assert all(command in output for command in LEGACY_COMMANDS + GENERIC_COMMANDS)


@pytest.mark.parametrize("command,function,arguments,prefix", [
    ("add-tag", "add_tag", ["--entity-id", "42", "--tag", "SecurityReview"], ("42", "SecurityReview", "work_items", True)),
    ("delete-backlog-item", "delete_backlog_item", ["--entity-id", "42"], ("42", "work_items")),
    ("add-attachment", "add_attachment", ["--entity-id", "42", "--file", "evidence.txt"], ("42", "evidence.txt")),
    ("delete-attachment", "delete_attachment", ["--entity-id", "42", "--attachment-id", "7"], ("7", "42")),
    ("download-attachment", "download_attachment", ["--attachment-id", "7", "--output-file", "evidence.txt"], ("7", "evidence.txt")),
])
def test_legacy_mutating_dispatch_keeps_arguments(generic_client, monkeypatch, capsys, command, function, arguments, prefix):
    client, session = generic_client
    calls = []
    def handler(*values):
        calls.append(values)
        print(json.dumps({"ok": True}))
    monkeypatch.setattr(client, function, handler)
    code, result, _ = invoke(client, monkeypatch, capsys, command, *arguments)
    assert code == 0 and result["ok"] is True
    assert calls[0][:len(prefix)] == prefix
    assert calls[0][-2:] == ("1003", "131002")
    assert session.calls == []


def test_query_and_search_are_mutually_exclusive(tmp_path, monkeypatch, isolated_runtime, capsys):
    client = load_script(relocated_skill(tmp_path, "exclusive"), "octane_client", monkeypatch)
    monkeypatch.setattr(client, "resolve_runtime_config", lambda *_: pytest.fail("runtime accessed for invalid arguments"))
    monkeypatch.setattr(sys, "argv", ["octane_client.py", "get-entities", "--entity-type", "work_items", "--query", "id EQ 1", "--search", "login"])
    with pytest.raises(SystemExit) as exc:
        client.main()
    assert exc.value.code == 2
    assert "not allowed" in capsys.readouterr().err
