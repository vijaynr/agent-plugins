---
name: ci-cd-and-automation
disable-model-invocation: true
description: Automates CI/CD pipeline setup in a stack-neutral way. Use when setting up or modifying build and deployment pipelines, automating quality gates, configuring test runners in CI, or establishing deployment/rollback strategies.
---

Use **ASD-STE100 Simplified Technical English** for all end-user replies and artifact text. First read and follow [the output language rules](../../references/output-language.md), including for delegated work.

# CI/CD and Automation

## Overview

Automate quality gates so no change reaches production without repeatable verification. This skill is stack-neutral: use the project's actual package manager, build tool, test runner, CI platform, and deployment target.

Core principles:

- **Shift left:** Run cheap checks before expensive checks.
- **Faster is safer:** Small, frequent, verified changes are easier to debug and roll back.
- **CI is the source of truth:** Local checks are useful; merge gates must be automated.
- **Deployment must be reversible:** Every release needs a rollback or disable path.

## When to Use

- Setting up a new CI pipeline
- Adding or changing automated checks
- Debugging CI failures
- Introducing deployment automation
- Adding branch protection, release gates, or rollback procedures

## Generic Quality Gate Pipeline

Every change should pass the smallest applicable version of this sequence:

```text
Change opened
  -> format/style check
  -> static analysis / lint
  -> compile / type check, if applicable
  -> unit tests
  -> integration tests
  -> package/build artifact
  -> security/dependency/license scan, if applicable
  -> end-to-end or smoke tests, if applicable
  -> deploy to staging/preview
  -> release gate
```

Do not skip a failed gate. Fix the cause, quarantine only with an owner and expiry, or revert.

## Pipeline Design Steps

1. **Discover project commands.** Read existing docs/config and use actual commands, not assumptions.
2. **Classify checks by cost.** Fast deterministic checks first; slow/flaky checks later or scheduled.
3. **Make artifacts reproducible.** Pin tool versions, use lockfiles where the ecosystem supports them, and build from clean environments.
4. **Separate verification from deployment.** Merging and deploying may share artifacts, but deployment needs explicit environment controls.
5. **Protect secrets.** Store credentials in the CI/secrets manager, never in repo files or logs.
6. **Add rollback.** Define how to revert code, disable flags, restore previous artifacts, or roll back infrastructure.

## CI Configuration Pattern

Use this platform-neutral structure and translate it into the project's CI system:

```yaml
pipeline:
  triggers:
    - pull_request
    - main_branch_push
  jobs:
    style:
      steps:
        - checkout
        - setup_toolchain
        - install_dependencies
        - run_format_or_lint_check
    test:
      needs: [style]
      steps:
        - checkout
        - setup_toolchain
        - install_dependencies
        - run_unit_tests
    build:
      needs: [test]
      steps:
        - checkout
        - setup_toolchain
        - install_dependencies
        - build_artifact
        - publish_artifact
    deploy_staging:
      needs: [build]
      when: main_branch_only
      steps:
        - deploy_artifact_to_staging
        - run_smoke_tests
```

Replace placeholder steps with the project's actual commands.

## Handling CI Failures

When CI fails:

1. Capture the first meaningful failure, not just the final summary.
2. Reproduce locally or in a comparable clean environment when possible.
3. Fix the root cause.
4. Add or adjust a guard if the failure exposed missing coverage.
5. Rerun the failed job and any dependent jobs.

Failure routing:

```text
Style/static analysis failure -> fix style, types, or rule violation
Test failure                  -> use debugging-and-error-recovery
Build/package failure         -> inspect toolchain, config, dependency, artifact paths
Deployment failure            -> stop rollout, inspect environment/permissions, use rollback if needed
Flaky failure                 -> isolate, quarantine with owner/expiry only if unavoidable
```

## Deployment Strategies

- **Preview/staging deployments:** Validate changes in a non-production environment.
- **Feature flags:** Deploy code separately from releasing behavior.
- **Canary or phased rollout:** Expose gradually and watch telemetry.
- **Blue/green or rolling deployment:** Use where the platform supports safe cutover.
- **Manual approval gates:** Use for high-risk production environments.

## Environment Management

```text
template config      -> committed, contains no secrets
local config         -> ignored, developer-only
CI/test config       -> committed only if non-secret
CI secrets           -> CI secret manager or vault
production secrets   -> production secret manager or vault
```

CI should not need broad production privileges. Use least privilege per environment.

## Optimization

When CI is too slow, improve it without weakening gates:

- Cache dependencies and toolchains safely.
- Split independent jobs and run them in parallel.
- Run path-scoped jobs for docs-only or isolated changes.
- Shard slow test suites.
- Move expensive non-blocking checks to scheduled jobs only if risk allows.
- Track pipeline duration as an engineering metric.

## Common Rationalizations

| Rationalization | Reality |
|---|---|
| "CI is too slow" | Optimize it; do not bypass the safety net. |
| "This change is trivial" | Trivial changes still break builds. |
| "The test is flaky, just rerun" | Flaky tests hide real failures and should be fixed or explicitly quarantined. |
| "We'll add CI later" | Broken states accumulate without early automation. |
| "Manual testing is enough" | Manual testing is not repeatable enough to be the merge gate. |

## Verification

After adding or changing CI/CD:

- [ ] The pipeline uses actual project commands documented in the repo.
- [ ] Required checks run on every merge request/pull request.
- [ ] Failures block merge or deployment according to project policy.
- [ ] Secrets are stored in the CI/secrets manager, not source control.
- [ ] Artifacts are reproducible from a clean environment.
- [ ] Deployment has a rollback or disable path.
- [ ] Staging/preview or smoke verification exists for deployable systems.
- [ ] Pipeline duration is acceptable or optimization work is tracked.
