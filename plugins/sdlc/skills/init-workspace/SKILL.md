---
name: init-workspace
disable-model-invocation: true
description: "Initialize SDD workspaces: optionally create a fresh git branch before /spec, then create or reuse .features/<feature> artifact folders."
---

Use **ASD-STE100 Simplified Technical English** for all end-user replies and artifact text. First read and follow [the output language rules](../../references/output-language.md), including for delegated work.

# Init Workspace

Use this skill before SDD phases write feature-scoped artifacts. For `/spec`, it
can first create a fresh git branch from the user's chosen base. It also reuses
or creates deterministic `.features/<feature>` workspaces, ensures the AIDD
`.gitignore` allowlist is present, and, when requested, artifact subdirectories
such as `threat-model`.

Default SDD workspace:

```text
.features/<feature>/
```

Threat modelling workspace:

```text
.features/<feature>/threat-model/
```

## Steps

1. For `/spec`, always prompt the user about worktree creation:
   - Ask whether to create a dedicated git worktree or continue in the current working copy.
   - If the user chooses a dedicated git worktree:
     - Read the repository's branch policy and apply `git-workflow-guidelines` before proposing or validating a branch name.
     - Propose the default worktree destination: `../<repo>.worktrees/<feature>`.
     - Run `init-git-worktree.ps1` or `init-git-worktree.sh`.
     - Run `prepare-init-workspace` with `-Root "<worktreePath>"` to create `.features/<feature>` inside the worktree.
     - Record worktree attributes in `status.json` using `python skills/ai-sdlc/scripts/update_status.py set-worktree "<worktreePath>/.features/<feature>" --worktree-path "<worktreePath>" --repo-root "<repoRoot>"`.
     - Direct all downstream lifecycle phases (`/design`, `/plan`, `/build`, `/review`, `/ship`) to execute inside `<worktreePath>`.
     - Completion criterion: a worktree is registered, and `.features/<feature>` exists inside the worktree root.
   - If the user chooses to continue in the current working copy:
     - Read the repository's branch policy and apply `git-workflow-guidelines` before proposing or validating a branch name.
     - Ask the user for the new branch name and base branch/ref unless already provided.
     - Inspect the working tree first. If there are existing changes, ask whether to stash them before branch creation.
     - If the user approves stashing, run the branch helper with stash approval.
     - If the user does not approve stashing, do not create a fresh branch; continue on the current branch.
     - Completion criterion: either a fresh branch is checked out, or the user has chosen to continue on the current branch.
   - For non-`/spec` SDD phases, do not create branches or worktrees unless the user explicitly asks.

2. Choose workspace kind.
   - For SDLC artifacts (`SPEC.md`, optional `DESIGN.md`, `tasks/PLAN.md`, `tasks/TODO.md`, `status.json`), use no subdir.
   - For threat modelling artifacts, use `--subdir threat-model`; the root feature folder still owns `status.json`.
   - Prefer reuse over creation: an existing `.features/<similar-feature-name>` folder is the workspace unless the user explicitly chooses a new folder.
   - Completion criterion: artifact destination is either the reused feature folder or a named subdirectory.

3. Run the workspace helper script from the repository root.

   The helper automatically invokes `ensure-aidd-gitignore` so `.features/*` is
   ignored by default while AI SDLC planning artifacts remain trackable.

   Bash/macOS/Linux/Git Bash:

   ```bash
   bash skills/init-workspace/scripts/prepare-init-workspace.sh "<feature-name-or-.features-folder>"
   bash skills/init-workspace/scripts/prepare-init-workspace.sh --subdir threat-model "<feature-name-or-.features-folder>"
   ```

   Windows PowerShell:

   ```powershell
   powershell -ExecutionPolicy Bypass -File skills/init-workspace/scripts/prepare-init-workspace.ps1 "<feature-name-or-.features-folder>"
   powershell -ExecutionPolicy Bypass -File skills/init-workspace/scripts/prepare-init-workspace.ps1 -Subdir threat-model "<feature-name-or-.features-folder>"
   ```

   Completion criterion: JSON output has `ok: true`, or `ambiguous: true` with candidate folders that must be shown to the user for selection before rerunning.

4. Use the JSON paths.
   - `featureFolder` / `featureWorkspace` is the canonical `.features/<feature>` folder.
   - `artifactWorkspace` is where the current artifact should be written.
   - `statusPath` is the canonical SDLC state file and must be read/updated by SDD phase skills.
   - `statusCreated: true` means the helper initialized a new `status.json`; if false, reuse and update the existing file.
   - `matchedSimilarFeatureFolder: true` means the helper reused one existing similar feature folder instead of creating a new one.
   - `ambiguous: true` means multiple similar folders exist; prompt the user to choose one and rerun the helper with that exact folder path.
   - `workspaceExisted: true` means resume and avoid overwrites without confirmation.
   - `createdWorkspace: true` means a new destination was created only because no exact or similar feature folder existed.
   - Completion criterion: downstream skills use `artifactWorkspace` for writes, update `statusPath`, and preserve existing artifacts when `workspaceExisted` is true.

## Worktree helper

Use when starting `/spec` and the user chooses a dedicated git worktree, or when the user explicitly asks for a worktree.

Bash/macOS/Linux/Git Bash:

```bash
bash skills/init-workspace/scripts/init-git-worktree.sh "<feature-name>"
bash skills/init-workspace/scripts/init-git-worktree.sh "<feature-name>" --branch "<branch>" --base "<base-ref>"
bash skills/init-workspace/scripts/init-git-worktree.sh "<feature-name>" --worktree-path "<custom-path>"
```

Windows PowerShell:

```powershell
powershell -ExecutionPolicy Bypass -File skills/init-workspace/scripts/init-git-worktree.ps1 -Feature "<feature-name>"
powershell -ExecutionPolicy Bypass -File skills/init-workspace/scripts/init-git-worktree.ps1 -Feature "<feature-name>" -Branch "<branch>" -Base "<base-ref>"
powershell -ExecutionPolicy Bypass -File skills/init-workspace/scripts/init-git-worktree.ps1 -Feature "<feature-name>" -WorktreePath "<custom-path>"
```

Both helpers verify that the base resolves to a commit. Before they create a
worktree, they fetch the selected remote and stop if the fetch fails. If the
requested path is already a worktree, they reuse it only when its checked-out
branch matches the requested branch. A dry run does not fetch; the base must
already resolve in the local repository.

## Branch helper

Use only when starting `/spec` or when the user explicitly asks for a fresh
branch.

Bash/macOS/Linux/Git Bash:

```bash
bash skills/init-workspace/scripts/init-git-branch.sh \
  --branch "<new-branch>" \
  --base "<base-branch-or-ref>"

bash skills/init-workspace/scripts/init-git-branch.sh \
  --branch "<new-branch>" \
  --base "<base-branch-or-ref>" \
  --stash-approved
```

Windows PowerShell:

```powershell
powershell -ExecutionPolicy Bypass -File skills/init-workspace/scripts/init-git-branch.ps1 `
  -Branch "<new-branch>" `
  -Base "<base-branch-or-ref>"

powershell -ExecutionPolicy Bypass -File skills/init-workspace/scripts/init-git-branch.ps1 `
  -Branch "<new-branch>" `
  -Base "<base-branch-or-ref>" `
  -StashApproved
```

If the helper returns `requiresStashApproval: true`, ask the user whether to
stash. Do not rerun with stash approval unless the user explicitly approves.

## Output JSON

Workspace helper output:

```json
{
  "ok": true,
  "featureFolder": ".features/my-feature",
  "featureWorkspace": ".features/my-feature",
  "artifactSubdir": "threat-model",
  "artifactWorkspace": ".features/my-feature/threat-model",
  "featureFolderExisted": true,
  "workspaceExisted": false,
  "createdFeatureFolder": false,
  "createdWorkspace": true,
  "statusPath": ".features/my-feature/status.json",
  "statusCreated": true,
  "matchedSimilarFeatureFolder": false,
  "ambiguous": false,
  "similarFeatureFolders": [],
  "dryRun": false
}
```

Branch helper output:

```json
{
  "ok": true,
  "requestedBranch": "feature/my-feature",
  "base": "main",
  "dirty": false,
  "requiresStashApproval": false,
  "stashCreated": false,
  "branchCreated": true,
  "checkedOut": true
}
```

Worktree helper output:

```json
{
  "ok": true,
  "error": "",
  "repoRoot": "C:/path/to/my-repo",
  "worktreePath": "C:/path/to/my-repo.worktrees/my-feature",
  "feature": "my-feature",
  "featureSlug": "my-feature",
  "branch": "my-feature",
  "base": "main",
  "branchCreated": true,
  "worktreeCreated": true,
  "worktreeExisted": false,
  "dryRun": false
}
```
