---
name: ship
description: >
  Check final readiness from the living SDLC documents and create/reuse a GitLab merge request.
argument-hint: "<feature> <target-branch> [--auto|--force-review]"
---

Use **ASD-STE100 Simplified Technical English** for all end-user replies and artifact text. First read and follow [the output language rules](../references/output-language.md), including for delegated work.

# /ship

First load `using-agent-skills` for the SDLC routing preflight; load `using-agents` only when custom-agent delegation is appropriate. Then use the `ai-sdlc` skill in `ship` mode. Require a passing review in `tasks/TODO.md`: the status must be `CONSISTENT` and the consolidated verdict must be `APPROVE`, as `skills/ai-sdlc/references/review-verdicts.md` specifies. Recheck applicable gates, and create or reuse the GitLab merge request after confirmation.
