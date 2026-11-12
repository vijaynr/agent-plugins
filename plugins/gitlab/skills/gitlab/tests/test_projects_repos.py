"""Eval tests for project, repository, and file operations."""
import json
import os
import sys
import pytest
from unittest.mock import patch, MagicMock

SCRIPTS_DIR = os.path.join(os.path.dirname(__file__), '..', 'scripts')
sys.path.insert(0, SCRIPTS_DIR)


def _reload():
    import importlib, gitlab_cli
    from functools import partial
    importlib.reload(gitlab_cli)
    runtime = gitlab_cli.resolve_runtime_config()
    gitlab_cli.request = partial(gitlab_cli.request, runtime=runtime)
    return gitlab_cli


class TestSearchRepositories:
    def test_search(self, mock_response):
        cli = _reload()
        resp = mock_response(json_body=[{"id": 1, "name": "test-repo"}])
        with patch("requests.request", return_value=resp) as req:
            with pytest.raises(SystemExit):
                cli.request("search_repositories", {"search": "test"})
            args, kwargs = req.call_args
            assert args[0] == "GET"
            assert "/search" in args[1]
            assert kwargs["params"]["scope"] == "projects"


class TestGetProject:
    def test_get(self, mock_response):
        cli = _reload()
        resp = mock_response(json_body={"id": 42, "name": "my-proj"})
        with patch("requests.request", return_value=resp) as req:
            with pytest.raises(SystemExit):
                cli.request("get_project", {"project_id": "42"})
            assert "/projects/42" in req.call_args[0][1]


class TestListProjects:
    def test_list(self, mock_response):
        cli = _reload()
        resp = mock_response(json_body=[{"id": 1}, {"id": 2}])
        with patch("requests.request", return_value=resp) as req:
            with pytest.raises(SystemExit):
                cli.request("list_projects", {})
            assert "/projects" in req.call_args[0][1]


class TestListProjectMembers:
    def test_list(self, mock_response):
        cli = _reload()
        resp = mock_response(json_body=[{"id": 10, "username": "dev"}])
        with patch("requests.request", return_value=resp) as req:
            with pytest.raises(SystemExit):
                cli.request("list_project_members", {"project_id": "42"})
            assert "/projects/42/members/all" in req.call_args[0][1]


class TestListGroupProjects:
    def test_list(self, mock_response):
        cli = _reload()
        resp = mock_response(json_body=[{"id": 5}])
        with patch("requests.request", return_value=resp) as req:
            with pytest.raises(SystemExit):
                cli.request("list_group_projects", {"group_id": "7"})
            assert "/groups/7/projects" in req.call_args[0][1]


class TestCreateRepository:
    def test_create(self, mock_response):
        cli = _reload()
        resp = mock_response(201, json_body={"id": 100, "name": "new"})
        with patch("requests.request", return_value=resp) as req:
            with pytest.raises(SystemExit):
                cli.request("create_repository", {"name": "new", "visibility": "private"})
            assert req.call_args[0][0] == "POST"
            assert "/projects" in req.call_args[0][1]


class TestForkRepository:
    def test_fork(self, mock_response):
        cli = _reload()
        resp = mock_response(201, json_body={"id": 101})
        with patch("requests.request", return_value=resp) as req:
            with pytest.raises(SystemExit):
                cli.request("fork_repository", {"project_id": "42"})
            assert req.call_args[0][0] == "POST"
            assert "/projects/42/fork" in req.call_args[0][1]


class TestCreateBranch:
    def test_create(self, mock_response):
        cli = _reload()
        resp = mock_response(201, json_body={"name": "feature"})
        with patch("requests.request", return_value=resp) as req:
            with pytest.raises(SystemExit):
                cli.request("create_branch", {"project_id": "42", "branch": "feature", "ref": "main"})
            assert req.call_args[0][0] == "POST"
            assert "/repository/branches" in req.call_args[0][1]


class TestGetRepositoryTree:
    def test_tree(self, mock_response):
        cli = _reload()
        resp = mock_response(json_body=[{"name": "src", "type": "tree"}])
        with patch("requests.request", return_value=resp) as req:
            with pytest.raises(SystemExit):
                cli.request("get_repository_tree", {"project_id": "42"})
            assert "/repository/tree" in req.call_args[0][1]


class TestGetFileContents:
    def test_get(self, mock_response):
        cli = _reload()
        resp = mock_response(json_body={"file_name": "README.md", "content": "..."})
        with patch("requests.request", return_value=resp) as req:
            with pytest.raises(SystemExit):
                cli.request("get_file_contents", {"project_id": "42", "file_path": "README.md", "ref": "main"})
            url = req.call_args[0][1]
            assert "/repository/files/" in url
            assert "README.md" in url

    def test_default_ref(self, mock_response):
        cli = _reload()
        resp = mock_response(json_body={"content": "..."})
        with patch("requests.request", return_value=resp) as req:
            with pytest.raises(SystemExit):
                cli.request("get_file_contents", {"project_id": "42", "file_path": "a.py"})
            assert req.call_args[1]["params"]["ref"] == "main"


class TestCreateOrUpdateFile:
    def test_update(self, mock_response):
        cli = _reload()
        resp = mock_response(json_body={"file_path": "test.py"})
        with patch("requests.request", return_value=resp) as req:
            with pytest.raises(SystemExit):
                cli.request("create_or_update_file", {
                    "project_id": "42", "file_path": "test.py",
                    "branch": "main", "content": "print(1)",
                    "commit_message": "add", "update": "true"
                })
            assert req.call_args[0][0] == "PUT"

    def test_create_mode(self, mock_response):
        cli = _reload()
        resp = mock_response(201, json_body={"file_path": "new.py"})
        with patch("requests.request", return_value=resp) as req:
            with pytest.raises(SystemExit):
                cli.request("create_or_update_file", {
                    "project_id": "42", "file_path": "new.py",
                    "branch": "main", "content": "x=1",
                    "commit_message": "new", "update": "false"
                })
            assert req.call_args[0][0] == "POST"


class TestPushFiles:
    def test_push(self, mock_response):
        cli = _reload()
        resp = mock_response(201, json_body={"id": "abc123"})
        with patch("requests.request", return_value=resp) as req:
            with pytest.raises(SystemExit):
                cli.request("push_files", {"project_id": "42", "branch": "main", "commit_message": "push"})
            assert req.call_args[0][0] == "POST"
            assert "/repository/commits" in req.call_args[0][1]


class TestGetBranchDiffs:
    def test_compare(self, mock_response):
        cli = _reload()
        resp = mock_response(json_body={"diffs": []})
        with patch("requests.request", return_value=resp) as req:
            with pytest.raises(SystemExit):
                cli.request("get_branch_diffs", {"project_id": "42", "from": "main", "to": "feature"})
            assert "/repository/compare" in req.call_args[0][1]
