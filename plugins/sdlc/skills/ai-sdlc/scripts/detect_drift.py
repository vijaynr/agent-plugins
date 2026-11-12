#!/usr/bin/env python3
"""Detect drift across AI SDLC feature artifacts, git state, and verification evidence.

This script is intentionally conservative: it reports drift and recommended routes,
but only updates status.json when --update-status is explicitly supplied.
"""
from __future__ import annotations

import argparse
import fnmatch
import hashlib
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ARTIFACTS = {
    "spec": "SPEC.md",
    "design": "DESIGN.md",
    "tasks": "tasks/PLAN.md",
    "todo": "tasks/TODO.md",
}

# These are living documents. A later phase may intentionally update the same
# document, so drift is about missing files and review freshness, not mtimes.
DEPENDENCIES: dict[str, list[str]] = {}
STALE_ROUTE: dict[str, str] = {}

ROUTE_ORDER = ["spec", "research", "design", "plan", "build", "review", "ship"]


def now_utc() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def sha256_file(path: Path) -> str | None:
    if not path.exists() or not path.is_file():
        return None
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def run_git(args: list[str], cwd: Path) -> tuple[int, str, str]:
    proc = subprocess.run(["git", *args], cwd=cwd, text=True, capture_output=True, check=False)
    return proc.returncode, proc.stdout.rstrip("\n"), proc.stderr.rstrip("\n")


def git_root(start: Path) -> Path | None:
    cwd = start if start.exists() else next((parent for parent in [start, *start.parents] if parent.exists()), Path.cwd())
    code, out, _ = run_git(["rev-parse", "--show-toplevel"], cwd)
    return Path(out) if code == 0 and out else None


def current_head(root: Path) -> str | None:
    code, out, _ = run_git(["rev-parse", "HEAD"], root)
    return out if code == 0 and out else None


def changed_files(root: Path) -> list[str]:
    code, out, _ = run_git(["status", "--porcelain=v1", "--untracked-files=all"], root)
    if code != 0 or not out:
        return []
    files: list[str] = []
    for line in out.splitlines():
        # Porcelain v1: XY path, or XY old -> new. Keep the destination path.
        path = line[3:].strip()
        if " -> " in path:
            path = path.split(" -> ", 1)[1]
        if path:
            files.append(path.replace("\\", "/"))
    return files


def committed_changed_files(root: Path, base_commit: str | None) -> list[str]:
    if not base_commit:
        return []
    code, out, _ = run_git(["diff", "--name-only", f"{base_commit}..HEAD"], root)
    if code != 0 or not out:
        return []
    return [line.strip().replace("\\", "/") for line in out.splitlines() if line.strip()]


def read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}


def drift_item(
    item_id: str,
    drift_type: str,
    severity: str,
    summary: str,
    route: str,
    *,
    artifact: str | None = None,
    blocking: bool = False,
    details: dict[str, Any] | None = None,
) -> dict[str, Any]:
    item: dict[str, Any] = {
        "id": item_id,
        "type": drift_type,
        "severity": severity,
        "summary": summary,
        "route": route,
        "blocking": blocking,
    }
    if artifact:
        item["artifact"] = artifact
    if details:
        item["details"] = details
    return item


def artifact_freshness_items(feature_folder: Path, start_index: int) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    n = start_index
    required_routes = {"SPEC.md": "spec", "tasks/PLAN.md": "plan", "tasks/TODO.md": "build"}
    for artifact, route in required_routes.items():
        if not (feature_folder / artifact).exists():
            n += 1
            items.append(drift_item(f"DRIFT-{n:03d}", "missing-artifact", "medium", f"{artifact} is missing.", route, artifact=artifact, blocking=False))

    spec_path = feature_folder / "SPEC.md"
    design_path = feature_folder / "DESIGN.md"
    if spec_path.exists() and "DESIGN.md" in spec_path.read_text(encoding="utf-8") and not design_path.exists():
        n += 1
        items.append(
            drift_item(
                f"DRIFT-{n:03d}",
                "missing-artifact",
                "medium",
                "DESIGN.md is referenced by SPEC.md but is missing.",
                "design",
                artifact="DESIGN.md",
                blocking=False,
            )
        )
    for artifact, deps in DEPENDENCIES.items():
        artifact_path = feature_folder / artifact
        if not artifact_path.exists():
            continue
        stale_deps = []
        artifact_mtime = artifact_path.stat().st_mtime
        for dep in deps:
            dep_path = feature_folder / dep
            if dep_path.exists() and dep_path.stat().st_mtime > artifact_mtime:
                stale_deps.append(dep)
        if stale_deps:
            n += 1
            route = STALE_ROUTE[artifact]
            items.append(
                drift_item(
                    f"DRIFT-{n:03d}",
                    "artifact-drift",
                    "medium",
                    f"{artifact} is older than upstream artifact(s): {', '.join(stale_deps)}.",
                    route,
                    artifact=artifact,
                    blocking=route in {"research", "design", "plan"},
                    details={"staleDependencies": stale_deps},
                )
            )
    return items


def load_traceability_module() -> Any | None:
    try:
        import importlib.util

        path = Path(__file__).with_name("validate_traceability.py")
        spec = importlib.util.spec_from_file_location("validate_traceability", path)
        if spec is None or spec.loader is None:
            return None
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module
    except Exception:
        return None


def traceability_items(feature_folder: Path, start_index: int) -> list[dict[str, Any]]:
    # Stable cross-document IDs are intentionally not part of the lightweight
    # workflow. Keep this hook for callers that still expect it.
    return []


def parse_expected_scope(plan_path: Path) -> list[str]:
    if not plan_path.exists():
        return []
    lines = plan_path.read_text(encoding="utf-8").splitlines()
    scope: list[str] = []
    in_section = False
    for line in lines:
        stripped = line.strip()
        if stripped.startswith("## "):
            in_section = stripped.lower() == "## expected file scope"
            continue
        if not in_section:
            continue
        if stripped.startswith("#"):
            break
        if not stripped or stripped.startswith("<!--"):
            continue
        if stripped.startswith("-"):
            value = stripped[1:].strip().strip("`")
            if value and "Add expected" not in value:
                scope.append(value.replace("\\", "/"))
    return scope


def matches_scope(path: str, patterns: list[str]) -> bool:
    if not patterns:
        return True
    normalized = path.replace("\\", "/")
    for pattern in patterns:
        p = pattern.strip().strip("`").replace("\\", "/")
        if not p:
            continue
        if p.endswith("/**") and normalized.startswith(p[:-3].rstrip("/") + "/"):
            return True
        if fnmatch.fnmatch(normalized, p):
            return True
        if normalized == p or normalized.startswith(p.rstrip("/") + "/"):
            return True
    return False


def git_items(feature_folder: Path, status: dict[str, Any], start_index: int) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    root = git_root(feature_folder)
    if root is None:
        return [], {"available": False}
    items: list[dict[str, Any]] = []
    n = start_index
    head = current_head(root)
    last_verified = status.get("git", {}).get("lastVerifiedCommit")
    dirty = changed_files(root)
    committed_since_verify = committed_changed_files(root, last_verified)

    if last_verified and head and head != last_verified:
        n += 1
        items.append(
            drift_item(
                f"DRIFT-{n:03d}",
                "evidence-drift",
                "high",
                "Current HEAD differs from the last reviewed commit.",
                "review",
                artifact="tasks/TODO.md",
                blocking=True,
                details={"lastVerifiedCommit": last_verified, "head": head, "changedFiles": committed_since_verify[:50]},
            )
        )

    if dirty:
        n += 1
        items.append(
            drift_item(
                f"DRIFT-{n:03d}",
                "working-tree-drift",
                "medium",
                f"Working tree has {len(dirty)} uncommitted changed file(s).",
                "status",
                blocking=False,
                details={"changedFiles": dirty[:50]},
            )
        )

    scope = parse_expected_scope(feature_folder / "tasks" / "PLAN.md")
    changed = sorted(set(dirty + committed_since_verify))
    outside = [path for path in changed if not matches_scope(path, scope) and not path.startswith(feature_folder.as_posix().strip("./") + "/")]
    # Feature artifacts themselves are allowed to change even when not listed in Expected File Scope.
    outside = [path for path in outside if not path.startswith(".features/")]
    if scope and outside:
        n += 1
        items.append(
            drift_item(
                f"DRIFT-{n:03d}",
                "scope-drift",
                "high",
                f"{len(outside)} changed file(s) are outside the expected file scope.",
                "refine",
                artifact="tasks/PLAN.md",
                blocking=True,
                details={"expectedScope": scope, "outsideScopeFiles": outside[:50]},
            )
        )

    return items, {
        "available": True,
        "root": root.as_posix(),
        "head": head,
        "lastVerifiedCommit": last_verified,
        "dirtyFiles": dirty,
        "committedFilesSinceVerification": committed_since_verify,
    }


def overall_status(items: list[dict[str, Any]]) -> str:
    if any(item["type"] in {"scope-drift", "intent-drift", "design-drift"} and item["severity"] in {"high", "critical"} for item in items):
        return "red"
    if any(item["severity"] == "critical" for item in items):
        return "red"
    if items:
        return "yellow"
    return "green"


def recommended_route(items: list[dict[str, Any]]) -> str | None:
    routes = [item.get("route") for item in items if item.get("route") and item.get("route") != "status"]
    if not routes:
        return None
    for route in ROUTE_ORDER:
        if route in routes:
            return route
    if "refine" in routes:
        return "refine"
    return routes[0]


def detect(feature_folder: Path) -> dict[str, Any]:
    feature_folder = feature_folder.resolve()
    status = read_json(feature_folder / "status.json")
    items: list[dict[str, Any]] = []
    items.extend(artifact_freshness_items(feature_folder, len(items)))
    items.extend(traceability_items(feature_folder, len(items)))
    git_drift, git_info = git_items(feature_folder, status, len(items))
    items.extend(git_drift)

    artifact_hashes = {rel: sha256_file(feature_folder / rel) for rel in ARTIFACTS.values()}
    route = recommended_route(items)
    overall = overall_status(items)
    return {
        "ok": overall == "green",
        "featureFolder": feature_folder.as_posix(),
        "checkedAt": now_utc(),
        "overall": overall,
        "nextRecommendedPhase": route,
        "items": items,
        "summary": {
            "total": len(items),
            "blocking": sum(1 for item in items if item.get("blocking")),
            "bySeverity": {severity: sum(1 for item in items if item.get("severity") == severity) for severity in ["critical", "high", "medium", "low"]},
        },
        "artifacts": artifact_hashes,
        "git": git_info,
    }


def update_status(feature_folder: Path, result: dict[str, Any]) -> None:
    path = feature_folder / "status.json"
    status = read_json(path)
    if not status:
        try:
            import importlib.util

            helper_path = Path(__file__).with_name("update_status.py")
            spec = importlib.util.spec_from_file_location("update_status", helper_path)
            if spec is None or spec.loader is None:
                raise RuntimeError("unable to load update_status.py")
            helper = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(helper)
            status = helper.default_status(feature_folder)
        except Exception:
            status = {"schemaVersion": 1, "feature": feature_folder.name, "featureFolder": feature_folder.as_posix()}
    status["updatedAt"] = now_utc()
    status["drift"] = {
        "overall": result["overall"],
        "lastCheckedAt": result["checkedAt"],
        "nextRecommendedAction": result.get("nextRecommendedPhase"),
        "items": result.get("items", []),
        "summary": result.get("summary", {}),
    }
    if result.get("nextRecommendedPhase"):
        status["nextRecommendedPhase"] = result["nextRecommendedPhase"]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(status, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Detect AI SDLC artifact, traceability, scope, and evidence drift")
    parser.add_argument("feature_folder", help="Path to .features/<feature>")
    parser.add_argument("--update-status", action="store_true", help="Write the drift summary into status.json")
    args = parser.parse_args(argv)

    feature_folder = Path(args.feature_folder)
    result = detect(feature_folder)
    if args.update_status:
        update_status(feature_folder, result)
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0 if result["overall"] != "red" else 2


if __name__ == "__main__":
    sys.exit(main())
