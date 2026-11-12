---
name: spec
description: >
  Create or update the living SDLC specification with focused codebase research.
argument-hint: "<feature> [--worktree [path]] [context]"
---

Use **ASD-STE100 Simplified Technical English** for all end-user replies and artifact text. First read and follow [the output language rules](../references/output-language.md), including for delegated work.

# /spec

First load `using-agent-skills` for the SDLC routing preflight; load `using-agents` only when custom-agent delegation is appropriate. Then use the `ai-sdlc` skill in `spec` mode. Prompt the user about worktree creation, resolve or create the worktree or branch and `.features/<feature>` workspace, gather requirements and focused evidence from the relevant codebase, then create or update `SPEC.md` and its `## Research` section.
