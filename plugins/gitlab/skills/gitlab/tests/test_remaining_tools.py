"""Eval tests for pipeline, milestone, wiki, label, namespace, user, commit, iteration, and attachment operations."""
import json
import os
import sys
import pytest
from unittest.mock import patch, mock_open

SCRIPTS_DIR = os.path.join(os.path.dirname(__file__), '..', 'scripts')
sys.path.insert(0, SCRIPTS_DIR)


def _reload():
    import importlib, gitlab_cli
    from functools import partial
    importlib.reload(gitlab_cli)
    runtime = gitlab_cli.resolve_runtime_config()
    gitlab_cli.request = partial(gitlab_cli.request, runtime=runtime)
    return gitlab_cli


# ── Pipelines ──────────────────────────────────────────────

class TestListPipelines:
    def test_list(self, mock_response):
        cli = _reload()
        resp = mock_response(json_body=[{"id": 1, "status": "success"}])
        with patch("requests.request", return_value=resp) as req:
            with pytest.raises(SystemExit):
                cli.request("list_pipelines", {"project_id": "42"})
            assert "/pipelines" in req.call_args[0][1]


class TestGetPipeline:
    def test_get(self, mock_response):
        cli = _reload()
        resp = mock_response(json_body={"id": 10, "status": "running"})
        with patch("requests.request", return_value=resp) as req:
            with pytest.raises(SystemExit):
                cli.request("get_pipeline", {"project_id": "42", "pipeline_id": "10"})
            assert "/pipelines/10" in req.call_args[0][1]


class TestListPipelineJobs:
    def test_list(self, mock_response):
        cli = _reload()
        resp = mock_response(json_body=[{"id": 100}])
        with patch("requests.request", return_value=resp) as req:
            with pytest.raises(SystemExit):
                cli.request("list_pipeline_jobs", {"project_id": "42", "pipeline_id": "10"})
            assert "/pipelines/10/jobs" in req.call_args[0][1]


class TestListPipelineTriggerJobs:
    def test_list(self, mock_response):
        cli = _reload()
        resp = mock_response(json_body=[])
        with patch("requests.request", return_value=resp) as req:
            with pytest.raises(SystemExit):
                cli.request("list_pipeline_trigger_jobs", {"project_id": "42", "pipeline_id": "10"})
            assert "/bridges" in req.call_args[0][1]


class TestGetPipelineJob:
    def test_get(self, mock_response):
        cli = _reload()
        resp = mock_response(json_body={"id": 100, "status": "success"})
        with patch("requests.request", return_value=resp) as req:
            with pytest.raises(SystemExit):
                cli.request("get_pipeline_job", {"project_id": "42", "job_id": "100"})
            assert "/jobs/100" in req.call_args[0][1]


class TestGetPipelineJobOutput:
    def test_get(self, mock_response):
        cli = _reload()
        resp = mock_response(json_body={"raw": "log output"})
        with patch("requests.request", return_value=resp) as req:
            with pytest.raises(SystemExit):
                cli.request("get_pipeline_job_output", {"project_id": "42", "job_id": "100"})
            assert "/jobs/100/trace" in req.call_args[0][1]


class TestCreatePipeline:
    def test_create(self, mock_response):
        cli = _reload()
        resp = mock_response(201, json_body={"id": 50})
        with patch("requests.request", return_value=resp) as req:
            with pytest.raises(SystemExit):
                cli.request("create_pipeline", {"project_id": "42", "ref": "main"})
            assert req.call_args[0][0] == "POST"
            assert "/pipeline" in req.call_args[0][1]


class TestRetryPipeline:
    def test_retry(self, mock_response):
        cli = _reload()
        resp = mock_response(json_body={"id": 10})
        with patch("requests.request", return_value=resp) as req:
            with pytest.raises(SystemExit):
                cli.request("retry_pipeline", {"project_id": "42", "pipeline_id": "10"})
            assert req.call_args[0][0] == "POST"
            assert "/retry" in req.call_args[0][1]


class TestCancelPipeline:
    def test_cancel(self, mock_response):
        cli = _reload()
        resp = mock_response(json_body={"id": 10})
        with patch("requests.request", return_value=resp) as req:
            with pytest.raises(SystemExit):
                cli.request("cancel_pipeline", {"project_id": "42", "pipeline_id": "10"})
            assert req.call_args[0][0] == "POST"
            assert "/cancel" in req.call_args[0][1]


# ── Milestones ─────────────────────────────────────────────

class TestListMilestones:
    def test_list(self, mock_response):
        cli = _reload()
        resp = mock_response(json_body=[{"id": 1, "title": "v1"}])
        with patch("requests.request", return_value=resp) as req:
            with pytest.raises(SystemExit):
                cli.request("list_milestones", {"project_id": "42"})
            assert "/milestones" in req.call_args[0][1]


class TestGetMilestone:
    def test_get(self, mock_response):
        cli = _reload()
        resp = mock_response(json_body={"id": 1})
        with patch("requests.request", return_value=resp) as req:
            with pytest.raises(SystemExit):
                cli.request("get_milestone", {"project_id": "42", "milestone_id": "1"})
            assert "/milestones/1" in req.call_args[0][1]


class TestCreateMilestone:
    def test_create(self, mock_response):
        cli = _reload()
        resp = mock_response(201, json_body={"id": 2})
        with patch("requests.request", return_value=resp) as req:
            with pytest.raises(SystemExit):
                cli.request("create_milestone", {"project_id": "42", "title": "v2"})
            assert req.call_args[0][0] == "POST"


class TestEditMilestone:
    def test_edit(self, mock_response):
        cli = _reload()
        resp = mock_response(json_body={"id": 1})
        with patch("requests.request", return_value=resp) as req:
            with pytest.raises(SystemExit):
                cli.request("edit_milestone", {"project_id": "42", "milestone_id": "1", "title": "v1.1"})
            assert req.call_args[0][0] == "PUT"


class TestDeleteMilestone:
    def test_delete(self, mock_response):
        cli = _reload()
        resp = mock_response(204, text="")
        with patch("requests.request", return_value=resp) as req:
            with pytest.raises(SystemExit):
                cli.request("delete_milestone", {"project_id": "42", "milestone_id": "1"})
            assert req.call_args[0][0] == "DELETE"


class TestGetMilestoneIssue:
    def test_get(self, mock_response):
        cli = _reload()
        resp = mock_response(json_body=[{"iid": 1}])
        with patch("requests.request", return_value=resp) as req:
            with pytest.raises(SystemExit):
                cli.request("get_milestone_issue", {"project_id": "42", "milestone_id": "1"})
            assert "/milestones/1/issues" in req.call_args[0][1]


class TestGetMilestoneMergeRequests:
    def test_get(self, mock_response):
        cli = _reload()
        resp = mock_response(json_body=[])
        with patch("requests.request", return_value=resp) as req:
            with pytest.raises(SystemExit):
                cli.request("get_milestone_merge_requests", {"project_id": "42", "milestone_id": "1"})
            assert "/merge_requests" in req.call_args[0][1]


class TestPromoteMilestone:
    def test_promote(self, mock_response):
        cli = _reload()
        resp = mock_response(json_body={})
        with patch("requests.request", return_value=resp) as req:
            with pytest.raises(SystemExit):
                cli.request("promote_milestone", {"project_id": "42", "milestone_id": "1"})
            assert req.call_args[0][0] == "POST"
            assert "/promote" in req.call_args[0][1]


class TestGetMilestoneBurndownEvents:
    def test_get(self, mock_response):
        cli = _reload()
        resp = mock_response(json_body=[])
        with patch("requests.request", return_value=resp) as req:
            with pytest.raises(SystemExit):
                cli.request("get_milestone_burndown_events", {"project_id": "42", "milestone_id": "1"})
            assert "/burndown_events" in req.call_args[0][1]


# ── Labels ─────────────────────────────────────────────────

class TestListLabels:
    def test_list(self, mock_response):
        cli = _reload()
        resp = mock_response(json_body=[{"id": 1, "name": "bug"}])
        with patch("requests.request", return_value=resp) as req:
            with pytest.raises(SystemExit):
                cli.request("list_labels", {"project_id": "42"})
            assert "/labels" in req.call_args[0][1]


class TestGetLabel:
    def test_get(self, mock_response):
        cli = _reload()
        resp = mock_response(json_body={"id": 1})
        with patch("requests.request", return_value=resp) as req:
            with pytest.raises(SystemExit):
                cli.request("get_label", {"project_id": "42", "label_id": "1"})
            assert "/labels/1" in req.call_args[0][1]


class TestCreateLabel:
    def test_create(self, mock_response):
        cli = _reload()
        resp = mock_response(201, json_body={"id": 2})
        with patch("requests.request", return_value=resp) as req:
            with pytest.raises(SystemExit):
                cli.request("create_label", {"project_id": "42", "name": "feature", "color": "#00ff00"})
            assert req.call_args[0][0] == "POST"


class TestUpdateLabel:
    def test_update(self, mock_response):
        cli = _reload()
        resp = mock_response(json_body={"id": 1})
        with patch("requests.request", return_value=resp) as req:
            with pytest.raises(SystemExit):
                cli.request("update_label", {"project_id": "42", "label_id": "1", "color": "#ff0000"})
            assert req.call_args[0][0] == "PUT"


class TestDeleteLabel:
    def test_delete(self, mock_response):
        cli = _reload()
        resp = mock_response(204, text="")
        with patch("requests.request", return_value=resp) as req:
            with pytest.raises(SystemExit):
                cli.request("delete_label", {"project_id": "42", "label_id": "1"})
            assert req.call_args[0][0] == "DELETE"


# ── Wiki ───────────────────────────────────────────────────

class TestListWikiPages:
    def test_list(self, mock_response):
        cli = _reload()
        resp = mock_response(json_body=[{"slug": "home"}])
        with patch("requests.request", return_value=resp) as req:
            with pytest.raises(SystemExit):
                cli.request("list_wiki_pages", {"project_id": "42"})
            assert "/wikis" in req.call_args[0][1]


class TestGetWikiPage:
    def test_get(self, mock_response):
        cli = _reload()
        resp = mock_response(json_body={"slug": "home", "content": "# Home"})
        with patch("requests.request", return_value=resp) as req:
            with pytest.raises(SystemExit):
                cli.request("get_wiki_page", {"project_id": "42", "slug": "home"})
            assert "/wikis/home" in req.call_args[0][1]


class TestCreateWikiPage:
    def test_create(self, mock_response):
        cli = _reload()
        resp = mock_response(201, json_body={"slug": "new-page"})
        with patch("requests.request", return_value=resp) as req:
            with pytest.raises(SystemExit):
                cli.request("create_wiki_page", {"project_id": "42", "title": "New", "content": "body"})
            assert req.call_args[0][0] == "POST"


class TestUpdateWikiPage:
    def test_update(self, mock_response):
        cli = _reload()
        resp = mock_response(json_body={"slug": "home"})
        with patch("requests.request", return_value=resp) as req:
            with pytest.raises(SystemExit):
                cli.request("update_wiki_page", {"project_id": "42", "slug": "home", "content": "updated"})
            assert req.call_args[0][0] == "PUT"


class TestDeleteWikiPage:
    def test_delete(self, mock_response):
        cli = _reload()
        resp = mock_response(204, text="")
        with patch("requests.request", return_value=resp) as req:
            with pytest.raises(SystemExit):
                cli.request("delete_wiki_page", {"project_id": "42", "slug": "home"})
            assert req.call_args[0][0] == "DELETE"


# ── Namespaces ─────────────────────────────────────────────

class TestListNamespaces:
    def test_list(self, mock_response):
        cli = _reload()
        resp = mock_response(json_body=[{"id": 1}])
        with patch("requests.request", return_value=resp) as req:
            with pytest.raises(SystemExit):
                cli.request("list_namespaces", {})
            assert "/namespaces" in req.call_args[0][1]


class TestGetNamespace:
    def test_get(self, mock_response):
        cli = _reload()
        resp = mock_response(json_body={"id": 1})
        with patch("requests.request", return_value=resp) as req:
            with pytest.raises(SystemExit):
                cli.request("get_namespace", {"namespace_id": "1"})
            assert "/namespaces/1" in req.call_args[0][1]


class TestVerifyNamespace:
    def test_verify(self, mock_response):
        cli = _reload()
        resp = mock_response(json_body={"id": 1})
        with patch("requests.request", return_value=resp) as req:
            with pytest.raises(SystemExit):
                cli.request("verify_namespace", {"namespace_id": "1"})
            assert "/namespaces/1" in req.call_args[0][1]


# ── Users ──────────────────────────────────────────────────

class TestGetUsers:
    def test_get(self, mock_response):
        cli = _reload()
        resp = mock_response(json_body=[{"id": 1, "username": "admin"}])
        with patch("requests.request", return_value=resp) as req:
            with pytest.raises(SystemExit):
                cli.request("get_users", {"search": "admin"})
            assert "/users" in req.call_args[0][1]


# ── Commits ────────────────────────────────────────────────

class TestListCommits:
    def test_list(self, mock_response):
        cli = _reload()
        resp = mock_response(json_body=[{"id": "abc123"}])
        with patch("requests.request", return_value=resp) as req:
            with pytest.raises(SystemExit):
                cli.request("list_commits", {"project_id": "42"})
            assert "/commits" in req.call_args[0][1]


class TestGetCommit:
    def test_get(self, mock_response):
        cli = _reload()
        resp = mock_response(json_body={"id": "abc123"})
        with patch("requests.request", return_value=resp) as req:
            with pytest.raises(SystemExit):
                cli.request("get_commit", {"project_id": "42", "commit_sha": "abc123"})
            assert "/commits/abc123" in req.call_args[0][1]


class TestGetCommitDiff:
    def test_get(self, mock_response):
        cli = _reload()
        resp = mock_response(json_body=[{"diff": "..."}])
        with patch("requests.request", return_value=resp) as req:
            with pytest.raises(SystemExit):
                cli.request("get_commit_diff", {"project_id": "42", "commit_sha": "abc123"})
            assert "/commits/abc123/diff" in req.call_args[0][1]


# ── Iterations ─────────────────────────────────────────────

class TestListGroupIterations:
    def test_list(self, mock_response):
        cli = _reload()
        resp = mock_response(json_body=[{"id": 1}])
        with patch("requests.request", return_value=resp) as req:
            with pytest.raises(SystemExit):
                cli.request("list_group_iterations", {"group_id": "7"})
            assert "/groups/7/iterations" in req.call_args[0][1]


# ── Upload / Download ─────────────────────────────────────

class TestUploadMarkdown:
    def test_upload(self, mock_response, tmp_path):
        cli = _reload()
        test_file = tmp_path / "image.png"
        test_file.write_bytes(b"\x89PNG")
        resp = mock_response(201, json_body={"markdown": "![img](url)"})
        with patch("requests.request", return_value=resp) as req:
            with pytest.raises(SystemExit):
                cli.request("upload_markdown", {"project_id": "42", "upload_file": str(test_file)})
            assert req.call_args[0][0] == "POST"
            assert "/uploads" in req.call_args[0][1]
            assert req.call_args[1]["files"] is not None

    def test_upload_missing_file(self):
        cli = _reload()
        with pytest.raises(SystemExit):
            cli.request("upload_markdown", {"project_id": "42", "upload_file": "/nonexistent/file.png"})


class TestDownloadAttachment:
    def test_download(self, mock_response):
        cli = _reload()
        resp = mock_response(json_body={}, content_type="text/plain")
        resp.text = "file contents"
        resp.content = b"file contents"
        with patch("requests.get", return_value=resp):
            with pytest.raises(SystemExit):
                cli.request("download_attachment", {
                    "project_id": "42", "secret": "s3cret", "filename": "file.txt"
                })


# ── Error Handling ─────────────────────────────────────────

class TestErrorResponses:
    def test_404_error(self, mock_response):
        cli = _reload()
        resp = mock_response(404, json_body={"message": "404 Not Found"})
        with patch("requests.request", return_value=resp):
            with pytest.raises(SystemExit) as exc_info:
                cli.request("get_project", {"project_id": "99999"})
            assert exc_info.value.code == 1

    def test_401_unauthorized(self, mock_response):
        cli = _reload()
        resp = mock_response(401, json_body={"message": "401 Unauthorized"})
        with patch("requests.request", return_value=resp):
            with pytest.raises(SystemExit) as exc_info:
                cli.request("list_projects", {})
            assert exc_info.value.code == 1

    def test_non_json_response(self, mock_response):
        cli = _reload()
        resp = mock_response(200, text="plain text", content_type="text/plain")
        resp.json.side_effect = ValueError("No JSON")
        with patch("requests.request", return_value=resp):
            with pytest.raises(SystemExit):
                cli.request("list_projects", {})


# ── Body File ──────────────────────────────────────────────

class TestBodyFile:
    def test_body_file_used(self, mock_response, tmp_path):
        cli = _reload()
        body_file = tmp_path / "payload.json"
        body_file.write_text(json.dumps({"title": "from file", "description": "body"}))
        resp = mock_response(201, json_body={"iid": 1})
        with patch("requests.request", return_value=resp) as req:
            with pytest.raises(SystemExit):
                cli.request("create_issue", {"project_id": "42"}, raw_body={"title": "from file", "description": "body"})
            assert req.call_args[1]["json"] == {"title": "from file", "description": "body"}
