# Edit and Review an RPM Package

## Before editing

Inspect the existing spec, changes file, patches, `_service`, `_link`, and `_multibuild` when present. Compare the checked-out revision with server history. Look for existing updates or open requests before doing duplicate work. Preserve unrelated local edits. Confirm target distribution rules and supported products with the owner; public openSUSE policy is background guidance, not internal policy.

```bash
osc -A "$OBS_API_URL" status
osc -A "$OBS_API_URL" diff
osc -A "$OBS_API_URL" log "$OBS_SOURCE_PROJECT" "$OBS_SOURCE_PACKAGE"
```

## Spec and source changes

- Keep changes small. Preserve package naming, subpackage layout, macro style, and target-distribution conventions unless the task requires a change.
- Verify upstream source versions, origin, signatures/checksums, and licenses. Never fabricate a checksum, license identifier, CVE fix, or source URL. Do not send proprietary package details to public services without permission.
- Build shipped code from source. Flag bundled dependencies, prebuilt binaries, network access during build, and unexplained executable payloads for review. Follow documented internal exceptions only after approval.
- Review `BuildRequires`, runtime requirements, `%prep`, `%build`, `%install`, `%check`, `%files`, scriptlets, ownership, and permissions. Use distribution macros where supported. Do not assume a macro exists on every configured target.
- Rebase patches with provenance and purpose. Inspect patch application failures rather than ignoring them. Record added, removed, or upstreamed patches by filename.
- Source services execute host commands and may access external networks. Review `_service` and its tools, parameters, destinations, and outputs first. Run only a specifically approved service in an isolated environment. Do not run all services automatically.
- Keep tests enabled. Explain missing tools or unsupported tests; do not weaken checks merely to make a build green.

## Changes file

Follow the consuming project's changelog format. For SUSE-style `.changes`, prepend a dated entry with the real author identity and clear user impact. Preserve historical entries. Include the version change, significant behavior changes, patch changes, and verified security references. Do not claim that a release fixes a CVE without code or authoritative advisory evidence. If internal vulnerability review is required, use the approved internal tracker, not an assumed public Bugzilla endpoint.

Inspect the complete diff for accidental source, generated-file, permission, or changelog changes. Run `spec-cleaner`, validators, and policy tools only when available, applicable, and approved for this target. If a required check cannot run, report it as a blocker rather than claiming success.

## Review gate

Before a remote commit or submission, review the exact diff for correctness, source/license provenance, patches, changelog accuracy, required tests, all required architectures/flavors, lint findings, and absence of secrets. Use an independent reviewer when the host supports one. Otherwise run this checklist inline and disclose that no independent review occurred. Resolve blockers before submission.

Do not execute scriptlets, sources, patches, or source services on the agent host as a way to review them. Use static inspection first and approved isolated execution when needed.
