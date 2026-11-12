"""Eval tests for dotenv integration."""
import json
import os
import sys
import pytest
from unittest.mock import patch, MagicMock

SCRIPTS_DIR = os.path.join(os.path.dirname(__file__), '..', 'scripts')
SKILL_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, SCRIPTS_DIR)


class TestDotenvLoading:
    """Verify configuration is loaded only through the explicit resolver."""

    def test_import_has_no_configuration_side_effects(self):
        import credential_config
        import importlib, gitlab_cli

        with patch.object(credential_config, "migrate_legacy") as migrate, \
             patch.object(credential_config, "active_profile") as active, \
             patch.object(credential_config, "named_profile") as named:
            importlib.reload(gitlab_cli)

        migrate.assert_not_called()
        active.assert_not_called()
        named.assert_not_called()

    def test_loads_dotenv_when_available(self, tmp_path, monkeypatch):
        env_file = tmp_path / ".env"
        env_file.write_text(
            "GITLAB_API_URL=https://dotenv.example.test/api/v4\n"
            "GITLAB_PERSONAL_ACCESS_TOKEN=glpat-from-dotenv\n"
        )
        monkeypatch.chdir(tmp_path)
        monkeypatch.delenv("GITLAB_PERSONAL_ACCESS_TOKEN", raising=False)
        monkeypatch.delenv("GITLAB_API_URL", raising=False)

        mock_values = MagicMock(return_value={
            "GITLAB_API_URL": "https://dotenv.example.test/api/v4",
            "GITLAB_PERSONAL_ACCESS_TOKEN": "glpat-from-dotenv",
        })
        with patch.dict("sys.modules", {"dotenv": MagicMock(dotenv_values=mock_values)}):
            import importlib, gitlab_cli
            importlib.reload(gitlab_cli)
            gitlab_cli.script_skill_root = tmp_path
            assert not mock_values.called
            runtime = gitlab_cli.resolve_runtime_config()
            assert mock_values.called
            assert runtime.token_value == "glpat-from-dotenv"

    def test_repeated_resolution_is_deterministic_and_does_not_mutate_environment(self, tmp_path, monkeypatch):
        (tmp_path / ".env").write_text(
            "GITLAB_API_URL=https://dotenv.example.com/api/v4\n"
            "GITLAB_PERSONAL_ACCESS_TOKEN=glpat-from-dotenv\n"
        )
        monkeypatch.delenv("GITLAB_API_URL", raising=False)
        monkeypatch.delenv("GITLAB_PERSONAL_ACCESS_TOKEN", raising=False)
        import importlib, gitlab_cli
        importlib.reload(gitlab_cli)
        gitlab_cli.script_skill_root = tmp_path

        first = gitlab_cli.resolve_runtime_config()
        second = gitlab_cli.resolve_runtime_config()

        assert first == second
        assert first.base_url == "https://dotenv.example.com/api/v4"
        assert "GITLAB_API_URL" not in os.environ
        assert "GITLAB_PERSONAL_ACCESS_TOKEN" not in os.environ

    def test_works_without_dotenv(self, monkeypatch):
        monkeypatch.setenv("GITLAB_PERSONAL_ACCESS_TOKEN", "glpat-direct")
        import importlib
        with patch.dict("sys.modules", {"dotenv": None}):
            import gitlab_cli
            importlib.reload(gitlab_cli)
            assert gitlab_cli.resolve_runtime_config().token_value == "glpat-direct"

    def test_env_vars_override_dotenv(self, tmp_path, monkeypatch):
        env_file = tmp_path / ".env"
        env_file.write_text("GITLAB_API_URL=https://dotenv.example.com/api/v4\n")
        monkeypatch.chdir(tmp_path)
        monkeypatch.setenv("GITLAB_API_URL", "https://override.example.com/api/v4")
        import importlib, gitlab_cli
        importlib.reload(gitlab_cli)
        gitlab_cli.script_skill_root = tmp_path
        assert gitlab_cli.resolve_runtime_config().base_url == "https://override.example.com/api/v4"


class TestEnvExample:
    """Verify .env.example file is correct and complete."""

    def test_example_exists(self):
        assert os.path.isfile(os.path.join(SKILL_DIR, '.env.example'))

    def test_example_has_all_env_vars(self):
        with open(os.path.join(SKILL_DIR, '.env.example')) as f:
            content = f.read()
        required_vars = [
            "GITLAB_PERSONAL_ACCESS_TOKEN",
            "GITLAB_API_URL",
            "GITLAB_PROJECT_ID",
            "GITLAB_ALLOWED_PROJECT_IDS",
            "GITLAB_READ_ONLY_MODE",
            "GITLAB_TIMEOUT",
        ]
        for var in required_vars:
            assert var in content, f".env.example missing {var}"

    def test_example_does_not_prepopulate_token(self):
        with open(os.path.join(SKILL_DIR, '.env.example')) as f:
            content = f.read()
        assert "GITLAB_PERSONAL_ACCESS_TOKEN=\n" in content
        assert "glpat-" not in content, ".env.example must not contain a token-looking placeholder"
