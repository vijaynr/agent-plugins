# Testing Guidelines

Keep existing tests that exercise scripts used by active plugins or skills. Tests can live at the repository root or beside their scripts. Do not add test files or cases as part of the current cleanup. Plugins without existing script tests do not need new tests for this task.

Static manifest, frontmatter, branding, agent-contract, documentation, CI, and test-harness self-tests are no longer part of the pytest suite. Tests for removed plugins are removed with their scripts. This deliberately reduces structural coverage; it does not prove that those contracts are unnecessary.

## Commands

Run from the repository root. Run plugin suites separately because independently installable plugins can use the same test module names.

```bash
./agents.sh validate
python -m pytest tests -q --strict-config --strict-markers
python -m pytest plugins/okf/tests -q
python -m pytest plugins/blackduck/skills/blackduck/tests -q
python -m pytest plugins/gitlab/skills/gitlab/tests -q
python -m pytest plugins/octane/skills/alm-octane/tests -q
python -m pytest plugins/sdlc/skills/ai-sdlc/scripts/test_update_status.py plugins/sdlc/skills/ai-sdlc/scripts/test_detect_drift.py -q
```

Use a Python environment with the declared dependencies installed. On Windows, a repository-local environment can use `.venv/Scripts/python.exe` in place of `python`. Dependency inputs and hash-pinned locks remain under `requirements/`. Do not install packages or contact external services as a side effect of a test run. No CI pipeline is bundled.

## Retained root suites

| File | Active script coverage |
|---|---|
| `test_credential_config_contract.py` | API plugin configuration, profile lifecycle, credential resolution, subprocess login, and failure handling. |
| `test_init_git_branch.py` | SDLC PowerShell branch helper in temporary Git repositories. |
| `test_init_git_worktree.py` | SDLC PowerShell worktree and workspace preparation helpers. |
| `test_init_git_worktree_shell.py` | SDLC Bash worktree helper. |
| `test_skill_cli_smoke.py` | Active skill CLI compilation, help, supported grammar, and dependency metadata. |
| `test_web_crawler.py` | Web crawler output using a loopback HTTP fixture. |

`tests/conftest.py` provides shared paths and command execution. Do not test these fixtures as standalone application functionality.

The root `agents.sh` helper remains available for manual workspace validation. It is not a plugin/skill script, so its dedicated pytest suite is not retained.

## Plugin suites

- **OKF:** initialization, validation, writing, export, ingestion, portability, and end-to-end script operations.
- **Black Duck, GitLab, Octane:** API payloads, reads, writes, profiles, credential isolation, and local error handling through fake HTTP/keyring boundaries.
- **SDLC:** drift detection and status persistence, including locking, atomic replacement, concurrent history, and bounded Windows retry behavior.

Instruction-only plugins have no script suite. Review their changed instructions, routes, links, and approval gates manually. Do not describe these reviews as executable security controls or live host validation.

## Credential isolation

Never read a real OS keyring or contact a real service. Inject fake `keyring`, `keyring.errors`, `requests`, and `dotenv` modules before importing API clients. Use temporary `HOME`/`USERPROFILE` and `AGENT_DEVELOPMENT_TOOLKIT_CONFIG_HOME` directories. Clear service credential variables. Keep fake state and HTTP logs in temporary files.

Credential tests cover generic platform paths, profile selection, rollback, locking, atomic-write failures, relocation, legacy `.env` discovery, endpoint provenance, and partial-override rejection. Secrets must not appear in stdout, stderr, stable JSON, profile files, or lock files. Local failures must produce no HTTP calls.

The storage rename is intentionally incompatible with earlier branded profile directories and keyring namespaces. Existing users must log in again. Tests use only `AgentDevelopmentToolkit:<service>` and generic config paths. Old user files and credentials must not be deleted by tests or runtime migration.

## SDLC status persistence

The existing status suite covers native Windows replacement errors 5/32/33, the ten-attempt/nine-wait bound, prior-byte preservation, temporary-file cleanup, immediate propagation of unrelated errors, and concurrent history preservation. Synthetic cases run across platforms. A separate Windows case exercises a controlled held reader.

Do not retry a failed gate until it happens to pass. Preserve the failure and investigate it. Do not infer that an unknown external process caused a failure.

## Platform limits

PowerShell/Git helper tests skip only when their required tools are unavailable. Use temporary repositories and local remotes, not the workspace's real repositories. Windows tests find Git Bash from the Git installation; set `GIT_BASH` when required. POSIX permission assertions do not run on Windows.

CLI smoke tests can use `uv` if available. If execution is unavailable, report the metadata fallback honestly. Passing local script tests does not prove native application rendering, live API compatibility, or Copilot host routing.

## Review checks

- Review both marketplace manifests and resolve their plugin source paths. The GitHub copy must use the `../../` prefix.
- Review changed router and skill links for removed components.
- Run `git diff --check` and inspect the scoped diff.
- Keep tests deterministic. Use fake service boundaries and synthetic fixtures.
- Do not commit credentials, local `.env` files, caches, reports, or machine-specific paths.
- Do not install/remove actual Copilot plugins in tests.
- Report failed, skipped, and unrun checks separately. Do not weaken or skip retained script tests to hide a regression.
