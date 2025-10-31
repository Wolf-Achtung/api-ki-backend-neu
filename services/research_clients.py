# -*- coding: utf-8 -*-
"""
services/research_clients.py
----------------------------
HTTP-Wrapper für Tavily & Perplexity mit robuster Fehlerbehandlung
und einheitlichem Ergebnisformat.

Resultat (normiert):
    {
      "title": str, "url": str, "snippet": str,
      "source": "tavily"|"perplexity",
      "published_at": "YYYY-MM-DD" | None,
      "score": float   # grobe Qualitätsgewichtung (Domain, Vollständigkeit)
    }
"""
from __future__ import annotations
from dataclasses import dataclass
from typing import Any, Dict, List, Optional
import os
import re
import json
import time
import logging
from urllib.parse import urlparse, urlunparse, parse_qs, urlencode

import requests

log = logging.getLogger(__name__)


# -----------------------------------------------------------------------------
# Utilities
# -----------------------------------------------------------------------------

def _normalize_url(u: str) -> str:
    try:
        p = urlparse(u)
        q = parse_qs(p.query)
        # Entferne Tracking-Parameter
        for key in list(q.keys()):
            if key.startswith("utm_") or key in {"fbclid", "gclid"}:
                q.pop(key, None)
        path = re.sub(r"/+$", "", p.path or "")
        return urlunparse((p.scheme, p.netloc.lower(), path, "", urlencode(q, doseq=True), ""))
    except Exception:
        return u

def _extract_date(text: str) -> Optional[str]:
    # primitive ISO-Dateisuche
    if not text:
        return None
    m = re.search(r"(20\d{2}-\d{2}-\d{2})", text)
    if m:
        return m.group(1)
    return None


# -----------------------------------------------------------------------------
# Tavily
# -----------------------------------------------------------------------------

@dataclass
class TavilyClient:
    api_key: str = os.getenv("TAVILY_API_KEY", "")
    endpoint: str = "https://api.tavily.com/search"
    timeout: int = 45

    def available(self) -> bool:
        return bool(self.api_key)

    def search(self, query: str, include_domains=None, exclude_domains=None,
               days: Optional[int] = None, max_results: int = 10) -> List[Dict[str, Any]]:
        if not self.available():
            return []
        payload = {
            "api_key": self.api_key,
            "query": query,
            "search_depth": "advanced",
            "max_results": max_results,
            "include_answer": False,
            "include_images": False,
            "include_raw_content": False,
        }
        if include_domains:
            payload["include_domains"] = include_domains
        if exclude_domains:
            payload["exclude_domains"] = exclude_domains
        if days:
            payload["days"] = int(days)
        try:
            r = requests.post(self.endpoint, json=payload, timeout=self.timeout)
            r.raise_for_status()
            data = r.json()
            items = []
            for it in data.get("results", []):
                url = _normalize_url(it.get("url", ""))
                if not url:
                    continue
                items.append({
                    "title": it.get("title") or it.get("url"),
                    "url": url,
                    "snippet": it.get("content") or "",
                    "published_at": _extract_date(json.dumps(it, ensure_ascii=False)),
                    "source": "tavily",
                    "score": 0.0,
                })
            return items
        except Exception as exc:
            log.warning("Tavily error for %r: %s", query, exc)
            return []


# -----------------------------------------------------------------------------
# Perplexity
# -----------------------------------------------------------------------------

@dataclass
class PerplexityClient:
    api_key: str = os.getenv("PERPLEXITY_API_KEY", "")
    endpoint: str = "https://api.perplexity.ai/chat/completions"
    model: str = os.getenv("PERPLEXITY_MODEL", "sonar")
    timeout: int = 60

    def available(self) -> bool:
        return bool(self.api_key)

    def ask_json(self, question: str) -> List[Dict[str, Any]]:
        """
        Fragt Perplexity mit der Bitte um eine JSON-Liste von Quellen.
        Fallback: versucht, JSON aus freiem Text zu extrahieren.
        """
        if not self.available():
            return []
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        system = (
            "You are a meticulous research assistant. "
            "Return ONLY a JSON array of objects with keys: "
            "title, url, date (YYYY-MM-DD if available), summary. "
            "Prefer primary sources (government, EU, official portals). "
            "German language where possible."
        )
        payload = {
            "model": self.model,
            "temperature": 0.0,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": question},
            ],
        }
        try:
            r = requests.post(self.endpoint, headers=headers, json=payload, timeout=self.timeout)
            r.raise_for_status()
            content = r.json()["choices"][0]["message"]["content"]
            # Versuche JSON direkt zu laden
            try:
                data = json.loads(content)
                items = []
                for x in data:
                    url = _normalize_url(x.get("url", ""))
                    if not url:
                        continue
                    items.append({
                        "title": x.get("title") or url,
                        "url": url,
                        "snippet": x.get("summary") or "",
                        "published_at": x.get("date") or _extract_date(json.dumps(x)),
                        "source": "perplexity",
                        "score": 0.0,
                    })
                return items
            except Exception:
                # Fallback: JSON im Fließtext extrahieren
                m = re.search(r"(\[.*\])", content, re.DOTALL)
                if m:
                    arr = json.loads(m.group(1))
                    items = []
                    for x in arr:
                        url = _normalize_url(x.get("url", ""))
                        if not url:
                            continue
                        items.append({
                            "title": x.get("title") or url,
                            "url": url,
                            "snippet": x.get("summary") or "",
                            "published_at": x.get("date") or _extract_date(json.dumps(x)),
                            "source": "perplexity",
                            "score": 0.0,
                        })
                    return items
        except Exception as exc:
            log.warning("Perplexity error: %s", exc)
            return []
        return []
