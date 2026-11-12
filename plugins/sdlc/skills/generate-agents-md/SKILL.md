---
name: generate-agents-md
disable-model-invocation: true
description: "Create or update AGENTS.md files after project setup or structural changes; delegates root/subfolder drafts to /init and verifies them."
---

Use **ASD-STE100 Simplified Technical English** for all end-user replies and artifact text. First read and follow [the output language rules](../../references/output-language.md), including for delegated work.

# Generate AGENTS.md

Create or update project AGENTS.md files.

## Steps

1. Identify candidate scopes.
   - Inspect the repository structure and existing AGENTS.md files.
   - Load `references/full-reference.md` for candidate rules and verification details.
   - Completion criterion: root/subfolder targets are listed.

2. Generate or update drafts.
   - Use `/init` where available, then prune no-ops and stale context.
   - Completion criterion: each target has a generated or intentionally skipped AGENTS.md.

3. Verify.
   - Check paths, commands, project conventions, and no secret leakage.
   - Completion criterion: changes are summarized with follow-up gaps.
