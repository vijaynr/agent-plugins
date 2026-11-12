# AGENTS.md

This repository is a plugin workspace.

Use the owning plugin's meta-skill first. Do not preload all skill, agent, or reference bodies. Read only the selected supporting instructions; reuse unchanged rules already in context. See `docs/context-loading.md` for the loading contract and host limits. Plugin-specific agent guidance lives under:

- `plugins/sdlc/AGENTS.md` — AI SDLC, setup, and artifact workflows.
- `plugins/obs/AGENTS.md` — Internal OBS RPM packaging, builds, and approved submissions.
- `plugins/octane/AGENTS.md` — ALM Octane backlog and work item workflows.
- `plugins/blackduck/AGENTS.md` — Black Duck vulnerability/component-review workflows.
- `plugins/gitlab/AGENTS.md` — GitLab issue and merge-request multi-agent workflows.
- `plugins/product-owner/AGENTS.md` — Product-owner PRD drafting and backlog-shaping workflows.
- `plugins/context-engineering/AGENTS.md` — local context-tooling setup workflows.
- `plugins/okf/AGENTS.md` — Open Knowledge Format catalog authoring and consumption workflows.

When working on a plugin, treat that plugin directory as the plugin root. Run plugin-local commands from that directory unless a command explicitly says otherwise.

When adding or materially changing scripts under `plugins/<plugin>/skills/<skill>/scripts/`, follow `docs/agent-skills-guide.md` and update related dependency/test documentation.
