"""
core/audit.py — Audit-trail helpers (client IP resolution, anonymization).

Centralizes helpers used by /submit and other endpoints that persist audit
metadata, so /chat and /admin/replay (6B) can share the same primitives.
"""
from __future__ import annotations

import ipaddress
import os
from typing import Optional

from fastapi import Request


def _resolve_client_ip(request: Request) -> Optional[str]:
    """Resolve the originating client IP.

    Railway routes through Fastly; ``request.client.host`` is the CDN IP, not
    the user. Prefer the first entry of ``X-Forwarded-For`` (the chain's
    leftmost address is the original client per RFC 7239).
    """
    xff = request.headers.get("x-forwarded-for")
    if xff:
        first = xff.split(",")[0].strip()
        if first:
            return str(first)
    if request.client and request.client.host:
        return str(request.client.host)
    return None


def anonymize_ip(ip: Optional[str]) -> Optional[str]:
    """Anonymize IP for audit logging.

    - IPv4: zero last octet (e.g., 203.0.113.42 -> 203.0.113.0)
    - IPv6: zero last 80 bits, preserve /48 prefix
    - Invalid/None: return as-is (helps debugging malformed inputs)

    Bypassed when AUDIT_FULL_IP=1 (set in Railway for forensic use only).
    """
    if not ip:
        return ip
    if os.getenv("AUDIT_FULL_IP", "0") == "1":
        return ip
    try:
        addr = ipaddress.ip_address(ip)
        if isinstance(addr, ipaddress.IPv4Address):
            net = ipaddress.ip_network(f"{ip}/24", strict=False)
            return str(net.network_address)
        else:  # IPv6
            net = ipaddress.ip_network(f"{ip}/48", strict=False)
            return str(net.network_address)
    except ValueError:
        return ip  # leave malformed IPs untouched


def _truncate(value: Optional[str], limit: int = 500) -> Optional[str]:
    """Truncate strings for DB columns / log lines."""
    if not value:
        return None
    return value if len(value) <= limit else value[: limit - 1] + "…"
