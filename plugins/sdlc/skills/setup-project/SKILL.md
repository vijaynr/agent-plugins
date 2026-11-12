---
name: setup-project
disable-model-invocation: true
description: Prepare any project for agent autopilot with explicit per-phase approval gates. Optionally generate ARCHITECTURE.md and AGENTS.md, then run cross-link checks on produced artifacts.
---

Use **ASD-STE100 Simplified Technical English** for all end-user replies and artifact text. First read and follow [the output language rules](../../references/output-language.md), including for delegated work.

# Setup Project

Prepare a project for agent autopilot. This workflow is interactive: before each phase, ask the user whether to proceed, skip, or stop.

## Inputs

- **Project root** — absolute or workspace-relative path. Default: workspace root.
- **Hints** — known patterns, monorepo scope, teams, or anything to highlight. Optional.
- **Specific instructions** — repository-specific agent guidance to add/update in root `AGENTS.md` (and, when scoped to a subsystem, the relevant nested `AGENTS.md`). Optional.
- **Proceed without phase confirmations** — optional boolean; default `false`.

Resolve `project_root` to an absolute path. Pass `hints` as extra context to all phases below. Treat `specific_instructions` as authoritative project guidance that must be preserved in `AGENTS.md` unless it conflicts with higher-priority system/developer instructions.

## Interaction contract (required)

Unless the user explicitly asked to run non-interactively, require a confirmation gate **before starting each phase**:

1. Show what the phase will do and what artifacts it may modify.
2. Ask the user: `Proceed`, `Skip phase`, or `Stop setup`.
3. Respect the choice:
   - **Proceed**: execute phase.
   - **Skip phase**: mark phase as skipped and continue to next phase gate.
   - **Stop setup**: end immediately and return a partial summary.

Skipping is valid for `ARCHITECTURE.md` generation and `AGENTS.md` generation.

Tool installation/bootstrap is intentionally out of scope for this skill. If the user asks to install RTK, ripgrep, or other local context tooling, route them to the `context-engineering` plugin's `setup-rtk` or `setup-ripgrep` skill.

## Phase 1 — Optional architecture generation (`generate-arch-md`)

At the phase gate, ask whether to generate `ARCHITECTURE.md`.

If approved, load and execute the full `generate-arch-md` skill against `project_root`, treating `hints` as extra context.

When executed, record:

- `ARCHITECTURE.md` path written
- One-line architecture summary: pattern + key layers

If skipped, record `ARCHITECTURE.md` generation as skipped and continue.

## Phase 2 — Optional agent guidance generation (`generate-agents-md`)

At the phase gate, ask whether to generate/update `AGENTS.md` files.

If approved, load and execute the full `generate-agents-md` skill against `project_root`, treating `hints` as additional context.

Additional constraints for root `AGENTS.md`:

1. It must include a row for `ARCHITECTURE.md` in its directory/file table:

   | File | Purpose |
   |------|---------|
   | `ARCHITECTURE.md` | Codebase layer map, data-flow diagrams, and extension guide — read before adding features |

   If `AGENTS.md` already exists and already has this row, update it only if the description is stale.

2. It must include caveman usage instructions so future agents know how to activate and stop terse mode. Add or update a concise section like this, preserving equivalent existing wording when present:

   ```md
   ## Caveman Mode

   When the user says `caveman mode`, `talk like caveman`, `use caveman`, `less tokens`, `be brief`, or invokes `/skill:caveman`, use the `caveman` skill if available.

   Once active, keep responses ultra-compressed: drop filler, articles, pleasantries, and hedging while preserving technical accuracy. Continue until the user says `stop caveman` or `normal mode`.

   Temporarily use normal clarity for security warnings, irreversible-action confirmations, or multi-step instructions where terse wording could be misread; then resume caveman mode.
   ```

3. It must include or update any user-provided **specific instructions**. Add them under an explicit section such as:

   ```md
   ## Project-Specific Agent Instructions

   - <instruction>
   ```

   Rules:
   - Preserve existing non-conflicting project-specific instructions.
   - Update stale or duplicate instructions instead of appending repeated copies.
   - If an instruction applies only to a subsystem, place it in that subsystem's nested `AGENTS.md` and add a root index/reference when useful.
   - If an instruction conflicts with existing guidance, surface the conflict and ask before overwriting.

Phase 2 has its own internal confirmation gate. Before writing, show the intended AGENTS changes (including specific-instruction updates) and require approval unless the user explicitly requested non-interactive execution.

If skipped, record `AGENTS.md` generation as skipped and continue.

## Phase 3 — Cross-link and verify

At the phase gate, ask whether to run verification on available artifacts.

When executed, run conditional checks:

1. **Coherence check** — if both files exist, confirm `ARCHITECTURE.md` and `AGENTS.md` do not contradict each other on layer names, entry points, or directory structure. If any contradiction is found, fix the stale file and note the correction.
2. **Forward references** — if both files exist, confirm root `AGENTS.md` references `ARCHITECTURE.md`, and `ARCHITECTURE.md` section `Extending the codebase` is consistent with the entry points listed in `AGENTS.md`.
3. **Caveman instructions** — if `AGENTS.md` exists, confirm root `AGENTS.md` includes the caveman usage section. If missing or stale, add/update it.
4. **Specific instructions** — if `AGENTS.md` exists and specific instructions were provided, confirm they are present in the correct file(s), with no duplicates or unresolved conflicts.
5. **Coverage check** — if nested `AGENTS.md` files were created/updated, confirm each is reachable from the root `AGENTS.md` index. Flag any gap.

If skipped, mark cross-link verification as skipped.

## Output

Return this summary:

```md
## Project prepared for autopilot

### Phase decisions
- Architecture generation (`generate-arch-md`): Proceeded / Skipped / Stopped
- Agent guidance generation (`generate-agents-md`): Proceeded / Skipped / Stopped
- Cross-link verification: Proceeded / Skipped / Stopped

### Files written
- `<path>/ARCHITECTURE.md` — <architecture summary line> (or skipped/not written)
- `<path>/AGENTS.md` — <N> sections, <M> subfolder AGENTS.md files indexed (or skipped/not written)
- `<path>/<subfolder>/AGENTS.md` — <one-line purpose>  (repeat for each)

### Cross-link status
- AGENTS.md → ARCHITECTURE.md reference: ✔ / ✖ / not-applicable (skipped)
- ARCHITECTURE.md ↔ AGENTS.md entry points: ✔ / ✖ / not-applicable (skipped)
- Caveman usage instructions present: ✔ / ✖ / not-applicable (AGENTS not generated)
- Specific project instructions applied to AGENTS.md: ✔ / ✖ / not-applicable (AGENTS not generated)
- Subfolder index complete: ✔ / ✖ / not-applicable (AGENTS not generated)

### Agents can now
- Orient to the codebase via generated `AGENTS.md` files (if enabled)
- Understand architecture and data flow via generated `ARCHITECTURE.md` (if enabled)
- Navigate to indexed subsystem guidance where subfolder `AGENTS.md` files were produced
```
