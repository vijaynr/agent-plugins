---
name: octane-fix
description: >
  Implement an ALM Octane backlog item through the Octane orchestrator:
  triage, analyse, plan, confirm, implement, verify, and report handoff.
agent: octane-agent
argument-hint: "<octane-url-or-id>"
---

# Octane Fix

Use the **octane-agent** orchestrator in `fix` mode for the supplied Octane item.

If the target item is missing, ask for an Octane URL or work item ID before starting.

Run the gated workflow exactly: triage → research → Gate A confirmation → plan → Gate B approval → implementation. Never implement without the required approval gates.
