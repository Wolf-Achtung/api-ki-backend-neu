# -*- coding: utf-8 -*-
"""
Research‑Policy Wrapper für Tavily/Perplexity
=============================================
- Domänen‑Whitelist (seriöse Quellen, EU/DE Fokus)
- Optional: Blocklist (Werbe‑/Affiliate‑Lastig)
- Zeitfenster 7/30/60 Tage (pro Recherchekategorie)
- Einheitliches Rückgabeformat
- Defensive Fehlerbehandlung (nie Exception nach außen)

Integration:
    from services.research_policy import ResearchPolicy

    rp = ResearchPolicy()
    tools = rp.search_tools(query="beste RAG Tools EU Hosting", days=30)
    funding = rp.search_funding(state="BE", topic="KI Förderung", days=30)

Wenn RESEARCH_PROVIDER in ENV nicht gesetzt ist, wird Tavily genutzt (so wie bisher).
"""
from __future__ import annotations

import os
import re
import time
import html
import json
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple
import logging

import requests

log = logging.getLogger(__name__)


def _d(val: str, default: str) -> str:
    return (val or "").strip() or default


def _int_env(name: str, default: int) -> int:
    try:
        return int(os.getenv(name, default))
    except Exception:
        return default


# ------------------------------ Whitelists ------------------------------

DEFAULT_WHITELIST = [
    # EU/DE Behörden & Programme
    "ec.europa.eu", "europe.eu", "digital-strategy.ec.europa.eu",
    "bmwk.de", "foerderdatenbank.de", "bmbf.de",
    # Länder (Beispiele, Liste beliebig erweiterbar)
    "bayern.de", "stmwi.bayern.de", "nrw.de", "mkw.nrw", "berlin.de",
    "hamburg.de", "sachsen.de", "baden-wuerttemberg.de", "rlp.de",
    # Sicherheit/Datenschutz
    "bsi.bund.de", "bfdi.bund.de", "gematik.de",
    # Fachpresse/Tech (DE/EU)
    "heise.de", "ct.de", "t3n.de", "golem.de",
    # Open Source/Standards
    "github.com", "huggingface.co", "apache.org",
]

DEFAULT_BLOCKLIST = [
    "youtube.com", "youtu.be", "facebook.com", "instagram.com", "pinterest.com",
    "medium.com", "slideshare.net", "kiberatung.de", "everlast.ai"  # Werbung/Promo häufig
]


def clamp_days(days: Optional[int], default_env_name: str, default_value: int = 30) -> int:
    dv = _int_env(default_env_name, default_value)
    n = int(days or dv)
    return 7 if n <= 7 else 30 if n <= 30 else 60


def _map_days_to_provider(days: int) -> Tuple[str, str]:
    """Mappt Tage auf Provider‑Parameter (Tavily, Perplexity)."""
    # Tavily: time_range ∈ {"day","week","month","year"} – wir nehmen week/month
    # Perplexity: search_recency ∈ {"past_day","past_week","past_month","past_year"}
    if days <= 7:
        return ("week", "past_week")
    if days <= 30:
        return ("month", "past_month")
    return ("month", "past_month")  # 60 Tage ≈ past_month, da kein 2‑Monate Fenster


@dataclass
class Result:
    title: str
    url: str
    snippet: str = ""
    published: Optional[str] = None
    source: Optional[str] = None


def _domain(url: str) -> str:
    try:
        return re.sub(r"^www\.", "", re.findall(r"://([^/]+)/?", url)[0]).lower()
    except Exception:
        return ""


def _allowed(url: str, whitelist: List[str], blocklist: List[str]) -> bool:
    dom = _domain(url)
    if any(b in dom for b in blocklist):
        return False
    return any(w in dom for w in whitelist)


class ResearchPolicy:
    def __init__(self) -> None:
        self.provider = _d(os.getenv("RESEARCH_PROVIDER", "tavily"), "tavily").lower()
        self.tavily_key = os.getenv("TAVILY_API_KEY", "")
        self.perplexity_key = os.getenv("PERPLEXITY_API_KEY", "")
        self.whitelist = list(filter(None, [x.strip() for x in os.getenv("RESEARCH_WHITELIST", "").split(",")])) or DEFAULT_WHITELIST
        self.blocklist = list(filter(None, [x.strip() for x in os.getenv("RESEARCH_BLOCKLIST", "").split(",")])) or DEFAULT_BLOCKLIST
        self.timeout = _int_env("RESEARCH_TIMEOUT_SEC", 25)
        self.max_results = _int_env("RESEARCH_MAX_RESULTS", 8)

    # ------------------- Provider Calls (defensive) -------------------

    def _call_tavily(self, query: str, include_domains: List[str], days: int) -> List[Result]:
        if not self.tavily_key:
            log.warning("Tavily API key missing; returning empty results")
            return []
        tr_tav, _ = _map_days_to_provider(days)
        payload = {
            "api_key": self.tavily_key,
            "query": query,
            "include_domains": include_domains,
            "exclude_domains": self.blocklist,
            "search_depth": "advanced",
            "time_range": tr_tav,
            "max_results": self.max_results,
        }
        try:
            r = requests.post("https://api.tavily.com/search", json=payload, timeout=self.timeout)
            r.raise_for_status()
            data = r.json()
            items = []
            for it in data.get("results", []):
                items.append(Result(
                    title=it.get("title") or "",
                    url=it.get("url") or "",
                    snippet=it.get("content") or "",
                    published=it.get("published_date") or None,
                    source=_domain(it.get("url") or ""),
                ))
            return items
        except Exception as exc:
            log.warning("Tavily error: %s", exc)
            return []

    def _call_perplexity(self, query: str, include_domains: List[str], days: int) -> List[Result]:
        if not self.perplexity_key:
            log.warning("Perplexity API key missing; returning empty results")
            return []
        _, rec = _map_days_to_provider(days)
        headers = {"Authorization": f"Bearer {self.perplexity_key}", "Content-Type": "application/json"}
        payload = {
            "model": "sonar-small-online",
            "search_recency": rec,
            "return_images": False,
            "top_k": self.max_results,
            "search_focus": "news",
            "query": f"{query}",
            "include_domains": include_domains,
            "exclude_domains": self.blocklist,
        }
        try:
            r = requests.post("https://api.perplexity.ai/search", json=payload, headers=headers, timeout=self.timeout)
            r.raise_for_status()
            data = r.json()
            items = []
            for it in (data.get("results") or []):
                items.append(Result(
                    title=it.get("title") or "",
                    url=it.get("url") or "",
                    snippet=it.get("snippet") or "",
                    published=it.get("date") or None,
                    source=_domain(it.get("url") or ""),
                ))
            return items
        except Exception as exc:
            log.warning("Perplexity error: %s", exc)
            return []

    # ------------------- Public Facade -------------------

    def _search(self, query: str, days: int, include_domains: Optional[List[str]] = None) -> List[Result]:
        include = include_domains or self.whitelist
        if self.provider == "perplexity":
            results = self._call_perplexity(query, include, days)
        else:
            results = self._call_tavily(query, include, days)

        # Filter/Normalize/Unique
        seen = set()
        filtered: List[Result] = []
        for res in results:
            if not res.url or not _allowed(res.url, include, self.blocklist):
                continue
            key = _domain(res.url) + "|" + (res.title or "")
            if key in seen:
                continue
            seen.add(key)
            filtered.append(res)
        return filtered[: self.max_results]

    # Semantic helpers for the renderer/normalizer
    def search_tools(self, branche: str, days: Optional[int] = None) -> List[Result]:
        d = clamp_days(days, "TOOLS_DAYS", 30)
        q = f"KI Tools {branche} EU DSGVO Open Source Preise Bewertung"
        return self._search(q, days=d)

    def search_funding(self, bundesland: str, branche: Optional[str] = None, days: Optional[int] = None) -> List[Result]:
        d = clamp_days(days, "FUNDING_DAYS", 30)
        state = (bundesland or "").upper()
        loc = {
            "BE": "Berlin", "BY": "Bayern", "BW": "Baden‑Württemberg", "NW": "Nordrhein‑Westfalen",
            "HE": "Hessen", "HH": "Hamburg", "HB": "Bremen", "RP": "Rheinland‑Pfalz", "SL": "Saarland",
            "SN": "Sachsen", "ST": "Sachsen‑Anhalt", "TH": "Thüringen", "MV": "Mecklenburg‑Vorpommern",
            "NI": "Niedersachsen", "SH": "Schleswig‑Holstein"
        }.get(state, state or "Deutschland/EU")
        q = f"Förderprogramme {loc} Künstliche Intelligenz KMU Zuschuss Laufzeit Antragsfrist"
        return self._search(q, days=d)

    # ------------------- HTML helpers -------------------

    @staticmethod
    def results_to_html(items: List[Result], empty_text: str) -> str:
        if not items:
            return f"<p class='small'>{html.escape(empty_text)}</p>"
        lis = []
        for r in items:
            dom = html.escape(r.source or "")
            title = html.escape(r.title or r.url)
            url = html.escape(r.url)
            snip = html.escape((r.snippet or "")[:220])
            lis.append(f"<li><a href='{url}' rel='noopener noreferrer'>{title}</a> <em>({dom})</em><br/><span class='small'>{snip}</span></li>")
        return "<ul>" + "".join(lis) + "</ul>"
