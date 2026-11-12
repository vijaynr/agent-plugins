---
name: source-driven-development
disable-model-invocation: true
description: Grounds implementation decisions in authoritative sources in a stack-neutral way. Use when framework/library/platform correctness matters, when APIs may have changed, or when avoiding stale assumptions is important.
---

Use **ASD-STE100 Simplified Technical English** for all end-user replies and artifact text. First read and follow [the output language rules](../../references/output-language.md), including for delegated work.

# Source-Driven Development

## Overview

Do not rely on memory for framework, library, protocol, or platform behavior. Verify the version in use, consult authoritative sources, and cite what you used. This skill is stack-neutral and applies to any language, runtime, platform, or toolchain.

## When to Use

- Using a framework, SDK, API, protocol, CLI, or library you may not know deeply
- Implementing against behavior that changes across versions
- Choosing between patterns with compatibility or security implications
- Debugging an issue that may be caused by version-specific behavior
- Writing code that depends on platform limits, flags, defaults, or deprecations

## Process

### 1. Identify the Exact Target

Before researching, establish:

- Library/framework/tool/platform name
- Version or version range actually used by the project
- Runtime/environment constraints
- Relevant configuration files
- The specific API, behavior, or pattern being used

Use the project's own files as the source of version truth: manifests, lockfiles, build files, dependency declarations, container images, CI config, runtime metadata, or deployment config.

### 2. Prefer Authoritative Sources

Source priority:

1. Official documentation for the exact version
2. Official API reference
3. Source code or generated docs from the project/repository
4. Official migration/deprecation notes
5. Maintainer-authored issues, discussions, or release notes
6. Community content only as supplemental context

If official and community guidance conflict, trust official sources and note the discrepancy.

### 3. Verify Version Fit

Do not copy examples for the wrong version. Check:

- Version-specific API signatures
- Deprecated methods/options
- Required imports/modules/packages
- Runtime/platform support
- Configuration defaults
- Security or compatibility notes

If you cannot verify version fit, state that explicitly and choose the conservative option.

### 4. Implement the Smallest Source-Backed Pattern

Translate the source into project-local code while following project conventions. Avoid cargo-culting entire examples. Use only the part needed for the task.

### 5. Cite and Record

When the source materially affects a decision, include a short note in the response, PR, comment, ADR, or code review explaining:

- What source was consulted
- Which version it applies to
- What decision it justified
- Any uncertainty or follow-up needed

## Anti-Stale-Code Checklist

Before implementing:

- [ ] Exact dependency/tool/platform version identified.
- [ ] Official source for that version consulted.
- [ ] Deprecated/removed APIs checked.
- [ ] Runtime/environment compatibility checked.
- [ ] Project conventions checked before applying examples.

## Common Failure Modes

| Failure | Safer behavior |
|---|---|
| Copying a blog example | Verify against official docs for the project version. |
| Using memory of an older API | Check current API reference or source. |
| Assuming defaults | Read the actual defaults for this version/config. |
| Applying official docs for another major version | Find the matching version or note the mismatch. |
| Treating generated/AI output as authoritative | Verify against source before implementing. |

## Verification

- [ ] The implementation matches authoritative documentation/source for the project version.
- [ ] Any version-sensitive decision is documented or cited.
- [ ] Tests/build/checks appropriate to the project pass.
- [ ] No deprecated or removed API is introduced unless explicitly justified.
- [ ] Unverified assumptions are called out rather than hidden.
