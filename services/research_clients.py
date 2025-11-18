
# -*- coding: utf-8 -*-
"""
services.research_clients
-------------------------
Leichtgewichtige HTTP/RSS-Client-Helper für die Live-Recherche.
- Keine externen Such-APIs notwendig
- Nutzt RSS/Atom (verlässlich, „scraping-light“)
- Robust: Timeouts, Fallbacks, Domain-Filter

Benötigte Pakete (requirements):
    requests>=2.31.0
    feedparser>=6.0.11
    beautifulsoup4>=4.12.3
    lxml>=5.3.0
"""
from __future__ import annotations

import re
import time
import json
import hashlib
import logging
from typing import Any, Dict, List, Optional
from urllib.parse import urlparse

import requests
import feedparser
from bs4 import BeautifulSoup

log = logging.getLogger(__name__)

DEFAULT_TIMEOUT = (10, 20)  # (connect, read)

USER_AGENT = (
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/118.0 Safari/537.36"
)

def _headers(extra: Optional[Dict[str, str]] = None) -> Dict[str, str]:
    h = {
        "User-Agent": USER_AGENT,
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "de,en;q=0.9",
    }
    if extra:
        h.update(extra)
    return h

# --- simple, file-based cache (avoids Redis dependency) ---

_CACHE_PATH = "/tmp/ksj_research_cache.json"

def _load_cache() -> Dict[str, Any]:
    try:
        with open(_CACHE_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
            return data if isinstance(data, dict) else {}
    except Exception:
        return {}

def _save_cache(cache: Dict[str, Any]) -> None:
    try:
        with open(_CACHE_PATH, "w", encoding="utf-8") as f:
            json.dump(cache, f, ensure_ascii=False)
    except Exception:
        pass

def _cache_get(key: str, max_age_sec: int) -> Optional[Any]:
    cache = _load_cache()
    item = cache.get(key)
    if not item:
        return None
    ts = item.get("ts", 0)
    if time.time() - ts > max_age_sec:
        return None
    return item.get("val")

def _cache_set(key: str, val: Any) -> None:
    cache = _load_cache()
    cache[key] = {"ts": time.time(), "val": val}
    _save_cache(cache)

def _cache_key(prefix: str, url: str) -> str:
    return prefix + "_" + hashlib.sha1(url.encode("utf-8")).hexdigest()[:12]

# --- HTTP helpers ---

def http_get(url: str, timeout: Optional[tuple] = None) -> str | None:
    """GET text content with UA + timeout + basic cache (5 minutes)."""
    if not timeout:
        timeout = DEFAULT_TIMEOUT
    key = _cache_key("GET", url)
    cached = _cache_get(key, 300)  # 5 min
    if cached:
        return str(cached) if isinstance(cached, str) else None
    try:
        r = requests.get(url, headers=_headers(), timeout=timeout)
        if r.ok and r.text:
            _cache_set(key, r.text)
            return str(r.text)
        log.warning("GET failed %s: %s", url, r.status_code)
    except Exception as exc:
        log.warning("GET exception %s: %s", url, exc)
    return None

def http_get_json(url: str, timeout: Optional[tuple] = None) -> dict[Any, Any] | None:
    raw = http_get(url, timeout=timeout)
    if not raw:
        return None
    try:
        data = json.loads(raw)
        return data if isinstance(data, dict) else None
    except Exception:
        return None

# --- RSS parsing ---

def parse_rss(url: str, limit: int = 12) -> List[Dict[str, Any]]:
    key = _cache_key("RSS", url)
    cached = _cache_get(key, 300)  # 5 min
    if cached and isinstance(cached, list):
        return list(cached)
    try:
        d = feedparser.parse(url)
        items: List[Dict[str, Any]] = []
        for entry in d.entries[:limit]:
            title = entry.get("title", "").strip()
            link = entry.get("link", "").strip()
            # Fallback to html.parser if lxml is not installed or parsing fails
            raw_summary = entry.get("summary", "") or entry.get("description", "")
            try:
                summary = BeautifulSoup(raw_summary, "lxml").get_text(" ", strip=True)
            except Exception:
                summary = BeautifulSoup(raw_summary, "html.parser").get_text(" ", strip=True)
            date = entry.get("published", "") or entry.get("updated", "")
            source = urlparse(link).netloc
            if title and link:
                items.append({
                    "title": title,
                    "url": link,
                    "summary": summary[:280],
                    "date": date,
                    "source": source,
                })
        _cache_set(key, items)
        return items
    except Exception as exc:
        log.warning("parse_rss failed %s: %s", url, exc)
        return []

# --- Lightweight HTML harvesting (links on curated pages) ---

def harvest_links(url: str, allow_domains: Optional[List[str]] = None, limit: int = 20) -> List[Dict[str, str]]:
    """
    Holt alle <a>-Links von einer Seite und filtert nach Domains.
    Nützlich z. B. für Tool-Kataloge oder Programmlisten.
    """
    html = http_get(url)
    if not html:
        return []
    # Attempt to parse with lxml; fallback to html.parser if lxml isn't available
    try:
        soup = BeautifulSoup(html, "lxml")
    except Exception:
        soup = BeautifulSoup(html, "html.parser")
    out: List[Dict[str, str]] = []
    for a in soup.find_all("a", href=True):
        href = a["href"].strip()
        text = a.get_text(" ", strip=True)
        if not href.startswith(("http://", "https://")):
            continue
        dom = urlparse(href).netloc.lower()
        if allow_domains and not any(dom == d or dom.endswith("." + d) for d in allow_domains):
            continue
        title = text or dom
        if title and href:
            out.append({"title": title[:140], "url": href, "source": dom})
        if len(out) >= limit:
            break
    return out
