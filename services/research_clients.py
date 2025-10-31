# -*- coding: utf-8 -*-
"""
services/research_clients.py
----------------------------
HTTP-Wrapper für Tavily & Perplexity mit robuster Fehlerbehandlung
und einheitlichem Ergebnisformat.
"""
from __future__ import annotations
from dataclasses import dataclass
from typing import Any, Dict, List, Optional
import os
import re
import json
import logging
from urllib.parse import urlparse, urlunparse, parse_qs, urlencode

import requests

log = logging.getLogger(__name__)

def _normalize_url(u: str) -> str:
    try:
        p = urlparse(u)
        q = parse_qs(p.query)
        # Entferne Tracking
        for key in list(q.keys()):
            if key.startswith("utm_") or key in {"fbclid", "gclid"}:
                q.pop(key, None)
        path = re.sub(r"/+$", "", p.path or "")
        return urlunparse((p.scheme, p.netloc.lower(), path, "", urlencode(q, doseq=True), ""))
    except Exception:
        return u

def _extract_date(text: str) -> Optional[str]:
    if not text:
        return None
    m = re.search(r"(20\d{2}-\d{2}-\d{2})", text)
    if m:
        return m.group(1)
    return None

def _price_hint(snippet: str) -> str:
    if not snippet:
        return "—"
    # sehr einfache Erkennung
    m = re.search(r"(\d{1,4}[,\.]?\d{0,2})\s*(€|EUR|Euro|\$|USD)\b", snippet, re.IGNORECASE)
    return f"{m.group(0)}" if m else "—"

def _trust_center(url: str) -> str:
    if any(x in url for x in ("/trust", "/security", "/privacy", "/compliance", "/gdpr")):
        return "Trust/Privacy"
    return "—"


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
                snippet = it.get("content") or ""
                items.append({
                    "title": it.get("title") or it.get("url"),
                    "url": url,
                    "snippet": snippet,
                    "published_at": _extract_date(json.dumps(it, ensure_ascii=False)),
                    "source": "tavily",
                    "score": 0.0,
                    "price_hint": _price_hint(snippet),
                    "tc": _trust_center(url),
                })
            return items
        except Exception as exc:
            log.warning("Tavily error for %r: %s", query, exc)
            return []


@dataclass
class PerplexityClient:
    api_key: str = os.getenv("PERPLEXITY_API_KEY", "")
    endpoint: str = "https://api.perplexity.ai/chat/completions"
    model: str = os.getenv("PERPLEXITY_MODEL", "sonar")
    timeout: int = 60

    def available(self) -> bool:
        return bool(self.api_key)

    def ask_json(self, question: str) -> List[Dict[str, Any]]:
        if not self.available():
            return []
        headers = {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}
        system = (
            "Return ONLY a JSON array of objects with keys: "
            "title, url, date (YYYY-MM-DD), summary. Prefer primary sources."
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
            try:
                data = json.loads(content)
            except Exception:
                m = re.search(r"(\[.*\])", content, re.DOTALL)
                data = json.loads(m.group(1)) if m else []
            items = []
            for x in data:
                url = _normalize_url(x.get("url", ""))
                if not url:
                    continue
                snippet = x.get("summary") or ""
                items.append({
                    "title": x.get("title") or url,
                    "url": url,
                    "snippet": snippet,
                    "published_at": x.get("date") or _extract_date(json.dumps(x)),
                    "source": "perplexity",
                    "score": 0.0,
                    "price_hint": _price_hint(snippet),
                    "tc": _trust_center(url),
                })
            return items
        except Exception as exc:
            log.warning("Perplexity error: %s", exc)
            return []
