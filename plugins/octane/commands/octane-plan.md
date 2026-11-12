---
name: octane-plan
description: >
  Plan an ALM Octane backlog implementation: triage, analyse, then produce a
  concrete proposed implementation approach after confirmation.
agent: octane-agent
argument-hint: "<octane-url-or-id>"
---

# Octane Plan

Use the **octane-agent** orchestrator in `plan` mode for the supplied Octane item.

If the target item is missing, ask for an Octane URL or work item ID before starting.

Run triage and research, then ask for confirmation before planning. After planning, present the proposed approach and stop. Do not implement unless the user explicitly approves implementation.
