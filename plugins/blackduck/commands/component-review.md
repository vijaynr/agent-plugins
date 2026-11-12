---
name: component-review
description: >
  Reviews and updates unreviewed Black Duck BOM components one at a time.
  For each component, determines the correct usage and license, applies the
  update, and verifies the result before moving on.
agent: blackduck
argument-hint: "<project> <version> [--usage DYNAMICALLY_LINKED|STATIC_LINKED|SOURCE_CODE|DEV_TOOL|SEPARATE_WORK|MERELY_AGGREGATED]"
---

# Black Duck Component Review

Review and update all unreviewed BOM components for a Black Duck project
version. Use the **blackduck** orchestrator to coordinate all subagents.

## Required input

If the user typed a prompt argument, parse it for:

| Argument | Required | Notes |
|---|---|---|
| `<project>` | ✅ | Black Duck project name (exact match) |
| `<version>` | ✅ | Black Duck version name (exact match) |
| `--usage` | Optional | Default usage to apply when not otherwise determinable (e.g. `DYNAMICALLY_LINKED`). If not supplied, the orchestrator will ask per component when usage is ambiguous. |

If `<project>` or `<version>` are missing, use `#tool:vscode/askQuestions`
to ask for them before starting.

## Workflow

Run the full **Component Review Workflow** from the blackduck orchestrator:

1. **Discovery** — resolve project + version to exact API hrefs.
2. **List unreviewed components** — fetch all components with
   `reviewStatus = NOT_REVIEWED`. Present a count and the component list
   before proceeding. If zero, report and stop.
3. **Per-component update loop** — for each component, **one at a time**:
   a. Display component details: name, version, current license, match
      type, risk profiles (license / operational / security).
   b. Determine usage:
      - Use `--usage` if provided and usage is not already set.
      - If usage cannot be inferred and `--usage` was not supplied, ask
        the user before updating.
   c. Resolve the correct license via `bd-component-updater` (it
      will run `list-licenses` and web-search if needed).
   d. Invoke `bd-component-updater` with the approved
      `reviewStatus`, `usage`, and `license`.
   e. Report the outcome (`ok` / `httpStatus` / `verifiedReviewStatus`).
   f. Update the running progress table before moving to the next component.
4. **Summary** — emit the completed progress table and a list of any
   skipped components with their exact blocker or open question.

## Progress table (maintained throughout)

```
| Component | Version | Match Type | Usage Applied | License Applied | Verified | Notes |
```

## Output

Final progress table plus:
- **Updated**: count of components successfully marked REVIEWED.
- **Skipped**: list of components not updated, with the exact reason (e.g.
  ambiguous license, usage unknown, API error).

## Guardrails

- Process one component at a time — never batch updates.
- Never guess a usage value; always ask if `--usage` was not provided and
  usage cannot be inferred from the match type or package metadata.
- Never guess a license name; always run `list-licenses` first. If no
  matching license is found, leave the existing license unchanged and add
  a comment explaining the situation.
- After every write, verify with `list-components` before continuing to
  the next component.
- Parse all subagent JSON output; surface errors explicitly.
