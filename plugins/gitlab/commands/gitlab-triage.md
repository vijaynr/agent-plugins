---
name: gitlab-triage
description: >
  Triage a GitLab MR or issue. Parses identifiers, classifies the item,
  assesses complexity and actionability, and returns a structured triage block.
agent: gitlab-agent
argument-hint: "<gitlab-url>"
---

# GitLab Triage

Triage a GitLab merge request or issue using the **gitlab-agent** orchestrator.

## Required input

If the user typed a prompt argument, parse it for:

| Argument | Required | Notes |
|---|---|---|
| `<gitlab-url>` | ✅ | Full GitLab MR or issue URL |

If the URL is missing, ask for it before starting.

## Workflow

Run in **triage** mode:

1. Delegate to **gl-triager** with the provided URL.
2. Return the `gitlab_triage` block and a short Triage notes paragraph.
3. Stop.

## Output

```yaml
gitlab_triage:
  gitlab_url:
  project_id:
  item_type:         # merge-request | issue
  item_iid:
  title:
  state:
  complexity_hint:   # small | medium | large
  actionable:        # true | false
  skip_reason:
  recommended_start: # research | plan | update
```

## Guardrails

- Triage mode only — do not start research, planning, or writes.
- If the item is closed/merged, set `actionable: false` with a reason.
