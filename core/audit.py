"""
core/audit.py — Audit-trail helpers (client IP resolution, anonymization).

Centralizes helpers used by /submit and other endpoints that persist audit
metadata, so /chat and /admin/replay (6B) can share the same primitives.
"""
from __future__ import annotations

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
            return first
    if request.client and request.client.host:
        return request.client.host
    return None
