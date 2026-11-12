---
name: "blackduck"
disable-model-invocation: true
description: "Black Duck CLI for project/version discovery, BOM components, vulnerabilities, code locations, and remediation status updates."
compatibility: >
  Requires uv (https://docs.astral.sh/uv/) installed and on PATH.
  Requires Python 3.10+. Requires network access to a Black Duck instance.
---

# Black Duck CLI

Use this skill for Black Duck project/version, BOM, vulnerability, code-location, and remediation-status work.

## Steps

0. Resolve the project/version.
   - Resolve the Black Duck skill root in this order: `plugins/blackduck/skills/blackduck` in this repository, an installed plugin at `~/.copilot/installed-plugins/*/blackduck/skills/blackduck`, then direct user skill roots.
   - Do not perform login, credential setup, keyring reads, or credential preflight in this skill. A plugin-local `.env` is not required: normal authentication uses OS keyring service `AgentDevelopmentToolkit:blackduck` plus stable profile metadata. Metadata is `%APPDATA%\AgentDevelopmentToolkit\blackduck.json` on Windows, `~/Library/Application Support/AgentDevelopmentToolkit/blackduck.json` on macOS, and `${XDG_CONFIG_HOME:-~/.config}/agent-development-toolkit/blackduck.json` on Linux; `AGENT_DEVELOPMENT_TOOLKIT_CONFIG_HOME` overrides the directory.
   - Select a named profile with API `--profile <name>` when the user identifies one. Otherwise selection is `BLACKDUCK_PROFILE`, then the active profile. Keep URL, token source, and SSL-verification policy coherent; never invent a host fallback.
   - If the CLI reports missing/invalid authentication, stop tool work and direct the user/agent to `blackduck-login`. For a new profile, login may read fallback values with `uv run scripts/blackduck_token.py defaults`; for an update, explicitly confirm URL and SSL behavior. Require the token every time, inject `BLACKDUCK_LOGIN_TOKEN` through the launcher's masked environment without putting its value in command text, and run:
     ```bash
     uv run scripts/blackduck_token.py login --profile "<name>" --url "<url>" --user "<keyring-username>" --verify-ssl "<true-or-false>"
     ```
   - Load `references/full-reference.md` only for profile lifecycle, migration/recovery, exact command syntax, filters, status values, or troubleshooting.
   - Completion criterion: project and version hrefs/IDs are known.

1. Read before deciding.
   - Run `uv run scripts/blackduck_vulnerabilities.py [--profile <name>] ...`.
   - List components or vulnerabilities with the narrowest filters.
   - Fetch details/code locations only for selected items.
   - Completion criterion: every decision has Black Duck evidence.

2. Write only when explicitly requested.
   - Apply one remediation/status update at a time.
   - Verify each write with a read command.
   - Completion criterion: requested Black Duck state is confirmed or no write occurred.
