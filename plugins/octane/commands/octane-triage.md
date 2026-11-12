---
name: octane-triage
description: >
  Triage an ALM Octane backlog item: classify severity, priority, complexity,
  scope, and recommended next action without planning or implementation.
agent: octane-agent
argument-hint: "<octane-url-or-id>"
---

# Octane Triage

Use the **octane-agent** orchestrator in `triage` mode for the supplied Octane item.

If the target item is missing, ask for an Octane URL or work item ID before starting.

Return the `octane_triage` block and stop. Do not continue to analysis, planning, or implementation unless the user explicitly asks.
