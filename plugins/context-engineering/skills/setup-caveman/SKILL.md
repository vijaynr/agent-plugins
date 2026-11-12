---
name: setup-caveman
disable-model-invocation: true
description: Check and optionally install or uninstall Caveman for GitHub Copilot with explicit approval gates. Use when configuring concise Caveman behavior through repo-wide Copilot instructions.
---

# Setup Caveman for GitHub Copilot

Set up or remove [Caveman](https://github.com/JuliusBrussee/caveman) for GitHub Copilot.

Reference install documentation:
`https://github.com/JuliusBrussee/caveman/blob/main/INSTALL.md`

Caveman treats GitHub Copilot as a **soft probe**, so the unified installer does not auto-detect it reliably. For Copilot, always pass `--only copilot`. Use `--with-init` when installing because Copilot activation is via repo-wide instructions in `.github/copilot-instructions.md`.

This skill intentionally uses documented shell commands directly; no helper script is required.

## Inputs

- **Action** — required: `install`, `uninstall`, `dry-run`, `list`, or `status`.
- **Proceed without confirmations** — optional boolean; default `false`.
- **Target repository** — optional path; default: current working directory. Required for `install`, `dry-run`, and repo-local instruction cleanup checks.
- **Install source** — optional: `npx` or `local-clone`. Default: `npx`.
- **Local clone path** — optional path; required when install source is `local-clone`.
- **Remove Copilot instruction file manually** — optional boolean; default: ask interactively during uninstall if Caveman content is detected in `.github/copilot-instructions.md`.

Resolve the target repository and local clone path to absolute paths before running commands.

## Required interaction model

Unless non-interactive mode is explicitly requested, require user approval before any command that writes files, installs packages, or removes files:

1. Detect Node/npm availability and current Caveman/Copilot instruction state first.
2. Show status, target repository, and the exact command(s) or file edits that will run.
3. Ask for one of: `Proceed`, `Skip`, or `Stop`.
4. Respect the decision and continue safely.

Skipping install, uninstall, or manual cleanup is valid and must not abort unrelated setup flows.

## Phase 1 — Detect prerequisites and current state

Run prerequisite checks:

```bash
node --version
npm --version
npx --version
```

Check the target repository:

```bash
git rev-parse --show-toplevel
```

Check for existing Copilot instructions and Caveman markers from the target repository root:

```bash
test -f .github/copilot-instructions.md && grep -nEi "caveman|talk less|grunt|src/rules/caveman-activate" .github/copilot-instructions.md || true
```

PowerShell equivalent:

```powershell
Test-Path .github/copilot-instructions.md
if (Test-Path .github/copilot-instructions.md) { Select-String -Path .github/copilot-instructions.md -Pattern "caveman|talk less|grunt|src/rules/caveman-activate" }
```

Interpretation:

- Missing `node`, `npm`, or `npx` means the `npx` installer cannot run. Ask the user to install Node.js/npm first or use a prepared local clone with Node available.
- GitHub Copilot may not be auto-detected by Caveman; this is expected. Use `--only copilot` explicitly.
- Caveman for Copilot is repository-scoped when installed with `--with-init`, because it writes `.github/copilot-instructions.md` in the current repository.

## Phase 2 — Preview or list installer behavior

Use these commands for read-only inspection.

### List supported agents

```bash
npx -y github:JuliusBrussee/caveman -- --list
```

### Dry run Copilot install

From the target repository root:

```bash
npx -y github:JuliusBrussee/caveman -- --only copilot --with-init --dry-run
```

Local clone alternative:

```bash
node bin/install.js --only copilot --with-init --dry-run
```

## Phase 3 — Install Caveman for GitHub Copilot (optional, approval-gated)

From the target repository root, show and approve this command before running it:

```bash
npx -y github:JuliusBrussee/caveman -- --only copilot --with-init
```

Local clone alternative from the Caveman clone, with the target repository as the working directory only if the installer is run there. If using a clone, prefer running `node <clone>/bin/install.js` from the target repository root:

```bash
node /path/to/caveman/bin/install.js --only copilot --with-init
```

Notes:

- `--only copilot` selects GitHub Copilot explicitly.
- `--with-init` writes always-on repo instructions, including `.github/copilot-instructions.md`.
- This is repo-local for Copilot; run it separately in each repository where Caveman behavior is desired.

## Phase 4 — Uninstall Caveman (optional, approval-gated)

The documented global uninstall command is:

```bash
npx -y github:JuliusBrussee/caveman -- --uninstall
```

Important Copilot limitation from Caveman's install documentation: `--uninstall` does **not** remove per-repo rule files written by `--with-init`, including `.github/copilot-instructions.md`. For GitHub Copilot, inspect and remove or edit that file manually if desired.

Before manual cleanup, show the detected file and ask for approval.

Conservative manual cleanup options from the target repository root:

```bash
# Remove the entire Copilot instructions file only if it is Caveman-only and user approves
rm .github/copilot-instructions.md
```

PowerShell:

```powershell
Remove-Item .github/copilot-instructions.md
```

If `.github/copilot-instructions.md` contains non-Caveman project guidance, do **not** delete it. Instead, remove only the Caveman block or Caveman lines after showing the exact diff to the user.

## Phase 5 — Verification

After install, verify from the target repository root:

```bash
test -f .github/copilot-instructions.md && grep -nEi "caveman|talk less|grunt|src/rules/caveman-activate" .github/copilot-instructions.md
```

PowerShell:

```powershell
Test-Path .github/copilot-instructions.md
Select-String -Path .github/copilot-instructions.md -Pattern "caveman|talk less|grunt|src/rules/caveman-activate"
```

After uninstall/manual cleanup, verify the Caveman markers are absent or explain any intentionally retained text:

```bash
test ! -f .github/copilot-instructions.md || ! grep -qiE "caveman|talk less|grunt|src/rules/caveman-activate" .github/copilot-instructions.md
```

## Output

Return:

```md
## Caveman setup summary

### Decisions
- Action: install / uninstall / dry-run / list / status
- Target repository: <absolute path>
- Caveman command: Proceeded / Skipped / Not needed / Stopped
- Copilot instruction cleanup: Proceeded / Skipped / Not needed / Stopped

### Final status
- Node/npm/npx available: ✔ / ✖ / skipped
- Caveman Copilot instruction markers present: ✔ / ✖ / skipped
- `.github/copilot-instructions.md` updated or cleaned as requested: ✔ / ✖ / skipped

### Notes
- <commands used, files touched, and any retained instructions>
```
