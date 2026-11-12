"""Eval tests for issue operations."""
import json
import os
import sys
import pytest
from unittest.mock import patch

SCRIPTS_DIR = os.path.join(os.path.dirname(__file__), '..', 'scripts')
sys.path.insert(0, SCRIPTS_DIR)


def _reload():
    import importlib, gitlab_cli
    from functools import partial
    importlib.reload(gitlab_cli)
    runtime = gitlab_cli.resolve_runtime_config()
    gitlab_cli.request = partial(gitlab_cli.request, runtime=runtime)
    return gitlab_cli


class TestListIssues:
    def test_list(self, mock_response):
        cli = _reload()
        resp = mock_response(json_body=[{"iid": 1, "title": "Bug"}])
        with patch("requests.request", return_value=resp) as req:
            with pytest.raises(SystemExit):
                cli.request("list_issues", {"scope": "all"})
            assert req.call_args[0][0] == "GET"
            assert "/issues" in req.call_args[0][1]


class TestMyIssues:
    def test_defaults(self, mock_response):
        cli = _reload()
        resp = mock_response(json_body=[])
        with patch("requests.request", return_value=resp) as req:
            with pytest.raises(SystemExit):
                cli.request("my_issues", {})
            params = req.call_args[1]["params"]
            assert params["scope"] == "assigned_to_me"
            assert params["state"] == "opened"


class TestGetIssue:
    def test_get(self, mock_response):
        cli = _reload()
        resp = mock_response(json_body={"iid": 5, "title": "Fix"})
        with patch("requests.request", return_value=resp) as req:
            with pytest.raises(SystemExit):
                cli.request("get_issue", {"project_id": "42", "issue_iid": "5"})
            assert "/projects/42/issues/5" in req.call_args[0][1]


class TestCreateIssue:
    def test_create(self, mock_response):
        cli = _reload()
        resp = mock_response(201, json_body={"iid": 10})
        with patch("requests.request", return_value=resp) as req:
            with pytest.raises(SystemExit):
                cli.request("create_issue", {"project_id": "42", "title": "New bug"})
            assert req.call_args[0][0] == "POST"
            assert "/projects/42/issues" in req.call_args[0][1]


class TestUpdateIssue:
    def test_update(self, mock_response):
        cli = _reload()
        resp = mock_response(json_body={"iid": 5})
        with patch("requests.request", return_value=resp) as req:
            with pytest.raises(SystemExit):
                cli.request("update_issue", {"project_id": "42", "issue_iid": "5", "state_event": "close"})
            assert req.call_args[0][0] == "PUT"


class TestDeleteIssue:
    def test_delete(self, mock_response):
        cli = _reload()
        resp = mock_response(204, text="")
        with patch("requests.request", return_value=resp) as req:
            with pytest.raises(SystemExit):
                cli.request("delete_issue", {"project_id": "42", "issue_iid": "5"})
            assert req.call_args[0][0] == "DELETE"


class TestIssueDiscussions:
    def test_list(self, mock_response):
        cli = _reload()
        resp = mock_response(json_body=[{"id": "disc1"}])
        with patch("requests.request", return_value=resp) as req:
            with pytest.raises(SystemExit):
                cli.request("list_issue_discussions", {"project_id": "42", "issue_iid": "5"})
            assert "/issues/5/discussions" in req.call_args[0][1]


class TestIssueNotes:
    def test_create(self, mock_response):
        cli = _reload()
        resp = mock_response(201, json_body={"id": 1})
        with patch("requests.request", return_value=resp) as req:
            with pytest.raises(SystemExit):
                cli.request("create_issue_note", {
                    "project_id": "42", "issue_iid": "5",
                    "discussion_id": "disc1", "body": "comment"
                })
            assert req.call_args[0][0] == "POST"

    def test_update(self, mock_response):
        cli = _reload()
        resp = mock_response(json_body={"id": 1})
        with patch("requests.request", return_value=resp) as req:
            with pytest.raises(SystemExit):
                cli.request("update_issue_note", {
                    "project_id": "42", "issue_iid": "5",
                    "discussion_id": "disc1", "note_id": "1", "body": "updated"
                })
            assert req.call_args[0][0] == "PUT"


class TestIssueLinks:
    def test_list(self, mock_response):
        cli = _reload()
        resp = mock_response(json_body=[])
        with patch("requests.request", return_value=resp) as req:
            with pytest.raises(SystemExit):
                cli.request("list_issue_links", {"project_id": "42", "issue_iid": "5"})
            assert "/issues/5/links" in req.call_args[0][1]

    def test_get(self, mock_response):
        cli = _reload()
        resp = mock_response(json_body={"id": 1})
        with patch("requests.request", return_value=resp) as req:
            with pytest.raises(SystemExit):
                cli.request("get_issue_link", {"project_id": "42", "issue_iid": "5", "issue_link_id": "1"})
            assert "/links/1" in req.call_args[0][1]

    def test_create(self, mock_response):
        cli = _reload()
        resp = mock_response(201, json_body={"id": 2})
        with patch("requests.request", return_value=resp) as req:
            with pytest.raises(SystemExit):
                cli.request("create_issue_link", {
                    "project_id": "42", "issue_iid": "5",
                    "target_project_id": "43", "target_issue_iid": "10"
                })
            assert req.call_args[0][0] == "POST"

    def test_delete(self, mock_response):
        cli = _reload()
        resp = mock_response(204, text="")
        with patch("requests.request", return_value=resp) as req:
            with pytest.raises(SystemExit):
                cli.request("delete_issue_link", {"project_id": "42", "issue_iid": "5", "issue_link_id": "1"})
            assert req.call_args[0][0] == "DELETE"
