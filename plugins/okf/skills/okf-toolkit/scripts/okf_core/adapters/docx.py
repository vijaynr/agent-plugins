from __future__ import annotations

from pathlib import Path
from zipfile import BadZipFile, ZipFile
from xml.etree import ElementTree

_MAX_BYTES = 10 * 1024 * 1024
_W_NS = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"


def extract_docx(path: Path) -> str:
    if path.stat().st_size > _MAX_BYTES:
        raise ValueError("DOCX exceeds the 10 MiB extraction limit")
    try:
        with ZipFile(path) as archive:
            info = archive.getinfo("word/document.xml")
            if info.file_size > _MAX_BYTES:
                raise ValueError("DOCX document.xml exceeds the extraction limit")
            root = ElementTree.fromstring(archive.read(info))
    except (BadZipFile, KeyError, ElementTree.ParseError) as exc:
        raise ValueError(f"invalid DOCX: {exc}") from exc
    return " ".join(node.text or "" for node in root.iter(f"{_W_NS}t")).strip()
