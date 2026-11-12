# Implementation Plan: Open-Source Readiness

## Current cleanup override

The latest owner request replaces conflicting historical scope below. The current session owns the existing task checkout. Keep the branch and recorded base; do not create a new task or MR.

Task / feature slug: open-source-readiness
Repository | Role | Checkout / ref | Commit SHA | Reason
agents | read/write | topic-open-source-readiness | 376bb776fa63baa845a699f5de7ba6c0bfeb8b86 | Continue the owner-requested cleanup
Authoritative source project: configured origin, portfolio/wpg/filr/agents.
Destination: existing agents task checkout; future target main; original base 4533df1f6a5b4213a7ddde5666ec07af0ddaf65c.
Writer: this session; delegate only disjoint files. Preserve the pre-existing branch-guideline description edit.
Publication: not requested. No existing MR is recorded. Live remote state is not checked for this local-only task.

1. Rename branding to Agent Development Toolkit, author vnr, marketplace ID vnr-agent-development-toolkit.
2. Rename credential storage with no legacy branded fallback. Require configured service endpoints. Existing users must log in again.
3. Remove CI, the banner, Office, JATO UI, and active routes/registrations.
4. Generalize Git guidance and Octane examples. Remove tests that do not exercise active plugin/skill scripts. Add no tests.
5. Run retained script suites separately, workspace validation, reference checks, and diff checks. Record results in tasks/todo.md.

This coupled cleanup supersedes the old five-file batches and retained-plugin requirements. Keep historical evidence and Git history unchanged.

## Review Status

Approved for local autonomous execution. The user explicitly approved the spec, this plan, a preparatory planning commit, and per-task local commits.

Read [the spec](../SPEC.md) first. Auto mode removes routine stepping between tasks. It does not remove owner decisions or high-risk approval gates. Legal, credential, history, CI, and publication gates remain separate.

**Latest scope takes precedence:** The user now directs removal of the entire threat-modelling plugin, not further replacement work inside it. Execute the active removal queue below before any remaining retained-plugin work. The old threat-plugin implementation/retirement tasks are historical or superseded, not pending implementation instructions.

Planning changed only task documents. The previous OKF task list is preserved byte-for-byte at [archive/okf-todo.md](archive/okf-todo.md). Its SHA-256 is `67b05eb176763c7deaca9551ae48f79664e1002373c0dfaebc9ad34b7bef61d2`. The archive is internal material, not part of a public deliverable.

## Active Scope Change: Remove the Threat-Modelling Plugin

### Current Execution Override: Approved Atomic Cutover

The owner selected `Atomic cutover (Recommended)` after the separate Windows prerequisite `e4af183` and public deregistration `0c94346` passed their gates. This is a narrow exception to the five-file rule, not extra deletion/publication scope. **Execute one atomic removal task instead of old Tasks 28-33 and the 38 payload batches below.** Those staged instructions are superseded execution detail, not additional pending work.

**Acceptance:** Remove the exact 182 tracked plugin paths at `e6a47c1`, plus the approved root guide/deck. Update coupled SDLC/JATO routes, context/model rosters, docs index/helper/testing guidance, and feature-specific test consumers together. Keep all 11 other plugins, every Office Word contract, generic security review, independent Octane APIs, user files/reports, and history. Retain both removed-component notices until covered files are gone in the working tree; do not change external notices. Do not add model-discovery filters or skip failing tests.

**Verification:** Add persistent feature-absence/retained-capability contracts and observe RED first. Review the exact current tracked/untracked state and immutable removal inventory before deleting. Remove only recorded tracked paths; stop on local changes/collisions. Run focused Office/model/discovery/absence tests, every existing separate regression suite, workspace validation, compile/help checks, and source/link/diff review. Get fresh read-only scope review before deletion and fresh diff review before the one retirement commit. Record intentional passing-feature test removal counts. No partial completion/commit or public-release claim.

**Write scope outside the 184 removals:** `plugins/sdlc/AGENTS.md`, `plugins/sdlc/skills/using-agent-skills/SKILL.md`, `plugins/sdlc/skills/using-agents/SKILL.md`, `plugins/jato-ui/skills/using-jato-ui-skills/SKILL.md`; `docs/{README,agent-models,agent-skills-guide,testing-guidelines,context-loading}.md`; `tests/test_{public_plugin_surface,lazy_loading,plugin_skill_discovery,agent_models,office_public_workflows}.py`; and the three existing task artifacts. Split/reconcile any newly discovered dependent path before writing it. Runtime code outside the removed component is unchanged by this cutover.

**Dependencies and result:** User removal/companion/atomic choices and prerequisite commits are complete. Fresh pre-deletion and final diff reviews approved the scope with no findings. RED/GREEN, focused/full gates, protected-tree/source/link checks, workspace validation, and compile/help/diff checks pass. The atomic cutover is complete; commit all 184 deletions and 17 coupled/artifact modifications together, not a deletion-only index. See the final ledger entry for exact counts and remaining release gates.

### User Decision and Evidence

The user explicitly said the plugin is not required in the open-source toolkit. This replaces the narrow two-template retirement proposal and the earlier requirement to preserve a full threat-model workflow. No replacement workflow is required. Keep the previous commits and evidence; do not reset, revert unrelated work, or rewrite history.

At source HEAD `e6a47c14b36f7d982dd05c6c1afbb3327a096e76`, `plugins/threat-modelling/` contains **182 tracked files**: 55 Markdown, 31 Python, 78 XSD, 5 XML, 3 PowerShell, 3 shell, 2 license text, 2 XLSX, and one each of PNG, JSON, and DOCX. These counts include the recently authored local helper and guides. At inventory time, no plugin file had been removed.

Verified integration points include both marketplace manifests; root README/AGENTS; SDLC companion/agent routing; JATO companion guidance; context/model/script/test documentation; explicit lazy-loading/model/discovery declarations; and shared Word tests. The dedicated root guide and slide deck have separate proposed dispositions below.

Retain the Office helper and generic security-auditor workflow. Retain independent Octane APIs, field-update support, and its report-description references unless a separate content audit identifies a problem. Their security terminology is not a plugin dependency. Do not delete by a broad `threat*` keyword match.

### Routing and Permissions

- Read/write only the existing `agents` task checkout on `topic-open-source-readiness`. Preserve base `4533df1f6a5b4213a7ddde5666ec07af0ddaf65c`; the removal inventory is pinned independently to `e6a47c1`.
- Keep the same intended private project/default target and sole writer. No push, MR, public host/destination, visibility change, or installed-host plugin removal is authorized.
- The user's whole-plugin direction authorizes the component withdrawal; do not treat the old two-file review as review of this expanded scope. Obtain a fresh read-only review of the expanded removal sequence before deletion.
- The owner explicitly selected `Retire both (Recommended)` for `docs/threat-modelling.md` and `slides/sdd-threat-modelling-process.pptx`. Retire these two companions and update their links in Task 32. The old two-template proposal is superseded, not separately pending.
- Preserve all user-generated reports, untracked/ignored user files, other plugins, license notices outside the removed component, and Git history/refs. Stop if a target differs from its recorded task-owned state.

### Dependency Graph

```text
27: deregister public entry points
  -> 28: remove obsolete consumer routes
  -> 29: deactivate local discovery and feature-specific test consumers
  -> 30: bounded payload retirement
       -> three agent batches, each with the matching explicit model-map update
       -> thirty-four non-agent payload batches
       -> one final notice-only batch after all covered material is gone
  -> 31: align retained helper/model/test guidance
  -> 32: dedicated root guide/deck disposition (owner decision)
  -> 33: complete feature-absence regression and reference review
  -> resume retained-plugin Tasks 7, 11, 12, 15-20, 22-26 as refined below
```

Use the safe staged removal pattern: callers and discovery stop using the component before inactive payload files are removed. Intermediate private cleanup commits are not public release candidates. Each task/batch needs its own scoped verification and local commit. Every implementation slice runs the full existing regression gate from Shared Verification Commands; do not skip failing tests or claim that smaller test counts prove unchanged coverage.

### Authorized Prerequisite: Bounded Windows Status-Save Repair

Task 27's full gate exposed an unchanged SDLC `os.replace` WinError 5 failure. The owner explicitly selected `Approve bounded fix (Recommended)` for a separate minimal repair. This is the only authorized exception to the unrelated-factory exclusion.

**Acceptance:** Keep the same closed/fsynced temporary file, writer lock, atomic replacement, prior bytes on failure, and persistent-error propagation. Retry only native Windows error codes 5/32/33, at most ten attempts with nine 0.05-second waits. No permissions changes, destination unlink, new dependency, broad refactor, or skipped test.

**Verification:** Deterministic RED/GREEN synthetic transient/persistent/unrelated-error tests; a real Windows held-reader recovery case; unchanged eight-process history check; full separate-suite/workspace/build-level gate and independent review. Do not claim that the original intermittent handle holder is identified. Commit the repair separately before committing the pending Task 27 entry-point changes.

**Files:** `plugins/sdlc/skills/ai-sdlc/scripts/update_status.py`, its adjacent `test_update_status.py`, `docs/agent-skills-guide.md`, `docs/testing-guidelines.md`, plus task artifacts. Four deliverable files; no other runtime source changes.

### Task 27: Deregister the Public Plugin Entry

**Acceptance:** Remove only the threat-modelling entries from the synchronized marketplace manifests and root install/navigation guidance. Preserve all other plugins and author/license attribution. Add a regression contract for the withdrawn marketplace/install surface, without requiring payload absence before its retirement phase.

**Verification:** RED before changing registrations; marketplace/workspace/frontmatter checks and the full regression gate after the change; review the exact manifest diff.

**Dependencies:** Recorded user component-withdrawal direction and expanded-scope review.

**Files:** `marketplace.json`, `.github/plugin/marketplace.json`, `README.md`, `AGENTS.md`, `tests/test_public_plugin_surface.py` (new). At most five deliverable files.

### Task 28: Remove Obsolete Companion Routes

**Acceptance:** No retained router tries to invoke the withdrawn plugin or its `tm-*` agents. Preserve generic SDLC security review and all unrelated companion routes. State that the full threat-model/Security Impact workflow is not bundled; do not silently pretend a generic audit is an equivalent replacement or auto-install a private plugin.

**Verification:** Scoped route tests/reference checks and the full regression gate. Inspect the retained security-auditor route and write-approval boundaries.

**Dependencies:** Task 27.

**Files:** `plugins/sdlc/AGENTS.md`, `plugins/sdlc/skills/using-agent-skills/SKILL.md`, `plugins/sdlc/skills/using-agents/SKILL.md`, `plugins/jato-ui/skills/using-jato-ui-skills/SKILL.md`, `docs/threat-modelling.md`. At most five files. Mark the dedicated root guide historical/unavailable and remove its active plugin link before payload retirement; its final retention/removal choice is still Task 32. Update the context-loading roster atomically with discovery in Task 29.

### Task 29: Deactivate Discovery and Removed-Feature Consumers

**Acceptance:** Remove the component manifest and its explicit lazy-loading/discovery cases. Keep Office Word behavior and its executable tests; remove only the retired threat copy, parity, caller, and activation expectations. Keep API-plugin resolver/safety tests. Do not weaken all-agent model coverage merely to hide inactive files; model declarations are retired together with their matching agent files in Task 30.

**Verification:** Add/adjust meaningful retirement expectations before removal; full regression and build-level gate. Record which passing feature-specific cases were removed because the feature is intentionally withdrawn.

**Dependencies:** Task 28.

**Files:** `plugins/threat-modelling/plugin.json` (remove), `tests/test_lazy_loading.py`, `tests/test_plugin_skill_discovery.py`, `tests/test_office_public_workflows.py`, `docs/context-loading.md`. At most five files. The new retirement-surface contract from Task 27 remains; its final payload-absence expectation is added in Task 33.

### Task 30: Retire the Inactive Payload in Bounded Batches

There are **181 remaining plugin files** after the manifest is removed. Nine are agent definitions. Keep per-task changes within five deliverable files:

- **Agent batches 1-3:** Select sorted agent paths from `e6a47c1` in groups of four, four, and one. Remove the selected files and their exact entries in `tests/test_agent_models.py` in the same slice. Do not filter agents out of discovery or skip model assertions to hide them. Each batch changes at most five files; the final batch removes the now-empty component model entry.
- **Payload batches 1-34:** Select the other 170 paths, excluding `plugin.json`, all `agents/` paths, and both `skills/{docx,xlsx}/LICENSE.txt` notices, from the same immutable inventory. Sort once at that source revision. Batch n is positions `5(n-1)+1` through `5n`. Each batch removes five selected files. Do not calculate positions from a shrinking live folder, remove user-generated/untracked files, or widen the paths.
- **Final notice-only batch:** Remove only the two excluded plugin-local `LICENSE.txt` files after every covered component file is gone. Keep notices in place through all earlier batches. Do not touch retained Office notices or root/SDLC attribution.

**Acceptance for each batch:** Only its approved retired paths are removed; retained Office/API/security behavior stays green; no user reports, other plugins, root notices, or Git refs change. Record exact resolved paths and source blobs before execution. The overall component is not retired while any payload remains.

**Verification for each batch:** Read scoped status/diff, run the relevant removal/model/Office contracts and the full shared regression/build-level gate, then make one local commit. Do not mark the parent removal complete after a partial batch. Audit every two batches (or the final three of an odd-length group); auto mode does not require routine stepping, but substantive failures or new scope still stop execution.

**Dependencies:** Task 29. Agent model-map edits require one writer; do not parallelize those batches.

Read-only inventory command (no deletions):

```bash
python - <<'PY'
import subprocess
base = 'e6a47c14b36f7d982dd05c6c1afbb3327a096e76'
root = 'plugins/threat-modelling/'
paths = subprocess.check_output(['git', 'ls-tree', '-r', '--name-only', base, '--', root], text=True).splitlines()
agents = sorted(p for p in paths if p.startswith(root + 'agents/'))
notices = sorted(root + 'skills/' + skill + '/LICENSE.txt' for skill in ['docx', 'xlsx'])
payload = sorted(p for p in paths if p != root + 'plugin.json' and p not in agents and p not in notices)
assert len(paths) == 182 and len(agents) == 9 and len(payload) == 170
assert all(p in paths for p in notices)
for label, selected, width in [('agents', agents, 4), ('payload', payload, 5), ('final notices', notices, 5)]:
    for start in range(0, len(selected), width):
        print(label, 'batch', start // width + 1)
        print('\n'.join(selected[start:start + width]))
PY
```

### Task 31: Align Retained Documentation

**Acceptance:** Model documentation lists only retained agents. Script/test guidance describes the retained Office helper, not a missing second copy. Do not claim that general security review or Octane APIs were removed. Clearly state that installed hosts and generated artifacts are not modified by this source change.

**Verification:** Documentation/reference review and the full regression gate; confirm Office standalone CLI/help and all retained agent model checks.

**Dependencies:** All Task 30 batches.

**Files:** `docs/agent-models.md`, `docs/agent-skills-guide.md`, `docs/testing-guidelines.md`, and at most two related retirement-test/guidance paths. Split first if further callers are found.

### Task 32: Resolve the Dedicated Root Guide and Deck

**Approved disposition:** The owner selected `Retire both (Recommended)`. Retire `docs/threat-modelling.md` and `slides/sdd-threat-modelling-process.pptx` because they describe the withdrawn plugin. Update `docs/README.md` with that same slice. These are not the independent Octane description templates, which remain used by its own skill.

**Acceptance:** Apply the explicit owner choice; no dangling guide/deck link is published. If the owner retains these materials, label the obsolete workflow accurately and keep their disclosure/license clearance open. Do not infer public approval from retention.

**Verification:** Asset/link inventory, feature-absence contract, and full regression gate. If removal is chosen, verify exactly these two root files and their callers; preserve all other slide/banner assets for their existing audits.

**Dependencies:** Task 31; the dedicated-doc/asset decision is complete.

**Files:** The two proposed removals, `docs/README.md`, and `tests/test_public_plugin_surface.py`. At most four files.

### Task 33: Verify Complete Withdrawal

**Acceptance:** No withdrawn subtree, marketplace entry, active route, model declaration, required resolver case, install command, or dangling component-doc link remains in the candidate. Remaining security terminology in standalone Octane APIs/generic SDLC review is reviewed semantically, not purged by keyword. Track the changed test count as intentional feature removal, not a performance/coverage claim.

**Verification:** Add the final absence contract, run the full shared regression/build checks, review remaining references and the scoped base-to-HEAD diff, and verify canonical checkouts/user artifacts are untouched. Report that old component contents still exist in private Git history and public release is still gated.

**Dependencies:** Tasks 27-32 and all 38 Task 30 batches.

**Files:** `tests/test_public_plugin_surface.py` and this internal task ledger. No arbitrary final cleanup, dependency installation, or publication.

### Superseded and Retained Work

- Prior Tasks 5-6 are historical implementation/decision records; do not continue replacement or standalone template retirement. Tasks 8-10, 13-14, 21, and the old Threat Word/Threat Excel support batches are superseded by whole-component removal, not completed. Do not edit their soon-to-be-absent paths.
- Keep completed Office Task 4 and its helper. Continue Office Tasks 7, 11-12 and its three legacy-corpus/license scopes after component withdrawal.
- Continue JATO Tasks 15-16 and its capture review/batches; those materials were not part of this plugin.
- Continue credential/configuration Tasks 17-18, CI Task 19 (only after CI approval), and retained content/licensing/regression/release Tasks 20, 22-26. Refine Tasks 22-23 to touch only remaining assets/README files; do not recreate or re-delete retired threat files.
- Retained-claim source provenance, credential-owner evidence, remaining corporate content, root license choice, independent scan, and public-history treatment still need their own evidence/gates. Whole-plugin removal does not purge private history or authorize release.

**Legacy detail below is reference only where it conflicts with this active queue.** It records the prior accepted plan and remaining retained-plugin tasks. No general plan approval needs to be repeated for already approved work; resolve only new scope/owner decisions.

## Overview and Route

Prepare a useful toolkit with release-approved contents. Keep existing plugin names and workflow contracts where practical. Replace restricted materials independently. Remove unused bundled material only after replacement paths work.

- Write repository: `agents` only.
- Checkout: workspace sibling `agents.worktrees/open-source-readiness`.
- Branch: `topic-open-source-readiness`.
- Pinned base: `4533df1f6a5b4213a7ddde5666ec07af0ddaf65c`, the verified authoritative `origin/main` when the task started.
- Initial audit source: `34f41d0c8bc8d93224ac3773b87ee13255767991` on `feat-software-factory`. Do not merge that branch into this task.
- Authoritative remote: configured `origin`, project `portfolio/wpg/filr/agents` on the verified internal GitLab host.
- Future MR target: that project, branch `main`, only after separate authorization and live MR-state verification.
- Writer: this session. Do not add another writer to this checkout without coordination.
- Current publication status: not requested; no push or MR.
- Future public host, namespace, name, and history: unresolved. Do not invent them.

The root spec and task directory are normally ignored. `tasks/todo.md` is nevertheless already tracked at the base. Do not change ignore rules or force-add artifacts. The task list contains internal findings and must not be published without disclosure review.

## Evidence from the Selected Base

| Evidence | Consequence |
| --- | --- |
| `plugins/office/plugin.json` discovers the whole `skills/` directory | Hiding a router entry alone does not exclude restricted material from the repository or installation. |
| `plugins/office/skills/using-office/SKILL.md` routes Word, Excel, PowerPoint, and corporate slides | Replace complete user paths, not isolated license headers. |
| Threat agents require `.docx` and `.xlsx` artifacts and use local Office skills | Preserve output contracts or stop for approval. A Markdown-only replacement is not equivalent. |
| `tests/test_plugin_skill_discovery.py` checks the local XLSX resolver | Changes must preserve or explicitly update discovery behavior with regression coverage. |
| Five restricted trees contain 290 files | Directory-level removal is too large for one task. Use the bounded support-file batches below. |
| JATO captured references contain 52 Markdown files | Replace the reference entry path before bounded capture removal. Review other JATO skill content too. |
| `blackduck_token.py` contains corporate URL defaults at the setup and login paths | Sanitize runtime defaults, not only examples. Verify configuration precedence and missing-endpoint behavior. |
| `tests/test_ci_reports.py` requires the corporate SMTP include and addresses | CI cleanup must change configuration, tests, and guidance together, after approval. |
| `docs/agent-skills-guide.md` documents Office runtime tools | Replacement instructions must match actual supported tooling. Do not promise format rendering or formula recalculation without proof. |
| `tasks/todo.md` is a tracked completed OKF checklist | Preserve it before using the requested task-list path. |

Inspect applicable plugin instructions before implementing each slice. Do not study restricted implementation bodies to construct replacements. Use task requirements, independently established format contracts, and public authoritative sources with verified licenses.

## Architecture Decisions

1. Keep Python, Bash, pytest, JSON manifests, and the current plugin layout. Do not build a scanner or export framework.
2. Prefer independently authored procedural Office skills at existing skill names. They may use already supported tools or user-supplied templates. They must not depend on bundled restricted helpers. If this cannot preserve a required behavior, stop at the capability gate. Do not silently downgrade the behavior.
3. Treat corporate templates as optional user inputs unless owners approve redistribution. Test workflows with synthetic fixtures, not corporate documents.
4. Preserve original authorship and required copyright notices. A corporate name, vendor API name, or public vendor documentation link is not automatically confidential.
5. Separate content-owner permission from technical validation. Passing tests cannot authorize release.
6. Preserve internal Git history during cleanup. Decide the public-history treatment separately. Restricted content in history also needs treatment; resolving credentials alone is not sufficient.
7. Maintain one writer for shared manifests, routers, notices, and task artifacts. Independent evidence reviews may run in parallel.
8. Use no numeric coverage threshold. Require regression coverage for changed behavior and explicit evidence for retained capabilities.

## Dependency Graph

```text
Task 1: inventory and baseline
  +--> Task 2: credential-owner evidence ---------> final release gate
  +--> Task 3: legal/content/capability decisions -> Checkpoint A
          +--> Office Word (4) -> local helper (5 preparation)
                  -> plain initial-analysis caller (6 caller slice)
                  -> local Word guide (5 activation)
                  -> old form retirement (6 final slice; separate approval)
          +--> Excel entry paths (7, 8) -> threat catalog (9) -> calculator (10)
          +--> PowerPoint entry (11) -> slide command (12)
          +--> DFD references (13)
          +--> security principles (14)
          +--> JATO entry path (15) -> component lookup (16)
          +--> endpoint behavior (17) -> service examples (18)
          +--> CI decision (19)

Working replacement entry paths
  +--> support-file batches (69 independent bounded tasks)
  +--> final subtree license decisions (20, 21)
  +--> corpus cleanup (22)
  +--> root release guidance (23)
  +--> consolidated licensing (24)
  +--> regression review (25)
  +--> artifact/history/security/owner review (26)
```

Tasks 2 and 3 involve human owners. Their delays must not cause guessed approvals. Independent local work can continue after its own gate is satisfied. Task 26 cannot complete while required owner evidence is missing. Office and JATO cleanup batches are distinct content-disposition slices, not permission to remove an entire plugin. If the review inventory finds more affected files than these bounded tasks cover, add explicit small tasks and obtain review before those files change.

## Task Contract

Each numbered task is a vertical path or a small review decision. Each has at most five intended deliverable files. Updates to the internal task ledger are incidental, not permission to widen implementation scope.

Acceptance criteria apply to the complete named path. If inspection finds more than five deliverable files or more than one focused session of work, stop and split that task in this plan before execution. Do not mark an oversized parent complete after a partial change.

For every implementation task:

- Add a failing regression test first when behavior changes.
- Run the named focused checks and `git diff --check`.
- Read back changed documents and inspect the scoped diff.
- Keep the task open for failures, missing capabilities, or unresolved errors.
- Make a scoped local commit after successful task verification, as now authorized by the user. Do not push or publish. Stop before unresolved owner decisions or high-risk actions.

### Shared Verification Commands

Run from this checkout root. These commands are planned, not executed during planning.

```bash
# Focused structure and discovery checks
python -m pytest tests/test_plugin_workspace.py tests/test_frontmatter.py tests/test_lazy_loading.py tests/test_plugin_skill_discovery.py -q

# Marketplace checks
python -m pytest tests/test_marketplace_sync.py -q

# Full repository gate
bash ./agents.sh validate
python -m pytest tests -q --strict-config --strict-markers
python -m pytest plugins/okf/tests -q
python -m pytest plugins/blackduck/skills/blackduck/tests -q
python -m pytest plugins/gitlab/skills/gitlab/tests -q
python -m pytest plugins/octane/skills/alm-octane/tests -q
python -m pytest plugins/sdlc/skills/ai-sdlc/scripts/test_update_status.py plugins/sdlc/skills/ai-sdlc/scripts/test_detect_drift.py -q

git diff --check
git status --short --branch
```

Full tests can use installed `uv` to resolve dependencies. Inspect the test harness first. Use an offline environment with existing dependencies and no service credentials. Do not allow automatic package downloads or install missing tools without approval. Report blocked checks.

## Phase 1: Resolve High-Risk Decisions

### Task 1: Establish the disposition inventory

**Description:** Inventory the selected revision and baseline checks. Record each finding's disposition in the internal task ledger.

**Acceptance:**
- [ ] Record tracked file counts, affected paths, license evidence, caller paths, and unresolved owner questions without secrets.
- [ ] Separate confirmed restrictions, suspected credentials, and approval-required corporate content.
- [ ] Record existing test failures and missing tools without changing production files.

**Verification:** Run available shared checks offline; compare the file inventory with `git ls-files`; review the internal ledger for secret values.

**Dependencies:** Human approval of the spec and plan.

**Files:** `tasks/todo.md` only. **Scope:** Small.

### Task 2: Resolve the historical credential finding

**Description:** Obtain the owner's decision for historical Octane credentials. This is coordination, not a credential API operation.

**Acceptance:**
- [ ] Record owner confirmation of revocation/rotation or evidence that the value is synthetic.
- [ ] Record the affected historical path and commits without the client secret or full client identifier.
- [ ] Keep the release blocked if the owner cannot confirm resolution. Do not test the credential.

**Verification:** Read the owner's evidence; confirm affected history is still reachable with Git metadata checks. Do not print historical file contents.

**Dependencies:** Task 1.

**Files:** `tasks/todo.md` only. **Scope:** Small; external-owner wait is not implementation time.

### Task 3: Approve the content and capability decisions

**Description:** Obtain owner decisions for restricted skills, corporate content, licensing, replacement capabilities, and public-history treatment.

**Acceptance:**
- [ ] Record removal, independent replacement, or explicit redistribution permission for each affected content family.
- [ ] Approve retained DOCX/XLSX/PPTX capabilities, the source and tool strategy, and the root-license owner. No new dependency or whole-plugin removal is implied.
- [ ] Assign owners to unresolved CI, history, scanner, and publication decisions. An unanswered decision remains blocked.

**Verification:** Review the inventory against the spec; verify permission scope covers code, prompts, templates, and history where applicable.

**Dependencies:** Task 1. Task 2 may proceed independently.

**Files:** `tasks/todo.md` only. **Scope:** Small decision record.

### Checkpoint A: Approval Before Replacement

- [ ] Human approves spec, plan, and the chosen replacement strategy.
- [ ] Content-owner decisions are explicit. Missing permissions imply exclusion, not automatic reuse.
- [ ] Missing credential evidence blocks release, not unrelated approved local cleanup.
- [ ] No production files have changed before this checkpoint.

## Phase 2: Preserve Document Workflows

### Task 4: Make the Office Word path independent

**Capability decision received:** The user selected `Basic scope (Recommended)` after reviewing the implemented limits. Activate the basic Word path with those limits. Rich-format preservation, arbitrary-template editing, native rendering, and full schema validation are not Task 4 promises. The completed CLI slice is commit `17bfaca`; activation remains the next bounded slice. No general plan approval is required again.

**Acceptance:**
- [ ] Independently authored Word instructions preserve the existing skill name and do not call restricted helpers.
- [ ] Synthetic DOCX read/create/edit checks demonstrate the promised scope with approved existing tools; missing-tool errors are explicit.
- [ ] Public Office guidance identifies supported and unsupported behavior accurately.

**Verification:** Focused structure checks; `python -m pytest tests/test_office_public_workflows.py -q` after adding the synthetic contract tests; manually verify the generated synthetic document with an approved tool.

**Dependencies:** Task 3 and Checkpoint A.

**Execution refinement:** Keep the existing router link unchanged. Split this task into two complete small paths so executable behavior and required script/test documentation fit the file limit:

- **Basic Word CLI:** Independently author `plugins/office/skills/docx/scripts/docx_basic.py`; add `tests/test_office_public_workflows.py`; update `docs/agent-skills-guide.md` and `docs/testing-guidelines.md`. Four deliverable files. Use only the Python standard library. Exercise the copied standalone script with isolated Python subprocesses, without legacy helpers. Support bounded main-body extraction, plain-paragraph creation, and literal replacement in the helper's own basic profile. Reject rich/template edits instead of discarding formatting. Prove the ZIP/XML structure independently; do not claim native Word rendering or full schema validation.
- **Word skill activation:** Replace only `plugins/office/skills/docx/SKILL.md`; update `plugins/office/README.md` and `plugins/office/AGENTS.md`. Three deliverable files. Route basic work only through the new helper. State unsupported rich editing/rendering clearly. Keep all legacy support files and their notices untouched for their later gated disposition. The existing router still points to the same skill name.

Run RED/GREEN and full regression/build checks for the CLI slice. Run the same checks after skill activation. Each completed slice gets a separate local commit. Do not mark the parent Task 4 complete until activation and capability verification pass. If native rendering or complex edits are required, stop for approved tooling rather than broaden the claim.

**Files:** The two bounded slices above. No runtime dependency is added. The helper and replacement instructions are newly authored; they do not grant a new license to any legacy subtree content. Root release licensing remains pending.

### Task 5: Make the threat-model Word path independent

**Artifact decision received:** The user selected `Plain report (Recommended)` after caller inspection identified the incompatible corporate table-editing requirement. Preserve DOCX/Markdown filenames, evidence, user confirmation, and upload gates; do not preserve corporate cell layout or derive new wording from its template/training text. This specific format decision is approved; do not request it again.

**Safe execution order:**

1. Prepare the plugin-local independently authored helper and prove its standalone CLI contract. Reuse only the newly authored Office helper, not legacy source. Update its parameterized synthetic tests and script/test guidance. Four deliverable files: the new threat helper, `tests/test_office_public_workflows.py`, `docs/agent-skills-guide.md`, and `docs/testing-guidelines.md`. Keep the legacy local Word guide unchanged in this slice.
2. Execute Task 6's plain-report caller slice using the prepared helper directly. Do not load legacy Word instructions or require copying/editing the corporate template. Keep the DOCX/Markdown filenames and existing result keys. Record no template (`templatePath: null`) for the approved plain-report mode. State the exact local checks behind any readiness result; do not imply server acceptance, rendering, full schema validation, or upload approval.
3. Activate the independent local Word guide only after the caller slice passes. Update the new local `SKILL.md`, threat README/AGENTS, and activation tests (four files). Keep the existing router link unless evidence requires a separate bounded change. Finish Task 5 only after its full regression gate passes.
4. Retire old templates only in Task 6's separately approved final removal slice. Do not introduce a parent-task dependency cycle: Task 6's caller slice depends on helper preparation, not on prior Task 5 activation; its retirement slice follows activation.

Each working slice receives its own scoped local commit. No legacy file deletion or new dependency is authorized by this refinement.

**Acceptance:**
- [ ] The plugin-local Word skill is independently authored and remains independently installable.
- [ ] Its output contract matches the supported synthetic DOCX path without importing the Office plugin.
- [ ] Threat-model routing remains correct and no active path requires the old Word support files.

**Verification:** Focused structure checks; `python -m pytest tests/test_office_public_workflows.py -q`; synthetic plugin-isolated DOCX exercise.

**Dependencies:** Task 4.

**Files:** The bounded preparation/activation slices above. The existing local Word router target remains valid. No task imports runtime code from another installed plugin.

### Task 6: Generate an initial-analysis form without a bundled corporate template

**Acceptance:**
- [ ] Use the user-approved independently authored plain-report layout; do not require the corporate table or cell map. Preserve matching DOCX/Markdown and their established filenames. Retire the unapproved corporate form only in the final separately approved removal slice.
- [ ] The complete entry path still produces matching `.docx` and Markdown artifacts, or stops clearly if prerequisites are missing.
- [ ] Validation does not claim corporate approval or upload readiness based only on a file extension.

**Verification:** `python -m pytest tests/test_office_public_workflows.py -q`; synthetic initial-analysis exercise; focused structure checks.

**Dependencies:** Task 5's helper-preparation slice and the explicit plain-report decision. The caller slice must not depend on prior Word-guide activation. Final template retirement additionally requires Task 5 activation and its own high-risk removal approval.

**Bounded execution slices:** First implement the approved plain-report path in the skill entry, `agents/tm-initial-analysis.agent.md`, the skill's independently rewritten `references/full-reference.md`, `docs/threat-modelling.md`, and `tests/test_office_public_workflows.py` (five files). Use the prepared local basic helper directly; preserve DOCX/Markdown filenames, evidence, confirmation, and output result keys. Derive new wording from independent requirements, not from the corporate form/training extract. After the local Word-guide activation and explicit high-risk removal approval, retire the unapproved `references/Initial Analysis Form.docx` and `references/initial-analysis-form.md` (two files). The first slice must not reference either bundled template. Each slice needs its own passing verification and local commit. Do not treat the Markdown template as implicitly cleared.

### Checkpoint B: Word Capability

- [ ] Office Word and initial-analysis flows work without restricted helpers or corporate fixtures.
- [ ] Human reviews the capability evidence. Stop if required behavior cannot be preserved.
- [ ] No license header has been changed to disguise remaining restricted material.

### Task 7: Make the Office Excel path independent

**Acceptance:**
- [ ] Independent Excel instructions preserve the skill name and use approved existing tools.
- [ ] Synthetic read/write checks pass; formula recalculation requires an actual supported calculation engine, not cached or invented values.
- [ ] Router and user guidance describe prerequisites and limitations accurately.

**Verification:** `python -m pytest tests/test_office_public_workflows.py -q`; synthetic workbook round-trip and formula check with approved tooling; focused structure checks.

**Dependencies:** Task 3 and Checkpoint A.

**Files:** `plugins/office/skills/xlsx/SKILL.md`, `plugins/office/skills/using-office/SKILL.md`, `plugins/office/README.md`, `plugins/office/AGENTS.md`, `tests/test_office_public_workflows.py`. **Scope:** Medium.

### Task 8: Make the threat-model Excel path independent

**Acceptance:**
- [ ] Independently authored local instructions preserve plugin isolation and XLSX discovery.
- [ ] Synthetic catalog/calculator workbook operations use no old helpers.
- [ ] Installed-plugin resolution still precedes direct-user-skill fallback.

**Verification:** `python -m pytest tests/test_plugin_skill_discovery.py tests/test_office_public_workflows.py -q`; isolated synthetic workbook exercise.

**Dependencies:** Task 7.

**Files:** `plugins/threat-modelling/skills/xlsx/SKILL.md`, `plugins/threat-modelling/skills/using-threat-modelling/SKILL.md`, `plugins/threat-modelling/AGENTS.md`, `tests/test_plugin_skill_discovery.py`, `tests/test_office_public_workflows.py`. **Scope:** Medium.

### Task 9: Produce a public-safe threat catalog

**Acceptance:**
- [ ] Remove or independently replace the bundled corporate catalog according to the owner decision.
- [ ] The workflow preserves matching `.xlsx` and Markdown catalogs and existing update-in-place behavior.
- [ ] Synthetic workbook contents contain no corporate metadata or unrelated records.

**Verification:** `python -m pytest tests/test_office_public_workflows.py -q`; inspect the synthetic workbook archive and compare catalog entries with Markdown.

**Dependencies:** Task 8 and the catalog disposition in Task 3.

**Bounded execution slices:** First implement and test the explicit-template catalog path through the skill entry, `references/full-reference.md`, `scripts/update_threat_catalog.py`, `docs/threat-modelling.md`, and `tests/test_office_public_workflows.py` within the relevant roots (five files). Do not assume that the existing script's template field map is public or reusable. Preserve its caller contract using independent requirements, or stop for a behavior decision. Then update `agents/tm-threats-and-mitigations.agent.md` and `agents/tm-threat-auditor.agent.md` and, only after explicit high-risk removal approval, retire `resources/Threat Catalog.xlsx` (three files). The first slice must no longer require the bundled workbook; the final slice must preserve an atomic tested agent path. Each slice needs its own passing verification and local commit.

### Checkpoint C: Spreadsheet Capability

- [ ] Independent Excel skills and catalog generation pass their synthetic checks.
- [ ] No recalculation or validation claim exceeds the tested tool capability.
- [ ] Human approves any proposed output-contract change before proceeding.

### Task 10: Support a user-supplied security-impact calculator

**Acceptance:**
- [ ] Remove the unapproved bundled calculator; use an explicit user-supplied approved workbook.
- [ ] A missing workbook produces an actionable request, not fabricated scoring rules.
- [ ] Synthetic workbook tests preserve confirmed upload boundaries and never call Octane.

**Verification:** `python -m pytest tests/test_plugin_skill_discovery.py tests/test_office_public_workflows.py -q`; missing-template and synthetic-template exercises.

**Dependencies:** Task 8 and the calculator disposition in Task 3.

**Files:** `plugins/threat-modelling/skills/security-impact-calculator/SKILL.md`, its `references/full-reference.md`, its `resources/Security_Impact_Calculator.xlsx`, `plugins/threat-modelling/agents/tm-security-impact-analysis.agent.md`, `tests/test_office_public_workflows.py`. **Scope:** Medium.

### Task 11: Make the PowerPoint path independent

**Acceptance:**
- [ ] Independent PowerPoint instructions preserve the skill name without old helpers or corporate templates.
- [ ] Synthetic presentation read/create/edit and render checks prove only the promised scope.
- [ ] Documentation states required tools and does not install them automatically.

**Verification:** `python -m pytest tests/test_office_public_workflows.py -q`; synthetic deck generation and visual inspection with approved tooling; focused structure checks.

**Dependencies:** Task 3 and Checkpoint A.

**Files:** `plugins/office/skills/pptx/SKILL.md`, `plugins/office/skills/using-office/SKILL.md`, `plugins/office/README.md`, `plugins/office/AGENTS.md`, `tests/test_office_public_workflows.py`. **Scope:** Medium.

### Task 12: Create slides without bundled corporate branding

**Acceptance:**
- [ ] The slide command uses neutral defaults and an optional user-supplied approved brand guide/template.
- [ ] Remove the unapproved corporate template and brand-reference capture; preserve the established skill name unless a rename is approved.
- [ ] The full command path has no mandatory corporate asset or private-link dependency.

**Verification:** `python -m pytest tests/test_office_public_workflows.py -q`; focused structure checks; manually exercise the command with a synthetic neutral template.

**Dependencies:** Task 11 and the brand disposition in Task 3.

**Files:** `plugins/office/commands/create-slide.md`, `plugins/office/skills/ot-slide-deck/SKILL.md`, its `references/full-reference.md`, `plugins/office/skills/pptx/resources/OT FY26 Corporate Template LIGHT.potx`, `tests/test_office_public_workflows.py`. **Scope:** Medium.

### Checkpoint D: Complete Document Paths

- [ ] Synthetic Word, Excel, initial form, catalog, calculator, and slide paths pass.
- [ ] Missing prerequisites fail clearly without network or credential access.
- [ ] Human accepts the retained capabilities before old support files are removed.

## Phase 3: Remove Mandatory Corporate Knowledge

### Task 13: Build a DFD from user evidence

**Acceptance:**
- [ ] Remove the copied product architecture documents unless redistribution permission is recorded.
- [ ] The DFD workflow uses user-supplied evidence and records unknowns instead of assuming Filr internals.
- [ ] No active reference points to removed private architecture files.

**Verification:** Focused structure checks; synthetic non-Filr DFD exercise; inspect all retained references to the two removed files. Task 15 creates the later shared content-contract tests. Do not run or claim those tests before they exist.

**Dependencies:** Task 3 and Checkpoint A.

**Bounded execution slices:** First update the DFD skill, its `references/full-reference.md`, its `references/sources.md`, and `agents/tm-dataflow-diagrams.agent.md` (four files) to use user evidence without any active reference to copied architecture. Then, after explicit high-risk removal approval, retire the two `references/filr-architecture/*.md` files (two files). Each slice needs independent reference checks and a synthetic non-Filr DFD exercise. Add shared content-contract coverage in Task 15/22; do not claim it exists before then.

### Task 14: Replace copied corporate training guidance

**Acceptance:**
- [ ] Independently author general security guidance from approved public sources, not the training extract.
- [ ] Preserve the existing support-skill identifier and required safety meaning without copied corporate legal language.
- [ ] Keep legitimate risk-reporting and approval gates intact.

**Verification:** Focused structure checks; source/provenance review; compare orchestrator references with the retained skill contract.

**Dependencies:** Task 3 and Checkpoint A.

**Files:** `plugins/threat-modelling/skills/ot-threat-model-guidelines/SKILL.md`, its `references/full-reference.md`, `plugins/threat-modelling/agents/threat-modelling.agent.md`, `plugins/threat-modelling/README.md`, `plugins/threat-modelling/AGENTS.md`. **Scope:** Medium.

### Task 15: Route JATO guidance without bundled internal captures

**Acceptance:**
- [ ] Guidance accepts an explicit user-supplied design system and does not require captured corporate reference pages.
- [ ] Retain JATO-specific identifiers only where lawful and useful; do not imply redistribution rights for external packages.
- [ ] Router and README match the supported public path.

**Verification:** Focused structure checks; synthetic design-system routing exercise; review remaining references before deleting captures.

**Dependencies:** Task 3 and Checkpoint A.

**Files:** `plugins/jato-ui/skills/jato-ux-guidelines/SKILL.md`, `plugins/jato-ui/skills/using-jato-ui-skills/SKILL.md`, `plugins/jato-ui/README.md`, `plugins/jato-ui/AGENTS.md`, `tests/test_public_content_contracts.py`. **Scope:** Medium.

### Checkpoint E: Evidence-Based Guidance

- [ ] DFD, security principles, and JATO routing work with public or user-supplied evidence.
- [ ] No internal policy is presented as universally approved legal language.
- [ ] Human approves the capture-removal inventory before batch cleanup.

### Task 16: Make UI component lookup configurable

**Acceptance:**
- [ ] Component lookup and design guidance use user-provided package/catalog locations instead of corporate service defaults.
- [ ] Review frontend, token, and handoff guidance for copied internal text and assets, not just URLs.
- [ ] Independent-source and missing-source paths are tested without fetching private services.

**Verification:** Focused structure checks; `python -m pytest tests/test_public_content_contracts.py -q`; inventory review. If more than four skill files need changes, split this task before implementation.

**Dependencies:** Task 15.

**Files:** `plugins/jato-ui/skills/jato-component-lookup/SKILL.md`, `plugins/jato-ui/skills/jato-design-tokens/SKILL.md`, `plugins/jato-ui/skills/frontend-design/SKILL.md`, `plugins/jato-ui/skills/design-handoff/SKILL.md`, `tests/test_public_content_contracts.py`. **Scope:** Medium.

### Task 17: Require an explicit Black Duck endpoint

**Acceptance:**
- [ ] No setup or login path silently selects the corporate URL; preserve explicit flags, environment, profile, and legacy configuration precedence.
- [ ] Missing endpoint produces a local actionable error before any credential is retrieved or transmitted.
- [ ] Existing profile safety, TLS settings, and secret-storage behavior remain intact.

**Verification:** `python -m pytest plugins/blackduck/skills/blackduck/tests -q`; `python -m pytest tests/test_credential_config_contract.py -q`; synthetic missing-endpoint and explicit-profile regression tests.

**Dependencies:** Task 3 and explicit approval of this CLI behavior change at Checkpoint A.

**Files:** `plugins/blackduck/skills/blackduck/scripts/blackduck_token.py`, its `tests/test_blackduck_profiles.py`, its `tests/test_blackduck_credential_config.py`, `plugins/blackduck/README.md`, `plugins/blackduck/skills/blackduck/SKILL.md`. **Scope:** Medium.

### Task 18: Use neutral service examples

**Acceptance:**
- [ ] Octane evaluations and public examples use synthetic tenant/workspace IDs and reserved example domains.
- [ ] Preserve valid public vendor documentation references and required author notices.
- [ ] Do not copy local `.env` files or user configuration into examples.

**Verification:** `python -m pytest plugins/octane/skills/alm-octane/tests -q`; read changed JSON/Markdown; redacted content review. Extend the inventory and split a follow-up slice if more paths need changes.

**Dependencies:** Task 1. Task 17 only if examples depend on its behavior.

**Files:** `plugins/octane/skills/alm-octane/evals/evals.json`, its `references/full-reference.md`, its `references/examples.md`, `plugins/blackduck/skills/blackduck/references/examples.md`, `plugins/gitlab/skills/gitlab/references/examples.md`. **Scope:** Medium.

### Checkpoint F: Public Configuration Paths

- [ ] UI guidance does not require private component services.
- [ ] Black Duck preserves configuration safety without an implicit corporate endpoint.
- [ ] Examples contain no real account, tenant, workspace, or credential values.

## Phase 4: Remove Unused Bundled Material

### Support-File Batch Tasks

These are individual tasks, not one 331-file deletion task. Each row in the task list is a separate task with at most five files. There are 69 batch tasks at the pinned base: 58 Office support batches and 11 JATO capture batches.

| Scope | Root | Eligible files | Batches | Prerequisites |
| --- | --- | --- | --- | --- |
| Office Word | `plugins/office/skills/docx` | 59 | 12 | Tasks 4-6 and Checkpoint D |
| Office PowerPoint | `plugins/office/skills/pptx` | 57 | 12 | Tasks 11-12 and Checkpoint D |
| Office Excel | `plugins/office/skills/xlsx` | 52 | 11 | Tasks 7-10 and Checkpoint D |
| Threat Word | `plugins/threat-modelling/skills/docx` | 59 | 12 | Tasks 5-6 and Checkpoint D |
| Threat Excel | `plugins/threat-modelling/skills/xlsx` | 52 | 11 | Tasks 8-10 and Checkpoint D |
| JATO captures | `plugins/jato-ui/skills/jato-ux-guidelines/references` | 52 | 11 | Tasks 15-16 and Checkpoint E |

For Office scopes, exclude `SKILL.md`, `LICENSE.txt`, and the corporate `.potx` handled by Task 12. The JATO scope contains only captured reference Markdown at this base.

**Exact file selection:** Sort eligible paths from the pinned base, not from a shrinking live directory. Batch `n` is the one-based range `5(n-1)+1` through `min(5n, count)`. Before each task, record its resolved paths in the task list and check for baseline drift. The following read-only command prints the full deterministic list. It does not create a tool or delete files.

```bash
python - <<'PY'
import subprocess
base = '4533df1f6a5b4213a7ddde5666ec07af0ddaf65c'
roots = [
    'plugins/office/skills/docx',
    'plugins/office/skills/pptx',
    'plugins/office/skills/xlsx',
    'plugins/threat-modelling/skills/docx',
    'plugins/threat-modelling/skills/xlsx',
    'plugins/jato-ui/skills/jato-ux-guidelines/references',
]
for root in roots:
    paths = subprocess.check_output(
        ['git', 'ls-tree', '-r', '--name-only', base, '--', root], text=True
    ).splitlines()
    excluded = {root + '/SKILL.md', root + '/LICENSE.txt',
                root + '/resources/OT FY26 Corporate Template LIGHT.potx'}
    eligible = sorted(path for path in paths if path not in excluded)
    for start in range(0, len(eligible), 5):
        print(root, 'batch', start // 5 + 1)
        print('\n'.join(eligible[start:start + 5]))
PY
```

**Acceptance for every batch:**
- [ ] Remove only its selected, owner-approved obsolete files. Do not delete newly authored replacements or shared files outside the scope.
- [ ] Confirm no active retained workflow calls a removed file. Retained licenses remain intact until no covered original files remain.
- [ ] The replacement user path and focused structure checks still pass. If a caller is found, stop and split a caller-update task before deletion.

**Verification for every batch:** Run focused structure checks, the relevant synthetic workflow exercise, and `git diff --check`. Inspect `git diff --name-only` against the resolved batch. For Office batches also run `python -m pytest tests/test_office_public_workflows.py -q`; for JATO use `python -m pytest tests/test_public_content_contracts.py -q`.

**Files:** Exactly the selected paths, at most five. **Scope:** Small or medium. Deletions are local only; the old material remains in private Git history.

**Checkpoint cadence:** Stop after each two batches, or the final three batches in an odd-length scope. Run the full repository gate available offline, verify the retained user path, and obtain human review before the next group. An inactive support tree is not a public-ready artifact until all of its batches and final license disposition complete.

### Task 19: Make approved CI validation independent

**Acceptance:**
- [ ] After explicit CI approval, remove or replace the private SMTP include and notification settings without removing validation jobs.
- [ ] CI contract tests assert the new public-safe behavior, not the deleted corporate notification contract.
- [ ] Test guidance describes actual jobs without private contacts, runner assumptions, or misleading delivery claims.

**Verification:** `python -m pytest tests/test_ci_reports.py -q`; inspect YAML and preserved job commands. GitLab-side validation is a separate approved external action.

**Dependencies:** Task 3 and explicit CI approval. Can run independently of support batches.

**Files:** `.gitlab-ci.yml`, `tests/test_ci_reports.py`, `docs/testing-guidelines.md`. **Scope:** Medium.

### Task 20: Close Office subtree license disposition

**Acceptance:**
- [ ] All three Office support scopes and template cleanup are complete or have explicit redistribution permission.
- [ ] Each retained skill contains only independently authored or approved material under the correct terms.
- [ ] Remove obsolete restrictive license files only when no covered material remains. Do not relabel surviving third-party material.

**Verification:** Compare the entire retained subtrees with the disposition inventory and approved author/license evidence; run focused checks.

**Dependencies:** Office Word, PowerPoint, and Excel batch scopes; Tasks 4, 7, 11, 12; root-license decision in Task 3.

**Files:** Three Office `skills/{docx,pptx,xlsx}/LICENSE.txt` files and at most two related attribution records. **Scope:** At most five files.

### Task 21: Close threat-model subtree license disposition

**Acceptance:**
- [ ] Both threat-model support scopes are complete or have explicit redistribution permission.
- [ ] Local Word/Excel skills remain independently installable under verified terms.
- [ ] Remove obsolete restrictive licenses only after all covered original files are gone.

**Verification:** Subtree inventory and source-license review; focused discovery tests and synthetic DOCX/XLSX paths.

**Dependencies:** Threat Word and Excel batch scopes; Tasks 5, 8; root-license decision in Task 3.

**Files:** Two threat-modelling `skills/{docx,xlsx}/LICENSE.txt` files and at most two related attribution records. **Scope:** At most four files.

### Checkpoint G: Restricted Corpus Removed

- [ ] All applicable batch rows are verified; no partial scope is marked complete.
- [ ] Five restricted subtrees and captured JATO content have final dispositions.
- [ ] License evidence covers retained files. The history decision remains open unless separately resolved.

## Phase 5: Complete Public Guidance and Licensing

### Task 22: Remove unapproved presentation assets

**Acceptance:**
- [ ] Remove or independently replace the corporate process deck and root banner, based on the owner decision.
- [ ] Update the root README in the same slice, so the root entry path has no broken asset or private install reference.
- [ ] Extend content-contract regression coverage for DFD/template dispositions and retained public asset paths.

**Verification:** `python -m pytest tests/test_public_content_contracts.py -q`; inspect retained images and Office metadata, not only filenames; verify root README links in the same slice.

**Dependencies:** Task 3, Tasks 6, 9, 10, 12, 13, 15.

**Files:** `slides/sdd-threat-modelling-process.pptx`, `assets/banner.png`, `README.md`, `tests/test_public_content_contracts.py`. **Scope:** Four files. If another active caller is found, include it only within the five-file limit; otherwise split the asset plus caller into a separate atomic slice.

### Task 23: Publish accurate local setup guidance

**Acceptance:**
- [ ] Retained SDLC and threat-modelling entry pages use approved assets or no banner and describe the retained public capabilities accurately.
- [ ] Remove or replace each plugin banner and its README reference together. Runtime-tool guidance matches the independently verified Office paths.
- [ ] Do not invent a public repository URL. Label remote installation pending the release destination decision.

**Verification:** Focused structure and marketplace checks; local Markdown-link review; verify local install instructions by inspection without installing plugins.

**Dependencies:** All capability changes, Task 19, Task 22.

**Files:** `plugins/sdlc/assets/sdlc_banner.png`, `plugins/sdlc/README.md`, `plugins/threat-modelling/assets/tm_banner.png`, `plugins/threat-modelling/README.md`, `docs/agent-skills-guide.md`. **Scope:** Five files. Office guidance is updated in Tasks 4, 7, and 11; root guidance is updated in Task 22.

### Task 24: Apply approved licenses and notices

**Acceptance:**
- [ ] Apply the owner-approved root license only after ownership and release rights are confirmed.
- [ ] Consolidated notices cover every retained imported source, including Angular, Vitest, SDLC imports, and other plugins. Verify upstream license scope and immutable provenance.
- [ ] Keep required plugin notices and author attribution. Correct misleading marketplace capability descriptions consistently.

**Verification:** File-by-file provenance review against the final inventory; `python -m pytest tests/test_marketplace_sync.py -q`; review permissions rather than relying only on declared frontmatter licenses.

**Dependencies:** Task 3, Tasks 16, 20-23, all cleanup scopes.

**Files:** root `LICENSE`, root `THIRD_PARTY_NOTICES.md`, `CONTRIBUTING.md`, `marketplace.json`, `.github/plugin/marketplace.json`. **Scope:** Medium. If existing plugin notices need correction, split independent notice tasks before proceeding.

### Checkpoint H: Public Contents and Notices

- [ ] Technical owners approve the retained user paths and removal scope.
- [ ] Legal/content owners approve licensing and retained corporate material.
- [ ] No unsupported capability, private CI dependency, broken link, or invented destination remains.

## Phase 6: Verify the Exact Release Candidate

### Task 25: Run the complete regression review

**Acceptance:**
- [ ] All applicable shared checks and changed-behavior tests pass in an isolated, offline-capable environment.
- [ ] Every removed capability reference and retained plugin resolver is reviewed; no unrelated failure is hidden.
- [ ] Review the scoped diff, local status, and known limitations. Keep the task open for failing or unavailable required checks.

**Verification:** Execute the full shared verification block; synthetic Office flow checks; compare tests and documentation with the final capability inventory.

**Dependencies:** All local implementation tasks and Checkpoint H.

**Files:** `tasks/todo.md` evidence only. Fixes require separate bounded tasks, not an unbounded final cleanup task. **Scope:** Small review task.

### Task 26: Assemble release-owner evidence

**Acceptance:**
- [ ] Independent redacted scans cover the intended public files and approved public-history scope; findings have owner dispositions.
- [ ] Confirm excluded local credentials, caches, internal planning artifacts, and unapproved historical material cannot enter the proposed release.
- [ ] Release owner approves the exact candidate SHA/file inventory and history policy. Publication still requires a separate explicit request.

**Verification:** Independent review of Task 2 evidence, license records, final file inventory, scan outputs, and candidate revision. Re-run scans if candidate files or refs change.

**Dependencies:** Task 2, Task 25, and explicit scanner/history/release-owner decisions.

**Files:** `tasks/todo.md` evidence only; retain sensitive scan reports outside public contents. **Scope:** Small review task with external approvals.

### Proposed Independent Scan Commands

Propose Gitleaks as a local independent scanner, not a new repository dependency or CI job. Tool selection, installation, and version are unapproved. Confirm the installed CLI syntax with `--help` before use. Do not download it during this planning phase.

```bash
gitleaks version
gitleaks git --help
gitleaks dir --help
# Private checkout: show all locally reachable historical findings, fully redacted.
gitleaks git --redact=100 --log-opts="--all" .
# Only in the approved candidate directory: inspect the exact public file contents.
gitleaks dir --redact=100 .
```

A history scan of this private checkout is expected to include old findings. Do not claim a clean public-history result from a current-directory scan. Once the history strategy is approved, record the exact candidate directory and ref set, run the corresponding read-only scan there, and preserve the internal evidence. Hidden remote refs and external release assets need separate platform-owner review. This plan does not create a candidate export or rewrite history.

### Final Checkpoint: Release Is Still Gated

- [ ] All spec success criteria have evidence or remain explicitly blocked.
- [ ] Required human owners approve credential, content, legal, and history decisions.
- [ ] No push, MR, visibility change, tag, or public release occurs under this plan's authority.

## Parallel Work

Read-only provenance reviews can run in parallel with credential-owner coordination. Tasks 13-16 and Task 19 can proceed independently after their approvals. Word, Excel, and slide work share routers, README files, and synthetic tests, so serialize their writes. Assign batch scopes to other worktrees and branches only after explicit writer coordination; never share this checkout concurrently. The designated integrator owns shared task records, manifests, notices, and final verification.

## Risks and Mitigations

| Risk | Impact | Mitigation |
| --- | --- | --- |
| Unsupported Office replacement | High | Prove synthetic capability paths before any helper deletion. Stop for tool or contract approval. |
| Derivative replacement of restricted materials | High | Use independent requirements and verified public sources; obtain license review. |
| Hidden corporate content in media or schemas | High | Inspect embedded files, metadata, images, and provenance. Do not assume a standard-looking schema is freely redistributable. |
| Credentials survive in history | High | Owner remediation and separately approved history policy; scan exact intended refs. |
| Oversized cleanup task | Medium | Deterministic five-file batches and two/three-task checkpoints. Split unexpected callers before deletion. |
| Tests are unavailable or may fetch dependencies | Medium | Inspect harness, run offline with existing dependencies, report blockers. |
| Third-party notices incomplete | High | Inventory all retained files, not only the known findings; verify pinned upstream evidence. |
| Internal plan accidentally published | High | Keep artifacts local; explicit disclosure review before staging or release. |

## Decisions for Human Review

1. Approve the spec and this plan before implementation.
2. Approve or change the independent procedural Office strategy. Tool or whole-plugin changes require separate approval.
3. Identify credential, legal, content, and release owners.
4. Approve the missing-endpoint behavior change and, separately, any CI change.
5. Approve a scan tool and history policy before release verification. No history rewrite or public export is authorized here.

Use [the task list](todo.md) as the execution ledger. Do not mark tasks complete until their acceptance and verification checks pass.
