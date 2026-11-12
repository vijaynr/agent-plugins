# Scaffold AGENTS.md

Use GitHub Copilot's built-in **`/init`** command to generate or update
`AGENTS.md` files at the project root and in qualifying subfolders.
Apply quality constraints and cross-link verification on top of what `/init`
produces. Every file must be **minimal and precise** — agents load these as
context; every unnecessary word is waste.

## Input

- **Project root** — path provided by the user, or the current working
  directory if not specified.

---

## Phase 1 — Identify candidates

Run the tree command to map the project, then identify which subfolders
warrant their own `AGENTS.md`.

```bash
find "<ROOT>" -mindepth 1 -maxdepth 2 \
  -not -path "*/.git/*" \
  -not -path "*/node_modules/*" \
  -not -path "*/__pycache__/*" \
  -not -path "*/.venv/*" \
  -not -name "*.pyc" \
  | sort
```

A subfolder warrants its own `AGENTS.md` when **two or more** of the
following apply:

| Signal | Example |
|--------|---------|
| Has its own scripts or entry points | `scripts/*.py`, `bin/*` |
| Has its own config / `.env.example` | credentials, endpoints |
| Has its own README or SKILL.md | existing local docs |
| Is invoked differently than the root | different runtime, cwd, flags |
| Contains >5 files that agents will touch | non-trivial surface area |
| Already has an `AGENTS.md` that may need updating | always re-evaluate |

Exclude: pure asset folders (`assets/`, `static/`), generated output
(`dist/`, `build/`, `coverage/`), test-only folders with no agent-visible
entry points, and folders that are fully described by a parent `AGENTS.md`
in ≤2 lines.

---

## Phase 2 — Plan

Before writing anything, output a plan to the user:

```
Root AGENTS.md        → [create | update | no change]
skills/alm-octane/    → [create | update | skip] — <one-line reason>
skills/ai-sdlc/       → [create | update | skip] — <one-line reason>
...
```

Ask the user to confirm or adjust before proceeding to Phase 3.
If the user gave an explicit "just do it" instruction, skip confirmation.

---

## Phase 3 — Generate with `/init`

For each location in the confirmed plan:

### Root

Run `/init` at `<ROOT>`. This scans the workspace and creates or enriches
`AGENTS.md` in the project root.

### Each subfolder candidate

Run `/init` scoped to the subfolder path. Pass the subfolder as the target
so Copilot generates a self-contained `AGENTS.md` for that directory.

> If `/init` cannot be scoped to a subfolder directly, run it at root with
> an explicit instruction: *"generate AGENTS.md for `<subfolder>` only,
> self-contained, no root-level conventions repeated"*.

### Post-generation constraints

After each `/init` invocation, review and edit the generated file to enforce
these rules — make only surgical edits, do not rewrite content that is
already accurate.

**Must include:**
- One sentence: what the project / subfolder is for.
- Root: flat directory table (`path` | `purpose`) and entry-points table.
- Subfolder: exact invocation commands with correct `cwd`.
- Subfolder: required env-var names (values come from `.env`, never written here).

**Must exclude (context bloat):**
- Motivation, philosophy, or marketing copy.
- Setup / installation steps — point to `README` or `SKILL.md` instead.
- ASCII file trees.
- Sections that duplicate what `SKILL.md` or `README` already say.
- Generic git or coding conventions every agent already knows.
- Any section that would never change an agent's action.

**Format limits:**
- Root: max ~60 lines for a simple project; ~100 lines for a large monorepo.
- Subfolder: max ~40 lines for a focused skill or module.
- If a full `SKILL.md` exists for a subfolder, reduce the `AGENTS.md` to a
  pointer: *"See `SKILL.md` for full usage. This file covers agent-specific
  cwd and invocation conventions only."*
- Use tables over prose wherever possible.
- No decorative horizontal rules or emojis.
- Section headers: `##` max (no `###` nesting unless strictly necessary).

**Preserve custom content:**
- Never overwrite a `<!-- custom -->` … `<!-- /custom -->` block.
- Never delete an existing `AGENTS.md`; only update it.

---

## Phase 4 — Verify

After all files are written, re-read each one and confirm:

- [ ] No section exceeds its line budget without good reason.
- [ ] Every command listed is syntactically plausible given the discovered
  runtime and file paths.
- [ ] No sensitive values (tokens, passwords, URLs with credentials) were written.
- [ ] Subfolder `AGENTS.md` files do not duplicate root-level conventions
  verbatim.
- [ ] Root `AGENTS.md` subfolder index matches the set of files actually written.

Report the final list of files written and their line counts.

---

## Guardrails

- Never write `.env` files or modify existing ones.
- Do not read or summarise files outside the target project root.
- If a file cannot be read (permission error, binary), skip it silently
  and note it in the plan output.
- Do not create `AGENTS.md` for a subfolder that already has a complete,
  accurate one unless the user explicitly asks for regeneration.
