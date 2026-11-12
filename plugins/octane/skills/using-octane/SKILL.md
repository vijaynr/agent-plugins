---
name: using-octane
description: Route ALM Octane backlog, work-item, API, attachment, and credential requests. Use for Octane work before loading API or agent instructions.
---

# Octane Router

Select one route. Do not load all skills, agents, examples, or references.

- API reads or a narrow question: [alm-octane](../alm-octane/SKILL.md).
- Backlog triage, analysis, planning, or implementation workflow: `../../agents/octane-agent.agent.md`.
- Credentials: `../../commands/octane-login.md`.

Read the selected file explicitly before acting. Supporting skills are not automatically invoked; read their files only after selection. Resolve paths from this file. Report missing files instead of scanning unrelated plugins.

Use the host's agent tool for delegation. Let the orchestrator load its subagents; do not load their bodies into the parent context. Pass only the task, scope, identifiers, evidence needed, and approval state. Request concise results with artifact paths and blockers, not raw tool logs.

Keep credential, attachment, and write approval gates. Never treat routing as approval. Verify each approved write with a read. Load references only for the current operation. Reuse instructions already in context.
