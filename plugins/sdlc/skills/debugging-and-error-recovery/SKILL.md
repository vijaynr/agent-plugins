---
name: debugging-and-error-recovery
disable-model-invocation: true
description: Guides systematic, stack-neutral root-cause debugging. Use when tests fail, builds break, behavior is unexpected, or an error appears and you need to fix the cause rather than guess.
---

Use **ASD-STE100 Simplified Technical English** for all end-user replies and artifact text. First read and follow [the output language rules](../../references/output-language.md), including for delegated work.

# Debugging and Error Recovery

## Overview

Debugging is evidence collection followed by the smallest safe fix. Do not guess, shotgun changes, or hide failures. Reproduce, localize, reduce, fix, and guard.

This skill is stack-neutral: use the project's actual test/build/run commands and tools.

## When to Use

- Tests fail
- Build or static checks fail
- Runtime behavior differs from expectations
- A command fails in CI or locally
- A bug report arrives
- A previous implementation attempt produced unclear errors

## The Five-Step Loop

```text
1. Reproduce -> 2. Localize -> 3. Reduce -> 4. Fix -> 5. Guard
```

### 1. Reproduce

Capture the exact failing command, input, environment, and output.

- Run the smallest command that demonstrates the failure.
- Save the first meaningful error, not only the final stack/summary.
- Note whether it fails consistently or intermittently.
- Compare local vs CI/staging if relevant.

If you cannot reproduce it, do not claim it is fixed. Document what was tried and what evidence is missing.

### 2. Localize

Narrow the failure to the smallest responsible area:

- Recent changes
- Failing test or scenario
- Specific module/function/config
- Dependency or environment difference
- Data shape or input boundary

Useful techniques:

- Inspect the exact failing assertion/error.
- Add temporary diagnostic logs locally, then remove them.
- Use binary search over commits or changes when regression timing is unknown.
- Compare a known-good path with the failing path.

### 3. Reduce

Create the smallest case that still fails:

- A single test
- A minimal input
- A minimal config
- A small script or reproduction command
- A narrowed fixture/sample

Reduction prevents accidental fixes and makes the root cause visible.

### 4. Fix

Make the smallest change that addresses the root cause.

Do not:

- Loosen assertions just to pass tests.
- Delete failing tests without approval.
- Silence errors without understanding them.
- Add broad retries/timeouts unless the failure is proven transient.
- Refactor unrelated code while fixing the bug.

### 5. Guard

Add or keep a guard so the bug does not return:

- A regression test
- A validation check
- A build/static-analysis rule
- A CI guard
- A monitoring/alerting signal for production-only issues

## Error Classification

| Symptom | First checks |
|---|---|
| Test failure | Assertion, fixture/input, recent code changes, expected behavior |
| Build/compile failure | Toolchain version, configuration, missing generated files, invalid imports/includes |
| Runtime exception | Stack trace, null/missing data, boundary validation, external dependency behavior |
| Integration failure | Credentials, network, service availability, contracts, timeouts, data setup |
| CI-only failure | Environment differences, paths, permissions, caches, parallelism, time/timezone/locale |
| Flaky failure | Shared state, ordering, time, randomness, resource leaks, external services |

## Stop Conditions

Stop and ask for help when:

- The fix would require changing requirements.
- The failure points to secrets, credentials, auth, data deletion, or production systems.
- The only apparent fix is to weaken a test, security control, or validation rule.
- You cannot reproduce the issue after reasonable attempts.
- The root cause suggests a larger design flaw outside the current task.

## Reporting Format

When reporting a debugging result, include:

```text
Observed failure:
Root cause:
Fix applied:
Verification run:
Regression guard:
Remaining risk / follow-up:
```

## Common Rationalizations

| Rationalization | Reality |
|---|---|
| "Maybe this will fix it" | A guess is not a root cause. Gather evidence first. |
| "The test is wrong" | It might be, but prove the expected behavior before changing it. |
| "It only fails in CI" | CI failures are real failures until explained. |
| "I'll clean this up while I'm here" | Keep debugging fixes focused and reviewable. |
| "It passed once" | One pass does not prove a flaky issue is fixed. |

## Verification

- [ ] The failure was reproduced or the inability to reproduce was documented.
- [ ] Root cause is identified with evidence.
- [ ] Fix is minimal and scoped.
- [ ] A regression guard exists where practical.
- [ ] Relevant tests/checks/build commands pass.
- [ ] No unrelated changes were included.
