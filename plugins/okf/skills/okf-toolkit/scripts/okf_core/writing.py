from __future__ import annotations

import difflib
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class WriteResult:
    files: list[str] = field(default_factory=list)
    conflicts: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    diff: str = ""


def _safe_relative(path: str) -> Path:
    relative = Path(path)
    if relative.is_absolute() or ".." in relative.parts:
        raise ValueError(f"unsafe relative path: {path}")
    return relative


def _assert_safe_target(root: Path, relative: Path) -> None:
    current = root
    for component in relative.parent.parts:
        if component == ".":
            continue
        current /= component
        if current.is_symlink():
            raise ValueError(f"target path contains a symlink: {relative.as_posix()}")
    if (root / relative).is_symlink():
        raise ValueError(f"target path is a symlink: {relative.as_posix()}")


def _file_diff(relative: str, before: str, after: str) -> list[str]:
    return list(
        difflib.unified_diff(
            before.splitlines(keepends=True),
            after.splitlines(keepends=True),
            fromfile=f"a/docs/{relative}",
            tofile=f"b/docs/{relative}",
        )
    )


def write_files(
    target_root: Path,
    files: dict[str, str],
    *,
    conflict_paths: set[str] | None = None,
) -> WriteResult:
    target_root = target_root.resolve()
    conflict_paths = set(files) if conflict_paths is None else conflict_paths
    result = WriteResult()
    diff: list[str] = []

    for name, content in sorted(files.items()):
        relative = _safe_relative(name)
        _assert_safe_target(target_root, relative)
        target = target_root / relative
        result.files.append(relative.as_posix())
        if target.exists():
            if target.is_dir():
                raise ValueError(f"target path is a directory: {relative.as_posix()}")
            if relative.as_posix() in conflict_paths:
                result.conflicts.append(relative.as_posix())
            before = target.read_text(encoding="utf-8")
        else:
            before = ""
        diff.extend(_file_diff(relative.as_posix(), before, content))

    result.diff = "".join(diff)
    if result.conflicts:
        return result

    for name, content in sorted(files.items()):
        relative = _safe_relative(name)
        _assert_safe_target(target_root, relative)
        target = target_root / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")
        if target.read_text(encoding="utf-8") != content:
            raise IOError(f"verification failed after writing {relative.as_posix()}")
    return result
