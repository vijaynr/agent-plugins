---
name: octane-analyse
description: >
  Analyse an ALM Octane backlog item: triage it, fetch details, summarize
  requirements, risks, acceptance criteria, linked work, and open questions.
agent: octane-agent
argument-hint: "<octane-url-or-id>"
---

# Octane Analyse

Use the **octane-agent** orchestrator in `analyse` mode for the supplied Octane item.

If the target item is missing, ask for an Octane URL or work item ID before starting.

Run triage followed by research. Present the resulting `alm_handoff` and stop. Do not plan or implement unless the user explicitly asks.
