---
name: gitlab-analyse
description: >
  Analyse a GitLab MR or issue in depth. Fetches discussions, pipeline status,
  failed jobs, and issue links, then returns a structured handoff block.
agent: gitlab-agent
argument-hint: "<gitlab-url>"
---

# GitLab Analyse

Run a full analysis of a GitLab merge request or issue using the
**gitlab-agent** orchestrator.

## Required input

| Argument | Required | Notes |
|---|---|---|
| `<gitlab-url>` | ✅ | Full GitLab MR or issue URL |

If the URL is missing, ask for it before starting.

## Workflow

Run in **analyse** mode:

1. **Triage** — delegate to **gl-triager** to resolve identifiers and classify.
2. **Research** — delegate to **gl-researcher** to fetch discussions, pipelines,
   jobs, and issue links.
3. Return the `gitlab_handoff` block and full research sections.
4. Stop.

## Output

Structured `gitlab_handoff` block, then:

- `## Requirement summary`
- `## Acceptance / success criteria`
- `## Discussion and evidence`
- `## Pipeline status` (MRs only)
- `## Open questions`

## Guardrails

- Analyse mode only — do not start planning or perform writes.
- Never write comments, labels, assignees, or state in this phase.
