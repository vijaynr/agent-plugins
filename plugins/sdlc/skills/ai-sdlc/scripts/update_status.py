#!/usr/bin/env python3
"""Manage .features/<feature>/status.json for the AI SDLC workflow.

All commands print JSON so agents can parse results directly.
"""
from __future__ import annotations

import argparse
import errno
import json
import os
import sys
import tempfile
import time
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterator

PHASES = {
    "workspace": {"status": "done", "artifact": "."},
    "spec": {"status": "pending", "artifact": "SPEC.md"},
    "research": {"status": "optional", "artifact": "SPEC.md"},
    "design": {"status": "pending", "artifact": "SPEC.md|DESIGN.md"},
    "plan": {"status": "pending", "artifact": "tasks/PLAN.md"},
    "implement": {"status": "pending", "artifact": "tasks/TODO.md"},
    "review": {"status": "pending", "artifact": "tasks/TODO.md"},
    "refine": {"status": "optional", "artifact": "SPEC.md|tasks/PLAN.md"},
    "ship": {"status": "pending", "artifact": "merge-request"},
}

NEXT_PHASE = {
    "workspace": "spec",
    "spec": "design",
    "research": "design",
    "design": "plan",
    "plan": "implement",
    "implement": "review",
    "review": "ship",
    "refine": "plan",
    "ship": None,
}

ROOT_IN_PROGRESS_STATUSES = {"pending", "initialized", "in_progress", "blocked"}


def now_utc() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def json_out(payload: dict[str, Any], exit_code: int = 0) -> None:
    print(json.dumps(payload, indent=2, sort_keys=False))
    raise SystemExit(exit_code)


def feature_folder_from_arg(value: str) -> Path:
    p = Path(value)
    if p.name == "status.json":
        return p.parent
    return p


def status_path(feature_folder: Path) -> Path:
    return feature_folder / "status.json"


def default_status(feature_folder: Path) -> dict[str, Any]:
    ts = now_utc()
    feature_name = feature_folder.name
    data: dict[str, Any] = {
        "schemaVersion": 1,
        "feature": feature_name,
        "featureFolder": feature_folder.as_posix(),
        "currentPhase": "workspace",
        "status": "initialized",
        "createdAt": ts,
        "updatedAt": ts,
        "phases": {},
        "blockers": [],
        "nextRecommendedPhase": "spec",
        "artifactHashes": {},
        "git": {
            "lastVerifiedCommit": None,
            "latestSddCommits": [],
            "repoRoot": None,
            "worktreePath": None,
            "isWorktree": False,
        },
        "evidence": {
            "verification": {"status": "pending", "timestamp": None, "summary": None},
        },
        "drift": {
            "overall": "unknown",
            "lastCheckedAt": None,
            "nextRecommendedAction": None,
            "items": [],
            "summary": {"total": 0, "blocking": 0},
        },
        "history": [
            {
                "phase": "workspace",
                "status": "done",
                "timestamp": ts,
                "summary": "Feature workspace initialized.",
            }
        ],
    }
    for phase, value in PHASES.items():
        data["phases"][phase] = dict(value)
    data["phases"]["workspace"]["updatedAt"] = ts
    return data


def load_status(feature_folder: Path, create: bool = False) -> tuple[dict[str, Any], bool]:
    path = status_path(feature_folder)
    if not path.exists():
        if not create:
            json_out({"ok": False, "error": f"status.json not found: {path.as_posix()}"}, 1)
        feature_folder.mkdir(parents=True, exist_ok=True)
        data = default_status(feature_folder)
        save_status(feature_folder, data)
        return data, True
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:  # noqa: BLE001 - CLI should surface exact parse failure
        json_out({"ok": False, "error": f"failed to read {path.as_posix()}: {exc}"}, 1)
    changed = normalize_status(feature_folder, data)
    if changed:
        save_status(feature_folder, data)
    return data, False


def normalize_status(feature_folder: Path, data: dict[str, Any]) -> bool:
    changed = False
    if data.get("schemaVersion") != 1:
        data["schemaVersion"] = 1
        changed = True
    if not data.get("feature"):
        data["feature"] = feature_folder.name
        changed = True
    if data.get("featureFolder") != feature_folder.as_posix():
        data["featureFolder"] = feature_folder.as_posix()
        changed = True
    if "phases" not in data or not isinstance(data["phases"], dict):
        data["phases"] = {}
        changed = True
    # Migrate status files created before the /review rename.
    if "verify" in data["phases"] and "review" not in data["phases"]:
        data["phases"]["review"] = data["phases"].pop("verify")
        changed = True
    if data.get("currentPhase") == "verify":
        data["currentPhase"] = "review"
        changed = True
    if data.get("nextRecommendedPhase") == "verify":
        data["nextRecommendedPhase"] = "review"
        changed = True
    for phase, defaults in PHASES.items():
        if phase not in data["phases"] or not isinstance(data["phases"][phase], dict):
            data["phases"][phase] = dict(defaults)
            changed = True
        else:
            for key, value in defaults.items():
                if key not in data["phases"][phase]:
                    data["phases"][phase][key] = value
                    changed = True
    if "blockers" not in data or not isinstance(data["blockers"], list):
        data["blockers"] = []
        changed = True
    if "history" not in data or not isinstance(data["history"], list):
        data["history"] = []
        changed = True
    if "artifactHashes" not in data or not isinstance(data["artifactHashes"], dict):
        data["artifactHashes"] = {}
        changed = True
    if "git" not in data or not isinstance(data["git"], dict):
        data["git"] = {
            "lastVerifiedCommit": None,
            "latestSddCommits": [],
            "repoRoot": None,
            "worktreePath": None,
            "isWorktree": False,
        }
        changed = True
    else:
        for key, value in {
            "lastVerifiedCommit": None,
            "latestSddCommits": [],
            "repoRoot": None,
            "worktreePath": None,
            "isWorktree": False,
        }.items():
            if key not in data["git"]:
                data["git"][key] = value
                changed = True
    if "evidence" not in data or not isinstance(data["evidence"], dict):
        data["evidence"] = {
            "verification": {"status": "pending", "timestamp": None, "summary": None},
        }
        changed = True
    elif "verification" not in data["evidence"] or not isinstance(data["evidence"]["verification"], dict):
        data["evidence"]["verification"] = {"status": "pending", "timestamp": None, "summary": None}
        changed = True
    if "drift" not in data or not isinstance(data["drift"], dict):
        data["drift"] = {
            "overall": "unknown",
            "lastCheckedAt": None,
            "nextRecommendedAction": None,
            "items": [],
            "summary": {"total": 0, "blocking": 0},
        }
        changed = True
    else:
        drift_defaults: dict[str, Any] = {
            "overall": "unknown",
            "lastCheckedAt": None,
            "nextRecommendedAction": None,
            "items": [],
            "summary": {"total": 0, "blocking": 0},
        }
        for key, value in drift_defaults.items():
            if key not in data["drift"]:
                data["drift"][key] = value
                changed = True
    if not data.get("createdAt"):
        data["createdAt"] = now_utc()
        changed = True
    if not data.get("updatedAt"):
        data["updatedAt"] = now_utc()
        changed = True
    if not data.get("currentPhase"):
        data["currentPhase"] = infer_next_phase(data) or "workspace"
        changed = True
    elif data.get("currentPhase") == "validate":
        data["currentPhase"] = "review"
        changed = True
    if "nextRecommendedPhase" not in data:
        data["nextRecommendedPhase"] = infer_next_phase(data)
        changed = True
    elif data.get("nextRecommendedPhase") == "validate":
        data["nextRecommendedPhase"] = infer_next_phase(data)
        changed = True
    return changed


@contextmanager
def status_lock(feature_folder: Path, timeout: float = 10.0) -> Iterator[None]:
    """Lock status updates across processes on Windows and POSIX systems."""
    lock_path = feature_folder / ".status.lock"
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    with lock_path.open("a+b") as lock_file:
        if os.name == "nt":
            import msvcrt

            lock_file.seek(0, os.SEEK_END)
            if lock_file.tell() == 0:
                lock_file.write(b"\0")
                lock_file.flush()
        else:
            import fcntl

        deadline = time.monotonic() + timeout
        while True:
            try:
                if os.name == "nt":
                    lock_file.seek(0)
                    msvcrt.locking(lock_file.fileno(), msvcrt.LK_NBLCK, 1)
                else:
                    fcntl.flock(lock_file.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
                break
            except OSError as exc:
                if exc.errno not in {errno.EACCES, errno.EAGAIN, errno.EDEADLK}:
                    raise
                if time.monotonic() >= deadline:
                    raise TimeoutError(f"timed out waiting for status lock: {lock_path}") from exc
                time.sleep(0.05)
        try:
            yield
        finally:
            if os.name == "nt":
                lock_file.seek(0)
                msvcrt.locking(lock_file.fileno(), msvcrt.LK_UNLCK, 1)
            else:
                fcntl.flock(lock_file.fileno(), fcntl.LOCK_UN)


def save_status(feature_folder: Path, data: dict[str, Any]) -> None:
    path = status_path(feature_folder)
    path.parent.mkdir(parents=True, exist_ok=True)
    temp_path: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            newline="\n",
            dir=path.parent,
            prefix=f".{path.name}.",
            suffix=".tmp",
            delete=False,
        ) as temp_file:
            temp_path = Path(temp_file.name)
            temp_file.write(json.dumps(data, indent=2, ensure_ascii=False) + "\n")
            temp_file.flush()
            os.fsync(temp_file.fileno())
        # Native Windows sharing/access errors can outlive the advisory writer lock.
        # Keep the same closed, fsynced sibling file; never unlink the destination.
        for attempt in range(10):
            try:
                os.replace(temp_path, path)
                break
            except OSError as exc:
                if getattr(exc, "winerror", None) not in {5, 32, 33} or attempt == 9:
                    raise
                time.sleep(0.05)
    finally:
        if temp_path is not None:
            temp_path.unlink(missing_ok=True)


def append_history(data: dict[str, Any], phase: str, status: str, summary: str | None = None, extra: dict[str, Any] | None = None) -> None:
    entry: dict[str, Any] = {"phase": phase, "status": status, "timestamp": now_utc()}
    if summary:
        entry["summary"] = summary
    if extra:
        entry.update({k: v for k, v in extra.items() if v is not None})
    data.setdefault("history", []).append(entry)


def clear_phase_blockers(data: dict[str, Any], phase: str) -> None:
    data["blockers"] = [b for b in data.get("blockers", []) if not isinstance(b, dict) or b.get("phase") != phase]


def infer_next_phase(data: dict[str, Any]) -> str | None:
    phases = data.get("phases", {})
    order = ["spec", "research", "design", "plan", "implement", "review", "ship"]
    for phase in order:
        status = phases.get(phase, {}).get("status")
        if phase == "review" and status in {"done", "waived"}:
            continue
        if status not in {"done", "skipped", "waived", "optional"}:
            return phase
    return None


def apply_start(args: argparse.Namespace) -> None:
    feature_folder = feature_folder_from_arg(args.feature_folder)
    data, created = load_status(feature_folder, create=True)
    phase = args.phase
    ts = now_utc()
    data["currentPhase"] = phase
    data["status"] = "in_progress"
    data["updatedAt"] = ts
    data["phases"][phase]["status"] = "in_progress"
    data["phases"][phase]["updatedAt"] = ts
    if args.artifact:
        data["phases"][phase]["artifact"] = args.artifact
    if args.summary:
        data["phases"][phase]["summary"] = args.summary
    append_history(data, phase, "in_progress", args.summary)
    save_status(feature_folder, data)
    json_out({"ok": True, "created": created, "statusPath": status_path(feature_folder).as_posix(), "status": data})


def apply_complete(args: argparse.Namespace) -> None:
    feature_folder = feature_folder_from_arg(args.feature_folder)
    data, created = load_status(feature_folder, create=True)
    phase = args.phase
    ts = now_utc()
    data["currentPhase"] = phase
    data["updatedAt"] = ts
    data["phases"][phase]["status"] = "done"
    data["phases"][phase]["updatedAt"] = ts
    if args.artifact:
        data["phases"][phase]["artifact"] = args.artifact
    if args.summary:
        data["phases"][phase]["summary"] = args.summary
    clear_phase_blockers(data, phase)
    next_phase = args.next_phase if args.next_phase is not None else NEXT_PHASE.get(phase)
    data["nextRecommendedPhase"] = next_phase
    data["status"] = "complete" if phase == "ship" else "in_progress"
    append_history(data, phase, "done", args.summary, {"artifact": args.artifact, "nextRecommendedPhase": next_phase})
    save_status(feature_folder, data)
    json_out({"ok": True, "created": created, "statusPath": status_path(feature_folder).as_posix(), "status": data})


def apply_block(args: argparse.Namespace) -> None:
    feature_folder = feature_folder_from_arg(args.feature_folder)
    data, created = load_status(feature_folder, create=True)
    phase = args.phase
    ts = now_utc()
    data["currentPhase"] = phase
    data["status"] = "blocked"
    data["updatedAt"] = ts
    data["phases"][phase]["status"] = "blocked"
    data["phases"][phase]["updatedAt"] = ts
    if args.artifact:
        data["phases"][phase]["artifact"] = args.artifact
    blocker = {"phase": phase, "summary": args.summary, "timestamp": ts}
    if args.required_input:
        blocker["requiredInput"] = args.required_input
    clear_phase_blockers(data, phase)
    data.setdefault("blockers", []).append(blocker)
    data["nextRecommendedPhase"] = phase
    append_history(data, phase, "blocked", args.summary, {"requiredInput": args.required_input})
    save_status(feature_folder, data)
    json_out({"ok": True, "created": created, "statusPath": status_path(feature_folder).as_posix(), "status": data})


def apply_waive(args: argparse.Namespace) -> None:
    feature_folder = feature_folder_from_arg(args.feature_folder)
    data, created = load_status(feature_folder, create=True)
    phase = args.phase
    ts = now_utc()
    data["currentPhase"] = phase
    data["status"] = "in_progress"
    data["updatedAt"] = ts
    data["phases"][phase]["status"] = "waived"
    data["phases"][phase]["updatedAt"] = ts
    data["phases"][phase]["waiverReason"] = args.reason
    clear_phase_blockers(data, phase)
    next_phase = args.next_phase if args.next_phase is not None else NEXT_PHASE.get(phase)
    data["nextRecommendedPhase"] = next_phase
    append_history(data, phase, "waived", args.reason, {"nextRecommendedPhase": next_phase})
    save_status(feature_folder, data)
    json_out({"ok": True, "created": created, "statusPath": status_path(feature_folder).as_posix(), "status": data})


def apply_set_worktree(args: argparse.Namespace) -> None:
    feature_folder = feature_folder_from_arg(args.feature_folder)
    data, created = load_status(feature_folder, create=True)
    if "git" not in data or not isinstance(data["git"], dict):
        data["git"] = {}
    data["git"]["worktreePath"] = args.worktree_path
    if args.repo_root:
        data["git"]["repoRoot"] = args.repo_root
    data["git"]["isWorktree"] = True
    data["updatedAt"] = now_utc()
    save_status(feature_folder, data)
    json_out({"ok": True, "created": created, "statusPath": status_path(feature_folder).as_posix(), "git": data["git"]})


def apply_show(args: argparse.Namespace) -> None:
    feature_folder = feature_folder_from_arg(args.feature_folder)
    data, created = load_status(feature_folder, create=args.create)
    next_phase = infer_next_phase(data)
    summary = {
        "ok": True,
        "created": created,
        "statusPath": status_path(feature_folder).as_posix(),
        "feature": data.get("feature"),
        "featureFolder": data.get("featureFolder"),
        "currentPhase": data.get("currentPhase"),
        "status": data.get("status"),
        "nextRecommendedPhase": data.get("nextRecommendedPhase") or next_phase,
        "blockers": data.get("blockers", []),
        "phases": data.get("phases", {}),
        "drift": data.get("drift", {}),
    }
    if args.full:
        summary["raw"] = data
    json_out(summary)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Manage AI SDLC status.json")
    sub = parser.add_subparsers(dest="command", required=True)

    def add_common(p: argparse.ArgumentParser) -> None:
        p.add_argument("feature_folder", help=".features/<feature> folder or status.json path")

    p = sub.add_parser("show", help="Show status summary")
    add_common(p)
    p.add_argument("--create", action="store_true", help="Create status.json if missing")
    p.add_argument("--full", action="store_true", help="Include raw status document")
    p.set_defaults(func=apply_show)

    p = sub.add_parser("start-phase", help="Mark a phase in progress")
    add_common(p)
    p.add_argument("phase", choices=sorted(PHASES))
    p.add_argument("--artifact")
    p.add_argument("--summary")
    p.set_defaults(func=apply_start)

    p = sub.add_parser("complete-phase", help="Mark a phase done")
    add_common(p)
    p.add_argument("phase", choices=sorted(PHASES))
    p.add_argument("--artifact")
    p.add_argument("--summary")
    p.add_argument("--next-phase", default=None, help="Override nextRecommendedPhase; use empty string for none")
    p.set_defaults(func=apply_complete)

    p = sub.add_parser("block-phase", help="Mark a phase blocked")
    add_common(p)
    p.add_argument("phase", choices=sorted(PHASES))
    p.add_argument("--artifact")
    p.add_argument("--summary", required=True)
    p.add_argument("--required-input")
    p.set_defaults(func=apply_block)

    p = sub.add_parser("waive-phase", help="Mark a phase waived")
    add_common(p)
    p.add_argument("phase", choices=sorted(PHASES))
    p.add_argument("--reason", required=True)
    p.add_argument("--next-phase", default=None, help="Override nextRecommendedPhase; use empty string for none")
    p.set_defaults(func=apply_waive)

    p = sub.add_parser("set-worktree", help="Record worktree and repository paths in status.json")
    add_common(p)
    p.add_argument("--worktree-path", required=True, help="Path to worktree")
    p.add_argument("--repo-root", help="Path to main repository root")
    p.set_defaults(func=apply_set_worktree)

    return parser


def main(argv: list[str] | None = None) -> None:
    args = build_parser().parse_args(argv)
    if getattr(args, "next_phase", None) == "":
        args.next_phase = None
    feature_folder = feature_folder_from_arg(args.feature_folder)
    with status_lock(feature_folder):
        args.func(args)


if __name__ == "__main__":
    main()
