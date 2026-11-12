---
name: "gitlab"
disable-model-invocation: true
description: "GitLab CLI for projects, issues, merge requests, pipelines, code-quality attachment reports, wikis, milestones, labels, branches, commits, and repository metadata."
license: MIT
compatibility: >
  Requires uv (https://docs.astral.sh/uv/) installed and on PATH.
  Requires Python 3.10+. Needs network access to the GitLab instance.
  Works with gitlab.com and self-hosted GitLab.
---

# GitLab CLI

Use this skill to interact with GitLab through the bundled Python CLI.

## Steps

0. Resolve the GitLab context.
   - Resolve the GitLab skill root in this order: `plugins/gitlab/skills/gitlab` in this repository, an installed plugin at `~/.copilot/installed-plugins/*/gitlab/skills/gitlab`, then direct user skill roots.
   - Do not perform login, credential setup, keyring reads, or credential preflight in this skill. A plugin-local `.env` is not required: normal authentication uses OS keyring service `AgentDevelopmentToolkit:gitlab` plus stable profile metadata. Metadata is `%APPDATA%\AgentDevelopmentToolkit\gitlab.json` on Windows, `~/Library/Application Support/AgentDevelopmentToolkit/gitlab.json` on macOS, and `${XDG_CONFIG_HOME:-~/.config}/agent-development-toolkit/gitlab.json` on Linux; `AGENT_DEVELOPMENT_TOOLKIT_CONFIG_HOME` overrides the directory.
   - Select a named profile with API `--profile <name>` when the user identifies one. Otherwise selection is `GITLAB_PROFILE`, then the active profile. Keep endpoint, token source, default project, allowlist, and read-only mode from one coherent source; never fall back a self-hosted credential to `gitlab.com`.
   - If the CLI reports missing/invalid authentication, stop tool work and direct the user/agent to `gitlab-login`. For a new profile, login may read fallback values with `uv run scripts/gitlab_token.py defaults`. For an update, those defaults are not the existing profile: require explicit confirmation of every project/safety setting. Require the token every time, inject `GITLAB_LOGIN_TOKEN` through the launcher's masked environment without putting its value in command text, and run:
     ```bash
     uv run scripts/gitlab_token.py login --profile "<name>" --api-url "<api-url>" --user "<keyring-username>" --project-id "<id>" --allowed-project-ids "<ids>" --read-only-mode "<true-or-false>" --timeout "<seconds>"
     ```
   - Load `references/full-reference.md` for profile lifecycle, migration/recovery, command syntax, or triage flows.
   - Completion criterion: project/group/resource identifiers and auth requirements are known.

1. Execute the narrowest command.
   - Prefer read/list commands before writes. Invoke `uv run scripts/gitlab_cli.py [--profile <name>] ...`.
   - Treat local read-only and project-allowlist rejection as a safety result; do not bypass it with environment overrides.
   - Use explicit project IDs/paths and pagination/filter options where available.
   - Completion criterion: JSON output is parsed into the requested answer or action plan.

2. Verify writes.
   - After creating/updating GitLab resources, fetch them back.
   - Completion criterion: final state is confirmed or the write failure is reported.
