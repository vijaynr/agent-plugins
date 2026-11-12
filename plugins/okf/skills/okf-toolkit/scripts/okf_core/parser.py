from __future__ import annotations

import ast
import re
from dataclasses import dataclass
from pathlib import PurePosixPath


_FRONTMATTER_RE = re.compile(r"\A---\r?\n(?P<meta>.*?)(?:\r?\n)---\r?\n?(?P<body>.*)\Z", re.DOTALL)


@dataclass(frozen=True)
class Document:
    path: PurePosixPath
    frontmatter: dict[str, object]
    body: str
    has_frontmatter: bool


def _parse_value(raw: str) -> object:
    value = raw.strip()
    if not value:
        return ""
    if value.startswith("[") and value.endswith("]"):
        try:
            return list(ast.literal_eval(value))
        except (ValueError, SyntaxError):
            return [item.strip().strip("'\"") for item in value[1:-1].split(",") if item.strip()]
    if len(value) >= 2 and value[0] == value[-1] and value[0] in "'\"":
        return value[1:-1]
    if value.lower() in {"true", "false"}:
        return value.lower() == "true"
    return value


def parse_document(path: PurePosixPath, text: str) -> Document:
    match = _FRONTMATTER_RE.match(text)
    if not match:
        return Document(path, {}, text, False)

    metadata: dict[str, object] = {}
    lines = match.group("meta").splitlines()
    index = 0
    while index < len(lines):
        line = lines[index]
        number = index + 1
        if not line.strip() or line.lstrip().startswith("#"):
            index += 1
            continue
        if ":" not in line:
            raise ValueError(f"invalid frontmatter line {number}: {line}")
        key, raw = line.split(":", 1)
        key = key.strip()
        if not key:
            raise ValueError(f"empty frontmatter key on line {number}")
        marker = raw.strip()
        if marker in {"|", ">"}:
            values: list[str] = []
            index += 1
            while index < len(lines) and (not lines[index].strip() or lines[index].startswith(" ")):
                values.append(lines[index].strip())
                index += 1
            separator = "\n" if marker == "|" else " "
            metadata[key] = separator.join(values).rstrip() + "\n"
            continue
        if not marker and index + 1 < len(lines) and lines[index + 1].lstrip().startswith("-"):
            values = []
            index += 1
            while index < len(lines) and lines[index].lstrip().startswith("-"):
                values.append(_parse_value(lines[index].lstrip()[1:]))
                index += 1
            metadata[key] = values
            continue
        metadata[key] = _parse_value(raw)
        index += 1
    return Document(path, metadata, match.group("body"), True)
