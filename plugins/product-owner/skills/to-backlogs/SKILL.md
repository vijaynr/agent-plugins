---
name: to-backlogs
disable-model-invocation: true
description: Break a PRD, feature description, plan, or backlog item into independently grabbable backlog items/user stories using tracer-bullet vertical slices.
---

# To Backlogs

Break a PRD, feature, plan, or product idea into independently grabbable backlog
items or user stories using vertical slices (tracer bullets). This skill is adapted
from Matt Pocock's `to-issues` engineering skill and repurposed for this
repository's product owner workflows.

## Process

### 1. Gather context

Work from whatever is already in the conversation context. If the user passes
an issue reference, Octane URL, document, file path, or PRD, fetch/read it and
include relevant body text and comments.

If useful and available, lightly explore the codebase to understand current
product vocabulary, existing seams, and constraints. Issue titles and
descriptions should use the project's domain glossary and avoid stale file-path
specifics.

For UI-facing work without approved UX designs, or when the supplied design
leaves important behavior undefined, explicitly read
[ui-requirements](../ui-requirements/SKILL.md) unless it is already in context.
Use its mandatory language rules, UI-state checks, and engineering handoff
sections for each affected story. Keep the approval sequence below. A mockup
alone does not define expected behavior.

### 2. Draft vertical slices

Break the plan into **tracer bullet** issues/stories. Each issue should be a
thin vertical slice that cuts through all needed integration layers end-to-end,
not a horizontal slice for a single layer.

Vertical-slice rules:

- Each slice delivers a narrow but complete user-visible outcome.
- A completed slice is demoable or verifiable on its own.
- Do **not** create horizontal slices such as "schema only", "API only", "UI only",
  or "tests only" unless the user explicitly asks for technical tasks.
- Put prerequisite/prefactoring/enabler work first only when it is necessary to
  make later slices safe or feasible.
- Keep slices small enough for independent ownership, but not so small that
  they stop delivering value.

### 3. Present the proposed breakdown

Present the proposed breakdown as a numbered list. For each slice, show:

- **Title**: short descriptive name
- **Blocked by**: which other slices, if any, must complete first
- **User stories covered**: which PRD/user stories this addresses, if source
  material has them
- **User-visible outcome**: what can be demonstrated or verified when complete

Ask the user:

- Does the granularity feel right: too coarse, too fine, or about right?
- Are the dependency relationships correct?
- Should any slices be merged, split, removed, or reprioritized?

Iterate until the user approves the breakdown.

### 4. Write issue/story bodies

For each approved slice, use this template. For UI work covered by
`ui-requirements`, expand **What to build** with its applicable UI sections.
Keep Parent, Acceptance criteria, and Blocked by. Omit states that do not apply.
Mark unresolved product decisions and affected stories as draft or blocked;
do not invent permission, deletion, security, compliance, or compatibility rules.

```markdown
## Parent

A reference to the parent feature/PRD/tracker item, if one exists. Omit this
section if there is no parent reference.

## User story

As an <actor>, I want <capability>, so that <benefit>.

## What to build

A concise description of this vertical slice. Describe the end-to-end behavior,
not layer-by-layer implementation.

Avoid specific file paths or code snippets because they go stale quickly.
Exception: if a prototype produced a snippet that encodes a decision more
precisely than prose can, inline only the decision-rich part and explain why it
is included.

## Acceptance criteria

- [ ] Given <context>, when <action>, then <observable result>.
- [ ] <Additional criterion.>

## Blocked by

- A reference to the blocking ticket/story, if any.

Or:

None - can start immediately.

## Notes

Optional assumptions, constraints, edge cases, or follow-up considerations.
```

Before returning UI stories or preparing a tracker payload, apply the
`ui-requirements` final review and mandatory rewrite to the actual story bodies
and acceptance criteria. Use short active sentences, one main action or
condition per sentence, consistent product terms, and observable behavior.

### 5. Optional publishing / backlog maintenance

If the user asked to publish or maintain issues/stories in ALM Octane, GitLab,
GitHub, or another tracker:

1. Show the final issue/story list and bodies.
2. Ask for explicit confirmation before any write.
3. Publish in dependency order, blockers first, so later stories can reference
   real issue IDs.
4. Verify each created item with a read command.
5. Report IDs/URLs and any failures verbatim.

For ALM Octane specifically, the product owner workflow may create/update a
feature, create/update user stories under that feature, list child backlog
items, and delete child backlog/user-story items after explicit confirmation.
Use the `alm-octane` skill for exact commands and verification.

Do **not** close, delete, or modify a parent item unless the user explicitly
asks and confirms that separate action.

## Guardrails

- Do not publish tracker items without explicit confirmation.
- Do not split only by technical layer when asked for product/user stories.
- Do not invent dependencies; mark assumptions clearly.
- Keep issue bodies concise and ready for independent execution.
