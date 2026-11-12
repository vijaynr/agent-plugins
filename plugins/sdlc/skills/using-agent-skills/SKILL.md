---
name: using-agent-skills
description: Route SDLC lifecycle, engineering quality, project context, and dependency tasks. Use before selecting an SDLC skill or companion plugin.
---

# SDLC Router

Use **ASD-STE100 Simplified Technical English** for all end-user replies and artifact text. Read [the output language rules](../../references/output-language.md) once before the first reply or artifact. Include the requirement in delegated work.

## Load only what the task needs

1. Select one route below. Do not load a skill bundle, all references, or agent bodies for discovery.
2. Supporting skills have automatic invocation disabled. Read the selected `SKILL.md` explicitly before acting. Resolve local skill paths as `../<skill>/SKILL.md` from this file.
3. Follow the selected skill's required safety, verification, and reference instructions. Load optional references only for the current step.
4. Reuse instructions already in context. At a phase change, load only newly required guidance. Do not reread unchanged files just to repeat a routing preflight.
5. Keep approval gates. Routing does not authorize writes, commits, external updates, or shipping. Ask if ambiguity changes ownership or permissions.

## Local routes

| Task | Skill |
|---|---|
| spec, research, design, plan, build, review, ship, status, resume | `ai-sdlc` |
| Create feature workspace | `init-workspace` |
| Project preparation | `setup-project` |
| Generate project instructions / architecture | `generate-agents-md` / `generate-arch-md` |
| Official source verification | `source-driven-development` |
| Tests / debugging | `test-driven-development` / `debugging-and-error-recovery` |
| API contracts / frontend UI | `api-and-interface-design` / `frontend-ui-engineering` |
| Code review / simplification | `code-review-and-quality` / `code-simplification` |
| Security / high-stakes review | `security-and-hardening` / `doubt-driven-development` |
| Performance / observability | `performance-optimization` / `observability-and-instrumentation` |
| CI/CD / deprecation | `ci-cd-and-automation` / `deprecation-and-migration` |
| Documentation and decisions | `documentation-and-adrs` |
| Dependency audit / npm updates | `dependency-risk-audit` / `update-npm-deps` |
| Git conventions / diagrams | `git-workflow-guidelines` / `mermaid-diagrams` |
| Clarification / handoff | `grilling` / `handoff` |
| Actual custom-agent selection needed | `using-agents` |

## Companion routes

Use only the relevant installed plugin. Do not scan every plugin or read every router.

| Task | Plugin / router skill |
|---|---|
| GitLab | `gitlab` / `using-gitlab` |
| RPM packaging or internal OBS builds/submissions | `obs` / `using-obs` |
| ALM Octane | `octane` / `using-octane` |
| Black Duck | `blackduck` / `using-blackduck` |
| PRD or backlog shaping | `product-owner` / `using-product-owner` |
| RTK, ripgrep, or Caveman setup | `context-engineering` / `using-context-engineering` |
| OKF catalogs | `okf` / `using-okf` |
| Web capture or browser automation | `web-tools` / `using-web-tools` |

The full threat-model and Security Impact workflow is not bundled. Generic secure-design review does not replace that workflow. Report the unavailable capability instead of invoking a missing plugin or installing one automatically.

SDLC keeps ownership of lifecycle artifacts, status, commits, and shipping. Add supporting skills only for a concrete need. Do not turn every route into a mandatory gate.

Agent frontmatter defines preferred model defaults. See [Agent model defaults](../../../../docs/agent-models.md) only when model selection or escalation is relevant. Host overrides can apply; the defaults do not change approval gates.

For delegation, pass only the task, scope, relevant artifact paths, constraints, approval state, and evidence needed. Use the host's agent tool; keep agent instructions in its separate context. Require concise results with evidence and blockers, not transcripts. Preserve the independent `code-reviewer` and `review-critic` loop for `/review`. Send review agents the `sdlc_review_request` block from `ai-sdlc`, and send `codebase-researcher` one `sdlc_research_request` for each workspace.
