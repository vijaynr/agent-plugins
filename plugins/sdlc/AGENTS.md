# AGENTS.md

## Context loading

Start with `skills/using-agent-skills/SKILL.md`. Only this router allows automatic skill selection. Read a supporting skill explicitly only after selection. Do not preload all skill, agent, or reference bodies. Keep existing approval gates. See the README for host limits.

## Required output language

Use **ASD-STE100 Simplified Technical English** for all end-user replies and all text that you create or change in artifacts. Read and follow [the output language rules](references/output-language.md) before you start. Include this requirement in delegated tasks. It applies to every SDLC agent, command, and skill.

This `plugins/sdlc` directory contains the SDLC plugin: AI SDLC, artifact-generation, dependency, and project-context skills plus related commands.

Companion plugins own adjacent workflows:

- `plugins/obs` — Internal OBS RPM packaging, builds, and approved submissions.
- `plugins/octane` — ALM Octane workflows.
- `plugins/blackduck` — Black Duck workflows.
- `plugins/gitlab` — GitLab workflows.
- `plugins/product-owner` — Product-owner PRD and backlog-shaping workflows.
- `plugins/context-engineering` — local context-tooling setup workflows.
- `plugins/okf` — repository Open Knowledge Format catalog workflows.

## Plugin Structure

```text
plugins/sdlc/
├── plugin.json
├── agents.sh
├── agents/                 # optional SDLC-support agents
├── commands/               # SDLC and integration slash command templates
├── hooks/                  # Lifecycle hook JSON files
├── skills/                 # SDLC, GitLab, docs, setup, and helper skills
├── docs/
├── scripts/
├── slides/
└── specs/
```

## Key Skills

- `ai-sdlc` — branch-based `/spec` (including focused research), optional deep `/research`, `/design`, `/plan`, `/build`, `/review`, and `/ship` workflow using `SPEC.md`, optional `DESIGN.md`, `tasks/PLAN.md`, and `tasks/TODO.md`, with a meta-skill routing preflight.
- `using-agent-skills` — meta-skill routing map for this plugin and companion plugins.
- `using-agents` — meta-skill that discovers nearby/installed custom agents and routes by prompt intent.
- `codebase-researcher` agent — read-only per-workspace research subagent. `ai-sdlc` `/research --workspaces` sends it one `sdlc_research_request` for each workspace.
- `code-reviewer` agent — independent five-axis review before merge and reviewer role in adversarial review.
- `review-critic` agent — independently scrutinizes reviewer findings with evidence-grounded disagreement and presents the consolidated result.
- `test-engineer` agent — test strategy, regression tests, and coverage-gap analysis; can serve as the focused test reviewer in adversarial review. It does not edit files in `/review`.
- `security-auditor` agent — threat modeling and secure-design review; can serve as the focused security reviewer in adversarial review. It uses `web` only for public security information.
- Review agents get the frozen `sdlc_review_request` block from `skills/ai-sdlc/references/review-request.md`. `skills/ai-sdlc/references/review-verdicts.md` maps each reviewer result to one consolidated verdict. Read-only agents have the same command limits.
- `init-workspace`, `setup-project`, `generate-arch-md`, `generate-agents-md` — project/workspace preparation and context artifact generation.
- Local tooling bootstrap (`setup-rtk`, `setup-ripgrep`) is owned by the `context-engineering` companion plugin.
- `grilling` — one-question-at-a-time clarification support for SDLC flows.
- Generic engineering quality skills — source-grounded implementation, TDD, API/interface design, frontend UI engineering, performance optimization, deprecation/migration, doubt-driven review, debugging, simplification, review, security, observability, `ci-cd-and-automation`, and `documentation-and-adrs` workflows.

## Agent model defaults

`codebase-researcher` and `review-critic` use `claude-haiku-5.5`. `code-reviewer`, `security-auditor`, and `test-engineer` use `gpt-6-luna`. See [Agent model defaults](../../docs/agent-models.md) for host limits and escalation guidance. These defaults do not change agent permissions or review contracts.

## Conventions

- Work from this plugin root when running plugin-local scripts: `cd plugins/sdlc`.
- Skill scripts return JSON where possible; parse outputs directly.
- Prefer OS keyring for service secrets; direct `.env` secrets are CI/non-interactive fallback only.
- Never commit `.env` files.
- After any write operation, verify with the corresponding read command.
- When adding, removing, renaming, or materially changing a skill or agent, update this file and `skills/using-agent-skills/SKILL.md`. Update `skills/using-agents/SKILL.md` only when agent routing changes.
