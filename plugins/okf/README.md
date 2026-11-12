# Open Knowledge Format Repository Toolkit

## Context loading

Start with [using-okf](skills/using-okf/SKILL.md). Only the router allows automatic skill selection. Supporting skills set `disable-model-invocation: true`; direct user commands remain available. The router reads the selected skill file explicitly. Read only relevant catalog concepts, not the whole catalog.

Copilot controls discovery metadata and system context. These rules do not guarantee a fixed token count or force the router to load at startup. Enable only the plugins needed for the task. Test loading in a fresh host session after updating.

The `okf` plugin creates and consumes Open Knowledge Format (OKF v0.1)
knowledge catalogs stored under a repository's `docs/` directory.

Authoring workflows are explicit and reviewable: initialization and ingestion
write directly only after approval, and both report a unified diff.

## Start here

Use OKF when a repository needs durable, structured knowledge that people and agents can find later. From the repository you want to document:

1. Run `/okf-init` to preview an initial catalog under `docs/`.
2. Review the proposed diff and approve it when it looks right.
3. Use `/okf-ingest` to add knowledge from a conversation or source material.
4. Run `/okf-validate` before sharing or committing the catalog.

Available commands:

- `/okf-init` — create an initial architecture, decisions, gotchas, indexes,
  and update log after explicit approval.
- `/okf-ingest` — convert conversation or supplied content into proposed concepts.
- `/okf-validate` — validate OKF v0.1 conformance.
- `/okf-export` — emit deterministic JSON for external consumers.

Initialization and ingestion write directly after explicit approval and report
the applied files and diff. Agents should use `using-okf-knowledge` to read catalogs
progressively and verify consequential claims against source evidence.

## Portable implementation

The self-contained `okf-toolkit` skill owns all four authoring/validation modes,
the executable CLI, and its shared package:

```text
skills/okf-toolkit/
├── SKILL.md
└── scripts/
    ├── okf_cli.py
    └── okf_core/
```

This follows the Agent Skills convention that executable and reusable helper
code lives under the owning skill's `scripts/` directory. The CLI has `init`,
`ingest`, `validate`, and `export` subcommands and does not depend on sibling
skills or the source repository's enclosing `plugins/okf` Python package path.
The four slash commands route to modes of this one portable skill.

## Install

```bash
copilot plugin marketplace add .
copilot plugin install okf@vnr-agent-development-toolkit
```

For a direct development install:

```bash
copilot plugin install plugins/okf
```
