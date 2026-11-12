---
name: using-obs
description: Route internal OBS setup and login guidance, RPM packaging, spec and changes edits, osc builds, build failures, and package submission requests.
---

# OBS Router

Select one route and read the selected file explicitly before acting:

- System/client setup, API URL configuration, credentials, or login problems: [setup-obs](../setup-obs/SKILL.md). The `obs-setup` command starts the same guided workflow.
- RPM package authoring, updates, reviews, builds, build-log diagnosis, or OBS submissions: [rpm-packaging](../rpm-packaging/SKILL.md).

Do not load all reference bodies or upstream skill files. The setup skill asks for the environment and URL; the packaging skill loads workspace configuration first. Load only references required for the selected operation. Resolve paths relative to this file.

Keep approval gates. Routing is not approval for server writes, credential access, privileged builds, or submission. Missing server details must produce a question, never a public OBS fallback. GitLab pipelines remain owned by the GitLab plugin; general CI/CD remains owned by SDLC.
