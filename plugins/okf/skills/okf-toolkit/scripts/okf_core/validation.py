from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path, PurePosixPath

from .parser import Document, parse_document

_LINK_RE = re.compile(r"\[[^\]]+\]\(([^)]+)\)")
_RESERVED = {"index.md", "log.md"}


@dataclass
class ValidationResult:
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    concepts: int = 0

    @property
    def ok(self) -> bool:
        return not self.errors

    def as_dict(self, docs_root: Path) -> dict[str, object]:
        return {
            "ok": self.ok,
            "operation": "validate",
            "docs_root": docs_root.as_posix(),
            "concepts": self.concepts,
            "errors": self.errors,
            "warnings": self.warnings,
        }


def _target_from_link(root: Path, source: Path, target: str) -> Path | None:
    target = target.split("#", 1)[0].split("?", 1)[0]
    if not target or target.startswith(("http://", "https://", "mailto:")):
        return None
    root = root.resolve()
    candidate = (root / target.lstrip("/")) if target.startswith("/") else source.parent / target
    candidate = candidate.resolve()
    if candidate != root and root not in candidate.parents:
        raise ValueError(f"link escapes bundle: {target}")
    return candidate


def _validate_links(root: Path, source: Path, body: str, result: ValidationResult) -> None:
    for target in _LINK_RE.findall(body):
        try:
            path = _target_from_link(root, source, target)
        except ValueError as exc:
            result.warnings.append(f"{source.relative_to(root).as_posix()}: {exc}")
            continue
        if path is not None and not path.exists():
            result.warnings.append(f"{source.relative_to(root).as_posix()}: broken link {target}")


def validate_bundle(docs_root: Path) -> ValidationResult:
    result = ValidationResult()
    if not docs_root.exists():
        result.errors.append(f"docs root does not exist: {docs_root}")
        return result
    if not docs_root.is_dir():
        result.errors.append(f"docs root is not a directory: {docs_root}")
        return result

    for path in sorted(docs_root.rglob("*.md")):
        relative = path.relative_to(docs_root)
        try:
            document: Document = parse_document(PurePosixPath(relative.as_posix()), path.read_text(encoding="utf-8"))
        except (OSError, UnicodeError, ValueError) as exc:
            result.errors.append(f"{relative.as_posix()}: {exc}")
            continue

        if path.name in _RESERVED:
            if path.name == "log.md" and document.has_frontmatter:
                result.errors.append(f"{relative.as_posix()}: log.md must not have frontmatter")
            _validate_links(docs_root, path, document.body, result)
            continue

        result.concepts += 1
        if not document.has_frontmatter:
            result.errors.append(f"{relative.as_posix()}: concept is missing frontmatter")
        elif not str(document.frontmatter.get("type", "")).strip():
            result.errors.append(f"{relative.as_posix()}: frontmatter requires non-empty type")
        _validate_links(docs_root, path, document.body, result)
    return result
