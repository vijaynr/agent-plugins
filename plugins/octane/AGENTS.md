# AGENTS.md

## Context loading

Start with `skills/using-octane/SKILL.md`. Only this router allows automatic skill selection. Read a supporting skill explicitly only after selection. Do not preload all skill, agent, or reference bodies. Keep existing approval gates. See the README for host limits.

This directory is the standalone Octane plugin.

## Structure

```text
plugins/octane/
├── plugin.json
├── agents/
│   ├── octane-agent.agent.md
│   └── oct-*.agent.md
├── skills/
│   └── alm-octane/
└── commands/
    ├── octane-login.md
    ├── octane-triage.md
    ├── octane-analyse.md
    ├── octane-plan.md
    └── octane-fix.md
```

## Guidance

- Use the `alm-octane` skill for all ALM Octane API calls.
- Use `octane-login` / `uv run scripts/octane_token.py login --profile <name> ...` for credential setup; the skill itself should not perform credential preflight.
- Login stores secrets in OS keyring service `AgentDevelopmentToolkit:alm-octane` and non-secret profile metadata in stable per-user `octane.json`, not in the plugin directory. `.env` is a legacy/CI fallback, not a prerequisite.
- Use `octane_token.py profiles`, `use-profile`, and `delete-profile` for lifecycle operations. Metadata deletion never deletes keyring credentials.
- Runtime profile precedence is API `--profile`, then `OCTANE_PROFILE`, then the active stable profile. Do not combine partial endpoint or credential overrides with a selected profile.
- Use the `octane-agent` orchestrator for multi-step backlog workflows.
- Direct `OCTANE_CLIENT_SECRET` is only for CI/non-interactive use and must be supplied with a coherent endpoint and client ID. Never expose or persist it in profile metadata.
- Never perform Octane writes/deletes without explicit user confirmation where required by the agent/skill. The orchestrator/host conversation is the approval boundary; direct CLI invocation is treated as already authorized and intentionally has no forgeable confirmation flag.
- After any write, verify with the corresponding read command.
