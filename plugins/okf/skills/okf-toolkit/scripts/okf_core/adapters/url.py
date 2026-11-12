from __future__ import annotations

import http.client
import ipaddress
import socket
import ssl
from urllib.parse import urlparse, urlunparse

_MAX_BYTES = 5 * 1024 * 1024
_ALLOWED_TYPES = {"text/plain", "text/markdown", "text/html", "application/json"}


class _PinnedHTTPSConnection(http.client.HTTPSConnection):
    """HTTPS connection that connects to an already-validated IP address."""

    def __init__(self, hostname: str, address: str, port: int, context: ssl.SSLContext):
        super().__init__(hostname, port=port, timeout=10, context=context)
        self._pinned_address = address

    def connect(self) -> None:
        raw_socket = socket.create_connection((self._pinned_address, self.port), self.timeout)
        self.sock = self._context.wrap_socket(raw_socket, server_hostname=self.host)


def _resolve_public_addresses(hostname: str) -> list[str]:
    try:
        addresses = {info[4][0] for info in socket.getaddrinfo(hostname, None)}
    except socket.gaierror as exc:
        raise ValueError(f"could not resolve URL host: {hostname}") from exc

    public_addresses: list[str] = []
    for address in sorted(addresses):
        if not ipaddress.ip_address(address).is_global:
            raise ValueError(f"URL host resolves to private or reserved address: {hostname}")
        public_addresses.append(address)
    return public_addresses


def fetch_url(url: str) -> tuple[str, str]:
    parsed = urlparse(url)
    if parsed.scheme.lower() != "https":
        raise ValueError("URL ingestion requires HTTPS")
    if not parsed.hostname or parsed.username or parsed.password:
        raise ValueError("URL must contain a public hostname and no credentials")
    port = parsed.port or 443
    addresses = _resolve_public_addresses(parsed.hostname)
    if not addresses:
        raise ValueError(f"URL host has no public addresses: {parsed.hostname}")

    path = urlunparse(("", "", parsed.path or "/", parsed.params, parsed.query, ""))
    context = ssl.create_default_context()
    connection = _PinnedHTTPSConnection(parsed.hostname, addresses[0], port, context)
    try:
        connection.request(
            "GET",
            path,
            headers={"Host": parsed.hostname, "User-Agent": "okf-repository-toolkit/0.1"},
        )
        response = connection.getresponse()
        content_type = response.getheader("Content-Type", "").split(";", 1)[0].lower()
        if content_type not in _ALLOWED_TYPES:
            raise ValueError(f"unsupported URL content type: {content_type or 'unknown'}")
        data = response.read(_MAX_BYTES + 1)
        if len(data) > _MAX_BYTES:
            raise ValueError("URL response exceeds the 5 MiB limit")
        if not 200 <= response.status < 300:
            raise ValueError(f"URL fetch returned HTTP {response.status}")
        return data.decode("utf-8", errors="replace"), url
    except (OSError, http.client.HTTPException) as exc:
        raise ValueError(f"URL fetch failed: {exc}") from exc
    finally:
        connection.close()
