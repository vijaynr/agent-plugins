---
name: setup-ripgrep
disable-model-invocation: true
description: Check and optionally install ripgrep, then optionally publish ripgrep usage instructions for Copilot with explicit approval gates. Use when preparing fast local search tooling for context-engineering workflows.
---

# Setup ripgrep

Set up ripgrep (`rg`) for fast, gitignore-aware code and text search.

This skill intentionally uses documented shell commands directly; no helper script is required.

This skill also includes `RIPGREP.md` as a reference document. Unlike RTK's `rtk init -g --copilot`, ripgrep does not install Copilot usage instructions, so copy/reference this document manually when requested.

## Inputs

- **Proceed without confirmations** — optional boolean; default `false`.
- **Install method** — optional: `winget`, `scoop`, `choco`, `brew`, `apt`, `dnf`, `pacman`, `zypper`, `cargo`, or `manual-release`. Default: choose the safest available method for the platform.
- **Copilot instructions directory** — optional path. Default: `~/.copilot`.
- **Publish usage instructions** — optional boolean. Default: ask interactively after install verification.

Resolve the Copilot instructions directory to an absolute path.

## Required interaction model

Unless non-interactive mode is explicitly requested, require user approval before any installation or documentation write command:

1. Detect ripgrep status first.
2. Show status and recommended action.
3. Ask: `Install now`, `Skip ripgrep`, or `Stop`.
4. If ripgrep is available, ask before publishing usage docs: `Publish RIPGREP.md`, `Skip docs`, or `Stop`.
5. Respect the decision and continue safely.

Skipping ripgrep installation or usage-doc publication is valid and must not abort unrelated setup flows.

## Phase 1 — Detect current ripgrep state

Run:

```bash
rg --version
# Check installation path (platform-specific)
which rg          # macOS/Linux
where rg          # Windows
```

Interpretation:

- `rg --version` confirms ripgrep is available.
- Missing `rg` means installation is needed.
- If `rg` exists but behaves unexpectedly, inspect the path output to detect aliases, wrappers, or stale binaries.

## Phase 2 — Choose install method

Pick the first suitable method for the current environment:

| Platform/environment | Preferred method |
|---|---|
| Windows with winget | `winget` |
| Windows with Scoop | `scoop` |
| Windows with Chocolatey | `choco` |
| macOS/Linux with Homebrew | `brew` |
| Debian/Ubuntu | `apt` |
| Fedora/RHEL | `dnf` |
| Arch Linux | `pacman` |
| openSUSE/SLES | `zypper` |
| Rust/Cargo available | `cargo` fallback |
| No package manager | manual release |

Package-manager detection commands:

```bash
# Windows
where winget
where scoop
where choco

# macOS/Linux
command -v brew
command -v apt-get
command -v dnf
command -v pacman
command -v zypper
command -v cargo
```

## Phase 3 — Install ripgrep (optional, approval-gated)

If ripgrep is missing, show the recommended command and ask before running it.

### Windows

```powershell
# Preferred when available
winget install BurntSushi.ripgrep.MSVC

# Alternatives
scoop install ripgrep
choco install ripgrep
```

After installation, open a new terminal if `rg` is not immediately on `PATH`.

### macOS

```bash
brew install ripgrep
```

### Debian/Ubuntu

```bash
sudo apt-get update
sudo apt-get install -y ripgrep
```

### Fedora/RHEL

```bash
sudo dnf install -y ripgrep
```

### Arch Linux

```bash
sudo pacman -S ripgrep
```

### openSUSE/SLES

```bash
sudo zypper install ripgrep
```

### Cross-platform Cargo fallback

```bash
cargo install ripgrep
```

Use Cargo as a fallback when a native package manager is unavailable. Native packages are usually easier to update and uninstall.

### Manual release fallback

1. Open `https://github.com/BurntSushi/ripgrep/releases`.
2. Download the archive for the current platform.
3. Extract the `rg` / `rg.exe` binary.
4. Place it in a directory on `PATH`.
5. Open a new terminal and verify with `rg --version`.

## Phase 4 — Publish Copilot usage instructions (optional, approval-gated)

Copy this skill's reference `RIPGREP.md` to `<copilot_dir>/RIPGREP.md`, then reference it from `<copilot_dir>/copilot-instructions.md`. Default `copilot_dir` is `~/.copilot`.

Ask before writing unless non-interactive mode was explicitly requested.

### Manual steps

From this skill directory:

```bash
# macOS/Linux/Git Bash
mkdir -p ~/.copilot
cp RIPGREP.md ~/.copilot/RIPGREP.md
```

```powershell
# PowerShell
New-Item -ItemType Directory -Force "$HOME\.copilot" | Out-Null
Copy-Item .\RIPGREP.md "$HOME\.copilot\RIPGREP.md" -Force
```

Then add this section to `~/.copilot/copilot-instructions.md` if no ripgrep/RIPGREP.md reference already exists:

```md
## ripgrep Usage

See `RIPGREP.md` for ripgrep (`rg`) fast-search instructions. Prefer `rg` over recursive `grep`, `find`, or shell loops when searching repositories.
```

Rules for updating `copilot-instructions.md`:

- Preserve existing content.
- Do not add duplicate `RIPGREP.md` or ripgrep sections.
- If a ripgrep section exists but is stale, update it instead of appending another section.
- If the file does not exist, create it with the section above.

## Phase 5 — Verification

Re-run:

```bash
rg --version
```

Basic usage checks:

```bash
rg --files .
rg "ripgrep" .
```

If usage docs were published, verify:

```bash
# macOS/Linux/Git Bash
ls ~/.copilot/RIPGREP.md ~/.copilot/copilot-instructions.md
grep -n "RIPGREP.md\|ripgrep" ~/.copilot/copilot-instructions.md
```

```powershell
# PowerShell
Test-Path "$HOME\.copilot\RIPGREP.md"
Select-String -Path "$HOME\.copilot\copilot-instructions.md" -Pattern "RIPGREP.md|ripgrep"
```

## Output

Return:

```md
## ripgrep setup summary

### Decisions
- ripgrep install: Proceeded / Skipped / Not needed / Stopped
- ripgrep usage docs: Proceeded / Skipped / Not needed / Stopped

### Final status
- ripgrep available and verified with `rg --version`: ✔ / ✖ / skipped
- Basic `rg --files .` usage check passed: ✔ / ✖ / skipped
- `~/.copilot/RIPGREP.md` written and referenced from `~/.copilot/copilot-instructions.md`: ✔ / ✖ / skipped

### Notes
- <platform-specific commands used or skip rationale>
```
