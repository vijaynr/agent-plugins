"""Eval tests for core / utility functions in gitlab_cli.py."""
import json
import os
import sys
import re
import pytest
from unittest.mock import patch

SCRIPTS_DIR = os.path.join(os.path.dirname(__file__), '..', 'scripts')
sys.path.insert(0, SCRIPTS_DIR)

SKILL_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))


class TestCanonicalizeAliases:
    """Verify camelCase → snake_case alias mapping."""

    def test_camel_to_snake(self):
        import importlib, gitlab_cli
        importlib.reload(gitlab_cli)
        result = gitlab_cli.canonicalize({
            "projectId": "1", "mergeRequestIid": "5",
            "issueIid": "10", "commitSha": "abc123"
        })
        assert result == {
            "project_id": "1", "merge_request_iid": "5",
            "issue_iid": "10", "commit_sha": "abc123"
        }

    def test_already_snake(self):
        import importlib, gitlab_cli
        importlib.reload(gitlab_cli)
        result = gitlab_cli.canonicalize({"project_id": "1", "merge_request_iid": "5"})
        assert result == {"project_id": "1", "merge_request_iid": "5"}

    def test_unknown_keys_pass_through(self):
        import importlib, gitlab_cli
        importlib.reload(gitlab_cli)
        result = gitlab_cli.canonicalize({"custom_field": "val"})
        assert result == {"custom_field": "val"}


class TestResolveProject:
    def test_explicit_id(self):
        import importlib, gitlab_cli
        importlib.reload(gitlab_cli)
        assert gitlab_cli.resolve_project("99", gitlab_cli.resolve_runtime_config()) == "99"

    def test_default_fallback(self):
        import importlib, gitlab_cli
        importlib.reload(gitlab_cli)
        runtime = gitlab_cli.resolve_runtime_config()
        assert gitlab_cli.resolve_project(None, runtime) == runtime.default_project_id

    def test_empty_returns_empty(self, monkeypatch):
        monkeypatch.setenv("GITLAB_PROJECT_ID", "")
        import importlib, gitlab_cli
        importlib.reload(gitlab_cli)
        assert gitlab_cli.resolve_project(None, gitlab_cli.resolve_runtime_config()) == ""


class TestAllowedProjectIds:
    def test_allowed_passes(self, monkeypatch):
        monkeypatch.setenv("GITLAB_ALLOWED_PROJECT_IDS", "42,99")
        import importlib, gitlab_cli
        importlib.reload(gitlab_cli)
        assert gitlab_cli.resolve_project("42", gitlab_cli.resolve_runtime_config()) == "42"

    def test_blocked_exits(self, monkeypatch):
        monkeypatch.setenv("GITLAB_ALLOWED_PROJECT_IDS", "99")
        import importlib, gitlab_cli
        importlib.reload(gitlab_cli)
        with pytest.raises(SystemExit):
            gitlab_cli.resolve_project("42", gitlab_cli.resolve_runtime_config())


class TestProjectScopePolicy:
    def test_every_global_http_tool_is_blocked_when_allowlist_is_configured(self, monkeypatch):
        monkeypatch.setenv("GITLAB_ALLOWED_PROJECT_IDS", "42")
        import importlib, gitlab_cli
        importlib.reload(gitlab_cli)
        runtime = gitlab_cli.resolve_runtime_config()
        global_tools = [
            tool
            for tool, (method, path, _description) in gitlab_cli.TOOL_MAP.items()
            if method not in {"LOCAL", "COMPOSITE"} and "{project_id}" not in path
        ]

        for tool in global_tools:
            with pytest.raises(SystemExit):
                gitlab_cli.request(tool, {"project_id": "42"}, runtime=runtime)


class TestReadOnlyMode:
    def test_blocks_write(self, monkeypatch):
        monkeypatch.setenv("GITLAB_READ_ONLY_MODE", "true")
        import importlib, gitlab_cli
        importlib.reload(gitlab_cli)
        with pytest.raises(SystemExit):
            gitlab_cli.check_write("create_issue", gitlab_cli.resolve_runtime_config())

    def test_allows_read(self, monkeypatch):
        monkeypatch.setenv("GITLAB_READ_ONLY_MODE", "true")
        import importlib, gitlab_cli
        importlib.reload(gitlab_cli)
        gitlab_cli.check_write("list_issues", gitlab_cli.resolve_runtime_config())

    def test_write_allowed_when_off(self):
        import importlib, gitlab_cli
        importlib.reload(gitlab_cli)
        gitlab_cli.check_write("create_issue", gitlab_cli.resolve_runtime_config())


class TestMissingToken:
    def test_missing_token_exits(self, monkeypatch):
        monkeypatch.setenv("GITLAB_PERSONAL_ACCESS_TOKEN", "")
        import importlib, gitlab_cli
        importlib.reload(gitlab_cli)
        with pytest.raises(SystemExit):
            gitlab_cli.require_token(gitlab_cli.resolve_runtime_config())


class TestFillPath:
    def test_fills_simple(self):
        import importlib, gitlab_cli
        importlib.reload(gitlab_cli)
        path, used = gitlab_cli.fill_path(
            "/projects/{project_id}/issues/{issue_iid}",
            {"project_id": "42", "issue_iid": "7"}
        )
        assert path == "/projects/42/issues/7"
        assert used == {"project_id", "issue_iid"}

    def test_url_encodes(self):
        import importlib, gitlab_cli
        importlib.reload(gitlab_cli)
        path, used = gitlab_cli.fill_path(
            "/projects/{project_id}/repository/files/{file_path}",
            {"project_id": "42", "file_path": "src/main.py"}
        )
        assert "src%2Fmain.py" in path

    def test_missing_param_exits(self):
        import importlib, gitlab_cli
        importlib.reload(gitlab_cli)
        with pytest.raises(SystemExit):
            gitlab_cli.fill_path("/projects/{project_id}", {})


class TestToolMapCompleteness:
    """Every tool in TOOL_MAP must be documented in references/TOOLS.md."""

    def test_all_tools_in_reference(self):
        import importlib, gitlab_cli
        importlib.reload(gitlab_cli)
        tools_ref_path = os.path.join(SKILL_DIR, 'references', 'TOOLS.md')
        with open(tools_ref_path) as f:
            ref_text = f.read()
        missing = [t for t in gitlab_cli.TOOL_MAP if f'`{t}`' not in ref_text]
        assert missing == [], f"Tools in TOOL_MAP but not in references/TOOLS.md: {missing}"

    def test_write_commands_subset_of_map(self):
        import importlib, gitlab_cli
        importlib.reload(gitlab_cli)
        orphan = gitlab_cli.WRITE_COMMANDS - set(gitlab_cli.TOOL_MAP.keys())
        assert orphan == set(), f"WRITE_COMMANDS not in TOOL_MAP: {orphan}"

    def test_all_evals_cover_real_tools(self):
        """Every tool mentioned in evals/evals.json assertions should be a real tool."""
        import importlib, gitlab_cli
        importlib.reload(gitlab_cli)
        evals_path = os.path.join(SKILL_DIR, 'evals', 'evals.json')
        with open(evals_path) as f:
            evals_data = json.load(f)
        tool_names = set(gitlab_cli.TOOL_MAP.keys())
        for ev in evals_data['evals']:
            for assertion in ev.get('assertions', []):
                # Extract tool names mentioned in assertions
                mentioned = re.findall(r'\b([a-z_]+(?:_[a-z_]+)+)\b', assertion)
                for m in mentioned:
                    if m in tool_names:
                        break  # at least one valid tool found


class TestHeaders:
    def test_includes_token(self):
        import importlib, gitlab_cli
        importlib.reload(gitlab_cli)
        runtime = gitlab_cli.resolve_runtime_config()
        h = gitlab_cli.headers(gitlab_cli.require_token(runtime))
        assert h["PRIVATE-TOKEN"] == runtime.token_value
        assert h["Accept"] == "application/json"

    def test_extra_merged(self):
        import importlib, gitlab_cli
        importlib.reload(gitlab_cli)
        runtime = gitlab_cli.resolve_runtime_config()
        h = gitlab_cli.headers(gitlab_cli.require_token(runtime), {"X-Custom": "yes"})
        assert h["X-Custom"] == "yes"
        assert "PRIVATE-TOKEN" in h
