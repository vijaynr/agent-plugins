#!/usr/bin/env python3
"""Portable command-line interface for repository OKF catalogs."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from okf_core.adapters.docx import extract_docx
from okf_core.adapters.pdf import extract_pdf
from okf_core.adapters.url import fetch_url
from okf_core.export import export_bundle
from okf_core.ingestion import ingest_text
from okf_core.initialization import initialize_bundle
from okf_core.validation import validate_bundle


def _add_docs_root(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--docs-root", type=Path, required=True, help="Path to the OKF bundle")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Create and consume repository OKF catalogs")
    subcommands = parser.add_subparsers(dest="command", required=True)

    init_parser = subcommands.add_parser("init", help="Initialize a repository OKF catalog")
    init_parser.add_argument("--repo-root", type=Path, required=True)
    _add_docs_root(init_parser)
    init_parser.set_defaults(handler=_run_init)

    ingest_parser = subcommands.add_parser("ingest", help="Ingest source content as OKF concepts")
    ingest_parser.add_argument("--repo-root", type=Path, default=Path.cwd())
    _add_docs_root(ingest_parser)
    source = ingest_parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--input", type=Path, help="Markdown, text, DOCX, or PDF source file")
    source.add_argument("--text-file", type=Path, help="Pasted conversation text file")
    source.add_argument("--conversation-file", type=Path, help="Current conversation saved as text")
    source.add_argument("--text", help="Explicit pasted conversation text")
    source.add_argument("--url", help="HTTPS URL to fetch as untrusted source content")
    ingest_parser.set_defaults(handler=_run_ingest)

    validate_parser = subcommands.add_parser("validate", help="Validate an OKF v0.1 bundle")
    _add_docs_root(validate_parser)
    validate_parser.add_argument("--format", choices=("json", "text"), default="text")
    validate_parser.set_defaults(handler=_run_validate)

    export_parser = subcommands.add_parser("export", help="Export an OKF bundle")
    _add_docs_root(export_parser)
    export_parser.add_argument("--format", choices=("json",), default="json")
    export_parser.set_defaults(handler=_run_export)
    return parser


def _read_source(args: argparse.Namespace) -> tuple[str, str]:
    if args.url:
        return fetch_url(args.url)
    if args.text is not None:
        return args.text, "conversation"

    source = args.input or args.text_file or args.conversation_file
    if source.suffix.lower() == ".docx":
        text = extract_docx(source)
    elif source.suffix.lower() == ".pdf":
        text = extract_pdf(source)
    else:
        text = source.read_text(encoding="utf-8")
    return text, source.as_posix()


def _run_init(args: argparse.Namespace) -> int:
    result = initialize_bundle(args.repo_root.resolve(), args.docs_root.resolve())
    print(json.dumps({
        "ok": not result.conflicts,
        "operation": "init",
        "files": result.files,
        "conflicts": result.conflicts,
        "diff": result.diff,
        "docs_root": args.docs_root.as_posix(),
    }, indent=2))
    return 0 if not result.conflicts else 2


def _run_ingest(args: argparse.Namespace) -> int:
    text, source_label = _read_source(args)
    result = ingest_text(
        args.docs_root.resolve(),
        text,
        source_label=source_label,
        repo_root=args.repo_root,
    )
    print(json.dumps({
        "ok": not result.conflicts,
        "operation": "ingest",
        "files": result.files,
        "conflicts": result.conflicts,
        "warnings": result.warnings,
        "diff": result.diff,
        "docs_root": args.docs_root.as_posix(),
    }, indent=2))
    return 0 if not result.conflicts else 2


def _run_validate(args: argparse.Namespace) -> int:
    result = validate_bundle(args.docs_root)
    payload = result.as_dict(args.docs_root)
    if args.format == "json":
        print(json.dumps(payload, indent=2))
    else:
        print(f"OKF validation: {'passed' if result.ok else 'failed'}")
        for error in result.errors:
            print(f"error: {error}")
        for warning in result.warnings:
            print(f"warning: {warning}")
    return 0 if result.ok else 1


def _run_export(args: argparse.Namespace) -> int:
    payload = export_bundle(args.docs_root.resolve())
    print(json.dumps(payload, indent=2))
    return 0 if payload["ok"] else 1


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    return args.handler(args)


if __name__ == "__main__":
    raise SystemExit(main())
