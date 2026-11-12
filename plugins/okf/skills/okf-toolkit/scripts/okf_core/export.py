from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from .parser import parse_document

_LINK_RE = re.compile(r"\[[^\]]+\]\(([^)]+)\)")


def export_bundle(docs_root: Path) -> dict[str, Any]:
    concepts: list[dict[str, Any]] = []
    warnings: list[str] = []
    for path in sorted(docs_root.rglob("*.md")):
        if path.name in {"index.md", "log.md"}:
            continue
        relative = path.relative_to(docs_root).as_posix()
        try:
            document = parse_document(path.relative_to(docs_root), path.read_text(encoding="utf-8"))
        except (OSError, UnicodeError, ValueError) as exc:
            warnings.append(f"{relative}: {exc}")
            continue
        if not document.has_frontmatter or not str(document.frontmatter.get("type", "")).strip():
            warnings.append(f"{relative}: omitted because required type metadata is missing")
            continue
        links = _LINK_RE.findall(document.body)
        source_dir = path.parent.resolve()
        bundle_root = docs_root.resolve()
        for link in links:
            target = link.split("#", 1)[0].split("?", 1)[0]
            if not target or target.startswith(("http://", "https://", "mailto:")):
                continue
            candidate = (bundle_root / target.lstrip("/")) if target.startswith("/") else source_dir / target
            candidate = candidate.resolve()
            if candidate != bundle_root and bundle_root not in candidate.parents:
                warnings.append(f"{relative}: link escapes bundle {link}")
            elif not candidate.exists():
                warnings.append(f"{relative}: broken link {link}")
        concepts.append({
            "id": relative.removesuffix(".md"),
            "path": relative,
            "metadata": document.frontmatter,
            "links": links,
            "body": document.body,
        })
    return {"ok": not warnings, "format": "okf-export-v1", "concepts": concepts, "warnings": warnings}
