# Agent model defaults

The repository defines a single `model` value in each plugin agent's YAML frontmatter. These are preferred defaults, not strict model locks. The approved allocation is **12 Claude Haiku 5.5 agents and 12 GPT-6 Luna agents**.

Use Haiku for bounded retrieval, classification, evidence checks, and pre-approved updates. Use Luna for coordination, planning, implementation, and security analysis. This allocation is a starting policy, not a measured comparison of model quality.

## Assignments

The files are under `plugins/<plugin>/agents/<agent>.agent.md`.

| Plugin | `claude-haiku-5.5` | `gpt-6-luna` |
|---|---|---|
| blackduck | `bd-discovery`, `bd-vuln-triage`, `bd-component-triage`, `bd-remediator`, `bd-component-updater` | `blackduck`, `bd-cve-researcher`, `bd-code-evidence` |
| gitlab | `gl-triager`, `gl-researcher`, `gl-operator` | `gitlab-agent`, `gl-planner` |
| octane | `oct-triager`, `oct-researcher` | `octane-agent`, `oct-planner`, `oct-implementer` |
| product-owner | None | `product-owner` |
| sdlc | `codebase-researcher`, `review-critic` | `code-reviewer`, `security-auditor`, `test-engineer` |

## Host limits

- The authored values use Copilot runtime model IDs. Check their availability in the intended session's model picker. Plan access and administrator policy can restrict models.
- In Copilot CLI, select an explicit session model. With the session set to Auto, subagents inherit the resolved session model regardless of their `model` value.
- VS Code's Copilot harness and Local harness differ. Copilot uses runtime model IDs. Local uses qualified model display names inserted by editor completion. For Local-only installations, select the equivalent model through completion rather than assuming that a runtime ID resolves.
- Local's explicit `runSubagent` model parameter takes precedence over the agent's default. Cost-tier restrictions can also prevent a selection.
- No fallback lists are authored. This does not disable fallback or overrides in the host. Do not rely on plugin metadata to enforce an exact-model-or-fail policy.
- This change does not modify tools, invocation restrictions, prompts, approval gates, or the user's session settings.

## Review and escalation

Both models are lightweight models. Keep a human or stronger-model review path for uncertain vulnerability reachability, threat dismissal, risk classification, complex code changes, and unresolved review disagreements. Do not treat missing evidence as proof of safety. Use deterministic tools for CVSS arithmetic.

Haiku's `review-critic` assignment provides a different model family for evidence checks. It does not guarantee independent reasoning or replace specialist review. Escalation is an operating recommendation; this metadata change does not add an automatic escalation mechanism.

## Verification

Review each agent's single `model` value against the assignment map. Check that no `models` list overrides it. Dedicated model/frontmatter/agent-contract pytest checks are not retained because they do not test plugin scripts. Manual source review does not prove runtime model selection or model access.

After updating the plugins, start a fresh session in each intended host. Run one bounded read-only Haiku task and one bounded read-only Luna task. Inspect the host's subagent trace for the actual model. Do not use external writes as a model-selection smoke test. Compare cost per accepted result, including retries and corrections, before changing this allocation.

## Sources

- [GitHub supported models](https://docs.github.com/en/copilot/reference/ai-models/supported-models)
- [GitHub model comparison](https://docs.github.com/en/copilot/reference/ai-models/model-comparison)
- [Copilot CLI custom-agent frontmatter](https://docs.github.com/en/copilot/reference/copilot-cli-reference/cli-command-reference#custom-agent-frontmatter-fields)
- [VS Code custom-agent model preferences](https://code.visualstudio.com/docs/agents/reference/custom-agent-file-reference#_model-preferences)
- [VS Code Local subagent model selection](https://code.visualstudio.com/docs/agents/run/subagents#_select-the-model-for-a-subagent)
