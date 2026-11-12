---
name: "ai-sdlc"
disable-model-invocation: true
description: "Simple, branch-based AI SDLC workflow using a living SPEC.md and checklist task files."
---

Use **ASD-STE100 Simplified Technical English** for all end-user replies and artifact text. First read and follow [the output language rules](../../references/output-language.md), including for delegated work.

# AI SDLC

Use this skill for the project lifecycle:

```text
spec (including focused research) → design → plan → build → review → ship
```

The workflow keeps the useful discipline of spec-driven development without
turning every phase into a separate report-management exercise.

## Workspace

Every feature lives in a dedicated branch and feature folder:

```text
.features/<feature>/
├── SPEC.md
├── DESIGN.md                   # optional; for substantial technical designs
├── status.json                 # internal state only
└── tasks/
    ├── PLAN.md                # implementation plan and task definitions
    └── TODO.md                # progress, verification, and review notes
```

`SPEC.md`, optional `DESIGN.md`, `tasks/PLAN.md`, and `tasks/TODO.md` are living
Markdown documents. Update them in place as understanding changes. Keep research
in `SPEC.md`; do not create separate requirements, research, implementation-log,
or verification-report files.

Use ordinary headings, bullets, and `- [ ]` / `- [x]` checkboxes. Do not invent
or require `REQ-*`, `AC-*`, `DES-*`, `PLAN-*`, `STAGE-*`, `EV-*`, or other
traceability IDs.

## Routing preflight

Before every SDLC phase, use `using-agent-skills` to route the current task.
Read it only if its instructions are not already in context. Route
using the feature request and the available `SPEC.md`, `DESIGN.md`, plan, code,
and prior notes. Load the smallest selected supporting skill or companion-plugin
skill before acting; keep `ai-sdlc` as the owner of lifecycle artifacts, status,
commits, and shipping.

When the task is best served by a custom agent—such as independent review,
test/security analysis, multi-workspace research, or a companion-plugin
orchestrator—also load `using-agents` to discover and select that agent. Do not
use agent discovery for ordinary skill-only guidance.

Record material routed decisions and results in the existing phase artifact:
`SPEC.md`/`DESIGN.md` for research and design, `tasks/PLAN.md` for planned
specialist work, and `tasks/TODO.md` for build/review evidence. Do not create a
routing report.

## Phase responsibilities

### `/spec`

1. Always prompt the user about workspace isolation: ask whether to create a dedicated git worktree (`../<repo>.worktrees/<feature>`) or continue in the current working tree. Initialize or reuse the feature workspace, create the worktree or branch as selected, and record the worktree path in `status.json`. When a worktree is created, execute all subsequent SDLC phases inside that worktree path.
2. Ask focused questions about objective, users, behavior, boundaries, and
   acceptance criteria.
3. Inspect the immediately relevant code, tests, configuration, documentation,
   and integrations.
4. Create or update `SPEC.md` with:
   - Objective
   - Users and use cases
   - Requirements
   - Acceptance criteria
   - Constraints and boundaries
   - Testing expectations
   - Open questions
   - `## Research` with concise evidence, paths, conventions, risks, and unknowns
5. Record resolved decisions in the spec rather than creating a research file,
   then ask for confirmation before moving to design.

### `/research` (optional deep research)

Use this only when the focused research in `/spec` is insufficient, such as for
multi-workspace investigation, complex integrations, or material unknowns.

1. Require `SPEC.md`.
2. Inspect the relevant code, tests, configuration, documentation, and
   integrations.
3. Update `## Research` in `SPEC.md` with concise additional evidence, paths,
   conventions, risks, and unknowns.
4. Record resolved decisions in the spec rather than creating a research file.

#### Multi-workspace research (`--workspaces`)

Use this procedure when the user gives `--workspaces <path> [<path> ...]`.
Without `--workspaces`, do steps 1–4 above.

1. Make one `sdlc_research_request` for each workspace path. Do not put two
   workspaces in one request:

   ```yaml
   sdlc_research_request:
     feature: <feature slug>
     spec_path: .features/<feature>/SPEC.md
     workspace_path: <one path from --workspaces>
     workspace_label: <short unique label, for example the folder name>
     focus: <focus from the user, or empty>
   ```

2. Send each request to the `codebase-researcher` agent. The requests are
   independent. You can send them in parallel.
3. Each agent returns one `### Workspace: <label>` section. Add each section
   under `## Research` in `SPEC.md`. Replace an older section that has the same
   label. Do not change other research text.
4. If a section has the status `partial` or `blocked`, keep it and keep the
   sections from the other workspaces. Add the gap to `## Open questions`.
5. If an agent returns no usable section, do not make one. Record the workspace
   path and the error in `## Open questions`.
6. After all sections are added, add the risks and decisions that affect more
   than one workspace to the research summary.

### `/design`

1. Require `SPEC.md` and its research section.
2. Keep a concise `## Design` summary in `SPEC.md` with the chosen approach and
   key tradeoffs.
3. For substantial designs (for example, cross-service architecture, API
   contracts, data models, security boundaries, or diagrams), also create or
   update `DESIGN.md` with the detailed approach, alternatives, tradeoffs, data
   flow, and security implications. Link it from the `SPEC.md` summary.
4. Keep the design proportional to the change. Do not create diagrams unless
   they clarify a meaningful boundary or flow.

### `/plan`

1. Require `SPEC.md`; read `DESIGN.md` when it exists.
2. Create or update `tasks/PLAN.md`.
3. Break implementation into small, independently verifiable tasks. Each task
   should include a short description, acceptance checkboxes, verification
   commands, dependencies, and likely files.
4. Prefer vertical slices and risk-first ordering. Avoid IDs and redundant
   traceability tables.
5. Create or reset `tasks/TODO.md` with the task checklist and a `## Notes`
   section for decisions and blockers.

### `/build`

Default behavior implements the next unchecked task and then stops. The agent
must:

1. Read the task and relevant context.
2. Write or update a focused failing test when behavior changes.
3. Implement the smallest change that makes the test pass.
4. Run focused tests, then applicable project checks/build.
5. Update the checkbox and verification notes in `tasks/TODO.md`.
6. Commit the task with a descriptive Conventional Commit.

`/build --auto` may execute all remaining tasks in dependency order, but it
must keep the same test → verify → update → commit loop and stop on ambiguity,
failed checks, risky changes, or an unapproved scope expansion.

### `/review`

Review is diagnostic and does not modify product code. It uses a minimal
adversarial-review inner loop: one focused reviewer and `review-critic`. The
critic receives the same frozen context and audits the review through explicit,
evidence-grounded disagreement. This follows the reviewer–critic protocol in
[Qiu et al., *Adversarial Review* (2026)](https://arxiv.org/abs/2608.18167).

1. Read `SPEC.md`, `DESIGN.md` when it exists, `tasks/PLAN.md`, `tasks/TODO.md`,
   and the code diff. Check each acceptance criterion literally and run
   applicable gates: formatting, lint, type/static analysis, tests, build,
   security/dependency checks, and manual/browser checks where relevant.
2. Freeze the artifact version and all review context before delegating. Create
   a review manifest containing the base `HEAD`, exact `git diff --binary HEAD`
   output (including staged and unstaged changes), relevant untracked paths and
   contents, and the exact `SPEC.md`, optional `DESIGN.md`, `tasks/PLAN.md`, and
   `tasks/TODO.md` content. Give this immutable manifest—not a newly-read
   worktree—to both agents as the `sdlc_review_request` block in
   [the review request reference](references/review-request.md). Put the step 1
   check results in `gate_results`, so that the agents do not run the same
   checks again. Record the `manifest_id` in `tasks/TODO.md`. Select
   `code-reviewer` by default; select `test-engineer` or `security-auditor` only
   when that focused review is the material need. Set `reviewer_role` to the
   selected agent and `critic_round` to `0` for the first review.
3. The reviewer produces an evidence-based review. Normalize its material
   findings for the critic without changing the source report: code Critical and
   Important findings; security Critical, High, and Medium findings; and test
   gaps that affect the test report conclusion. Invoke `review-critic` with the
   same `sdlc_review_request`, that review, and `critic_round: 1`. The critic
   must return `AGREE`, `DISAGREE_EVIDENCE`, or `DISAGREE_CONCERN` and a
   consolidated review result.
4. On either disagreement, send the critic assessment to the same reviewer for
   a code-grounded revision or rebuttal, then have the critic audit the revised
   review. Increase `critic_round` by 1 for each critic audit. Do not edit the
   artifact during this exchange. Stop when the critic agrees or after
   `critic_round: 5`; at the cap, preserve the unresolved evidence rather than
   forcing consensus.
5. Map the final reviewer result with
   [the review verdict table](references/review-verdicts.md). For a
   `security-auditor` `PROCEED WITH CONDITIONS` result, the critic returns
   `REQUEST CHANGES`. If the status is `CONSISTENT`, ask the user about each
   condition. Record each waiver and the final verdict as the table reference
   specifies.
6. Add a `## Review` section to `tasks/TODO.md` containing:
   - The `manifest_id` and checks run with results
   - Reviewer findings, the critic's status, and the mapped consolidated verdict
   - Acceptance-criteria status, remaining work, and explicit waivers
   - Recommendation: `/build` for `REQUEST CHANGES`, `MORE EVIDENCE NEEDED`, or
     unresolved evidence, `/refine` for requirements/design gaps, or `/ship`
     only for `CONSISTENT` with the consolidated verdict `APPROVE`

Do not require unrelated specialist reports. The reviewer–critic pair is the
review protocol; invoke other specialist skills only when the change needs them.

### `/ship`

1. Require a passing, current review recorded in `tasks/TODO.md`. A passing
   review has the status `CONSISTENT` and the consolidated verdict `APPROVE`, as
   [the review verdict table](references/review-verdicts.md) specifies.
2. Recheck the working tree, branch, scope, and applicable gates.
3. Push the feature branch and create or reuse the GitLab merge request after
   confirmation, unless an explicit auto mode allows it.
4. Record the MR link and final outcome in `tasks/TODO.md` and `status.json`.

## Status and drift

`status.json` is compact internal state used by commands and resume/status
helpers. It may record phase, timestamps, blockers, artifact hashes, git state,
and the latest verification summary. It must not duplicate the contents of the
Markdown documents. The status updater locks each update across processes and
replaces `status.json` atomically.

Use the helpers when useful:

```bash
python skills/ai-sdlc/scripts/update_status.py show .features/<feature> --create
python skills/ai-sdlc/scripts/detect_drift.py .features/<feature>
```

Drift checks should focus on missing/stale `SPEC.md`, optional `DESIGN.md` when
referenced by the spec or status, task files, working-tree state, expected scope,
and review freshness. They must not perform ID-based traceability validation.

## Guardrails

- Ask before destructive actions, branch changes, dirty-tree ambiguity,
  security-sensitive changes, public API changes, and merge-request creation.
- Keep the feature branch and folder isolated from unrelated work.
- Keep documents concise and current; update rather than append duplicate prose.
- Prefer the simplest implementation that satisfies the spec.
- Never claim verification passed without command output or other evidence.
