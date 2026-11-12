# AGENTS.md

## Context loading

Start with `skills/using-blackduck/SKILL.md`. Only this router allows automatic skill selection. Read a supporting skill explicitly only after selection. Do not preload all skill, agent, or reference bodies. Keep existing approval gates. See the README for host limits.

This directory is the standalone Black Duck plugin.

## Structure

```text
plugins/blackduck/
├── plugin.json
├── agents/
│   ├── blackduck.agent.md
│   └── bd-*.agent.md
├── skills/
│   └── blackduck/
└── commands/
    ├── blackduck-login.md
    ├── component-review.md
    ├── vulnerability-analysis.md
    └── vulnerability-review.md
```

## Guidance

- Use the `blackduck` skill for all Black Duck API calls.
- Use `blackduck-login` / `uv run scripts/blackduck_token.py login --profile <name> ...` for credential setup; the skill itself should not perform credential preflight.
- Login stores tokens in OS keyring service `AgentDevelopmentToolkit:blackduck` and non-secret URL/SSL metadata in stable per-user `blackduck.json`; `.env` is a legacy/CI fallback, not a prerequisite.
- Use `blackduck_token.py profiles`, `use-profile`, and `delete-profile` for lifecycle operations. Metadata deletion never deletes keyring tokens.
- Runtime profile precedence is API `--profile`, then `BLACKDUCK_PROFILE`, then the active stable profile. Never mix partial URL/credential overrides with profile credentials.
- Preserve each profile's `verify_ssl` setting after relocation. Do not disable SSL verification without explicit user acceptance for a known private/self-signed certificate environment.
- Use the `blackduck` orchestrator agent for multi-step workflows.
- `bd-remediator` and `bd-component-updater` are write agents; they must only run after the orchestrator presents proposed changes and receives explicit confirmation. The orchestrator/host conversation is the approval boundary; direct CLI invocation is treated as already authorized and intentionally has no forgeable confirmation flag.
- Direct `BLACKDUCK_TOKEN` is only a CI/non-interactive fallback and must be supplied with matching `BLACKDUCK_URL`. Never expose or persist it in profile metadata.
- After any write, verify with the corresponding read command.
