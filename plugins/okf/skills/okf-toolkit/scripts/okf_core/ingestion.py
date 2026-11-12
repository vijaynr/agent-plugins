from __future__ import annotations

import re
from pathlib import Path

from .writing import WriteResult, write_files


def _classify(text: str) -> tuple[str, str, str]:
    lower = text.lower()
    if any(word in lower for word in ("decided", "decision", "we will", "choose")):
        return "Architecture Decision", "decisions", "Decision"
    if any(word in lower for word in ("gotcha", "caveat", "watch out", "pitfall")):
        return "Gotcha", "gotchas", "Gotcha"
    if any(word in lower for word in ("design", "proposed", "should support")):
        return "Design", "designs", "Design"
    return "Conversation Record", "references", "Conversation"


def _slug(source_label: str, text: str) -> str:
    heading = next((line.lstrip("# ").strip() for line in text.splitlines() if line.startswith("#")), "")
    basis = heading or Path(source_label).stem or "conversation"
    value = re.sub(r"[^a-z0-9]+", "-", basis.lower()).strip("-")
    return value or "conversation"


def _existing_text(path: Path, fallback: str) -> str:
    return path.read_text(encoding="utf-8") if path.is_file() else fallback


def _fenced_content(text: str) -> str:
    fence_length = max((len(match) for match in re.findall(r"`+", text)), default=3) + 1
    fence = "`" * fence_length
    return f"{fence}text\n{text.strip()}\n{fence}"


def ingest_text(
    docs_root: Path,
    text: str,
    *,
    source_label: str,
    repo_root: Path | None = None,
) -> WriteResult:
    docs_root = docs_root.resolve()
    if repo_root is not None:
        repo_root = repo_root.resolve()
        if repo_root != docs_root and repo_root not in docs_root.parents:
            raise ValueError("docs root must be inside the repository root")
    if not text.strip():
        raise ValueError("input text must not be empty")
    concept_type, directory, display_type = _classify(text)
    slug = _slug(source_label, text)
    relative = f"{directory}/{slug}.md"
    description = " ".join(text.strip().split())[:160]
    concept = f"""---
type: {concept_type}
title: {display_type} — {slug.replace('-', ' ').title()}
description: {description}
tags: [ingested]
source: {source_label}
source_trust: untrusted
status: proposed
---

# Source Content

{_fenced_content(text)}

# Provenance

Source: `{source_label}`
"""

    root_index_path = docs_root / "index.md"
    root_index = _existing_text(root_index_path, "# Repository Knowledge Catalog\n")
    entry = f"* [{display_type} — {slug.replace('-', ' ').title()}]({relative}) - {description}\n"
    if relative not in root_index:
        root_index = root_index.rstrip() + "\n\n# Ingested concepts\n\n" + entry

    log_path = docs_root / "log.md"
    log = _existing_text(log_path, "# Directory Update Log\n")
    log = log.rstrip() + f"\n\n* **Ingestion**: Added [{relative}]({relative}) from `{source_label}`.\n"

    result = write_files(
        docs_root,
        {relative: concept, "index.md": root_index, "log.md": log},
        conflict_paths={relative},
    )
    existing_concept = docs_root / relative
    if existing_concept.exists():
        result.warnings.append(f"possible duplicate concept: {relative}")
    return result
