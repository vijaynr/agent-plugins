---
name: using-blackduck
description: Route Black Duck vulnerability, CVE/BDSA, BOM component review, and credential requests. Use for Black Duck work before loading API or agent instructions.
---

# Black Duck Router

Select one route. Do not load all skills, agent bodies, examples, or references.

- API reads or a narrow question: [blackduck](../blackduck/SKILL.md).
- Vulnerability or component-review workflow: `../../agents/blackduck.agent.md`.
- Credentials: `../../commands/blackduck-login.md`.

Read the selected file explicitly before acting. Supporting skills are not automatically invoked; read their files only after selection. Resolve paths from this file, not from the user's working directory. If a file is missing, report it. Do not search unrelated plugins.

For delegation, use the host's agent tool. Let the selected orchestrator load its own subagents; do not read their bodies into the parent context. Pass only the task, scope, identifiers, required evidence, and approval state. Return concise results with artifact paths and blockers, not raw tool logs.

Keep credential and write approval gates. Never treat routing as approval. Verify each approved write with a read. Load linked references only when needed for the current operation. Reuse instructions already present in context.
