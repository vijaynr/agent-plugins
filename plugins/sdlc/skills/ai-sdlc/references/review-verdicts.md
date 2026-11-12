# Review Verdicts

Each `/review` reviewer uses a different result scale. Use this table to change the final reviewer result to one consolidated verdict: `APPROVE`, `REQUEST CHANGES`, or `MORE EVIDENCE NEEDED`. Use ASD-STE100 Simplified Technical English for text that you write about the result. See [the output language rules](../../../references/output-language.md).

## Verdict table

| Reviewer | Reviewer result | Consolidated verdict |
|---|---|---|
| `code-reviewer` | `APPROVE` | `APPROVE` |
| `code-reviewer` | `REQUEST CHANGES` | `REQUEST CHANGES` |
| `security-auditor` | `PROCEED` | `APPROVE` |
| `security-auditor` | `PROCEED WITH CONDITIONS` | `REQUEST CHANGES` until each condition has a user waiver; then the orchestrator records `APPROVE` |
| `security-auditor` | `BLOCK` | `REQUEST CHANGES` |
| `test-engineer` | `COVERAGE SUFFICIENT` | `APPROVE` |
| `test-engineer` | `TESTS READY FOR FIX` | `REQUEST CHANGES` |
| `test-engineer` | `READY FOR IMPLEMENTATION` | `REQUEST CHANGES` |
| `test-engineer` | `MORE EVIDENCE NEEDED` | `MORE EVIDENCE NEEDED` |

If `test-engineer` gives a result that is not in this table, use `REQUEST CHANGES`. If `code-reviewer` or `security-auditor` gives a result that is not in this table, use `MORE EVIDENCE NEEDED`.

## Critic status

- When the critic returns `AGREE`, the status is `CONSISTENT`. The consolidated verdict is the value from the table.
- When the critic returns `DISAGREE_EVIDENCE` or `DISAGREE_CONCERN` at `critic_round: 5`, the status is `UNRESOLVED`. The consolidated verdict must not be `APPROVE`.

## Waivers

Only the user can waive a `PROCEED WITH CONDITIONS` condition. The agents cannot. The frozen review copy does not contain waivers, because the user gives them after the critic loop. Thus the critic always returns `REQUEST CHANGES` for this result and lists each condition.

1. After the critic loop, show each condition from the critic result to the user. Do this only when the status is `CONSISTENT`.
2. For each condition that the user waives, add one line under `## Review` in `.features/<feature>/tasks/TODO.md`:

   ```markdown
   - Waiver: <condition> — accepted by <user> on <YYYY-MM-DD>. Reason: <reason>.
   ```

3. Only the orchestrator changes the verdict to `APPROVE`, and only when each condition has a waiver line. Record the critic verdict and the final verdict. If one condition has no waiver, record `REQUEST CHANGES`.
4. The waiver lines belong to the review with the same `manifest_id`. They do not make a new manifest.

## Ship rule

`/ship` accepts only a review that has the status `CONSISTENT` and the consolidated verdict `APPROVE`. The review must use the current `manifest_id`.
