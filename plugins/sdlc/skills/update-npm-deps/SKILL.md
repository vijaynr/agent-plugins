---
name: update-npm-deps
disable-model-invocation: true
description: "Audit and upgrade npm dependencies in safe phases with breaking-change research and validation."
---

Use **ASD-STE100 Simplified Technical English** for all end-user replies and artifact text. First read and follow [the output language rules](../../references/output-language.md), including for delegated work.

# Update npm Dependencies

Audit and upgrade npm dependencies in safe phases.

## Steps

1. Baseline.
   - Inspect package manager, lockfile, scripts, current install state, and outdated/audit output.
   - Load `references/full-reference.md` for phased upgrade rules and validation details.
   - Completion criterion: dependency candidates, risks, and validation commands are known.

2. Plan phases.
   - Group patch/minor updates before majors and research breaking changes for risky packages.
   - Completion criterion: each phase has packages, rationale, and rollback notes.

3. Apply and validate.
   - Install one phase at a time; run tests/build/lint after each phase.
   - Completion criterion: lockfile/package changes and validation results are reported, with blockers isolated.
