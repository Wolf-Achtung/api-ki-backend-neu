# -*- coding: utf-8 -*-
"""KIS-1273: Der Tool-Radar sucht nur noch auf der Herstellerseite.

Der erste Lauf am 03.09.2026 (32 Befunde, Issue #1168) lieferte
unbrauchbare Vorschlaege. Die Suche lief als freie Websuche mit der
Query "<Name> Preise Preisaenderung Datenschutz AVV Hosting <Jahr>" —
bei mehrdeutigen Tool-Namen kam Unsinn heraus:

  Railway.app     -> "Railway Pricing 2026 ... Indian Railways"
  Perplexity API  -> "Fernwaerme: Preise und Preisaenderung" (BEW Berlin)

Der Rest waren Preis-Blogs. Fuer Preise in einem Beratungsbericht ist
das nicht belastbar — dieselbe Regel wie bei den Foerderquoten: der
Radar meldet, der Mensch entscheidet, aber er muss auf die richtige
Quelle zeigen.
"""
from __future__ import annotations

import pytest

from scripts.tools_radar import (
    build_candidate_query,
    collect_candidates,
    hersteller_domain,
    tavily_candidates,
)


class TestHerstellerDomain:

    @pytest.mark.parametrize("url,erwartet", [
        ("https://tally.so", "tally.so"),
        ("https://www.make.com", "make.com"),
        ("https://railway.app", "railway.app"),
        ("https://www.cloudflare.com/products/turnstile/", "cloudflare.com"),
        ("https://platform.openai.com", "platform.openai.com"),
    ])
    def test_domain_wird_sauber_gelesen(self, url, erwartet):
        assert hersteller_domain(url) == erwartet

    @pytest.mark.parametrize("url", ["", None, "kaputt", "ftp://x"])
    def test_unbrauchbare_url_ergibt_leer(self, url):
        assert hersteller_domain(url) == ""


class TestQuery:

    def test_ohne_jahreszahl(self):
        """Die Jahreszahl zog Blog-Artikel an ('Pricing 2026')."""
        q = build_candidate_query("Railway.app", 2026)
        assert "2026" not in q

    def test_enthaelt_die_sachbegriffe(self):
        q = build_candidate_query("Tally.so", 2026).lower()
        assert "pricing" in q and "privacy" in q

    def test_toolname_bleibt_erhalten(self):
        assert "Aleph Alpha PhariaAI" in build_candidate_query("Aleph  Alpha   PhariaAI", 2026)


class TestSucheIstDomainGebunden:

    def test_ohne_domain_wird_nicht_gesucht(self):
        """Lieber kein Vorschlag als ein Preis-Blog."""
        assert tavily_candidates("Railway.app", 2026, "key", domain="") == []

    def test_domain_landet_im_payload(self, monkeypatch):
        gesendet = {}

        class _Antwort:
            def raise_for_status(self): pass
            def json(self): return {"results": [
                {"url": "https://railway.app/pricing", "title": "Pricing"}]}

        import requests
        monkeypatch.setattr(requests, "post",
                            lambda *a, **kw: gesendet.update(kw.get("json") or {}) or _Antwort())
        treffer = tavily_candidates("Railway.app", 2026, "key", domain="railway.app")
        assert gesendet["include_domains"] == ["railway.app"]
        assert treffer[0]["url"] == "https://railway.app/pricing"

    def test_collect_reicht_die_domain_je_tool_durch(self):
        tools = [
            {"name": "Railway.app", "url": "https://railway.app"},
            {"name": "Perplexity API", "url": "https://www.perplexity.ai"},
        ]
        findings = [{"type": "stale", "tool": "Railway.app", "detail": ""},
                    {"type": "stale", "tool": "Perplexity API", "detail": ""}]
        gesehen = {}

        def _fake(name, year, api_key, *, domain="", **kw):
            gesehen[name] = domain
            return [{"title": "x", "url": f"https://{domain}/pricing"}]

        collect_candidates(tools, findings, "key", 2026, search=_fake)
        assert gesehen == {"Railway.app": "railway.app",
                           "Perplexity API": "perplexity.ai"}

    def test_tool_ohne_url_wird_uebersprungen(self):
        tools = [{"name": "Ohne URL", "url": ""}]
        findings = [{"type": "stale", "tool": "Ohne URL", "detail": ""}]
        ergebnis = collect_candidates(tools, findings, "key", 2026,
                                      search=tavily_candidates)
        assert ergebnis == {}
