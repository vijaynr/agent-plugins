---
name: update
description: >
  Plan and apply approved GitLab updates to a MR or issue. Supports adding
  notes, updating title/description/state/labels/draft, and setting reviewers
  or assignees.
agent: gitlab-agent
argument-hint: "<gitlab-url> [--action <add-note|update-mr|update-issue|set-reviewers|set-assignees>]"
---

# GitLab Update

Plan and apply approved GitLab updates using the **gitlab-agent** orchestrator.

## Required input

| Argument | Required | Notes |
|---|---|---|
| `<gitlab-url>` | ✅ | Full GitLab MR or issue URL |
| `--action` | Optional | Hint the intended action; omit to let the orchestrator infer |

## Workflow

Run in **update** mode:

1. **Triage** — resolve identifiers and classify item.
2. **Research** — fetch current state and open discussions.
3. **Collect actions** — gather all intended GitLab changes in a table.
4. **Confirmation gate** — present the table and ask for explicit approval.
5. **Apply** — invoke **gl-operator** sequentially for each confirmed action.
6. **Verify** — read back each changed item and report verification status.

## Guardrails

- **Never write** without first presenting the full action table and receiving
  explicit user confirmation.
- Invoke **gl-operator** for one action at a time.
- Surface any write error verbatim and stop further writes.
