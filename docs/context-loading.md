# Low-Context Plugin Loading

## Loading contract

Each plugin has one small router skill. It is the only skill in that plugin that permits automatic selection. Other skills set `disable-model-invocation: true`.

This flag stops relevance-based automatic skill invocation. It does not prevent a file read. After selecting a task route, the router explicitly reads the required skill file. This is how supporting instructions enter context. Direct user invocation remains available unless a skill already has a separate restriction. Existing commands and agent permissions stay unchanged.

| Plugin | Router |
|---|---|
| blackduck | `using-blackduck` |
| context-engineering | `using-context-engineering` |
| gitlab | `using-gitlab` |
| obs | `using-obs` |
| octane | `using-octane` |
| okf | `using-okf` |
| product-owner | `using-product-owner` |
| sdlc | `using-agent-skills` |
| web-tools | `using-web-tools` |

Routers select a path; they do not execute a full workflow. They load one primary skill and add support only for a concrete need. Required safety and verification references still apply. A token-saving rule must never remove approval gates, evidence, independent review, or the SDLC output-language requirement.

## Agent model defaults

See [Agent model defaults](agent-models.md) for the approved Haiku/Luna assignments, host overrides, escalation guidance, and model-selection checks. Model defaults do not change context-loading rules or approval gates.

## What the host controls

Copilot already uses progressive disclosure: skill names and descriptions support discovery; skill bodies load when selected. These repository changes limit automatic selection to routers. They do not force router bodies into every new conversation or remove all skill/agent metadata from the host's prompt.

There is no portable plugin switch that guarantees an initial context with exactly one skill and no other instructions across Copilot CLI and VS Code. The host can include system instructions, tool definitions, project rules, enabled-plugin metadata, and conversation history. An explicit slash command can also bypass router selection by design.

Use only the plugins needed for the current project. Disable others in the host's plugin manager. Avoid duplicate direct skill installations beside plugin installations. Keep project-wide instruction files small. Do not copy a router's full catalog into an always-loaded rules file.

## Context during work

- Use known agent metadata or a selected plugin's frontmatter. Do not read every agent body for discovery.
- Invoke agents through the host. Keep their instructions and investigation in separate agent contexts where supported. Do not paste them into the parent prompt.
- Give each delegated agent the task, scope, relevant paths, constraints, approval state, and evidence needed. A separate context reduces parent context; it does not guarantee lower total billed tokens.
- Read optional examples and references only for the current operation. Reuse unchanged instructions already in context.
- Use targeted file searches and bounded command output. Preserve failures and verification evidence. Do not hide errors to reduce output.
- Return concise findings, decisions, artifact paths, and blockers. Do not return transcripts or full documents unless required.
- Loading a file is not reversible within a conversation. Start a fresh session or use host compaction when changing to unrelated work. Preserve current decisions and blockers in a short handoff.

## Verify in Copilot CLI and VS Code

After updating or reinstalling plugins, start a fresh session in each host. Do not use an old conversation as a startup measurement.

1. Confirm that only the router in each enabled plugin allows automatic skill invocation. Confirm that direct skills and commands still appear where intended.
2. Make a narrow request, such as a GitLab issue read or web capture. Inspect the host's tool/context trace. Expect the owning router and selected skill, not every skill body.
3. Invoke a supporting skill directly. Confirm that its instructions still load without enabling automatic invocation.
4. Request an agent-led workflow. Confirm that only the selected agent and required stages run. Verify that approval gates still stop writes.
5. Compare the same task, model, plugin set, and fresh-session state before and after the change. Record host version, input tokens, output tokens, tool output, and agent usage separately. Use actual host usage reports, not character counts, as token evidence.

Check router frontmatter, local links, and the plugin roster during review. These source checks cannot prove that a host followed a route or measured token savings. Run the workspace helper from the repository root:

```bash
./agents.sh validate
```

## Sources

- [VS Code Agent Skills](https://code.visualstudio.com/docs/agent-customization/agent-skills): progressive disclosure and invocation flags.
- [Copilot CLI command reference](https://docs.github.com/en/copilot/reference/copilot-cli-reference/cli-command-reference): skill frontmatter and direct invocation.
- [Copilot CLI plugin reference](https://docs.github.com/en/copilot/reference/copilot-cli-reference/cli-plugin-reference): plugin components and management.

Do not use `user-invocable: false` as a token-saving substitute. It hides a skill from the user menu but does not stop automatic selection. Do not change agent invocation flags as if they were skill flags; writer-agent restrictions must stay intact.
