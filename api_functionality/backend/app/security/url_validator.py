"""Validate monitor targets before any outbound HTTP request."""

import asyncio
import ipaddress
import socket
from dataclasses import dataclass
from urllib.parse import urlsplit


ALLOWED_SCHEMES = frozenset({"http", "https"})
DNS_RESOLUTION_TIMEOUT_SECONDS = 5


class MonitorUrlRejectedError(ValueError):
    """Raised when a monitor target violates the outbound request policy."""

    def __init__(self, reason: str) -> None:
        super().__init__(f"Monitor URL rejected: {reason}")


@dataclass(frozen=True)
class MonitorTarget:
    """The network-relevant parts of a syntactically valid monitor URL."""

    hostname: str
    port: int


def validate_monitor_url_syntax(url: str) -> MonitorTarget:
    """Require an ordinary credential-free HTTP(S) URL."""
    if not isinstance(url, str) or not url:
        raise MonitorUrlRejectedError("A URL is required.")

    if "\\" in url or any(ord(character) < 32 for character in url):
        raise MonitorUrlRejectedError(
            "Backslashes and control characters are not allowed."
        )

    try:
        parsed = urlsplit(url)
        hostname = parsed.hostname
        port = parsed.port
    except ValueError as error:
        raise MonitorUrlRejectedError("The URL is malformed.") from error

    if parsed.scheme.lower() not in ALLOWED_SCHEMES:
        raise MonitorUrlRejectedError(
            "Only http:// and https:// URLs are allowed."
        )

    if parsed.username is not None or parsed.password is not None:
        raise MonitorUrlRejectedError(
            "Embedded usernames and passwords are not allowed."
        )

    if hostname is None or not hostname.strip():
        raise MonitorUrlRejectedError("The URL must include a hostname.")

    if port is None:
        port = 443 if parsed.scheme.lower() == "https" else 80
    elif port <= 0:
        raise MonitorUrlRejectedError("The URL port must be positive.")

    return MonitorTarget(hostname=hostname, port=port)


def _parse_resolved_address(value: str) -> ipaddress.IPv4Address | ipaddress.IPv6Address:
    """Convert getaddrinfo output to an address without an IPv6 scope id."""
    return ipaddress.ip_address(value.split("%", 1)[0])


def _require_global_address(
    address: ipaddress.IPv4Address | ipaddress.IPv6Address,
) -> None:
    if (
        not address.is_global
        or address.is_private
        or address.is_loopback
        or address.is_link_local
        or address.is_multicast
        or address.is_reserved
        or address.is_unspecified
    ):
        raise MonitorUrlRejectedError(
            "The target resolves to a private, local, reserved, or otherwise "
            "non-public network address."
        )


async def _resolve_hostname(hostname: str, port: int) -> tuple[str, ...]:
    loop = asyncio.get_running_loop()

    try:
        records = await asyncio.wait_for(
            loop.getaddrinfo(
                hostname,
                port,
                type=socket.SOCK_STREAM,
                proto=socket.IPPROTO_TCP,
            ),
            timeout=DNS_RESOLUTION_TIMEOUT_SECONDS,
        )
    except (TimeoutError, socket.gaierror, UnicodeError) as error:
        raise MonitorUrlRejectedError(
            "The target hostname could not be resolved to a public address."
        ) from error

    addresses = tuple(
        dict.fromkeys(record[4][0] for record in records)
    )
    if not addresses:
        raise MonitorUrlRejectedError(
            "The target hostname did not resolve to an address."
        )

    return addresses


async def validate_monitor_url(url: str) -> None:
    """Resolve a monitor URL and reject every non-global destination."""
    target = validate_monitor_url_syntax(url)

    try:
        literal_address = _parse_resolved_address(target.hostname)
    except ValueError:
        resolved_addresses = await _resolve_hostname(
            target.hostname,
            target.port,
        )
    else:
        _require_global_address(literal_address)
        return

    for value in resolved_addresses:
        try:
            address = _parse_resolved_address(value)
        except ValueError as error:
            raise MonitorUrlRejectedError(
                "DNS returned an invalid network address."
            ) from error

        _require_global_address(address)
