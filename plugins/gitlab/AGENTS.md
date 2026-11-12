# AGENTS.md

## Context loading

Start with `skills/using-gitlab/SKILL.md`. Only this router allows automatic skill selection. Read a supporting skill explicitly only after selection. Do not preload all skill, agent, or reference bodies. Keep existing approval gates. See the README for host limits.

This directory is the standalone GitLab plugin.

## Structure

```text
plugins/gitlab/
├── plugin.json
├── agents/
│   ├── gitlab-agent.agent.md
│   └── gl-*.agent.md
├── skills/
│   └── gitlab/
└── commands/
    ├── gitlab-login.md
    ├── gitlab-triage.md
    ├── gitlab-analyse.md
    └── update.md
```

## Agent Architecture

The GitLab plugin uses a **hub-and-spoke orchestrator pattern**. The
`gitlab-agent` orchestrator routes intent and coordinates four specialised
subagents. All subagents are `user-invocable: false`. The write agent
additionally sets `disable-model-invocation: true`.

| Agent | Role | Writes? |
|---|---|---|
| `gitlab-agent` | Orchestrator — routes intent, sequences subagents, owns write confirmation gate | No |
| `gl-triager` | Parses GitLab URL, classifies MR/issue, returns triage block | No |
| `gl-researcher` | Fetches discussions, pipelines, pipeline jobs, issue links | No |
| `gl-planner` | Repo-impact planning, concrete step-by-step plan; read-only | No |
| `gl-operator` | Applies one pre-approved write action and verifies it | **Yes** |

## Workflow

```text
User prompt → gitlab-agent (orchestrator)
                │
                ├─ gl-triager
                │
                ├─ gl-researcher
                │
                ├─ [optional, confirmed for planning]
                │   gl-planner
                │
                └─ [confirmed writes only]
                    gl-operator ×N (sequential)
```

## Guidance

- Use the `gitlab` skill for all GitLab API calls.
- Use `gitlab-login` / `uv run scripts/gitlab_token.py login --profile <name> ...` for credential setup; the skill itself should not perform credential preflight.
- Login stores tokens in OS keyring service `AgentDevelopmentToolkit:gitlab` and non-secret endpoint/safety metadata in stable per-user `gitlab.json`; `.env` is a legacy/CI fallback, not a prerequisite.
- Use `gitlab_token.py profiles`, `use-profile`, and `delete-profile` for lifecycle operations. Metadata deletion never deletes keyring tokens.
- Runtime profile precedence is API `--profile`, then `GITLAB_PROFILE`, then the active stable profile. Never combine partial endpoint/credential overrides with profile credentials or allow self-hosted credentials to fall back to `gitlab.com`.
- `GITLAB_READ_ONLY_MODE`, `GITLAB_ALLOWED_PROJECT_IDS`, and default-project restrictions belong to the selected profile and must remain enforced after relocation.
- `gl-operator` is a write agent; it must only run after the orchestrator
  presents proposed changes and receives explicit confirmation. The orchestrator/host conversation is the approval boundary; direct CLI invocation is treated as already authorized and intentionally has no forgeable confirmation flag.
- Direct `GITLAB_PERSONAL_ACCESS_TOKEN` is only a CI/non-interactive fallback and must be supplied with its matching `GITLAB_API_URL`. Never expose or persist it in profile metadata.
- After any write, verify with the corresponding read command.
