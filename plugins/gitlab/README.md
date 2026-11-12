# GitLab Agent Toolkit

## Context loading

Start with [using-gitlab](skills/using-gitlab/SKILL.md). Only the router allows automatic skill selection. Supporting skills set `disable-model-invocation: true`; direct user commands remain available. The router reads the selected skill file explicitly. Agents load their own instructions when invoked. Do not preload the whole plugin.

Copilot controls discovery metadata and system context. These rules do not guarantee a fixed token count or force the router to load at startup. Enable only the plugins needed for the task. Test loading in a fresh host session after updating.

Multi-agent plugin for GitLab issue and merge-request triage, analysis, planning, and explicitly approved updates.

## Agents and commands

| Agent | Role |
|---|---|
| `gitlab-agent` | Orchestrates triage, analysis, planning, and write confirmation |
| `gl-triager` | Parses and classifies issues/MRs |
| `gl-researcher` | Reads discussions, pipelines, jobs, and links |
| `gl-planner` | Produces a read-only action plan |
| `gl-operator` | Performs one pre-approved write and verifies it |

Commands: `/gitlab-login`, `/gitlab-triage`, `/gitlab-analyse`, and `/update`.

```text
/gitlab-login
/gitlab-triage https://gitlab.example.com/group/project/-/merge_requests/123
/gitlab-analyse https://gitlab.example.com/group/project/-/issues/456
/update https://gitlab.example.com/group/project/-/merge_requests/123 --action add-note
```

The update workflow presents intended changes and invokes the write agent only after explicit approval.

### Your first GitLab task

1. Run `/gitlab-login` once to connect your GitLab account.
2. Paste an issue or merge-request URL into `/gitlab-triage`.
3. Use `/gitlab-analyse` when you want the discussions, pipeline results, and next steps summarized.

Use `/update` only after reviewing the proposed change. It will ask for explicit approval before adding a note or making another supported update.

## Durable credential profiles

Login stores the personal access token in OS keyring service `AgentDevelopmentToolkit:gitlab`. Stable `gitlab.json` stores only non-secret endpoint, keyring username, default project, project allowlist, read-only mode, and timeout:

| Platform | Default metadata path |
|---|---|
| Windows | `%APPDATA%\AgentDevelopmentToolkit\gitlab.json` |
| macOS | `~/Library/Application Support/AgentDevelopmentToolkit/gitlab.json` |
| Linux | `${XDG_CONFIG_HOME:-~/.config}/agent-development-toolkit/gitlab.json` |

`AGENT_DEVELOPMENT_TOOLKIT_CONFIG_HOME` overrides the directory on every platform. Profiles survive plugin relocation and upgrades because configuration is outside the plugin. The generic storage rename requires a fresh login for users of earlier names; old profiles and keyring entries are not read or removed. Supply the endpoint explicitly with `--api-url`, `GITLAB_API_URL`, or an existing generic profile. There is no default host.

From the skill root, inspect fallback defaults when creating a new profile. When updating an existing profile, explicitly confirm and pass every project/safety setting instead of assuming `defaults` reflects that profile. Inject `GITLAB_LOGIN_TOKEN` through the launcher's masked environment; never place its value in command text or chat.

```bash
uv run scripts/gitlab_token.py defaults
uv run scripts/gitlab_token.py login \
  --profile default \
  --api-url "https://gitlab.example.com/api/v4" \
  --user "https://gitlab.example.com/api/v4" \
  --project-id "<default-project-id>" \
  --allowed-project-ids "<comma-separated-project-ids>" \
  --read-only-mode true \
  --timeout 60
```

Login verifies the named profile with a minimal API read unless `--skip-test` is supplied, including profiles saved with `--no-activate`. Login attempts stage-appropriate rollback after failure; if it reports rollback trouble, treat metadata and keyring state as needing separate inspection.

### Profile lifecycle and selection

```bash
# Add/update without changing the active profile
uv run scripts/gitlab_token.py login --profile staging --no-activate \
  --api-url "https://staging-gitlab.example.com/api/v4" \
  --user "https://staging-gitlab.example.com/api/v4" \
  --read-only-mode true

uv run scripts/gitlab_token.py profiles
uv run scripts/gitlab_token.py use-profile --profile staging
uv run scripts/gitlab_token.py delete-profile --profile staging
uv run scripts/gitlab_cli.py --profile default list_projects
```

Runtime selection is API `--profile`, then `GITLAB_PROFILE`, then the active stable profile. Deleting a profile removes metadata only; it never deletes the token from keyring.

## Safety and endpoint pairing

`GITLAB_READ_ONLY_MODE`, `GITLAB_ALLOWED_PROJECT_IDS`, and the default project are profile settings. They remain enforced after plugin replacement. The generic request path rejects disallowed writes/projects locally; keep restrictive settings when creating replacement profiles.

Agent workflows require explicit confirmation in the orchestrator before invoking `gl-operator`. The orchestrator/host conversation is the accepted approval boundary; direct CLI calls are treated as already authorized and do not accept a model-forgeable confirmation flag. For untrusted automation, enforce safety with read-only/scoped credentials, profile restrictions, and host tool permissions.

Credential endpoints must use HTTPS and cannot contain userinfo, query strings, or fragments. A selected profile's endpoint and keyring locator are one credential source. Process-level partial `GITLAB_API_URL`, `GITLAB_PERSONAL_ACCESS_TOKEN`, or `GITLAB_TOKEN_KEYRING_USER` overrides are rejected rather than mixed with profile values. Legacy `.env` credentials do not override a selected stable profile. This prevents a self-hosted token from being sent to `gitlab.com` or another host. The primary API request path refuses redirects rather than forwarding its token to a redirected host.

For CI, supply the complete pair `GITLAB_API_URL` and `GITLAB_PERSONAL_ACCESS_TOKEN`. Optional safety and timeout environment settings then override profile defaults. Never commit a direct token or place it in normal logs.

## Legacy `.env` migration

When no stable document exists, startup checks the executing skill root, `~/.copilot/skills/gitlab`, and `~/.agents/skills/gitlab`. One unambiguous, usable keyring-backed candidate is migrated into `default`. Migration persists only non-secret metadata, deduplicates equivalent aliases, and never rewrites or deletes source files. Conflicting candidates or unusable keyring entries fail without stable-state or network mutation. A direct-token `.env` in the executing skill root remains a fallback when no stable profile is selected and is never migrated; direct-token files found only in other migration-discovery roots are not loaded. Help commands skip migration.

## Troubleshooting

| Error class | Safe recovery |
|---|---|
| Missing/invalid profile metadata | Run `gitlab_token.py profiles`; select an existing profile or log in again. Do not hand-edit malformed JSON. |
| `GITLAB_KEYRING_ENTRY_MISSING` | Re-run login for the selected profile and keyring username. |
| `GITLAB_KEYRING_BACKEND_FAILURE` | Unlock/configure the OS credential store, then retry without plaintext fallback. |
| `GITLAB_CREDENTIAL_SOURCE_MISMATCH` | Remove partial environment overrides or provide one complete direct/keyring-backed source. |
| `GITLAB_REMOTE_AUTHENTICATION_FAILED` / HTTP 401 | Verify selected host and token rotation, then log in again. |
| `GITLAB_REMOTE_AUTHORIZATION_FAILED` / HTTP 403 | Request permission for the selected GitLab/project; changing host or token blindly is unsafe. |
| Project allowlist/read-only rejection | Select the intended profile or deliberately update its safety settings through login; do not bypass the local check. |
| Legacy migration conflict | Reconcile reported non-secret paths/fields and retry; source files remain unchanged. |
| Incomplete rollback | Stop and inspect profile metadata and keyring selection separately before retrying; never print the token. |

Coded credential failures use JSON and generic API responses omit exact known credential-key fields; other errors may lack codes, and all server-provided response bodies must be treated as potentially sensitive. Token-helper diagnostics are written to stderr.

## Relationship to SDLC

Use GitLab for repository-hosting and MR/issue workflows. The [SDLC plugin](../sdlc/README.md) owns feature artifacts and `/ship` readiness; this plugin owns GitLab authentication and API operations.

## Install

From the repository root:

```bash
copilot plugin marketplace add .
copilot plugin install gitlab@vnr-agent-development-toolkit
```

For a direct development install:

```bash
copilot plugin install plugins/gitlab
```
