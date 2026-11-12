# Open-Source Readiness Tasks

## Current owner-requested cleanup

The current request supersedes conflicting historical checklists below. No new tests, commits, or publication are requested.

- [x] Rename public branding and attribution.
- [x] Use generic credential storage and require configured endpoints.
- [x] Remove CI, banner, Office, JATO UI, and active references.
- [x] Generalize Git guidance and Octane examples.
- [x] Keep only existing tests for active plugin/skill scripts.
- [x] Validate retained capabilities and record results.

### Local cleanup validation

Source snapshot: `376bb776fa63baa845a699f5de7ba6c0bfeb8b86`. Work remains uncommitted in the existing `topic-open-source-readiness` checkout. No fetch, push, MR, host uninstall, or history rewrite was performed.

- Removed 183 tracked Office files, 117 tracked JATO UI files, the CI file, and the banner. Removed their active registrations/routes and updated user guides.
- Removed 18 test modules: 17 root structural/documentation/helper/retired-component suites and the GitLab skill-spec suite. Removed the cross-plugin AST-identity case and unused fixtures. Retained tests exercise active scripts. No test files or cases were added.
- Root suite: **156 passed**.
- OKF: **22 passed, 2 skipped** (symlink support unavailable).
- Black Duck: **116 passed, 1 skipped** (POSIX permissions on Windows).
- GitLab: **243 passed, 1 skipped** (POSIX permissions on Windows).
- Octane: **372 passed, 1 skipped** (POSIX permissions on Windows).
- SDLC status/drift: **13 passed; 9 subtests passed**.
- Total across separate suite runs: **922 passed, 5 platform skips**, plus 9 subtests. Commands use `.venv/Scripts/python.exe -m pytest` and the paths in `docs/testing-guidelines.md`.
- `./agents.sh validate` passed. Manual JSON/source parity checks passed for both manifests and all nine plugins. All 80 retained tracked Python files compiled in memory without creating cache artifacts.
- Manual synthetic calls confirmed all three logins and both changed setup paths reject missing endpoints before keyring access. No live service or real keyring was accessed.
- Source searches found no active branded storage/toolkit names or internal Octane example host. Two OpenText matches remain as official vendor source links/labels. Historical task records and Git history retain source names and private provenance; this is not a history scrub or public-release clearance.
- Independent review found one remaining workspace-specific Octane list-node example. It was removed. The focused follow-up approved the fix with no new required findings. Review did not independently rerun tests.
- `git diff --check` passed. Git reports existing LF/CRLF normalization notices, not whitespace errors.
- Native Copilot host routing, live service compatibility, redistribution rights, secret scanning, and remote freshness/publication were not verified by this cleanup.

Chosen identifiers: Agent Development Toolkit; author vnr; marketplace vnr-agent-development-toolkit; keyring namespace AgentDevelopmentToolkit; config override AGENT_DEVELOPMENT_TOOLKIT_CONFIG_HOME. The credential rename intentionally requires a fresh login; no branded migration fallback is required.

## Status and Use

The user explicitly approved [SPEC.md](../SPEC.md), [the plan](plan.md), local autonomous execution, and scoped per-task commits. No cleanup has started. Owner decisions and high-risk approval gates remain required. Credential actions, history rewriting, pushes, and publication are not authorized.

The previous OKF task list is preserved at [archive/okf-todo.md](archive/okf-todo.md). Archive SHA-256: `67b05eb176763c7deaca9551ae48f79664e1002373c0dfaebc9ad34b7bef61d2`.

Use this checkout only: workspace sibling `agents.worktrees/open-source-readiness`, branch `topic-open-source-readiness`, base `4533df1f6a5b4213a7ddde5666ec07af0ddaf65c`. No MR or publication is authorized.

Each task inherits its complete acceptance criteria, verification steps, file scope, and approval gates from the matching section of the plan. All boxes start unchecked. Record actual commands, results, resolved file lists, owner evidence, and blockers below. Do not record secrets or mark missing verification as passed.

## Current Execution: Approved Atomic Cutover

The user selected `Atomic cutover (Recommended)` as a narrow file-count exception. Supersede old Tasks 28-33 and all 38 payload/model batch rows below; do not execute or falsely complete those obsolete staged tasks.

- [x] **Retire the component atomically — COMPLETE within the owner-approved file-count exception**
  - Acceptance: Remove exactly 182 tracked plugin files plus both approved root companions; align only coupled routes, rosters, docs, and tests. Preserve all 11 other plugins, Office contracts, generic security review, independent Octane APIs, user reports/files, history, and external notices.
  - Verification: Persistent absence/retention tests observed RED, immutable-inventory/local-state preflight and fresh scope review before deletion; focused and full separate suites, workspace/compile/help/link/diff checks; fresh diff review; one local retirement commit. Remove both component notices only after their covered files are gone.
  - Scope/dependencies: Use the plan's Current Execution Override; owner choices and prerequisites `e4af183`/`0c94346` complete. No new target, dependency, service action, history rewrite, publication, or generic test suppression.

## Historical Staged Queue: Whole Threat-Modelling Plugin Removal

**Latest direction:** In response to the two-template question, the user instead requested removal of the entire plugin because it is not needed in open source. The two-file retirement proposal and further in-plugin replacement tasks are superseded, not approved/completed as separate removals. No plugin file has been removed yet.

Execute this queue before the legacy checklist below. Use the corresponding active Tasks 27-33 in [the plan](plan.md) for full acceptance criteria, paths, dependencies, and verification. Preserve all previous commits and the completed Office Word path. Keep generic security review and independent Octane APIs. Do not treat a security-related keyword as proof of plugin ownership.

- [x] **Task 27: Deregister the public plugin entry — COMPLETE after the separately approved Windows prerequisite.**
  - Acceptance: Only the withdrawn plugin leaves both marketplace manifests and root install/navigation guidance; all other entries and attribution remain.
  - Verify: RED/GREEN retirement-surface contract, marketplace/workspace checks, full regression/build gate.
  - Depends on: User component-removal direction and fresh expanded-scope review, both complete.
- [ ] **Task 28: Remove obsolete companion routes**
  - Acceptance: SDLC/JATO/context guidance no longer invokes the missing plugin. Generic security review remains; full withdrawn workflows are honestly unavailable.
  - Verify: Scoped route/reference tests and full gate. Do not install a replacement automatically.
  - Depends on: Task 27.
- [ ] **Task 29: Deactivate discovery and removed-feature consumers**
  - Acceptance: Remove the component manifest and only its lazy-loading, resolver, and threat Word/caller/parity expectations. Preserve Office and API behavior/tests.
  - Verify: Meaningful retirement expectations before removal, full gate, record intentional removed-feature case counts.
  - Depends on: Task 28. Model-map entries retire with their actual files below; do not weaken all-agent coverage.
- [ ] **Task 30: Retire the inactive payload**
  - Acceptance: Remove only selected tracked component paths from immutable source `e6a47c14b36f7d982dd05c6c1afbb3327a096e76`. No user files, generated reports, other plugins, external notices, or history/refs change.
  - Verify each batch: Record exact paths/blobs, scoped diff/status, relevant removal/model/Office contracts, full shared regression/build gate, and a local commit. No parent completion after partial batches.
  - Depends on: Task 29. Use the plan's read-only inventory command, not a shrinking directory listing.

### Task 30 Agent Batches

Nine sorted `plugins/threat-modelling/agents/` paths from the pinned removal inventory. Update only their matching entries in `tests/test_agent_models.py` in the same slice. Keep the exact all-agent policy assertion; do not add filters or skips to hide inactive files.

- [ ] Removal agent batch 1: positions 1-4 plus matching model-map entries (at most five files).
- [ ] Removal agent batch 2: positions 5-8 plus matching model-map entries (at most five files).
- [ ] Removal agent batch 3: position 9 plus the final now-empty component model entry (at most two files).
- [ ] Checkpoint: All retired agent definitions and their declarations agree; retained agent policy stays green.

### Task 30 Non-Agent Payload Batches

170 sorted plugin paths from the pinned removal inventory, excluding `plugin.json`, the nine agent files, and both plugin-local `skills/{docx,xlsx}/LICENSE.txt` notices. Each task inherits Task 30 acceptance, exact-path verification, full gate, and commit requirements. Inspect every two batches; auto mode removes routine stepping, not failure/scope gates. Preserve both notices until all their covered material is gone.

- [ ] Removal payload batch 1: positions 1-5.
- [ ] Removal payload batch 2: positions 6-10.
- [ ] Removal payload batch 3: positions 11-15.
- [ ] Removal payload batch 4: positions 16-20.
- [ ] Removal payload batch 5: positions 21-25.
- [ ] Removal payload batch 6: positions 26-30.
- [ ] Removal payload batch 7: positions 31-35.
- [ ] Removal payload batch 8: positions 36-40.
- [ ] Removal payload batch 9: positions 41-45.
- [ ] Removal payload batch 10: positions 46-50.
- [ ] Removal payload batch 11: positions 51-55.
- [ ] Removal payload batch 12: positions 56-60.
- [ ] Removal payload batch 13: positions 61-65.
- [ ] Removal payload batch 14: positions 66-70.
- [ ] Removal payload batch 15: positions 71-75.
- [ ] Removal payload batch 16: positions 76-80.
- [ ] Removal payload batch 17: positions 81-85.
- [ ] Removal payload batch 18: positions 86-90.
- [ ] Removal payload batch 19: positions 91-95.
- [ ] Removal payload batch 20: positions 96-100.
- [ ] Removal payload batch 21: positions 101-105.
- [ ] Removal payload batch 22: positions 106-110.
- [ ] Removal payload batch 23: positions 111-115.
- [ ] Removal payload batch 24: positions 116-120.
- [ ] Removal payload batch 25: positions 121-125.
- [ ] Removal payload batch 26: positions 126-130.
- [ ] Removal payload batch 27: positions 131-135.
- [ ] Removal payload batch 28: positions 136-140.
- [ ] Removal payload batch 29: positions 141-145.
- [ ] Removal payload batch 30: positions 146-150.
- [ ] Removal payload batch 31: positions 151-155.
- [ ] Removal payload batch 32: positions 156-160.
- [ ] Removal payload batch 33: positions 161-165.
- [ ] Removal payload batch 34: positions 166-170.
- [ ] Removal final-notice batch: remove only `skills/docx/LICENSE.txt` and `skills/xlsx/LICENSE.txt` after all covered material is retired. Keep retained Office/root/SDLC notices unchanged.
- [ ] Checkpoint: All 181 remaining plugin files (nine agents, 170 other payload files, and two final notices) are retired; no leftover user/untracked file is deleted implicitly.

### Complete the Component Withdrawal

- [ ] **Task 31: Align retained documentation**
  - Acceptance: Agent/model and helper/test docs describe only retained functionality and no missing second Word helper. Host installations and generated reports are untouched.
  - Verify: Retained Office/API/model contracts, reference review, full gate.
  - Depends on: All Task 30 batches.
- [ ] **Task 32: Resolve the dedicated root guide and deck**
  - Approved retirement: The owner selected `Retire both (Recommended)` for `docs/threat-modelling.md` and `slides/sdd-threat-modelling-process.pptx`; update their index/links and removal contract together.
  - Acceptance: Apply the explicit owner choice and leave no dangling links or implied public-content approval.
  - Verify: Exact asset/link inventory and full gate. Preserve independent Octane description templates.
  - Depends on: Task 31; the owner's dedicated-doc/asset decision is complete.
- [ ] **Task 33: Verify complete withdrawal**
  - Acceptance: No withdrawn payload, registration, active route, model declaration, install command, required resolver case, or dangling component-doc link remains in the candidate. Review generic security references semantically.
  - Verify: Final absence contract, full gate, scoped base-to-HEAD diff and reference review, canonical checkout/user-artifact preservation. Report changed test counts and retained private history honestly.
  - Depends on: Tasks 27-32 and all 38 payload/model batches. No push, MR, history rewrite, host uninstall, or public release.

After this queue, continue retained-plugin Tasks 7, 11-12, 15-20, 22-26 and the Office/JATO corpus scopes as refined in the plan. Superseded threat-plugin tasks and its old support batches below are historical, not executable pending tasks. Do not mark them complete just because the user changed scope.

## Historical and Retained Checklist

The following checklist records earlier accepted work. The active removal queue above takes precedence. Completed Task 5 is a historical implementation now scheduled for removal, not a requirement to preserve that plugin. No general plan approval is repeated; resolve only new scope/owner decisions.

## Phase 1: Owner Decisions

- [x] **Task 1: Establish the disposition inventory** — COMPLETE.
  - Acceptance: Classified affected file families and callers; recorded baseline failures, their resolution, missing optional tools, and unknown permissions.
  - Verify: Immutable-base inventory; workspace validation; 1,268 tests passed with 5 existing platform skips after environment repair and GitLab configuration isolation. See the resumed-run evidence below.
  - Depends on: Human spec/plan approval, received.
  - Remaining gates: Tasks 2-3 need owner decisions. The caller-scope refinements are documented for review before affected cleanup slices.
- [x] **Task 2: Resolve the historical credential finding** — COMPLETE by owner confirmation.
  - Acceptance: The user answered `Revoked or rotated` at the credential-owner gate. Record this as reported remediation, not an independently tested fact.
  - Verify: Owner confirmation received in this session; affected introduction remains reachable in private Git history. No credential value was printed, tested, revoked, or rotated by the agent.
  - Depends on: Task 1, complete.
  - Remaining gate: Public-history treatment and release permission remain unresolved. No ticket reference or revocation timestamp was supplied.
- [x] **Task 3: Approve the content and capability decisions** — COMPLETE as a direction/ownership decision.
  - Acceptance: The user confirms release/licensing authority and selects `Exclude unapproved content`. Apply that exclusion direction to every uncleared content family in the inventory. The previously approved plan supplies the independent procedural replacement strategy and existing-stack constraint.
  - Verify: Explicit user responses recorded in this session; the direction does not grant redistribution rights, select a root license, authorize private-source derivatives, or prove replacement capabilities.
  - Depends on: Task 1, complete.
  - Decision owner: The user owns remaining license choice, retention exceptions, CI behavior, public history/destination, external tool approvals, and publication decisions. Those gates remain open until their specific tasks.
- [x] **Checkpoint A:** The user approved the spec/plan and the independent replacement/exclusion direction. No product files changed. Per-task high-risk, CI, endpoint-behavior, capability-proof, and release gates are not waived.

## Phase 2: Document User Paths

- [x] **Task 4: Make the Office Word path independent** — COMPLETE within the explicitly approved basic scope.
  - [x] Basic Word CLI slice: independently authored standalone helper, executable synthetic tests, and dependency/test documentation; commit `17bfaca`.
  - [x] Word skill activation slice: independently authored guide and updated Office README/AGENTS route only through the basic helper. New routing/example tests and the complete regression/build-level gate pass.
  - Acceptance: Basic Word path runs without legacy helpers. Unsupported rich/template edits stop clearly. No native-rendering or full-schema claim is made.
  - Verify: 59 Word workflow cases, full separate suites, workspace validation, and documented commands executed in a copied skill with only the new helper. Final gate: 1,327 passed, 5 existing platform skips.
  - Depends on: Task 3, Checkpoint A, and explicit basic-scope approval, all complete.
- [x] **Task 5: Make the threat-model Word path independent** — COMPLETE within the approved plain-report/basic scope.
  - [x] Prepare and test the plugin-local helper; commit `db42dd5`. Shared CLI cases cover both standalone copies and a parity check.
  - [x] Complete Task 6's caller slice before guide activation; commit `a009428`. Canonical and approved alternate paths work without templates.
  - [x] Activate and fully verify the independently authored local Word guide and threat README/AGENTS. Standalone plugin installation remains supported; the router link is unchanged.
  - Acceptance: Plain initial-analysis DOCX/Markdown retains evidence, confirmation, default/approved paths, result keys, and upload gates, without the corporate cell layout.
  - Verify: Four new activation cases were observed failing before the guide change. All 126 Word/caller cases and the full gate pass: 1,394 passed, 5 existing platform skips.
  - Depends on: Task 4, the explicit plain-report decision, and the tested caller slice, all complete. Legacy retirement remains a separate Task 6 gate.
- **Task 6: Generate an initial-analysis form without a bundled corporate template — SUPERSEDED by whole-plugin removal, not completed.**
  - [x] Implement the approved independently authored plain-report caller path with matching DOCX/Markdown and honest readiness checks. Seven new caller cases and the full regression gate pass.
  - Former two-template retirement is superseded by the whole-component removal queue. Do not execute it as a separate pending task.
  - Acceptance: Preserve output filenames, evidence, unknowns, user confirmation, result keys, and Octane upload boundaries; do not copy corporate question wording, cell maps, or training text.
  - Verify: Execute synthetic caller commands without bundled templates; compare DOCX text with matching Markdown and inspect readiness/approval instructions.
  - Depends on: Task 5 helper preparation for the caller slice, not prior guide activation. Final retirement follows guide activation and the separate removal gate.
- [ ] **Checkpoint B:** Human reviews Word and initial-form capability evidence before support deletion.
- [ ] **Task 7: Make the Office Excel path independent**
  - Acceptance: Synthetic workbook operations work; recalculation claims match an actual supported engine.
  - Verify: Office contract tests, workbook round-trip/formula exercise, structure checks.
  - Depends on: Task 3 and Checkpoint A.
- **Task 8: Make the threat-model Excel path independent — SUPERSEDED by whole-plugin removal.**
  - Acceptance: Isolated local skill preserves safe XLSX discovery and does not call old helpers.
  - Verify: `tests/test_plugin_skill_discovery.py`, Office contract tests, synthetic workbook exercise.
  - Depends on: Task 7.
- **Task 9: Produce a public-safe threat catalog — SUPERSEDED by whole-plugin removal.**
  - Acceptance: Approved template disposition preserves matching catalog XLSX/Markdown and update-in-place behavior.
  - Verify: Office contract tests; synthetic archive and catalog-content comparison.
  - Depends on: Task 8 and Task 3 catalog decision.
- [ ] **Checkpoint C:** Human reviews spreadsheet/catalog paths and formula limitations.
- **Task 10: Support a user-supplied security-impact calculator — SUPERSEDED by whole-plugin removal.**
  - Acceptance: No unapproved bundled workbook or invented scoring; missing workbook fails clearly.
  - Verify: Discovery and Office contract tests; synthetic-template/missing-template exercises.
  - Depends on: Task 8 and Task 3 calculator decision.
- [ ] **Task 11: Make the PowerPoint path independent**
  - Acceptance: Synthetic presentation path works without old helpers or corporate templates.
  - Verify: Office contract tests, synthetic deck render/visual check, structure checks.
  - Depends on: Task 3 and Checkpoint A.
- [ ] **Task 12: Create slides without bundled corporate branding**
  - Acceptance: Neutral slide command works with optional user inputs; unapproved corporate template/reference is removed.
  - Verify: Office contract tests, structure checks, synthetic slide-command exercise.
  - Depends on: Task 11 and Task 3 brand decision.
- [ ] **Checkpoint D:** All six document paths pass their capability checks before old support files are removed.

## Phase 3: Evidence and Configuration Paths

- **Task 13: Build a DFD from user evidence — SUPERSEDED by whole-plugin removal.**
  - Acceptance: No copied private architecture default; unknowns and user sources are explicit.
  - Verify: Structure checks, non-Filr DFD exercise, retained-reference review.
  - Depends on: Task 3 and Checkpoint A.
- **Task 14: Replace copied corporate training guidance — SUPERSEDED by whole-plugin removal.**
  - Acceptance: Independent public-source guidance preserves legitimate safety and reporting gates.
  - Verify: Source/provenance review, structure checks, orchestrator-reference review.
  - Depends on: Task 3 and Checkpoint A.
- [ ] **Task 15: Route JATO guidance without bundled internal captures**
  - Acceptance: User-supplied design-system path works without bundled captures or implied package rights.
  - Verify: Structure checks, new `tests/test_public_content_contracts.py`, synthetic routing exercise.
  - Depends on: Task 3 and Checkpoint A.
- [ ] **Checkpoint E:** Human reviews evidence-based guidance and the capture-removal inventory.
- [ ] **Task 16: Make UI component lookup configurable**
  - Acceptance: Component/theme/handoff paths have no mandatory corporate service and no unapproved captured content.
  - Verify: Structure and content-contract tests; remaining skill-content inventory review.
  - Depends on: Task 15.
- [ ] **Task 17: Require an explicit Black Duck endpoint**
  - Acceptance: Missing endpoint fails locally before secret retrieval; explicit configuration precedence and safety remain intact.
  - Verify: Black Duck suite and cross-plugin credential-contract suite; synthetic endpoint regression cases.
  - Depends on: Task 3 and explicit behavior-change approval.
- [ ] **Task 18: Use neutral service examples**
  - Acceptance: Examples/evaluations use synthetic values; preserve legitimate vendor references and authorship.
  - Verify: Octane suite, changed JSON/Markdown review, redacted content review.
  - Depends on: Task 1; Task 17 only when example behavior depends on it.
- [ ] **Checkpoint F:** Human reviews UI configuration, endpoint safety, and synthetic examples.

## Phase 4: Bounded Corpus Cleanup

### Batch Contract

Each row below is a separate task with at most five deliverable files. All rows inherit the plan's Support-File Batch Tasks contract:

- Acceptance: Delete only selected approved obsolete files; preserve replacements and required notices; no active caller is broken.
- Verification: Resolve and record exact paths from the pinned base; run focused structure checks, relevant synthetic workflow checks, and `git diff --check`; inspect the scoped diff.
- Scope: One-based sorted eligible path positions from the pinned base. Do not recalculate positions from a shrinking live tree.
- Exclusions for Office: `SKILL.md`, `LICENSE.txt`, and the corporate `.potx` handled by Task 12.
- If permission permits retention, mark the batch complete only after verifying that permission covers every selected file and recording the decision. Do not delete the license of retained material.
- If an unexpected active caller exists, stop and split a bounded caller-update slice before deletion.
- Stop after each two batches, or the final three of an odd-length scope, for the prescribed human checkpoint. Do not batch all completion updates at the end.

### Office Word Support

Root: `plugins/office/skills/docx`. Depends on Tasks 4-6 and Checkpoint D. Acceptance/verification: Batch Contract above.

- [ ] Office Word support batch 1: positions 1-5.
- [ ] Office Word support batch 2: positions 6-10.
- [ ] Checkpoint: Office Word batches 1-2.
- [ ] Office Word support batch 3: positions 11-15.
- [ ] Office Word support batch 4: positions 16-20.
- [ ] Checkpoint: Office Word batches 3-4.
- [ ] Office Word support batch 5: positions 21-25.
- [ ] Office Word support batch 6: positions 26-30.
- [ ] Checkpoint: Office Word batches 5-6.
- [ ] Office Word support batch 7: positions 31-35.
- [ ] Office Word support batch 8: positions 36-40.
- [ ] Checkpoint: Office Word batches 7-8.
- [ ] Office Word support batch 9: positions 41-45.
- [ ] Office Word support batch 10: positions 46-50.
- [ ] Checkpoint: Office Word batches 9-10.
- [ ] Office Word support batch 11: positions 51-55.
- [ ] Office Word support batch 12: positions 56-59.
- [ ] Checkpoint: Office Word batches 11-12.

### Office PowerPoint Support

Root: `plugins/office/skills/pptx`. Depends on Tasks 11-12 and Checkpoint D. Acceptance/verification: Batch Contract above.

- [ ] Office PowerPoint support batch 1: positions 1-5.
- [ ] Office PowerPoint support batch 2: positions 6-10.
- [ ] Checkpoint: Office PowerPoint batches 1-2.
- [ ] Office PowerPoint support batch 3: positions 11-15.
- [ ] Office PowerPoint support batch 4: positions 16-20.
- [ ] Checkpoint: Office PowerPoint batches 3-4.
- [ ] Office PowerPoint support batch 5: positions 21-25.
- [ ] Office PowerPoint support batch 6: positions 26-30.
- [ ] Checkpoint: Office PowerPoint batches 5-6.
- [ ] Office PowerPoint support batch 7: positions 31-35.
- [ ] Office PowerPoint support batch 8: positions 36-40.
- [ ] Checkpoint: Office PowerPoint batches 7-8.
- [ ] Office PowerPoint support batch 9: positions 41-45.
- [ ] Office PowerPoint support batch 10: positions 46-50.
- [ ] Checkpoint: Office PowerPoint batches 9-10.
- [ ] Office PowerPoint support batch 11: positions 51-55.
- [ ] Office PowerPoint support batch 12: positions 56-57.
- [ ] Checkpoint: Office PowerPoint batches 11-12.

### Office Excel Support

Root: `plugins/office/skills/xlsx`. Depends on Tasks 7-10 and Checkpoint D. Acceptance/verification: Batch Contract above.

- [ ] Office Excel support batch 1: positions 1-5.
- [ ] Office Excel support batch 2: positions 6-10.
- [ ] Checkpoint: Office Excel batches 1-2.
- [ ] Office Excel support batch 3: positions 11-15.
- [ ] Office Excel support batch 4: positions 16-20.
- [ ] Checkpoint: Office Excel batches 3-4.
- [ ] Office Excel support batch 5: positions 21-25.
- [ ] Office Excel support batch 6: positions 26-30.
- [ ] Checkpoint: Office Excel batches 5-6.
- [ ] Office Excel support batch 7: positions 31-35.
- [ ] Office Excel support batch 8: positions 36-40.
- [ ] Checkpoint: Office Excel batches 7-8.
- [ ] Office Excel support batch 9: positions 41-45.
- [ ] Office Excel support batch 10: positions 46-50.
- [ ] Office Excel support batch 11: positions 51-52.
- [ ] Checkpoint: Office Excel batches 9-11.

### Threat Word Support

Root: `plugins/threat-modelling/skills/docx`. Depends on Tasks 5-6 and Checkpoint D. Acceptance/verification: Batch Contract above.

- [ ] Threat Word support batch 1: positions 1-5.
- [ ] Threat Word support batch 2: positions 6-10.
- [ ] Checkpoint: Threat Word batches 1-2.
- [ ] Threat Word support batch 3: positions 11-15.
- [ ] Threat Word support batch 4: positions 16-20.
- [ ] Checkpoint: Threat Word batches 3-4.
- [ ] Threat Word support batch 5: positions 21-25.
- [ ] Threat Word support batch 6: positions 26-30.
- [ ] Checkpoint: Threat Word batches 5-6.
- [ ] Threat Word support batch 7: positions 31-35.
- [ ] Threat Word support batch 8: positions 36-40.
- [ ] Checkpoint: Threat Word batches 7-8.
- [ ] Threat Word support batch 9: positions 41-45.
- [ ] Threat Word support batch 10: positions 46-50.
- [ ] Checkpoint: Threat Word batches 9-10.
- [ ] Threat Word support batch 11: positions 51-55.
- [ ] Threat Word support batch 12: positions 56-59.
- [ ] Checkpoint: Threat Word batches 11-12.

### Threat Excel Support

Root: `plugins/threat-modelling/skills/xlsx`. Depends on Tasks 8-10 and Checkpoint D. Acceptance/verification: Batch Contract above.

- [ ] Threat Excel support batch 1: positions 1-5.
- [ ] Threat Excel support batch 2: positions 6-10.
- [ ] Checkpoint: Threat Excel batches 1-2.
- [ ] Threat Excel support batch 3: positions 11-15.
- [ ] Threat Excel support batch 4: positions 16-20.
- [ ] Checkpoint: Threat Excel batches 3-4.
- [ ] Threat Excel support batch 5: positions 21-25.
- [ ] Threat Excel support batch 6: positions 26-30.
- [ ] Checkpoint: Threat Excel batches 5-6.
- [ ] Threat Excel support batch 7: positions 31-35.
- [ ] Threat Excel support batch 8: positions 36-40.
- [ ] Checkpoint: Threat Excel batches 7-8.
- [ ] Threat Excel support batch 9: positions 41-45.
- [ ] Threat Excel support batch 10: positions 46-50.
- [ ] Threat Excel support batch 11: positions 51-52.
- [ ] Checkpoint: Threat Excel batches 9-11.

### JATO Captures

Root: `plugins/jato-ui/skills/jato-ux-guidelines/references`. Depends on Tasks 15-16 and Checkpoint E. Acceptance/verification: Batch Contract above.

- [ ] JATO captures batch 1: positions 1-5.
- [ ] JATO captures batch 2: positions 6-10.
- [ ] Checkpoint: JATO captures batches 1-2.
- [ ] JATO captures batch 3: positions 11-15.
- [ ] JATO captures batch 4: positions 16-20.
- [ ] Checkpoint: JATO captures batches 3-4.
- [ ] JATO captures batch 5: positions 21-25.
- [ ] JATO captures batch 6: positions 26-30.
- [ ] Checkpoint: JATO captures batches 5-6.
- [ ] JATO captures batch 7: positions 31-35.
- [ ] JATO captures batch 8: positions 36-40.
- [ ] Checkpoint: JATO captures batches 7-8.
- [ ] JATO captures batch 9: positions 41-45.
- [ ] JATO captures batch 10: positions 46-50.
- [ ] JATO captures batch 11: positions 51-52.
- [ ] Checkpoint: JATO captures batches 9-11.

### Remaining Phase 4 Tasks

- [ ] **Task 19: Make approved CI validation independent**
  - Acceptance: Approved removal/replacement of corporate SMTP integration preserves validation jobs and updates their tests/guidance.
  - Verify: `tests/test_ci_reports.py`; YAML and job-command review. Remote validation requires separate approval.
  - Depends on: Task 3 and explicit CI approval.
- [ ] **Task 20: Close Office subtree license disposition**
  - Acceptance: Three Office subtrees contain only approved retained material; obsolete licenses removed only after covered files are gone.
  - Verify: Inventory, permission/provenance evidence, focused structure tests.
  - Depends on: All Office support batches, Tasks 4, 7, 11, 12, and root-license decision.
- **Task 21: Close threat-model subtree license disposition — SUPERSEDED by whole-plugin removal.**
  - Acceptance: Two local skills remain installable under verified terms; no remaining restricted originals are relabeled.
  - Verify: Inventory/provenance review, discovery checks, synthetic DOCX/XLSX paths.
  - Depends on: All Threat support batches, Tasks 5, 8, and root-license decision.
- [ ] **Checkpoint G:** Human reviews complete corpus dispositions, not partial batch counts.

## Phase 5: Public Guidance and Licensing

- [ ] **Task 22: Remove unapproved presentation assets**
  - Acceptance: Root banner/process deck disposition and root entry guidance agree; extend content-contract tests.
  - Verify: Content-contract tests, image/Office metadata inspection, local link review.
  - Depends on: Task 3 and Tasks 6, 9, 10, 12, 13, 15.
- [ ] **Task 23: Publish accurate local setup guidance**
  - Acceptance: SDLC/threat banners and callers change together; runtime instructions match proven capabilities; no invented public URL.
  - Verify: Structure and marketplace checks, Markdown-link review, local install-command inspection.
  - Depends on: All capability changes, Tasks 19 and 22.
- [ ] **Task 24: Apply approved licenses and notices**
  - Acceptance: Root license, retained-import notices, author attribution, and synchronized marketplace descriptions have owner approval.
  - Verify: Final provenance inventory and marketplace tests; split any extra plugin notice corrections before implementation.
  - Depends on: Task 3, Tasks 16 and 20-23, and all cleanup scopes.
- [ ] **Checkpoint H:** Technical and legal/content owners review the retained public file set and licensing.

## Phase 6: Final Verification

- [ ] **Task 25: Run the complete regression review**
  - Acceptance: Required tests and synthetic paths pass; no hidden failures, broken references, or missing required checks.
  - Verify: Full shared command block, scoped diff/status review, capability inventory comparison.
  - Depends on: All local implementation tasks and Checkpoint H.
- [ ] **Task 26: Assemble release-owner evidence**
  - Acceptance: Exact file/ref scan scope, resolved credentials, legal permissions, approved history treatment, and release-owner decision are recorded.
  - Verify: Approved independent redacted scans and owner review against the exact candidate revision. No publication.
  - Depends on: Task 2, Task 25, and scanner/history/release-owner approvals.
- [ ] **Final checkpoint:** All spec criteria have evidence; no publication occurs without a separate explicit request.

## Planning Validation

Planning checks belong here. They do not complete any implementation task.

- Scope: Only `tasks/plan.md`, `tasks/todo.md`, and the authorized exact archive copy.
- Baseline: Pinned task checkout at `4533df1f6a5b4213a7ddde5666ec07af0ddaf65c`.
- Code changes, removals, tests, credential calls, scanner installation, commits, pushes, and MRs: not performed during planning.

## Owner Evidence and Decisions

- Spec and plan approval: explicit approval received through the autonomous-build checkpoint. Local preparation and per-task commits are authorized. The user also authorized explicitly adding the ignored spec, plan, and exact OKF archive without changing ignore rules.
- Credential-owner confirmation: the user reports `Revoked or rotated`. No service-side verification, ticket reference, or timestamp was supplied. Treat the credential disposition as owner-reported; public-history treatment remains a separate gate.
- Corporate content policy: exclude all unapproved material; the user explicitly selected this direction and confirmed authority over release/licensing decisions. No retention exception or root license has been selected.
- Office capability/tool strategy: the approved plan uses independently authored procedural replacements and the existing stack. Actual capability proof remains required before support-file deletion. No new Office tool, dependency, or restricted derivative is authorized.
- CI change approval: pending.
- Black Duck missing-endpoint behavior approval: pending.
- Independent scanner choice/version/installation approval: pending.
- Public-history strategy and destination: pending.
- Publication request: absent.

## Blockers and Execution Notes

Record date, task, actual check/result, affected paths, and next action here. Keep pending tasks unchecked. Never include real credentials, user configuration, or raw sensitive scan output.

### Autonomous Run: Preparation and Task 1

- The user explicitly approved local execution and preparation/per-task commits. Preparation commit: `b21ce4cf5426867d1c43e33221f1294e491f09bf` (`docs: record approved open-source readiness plan`).
- No product code, tests, assets, CI, dependencies, credentials, or remotes were changed. The local branch advanced only through the approved planning commit. No implementation test was added. Task 1 changes only this review ledger; a fabricated RED/GREEN test is not appropriate for an inventory record.
- At the first run's stop, Task 1 remained in progress. No later task had started. Required baseline errors were not waived. The resumed-run evidence below records their resolution.

#### Revision and Content Inventory

The pinned implementation base contains **794 tracked files and 12 plugin manifests**. This differs from the initial audit's 800 files because that audit used the separate software-factory revision. Do not mix the counts or import its changes. The preparation commit adds three planning documents; those documents are internal review artifacts, not approved public contents.

| Classification | Scope and count at the pinned base | Current disposition |
| --- | --- | --- |
| Confirmed restrictive terms | `plugins/office/skills/docx/`: 61 files | Independent replacement proposed; existing bundled material is not cleared for distribution. |
| Confirmed restrictive terms | `plugins/office/skills/pptx/`: 60 files | Independent replacement proposed; corporate template also needs a separate disposition. |
| Confirmed restrictive terms | `plugins/office/skills/xlsx/`: 54 files | Independent replacement proposed. |
| Confirmed restrictive terms | `plugins/threat-modelling/skills/docx/`: 61 files | Preserve the local DOCX contract through an independent replacement. |
| Confirmed restrictive terms | `plugins/threat-modelling/skills/xlsx/`: 54 files | Preserve the local XLSX contract through an independent replacement. |
| Approval-required corporate captures | `plugins/jato-ui/skills/jato-ux-guidelines/references/`: 52 files | No public redistribution evidence recorded. Replace the caller path before exclusion. |
| Approval-required internal architecture | Two files under `plugins/threat-modelling/skills/dfd/references/filr-architecture/` | No release permission recorded. Public path must use user evidence. |
| Approval-required training extract | `plugins/threat-modelling/skills/ot-threat-model-guidelines/references/full-reference.md` | Independently authored public-source guidance proposed. |
| Approval-required documents | Initial Analysis DOCX/Markdown, Security Impact Calculator workbook, Threat Catalog workbook | Review every template, formula, field-map, and supporting instruction. Missing approval does not permit rebranding. |
| Approval-required media | Corporate POTX, process PPTX, root/SDLC/threat banners | No public release evidence recorded. Review media and embedded metadata. |
| Suspected historical credential | `skills/alm-octane/.env.example:10-11` at `9efd4fc`; value removed by `93c81b3` | Owner confirmation was missing during the inventory. The user subsequently reported revocation/rotation at the Task 2 gate. Introduction remains in private history; no secret value or full client identifier was copied into this ledger. |
| Runtime corporate default | Black Duck token helper setup/login URL fallback | Explicit-endpoint behavior change still needs its separate approval. |
| Corporate CI coupling | `.gitlab-ci.yml`, `tests/test_ci_reports.py`, `docs/testing-guidelines.md` | CI change is not approved. Preserve current jobs until that gate is resolved. |
| Incomplete release licensing | Root license absent; Angular/Vitest and other retained imports need full provenance review | Corporate license/release owner is not identified. Existing per-plugin notices are not a root license. |
| Local-only credential configuration | Canonical checkout's ignored Black Duck `.env` identified by the prior audit | Not copied to the task checkout. Exclude local configuration from any candidate. |
| Other retained tracked files | Remaining files across all 12 plugins, docs, tests, manifests, scripts, and lockfiles | Not automatically cleared. Task 3 and final provenance/content review must assign dispositions before release. |

Each restrictive subtree contains `LICENSE.txt`. The reviewed terms cover code, prompts, assets, and other skill components. They prohibit derivative works and third-party distribution at lines 20-21. Retain the notices while covered originals remain. This inventory does not claim legal interpretation beyond the recorded restriction.

#### Caller Inventory and Required Plan Refinements

Caller paths were identified using `git grep -l -F` against immutable base `4533df1f6a5b4213a7ddde5666ec07af0ddaf65c`, without printing matched content.

- Filr architecture: `plugins/threat-modelling/agents/tm-dataflow-diagrams.agent.md`, `skills/dfd/SKILL.md`, `skills/dfd/references/full-reference.md`, and `skills/dfd/references/sources.md` within that plugin. **Task 13 omits the full reference file. Split the caller/content changes into reviewed bounded slices before execution.**
- Initial form: `docs/threat-modelling.md`, `plugins/threat-modelling/agents/tm-initial-analysis.agent.md`, and the initial-analysis skill's `references/full-reference.md`. The Markdown template also requires a content-owner decision. **Add the general documentation caller to the bounded plan before template removal.**
- Security calculator: `plugins/threat-modelling/skills/security-impact-calculator/references/full-reference.md` contains the exact workbook-name reference. The planned skill and agent routes also require review.
- Threat Catalog: `docs/threat-modelling.md`, `plugins/threat-modelling/skills/threat-catalog-update/references/full-reference.md`, and its `scripts/update_threat_catalog.py`. **Task 9 does not cover all callers. Review the script and reference guide, and split complete caller paths before replacing the workbook.**
- Corporate slide template: `plugins/office/skills/ot-slide-deck/references/full-reference.md`, `plugins/office/skills/pptx/SKILL.md`, and `plugins/office/skills/pptx/editing.md`. The editing reference is part of the obsolete support inventory; it must not remain an active route during removal.
- Corporate threat guidance: `docs/threat-modelling.md`, the threat orchestrator, five threat agents, the guidance skill entry, and the threat router reference the skill identifier. Preserve the identifier or expand the bounded caller-change plan before a rename.
- JATO guideline entry: `plugins/jato-ui/README.md`, `plugins/jato-ui/skills/jato-ux-guidelines/SKILL.md`, and its router. Task 16 must still review other JATO content rather than infer clearance from this narrow identifier search.
- Tests: `tests/test_plugin_skill_discovery.py` asserts the local threat XLSX resolver; `tests/test_ci_reports.py` asserts corporate SMTP behavior. Preserve or explicitly revise those behavioral contracts with tests.

These findings are execution blockers for the affected future slices, not permission to exceed the five-file scope or silently revise approved behavior. The plan is not yet updated because execution stopped at baseline verification.

#### Baseline Commands and Results

The default `python` has no pytest. The already-existing canonical virtual environment has Python 3.11.12 and pytest 9.1.1. It lacks `requests`, `yaml`, `dotenv`, and `keyring`. Its interpreter was used to execute tests from the task checkout; no packages were installed into that environment.

From this checkout root, `PY` below denotes `../../agents/.venv/Scripts/python.exe`. Test commands used `PYTHONDONTWRITEBYTECODE=1`, `PYTHONNOUSERSITE=1`, and `UV_OFFLINE=1`. Pytest cache creation was disabled with `-p no:cacheprovider`. No package downloads were permitted.

| Actual command | Result |
| --- | --- |
| `bash ./agents.sh validate` | Passed: both marketplace manifests, 12 plugin manifests, and marketplace source paths. |
| `$PY -m pytest tests -q --strict-config --strict-markers -p no:cacheprovider --tb=short` | Incomplete: tool timeout at 240 seconds. No root failure summary was returned. Do not claim the suite passed. |
| `$PY -m pytest plugins/okf/tests -q -p no:cacheprovider --tb=short` | 22 passed, 2 skipped. Existing skips were not changed or suppressed. |
| `$PY -m pytest plugins/blackduck/skills/blackduck/tests -q -p no:cacheprovider --tb=short` | Collection error: `requests` is missing in `test_blackduck_vulnerabilities.py`. |
| `$PY -m pytest plugins/gitlab/skills/gitlab/tests -q -p no:cacheprovider --tb=short` | Collection error: `yaml` is missing in `test_spec_compliance.py`. |
| `$PY -m pytest plugins/octane/skills/alm-octane/tests -q -p no:cacheprovider --tb=short` | 372 passed, 1 skipped. Existing skip was not changed or suppressed. |
| `$PY -m pytest plugins/sdlc/skills/ai-sdlc/scripts/test_update_status.py plugins/sdlc/skills/ai-sdlc/scripts/test_detect_drift.py -q -p no:cacheprovider --tb=short` | 9 passed. |
| `$PY -m pytest tests --collect-only -q -p no:cacheprovider` | 476 root tests collected in isolation. Collection is not execution. |
| `$PY -m pytest tests/test_skill_cli_smoke.py -vv -p no:cacheprovider -o faulthandler_timeout=20 --durations=10 --tb=short` | Diagnostic run: 18 passed in 29.46 seconds. Compilation and CLI-help checks pass in isolation. This does not resolve the full-suite timeout. |

`requirements/ci.lock` already pins PyYAML. `requirements/credential-runtime.lock` already pins requests and the credential runtime dependencies. This is an incomplete local test environment, not evidence that production code needs a dependency change. Obtain approval for a separate task-local test environment using those existing hash-pinned lockfiles. Do not modify the canonical environment or project lockfiles.

The full-suite timeout's precise cause is unconfirmed. Isolated smoke checks passed; do not label the timeout a product bug without a targeted reproduction. After the environment is approved and ready, rerun the root suite with verbose progress, duration reporting, and a larger bounded timeout to identify any remaining slow or blocked test.

The first inventory command exceeded 120 seconds because it repeatedly launched `git show` for each file and search term. Replacing those reads with a few immutable `git grep` queries completed the same caller inventory. No repository changes were needed.

Tool availability: `uv` and PowerShell are present; LibreOffice (`soffice`) and Gitleaks are absent. Do not install Office/scanner tools or claim corresponding capability/scan checks passed.

#### Stop and Resume Conditions

1. RESOLVED: The user approved task-local environment setup from the two existing hash-pinned lockfiles, including downloads if needed. The resumed run prepared that environment without modifying the canonical environment, lockfiles, or runtime dependencies.
2. RESOLVED: Baseline collection errors and the incomplete root run are resolved. Task 1 verification is complete; see results below.
3. RESOLVED FOR LOCAL DIRECTION: Task 2 received owner-reported revocation/rotation confirmation. Task 3 received the user's authority confirmation and exclusion policy. Specific license, CI, endpoint behavior, external tool, history, and publication decisions remain gated in their own tasks.
4. OPEN: Revise the affected bounded caller slices before cleanup, then obtain any changed scope or high-risk approval.
5. Stop at the owner-decision gate. Re-invoke `/build auto` after the owner decisions are supplied. No product cleanup, credential action, history rewrite, push, or publication has occurred.

### Resumed Autonomous Run: Task 1 Verification Completed

The user re-invoked `/build auto` after explicitly approving an isolated test environment. Existing uncommitted changes were limited to this expected task ledger. The selected branch was `topic-open-source-readiness` at planning commit `b21ce4cf5426867d1c43e33221f1294e491f09bf`.

#### Isolated Environment Repair

Run from the task checkout:

```bash
uv venv --no-project --no-python-downloads --python C:/Users/vnr/Code/Gitlab/Filr/agents/.venv/Scripts/python.exe .venv
uv pip install --python .venv/Scripts/python.exe --require-hashes --only-binary :all: -r requirements/ci.lock -r requirements/credential-runtime.lock
```

- Created only the ignored task-local `.venv`. It uses the existing CPython 3.11.12 interpreter.
- Installed 22 packages with required hashes from the existing lockfiles. No package versions, lockfiles, project runtime requirements, or canonical environment were changed.
- Verified local imports of pytest 9.1.1, requests 2.34.2, PyYAML 6.0.3, dotenv, and keyring. Import verification did not query the keyring or authenticate to a service.
- Package downloads were authorized for setup. All test runs used `UV_OFFLINE=1`, `PYTHONDONTWRITEBYTECODE=1`, and `PYTHONNOUSERSITE=1`. Pytest cache creation was disabled.

#### Complete Baseline Results

In this table, `PY` denotes `.venv/Scripts/python.exe` in the task checkout.

| Actual command | Result |
| --- | --- |
| `bash ./agents.sh validate` | Passed: marketplace/plugin JSON and marketplace source checks. |
| `$PY -m pytest tests -vv --strict-config --strict-markers -p no:cacheprovider --tb=short --durations=12 -o faulthandler_timeout=90` | 476 passed in 196.48 seconds, within a 600-second command limit. Includes the existing script compilation and CLI-help checks. |
| `$PY -m pytest plugins/okf/tests -q -rs -p no:cacheprovider --tb=short` | 22 passed, 2 existing skips: symlinks unavailable. |
| `$PY -m pytest plugins/blackduck/skills/blackduck/tests -q -rs -p no:cacheprovider --tb=short` | 116 passed, 1 existing Windows skip for POSIX permission bits. |
| `$PY -m pytest plugins/gitlab/skills/gitlab/tests -q -rs -p no:cacheprovider --tb=short` | Initial run: 271 passed, 2 dotenv failures, 1 existing Windows permission skip. Resolved by the isolated rerun below. |
| `$PY -m pytest plugins/octane/skills/alm-octane/tests -q -rs -p no:cacheprovider --tb=short` | 372 passed, 1 existing Windows skip for POSIX permission bits. |
| `$PY -m pytest plugins/sdlc/skills/ai-sdlc/scripts/test_update_status.py plugins/sdlc/skills/ai-sdlc/scripts/test_detect_drift.py -q -rs -p no:cacheprovider --tb=short` | 9 passed. |
| GitLab command above with an empty temporary home/configuration and inherited service variables removed | 273 passed, 1 existing Windows permission skip in 9.96 seconds. No product or test edit was required. |

The first complete GitLab run exposed user-configuration interference in two dotenv tests. The shared fixture sets synthetic process credentials but does not isolate the durable profile directory for tests that remove those credentials. The resolver can prefer active profile metadata over a legacy dotenv fixture, as its contract permits.

The diagnostic rerun removed inherited `GITLAB_`, `OCTANE_`, `BLACKDUCK_`, and `FILR_AGENT_SKILLS_` variables. It set `HOME`, `USERPROFILE`, `APPDATA`, and `XDG_CONFIG_HOME` to a fresh temporary home and set `FILR_AGENT_SKILLS_CONFIG_HOME` to a separate empty temporary directory. It used the same task-local interpreter and full GitLab suite. The fixture-provided synthetic settings remained available within tests. The suite then passed without reading user profile files or changing configuration precedence. The precise user-profile contents were not inspected or copied.

Record this as a test-runner isolation requirement, not a production authentication fix. A future test-fixture hardening change needs its own bounded task and regression test. No test was disabled or changed in this task.

The previous root-suite timeout is no longer a baseline blocker. The complete rerun finished under the larger bounded limit. Duration reporting identified several Git Bash/PowerShell helper tests as relatively slow, but did not establish a single defect as the cause of the prior timeout.

**Final baseline:** workspace validation passed; **1,268 passed, 5 existing platform skips** across separate suite processes. All previously failing collection and dotenv checks passed in the appropriate isolated environment. No new behavioral test was warranted for this inventory-only task. No new application build system exists; the root compilation/help and workspace checks provide the existing build-level gate.

Task 1 changed only this internal evidence ledger. Its local commit is `e8d0bc721a0c1ade3876486635e5e8956fb2851b` (`docs: record readiness inventory and verified baseline`). No product cleanup is complete. LibreOffice and Gitleaks remain unavailable and unapproved for installation; corresponding future capability/scan gates remain open.

### Owner Decisions After the Baseline Checkpoint

The user supplied these explicit responses:

1. Credential disposition: `Revoked or rotated`. Task 2 records this as owner-reported remediation. No independent service check or credential operation was performed. Commit: `55c617f` (`docs: record owner-reported credential remediation`).
2. Corporate release/licensing authority: `I am authorized`. Record the user as the owner of subsequent corporate release and licensing decisions. This does not select a license or establish third-party redistribution rights.
3. Local public-content direction: `Exclude unapproved content`. Apply this to the restrictive Office corpus, JATO captures, internal architecture/training material, corporate forms/calculator/catalog, presentation media, and other uncleared content identified by the inventory. Replace required user paths independently before approved support deletion. No retention exception is assumed.

These decisions complete the coordination scope of Tasks 2-3. They do not authorize a history rewrite, public export, release, credential operation, new tool installation, CI change, or implicit-endpoint behavior change. Capability gates remain required. Before affected implementation slices, revise the bounded caller scopes identified by Task 1 and preserve their atomic user paths. The next `/build auto` invocation resumes from that planning refinement and Task 4; do not ask for general plan approval again. Ask only about materially changed scope or a specific required safety/owner decision.

### Task 4: Bounded CLI Slice and Capability Gate

The resumed run verified a clean task checkout at `9ee29b5e7fa882963eb51199977f8dbdeb7a4f5b`. No general plan approval was repeated.

#### Bounded Plan Refinement

- Split Task 4 into a complete standalone basic CLI slice (helper, tests, script guide, test guide: four deliverable files) and the separate skill activation path (skill entry, plugin README, plugin AGENTS: three files).
- Keep the existing Office router link unchanged. The new helper is not an import, copy, or derivative of the legacy helper implementations. Only legacy file paths/metadata were inspected; the helper was authored from independent requirements and public format/API documentation.
- Refine Tasks 6, 9, and 13 into bounded caller-path and later gated-retirement slices. Include the general threat-modelling guide, initial-form Markdown, catalog updater/full reference, and DFD full reference discovered by Task 1. No template, support file, or architecture page was removed.
- The new CLI does not activate the Word skill or clear the legacy subtree for release. Its licensing remains an owner decision. Existing restrictive licenses remain untouched.

#### RED / GREEN Evidence

Added `tests/test_office_public_workflows.py` before adding the helper. The initial four cases failed because the independently authored helper did not exist. The minimum implementation made those four pass. Additional tests first exposed rich-document data loss, entity handling, invalid package acceptance, resource bounds, nested-paragraph amplification, metadata loss, carriage-return normalization, and archive/XML edge cases. Each targeted test group was observed failing before its corresponding fix.

The final **55 synthetic cases pass**. Tests copy only `docx_basic.py` into a temporary directory and invoke it with `python -I`. They do not depend on the legacy Office implementation, corporate templates, credentials, native Office applications, or newly installed packages. Expected data is checked through CLI results and independent ZIP/XML reads.

The helper supports body-XML paragraph extraction, plain-paragraph creation, and literal replacement only in its exact basic three-part document/profile. It rejects unsupported edits rather than silently flattening rich documents. It never overwrites an existing path, changes an input file, executes a package member, or fetches an external relationship. Text/ZIP/XML/count/depth limits apply together. Expat 2.6.0+ is required for parsing. This is not a server sandbox or a Word renderer.

#### Bounded Adversarial Review

Three read-only review rounds inspected only the new helper and tests. Cross-model review was skipped in this autonomous context; no external review CLI was invoked.

- Round 1 findings were **valid and actionable**: nested-paragraph output amplification, XML escaping exceeding the read limit, missing structured EOF handling, and unsupported metadata loss. Added reproductions, then bounded traversal/output, checked serialized XML size, caught EOF reads, and validated the basic metadata profile before replacement.
- Round 2 findings were **valid and actionable**: out-of-root comments/PIs could be discarded, and literal CR serialization could normalize unrelated text. Added failing cases for all three package parts and both source/replacement CR values. Basic editing now rejects comments/PIs before tree construction and serializes CR as character references.
- Round 3 findings were **valid and actionable**: corrupt unused members were not checked, metadata XML lacked the global depth bound, and Unicode whitespace outside text could be silently removed. Added failing reproductions, then streamed every accepted member for bounded integrity checks, bounded all parsed XML during construction, and allowed only XML whitespace in structural positions.

All finding reproductions pass after fixes. No fourth review round was run; the bounded review limit was reached. Present the remaining capability limitation to the user before activation. These checks do not certify native compatibility or legal clearance.

#### Full Regression and Build-Level Results

Test commands used the task-local `.venv/Scripts/python.exe`, `PYTHONDONTWRITEBYTECODE=1`, `PYTHONNOUSERSITE=1`, `UV_OFFLINE=1`, and `-p no:cacheprovider`. No new dependencies were installed. GitLab used the previously established empty temporary home/configuration and removed inherited service variables.

| Check | Result |
| --- | --- |
| `bash ./agents.sh validate` | Passed. |
| `python -m pytest tests -q --strict-config --strict-markers --tb=short --durations=8` with the test environment above | 531 passed in 197.41 seconds, including the 55 new Word cases and existing compile/help checks. |
| OKF suite | 22 passed, 2 existing symlink-unavailable skips. |
| Black Duck suite | 116 passed, 1 existing Windows POSIX-permission skip. |
| Isolated GitLab suite | 273 passed, 1 existing Windows POSIX-permission skip. |
| Octane suite | 372 passed, 1 existing Windows POSIX-permission skip. |
| SDLC status/drift suite | 9 passed. |
| New helper compilation and Python 3.10 grammar parse | Passed, without writing bytecode. |
| Separate synthetic create/replace/extract exercise | Passed; output read back as expected, CRC checks passed, and every generated package part parsed independently. |

**Total: 1,323 passed, 5 existing platform skips.** No failing test was removed or disabled. No standalone application build system exists. Native rendering and full OOXML schema validation were not performed.

#### Capability Decision Required Before Activation

The implemented CLI is intentionally basic. It does not preserve rich formatting, comments, tracked changes, images, headers/footers, arbitrary templates, or visual layout during edits; unsupported editing inputs are rejected. Main-body extraction is not a complete document-story extractor. No native Word/LibreOffice rendering was verified.

Do not activate this helper as the broad Word skill until the user either accepts that reduced basic scope or authorizes research/installation of appropriate richer tooling under a revised bounded plan. Do not silently downgrade the advertised capability. Task 4 remains open, and all dependent Word/template tasks remain pending. General plan approval, credential confirmation, and content-exclusion direction remain recorded and need not be requested again.

#### Capability Gate Resolved

After the tested CLI checkpoint, the user explicitly selected `Basic scope (Recommended)`. The user accepts plain-paragraph creation, bounded body-text extraction, and edits only within the basic profile, with no rich-formatting, arbitrary-template-editing, or rendering claims. This is recorded in the root spec and Task 4 plan.

The completed CLI slice is commit `17bfaca2532de194fc0c8596045c5fbfcaceebf8`; the prior bounded-plan refinement is `d9d534a0af3cf73448075eb45495bbd06e4a4b2a`. The legacy Word skill and support files remain unchanged. The subsequent `/build auto` run resumed the activation slice and its full verification without repeating the general plan or basic-scope approval. Legacy deletion, other artifact capability decisions, and publication remain separately gated.

### Task 4: Word Skill Activation Completed

The activation run started from clean task HEAD `6a8cb049e8ab7ec0cdd3956c07a3ef8db43527b6`. It invoked the incremental implementation and TDD workflows with the already approved basic scope.

Added four activation cases before changing the guide. They failed because the Office README/AGENTS did not identify the independent helper, the legacy guide referenced other helpers, and the standalone example path was absent. Replaced the guide independently from the approved helper contract and public format/API references. Updated only Office README/AGENTS and the new test module. A test command-extraction regex initially matched only the help line; corrected its newline escape, then verified all five documented commands execute in the copied standalone skill.

The 59-case Word suite passes. The guide resolves its own installation directory, uses only `scripts/docx_basic.py`, confirms writes through the host, reads outputs back, states resource/parser limits, and refuses unsupported rich capabilities. It does not import or authorize legacy fallback helpers. The existing router link and all legacy support files/license notices are unchanged. The former guide remains in private Git history; public-history disposition remains open.

#### Activation Regression Gate

Runs used the task-local interpreter, `PYTHONDONTWRITEBYTECODE=1`, `PYTHONNOUSERSITE=1`, `UV_OFFLINE=1`, and disabled pytest cache creation. GitLab used the established empty temporary home/configuration and removed inherited service variables. No dependency or tool was installed.

| Check | Result |
| --- | --- |
| `bash ./agents.sh validate` | Passed. |
| Repository suite with strict config/markers | 535 passed in 241.89 seconds, including compile/help, discovery/frontmatter/marketplace checks, and the 59 Word cases. |
| OKF | 22 passed, 2 existing symlink-unavailable skips. |
| Black Duck | 116 passed, 1 existing Windows permission skip. |
| Isolated GitLab | 273 passed, 1 existing Windows permission skip. |
| Octane | 372 passed, 1 existing Windows permission skip. |
| SDLC status/drift | 9 passed. |

**Total: 1,327 passed, 5 existing platform skips.** No test was disabled or deleted. The guide's actual create/extract/replace/read-back commands ran under `python -I` from a copied skill with no legacy support files. This verifies the approved basic path, not native Word rendering, visual layout, or complete schema conformance. Those claims remain excluded from Task 4.

The activation slice has four deliverable files (guide, Office README, Office AGENTS, and executable routing/example tests), plus this status ledger. It contains no support-file deletion, template change, credential action, CI change, dependency change, or remote publication. Task 4 is complete in commit `fa5b022fa1b7b2893e9eb3076b884ce6cdb9678f` (`feat(office): activate the approved basic Word workflow`). Task 5 starts with its separate threat-modelling caller and artifact-contract checks.

### Task 5: Initial-Analysis Contract Blocker

Read the threat-modelling README and the immediately relevant initial-analysis agent, skill, reference, and orchestrator call sites. The current agent requires copying the bundled corporate DOCX and editing only its designated table cells. The full reference also requires the legacy Word unpack/pack path. The orchestrator requires `initial-analysis-form.docx` plus matching Markdown and an explicit readiness result.

The independent basic helper intentionally rejects tables, rich templates, and unknown metadata. Office-only basic-scope approval does not establish permission to change this separate threat-model form contract. Replacing the local Word guide first would leave its caller unable to meet the current mandatory template-editing requirements.

No threat-model helper, guide, agent, template, or output was changed during inspection. Task 5 stays open. The user subsequently selected `Plain report (Recommended)`: independently authored plain-paragraph initial-analysis DOCX plus matching Markdown instead of the corporate table layout. This is the required format decision, not an approval for new dependencies or template deletion. Preserve artifact filenames, evidence, user-confirmation, and Octane upload approval boundaries in any option.

If the plain artifact is approved, refine the dependency graph into: prepare/test the plugin-local helper; change and test the initial-analysis caller path; activate the independent local Word skill; retire old templates/support only at the separate removal gate. The caller slice must depend on the helper preparation, not on prior activation of an incompatible replacement guide. Do not combine the whole change into an oversized task or create a cyclic dependency between Tasks 5 and 6.

#### Plain-Report Decision Recorded

The root spec and plan now record the explicit `Plain report (Recommended)` response. Preserve `initial-analysis-form.docx`, `initial-analysis-form.md`, evidence, user confirmation, output result keys, and upload gates. Use `templatePath: null` for the independent plain-report mode. Describe local structural/read-back checks accurately; do not equate them with native rendering, full schema validation, remote server acceptance, or upload authorization.

The user did not authorize copying the corporate question wording or field map, adding dependencies, deleting the old templates, or publishing remotely. Keep the old local Word guide intact while preparing its independent helper. Change/test the caller with that helper before activating the replacement guide. These bounded slices and their non-cyclic order are recorded in the plan.

The next `/build auto` run resumes helper preparation, then the plain-report caller and local Word activation. Do not repeat the general plan, Office basic-scope, or initial-analysis plain-format approval. Stop only for a new unresolved decision or a specific required safety/removal gate.

### Task 5: Local Helper Preparation Verified

Resumed from clean `3541ed73d9e8ac2e69e2ab4b57ebd86513fada64`. Before adding the threat helper, parameterized the shared synthetic CLI cases for both plugins and added a parity check. RED: 55 threat cases reported the missing independent helper and the parity check failed; 59 existing Office cases still passed.

Copied only the newly authored Office `docx_basic.py` into the threat plugin's own `skills/docx/scripts/` directory. No legacy source was copied or imported. Both copies have SHA-256 `96e6b81c188902ed82316f9de31d4bf8ba7673d37c65331aa5c978ea8165dcbd`. This is deliberate plugin-local duplication, not a cross-plugin runtime dependency. Updated script/test guidance to document both maintained copies and their independent-installation contract.

GREEN: all 115 Word workflow cases pass, including copied standalone subprocesses for both plugins and byte parity. The existing threat Word guide, initial-analysis caller, corporate templates, and all legacy license/support files remain unchanged in this preparation slice.

Full regression used the task-local interpreter, offline `uv`, disabled bytecode/pytest caches, and the established isolated GitLab home/configuration:

| Check | Result |
| --- | --- |
| Workspace validation | Passed. |
| Root suite with strict configuration/markers | 591 passed in 268.17 seconds. |
| OKF | 22 passed, 2 existing symlink-unavailable skips. |
| Black Duck | 116 passed, 1 existing Windows permission skip. |
| Isolated GitLab | 273 passed, 1 existing Windows permission skip. |
| Octane | 372 passed, 1 existing Windows permission skip. |
| SDLC status/drift | 9 passed. |

Total: **1,383 passed, 5 existing platform skips**. Existing compilation/help checks pass; no separate application build system exists. Native rendering and full schema validation are not claimed. No dependency was installed or changed. The four deliverable files are the local helper, parameterized tests, script guide, and test guide; this ledger is the status record.

Task 5 remains in progress. Continue directly to the already approved Task 6 caller slice before activating the replacement local Word guide. Do not retire templates or support files under this preparation commit.

### Task 6: Plain-Report Caller Slice Verified

The helper preparation is commit `db42dd5` (`feat(threat-modelling): prepare standalone basic Word helper`). Continued directly to the approved caller slice without repeating the format or plan approval.

Added six initial-analysis cases before rewriting any caller instruction. RED: the old paths still required the corporate form/legacy Word path, lacked the plain helper command path and draft/null-template states, and did not describe the approved plain mode. Rewrote only the initial-analysis agent, skill entry, full reference, and Step 1/destination text in the root workflow guide from independent requirements. Preserved the sixteen existing result keys, default filenames, evidence/unknowns, specific content confirmation, and separate Octane upload gates.

The reference now creates a literal plain-paragraph DOCX from the new UTF-8 Markdown report and reads it back with the prepared plugin-local helper. It does not load the legacy Word guide, corporate form, question wording, or cell map. It records `templatePath: null`, defaults both confirmation/readiness flags to false, and explicitly separates local readiness from upload authorization, native rendering, full schema validation, service acceptance, and corporate approval.

The read-only adversarial review found one valid, actionable path bug: approved alternate filenames were not carried through fixed command examples. Added a failing case with existing canonical artifacts and approved alternate outputs. Corrected the guide/agent/reference/workflow to resolve and retain explicit `MARKDOWN_PATH` and `DOCX_PATH` values. The alternate-path case now proves canonical existing files remain unchanged. A second review found no substantive remaining contract violation. Cross-model review was skipped for this autonomous run; no external review CLI was invoked.

Seven caller cases pass. Executable tests copy only the local helper into an isolated plugin, run the reference's actual create/read-back commands for canonical and approved alternate paths (including workspace spaces), and compare DOCX text with Markdown. Other caller tests inspect instruction/schema/approval contracts; no live model-host behavior or remote upload was tested.

Full gate, with the same task-local/offline/cache-disabled environment and isolated GitLab home:

| Check | Result |
| --- | --- |
| Workspace validation | Passed. |
| Root strict suite | 598 passed in 269.87 seconds, including compilation/help and 122 Word/caller cases. |
| OKF | 22 passed, 2 existing symlink-unavailable skips. |
| Black Duck | 116 passed, 1 existing Windows permission skip. |
| Isolated GitLab | 273 passed, 1 existing Windows permission skip. |
| Octane | 372 passed, 1 existing Windows permission skip. |
| SDLC status/drift | 9 passed. |

Total: **1,390 passed, 5 existing platform skips**. No failing test was disabled or deleted. No separate application build system exists; existing compile/help and structural checks passed. The five deliverable files are the agent, skill entry, independently rewritten reference, root workflow guide, and tests, plus this status ledger.

Task 6 remains incomplete because its final template-retirement slice requires explicit removal approval. No template or legacy support/license file changed. Task 5 remains in progress until the local Word guide is activated and verified. Continue to that activation next; do not restore a corporate-template dependency or ask for the already recorded plain-report decision again.

### Task 5: Local Word Activation Verified

Activated the local guide only after the plain caller was committed in `a009428`. Added four new failing activation cases by extending the README/AGENTS scope, guide-route, and actual guide-command checks to the threat plugin. Copied only the independently authored Office basic guide into the local `docx` entry and updated threat README/AGENTS. No legacy implementation or template content was reused. The local guide uses only its own `docx_basic.py`; it imports no other installed plugin and makes no legacy fallback.

GREEN: all 126 Word/caller cases pass. Both plugins' five documented guide commands run from copied standalone skill directories with only their local helper. The existing threat router still selects the same local skill name. The initial-analysis caller continues to use the prepared helper directly, preserving its approved paths and result protocol.

Final activation gate used the task-local interpreter, offline `uv`, disabled bytecode/pytest caches, and isolated GitLab home/configuration:

| Check | Result |
| --- | --- |
| Workspace validation | Passed. |
| Root strict suite | 602 passed in 279.11 seconds, including compilation/help, discovery/frontmatter checks, and 126 Word/caller cases. |
| OKF | 22 passed, 2 existing symlink-unavailable skips. |
| Black Duck | 116 passed, 1 existing Windows permission skip. |
| Isolated GitLab | 273 passed, 1 existing Windows permission skip. |
| Octane | 372 passed, 1 existing Windows permission skip. |
| SDLC status/drift | 9 passed. |

Total: **1,394 passed, 5 existing platform skips**. This run added 67 test cases relative to its starting baseline through shared-copy coverage, caller/path checks, and guide activation. No test was disabled or removed. No native rendering, complete schema validation, live model-host behavior, remote upload, or corporate approval was claimed.

The four activation deliverable files are the local guide, threat README/AGENTS, and tests, plus this status ledger. All legacy support/license files and both old initial-analysis templates remain unchanged. No new dependency, credential action, CI change, history rewrite, push, or MR occurred. Task 5 is complete in `e6a47c1` (`feat(threat-modelling): activate the independent Word path`); Task 6 remains open only for the separately approved template-retirement slice.

### Task 6: Exact Template-Retirement Review

At clean HEAD `e6a47c1`, identified exactly two tracked resource files for the final retirement slice. No contents were printed:

| Candidate | Size | Git blob |
| --- | --- | --- |
| `plugins/threat-modelling/skills/initial-threat-model-analysis/references/Initial Analysis Form.docx` | 29,858 bytes | `1d412cfbcb255cae212f44e2f36ba70d9620e484` |
| `plugins/threat-modelling/skills/initial-threat-model-analysis/references/initial-analysis-form.md` | 2,426 bytes | `a8004e8483eb8277ced2856f44b90f20ce29572c` |

A tracked search of plugins/docs/tests/root entry guidance found only a negative naming example in `docs/threat-modelling.md` and a negative regression assertion for the spaced DOCX name. The legacy Markdown resource path has no remaining reference in those sources. Neither is an active caller. Executable report tests already operate in an isolated plugin containing neither resource and verify canonical/approved alternate outputs without changing existing canonical artifacts.

A fresh read-only adversarial review inspected the exact two-file scope, new caller/guidance, and tests. It found no substantive remaining caller or output-name collision. The review explicitly retained the requirement for deletion sign-off. Cross-model review was skipped in this autonomous context; no external review CLI ran.

The proposed action is local retirement of those two reference files only, followed by scoped regression/documentation checks and a revertible commit. It must not remove generated workspace reports, helpers, any license notice, another template, or Git history/refs. It does not purge the former material from private history or clear the repository for public release. Recheck the approved file paths/blobs and worktree status before removal.

At that review, removal approval was not recorded and no file was deleted. The user's subsequent whole-plugin direction superseded this exact two-file question. Do not ask it again or treat the old Task 6 retirement as the next executable task.

### Scope Change — Remove the Whole Plugin

The user explicitly requested removal of the threat-modelling plugin because it is not required in open source. Updated `SPEC.md`, the active queue in `tasks/plan.md`, and this ledger. Earlier in-plugin replacements remain historical commits; dependent replacement/corpus tasks are superseded, not falsely marked complete. All other release work remains in scope.

Read-only checks against `e6a47c14b36f7d982dd05c6c1afbb3327a096e76` confirm **182 tracked component paths = 1 manifest + 9 agents + 170 other payload files + 2 notices**. The cleanup partition contains 38 bounded batches, with notices retained until all covered material is gone. Agent batches include their exact model-map deletions without filtering all-agent policy coverage. The read-only inventory snippet parses, its partition covers each path exactly once, and `git diff --check` passes.

A fresh read-only `code-reviewer` reviewed this expanded plan and relevant structural/test consumers. Verdict: approved plan, no actionable findings. That review ran no tests/builds, read no restricted helper or corporate training/architecture bodies, and made no writes/service calls. It does not grant content/legal clearance. No cross-model review is claimed.

No implementation or deletion occurred for the new scope. Only the three planning/status files changed. The previous full runtime gate remains the unchanged-source baseline: **1,394 passed, 5 existing platform skips**. It was not rerun for these prose-only planning changes.

**Owner choice resolved:** The user selected `Retire both (Recommended)` for `docs/threat-modelling.md` and `slides/sdd-threat-modelling-process.pptx`. Include both companions and their link cleanup in Task 32. This does not reopen authorization to remove the plugin itself. Do not repeat general plan, basic Word, or plain-report approvals. No remote publication, history rewrite, credential action, CI change, host uninstall, or new dependency is authorized.

### Task 27 — Public Registration Slice; Gate Blocked

Added `tests/test_public_plugin_surface.py`. All five new cases failed before implementation. Removed only the withdrawn entry/metadata from both marketplaces and its install/navigation examples from root README/AGENTS; retained all 11 other registered plugins and author attribution. Added an accurate full-workflow withdrawal and unchanged-host/report notice.

Focused gate: **33 passed** (retirement surface, marketplace synchronization, workspace structure, helper checks). Workspace validation and `git diff --check` pass. The full separate-suite run reached root **607 passed**, OKF **22 passed/2 skipped**, Black Duck **116 passed/1 skipped**, GitLab **273 passed/1 skipped**, Octane **372 passed/1 skipped**, then SDLC **8 passed/1 failed**. Total: **1,398 passed, 5 existing skips, 1 failure**. Do not describe this as a passing full gate.

The failure is `UpdateStatusTests.test_concurrent_status_updates_preserve_each_history_entry`: `update_status.py` raises `PermissionError [WinError 5]` at the atomic `os.replace` of a temporary `status.json`. Both that helper and its test are unchanged from pinned pre-removal source `e6a47c1`.

Read-only diagnostics used source copies in temporary folders, not another checkout or user feature artifacts. A fixed 20-run isolated baseline concurrency experiment had **0 failures**; this does not explain away the observed full-gate failure. A controlled baseline reproduction with a destination read handle open fails with the same WinError 5 even while the writer holds its advisory lock, preserves previous status bytes, and succeeds once that handle closes. The original intermittent handle holder is **not identified**; do not blame an antivirus or claim a complete root-cause identification.

Both independent helper compile/help checks pass. No app build system exists. No tests were skipped/disabled, no production SDLC code was changed, and no plugin payload, guide, deck, or notice has been deleted. Task 27 remains incomplete; its five deliverable changes and this ledger are uncommitted. The owner approved both companion retirements in `dcd3ee5`; no need to ask that again.

**Blocker decision:** The owner explicitly selected `Approve bounded fix (Recommended)` for a separate minimal Windows-sharing-error repair. Do not repeat that approval or suppress the original failing evidence.

### Authorized Prerequisite — Bounded Windows Status Save

Added four test methods: transient native errors 5/32/33, persistent native-error attempt/wait bounds and byte preservation, unrelated errors with no retry, and real Windows held-reader recovery while the writer lock is held. Before the implementation, the transient/persistent subtests and the real held-reader case failed. The implementation now retries only those native error codes, using the same closed/fsynced sibling file, at most ten attempts and nine 0.05-second waits. No destination unlink, permission change, broad refactor, dependency, or lock change.

Scoped gate: **13 passed and 9 subtests passed**. A fresh read-only code review approved the four deliverable files with no findings; the reviewer did not independently run tests. Official Python/Microsoft sources establish native error meanings, not our selected retry policy.

Fresh full gate on the combined working tree: root **607 passed**, OKF **22 passed/2 skipped**, Black Duck **116 passed/1 skipped**, GitLab **273 passed/1 skipped**, Octane **372 passed/1 skipped**, SDLC **13 passed/9 subtests passed**. Total: **1,403 passed, 9 additional subtests passed, 5 existing platform skips**. The existing concurrency test remains enabled. The original intermittent handle holder remains unknown; the deterministic regression proves the class of sharing failure is handled within the approved bound, not that every filesystem interference is recoverable.

The Windows-Python-launched Bash validation attempt rejected the existing CRLF script invocation. The documented validation command succeeded when run through the same outer Bash used for prior checks; no script line-ending or Git/environment configuration was changed. Workspace validation, diff checks, and independent helper/status source compile/help checks pass. No app build system exists.

Commit only the four prerequisite deliverables (`update_status.py`, its test, script guide, testing guide) plus SPEC/plan/ledger. The five pending Task 27 deliverables stay unstaged for their own scoped commit. This repair does not delete any plugin file or authorize publication. The prerequisite was committed separately as `e4af183`.

### Task 27 — Complete

Fresh scoped review approved all five entry-point deliverables with no findings; all 11 retained marketplace entries and author attribution are unchanged. The five new contracts passed after their recorded RED run. The same combined-state full gate above is green: **1,403 passed, 9 subtests passed, 5 existing skips**, with workspace validation and compile/help/diff checks. No source changed after that gate other than this status text.

Commit the five deliverables and this ledger separately from the Windows prerequisite. The component payload and dedicated root assets are still present. Continue to Task 28 consumer routing, not another approval question or legacy template task. At that public-deregistration stage, no publication, external service action, history rewrite, or payload/license deletion occurred.

### Whole-Component Atomic Retirement — Complete

The owner explicitly selected `Atomic cutover (Recommended)`, replacing the 38 planned cleanup batches with one reviewed, full-gated component retirement. SPEC and the active plan/queue record this narrow file-count exception. The old staged task/batch rows are superseded, not falsely completed.

Before deletion, all **184** authorized tracked paths matched immutable `e6a47c1`: **182** component files plus the dedicated guide and slide deck. No changed, untracked, or ignored component data was found. A fresh read-only scope review approved the atomic sequence. New absence/route contracts were observed **12 failing / 6 passing** before implementation; the retained-capability case already passed.

Removed exactly those paths. The two component notices stayed present until all 180 other component files were gone, then retired with the approved root companions. No intermediate deletion commit. Aligned the 14 coupled SDLC/JATO route, docs/roster, and test files; no scope expansion or runtime-code change outside the retired component.

Focused gate: **155 passed**, including all **59** retained Office Word cases. Every retained Word fixture/helper/test function body is AST-identical to `0c94346` when compared as UTF-8. Office and Octane trees, SDLC agents, and status runtime have zero cutover diff. The all-agent model policy remains unfiltered; model allocation is now **12 Haiku / 12 Luna** across 24 retained agents.

Fresh separate full gate: root **502 passed**, OKF **22 passed/2 skipped**, Black Duck **116 passed/1 skipped**, GitLab **273 passed/1 skipped**, Octane **372 passed/1 skipped**, SDLC **13 passed/9 subtests passed**. Total: **1,298 passed, 9 subtests passed, 5 existing platform skips**. Workspace validation, retained helper/status compile/help, unstaged/staged diff checks, and obsolete-path/command reference checks pass. No application build system, native rendering, host-installation test, or live service verification is claimed.

Test-count change reconciles exactly: **13** new withdrawal/retention cases and **118** intentionally retired passing cases (67 threat-copy/parity/initial-analysis Word cases, 9 model assignments, 3 lazy-router cases, 6 component-owned resolver cases, and 33 frontmatter candidates: 9 agents, 11 commands, 13 skills). Thus `1403 + 13 - 118 = 1298`. No retained Office test body or generic model/discovery assertion was weakened, and no failing test was skipped.

Fresh final read-only review approved all 184 removal identities and all 14 coupled/three artifact changes with no findings. It independently checked scope, protected-tree equality, model counts, AST equality, and diff whitespace; it did not rerun the full suite or inspect restricted deleted bodies. Final-diff review cannot itself prove deletion order; the preflight/deletion checks above recorded that sequence.

Commit boundary: **201 files**, comprising 184 approved deletions and 17 coupled/artifact modifications. Stage the complete reviewed diff before the single atomic retirement commit; do not commit only the already-staged deletions. All source/research is local at recorded SHAs. No push/MR, new dependency, CI change, credential action, host uninstall, user-report removal, or history rewrite. Canonical checkout and other repositories were not written.

The withdrawn component still exists in private Git history. Remaining Office restricted material, JATO/corporate-content review, credentials/history treatment, CI approval, root license, exact-artifact scan, and release/publication gates are not cleared by this retirement. Next retained work is Office Excel Task 7; its supported capability/recalculation boundary must be settled before any reduced-scope activation or new tool/dependency installation.
