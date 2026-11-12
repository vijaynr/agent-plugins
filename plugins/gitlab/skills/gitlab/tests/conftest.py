"""Shared fixtures for gitlab_cli.py eval tests."""
import json
import os
import sys
import pytest
from unittest.mock import patch, MagicMock

# Ensure the scripts directory is importable
SKILL_DIR = os.path.join(os.path.dirname(__file__), '..')
SCRIPTS_DIR = os.path.join(SKILL_DIR, 'scripts')
sys.path.insert(0, SCRIPTS_DIR)


@pytest.fixture(autouse=True)
def gitlab_env(monkeypatch):
    """Set required env vars for every test."""
    monkeypatch.setenv("GITLAB_PERSONAL_ACCESS_TOKEN", "glpat-test-token-1234567890")
    monkeypatch.setenv("GITLAB_API_URL", "https://gitlab.example.com/api/v4")
    monkeypatch.setenv("GITLAB_PROJECT_ID", "42")
    monkeypatch.setenv("GITLAB_ALLOWED_PROJECT_IDS", "")
    monkeypatch.setenv("GITLAB_READ_ONLY_MODE", "false")
    monkeypatch.setenv("GITLAB_TIMEOUT", "10")


@pytest.fixture
def mock_response():
    """Factory for mock requests.Response objects."""
    def _make(status_code=200, json_body=None, text="", content_type="application/json"):
        resp = MagicMock()
        resp.ok = 200 <= status_code < 300
        resp.status_code = status_code
        resp.headers = {"content-type": content_type}
        resp.text = text or json.dumps(json_body or {})
        resp.json.return_value = json_body if json_body is not None else {}
        resp.content = (text or json.dumps(json_body or {})).encode()
        return resp
    return _make


@pytest.fixture
def skill_dir():
    """Return the absolute path to the skill root directory."""
    return os.path.abspath(SKILL_DIR)
