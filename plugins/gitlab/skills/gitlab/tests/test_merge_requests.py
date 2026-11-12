"""Eval tests for merge request operations."""
import json
import os
import sys
import pytest
from unittest.mock import MagicMock, patch

SCRIPTS_DIR = os.path.join(os.path.dirname(__file__), '..', 'scripts')
sys.path.insert(0, SCRIPTS_DIR)


def _reload():
    import importlib, gitlab_cli
    from functools import partial
    importlib.reload(gitlab_cli)
    runtime = gitlab_cli.resolve_runtime_config()
    gitlab_cli.request = partial(gitlab_cli.request, runtime=runtime)
    gitlab_cli.get_mr_code_quality_attachment_report = partial(
        gitlab_cli.get_mr_code_quality_attachment_report, runtime=runtime
    )
    return gitlab_cli


class TestListMergeRequests:
    def test_list(self, mock_response):
        cli = _reload()
        resp = mock_response(json_body=[{"iid": 1}])
        with patch("requests.request", return_value=resp) as req:
            with pytest.raises(SystemExit):
                cli.request("list_merge_requests", {"project_id": "42"})
            assert "/merge_requests" in req.call_args[0][1]


class TestGetMergeRequest:
    def test_get(self, mock_response):
        cli = _reload()
        resp = mock_response(json_body={"iid": 5, "title": "MR"})
        with patch("requests.request", return_value=resp) as req:
            with pytest.raises(SystemExit):
                cli.request("get_merge_request", {"project_id": "42", "merge_request_iid": "5"})
            assert "/merge_requests/5" in req.call_args[0][1]

    def test_camel_alias(self, mock_response):
        cli = _reload()
        resp = mock_response(json_body={"iid": 5})
        with patch("requests.request", return_value=resp) as req:
            with pytest.raises(SystemExit):
                cli.request("get_merge_request", {"projectId": "42", "mergeRequestIid": "5"})
            assert "/merge_requests/5" in req.call_args[0][1]


class TestGetMergeRequestDiffs:
    def test_get(self, mock_response):
        cli = _reload()
        resp = mock_response(json_body={"changes": []})
        with patch("requests.request", return_value=resp) as req:
            with pytest.raises(SystemExit):
                cli.request("get_merge_request_diffs", {"project_id": "42", "merge_request_iid": "5"})
            assert "/changes" in req.call_args[0][1]


class TestListMergeRequestDiffs:
    def test_list(self, mock_response):
        cli = _reload()
        resp = mock_response(json_body=[{"id": 1}])
        with patch("requests.request", return_value=resp) as req:
            with pytest.raises(SystemExit):
                cli.request("list_merge_request_diffs", {"project_id": "42", "merge_request_iid": "5"})
            assert "/versions" in req.call_args[0][1]


class TestCreateMergeRequest:
    def test_create(self, mock_response):
        cli = _reload()
        resp = mock_response(201, json_body={"iid": 10})
        with patch("requests.request", return_value=resp) as req:
            with pytest.raises(SystemExit):
                cli.request("create_merge_request", {
                    "project_id": "42", "source_branch": "feature",
                    "target_branch": "main", "title": "New MR"
                })
            assert req.call_args[0][0] == "POST"


class TestUpdateMergeRequest:
    def test_update(self, mock_response):
        cli = _reload()
        resp = mock_response(json_body={"iid": 5})
        with patch("requests.request", return_value=resp) as req:
            with pytest.raises(SystemExit):
                cli.request("update_merge_request", {
                    "project_id": "42", "merge_request_iid": "5", "title": "Updated"
                })
            assert req.call_args[0][0] == "PUT"


class TestMergeMergeRequest:
    def test_merge(self, mock_response):
        cli = _reload()
        resp = mock_response(json_body={"state": "merged"})
        with patch("requests.request", return_value=resp) as req:
            with pytest.raises(SystemExit):
                cli.request("merge_merge_request", {"project_id": "42", "merge_request_iid": "5"})
            assert req.call_args[0][0] == "PUT"
            assert "/merge" in req.call_args[0][1]


class TestMRDiscussions:
    def test_list(self, mock_response):
        cli = _reload()
        resp = mock_response(json_body=[{"id": "d1"}])
        with patch("requests.request", return_value=resp) as req:
            with pytest.raises(SystemExit):
                cli.request("mr_discussions", {"project_id": "42", "merge_request_iid": "5"})
            assert "/discussions" in req.call_args[0][1]


class TestCreateMRThread:
    def test_create(self, mock_response):
        cli = _reload()
        resp = mock_response(201, json_body={"id": "d2"})
        with patch("requests.request", return_value=resp) as req:
            with pytest.raises(SystemExit):
                cli.request("create_merge_request_thread", {
                    "project_id": "42", "merge_request_iid": "5", "body": "thread"
                })
            assert req.call_args[0][0] == "POST"


class TestMRNotes:
    def test_create(self, mock_response):
        cli = _reload()
        resp = mock_response(201, json_body={"id": 1})
        with patch("requests.request", return_value=resp) as req:
            with pytest.raises(SystemExit):
                cli.request("create_merge_request_note", {
                    "project_id": "42", "merge_request_iid": "5",
                    "discussion_id": "d1", "body": "reply"
                })
            assert req.call_args[0][0] == "POST"

    def test_update(self, mock_response):
        cli = _reload()
        resp = mock_response(json_body={"id": 1})
        with patch("requests.request", return_value=resp) as req:
            with pytest.raises(SystemExit):
                cli.request("update_merge_request_note", {
                    "project_id": "42", "merge_request_iid": "5",
                    "discussion_id": "d1", "note_id": "1", "body": "edited"
                })
            assert req.call_args[0][0] == "PUT"


class TestCreateNote:
    def test_generic_note(self, mock_response):
        cli = _reload()
        resp = mock_response(201, json_body={"id": 1})
        with patch("requests.request", return_value=resp) as req:
            with pytest.raises(SystemExit):
                cli.request("create_note", {
                    "project_id": "42", "note_target": "issues",
                    "target_id": "5", "body": "comment"
                })
            assert req.call_args[0][0] == "POST"
            assert "/issues/5/notes" in req.call_args[0][1]


class TestMRCodeQualityAttachmentReport:
    def test_finds_report_on_later_discussion_page(self, mock_response, capsys):
        cli = _reload()
        page1 = mock_response(json_body=[{"id": "d1", "notes": [{"id": 1, "body": "No report here"}]}])
        page1.headers = {"content-type": "application/json", "X-Next-Page": "2"}
        page2 = mock_response(json_body=[{
            "id": "d2",
            "notes": [{
                "id": 2,
                "created_at": "2026-07-07T10:00:00Z",
                "body": "Code quality report: [report](/uploads/0123456789abcdef0123456789abcdef/gl-code-quality-report.json)",
            }],
        }])
        page2.headers = {"content-type": "application/json", "X-Next-Page": ""}
        report = mock_response(json_body=[{"description": "issue"}])

        with patch("requests.get", side_effect=[page1, page2, report]) as req:
            with pytest.raises(SystemExit) as exc:
                cli.get_mr_code_quality_attachment_report({"project_id": "42", "merge_request_iid": "5"})

        assert exc.value.code == 0
        output = json.loads(capsys.readouterr().out)
        assert output["ok"] is True
        assert output["candidate_count"] == 1
        assert output["report"] == [{"description": "issue"}]
        assert req.call_count == 3
        assert req.call_args_list[0].kwargs["params"] == {"per_page": 100, "page": 1}
        assert req.call_args_list[1].kwargs["params"] == {"per_page": 100, "page": "2"}

    def test_invalid_filename_regex_returns_json_error(self, capsys):
        cli = _reload()

        with pytest.raises(SystemExit) as exc:
            cli.get_mr_code_quality_attachment_report({
                "project_id": "42",
                "merge_request_iid": "5",
                "filename_regex": "[",
            })

        assert exc.value.code == 1
        output = json.loads(capsys.readouterr().out)
        assert output["ok"] is False
        assert output["error"] == "Invalid filename_regex"
        assert "unterminated character set" in output["details"]

    def test_unexpected_discussions_shape_returns_json_error(self, mock_response, capsys):
        cli = _reload()
        resp = mock_response(json_body={"message": "unexpected object"})
        resp.headers = {"content-type": "application/json", "X-Next-Page": ""}

        with patch("requests.get", return_value=resp):
            with pytest.raises(SystemExit) as exc:
                cli.get_mr_code_quality_attachment_report({"project_id": "42", "merge_request_iid": "5"})

        assert exc.value.code == 1
        output = json.loads(capsys.readouterr().out)
        assert output["ok"] is False
        assert output["error"] == "Unexpected discussions response shape"
        assert output["details"] == "Expected a JSON array of discussions"

    def test_oversized_attachment_returns_json_error(self, mock_response, capsys):
        cli = _reload()
        discussions = mock_response(json_body=[{
            "id": "d1",
            "notes": [{
                "id": 1,
                "created_at": "2026-07-07T10:00:00Z",
                "body": "Code quality report: [report](/uploads/0123456789abcdef0123456789abcdef/gl-code-quality-report.json)",
            }],
        }])
        discussions.headers = {"content-type": "application/json", "X-Next-Page": ""}
        report = mock_response(json_body=[])
        report.headers = {"content-type": "application/json", "content-length": "6"}

        with patch("requests.get", side_effect=[discussions, report]):
            with pytest.raises(SystemExit) as exc:
                cli.get_mr_code_quality_attachment_report({
                    "project_id": "42",
                    "merge_request_iid": "5",
                    "max_report_bytes": "5",
                })

        assert exc.value.code == 1
        output = json.loads(capsys.readouterr().out)
        assert output["ok"] is False
        assert output["error"] == "Code-quality attachment exceeds max_report_bytes"
        assert output["content_length"] == 6
        assert output["max_report_bytes"] == 5
        assert "report" not in output

    def test_invalid_max_report_bytes_returns_json_error(self, mock_response, capsys):
        cli = _reload()
        discussions = mock_response(json_body=[{
            "id": "d1",
            "notes": [{
                "id": 1,
                "created_at": "2026-07-07T10:00:00Z",
                "body": "Code quality report: [report](/uploads/0123456789abcdef0123456789abcdef/gl-code-quality-report.json)",
            }],
        }])
        discussions.headers = {"content-type": "application/json", "X-Next-Page": ""}

        with patch("requests.get", return_value=discussions):
            with pytest.raises(SystemExit) as exc:
                cli.get_mr_code_quality_attachment_report({
                    "project_id": "42",
                    "merge_request_iid": "5",
                    "max_report_bytes": "not-a-number",
                })

        assert exc.value.code == 1
        output = json.loads(capsys.readouterr().out)
        assert output["ok"] is False
        assert output["error"] == "Invalid max_report_bytes"
        assert output["details"] == "Expected a positive integer byte limit"

    def test_extract_upload_links_omits_markdown_parentheses(self):
        cli = _reload()

        links = cli._extract_upload_links(
            "Code quality report: [report](/uploads/0123456789abcdef0123456789abcdef/gl-code-quality-report.json)"
        )

        assert links == [{
            "url": "/uploads/0123456789abcdef0123456789abcdef/gl-code-quality-report.json",
            "secret": "0123456789abcdef0123456789abcdef",
            "filename": "gl-code-quality-report.json",
        }]


class TestDraftNotes:
    def test_list(self, mock_response):
        cli = _reload()
        resp = mock_response(json_body=[{"id": 1}])
        with patch("requests.request", return_value=resp) as req:
            with pytest.raises(SystemExit):
                cli.request("list_draft_notes", {"project_id": "42", "merge_request_iid": "5"})
            assert "/draft_notes" in req.call_args[0][1]

    def test_get(self, mock_response):
        cli = _reload()
        resp = mock_response(json_body={"id": 1})
        with patch("requests.request", return_value=resp) as req:
            with pytest.raises(SystemExit):
                cli.request("get_draft_note", {"project_id": "42", "merge_request_iid": "5", "note_id": "1"})
            assert "/draft_notes/1" in req.call_args[0][1]

    def test_create(self, mock_response):
        cli = _reload()
        resp = mock_response(201, json_body={"id": 2})
        with patch("requests.request", return_value=resp) as req:
            with pytest.raises(SystemExit):
                cli.request("create_draft_note", {
                    "project_id": "42", "merge_request_iid": "5", "note": "draft"
                })
            assert req.call_args[0][0] == "POST"

    def test_update(self, mock_response):
        cli = _reload()
        resp = mock_response(json_body={"id": 1})
        with patch("requests.request", return_value=resp) as req:
            with pytest.raises(SystemExit):
                cli.request("update_draft_note", {
                    "project_id": "42", "merge_request_iid": "5",
                    "note_id": "1", "note": "updated"
                })
            assert req.call_args[0][0] == "PUT"

    def test_delete(self, mock_response):
        cli = _reload()
        resp = mock_response(204, text="")
        with patch("requests.request", return_value=resp) as req:
            with pytest.raises(SystemExit):
                cli.request("delete_draft_note", {
                    "project_id": "42", "merge_request_iid": "5", "note_id": "1"
                })
            assert req.call_args[0][0] == "DELETE"

    def test_publish(self, mock_response):
        cli = _reload()
        resp = mock_response(json_body={})
        with patch("requests.request", return_value=resp) as req:
            with pytest.raises(SystemExit):
                cli.request("publish_draft_note", {
                    "project_id": "42", "merge_request_iid": "5", "note_id": "1"
                })
            assert req.call_args[0][0] == "POST"
            assert "/publish" in req.call_args[0][1]

    def test_bulk_publish(self, mock_response):
        cli = _reload()
        resp = mock_response(json_body={})
        with patch("requests.request", return_value=resp) as req:
            with pytest.raises(SystemExit):
                cli.request("bulk_publish_draft_notes", {
                    "project_id": "42", "merge_request_iid": "5"
                })
            assert "/bulk_publish" in req.call_args[0][1]
