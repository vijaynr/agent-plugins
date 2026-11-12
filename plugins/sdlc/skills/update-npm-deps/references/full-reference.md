# Update npm Dependencies

Use this skill to perform a structured, phased workflow for safely upgrading outdated packages in `package.json`.
Produce a written plan before touching dependencies, then execute phase by phase with build/lint/test verification at each step.

**Constraint priority (highest to lowest):**
1. Never break the build — verify after every phase before continuing.
2. Research breaking changes for every major bump before installing.
3. Use `--legacy-peer-deps` for Angular or Angular-adjacent packages.
4. Respect known holds — do not upgrade held packages unless explicitly asked.

---

## Prerequisite Knowledge

### Angular peer-dep pinning

Angular packages pin **exact** peer versions, for example `@angular/core@"21.2.12"` rather than `"^21.2.12"`.
Always pass `--legacy-peer-deps` when installing Angular or Angular-adjacent packages; omitting it can cause `ERESOLVE` errors.

### Known holds for this project

| Package | Held at | Reason |
|---|---|---|
| TypeScript | `<5.10.0` | Angular 21 is incompatible with TS 6.x |
| ESLint | `^9.x` | `angular-eslint` compatibility with ESLint 10 unconfirmed |

---

## Phase 0 — Audit

Run:

```bash
npm outdated
```

Record every package, its **current** version, and the **latest** version.
Group updates by risk:

| Group | Criteria |
|---|---|
| Patch | SemVer patch bump only, e.g. `1.2.3` → `1.2.4` |
| Minor | Minor bump, no known breaking changes |
| Major | Major version bump; requires breaking-change research |
| Hold | Project constraints prevent upgrade |

---

## Phase 1 — Research Breaking Changes

For every **major** bump, research breaking changes before writing the plan.
Use authoritative sources where possible:

- Official `CHANGELOG.md` on GitHub
- Framework migration guides, such as `ng update`
- npm release notes
- Maintainer documentation

Document for each major package:

- Removed APIs or renamed exports
- Required code changes in consumer code
- Required peer dependency changes
- Migration commands, if any

---

## Phase 2 — Write the Plan

Create `UPDATE_PLAN.md` at the repository root with:

1. **Phase list** — each phase is one logical group of upgrades with an npm install command.
2. **Breaking changes per package** — what needs fixing, with file references where known.
3. **HOLD section** — packages intentionally skipped and why.
4. **Validation commands** per phase, such as `npm run build`, `npm run lint`, and `npm test`.

Group strategy:

- Phase 1: Core framework packages, such as Angular and ngrx, upgraded together.
- Phase 2: Tooling, such as ESLint plugins and prettier, verified with linting.
- Phase 3a–3n: One high-risk package per sub-phase.
- Patch/minor packages can be bundled together.

---

## Phase 3 — Execute Phases

For each phase in the plan:

### 3a. Install

```bash
npm install --legacy-peer-deps <package>@<version> [<package2>@<version2> ...]
```

Always use `--legacy-peer-deps` for Angular projects; it is safe and required for Angular peer dependency pinning.

### 3b. Verify

Run the appropriate verification for this phase:

| Phase type | Command |
|---|---|
| Any code change | `npm run build` |
| ESLint / tooling | `npm run lint` |
| Unit test libraries | `npm test` or `npx ng test --watch=false` |

Fail fast: do not proceed to the next phase if verification fails.

### 3c. Fix breaking changes

If build, lint, or tests fail after an upgrade:

1. Read the error output carefully. TypeScript errors include file and line numbers.
2. Check the breaking-change notes from Phase 1 research.
3. Fix source files: update imports, rename APIs, fix types, or update mocks.
4. Re-run verification before continuing.

#### Common fix patterns

| Error pattern | Likely cause | Fix |
|---|---|---|
| `TS2561: Object literal may only specify known properties` | Interface property renamed, such as snake_case ↔ camelCase | Rename properties to match the interface |
| `toEqual` test failures after partial mock | Mock has fewer properties than full object | Change `toEqual(x)` to `toEqual(expect.objectContaining(x))` |
| Boolean assigned to number field | Type narrowed from `boolean` to `number` in new version | Change `true` to `1`, `false` to `0` |
| `ERESOLVE` on npm install | Angular peer-dependency exact pinning | Add `--legacy-peer-deps` |
| Unknown import from package | API renamed or removed in major version | Check migration guide for new import path |

---

## Phase 4 — Final Validation

After all phases are complete, run the project's full validation suite. For Angular projects, prefer:

```bash
npm run lint && npx ng test --watch=false && npm run build
```

All required validation commands must pass before the update is considered done.

---

## Spec File Repair Checklist

When spec files break after an upgrade, check these common issues:

- [ ] Property names match the **current** interface definition.
- [ ] Mock objects for API DTO/response types use the casing expected by the current interface.
- [ ] Mock objects for view models use the casing expected by the current interface.
- [ ] `toEqual` assertions on partial mocks use `expect.objectContaining()`.
- [ ] Boolean values assigned to `number`-typed interface fields are replaced with `0` / `1`.

---

## Tips

- Check `npm outdated` output carefully: `wanted` satisfies the current range; `latest` is the newest available.
- After every `npm install`, the lockfile changes. Consider committing phases separately for easy bisecting.
- Run `npm audit fix` only after planned upgrades are complete, unless the user explicitly asks to prioritize audit remediation.
- Do not upgrade held packages unless the user explicitly asks and accepts the compatibility risk.
