from __future__ import annotations

from pathlib import Path

from .writing import WriteResult, write_files

_IGNORED_DIRS = {".git", ".venv", "node_modules", "__pycache__", "docs"}


def _top_level_evidence(repo_root: Path) -> tuple[list[str], list[str]]:
    entries = sorted(path.name for path in repo_root.iterdir() if path.name not in _IGNORED_DIRS)
    files = [name for name in entries if (repo_root / name).is_file()]
    directories = [name for name in entries if (repo_root / name).is_dir()]
    return files, directories


def _manifest_names(files: list[str]) -> list[str]:
    return [name for name in files if name in {"pyproject.toml", "package.json", "pom.xml", "build.gradle", "Cargo.toml", "go.mod"}]


def _index() -> str:
    return """---\nokf_version: 0.1\ntype: Knowledge Bundle
title: Repository Knowledge Catalog\ndescription: Agent-readable architecture, decisions, gotchas, designs, and references for this repository.\n---\n\n# Repository Knowledge Catalog\n\n## Architecture\n\n* [System architecture](architecture/system.md) - Initial repository structure and entry-point evidence.\n\n## Decisions\n\n* [Initial conventions](decisions/initial-conventions.md) - Conventions observed during catalog initialization.\n\n## Gotchas\n\n* [Repository workflow](gotchas/repository-workflow.md) - Initial workflow risks and verification guidance.\n"""


def _log() -> str:
    return "# Directory Update Log\n\n## Initialization\n* **Initialization**: Proposed the initial repository OKF knowledge catalog.\n"


def initialize_bundle(repo_root: Path, docs_root: Path) -> WriteResult:
    repo_root = repo_root.resolve()
    docs_root = docs_root.resolve()
    if repo_root != docs_root and repo_root not in docs_root.parents:
        raise ValueError("docs root must be inside the repository root")
    if not repo_root.is_dir():
        raise ValueError(f"repository root is not a directory: {repo_root}")
    files, directories = _top_level_evidence(repo_root)
    manifests = _manifest_names(files)
    directory_text = ", ".join(f"`{name}/`" for name in directories) or "No top-level source directories detected."
    manifest_text = ", ".join(f"`{name}`" for name in manifests) or "No recognized build manifest detected."
    architecture = f"""---
type: Architecture
title: Repository system architecture
description: Initial architecture orientation derived from repository structure and build manifests.
tags: [architecture, generated]
resource: .
---

# Pattern & stack

This initial orientation is generated from repository evidence and should be reviewed before being treated as authoritative.

# Repository evidence

- Build manifests: {manifest_text}
- Top-level directories: {directory_text}
- Repository root: `{repo_root.name}/`

# Entry points

Inspect the build manifests and top-level source directories above to identify runtime entry points. This concept intentionally records evidence rather than guessing an entry point.

# Citations

- [Repository root](../../README.md)
"""
    decisions = """---
type: Architecture Decision
title: Initial repository documentation conventions
description: The OKF catalog is stored as Markdown concepts under docs/ and changes are reviewed as diffs.
tags: [documentation, conventions, generated]
status: proposed
---

# Context

Repository knowledge needs to be portable, diffable, and consumable by agents.

# Decision

Use an OKF v0.1 bundle under `docs/`, with `index.md` and `log.md` as reserved structural files and frontmatter on ordinary concept files.

# Consequences

- Knowledge remains version-controlled beside the code.
- Generated changes must be reviewed before application.
- Claims should retain repository evidence and provenance.

# Citations

- [OKF specification](https://github.com/GoogleCloudPlatform/knowledge-catalog/blob/main/okf/SPEC.md)
"""
    gotchas = """---
type: Gotcha
title: Repository documentation workflow
description: Generated OKF content is a proposal and must be validated and reviewed before applying it.
tags: [workflow, generated]
---

# Risk

Generated architecture and gotcha descriptions can become stale or encode assumptions that are not supported by executable evidence.

# Guidance

Validate the bundle, inspect evidence links, and compare consequential claims with current code, tests, and configuration before relying on them.

# Verification

Run the repository's test and build commands after changes that affect documented behavior.
"""
    proposal = {
        "index.md": _index(),
        "log.md": _log(),
        "architecture/system.md": architecture,
        "decisions/initial-conventions.md": decisions,
        "gotchas/repository-workflow.md": gotchas,
    }
    return write_files(docs_root, proposal)
