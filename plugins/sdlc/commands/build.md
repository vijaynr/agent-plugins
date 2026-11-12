---
name: build
description: >
  Implement checklist tasks incrementally; one task by default, all remaining tasks with --auto.
argument-hint: "<feature> [--auto]"
---

Use **ASD-STE100 Simplified Technical English** for all end-user replies and artifact text. First read and follow [the output language rules](../references/output-language.md), including for delegated work.

# /build

First load `using-agent-skills` for the SDLC routing preflight; load `using-agents` only when custom-agent delegation is appropriate. Then use the `ai-sdlc` skill in `build` mode. Read the next unchecked task from `tasks/PLAN.md`, implement and verify it, then update `tasks/TODO.md` and commit the task.
