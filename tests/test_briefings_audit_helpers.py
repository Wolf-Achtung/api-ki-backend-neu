# -*- coding: utf-8 -*-
"""Unit tests for the audit-trail helpers in routes.briefings (Schritt 6).

Wir testen die zwei reinen Helper, nicht das volle FastAPI-Setup.
``_resolve_client_ip`` ist die kritische Funktion — Railway routet durch
Fastly, ohne XFF-Auswertung würde jedes Briefing die CDN-IP loggen.
"""
from __future__ import annotations

from types import SimpleNamespace

import pytest

from routes.briefings import _resolve_client_ip, _truncate


class _FakeRequest:
    """Minimal Request-Stub: nur ``headers`` (dict-like) und ``client``."""

    def __init__(self, headers: dict | None = None, client_host: str | None = None):
        self.headers = headers or {}
        self.client = SimpleNamespace(host=client_host) if client_host else None


def test_resolve_client_ip_uses_xff_first_entry() -> None:
    """X-Forwarded-For: leftmost = ursprünglicher Client (RFC 7239)."""
    req = _FakeRequest(
        headers={"x-forwarded-for": "203.0.113.42, 100.64.0.5, 10.0.0.1"},
        client_host="100.64.0.5",  # CDN-IP
    )
    assert _resolve_client_ip(req) == "203.0.113.42"


def test_resolve_client_ip_falls_back_to_request_client() -> None:
    """Ohne XFF: request.client.host."""
    req = _FakeRequest(client_host="198.51.100.7")
    assert _resolve_client_ip(req) == "198.51.100.7"


def test_resolve_client_ip_returns_none_when_unknown() -> None:
    """Weder XFF noch request.client → None (statt empty string)."""
    req = _FakeRequest()
    assert _resolve_client_ip(req) is None


def test_resolve_client_ip_strips_whitespace_in_xff() -> None:
    """XFF-Liste mit Spaces → erstes IP getrimmt."""
    req = _FakeRequest(headers={"x-forwarded-for": "  192.0.2.1  ,  10.0.0.1  "})
    assert _resolve_client_ip(req) == "192.0.2.1"


def test_resolve_client_ip_empty_xff_falls_back() -> None:
    """Leerer XFF-Header → fallback auf request.client."""
    req = _FakeRequest(
        headers={"x-forwarded-for": ""},
        client_host="198.51.100.7",
    )
    assert _resolve_client_ip(req) == "198.51.100.7"


# --- _truncate ----------------------------------------------------------


def test_truncate_keeps_short_strings_unchanged() -> None:
    assert _truncate("Mozilla/5.0") == "Mozilla/5.0"


def test_truncate_returns_none_for_none() -> None:
    assert _truncate(None) is None


def test_truncate_returns_none_for_empty_string() -> None:
    """Empty UA-Header sollte None loggen, nicht ''."""
    assert _truncate("") is None


def test_truncate_cuts_long_strings_with_ellipsis() -> None:
    long = "x" * 600
    out = _truncate(long, limit=500)
    assert out is not None
    assert len(out) == 500
    assert out.endswith("…")


def test_truncate_default_limit_is_500() -> None:
    long = "x" * 1000
    out = _truncate(long)
    assert out is not None
    assert len(out) == 500
