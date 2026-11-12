from __future__ import annotations

import re
from pathlib import Path

_MAX_BYTES = 20 * 1024 * 1024
_TEXT_RE = re.compile(rb"\(([^()]*)\)\s*T[Jj]")


def extract_pdf(path: Path) -> str:
    data = path.read_bytes()
    if len(data) > _MAX_BYTES:
        raise ValueError("PDF exceeds the 20 MiB extraction limit")
    if not data.startswith(b"%PDF-"):
        raise ValueError("invalid PDF header")
    parts = [match.group(1).decode("latin-1") for match in _TEXT_RE.finditer(data)]
    return " ".join(parts).strip()
