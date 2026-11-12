import pytest

from okf_core.adapters.url import fetch_url


def test_fetch_url_requires_https():
    with pytest.raises(ValueError, match="HTTPS"):
        fetch_url("http://example.com/notes")


def test_fetch_url_rejects_local_hosts():
    with pytest.raises(ValueError, match="private"):
        fetch_url("https://localhost/notes")


def test_fetch_url_reads_allowed_text_response(monkeypatch):
    class Response:
        status = 200

        def getheader(self, name, default):
            assert name == "Content-Type"
            return "text/plain; charset=utf-8"

        def read(self, limit):
            assert limit > 0
            return b"decision text"

    class Connection:
        def __init__(self, hostname, address, port, context):
            assert (hostname, address, port) == ("example.com", "203.0.113.10", 443)

        def request(self, method, path, headers):
            assert (method, path) == ("GET", "/notes")
            assert headers["Host"] == "example.com"

        def getresponse(self):
            return Response()

        def close(self):
            pass

    monkeypatch.setattr(
        "okf_core.adapters.url._resolve_public_addresses",
        lambda host: ["203.0.113.10"],
    )
    monkeypatch.setattr("okf_core.adapters.url._PinnedHTTPSConnection", Connection)

    assert fetch_url("https://example.com/notes") == ("decision text", "https://example.com/notes")
