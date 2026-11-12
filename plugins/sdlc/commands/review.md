---
name: review
description: >
  Review the implementation against `SPEC.md`, optional `DESIGN.md`, and the task checklists.
argument-hint: "<feature> [--traceability-only]"
---

Use **ASD-STE100 Simplified Technical English** for all end-user replies and artifact text. First read and follow [the output language rules](../references/output-language.md), including for delegated work.

# /review

First load `using-agent-skills` for the SDLC routing preflight, then load `using-agents`: `/review` uses the `code-reviewer` and `review-critic` adversarial-review pair (or `test-engineer`/`security-auditor` as the focused reviewer when appropriate). Then use the `ai-sdlc` skill in `review` mode. Read `SPEC.md`, `DESIGN.md` when present, `tasks/PLAN.md`, `tasks/TODO.md`, and the code diff; run applicable project gates; keep that artifact version frozen while the reviewer–critic loop runs; send both agents the `sdlc_review_request` block with `gate_results` and `critic_round`; map the final result with the `ai-sdlc` review verdict table; and record the critic's consolidated result and concise findings in `tasks/TODO.md`.

`/review` is diagnostic for product code. If fixes are needed, route the user back to `/build`.
