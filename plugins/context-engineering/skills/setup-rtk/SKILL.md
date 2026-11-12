---
name: setup-rtk
disable-model-invocation: true
description: Check and optionally install or initialize RTK (Rust Token Killer) with explicit user approval gates. Use when preparing local context-engineering token/context tooling.
---

# Setup RTK

Set up RTK (Rust Token Killer) for local context-engineering workflows.

Follow RTK guidance from:
`https://github.com/rtk-ai/rtk/blob/develop/INSTALL.md`

This skill intentionally uses documented shell commands directly; no helper script is required.

## Inputs

- **Proceed without confirmations** — optional boolean; default `false`.
- **Install method** — optional: `quick-install`, `brew`, `cargo-git`, or `manual-release`. Default: choose the safest available method for the platform.
- **Init mode** — optional: `global-copilot`, `global`, `global-hook-only`, `global-auto-patch`, `global-no-patch`, `local`, `show`, or `uninstall`. Default: ask interactively after install verification.

This skill also includes `RTK.md` as a reference document, but current RTK can install Copilot usage instructions directly with `rtk init -g --copilot`.

## Required interaction model

Unless non-interactive mode is explicitly requested, require user approval before any installation, replacement, uninstall, or initialization command:

1. Detect RTK status first.
2. Show status and recommended action.
3. Ask: `Install/fix now`, `Skip RTK`, or `Stop`.
4. If RTK is available, ask before initialization changes: `Initialize now`, `Skip init`, or `Stop`.
5. Respect the decision and continue safely.

Skipping RTK installation or initialization is valid and must not abort unrelated setup flows.

## Phase 1 — Detect current RTK state

Run:

```bash
rtk --version
rtk gain
# Check installation path (platform-specific)
which rtk          # macOS/Linux
where rtk          # Windows
```

Interpretation:

- `rtk --version` confirms an `rtk` binary is available.
- `rtk gain` confirms RTK is **Rust Token Killer** (`rtk-ai/rtk`), not the Rust Type Kit name-collision package.
- Missing `rtk`, failing `rtk gain`, or evidence of the wrong crates.io `rtk` means install/fix is needed.

## Phase 2 — RTK install/fix (optional, approval-gated)

If RTK is missing or incorrect, ask before any change.

Recommended install/fix options:

### Linux/macOS quick install

```bash
curl -fsSL https://raw.githubusercontent.com/rtk-ai/rtk/master/install.sh | sh
```

### Homebrew (macOS/Linux)

```bash
brew install rtk-ai/tap/rtk
```

### Cargo (explicit Git source to avoid name collision)

```bash
cargo install --git https://github.com/rtk-ai/rtk
```

Use this instead of `cargo install rtk` because the crates.io `rtk` package may be a different project.

### Windows manual release install

1. Open `https://github.com/rtk-ai/rtk/releases`.
2. Download `rtk-x86_64-pc-windows-msvc.zip`.
3. Extract `rtk.exe`.
4. Place `rtk.exe` in a directory on `PATH`.
5. Open a new terminal and verify with `rtk gain`.

### Wrong package remediation

If the wrong crates.io `rtk` is installed and Cargo is available, ask before removing it:

```bash
cargo uninstall rtk
```

Then reinstall using one of the supported methods above.

After install/fix, verify:

```bash
rtk --version
rtk gain
```

## Phase 3 — RTK initialization and Copilot setup (optional, approval-gated)

After RTK is correctly installed, ask whether to initialize it.

Recommended Copilot setup:

```bash
rtk init -g --copilot
```

This is the preferred setup path because RTK handles Copilot usage instructions and integration itself.

Other initialization options:

```bash
# Global hook-first setup
rtk init -g

# Global, hook-only (minimal context footprint)
rtk init -g --hook-only

# Global, non-interactive patch behavior
rtk init -g --auto-patch
rtk init -g --no-patch

# Local project-only setup
rtk init

# Show current init status
rtk init --show

# Roll back global setup
rtk init -g --uninstall
```

Show status after initialization:

```bash
rtk init --show
```

## Phase 4 — Verification

Re-run:

```bash
rtk --version
rtk gain
rtk init --show
```

Basic usage checks:

```bash
rtk ls .
rtk git status
```

## Output

Return:

```md
## RTK setup summary

### Decisions
- RTK install/fix: Proceeded / Skipped / Not needed / Stopped
- RTK init/Copilot setup: Proceeded / Skipped / Not needed / Stopped

### Final status
- RTK available and verified with `rtk gain`: ✔ / ✖ / skipped
- RTK init status checked with `rtk init --show`: ✔ / ✖ / skipped
- Copilot setup via `rtk init -g --copilot`: ✔ / ✖ / skipped

### Notes
- <platform-specific commands used or skip rationale>
```
