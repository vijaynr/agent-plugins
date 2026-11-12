---
name: code-simplification
disable-model-invocation: true
description: Simplifies code for clarity in a stack-neutral way. Use when refactoring code for clarity without changing behavior, when code works but is hard to read/maintain, or when reviewing accumulated complexity.
---

Use **ASD-STE100 Simplified Technical English** for all end-user replies and artifact text. First read and follow [the output language rules](../../references/output-language.md), including for delegated work.

# Code Simplification

## Overview

Simplify code by reducing complexity while preserving exact behavior. The goal is not fewer lines; it is code that is easier to understand, modify, test, and debug.

This skill is language-neutral. Apply the principles using the idioms and conventions of the current project.

## When to Use

- Working code is harder to read than it should be.
- A review flags complexity, duplication, or unclear naming.
- Logic is deeply nested or spread across too many places.
- A function/module has accumulated multiple responsibilities.
- A refactor can make future changes safer without changing behavior.

Do not use when:

- You do not understand the current behavior.
- Tests or characterization checks are missing for risky logic.
- The change would alter behavior rather than clarify expression.
- The code is about to be replaced entirely.
- The simplification is unrelated to the current task and was not requested.

## Principles

### 1. Preserve Behavior Exactly

Before every change, ask:

```text
Does this keep the same inputs, outputs, side effects, ordering, errors, and edge cases?
Do existing tests pass without modification?
Can I explain why the new form is equivalent?
```

If not, stop and add characterization tests or ask for guidance.

### 2. Follow Project Conventions

Simplification means making code fit the project better, not imposing personal style. Match local conventions for naming, error handling, module boundaries, formatting, and abstraction level.

### 3. Prefer Clarity Over Cleverness

Readable, explicit code beats compact code that requires mental decoding.

```text
UNCLEAR:
  result = deeply_nested_expression_with_multiple_conditions

CLEAR:
  if invalid_input:
      return error
  if missing_permission:
      return forbidden
  return perform_action
```

### 4. Keep Useful Names

A helper that names a domain concept can be clearer than inlining. Remove abstractions that hide nothing; keep abstractions that explain intent.

### 5. Scope the Refactor

Simplify the code you are already changing or the code explicitly requested. Do not create drive-by refactors.

## Process

### Step 1: Understand Before Touching

Answer:

- What is this code responsible for?
- What calls it and what does it call?
- What are the edge cases and error paths?
- What tests or examples define behavior?
- Why might it be written this way: performance, compatibility, history, policy?

If you cannot answer, read more before editing.

### Step 2: Identify Concrete Opportunities

| Pattern | Signal | Simplification |
|---|---|---|
| Deep nesting | Control flow is hard to follow | Use guard clauses or extract predicates |
| Long function/module | Multiple responsibilities | Split by responsibility with clear names |
| Repeated conditionals | Same decision in many places | Extract a named predicate/policy |
| Generic names | `data`, `result`, `temp` everywhere | Rename to domain-specific names |
| Dead code | Unreachable or unused code | Remove after confirming it is unused |
| Duplicate logic | Same behavior copied | Extract shared behavior or consolidate call sites |
| Boolean flags | Call sites pass unexplained true/false values | Use named options or separate functions |
| Pass-through wrappers | Wrapper adds no policy/translation | Inline or call the underlying API directly |
| Over-generalization | Framework/pattern for one case | Replace with direct code until variation exists |

### Step 3: Change Incrementally

For each simplification:

1. Make one focused change.
2. Run the smallest relevant verification.
3. If it passes, continue or commit.
4. If it fails, revert and reconsider.

Do not batch many speculative simplifications into one untested edit.

### Step 4: Compare Before and After

The result is better only if:

- A new reader can understand it faster.
- The diff is reviewable.
- Behavior is unchanged.
- Project conventions are preserved.
- Error handling and security checks are not weakened.

If the simplified version is harder to explain, revert.

## Generic Examples

### Replace nested flow with guard clauses

```text
Before:
  if input exists:
      if input is valid:
          if actor is allowed:
              do work
          else: reject unauthorized
      else: reject invalid
  else: reject missing

After:
  if input missing: reject missing
  if input invalid: reject invalid
  if actor not allowed: reject unauthorized
  do work
```

### Name a repeated decision

```text
Before:
  if status in allowed_statuses and actor has permission and item is not locked:
      approve
  ...
  if status in allowed_statuses and actor has permission and item is not locked:
      notify

After:
  if can_change_item(actor, item): approve
  ...
  if can_change_item(actor, item): notify
```

### Remove a pass-through wrapper

```text
Before:
  function fetch_record(id):
      return repository.fetch_record(id)

After:
  call repository.fetch_record(id) directly
```

Only do this if the wrapper adds no domain language, validation, logging, compatibility, or future seam currently relied on by the project.

## Common Rationalizations

| Rationalization | Reality |
|---|---|
| "Fewer lines is always simpler" | Simplicity is comprehension speed, not line count. |
| "I'll simplify unrelated code while I'm here" | Unscoped refactors create noisy diffs and risk regressions. |
| "The tests need updating" | If behavior is unchanged, tests should usually keep passing unchanged. |
| "This abstraction might be useful later" | Speculative abstractions are present complexity for hypothetical value. |
| "The original author must have had a reason" | Maybe. Check history and context before removing it. |

## Verification

After simplification:

- [ ] Existing tests pass without behavior changes.
- [ ] Build/compile/check command succeeds where applicable.
- [ ] Lint/format command succeeds where applicable.
- [ ] No error handling, authorization, validation, or logging was weakened.
- [ ] The diff is focused and reviewable.
- [ ] Names and structure follow project conventions.
- [ ] No unrelated files were changed.
