#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = []
# ///
"""Capture bounded same-origin HTML pages as local Markdown."""

from __future__ import annotations

import argparse
import ipaddress
import json
import re
import socket
import sys
from collections import deque
from html.parser import HTMLParser
from pathlib import Path
from typing import Iterable
from urllib.error import URLError
from urllib.parse import urljoin, urlsplit, urlunsplit
from urllib.request import Request, urlopen

BLOCK_TAGS = {"p", "div", "section", "article", "main", "li", "tr", "br"}
HEADING_TAGS = {"h1", "h2", "h3", "h4", "h5", "h6"}
SKIP_TAGS = {"script", "style", "svg", "noscript", "nav", "footer", "header"}
MAX_RESPONSE_BYTES = 5 * 1024 * 1024


def canonical_url(url: str) -> str:
    """Remove fragments and normalize a URL without changing its query."""
    parts = urlsplit(url)
    return urlunsplit((parts.scheme.lower(), parts.netloc.lower(), parts.path or "/", parts.query, ""))


def page_filename(url: str, used: set[str]) -> str:
    """Return a deterministic, collision-free Markdown filename for a URL."""
    path = urlsplit(url).path.rstrip("/") or "/"
    stem = "index" if path == "/" else Path(path).stem or "index"
    stem = re.sub(r"[^a-zA-Z0-9._-]+", "-", stem).strip(".-") or "page"
    candidate = f"{stem}.md"
    suffix = 2
    while candidate.casefold() in used:
        candidate = f"{stem}-{suffix}.md"
        suffix += 1
    used.add(candidate.casefold())
    return candidate


class PageParser(HTMLParser):
    """Extract readable text and links from a HTML document using stdlib only."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.title = ""
        self._title_depth = 0
        self._skip_depth = 0
        self._tag_stack: list[str] = []
        self._current_heading: str | None = None
        self._text: list[str] = []
        self._lines: list[str] = []
        self.links: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        tag = tag.lower()
        self._tag_stack.append(tag)
        attributes = dict(attrs)
        if tag in SKIP_TAGS:
            self._skip_depth += 1
        if tag == "title":
            self._title_depth += 1
        if tag == "a" and attributes.get("href"):
            self.links.append(attributes["href"] or "")
        if self._skip_depth:
            return
        if tag in HEADING_TAGS:
            self._flush_text()
            self._current_heading = tag
        elif tag in BLOCK_TAGS:
            self._flush_text()

    def handle_endtag(self, tag: str) -> None:
        tag = tag.lower()
        if self._skip_depth == 0 and (tag in HEADING_TAGS or tag in BLOCK_TAGS):
            self._flush_text()
        if tag == "title" and self._title_depth:
            self._title_depth -= 1
        if tag in SKIP_TAGS and self._skip_depth:
            self._skip_depth -= 1
        if self._tag_stack:
            self._tag_stack.pop()

    def handle_data(self, data: str) -> None:
        value = re.sub(r"\s+", " ", data).strip()
        if not value:
            return
        if self._title_depth:
            self.title = f"{self.title} {value}".strip()
        if not self._skip_depth:
            self._text.append(value)

    def _flush_text(self) -> None:
        if not self._text:
            return
        value = re.sub(r"\s+", " ", " ".join(self._text)).strip()
        self._text.clear()
        if not value:
            return
        if self._current_heading:
            level = int(self._current_heading[1])
            self._lines.append(f"{'#' * level} {value}")
            self._current_heading = None
        else:
            self._lines.append(value)

    @property
    def markdown_lines(self) -> list[str]:
        self._flush_text()
        return self._lines


def parse_page(html: str, url: str) -> tuple[str, list[str], list[str]]:
    parser = PageParser()
    parser.feed(html)
    lines = parser.markdown_lines
    title = next((line[2:] for line in lines if line.startswith("# ")), parser.title or url)
    if not any(line.startswith("# ") for line in lines):
        lines.insert(0, f"# {title}")
    return title, lines, parser.links


def is_allowed(url: str, origin: tuple[str, str], prefixes: Iterable[str]) -> bool:
    parts = urlsplit(url)
    if (parts.scheme.lower(), parts.netloc.lower()) != origin:
        return False
    return any(parts.path.startswith(prefix) for prefix in prefixes)


def assert_public_host(url: str, allow_private_hosts: bool) -> None:
    if allow_private_hosts:
        return
    hostname = urlsplit(url).hostname
    if not hostname:
        raise ValueError("URL must include a hostname")
    try:
        addresses = {entry[4][0] for entry in socket.getaddrinfo(hostname, None)}
    except socket.gaierror as exc:
        raise ValueError(f"Unable to resolve host: {hostname}") from exc
    if any(not ipaddress.ip_address(address).is_global for address in addresses):
        raise ValueError("Refusing a private, loopback, link-local, or reserved host; use --allow-private-hosts only with explicit approval")


def fetch(url: str, origin: tuple[str, str], allow_private_hosts: bool) -> str:
    assert_public_host(url, allow_private_hosts)
    request = Request(url, headers={"User-Agent": "Agent-Development-Toolkit-Web-Crawler/1.0"})
    with urlopen(request, timeout=30) as response:
        final_url = canonical_url(response.geturl())
        final_parts = urlsplit(final_url)
        if (final_parts.scheme.lower(), final_parts.netloc.lower()) != origin:
            raise ValueError("Refusing a redirect outside the start URL's origin")
        assert_public_host(final_url, allow_private_hosts)
        content_type = response.headers.get_content_type()
        if content_type not in {"text/html", "application/xhtml+xml"}:
            raise ValueError(f"Unsupported content type: {content_type}")
        data = response.read(MAX_RESPONSE_BYTES + 1)
        if len(data) > MAX_RESPONSE_BYTES:
            raise ValueError(f"Response exceeds {MAX_RESPONSE_BYTES} byte limit")
        charset = response.headers.get_content_charset() or "utf-8"
        return data.decode(charset, errors="replace")


def crawl(start_url: str, output: Path, max_pages: int, prefixes: list[str], allow_private_hosts: bool) -> dict[str, object]:
    start_url = canonical_url(start_url)
    start_parts = urlsplit(start_url)
    if start_parts.scheme not in {"http", "https"} or not start_parts.netloc:
        raise ValueError("URL must be an absolute http(s) URL")
    if max_pages < 1:
        raise ValueError("--max-pages must be at least 1")

    origin = (start_parts.scheme.lower(), start_parts.netloc.lower())
    allowed_prefixes = prefixes or [str(Path(start_parts.path).parent).replace("\\", "/")]
    allowed_prefixes = [prefix if prefix.startswith("/") else f"/{prefix}" for prefix in allowed_prefixes]
    if not any(start_parts.path.startswith(prefix) for prefix in allowed_prefixes):
        allowed_prefixes.append(start_parts.path or "/")

    output.mkdir(parents=True, exist_ok=True)
    queue = deque([start_url])
    seen: set[str] = set()
    used_names: set[str] = set()
    pages: list[tuple[str, str, str]] = []
    warnings: list[str] = []

    while queue and len(pages) < max_pages:
        url = queue.popleft()
        if url in seen:
            continue
        seen.add(url)
        try:
            title, lines, hrefs = parse_page(fetch(url, origin, allow_private_hosts), url)
        except (URLError, OSError, ValueError) as exc:
            warnings.append(f"{url}: {exc}")
            continue
        filename = page_filename(url, used_names)
        content = "\n\n".join(line for line in lines if line).rstrip() + "\n"
        (output / filename).write_text(content, encoding="utf-8")
        pages.append((title, filename, url))
        for href in hrefs:
            candidate = canonical_url(urljoin(url, href))
            if is_allowed(candidate, origin, allowed_prefixes) and candidate not in seen:
                queue.append(candidate)

    index = ["# Local web capture", "", "## Pages", ""]
    index.extend(f"- [{title}]({filename})" for title, filename, _ in pages)
    index.append("")
    (output / "catalog.md").write_text("\n".join(index), encoding="utf-8")
    return {
        "ok": True,
        "output": str(output),
        "pages_captured": len(pages),
        "pages_discovered": len(seen),
        "warnings": warnings,
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Capture bounded same-origin HTML pages as local Markdown.")
    parser.add_argument("url", help="Absolute http(s) URL to start crawling from")
    parser.add_argument("--output", type=Path, required=True, help="Empty or existing directory for generated Markdown")
    parser.add_argument("--max-pages", type=int, default=25, help="Maximum pages to capture (default: 25)")
    parser.add_argument(
        "--allow-private-hosts",
        action="store_true",
        help="Allow private, loopback, link-local, or reserved hosts after explicit user approval.",
    )
    parser.add_argument(
        "--include-prefix",
        action="append",
        default=[],
        help="Same-origin URL path prefix allowed during crawl; repeatable. Defaults to the start URL's directory.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        print(json.dumps(crawl(args.url, args.output, args.max_pages, args.include_prefix, args.allow_private_hosts), indent=2))
        return 0
    except (ValueError, URLError, OSError) as exc:
        print(json.dumps({"ok": False, "error": str(exc)}), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
