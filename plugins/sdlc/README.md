# SDLC Agent Development Toolkit

## Context loading

Start with [using-agent-skills](skills/using-agent-skills/SKILL.md). Only the router allows automatic skill selection. Supporting skills set `disable-model-invocation: true`; direct user commands remain available. The router reads the selected skill file explicitly. Use `using-agents` only for actual delegation. Do not preload all quality skills or agent bodies. Reuse unchanged rules across phases.

Copilot controls discovery metadata and system context. These rules do not guarantee a fixed token count or force the router to load at startup. Enable only the plugins needed for the task. Test loading in a fresh host session after updating.

A branch-based, artifact-light workflow for feature development:

```text
spec (including focused research) → design → plan → build → review → ship
```

The workflow keeps a separate branch and feature workspace, using three core
living Markdown documents and an optional detailed design:

```text
.features/<feature>/
├── SPEC.md
├── DESIGN.md                 # optional for substantial designs
├── status.json               # internal workflow state
└── tasks/
    ├── PLAN.md
    └── TODO.md
```

`status.json` is internal command state and is not a planning document.

## Output language

All SDLC agents, commands, and skills must use **ASD-STE100 Simplified Technical English** for replies to users and for text they create or change in artifacts. This includes artifacts saved outside the plugin directory and work assigned to other agents. Code, identifiers, required formats, and exact source quotations stay unchanged.

See [the output language rules](references/output-language.md). Each entry point loads these rules. Agents must check their text before they send or save it. These checks do not certify full compliance with the standard.

## Quickstart

Pick a short, kebab-case feature name. Start with `/spec`; each command updates the feature workspace, so you can pause and continue later.

```text
/spec encrypted-share-links allow admins to require expiring public links
/research encrypted-share-links focus on existing public-link services
/design encrypted-share-links compare policy enforcement approaches
/plan encrypted-share-links
/build encrypted-share-links
/review encrypted-share-links
/ship encrypted-share-links main
```

Use `/build --auto` to process all remaining checklist tasks in one approved
run. Each task still follows test → verify → update → commit. If you are unsure what to do next, use `/resume <feature>` to inspect the workspace and get the safest next step.

## Documents

### `SPEC.md`

A living source of truth containing the objective, users, requirements,
acceptance criteria, constraints, research, a concise design summary, risks, and
open questions. `SPEC.md` links to `DESIGN.md` when a detailed design is needed.

### `DESIGN.md` (optional)

A detailed technical design for substantial changes, such as cross-service
architecture, API contracts, data models, security boundaries, or diagrams.

### `tasks/PLAN.md`

The implementation plan. It contains small tasks, dependencies, acceptance
checks, verification commands, and likely files.

### `tasks/TODO.md`

The working checklist. Build marks tasks complete and records verification.
Review adds its checks, findings, acceptance status, and recommendation here.
`/review` freezes the artifact while a reviewer and independent `review-critic`
resolve evidence-grounded disagreements; the critic's consolidated result is
recorded before `/build`, `/refine`, or `/ship` is recommended.

Use ordinary Markdown headings and `- [ ]` / `- [x]` checkboxes. No generated
cross-document ID system is required.

## Skills

The plugin adapts the useful parts of Addy Osmani's agent-skills workflow:

- spec-driven development with a living specification;
- small, dependency-ordered checklist tasks;
- incremental implementation with tests and verification;
- debugging when checks fail;
- focused code, security, performance, and UI reviews when relevant; and
- final shipping checks with branch/MR safeguards.

Generic engineering skills remain available, but should be loaded selectively
for the change at hand rather than as mandatory gates for every feature.

## Installation

```bash
copilot plugin marketplace add .
copilot plugin install sdlc@vnr-agent-development-toolkit
```

For direct development:

```bash
copilot plugin install plugins/sdlc
```
