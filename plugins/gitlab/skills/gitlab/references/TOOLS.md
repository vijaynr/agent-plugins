# GitLab CLI — Complete Tool Reference

All tools are invoked via:

```bash
uv run scripts/gitlab_cli.py <tool_name> --param key=value ...
```

---

## Projects & Repositories

| Tool | Method | Description | Key Params |
|------|--------|-------------|------------|
| `search_repositories` | GET | Search GitLab projects | `search` (required) |
| `create_repository` | POST | Create a new project | `name`, `visibility` |
| `get_project` | GET | Get project details | `project_id` |
| `list_projects` | GET | List accessible projects | `search`, `owned`, `membership` |
| `list_project_members` | GET | List all project members | `project_id` |
| `list_group_projects` | GET | List projects in a group | `group_id` |
| `fork_repository` | POST | Fork a project | `project_id` |

## Branches & Repository

| Tool | Method | Description | Key Params |
|------|--------|-------------|------------|
| `create_branch` | POST | Create a branch | `project_id`, `branch`, `ref` |
| `get_repository_tree` | GET | List repository tree | `project_id`, `path`, `ref`, `recursive` |
| `get_file_contents` | GET | Get a file | `project_id`, `file_path`, `ref` |
| `create_or_update_file` | PUT/POST | Create or update a file | `project_id`, `file_path`, `branch`, `content`, `commit_message`, `update` |
| `push_files` | POST | Push multiple files in one commit | `project_id`, `branch`, `commit_message`, `actions` (via `--body-file`) |
| `get_branch_diffs` | GET | Compare two branches | `project_id`, `from`, `to`, `straight` |

## Commits

| Tool | Method | Description | Key Params |
|------|--------|-------------|------------|
| `list_commits` | GET | List commits | `project_id`, `ref_name`, `since`, `until` |
| `get_commit` | GET | Get a single commit | `project_id`, `commit_sha` |
| `get_commit_diff` | GET | Get commit diff | `project_id`, `commit_sha` |

## Issues

| Tool | Method | Description | Key Params |
|------|--------|-------------|------------|
| `list_issues` | GET | List issues (global) | `scope`, `state`, `labels`, `search` |
| `my_issues` | GET | List issues assigned to me | `state`, `scope` |
| `get_issue` | GET | Get a single issue | `project_id`, `issue_iid` |
| `create_issue` | POST | Create an issue | `project_id`, `title`, `description`, `labels`, `assignee_ids` |
| `update_issue` | PUT | Update an issue | `project_id`, `issue_iid`, `state_event`, `title`, etc. |
| `delete_issue` | DELETE | Delete an issue | `project_id`, `issue_iid` |
| `list_issue_discussions` | GET | List issue discussions | `project_id`, `issue_iid` |
| `create_issue_note` | POST | Reply to an issue discussion | `project_id`, `issue_iid`, `discussion_id`, `body` |
| `update_issue_note` | PUT | Update an issue note | `project_id`, `issue_iid`, `discussion_id`, `note_id`, `body` |

## Issue Links

| Tool | Method | Description | Key Params |
|------|--------|-------------|------------|
| `list_issue_links` | GET | List issue links | `project_id`, `issue_iid` |
| `get_issue_link` | GET | Get an issue link | `project_id`, `issue_iid`, `issue_link_id` |
| `create_issue_link` | POST | Create an issue link | `project_id`, `issue_iid`, `target_project_id`, `target_issue_iid` |
| `delete_issue_link` | DELETE | Delete an issue link | `project_id`, `issue_iid`, `issue_link_id` |

## Merge Requests

| Tool | Method | Description | Key Params |
|------|--------|-------------|------------|
| `list_merge_requests` | GET | List merge requests | `project_id`, `state`, `scope` |
| `get_merge_request` | GET | Get a merge request | `project_id`, `merge_request_iid` |
| `get_merge_request_diffs` | GET | Get MR changes (full diff) | `project_id`, `merge_request_iid` |
| `list_merge_request_diffs` | GET | List MR diff versions | `project_id`, `merge_request_iid` |
| `create_merge_request` | POST | Create a merge request | `project_id`, `source_branch`, `target_branch`, `title` |
| `update_merge_request` | PUT | Update a merge request | `project_id`, `merge_request_iid`, `title`, `description`, etc. |
| `set_mr_reviewers` | PUT | Set reviewers on a merge request | `project_id`, `merge_request_iid`, `reviewer_ids` (comma-separated user IDs, e.g. `123,456`; pass `0` to clear) |
| `set_mr_assignees` | PUT | Set assignees on a merge request | `project_id`, `merge_request_iid`, `assignee_ids` (comma-separated user IDs; pass `0` to clear) |
| `merge_merge_request` | PUT | Merge a merge request | `project_id`, `merge_request_iid` |

## MR Discussions & Notes

| Tool | Method | Description | Key Params |
|------|--------|-------------|------------|
| `mr_discussions` | GET | List MR discussions | `project_id`, `merge_request_iid` |
| `create_merge_request_thread` | POST | Start a new MR thread | `project_id`, `merge_request_iid`, `body` |
| `create_merge_request_note` | POST | Reply to an MR discussion | `project_id`, `merge_request_iid`, `discussion_id`, `body` |
| `update_merge_request_note` | PUT | Edit an MR note | `project_id`, `merge_request_iid`, `discussion_id`, `note_id`, `body` |
| `create_note` | POST | Create a generic note | `project_id`, `note_target` (e.g. `issues`), `target_id`, `body` |

## Draft Notes

| Tool | Method | Description | Key Params |
|------|--------|-------------|------------|
| `list_draft_notes` | GET | List draft notes on MR | `project_id`, `merge_request_iid` |
| `get_draft_note` | GET | Get a draft note | `project_id`, `merge_request_iid`, `note_id` |
| `create_draft_note` | POST | Create a draft note | `project_id`, `merge_request_iid`, `note` |
| `update_draft_note` | PUT | Update a draft note | `project_id`, `merge_request_iid`, `note_id`, `note` |
| `delete_draft_note` | DELETE | Delete a draft note | `project_id`, `merge_request_iid`, `note_id` |
| `publish_draft_note` | POST | Publish a single draft | `project_id`, `merge_request_iid`, `note_id` |
| `bulk_publish_draft_notes` | POST | Publish all drafts | `project_id`, `merge_request_iid` |

## Pipelines & Jobs

| Tool | Method | Description | Key Params |
|------|--------|-------------|------------|
| `list_pipelines` | GET | List pipelines | `project_id`, `ref`, `status` |
| `get_pipeline` | GET | Get pipeline details | `project_id`, `pipeline_id` |
| `list_pipeline_jobs` | GET | List jobs in a pipeline | `project_id`, `pipeline_id`, `scope` (e.g. `failed`) |
| `list_pipeline_trigger_jobs` | GET | List trigger (bridge) jobs | `project_id`, `pipeline_id` |
| `get_pipeline_job` | GET | Get a single job | `project_id`, `job_id` |
| `get_pipeline_job_output` | GET | Get job log/trace | `project_id`, `job_id` |
| `create_pipeline` | POST | Trigger a new pipeline | `project_id`, `ref` |
| `retry_pipeline` | POST | Retry a pipeline | `project_id`, `pipeline_id` |
| `cancel_pipeline` | POST | Cancel a pipeline | `project_id`, `pipeline_id` |

## MR Analysis

| Tool | Method | Description | Key Params |
|------|--------|-------------|------------|
| `parse_mr_url` | LOCAL | Parse a GitLab MR URL into `project_id` and `merge_request_iid` (no auth needed) | `url` |
| `get_mr_pipelines` | GET | List pipelines for an MR (latest first) | `project_id`, `merge_request_iid`, `per_page` |
| `get_mr_code_quality` | GET | Code quality violations introduced by an MR (GitLab EE/Ultimate only; may return 403/404 when unavailable) | `project_id`, `merge_request_iid` |
| `get_mr_code_quality_attachment_report` | COMPOSITE | Find and download the latest matching MR code-quality report from uploaded MR discussion attachments; follows paginated discussions and use when native code-quality endpoint returns 404 | `project_id`, `merge_request_iid`, optional `filename_regex`, `text_regex`, `max_report_bytes` (default 5 MiB) |

## Milestones

| Tool | Method | Description | Key Params |
|------|--------|-------------|------------|
| `list_milestones` | GET | List milestones | `project_id` |
| `get_milestone` | GET | Get a milestone | `project_id`, `milestone_id` |
| `create_milestone` | POST | Create a milestone | `project_id`, `title` |
| `edit_milestone` | PUT | Edit a milestone | `project_id`, `milestone_id`, `title`, etc. |
| `delete_milestone` | DELETE | Delete a milestone | `project_id`, `milestone_id` |
| `get_milestone_issue` | GET | Get milestone issues | `project_id`, `milestone_id` |
| `get_milestone_merge_requests` | GET | Get milestone MRs | `project_id`, `milestone_id` |
| `promote_milestone` | POST | Promote to group milestone | `project_id`, `milestone_id` |
| `get_milestone_burndown_events` | GET | Get burndown events | `project_id`, `milestone_id` |

## Labels

| Tool | Method | Description | Key Params |
|------|--------|-------------|------------|
| `list_labels` | GET | List project labels | `project_id` |
| `get_label` | GET | Get a label | `project_id`, `label_id` |
| `create_label` | POST | Create a label | `project_id`, `name`, `color` |
| `update_label` | PUT | Update a label | `project_id`, `label_id`, `name`, `color` |
| `delete_label` | DELETE | Delete a label | `project_id`, `label_id` |

## Wiki

| Tool | Method | Description | Key Params |
|------|--------|-------------|------------|
| `list_wiki_pages` | GET | List wiki pages | `project_id` |
| `get_wiki_page` | GET | Get a wiki page | `project_id`, `slug` |
| `create_wiki_page` | POST | Create a wiki page | `project_id`, `title`, `content` |
| `update_wiki_page` | PUT | Update a wiki page | `project_id`, `slug`, `content` |
| `delete_wiki_page` | DELETE | Delete a wiki page | `project_id`, `slug` |

## Namespaces

| Tool | Method | Description | Key Params |
|------|--------|-------------|------------|
| `list_namespaces` | GET | List namespaces | `search` |
| `get_namespace` | GET | Get a namespace | `namespace_id` |
| `verify_namespace` | GET | Verify namespace exists | `namespace_id` |

## Users

| Tool | Method | Description | Key Params |
|------|--------|-------------|------------|
| `get_users` | GET | Search users | `search`, `username` |

## Iterations

| Tool | Method | Description | Key Params |
|------|--------|-------------|------------|
| `list_group_iterations` | GET | List group iterations | `group_id` |

## Uploads & Attachments

| Tool | Method | Description | Key Params |
|------|--------|-------------|------------|
| `upload_markdown` | POST | Upload a file for markdown embedding | `project_id`, `upload_file` (local path) |
| `download_attachment` | GET | Download an attachment | `project_id`, `secret`, `filename` |
