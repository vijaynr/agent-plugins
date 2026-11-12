---
name: using-gitlab
description: Route GitLab issue, merge-request, pipeline, API, and credential requests. Use for GitLab work before loading API or agent instructions.
---

# GitLab Router

Select one route. Do not load all skills, agent bodies, examples, or references.

- API reads or a narrow question: [gitlab](../gitlab/SKILL.md).
- Issue/MR triage, analysis, planning, or approved updates: `../../agents/gitlab-agent.agent.md`.
- Credentials: `../../commands/gitlab-login.md`.

Read the selected file explicitly before acting. Supporting skills are not automatically invoked; read their files only after selection. Resolve paths from this file. Report missing files instead of scanning unrelated plugins.

Use the host's agent tool for delegation. Let the orchestrator load its subagents; do not load their bodies into the parent context. Pass only the task, scope, identifiers, required evidence, and approval state. Request a concise result with artifact paths and blockers, not raw tool logs.

Keep profile restrictions and write approval gates. Never treat routing as approval. Verify approved writes with a read. Load references only for the current operation. Reuse instructions already in context.
