# Commit, Submit, and Verify

## Approval boundary

A request to edit or build locally does not authorize OBS writes. Before each server action, show the API URL, exact action, source/target project and package, reviewed revision or diff, message, checks, and remaining risks. Obtain explicit user approval for that action. A bounded approval can cover named file additions/removals and a single source commit; it must not imply later submission or acceptance.

Use a scratch/development source project approved by the owner. Do not directly commit to release or maintenance targets in this workflow. Respect reviewer roles and internal release policy. Maintenance, signing, publishing, metadata changes, and Git/scmsync packages need separate internal procedures.

## Upload reviewed sources

From the verified package checkout, inspect status and diff again. Review and explicitly name any files to add or remove with the installed client's add/remove commands; never stage all unknown files blindly. Confirm the checkout has not changed since approval. If it changed, repeat review and approval.

The following message is illustrative; prepare the actual non-secret message before approval:

```bash
osc -A "$OBS_API_URL" status
osc -A "$OBS_API_URL" diff
osc -A "$OBS_API_URL" commit -m "Describe the approved package change" </dev/null
osc -A "$OBS_API_URL" log "$OBS_SOURCE_PROJECT" "$OBS_SOURCE_PACKAGE"
```

Record the returned source revision. Read remote history and changed source files to verify it matches the approved change. Use `osc cat` for individual files when needed; never dump confidential sources into reports. A clean local status alone does not prove a successful remote commit. If the response is uncertain, inspect remote history and source state before any retry.

For remote-only builds, this scratch commit precedes the build gate. Report the upload as an upload, not a completed package update. Do not submit until current remote builds and other required checks pass.

## Create a submit request

Confirm destination metadata and package identity on the same API URL. Inspect existing requests for the exact source/target pair to avoid duplicates. Review the source/target difference, checks, and request message. Obtain separate approval for the submission. Re-read the source revision immediately before submitting; if it differs from the approved, tested revision, stop. Never submit a moving unreviewed revision.

```bash
osc -A "$OBS_API_URL" meta pkg "$OBS_TARGET_PROJECT" "$OBS_TARGET_PACKAGE"
osc -A "$OBS_API_URL" rdiff "$OBS_TARGET_PROJECT" "$OBS_TARGET_PACKAGE" "$OBS_SOURCE_PROJECT" "$OBS_SOURCE_PACKAGE"
```

Set `OBS_SOURCE_REVISION` to the reviewed, tested remote source checksum/revision, never a moving value such as HEAD or latest. Check the installed client's help for `--revision` and `--no-update` before execution. The latter prevents client-configured cleanup or source updates on acceptance; for linked packages, review its effect on the link and ask for a separate policy decision if unsuitable. If these options are unsupported, stop. Do not rely on default acceptance side effects.

```bash
osc -A "$OBS_API_URL" submitrequest --revision "$OBS_SOURCE_REVISION" --no-update "$OBS_SOURCE_PROJECT" "$OBS_SOURCE_PACKAGE" "$OBS_TARGET_PROJECT" "$OBS_TARGET_PACKAGE" -m "Describe the reviewed package update" </dev/null
```

Read back the request's source-update policy as well as its revision; stop if cleanup or another unexpected side effect is present. Do not add cleanup, supersede, automatic acceptance, or force flags. Run server commands with stdin closed so a credential or replacement prompt fails instead of hanging. Do not answer interactive prompts with piped input. A prompt to replace an existing request requires a stop and a separate user decision, not a default answer.

## Read-back and monitoring

Capture the returned request ID as `OBS_REQUEST_ID`. Verify its API server, source and target project/package, pinned source revision, description, and state:

```bash
osc -A "$OBS_API_URL" request show "$OBS_REQUEST_ID"
osc -A "$OBS_API_URL" request log "$OBS_REQUEST_ID"
```

If the ID is missing or a timeout occurs, inspect requests on this server for the exact pair and revision. Never blindly repeat the write. A declined request or reviewer comment starts a new review/edit/build cycle. Changes, comments, replacements, and resubmissions need approval. Leave acceptance to the designated internal reviewers. Report the verified request ID and state; do not call a pending request accepted or published.
