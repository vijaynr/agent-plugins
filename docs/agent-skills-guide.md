# Agent Skills Guide

This guide is the opinionated repository guide for creating and maintaining agent skills in this plugin workspace, especially executable scripts under `plugins/<plugin>/skills/<skill>/scripts/`.

Start with the local [Agent Skills Specification](../specs/agent-skills-spec.md), which points to the upstream agent skills standard. This guide builds on that spec with Agent Development Toolkit workspace conventions: where skill files live, how scripts are named, how dependencies are declared, how CLIs behave, and how changes are validated in this repo.

## Context loading

Follow [the low-context loading contract](context-loading.md). Each plugin has one small router that permits automatic skill selection. Other skills must set `disable-model-invocation: true` and remain reachable through the router's explicit file reads. Keep direct user invocation unless there is a separate reason to restrict it. Update the router and plugin roster when adding a plugin. Review frontmatter and local links manually. Keep required safety and verification references; make optional examples lazy.

## When to add a script

Add a script when a workflow needs deterministic behavior that is better handled by code than by model instructions, for example:

- calling an external API,
- parsing URLs or structured files,
- validating or updating generated artifacts,
- performing repeatable setup checks.

Keep scripts small and task-focused. Put workflow orchestration in the skill or agent markdown; put deterministic mechanics in scripts.

## Location and naming

Place scripts under the owning skill:

```text
plugins/<plugin>/skills/<skill>/scripts/<script_name>.py
```

Rules:

- Use `snake_case.py` for Python script names.
- Keep reusable helper modules under `scripts/<package>/` when needed.
- Do not write generated files beside scripts unless they are intentional fixtures/templates.
- Do not commit `__pycache__/`, `*.pyc`, `.env`, tokens, generated workspaces, or machine-local outputs.

## Runtime and dependency metadata

Every top-level Python script that imports third-party packages must declare inline PEP 723 metadata at the top of the file:

```python
#!/usr/bin/env python3
# /// script
# requires-python = ">=3.9"
# dependencies = [
#   "requests>=2.28,<3",
#   "python-dotenv>=1.0,<2",
# ]
# ///
```

Run dependency-backed scripts with `uv run` from the skill root:

```bash
cd plugins/gitlab/skills/gitlab
uv run scripts/gitlab_cli.py --help
```

Scripts that use only the Python standard library may run with `python` directly, but they may still include PEP 723 metadata for consistency.

### External tools

Some workflows require external applications in addition to Python packages:

- `uv` for running scripts with PEP 723 dependency metadata.
- Git for repository-relative plugin development helpers.

### Current third-party Python packages

| Area | Packages | Notes |
|---|---|---|
| GitLab skill | `requests`, `python-dotenv`, `keyring` | API access and keyring-backed token storage. |
| Octane skill | `requests`, `python-dotenv`, `keyring` | API access and keyring-backed client-secret storage. |
| Black Duck skill | `requests`, `python-dotenv`, `keyring` | API access and keyring-backed token storage. |

### Dependency maintenance rule

When adding a script that imports a third-party package, either:

1. add PEP 723 dependency metadata to that script, or
2. document why the dependency is provided by the host runtime in this guide.

The pytest skill CLI smoke suite (`tests/test_skill_cli_smoke.py`) verifies the API-backed skill CLIs and catches missing dependency metadata for scripts it cannot execute directly.

## Command-line interface conventions

Scripts intended for agent use should provide a predictable CLI:

- Use `argparse` or an equivalent standard parser.
- Support `--help` without requiring credentials, network access, or local config.
- Prefer subcommands for multi-operation CLIs.
- Use explicit arguments instead of interactive prompts.
- Fail fast when required arguments are missing.
- Return non-zero exit codes for errors.

Good pattern:

```bash
uv run scripts/example_client.py list-items --project "My Project" --limit 20
```

Avoid:

```bash
python script.py
# then prompt interactively for project, token, action, output path, etc.
```

Agents can ask users for missing values; scripts should execute the already-decided action.

## Output conventions

Prefer machine-readable JSON for script output, especially for scripts called by agents.

Recommended success shape:

```json
{
  "ok": true,
  "items": [],
  "warnings": []
}
```

Recommended error shape:

```json
{
  "ok": false,
  "error": "Missing required argument: --project",
  "recovery": "Run with --project <name> or ask the user for the project name."
}
```

Guidelines:

- Print parseable result data to stdout.
- Send diagnostics and tracebacks to stderr.
- Include stable IDs, URLs, paths, and verification details in write results.
- Avoid prose-only output for data that another agent or script must parse.

## Credentials and secrets

Never ask for secrets through normal script prompts or commit secrets to the repository.

For service integrations, use the durable profile convention:

- Store secrets only in the OS credential store under `AgentDevelopmentToolkit:<service>`. Keep these generic names stable across future releases. This rename intentionally requires existing users to log in again; old branded profile/keyring entries are not read, moved, or removed.
- Store non-secret profile metadata in service-specific JSON under the platform user config directory: `%APPDATA%/AgentDevelopmentToolkit` on Windows, `~/Library/Application Support/AgentDevelopmentToolkit` on macOS, and `${XDG_CONFIG_HOME:-~/.config}/agent-development-toolkit` on Linux. Honor `AGENT_DEVELOPMENT_TOOLKIT_CONFIG_HOME` in every plugin and test. Require a configured service endpoint; do not supply a default host.
- Keep the profile module plugin-local so each standalone plugin remains independently installable. Use Python standard-library filesystem/JSON primitives rather than adding a configuration dependency.
- Support named profiles, one optional active profile, and precedence of API `--profile`, service profile environment variable, then active profile.
- Resolve endpoint, keyring locator, and safety settings as one coherent source. Reject partial credential overrides before keyring/network access; never pair a self-hosted credential with a default host.
- Treat plugin-local `.env` as legacy/CI input, not required state. Complete direct credentials may remain a CI fallback, but secrets are never migrated into stable JSON.
- Migrate only one unambiguous, usable keyring-backed legacy candidate. Deduplicate canonical path aliases, preserve source bytes, and fail closed on conflicts or keyring errors.
- Serialize mutations with a bounded cross-process lock and write UTF-8 JSON through a flushed/fsynced sibling temporary file plus atomic replacement. Lock files record only owner PID/timing metadata, recover dead owners and sufficiently old metadata-free legacy sentinels, and must never reclaim a live owner's lock. Use restrictive permissions where supported.
- Make login transactional across metadata, keyring writes, and bounded remote verification. Release the mutation lock before network verification, then use compare-and-swap checks for rollback/commit confirmation so an older failed login never overwrites a newer update. Preserve exact prior metadata bytes and report superseded or incomplete rollback rather than hiding it.
- Ensure `--help` never requires credentials, migration, network access, or local configuration.

Credential setup scripts should:

1. expose `defaults`, `login`, `profiles`, `use-profile`, and `delete-profile` operations while retaining documented compatibility helpers,
2. support non-interactive login with secret values injected through a masked launcher environment—not normal chat or command text,
3. persist only non-secret endpoint/locator/safety metadata and never enumerate keyring contents,
4. verify the named profile with a minimal read operation,
5. distinguish missing metadata, missing keyring entry, keyring backend failure, remote 401, and remote 403 without emitting secrets,
6. delete profile metadata without deleting the underlying keyring credential.

Agent and skill guidance must resolve the adjacent repository/standalone/user skill root, rely on stable profiles without keyring preflight, propagate explicit profile selection, and route authentication failures to the owning login command.

## Safety and write operations

Scripts that perform writes must be conservative:

- Require all target identifiers explicitly.
- Validate action values before writing.
- Do exactly one write operation or one clearly bounded transaction.
- Verify the resulting state with a read after writing.
- Emit enough evidence for the orchestrator to report what changed.

Write decisions belong in the orchestrating agent/skill after user confirmation. Write scripts execute the pre-approved action; they must not invent remediation statuses, labels, assignments, or content.

### Local SDLC status saves

The SDLC status writer keeps its existing cross-process lock and atomic sibling-file replacement. It flushes, fsyncs, and closes the temporary file before replacement. Native Windows errors 5 (access denied), 32 (sharing violation), and 33 (lock violation) can be transient even with an advisory writer lock.

Local retry policy: at most ten replacement attempts, with a 0.05-second wait between attempts (at most nine waits). Retry the same closed temporary file. Do not unlink the destination, change permissions, bypass the lock, retry unrelated errors, or hide a persistent failure. Failed replacement preserves the previous status; the existing temporary-file cleanup still applies. This policy does not identify which process holds a file open or guarantee recovery from all filesystem interference.

Sources: Python [`OSError.winerror`](https://docs.python.org/3/library/exceptions.html#OSError.winerror) identifies native Windows codes; Microsoft documents [system error codes 5, 32, and 33](https://learn.microsoft.com/en-us/windows/win32/debug/system-error-codes--0-499-). The retry count and delay above are this repository's policy, not a vendor recommendation. No new dependency is required.

### Write approval trust boundary

The workspace intentionally treats the orchestrating agent and its host conversation as the write-approval boundary. General-purpose service CLIs do not distinguish an agent from a human operator and do not require a forgeable `--confirmed` flag or environment variable. Direct invocation therefore means the caller is already authorized to perform the requested operation.

This is an explicit accepted-risk decision, not a claim that prompt instructions are a cryptographic authorization control. Deployments that allow untrusted autonomous execution must constrain writes outside the model—for example with read-only service credentials, GitLab read-only/allowlist profiles, process sandboxing, or host tool permissions. Revisit this decision if the host adds a trusted, unforgeable, short-lived approval capability that can bind profile, target, action, and payload; do not emulate such a capability with model-supplied command arguments.

## Paths and portability

- Use `pathlib.Path` in Python.
- Accept repository-root-relative paths where practical.
- Avoid hard-coded absolute paths.
- In markdown examples, prefer forward slashes so commands work in Git Bash and are not misread as escapes.
- Resolve script-relative templates with `Path(__file__).resolve()`.

## Testing and validation

Before merging a script change, run the pytest validation suite:

```bash
python -m pytest tests plugins/okf/tests -q
```

For focused script smoke coverage, run:

```bash
python -m pytest tests/test_skill_cli_smoke.py -q
```

For the current cleanup, keep and update existing tests only for active plugin/skill scripts. Do not add test files or cases for scripts that lack them. Keep tests deterministic and avoid live service calls. See [testing-guidelines.md](testing-guidelines.md) for repository test conventions.

The current validation suite checks that:

- top-level scripts with known third-party imports have PEP 723 metadata,
- API-backed CLIs expose `--help`,
- supported script syntax and credential behavior remain valid.

Review metadata, routes, links, and generated-artifact exclusions manually and run `./agents.sh validate`. Structural pytest suites are not retained.

## Minimal script template

```python
#!/usr/bin/env python3
# /// script
# requires-python = ">=3.9"
# dependencies = []
# ///
from __future__ import annotations

import argparse
import json
import sys


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Do one deterministic skill task")
    parser.add_argument("--input", required=True, help="Input value to process")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        result = {"ok": True, "input": args.input}
        print(json.dumps(result, indent=2))
        return 0
    except Exception as exc:
        print(json.dumps({"ok": False, "error": str(exc)}), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
```

## Documentation checklist

When adding or materially changing a skill script:

- Update the owning `SKILL.md` with the command, inputs, outputs, and safety rules.
- Update the plugin `README.md` if user-facing behavior changes.
- Update `.env.example` when non-secret configuration changes.
- Update this guide when dependencies or external tools change.
- Update existing script/smoke tests when the CLI surface changes. Do not add tests in the current cleanup.
