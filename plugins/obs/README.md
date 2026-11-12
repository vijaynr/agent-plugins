# OBS RPM Packaging Toolkit

Package RPMs with the team's internal Open Build Service (OBS). This plugin uses the existing `osc` client for package edits, builds, build-log diagnosis, review, and approved submit requests.

## Entry points

Start with `skills/using-obs/SKILL.md`. It explicitly reads `skills/setup-obs/SKILL.md` for system/login setup or `skills/rpm-packaging/SKILL.md` for package work. References load only for the current operation. Do not install a second copy of the same skills beside this plugin.

```bash
copilot plugin install obs@vnr-agent-development-toolkit
```

For a development install from the repository root:

```bash
copilot plugin install plugins/obs
```

## Guided system setup

Invoke the `obs-setup` command with an optional internal API URL, or ask: “Help me configure osc for our internal OBS server.” Use the command invocation syntax supplied by your host.

The guide checks the selected Linux, Windows/WSL, macOS, or remote environment. It asks before installation or local configuration changes. You enter credentials in a private terminal, never in chat or an agent shell. Choose an approved OS keyring backend; plaintext and obfuscated stores are not accepted. Existing working host configuration is preserved. A transient store is manual-only and cannot support unattended agent use.

After private setup, the guide verifies approved read-only access and can create a non-secret workspace `OBS.md` after you review its content/diff. It reports connection, authentication, workspace, and local-build prerequisites separately. Public metadata access alone does not prove authentication. There are no package uploads, submissions, or builds during setup.

See [setup-obs](skills/setup-obs/SKILL.md) and its [source-backed research notes](skills/setup-obs/references/research.md) for details and failure handling. The guide does not create a second credential store or require a new runtime dependency.

## Workspace setup

Use guided setup or create a non-secret `OBS.md` in the consuming workspace using the [workspace template](skills/rpm-packaging/references/workspace.md). Supply projects, package names, repositories, architectures, build mode, approved Linux environment, and release policy. Explicit task values can override workspace values after conflicts are resolved.

Local builds need an approved isolated Linux environment, the OBS build tool, and the target RPM toolchain. Use `rpmlint` and internal validators when policy requires them. Client connection setup does not prove build readiness.

There is no built-in server URL, credential manager, or new Python dependency. No helper scripts are included in this version. Every OBS command names the selected API URL explicitly. Missing configuration blocks the operation instead of falling back to a public server.

## Example prompts

- “Run obs-setup to configure our internal OBS client. Ask before installing tools.”
- “Use the OBS workspace configuration to review this spec and changes file. Do not upload anything.”
- “Build this RPM for the repositories and architectures in OBS.md using our approved VM.”
- “Diagnose the failed OBS build for this project/package and propose a minimal fix.”
- “Prepare an OBS submit request for the tested revision. Show the exact targets and ask before writing.”

Local edit approval does not authorize a server commit. Source commits and submit requests have separate approval gates and read-back checks. Reviewers accept requests; the plugin does not automatically accept, publish, or delete sources. Prompt rules are not a server-side permission control. Use least-privilege credentials and host execution permissions.

## Scope and provenance

This is a focused adaptation of [openSUSE/openSUSE-packaging-skill](https://github.com/openSUSE/openSUSE-packaging-skill), not a full import. See [UPSTREAM.md](UPSTREAM.md) and [LICENSE](LICENSE). Public openSUSE release routes, public forge/bug integrations, maintenance, signing, and Git/scmsync workflows are not included. Internal policies must be supplied by the workspace owner.

## Offline verification

This instruction-only plugin has no script tests. Review registration, local references, routing, explicit-host examples, and setup/safety/provenance instructions manually. Run `./agents.sh validate` from the repository root. These checks do not execute `osc`, contact OBS, or prove server/client compatibility. A live pilot needs separate permission and real workspace targets.
