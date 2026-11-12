---
name: git-workflow-guidelines
disable-model-invocation: true
description: "Generic Git branch, commit, and pull/merge request guidance. Follow repository policy first."
---

Use **ASD-STE100 Simplified Technical English** for all end-user replies and artifact text. First read and follow [the output language rules](../../references/output-language.md), including for delegated work.

# Git Workflow Guidelines

Use this skill to create branches, commits, or pull/merge requests. These are portable defaults, not universal rules. Read the repository's contributor guide, branch policy, and request template first. Repository policy takes precedence. Do not rename existing branches as a side effect.

## Select the base

- Verify the authoritative remote and its default branch. Do not assume `main`, `master`, or `origin`.
- Use the requested release or maintenance branch when the task requires it.
- Inspect status, worktrees, and existing task branches before any write. Preserve unrelated work.
- Fetch when permitted. Pin the selected base commit. Do not pull, reset, or switch an occupied checkout to refresh it.
- Keep each task isolated in a short-lived branch and, when required, a worktree.

## Branch names

Use the repository convention. If it has none, use a descriptive type and a short kebab-case summary:

```text
feature/add-export
fix/retry-timeout
chore/update-dependencies
docs/setup-guide
refactor/profile-loader
```

An issue ID is optional unless local policy requires it. Use only a verified ID, for example `fix/123-retry-timeout`. Do not invent a backlog ID or require a particular issue tracker. Check proposed names with `git check-ref-format --branch <name>`.

Branch names do not imply a CI trigger. Inspect the actual pipeline configuration. Keep branches focused and short-lived. Use release branches only when the project needs separate stabilization or maintenance.

## Commits

Keep commits small and coherent. Include only task-owned files. Review the staged diff and run the applicable checks before committing. Never commit secrets or unrelated changes.

If the repository has no message convention, use Conventional Commits:

```text
feat: add export command
fix(auth): reject missing endpoint
docs: explain local installation
```

Use `!` or a `BREAKING CHANGE:` footer for incompatible changes. Explain the reason and migration steps in the body when needed. Commit only when the user or active workflow authorizes it.

## Pull or merge requests

Use a short, factual title. Follow local title rules; otherwise use an outcome-focused title or the commit convention. Link verified issue IDs when available. No tracker-specific prefix is required by this skill.

Use the repository template. If it has none, include:

```markdown
## Summary
- What changed and why.

## Validation
- Commands run and actual results.
- Checks not run and the reason.

## Compatibility and risk
- Breaking changes, migration steps, and rollback limits.

## Related work
- Verified issue or dependent request links, if any.
```

Keep the diff limited to the task. Verify source and target projects and branches. Reuse a matching existing request. Push and create requests only when authorized. Verify the published diff with a read. Do not merge automatically.

## Integration and releases

Use the project's merge strategy: squash, merge commit, or rebase. No single strategy applies to all projects. Never rewrite shared history or force-push without explicit approval. Do not delete branches or worktrees without authorization.

Use the project's version policy. Semantic Versioning is a useful default for a versioned public API: major for incompatible changes, minor for compatible features, patch for compatible fixes. Do not impose a quarterly release scheme. Tags and releases need separate authorization.

## Use with SDLC

- `init-workspace`: resolve the base and validate the branch name before creation.
- `ai-sdlc ship`: apply project-specific request rules and publication gates.

## References

- [GitHub flow](https://docs.github.com/en/get-started/using-github/github-flow) — one example of a branch-and-review workflow, not a required host.
- [Conventional Commits 1.0.0](https://www.conventionalcommits.org/en/v1.0.0/).
- [Semantic Versioning 2.0.0](https://semver.org/).
