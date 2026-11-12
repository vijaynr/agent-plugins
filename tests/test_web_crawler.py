from __future__ import annotations

import json
import subprocess
import sys
import threading
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path


def test_web_crawler_captures_same_origin_pages_as_local_markdown(repo_root: Path, tmp_path: Path) -> None:
    source = tmp_path / "site"
    source.mkdir()
    (source / "index.html").write_text(
        "<html><body><main><h1>Start</h1><p>Welcome.</p>"
        '<a href="guide.html">Guide</a><a href="https://example.com/ignored">External</a>'
        "</main></body></html>",
        encoding="utf-8",
    )
    (source / "guide.html").write_text(
        "<html><body><main><h1>Guide</h1><p>Local guidance.</p>"
        '<a href="index.html">Start</a></main></body></html>',
        encoding="utf-8",
    )
    handler = partial(SimpleHTTPRequestHandler, directory=str(source))
    server = ThreadingHTTPServer(("127.0.0.1", 0), handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    output = tmp_path / "capture"
    script = repo_root / "plugins/web-tools/skills/web-crawler/scripts/web_crawler.py"

    try:
        result = subprocess.run(
            [
                sys.executable,
                str(script),
                f"http://127.0.0.1:{server.server_port}/index.html",
                "--output",
                str(output),
                "--max-pages",
                "5",
                "--allow-private-hosts",
            ],
            text=True,
            capture_output=True,
            check=False,
        )
    finally:
        server.shutdown()
        thread.join()

    assert result.returncode == 0, result.stderr
    summary = json.loads(result.stdout)
    assert summary["ok"] is True
    assert summary["pages_captured"] == 2
    assert "# Start" in (output / "index.md").read_text(encoding="utf-8")
    assert "# Guide" in (output / "guide.md").read_text(encoding="utf-8")
    assert "example.com" not in (output / "index.md").read_text(encoding="utf-8")
    assert "guide.md" in (output / "catalog.md").read_text(encoding="utf-8")
