#!/usr/bin/env python3
"""Validate the lightweight SDLC documents.

Kept as a compatibility command for callers of the old helper. The workflow no
longer requires cross-document IDs; it checks that the living spec and task
files exist and reports unchecked task/acceptance items.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


def validate(feature_folder: Path) -> dict[str, Any]:
    feature_folder = feature_folder.resolve()
    files = {
        "spec": feature_folder / "SPEC.md",
        "tasks": feature_folder / "tasks" / "PLAN.md",
        "todo": feature_folder / "tasks" / "TODO.md",
    }
    issues: list[dict[str, str]] = []
    for name, path in files.items():
        if not path.exists():
            issues.append({"severity": "error", "code": "MISSING_FILE", "file": path.relative_to(feature_folder).as_posix(), "message": f"{name} document is missing."})

    unchecked: dict[str, int] = {}
    for name, path in files.items():
        if path.exists():
            count = sum(1 for line in path.read_text(encoding="utf-8").splitlines() if line.lstrip().startswith("- [ ]"))
            unchecked[name] = count

    return {
        "ok": not any(item["severity"] == "error" for item in issues),
        "featureFolder": feature_folder.as_posix(),
        "artifacts": {name: path.exists() for name, path in files.items()},
        "uncheckedTasks": unchecked,
        "issues": issues,
        "summary": {"errors": len(issues), "warnings": 0},
    }


def markdown_report(result: dict[str, Any]) -> str:
    lines = ["# SDLC Document Check", "", f"Result: {'PASS' if result['ok'] else 'FAIL'}", "", "## Unchecked items", ""]
    for name, count in result.get("uncheckedTasks", {}).items():
        lines.append(f"- **{name}:** {count}")
    if result["issues"]:
        lines += ["", "## Issues", ""]
        lines.extend(f"- **{item['file']}:** {item['message']}" for item in result["issues"])
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description="Check lightweight AI SDLC documents")
    parser.add_argument("feature_folder")
    parser.add_argument("--markdown")
    args = parser.parse_args()
    result = validate(Path(args.feature_folder))
    if args.markdown:
        Path(args.markdown).write_text(markdown_report(result), encoding="utf-8")
        result["markdownReport"] = args.markdown
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
