---
name: using-agents
description: Select a custom agent for independent review, workspace research, test/security analysis, or an agent-led domain workflow. Load only after the SDLC router selects agent work.
disable-model-invocation: true
---

# Select an Agent

Use **ASD-STE100 Simplified Technical English** for end-user replies and artifact text. Follow [the output language rules](../../references/output-language.md), including for delegated work. Reuse these rules if already in context.

## Bounded discovery

1. Prefer an explicit agent name or the host's available-agent metadata. Do not scan the repository or every installed plugin when the agent is already known.
2. For local SDLC work, use the relevant candidate below. For a domain workflow, use that plugin's router and orchestrator.
3. Only if the host cannot identify a candidate, inspect filenames and YAML frontmatter in the owning plugin's `agents/` directory. Search project `.github/agents/` or user agent locations only if the owning location has no match. Read names and descriptions, not all agent bodies.
4. Respect declared `agents`, tools, handoffs, visibility, and invocation restrictions. Never bypass a disabled writer by reading its instructions and acting as that writer.

| Task | Candidate |
|---|---|
| Multi-workspace research | `codebase-researcher` through `ai-sdlc` research |
| Independent code review | `code-reviewer`, then independent `review-critic` |
| Audit findings and consolidate review | `review-critic` |
| Tests and coverage gaps | `test-engineer` |
| Secure design review | `security-auditor` |
| GitLab / Octane / Black Duck / product workflows | Owning plugin's orchestrator |

Use the host's agent tool. Let the selected agent load its own instructions and supporting skills. Do not copy agent bodies or the full parent conversation into delegated prompts. Pass the task, scope, relevant paths, identifiers, constraints, approval state, and evidence needed. Ask for concise findings, evidence paths, verification, and blockers; do not request raw logs.

## Safety and fallback

Prefer orchestrators for broad workflows. Use internal subagents only as their owning workflow permits. The full threat-model and Security Impact workflow is not bundled; do not silently replace it with generic security review or invoke missing agents. Preserve independent review and critic separation. Routing is not write approval. Ask and stop if candidate choice changes writes or artifact ownership.

If invocation is unavailable, report the selected agent name/path and the limitation. Offer a safe skill fallback only with the required confirmation. Do not silently reroute a failure to a writer. Report missing candidates and the bounded locations searched.
