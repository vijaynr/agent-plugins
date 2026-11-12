# GitLab Python Skill

## Mandatory Script Location / Invocation

**Before every tool command, resolve `SKILL_ROOT` and invoke scripts by absolute path.**
Do not run `uv run scripts/...` unless your shell is already in `"$SKILL_ROOT"`.
The safest copy/paste pattern is:

```bash
SKILL_ROOT=""
for d in "$HOME"/.copilot/installed-plugins/*/gitlab/skills/gitlab "$HOME/.copilot/skills/gitlab" "$HOME/.agents/skills/gitlab"; do
  if [ -f "$d/SKILL.md" ]; then SKILL_ROOT="$d"; break; fi
done
[ -n "$SKILL_ROOT" ] || { echo "gitlab skill not found"; exit 1; }
[ -d "$SKILL_ROOT/scripts" ] || { echo "scripts folder not found under $SKILL_ROOT"; exit 1; }
```

Then run `uv run "$SKILL_ROOT/scripts/<script>.py" ...`. This works even
when the current working directory is a project checkout, a temp directory, or
an agent harness directory.

## Skill Resource Location

This is a **user-level skill**. Do not look for its `scripts/`, `references/`,
`.env`, or other resources in the current project directory. Before using the
skill, resolve the skill root from the installed GitLab plugin root, then the
direct user skill directories:

```bash
for d in "$HOME"/.copilot/installed-plugins/*/gitlab/skills/gitlab "$HOME/.copilot/skills/gitlab" "$HOME/.agents/skills/gitlab"; do
  if [ -f "$d/SKILL.md" ]; then SKILL_ROOT="$d"; break; fi
done
[ -n "$SKILL_ROOT" ] || { echo "GitLab skill not found in installed plugin or user skill directories"; exit 1; }
```

Run commands from `"$SKILL_ROOT"` or use absolute paths under `"$SKILL_ROOT"`.
Read `"$SKILL_ROOT/references/TOOLS.md"` only when the needed command or
parameter details are not listed below. Do not read `./references/TOOLS.md`
from the current project.

## Setup

The Python script declares its own dependencies via PEP 723 inline metadata
and must be invoked with **`uv run`** — no `pip install` step is required.

Prerequisites:

1. **[uv](https://docs.astral.sh/uv/)** must be installed and on `PATH`.
   uv is **not** bundled with Python and must be installed separately.
   See https://docs.astral.sh/uv/getting-started/installation/ for install
   instructions.
2. **Python 3.9+** must be available (uv will locate it automatically).

Before first use, create a durable profile rather than copying `.env`. Inject `GITLAB_LOGIN_TOKEN` through a masked launcher environment without placing its value in command text:

```bash
cd "$SKILL_ROOT"
uv run scripts/gitlab_token.py login --profile default \
  --api-url "https://gitlab.example.com/api/v4" \
  --user "https://gitlab.example.com/api/v4" \
  --project-id "<project-id>" --allowed-project-ids "<ids>" \
  --read-only-mode true --timeout 60
```

## Credential Profiles and Environment

The PAT is stored in OS keyring service `AgentDevelopmentToolkit:gitlab`. Stable `gitlab.json` stores only endpoint, keyring username, project restrictions, read-only mode, and timeout.

| Platform | Default `gitlab.json` directory |
|---|---|
| Windows | `%APPDATA%\AgentDevelopmentToolkit` |
| macOS | `~/Library/Application Support/AgentDevelopmentToolkit` |
| Linux | `${XDG_CONFIG_HOME:-~/.config}/agent-development-toolkit` |

`AGENT_DEVELOPMENT_TOOLKIT_CONFIG_HOME` overrides the directory. Runtime precedence is `gitlab_cli.py --profile <name>`, then `GITLAB_PROFILE`, then the active profile.

```bash
uv run scripts/gitlab_token.py profiles
uv run scripts/gitlab_token.py use-profile --profile default
uv run scripts/gitlab_token.py delete-profile --profile default
uv run scripts/gitlab_cli.py --profile default list_projects
```

Use `login --no-activate` to save without changing the active profile. Deletion removes metadata only, never keyring tokens. Login verifies the named profile, including profiles created with `--no-activate`. `defaults` provides new-profile fallbacks, not the settings of an existing named profile, so explicitly pass every project/safety setting on updates. Login attempts stage-appropriate rollback and reports recovery trouble.

### Safety and provenance

`project_id`, `allowed_project_ids`, and `read_only_mode` are profile settings and survive plugin relocation. The generic request path rejects disallowed writes/projects locally. Process-level partial endpoint/token/keyring-user overrides are rejected when a profile is selected, and legacy `.env` credentials do not override a selected stable profile, preventing self-hosted credentials from being paired with `gitlab.com` or another host. The primary API request path refuses redirects rather than forwarding its token to a redirected host.

For CI, provide complete `GITLAB_API_URL` plus `GITLAB_PERSONAL_ACCESS_TOKEN`; optional safety/timeout environment variables override profile settings. Direct tokens are not persisted or migrated.

| Variable | Purpose |
|---|---|
| `GITLAB_PROFILE` | Named profile when API `--profile` is absent |
| `GITLAB_TOKEN_KEYRING_USER` | Keyring username for a complete explicit URL/keyring override |
| `GITLAB_PERSONAL_ACCESS_TOKEN` | Direct CI token, paired with `GITLAB_API_URL` |
| `GITLAB_API_URL` | Matching API base URL; never silently default a self-hosted credential |
| `GITLAB_PROJECT_ID` | Default project |
| `GITLAB_ALLOWED_PROJECT_IDS` | Comma-separated allowlist; empty allows all |
| `GITLAB_READ_ONLY_MODE` | `true` blocks writes locally |
| `GITLAB_TIMEOUT` | Positive request timeout in seconds |

### Legacy migration

With no stable document, startup checks the executing skill root, `~/.copilot/skills/gitlab`, and `~/.agents/skills/gitlab`. One unambiguous usable keyring-backed candidate is migrated to `default`; equivalent aliases are deduplicated. Only non-secret metadata is persisted and sources remain byte-for-byte unchanged. Conflicts and unusable keyring entries fail before HTTP. A direct-token `.env` in the executing skill root remains a fallback and is never migrated; direct-token files found only in the other discovery roots are not loaded. Help commands skip migration.

## Command Pattern

```bash
cd "$SKILL_ROOT"
uv run "$SKILL_ROOT/scripts/gitlab_cli.py" [--profile <name>] <tool_name> --param key=value --param key=value
```

Equivalent absolute-path form when you must stay in a project directory:

```bash
uv run "$SKILL_ROOT/scripts/gitlab_cli.py" <tool_name> --param key=value --param key=value
```

For complex write payloads:

```bash
uv run "$SKILL_ROOT/scripts/gitlab_cli.py" <tool_name> --body-file payload.json --param project_id=123
```

All commands return JSON. Parse it directly.

## Tool Reference

If the needed command is not listed here, see `"$SKILL_ROOT/references/TOOLS.md"` for the complete list of 83 tools grouped by category with parameter details.

### Commonly Used Tools

| Task | Command |
|------|---------|
| List projects | `uv run "$SKILL_ROOT/scripts/gitlab_cli.py" list_projects` |
| Get project | `uv run "$SKILL_ROOT/scripts/gitlab_cli.py" get_project --param project_id=123` |
| List issues | `uv run "$SKILL_ROOT/scripts/gitlab_cli.py" list_issues --param scope=all` |
| Create issue | `uv run "$SKILL_ROOT/scripts/gitlab_cli.py" create_issue --param project_id=123 --param title="Bug"` |
| Get merge request | `uv run "$SKILL_ROOT/scripts/gitlab_cli.py" get_merge_request --param project_id=123 --param merge_request_iid=45` |
| Get file | `uv run "$SKILL_ROOT/scripts/gitlab_cli.py" get_file_contents --param project_id=123 --param file_path=README.md --param ref=main` |
| List pipelines | `uv run "$SKILL_ROOT/scripts/gitlab_cli.py" list_pipelines --param project_id=123` |
| Get job log | `uv run "$SKILL_ROOT/scripts/gitlab_cli.py" get_pipeline_job_output --param project_id=123 --param job_id=456` |
| Parse MR URL | `uv run "$SKILL_ROOT/scripts/gitlab_cli.py" parse_mr_url --param url=https://gitlab.com/group/repo/-/merge_requests/42` |
| Get MR pipelines | `uv run "$SKILL_ROOT/scripts/gitlab_cli.py" get_mr_pipelines --param project_id=123 --param merge_request_iid=42` |
| Get MR code quality via native API | `uv run "$SKILL_ROOT/scripts/gitlab_cli.py" get_mr_code_quality --param project_id=123 --param merge_request_iid=42` |
| Get MR code quality via attachment report | `uv run "$SKILL_ROOT/scripts/gitlab_cli.py" get_mr_code_quality_attachment_report --param project_id=123 --param merge_request_iid=42` |
| Get MR code quality attachment with explicit size limit | `uv run "$SKILL_ROOT/scripts/gitlab_cli.py" get_mr_code_quality_attachment_report --param project_id=123 --param merge_request_iid=42 --param max_report_bytes=5242880` |

## Gotchas

- **`file_path` is URL-encoded automatically.** Pass the raw path (`src/main.py`), not percent-encoded (`src%2Fmain.py`).
- **`create_or_update_file` defaults to PUT (update).** Pass `--param update=false` for a new file create.
- **`my_issues` defaults to `scope=assigned_to_me` and `state=opened`.** Override explicitly if you want all issues.
- **`search_repositories` requires a `search` param** and defaults `scope=projects`. Pass `--param search=query`.
- **Both camelCase and snake_case params work.** `projectId` and `project_id` are both accepted; they're canonicalized internally.
- **Write operations are blocked when `GITLAB_READ_ONLY_MODE=true`.** The script exits with an error; it does not silently skip.
- **`get_branch_diffs` requires `from` and `to` params** (branch names or SHAs). Other params are ignored for this tool.
- **File uploads (`upload_markdown`) need `--param upload_file=/absolute/path`**. Relative paths must be resolvable from the working directory.
- **The script exits with code 1 on HTTP errors.** The JSON output still contains the error body from GitLab for debugging.
- **MR code-quality attachment reports are searched across paginated MR discussions.** `get_mr_code_quality_attachment_report` selects the latest matching uploaded attachment by note timestamp. Use `filename_regex`/`text_regex` if your bot uses custom wording, and `max_report_bytes` to override the default 5 MiB response-size guard.

## MR Triage & Fix Workflow

When given a GitLab MR URL, use these steps to diagnose failures and apply fixes:

1. **Parse URL** — `parse_mr_url --param url=<url>` (no auth needed). Note `project_id` and `merge_request_iid`.
2. **Get MR details** — `get_merge_request`. Note `source_branch` and **`source_project_id`** (differs from target for fork MRs). Use `source_project_id` for all file writes.
3. **Find failed pipeline** — `get_mr_pipelines --param per_page=5`. Take the most recent pipeline with `status=failed`.
4. **List failed jobs** — `list_pipeline_jobs --param pipeline_id=<id> --param scope=failed`. Also run `list_pipeline_trigger_jobs` to catch failed bridge/child pipelines.
5. **Fetch logs** — `get_pipeline_job_output` for each failed job. Prioritise jobs with `stage` = `test`, `lint`, or `build`.
6. **Code quality** — Prefer `get_mr_code_quality_attachment_report` on instances where the native MR code-quality API returns 404; the uploaded attachment report is authoritative. Use `get_mr_code_quality` only when the native endpoint is known to work.
7. **Review diff** — `get_merge_request_diffs` to see all changed files before editing.
8. **Apply fixes** — fetch the relevant source files, make targeted corrections, push all changes in a single commit via `push_files` targeting the `source_branch` on the `source_project_id`.
9. **Verify** — `get_mr_pipelines` again to confirm a new pipeline was triggered, or state that verification is pending.
10. **Comment** — `create_merge_request_thread` on the target project's MR to summarise what was fixed.

### Gotchas
- **Fork MRs**: always write to `source_project_id`, not the target project. Read `source_project_id` from `get_merge_request` response.
- **No failed pipeline**: if all pipelines are passing/running/pending, report the current status and stop.
- **Pipeline still running**: wait before concluding failures; report status and ask user to retry later.
- **Bridge jobs**: a passing top-level job can mask a failing child pipeline — always run `list_pipeline_trigger_jobs`.

## Credential Troubleshooting

Stop rather than retrying against another host or bypassing local restrictions.

| Symptom / code | Safe recovery |
|---|---|
| Missing or invalid profile metadata | Run `gitlab_token.py profiles`; select an existing profile or log in again. Do not hand-edit malformed JSON. |
| `GITLAB_KEYRING_ENTRY_MISSING` | Re-run login for the selected profile/keyring username. |
| `GITLAB_KEYRING_BACKEND_FAILURE` | Unlock or configure the OS credential backend; do not switch to plaintext. |
| `GITLAB_CREDENTIAL_SOURCE_MISMATCH` | Remove partial environment overrides or provide a complete matching URL/token or URL/keyring-user source. |
| `GITLAB_REMOTE_AUTHENTICATION_FAILED` / HTTP 401 | Confirm selected host and token validity/rotation, then log in again. |
| `GITLAB_REMOTE_AUTHORIZATION_FAILED` / HTTP 403 | Request access to the selected GitLab resource; do not silently change hosts. |
| Read-only or project allowlist rejection | Select the intended profile or deliberately update its safety metadata through login. Do not bypass the local check. |
| Legacy migration conflict | Reconcile reported non-secret candidate paths/fields; source `.env` files were not changed. |
| Login rollback incomplete | Stop and inspect metadata and keyring selection separately before restoring either side; never print the token. |

Coded credential failures use JSON, and generic API responses omit exact known credential-key fields. Other errors may have no code; treat every server-provided response body as potentially sensitive. Token-helper setup diagnostics use stderr.

## Validation

After any write operation, verify the result by calling the corresponding read tool. For example, after `create_issue`, call `get_issue` to confirm it was created correctly.

## Usage Rules

1. Always pass `--param project_id=...` unless `GITLAB_PROJECT_ID` is set in the environment.
2. Respect `GITLAB_ALLOWED_PROJECT_IDS` — the script enforces it, but avoid unnecessary failures.
3. Check `GITLAB_READ_ONLY_MODE` before invoking write tools.
4. For batch operations, prefer `push_files` (single commit) over multiple `create_or_update_file` calls.
5. Use `--body-file` for complex payloads with nested JSON rather than cramming everything into `--param`.
