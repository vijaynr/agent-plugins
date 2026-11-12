# Spec: Open-Source Readiness

## Current owner scope override

The latest owner request supersedes the older retention, CI, credential-name, and test requirements below. Rename the public toolkit to **Agent Development Toolkit**, attribute it to **vnr**, and use marketplace ID `vnr-agent-development-toolkit`. Remove the CI file, banner, Office plugin, JATO UI plugin, and their active callers. Use generic credential storage without a branded compatibility fallback; existing users must log in again. Require configured service endpoints. Use general Git guidance and neutral Octane examples. Keep only existing tests for active plugin or skill scripts. Do not add tests. Preserve historical evidence and Git history. These coupled changes form one owner-requested cleanup; the older five-file batch limit does not apply to this scope. No commit, push, or publication is requested.

## Status

Approved for local execution with the implementation plan. The user explicitly approved autonomous execution and local per-task commits. Separate owner, safety, and publication gates still apply.

The user selected credential remediation, license-safe replacements, and corporate-content separation. The user subsequently directed removal of the entire `threat-modelling` plugin because it is not required in the open-source toolkit. This supersedes replacement work inside that plugin and the standalone two-template retirement proposal. Keep the existing technical stack. Remote changes are not authorized.

This spec is an internal review artifact. Do not include it in a public release without a disclosure review.

## Objective

Prepare the agent toolkit for a possible public open-source release. Remove unauthorized material from the proposed public contents. Resolve suspected credential exposure. Keep the remaining plugins useful and independently installable.

Target users:

- Public developers who install and use the toolkit without corporate network access.
- Maintainers who prepare and verify the public contents.
- Security, legal, and content owners who approve release decisions.

Local cleanup does not establish legal permission to publish. A public release remains blocked until credential owners and release owners complete the required decisions.

### Core features

1. Record credential findings without secret values. Track owner decisions and remediation status.
2. Remove restricted third-party materials unless documented redistribution rights permit retention.
3. Replace retained required capabilities with independently authored material or approved open-source alternatives. The withdrawn `threat-modelling` plugin requires no replacement workflow. Do not copy or paraphrase restricted materials to create replacements.
4. Remove corporate documents, training extracts, design captures, and branded assets from the proposed public contents unless their owners approve release.
5. Use neutral examples and explicit user configuration instead of corporate hosts, workspace identifiers, personal paths, and contact details.
6. Keep plugin manifests, marketplace files, commands, routers, tests, and documentation consistent with retained capabilities.
7. Establish approved licensing and third-party notices for all retained material.
8. Review the exact proposed public artifact and its intended Git history before publication.

### Approved Word capability scope

At the Task 4 capability gate, the user explicitly selected `Basic scope (Recommended)`. The public Office Word replacement may provide plain-paragraph creation, bounded body-text extraction, and literal edits only to the helper's basic document profile. It must reject unsupported rich/template edits instead of silently removing content. It must not claim rich-format preservation, arbitrary-template editing, native rendering, or full OOXML schema validation.

This decision permits the retained Office helper and guide with accurate limitations. It does not authorize new dependencies or broader spreadsheet/presentation capability changes. Removing the separate threat-modelling plugin must not remove or weaken the Office helper or its tests.

### Approved removal of threat-modelling

The user explicitly directed removal of the `threat-modelling` plugin from the open-source toolkit and selected `Atomic cutover (Recommended)`. This is a narrow file-count exception: retire the already-approved component, two root companions, and coupled references/declarations/tests together in one reviewed, full-gated local commit instead of 38 payload batches. It adds no deletion targets or other permissions. The earlier plain initial-analysis replacement is no longer a required deliverable. Preserve the historical implementation records and commits; do not reset or rewrite history to undo that work.

Remove the complete tracked `plugins/threat-modelling/` subtree and its marketplace/install/discovery registrations, obsolete companion routes, and feature-specific tests. The subtree contains 182 tracked files at `e6a47c14b36f7d982dd05c6c1afbb3327a096e76`, including the recent independently authored helper and guides. Do not leave those new files behind as an unregistered duplicate plugin.

Keep the independent Office Word path, generic SDLC security review, and standalone Octane APIs and their tests. A reference to threat assessment or security fields is not evidence of a dependency on the withdrawn plugin. Do not remove those independent capabilities by keyword matching.

The owner explicitly selected `Retire both (Recommended)` for the dedicated root companions: remove `docs/threat-modelling.md` and `slides/sdd-threat-modelling-process.pptx` and update their links with the component cleanup. Update related guidance and tests consistently. Do not uninstall anything from a user's host, delete generated workspace reports, remove other plugins, or invent a replacement full threat workflow. The removed workflow must be described as unavailable, not silently redirected to an incompatible service.

This scope change does not authorize new dependencies, CI changes, credential actions, Git history rewriting, pushes, or public publication. Remaining Office, JATO, credential, corporate-content, and release-license work stays in scope.

### Out of scope

- Build a new audit product, scanner, public-export system, or CI security gate.
- Add runtime dependencies or replace Python, Bash, pytest, or the plugin layout.
- Publish a repository, push branches, create an MR, or change repository visibility.
- Rewrite Git history, delete refs, or rotate credentials automatically.
- Change product repositories or access real service accounts to test credentials.
- Carry unrelated software-factory changes into the default-branch baseline. One explicit owner-approved prerequisite is permitted: a separate minimal fix/test slice for native Windows status-file replacement failures, with bounded retries, unchanged atomicity/locking, persistent errors preserved, and a fresh full gate. No broader factory refactor is authorized.

## Tech Stack

Keep the existing Python scripts, Bash helpers, JSON manifests, Markdown skills, and pytest tests. Keep current runtime version requirements and pinned dependencies.

Use Python standard-library modules for any small local inspection utilities. New external audit tools require separate approval. Existing heuristic audit results are not a substitute for a final independent security review.

## Commands

Run these commands from the task checkout root. They are validation commands, not permission to install packages or contact services.

```bash
# Workspace structure and declared assets
bash ./agents.sh validate

# Repository checks, including marketplace synchronization and CLI smoke tests
python -m pytest tests -q --strict-config --strict-markers

# Additional existing plugin checks; run as separate processes
python -m pytest plugins/okf/tests -q
python -m pytest plugins/blackduck/skills/blackduck/tests -q
python -m pytest plugins/gitlab/skills/gitlab/tests -q
python -m pytest plugins/octane/skills/alm-octane/tests -q
python -m pytest plugins/sdlc/skills/ai-sdlc/scripts/test_update_status.py plugins/sdlc/skills/ai-sdlc/scripts/test_detect_drift.py -q

# Focused checks for manifest, reference, and marketplace changes
python -m pytest tests/test_plugin_workspace.py tests/test_frontmatter.py tests/test_marketplace_sync.py -q

# Final local change review
git diff --check
git diff --stat
git status --short --branch
```

There is no new build, development server, or lint tool for this task. CLI smoke tests and workspace checks provide the existing build-level validation. Run the documented PowerShell worktree-helper tests only if that helper changes and the required toolchain is available.

Do not install missing test dependencies without approval. Record unavailable tools and blocked checks. Do not claim that an unrun check passed.

Secret scans must report locations and classifications, not secret values. Select the final independent scan tool and its executable command during planning, subject to approval. No scanner is added by this spec.

## Project Structure

```text
SPEC.md                         Draft spec at this checkout root
plugins/<plugin>/               Retained commands, agents, skills, and assets
plugins/<plugin>/plugin.json     Plugin surface and declared assets
marketplace.json                Primary marketplace manifest
.github/plugin/marketplace.json Synchronized marketplace copy
AGENTS.md                       Workspace routing instructions
README.md                       Public setup and capability descriptions
CONTRIBUTING.md                 Contributor and validation rules
docs/                           General developer and test guidance
tests/                          Workspace and cross-plugin regression tests
requirements/                   Existing pinned test/runtime dependencies
assets/                         Assets that need license and branding review
slides/                         Presentations that need disclosure review
.gitlab-ci.yml                  Existing CI and corporate notification integration
```

Future implementation may add a root `LICENSE` and a consolidated third-party notice only after the applicable license decision. Preserve plugin-specific notices where required.

Use the existing feature-artifact layout for later plan and task records if that workflow is selected. Do not create a second copy of this spec. The user approved the root path instead of the local SDLC feature-folder convention.

`SPEC.md` is ignored by the current `.gitignore`. Keep it local for this review. Do not force-add it or change ignore rules without approval. Preserve the unrelated `SPEC.md` in the canonical checkout.

## Code Style

- Use four-space indentation, `snake_case` names, and `pathlib.Path` in Python.
- Keep scripts small. Follow existing CLI and JSON-output contracts.
- Use kebab-case plugin, skill, command, and agent names.
- Keep secret values out of source, diagnostics, tests, and review artifacts.
- Use synthetic credentials and reserved example domains in tests and examples.
- Use short, clear sentences in new documentation. Follow the SDLC output-language guidance without claiming formal language certification.

Illustrative style for a secret-free finding record:

```python
from pathlib import Path


def finding_location(path: Path, line_number: int) -> dict[str, object]:
    if line_number < 1:
        raise ValueError("line_number must be positive")
    return {
        "path": path.as_posix(),
        "line_number": line_number,
        "review_required": True,
    }
```

This example sets style only. It does not require a new scanner or reporting API.

## Testing Strategy

### Local regression tests

Use existing pytest suites. Run focused tests after each cleanup slice. Run the workspace suite and affected plugin suites before implementation is complete.

- Verify that retained manifests reference files that exist.
- Verify that removed skills have no active command, router, agent, or documentation references.
- Verify that the two marketplace manifests remain synchronized.
- Verify CLI help without credentials, user configuration, keyring access, or network access.
- Preserve authentication safety checks and independently installable plugins.
- Use temporary directories, synthetic fixtures, and mocked service calls.
- Add regression tests for changed behavior in the closest existing test module.
- If a capability is removed, replace obsolete assertions with checks for the approved new behavior. Do not delete failing tests merely to obtain a pass.

No new repository-wide coverage threshold is required. Each changed behavior must have a deterministic regression test. Pure content removals require reference checks and scope review.

### Content and release review

- Inventory every retained third-party component and its applicable license and notice requirements.
- Review Office archive text, embedded files, metadata, comments, and hidden content. Review image content separately when relevant.
- Review corporate references in code, examples, documentation, CI, templates, and assets.
- Check the final file set and the intended public Git refs. A clean working tree does not mean that Git history is safe.
- Keep ignored local configuration, virtual environments, caches, reports, and task artifacts outside the public contents.
- Require an independent credential scan before release. Record scan scope, tool version, result, and reviewed false positives without secret values.
- Record legal and content-owner approval separately from passing technical checks.

## Boundaries

### Always do

- Work only in the dedicated task checkout and task branch.
- Preserve canonical checkouts and unrelated local work.
- Record findings with paths and immutable source revisions.
- Distinguish confirmed restrictions, suspected secrets, and approval-required content.
- Make unresolved decisions block release rather than guess permission.
- Use independently authored or explicitly licensed replacements.
- Keep required third-party notices intact.
- Update affected manifests, routers, README files, and tests together.
- Validate from the task checkout and report checks honestly.
- Recheck the complete public artifact after local cleanup.

### Ask first

- Choose an open-source license or claim corporate permission to publish.
- Retain corporate assets or documents based on a claimed release exception.
- Add dependencies, scanner tools, or external services.
- Change CI configuration, including notification behavior and corporate includes.
- Add a new public-export process or split the repository.
- Change public CLI contracts or remove an entire plugin.
- Change ignore rules or track this internal spec.
- Rewrite history, remove refs, revoke/rotate credentials, push, publish, or create an MR.

### Never do

- Print, copy into artifacts, commit, or transmit real secret values.
- Test suspected credentials against live services.
- Treat deletion from the latest files as credential remediation.
- Treat a replacement license header as permission to redistribute restricted content.
- Derive replacement material from restricted third-party content without permission.
- Claim legal approval, credential revocation, or complete secret detection without evidence.
- Upload repository contents to an external scanner without approval.
- Disable safety gates or remove failing tests to hide a regression.
- Include ignored local files by copying the entire checkout into a public archive.

## Success Criteria

- [ ] The owner resolves the historical Octane client-secret finding. Record revocation/rotation confirmation or evidence that the value is synthetic.
- [ ] Release owners approve the treatment of affected history. No affected history is published while this decision is open.
- [x] The withdrawn threat-modelling plugin is absent from the local candidate tree, registrations, discovery/model declarations, and active routes; both dedicated companions are retired under explicit owner approval. Full regression/source/diff checks pass. This does not clear remaining content, history, or publication gates.
- [ ] Each retained restricted Office skill subtree is removed, replaced independently, or covered by documented redistribution permission. Removing the threat plugin does not clear the remaining Office corpus.
- [ ] Each retained third-party component has verified provenance and required license notices.
- [ ] Corporate content is removed from public contents or has written owner approval for release.
- [ ] Public setup and retained plugin use do not depend on corporate endpoints or private documents. Service plugins accept user-supplied configuration.
- [ ] Corporate CI includes, notification addresses, personal metadata, and branding have explicit dispositions. Apply any CI changes only after approval.
- [ ] A corporate owner approves the root license and public-release rights before a public license is applied.
- [ ] Retained manifests and documentation contain no broken references caused by the cleanup.
- [ ] Relevant existing validation suites pass. Record any missing checks; unresolved failures block completion.
- [ ] The final independent credential scan has no unresolved findings. Exclude ignored local credentials from the artifact.
- [ ] A release owner approves the exact file set and intended Git history. Publication requires a separate user request.

## Research

### Routing and source revisions

Task slug: `open-source-readiness`.

| Repository | Role | Ref and commit | Reason |
| --- | --- | --- | --- |
| agents | Read | audited `feat-software-factory`, `34f41d0c8bc8d93224ac3773b87ee13255767991` | Initial audit evidence |
| agents | Read/write | verified `origin/main`, `4533df1f6a5b4213a7ddde5666ec07af0ddaf65c` | Independent default-branch base for this task |

- Authoritative project and remote: configured `origin`, `git@gitlab.otxlab.net:portfolio/wpg/filr/agents.git`.
- Intended future MR target: the same project, branch `main`. No MR or push is requested.
- Task branch: `topic-open-source-readiness`.
- Checkout: sibling `agents.worktrees/open-source-readiness` under the workspace root.
- Writer: this session only. No other writer is assigned.
- Intended files in this phase: root `SPEC.md` only.
- Existing MR: none recorded for this new task. Verify live state before any future publication.
- The user approved a new worktree and the root spec location. No existing feature workspace was reused.

### Audit evidence

- Historical `skills/alm-octane/.env.example:10-11` at `9efd4fc` contains a client ID and a secret-looking value. The value was removed by `93c81b3`. Affected history remains reachable from both audited HEAD and the selected default branch. Credential validity is unverified.
- The `LICENSE.txt` files under `plugins/office/skills/{docx,pptx,xlsx}` and `plugins/threat-modelling/skills/{docx,xlsx}` prohibit third-party distribution and derivative works. These license files are identical at the two recorded source revisions.
- `plugins/jato-ui/README.md` describes local JATO guidance captures. Review the captured reference tree for public-release rights.
- `plugins/threat-modelling/skills/dfd/references/sources.md` identifies copied Filr architecture documents. This source list is identical at the two recorded revisions.
- `plugins/threat-modelling/skills/ot-threat-model-guidelines/references/full-reference.md` identifies a corporate training PDF as its source. This reference is identical at the two recorded revisions.
- Corporate Office templates, threat-model forms/workbooks, presentation assets, and author metadata need individual review. Copyright alone does not prove that release is prohibited; absence of approval blocks inclusion.
- The root has no repository-wide `LICENSE`. Existing third-party notices cover selected imported materials, not the whole repository.
- A populated ignored Black Duck token-like value exists only in the canonical checkout configuration. The audit found no exact match in reachable Git objects. Do not copy that configuration into this task or a public artifact.
- The selected base's `.gitlab-ci.yml` includes a corporate project and notification settings. Public portability and disclosure review must include CI. This spec does not authorize CI changes.

### Verification limits

The initial audit checked 800 tracked files and 270 locally reachable commits. It used local heuristic text checks and Office archive inspection. It was not a certified secret scan, complete image review, or legal clearance. Do not assume every conclusion applies to unreviewed branches, hidden remote refs, external release assets, or future commits.

## Open Questions and Approval Gates

These decisions do not prevent local spec review. They block the corresponding implementation or publication step.

1. Which corporate owner can approve public release and the root license?
2. Can the credential owner confirm remediation of the historical Octane value?
3. Which corporate documents or assets have explicit public redistribution approval?
4. If replacements cannot preserve required functionality, should the affected capability be removed? Ask before removing a whole plugin.
5. Should the eventual public release use approved rewritten history or a separately approved clean-history destination? Do not execute either option without approval.
6. Which independent scan tool and final release-review process will the user approve?

The user approved this spec and the implementation plan for local execution. Proceed in dependency order. Stop for unresolved owner decisions and high-risk actions. Publication is not authorized.
