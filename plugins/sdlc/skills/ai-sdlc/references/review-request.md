# Review Request

The `/review` orchestrator sends this block to the reviewer and to `review-critic`. Use ASD-STE100 Simplified Technical English for all text in the block that you write. See [the output language rules](../../../references/output-language.md).

## Input block

```yaml
sdlc_review_request:
  manifest_id: <unique identifier for this frozen review copy>
  base_head: <commit SHA of HEAD when the copy was frozen>
  diff: |
    <exact output of `git diff --binary HEAD`, with staged and unstaged changes>
  untracked:
    - path: <repository-relative path>
      content: |
        <file content>
  artifacts:
    spec: <content of SPEC.md>
    design: <content of DESIGN.md, or empty>
    plan: <content of tasks/PLAN.md>
    todo: <content of tasks/TODO.md>
  reviewer_role: code-reviewer | test-engineer | security-auditor
  critic_round: <0 for the reviewer's first review; 1–5 for critic audits>
  gate_results:
    - check: <name, for example tests or lint>
      command: <exact command>
      result: pass | fail | not run
      summary: <short result or reason>
  critic_assessment: <previous critic report, only for a reviewer response>
  review: <current reviewer report, only for a critic audit>
```

## Rules for the frozen review copy

1. The manifest is the only source for changed content. Use `diff`, `untracked`, and `artifacts`. Do not review changed content from the current worktree.
2. You can read files that the diff does not change to get more context.
3. Before you use a file from the worktree, make sure that the diff does not change it. If the worktree is different from the manifest for a changed path, report the difference as a review limit. Do not review the new content.
4. Use `gate_results` for the check status in your report. Do not run the same checks again.
5. You can run one focused, read-only check to get evidence for a finding. State the command and the reason in the report.
6. If `sdlc_review_request` is missing or a required field is empty, report the missing field. Do not guess the frozen content.

## Orchestrator rules

- Make the manifest one time, before the first review. Use the same `manifest_id` for all rounds.
- Set `critic_round` to `0` for the first review. Increase it by 1 for each critic audit. The maximum value is `5`.
- Copy the results of the `/review` step 1 checks into `gate_results`.
- Map the final result with [the review verdict table](review-verdicts.md).
