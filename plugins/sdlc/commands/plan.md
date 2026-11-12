---
name: plan
description: >
  Create the checklist implementation plan from `SPEC.md`.
argument-hint: "<feature> [constraints]"
---

Use **ASD-STE100 Simplified Technical English** for all end-user replies and artifact text. First read and follow [the output language rules](../references/output-language.md), including for delegated work.

# /plan

First load `using-agent-skills` for the SDLC routing preflight; load `using-agents` only when custom-agent delegation is appropriate. Then use the `ai-sdlc` skill in `plan` mode. Require `SPEC.md`, read `DESIGN.md` when present, then create or update `tasks/PLAN.md` and `tasks/TODO.md` with simple Markdown task checkboxes.
