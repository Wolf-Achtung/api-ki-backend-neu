# -*- coding: utf-8 -*-
"""
services/research_clients.py
----------------------------
HTTP-Wrapper für Tavily & Perplexity mit robuster Fehlerbehandlung,
NSFW-Filterung und einheitlichem Ergebnisformat.

Usage:
    tavily = TavilyClient()
    results = tavily.search("KI Tools Deutschland", days=30, max_results=10)
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

# ============================================================================
# NSFW-FILTER CONFIGURATION
# ============================================================================

NSFW_KEYWORDS = {
    # Englisch
    'porn', 'sex', 'xxx', 'adult', 'nude', 'naked', 'erotic', '18+', 'nsfw',
    'fetish', 'escort', 'dating', 'hookup', 'singles', 'webcam', 'camgirl',
    # Hindi/andere
    'chudai', 'sexy', 'bf video', 'desi sex', 'bhabhi',
    # Deutsch
    'porno', 'sexfilm', 'erotik', 'bordell', 'huren', 'nutten',
}

SPAM_DOMAINS = {
    # Pornoseiten
    'xvideos.com', 'pornhub.com', 'xhamster.com', 'youporn.com', 'redtube.com',
    'xnxx.com', 'beeg.com', 'spankbang.com', 'eporner.com',
    # Dating/Escort
    'tinder.com', 'bumble.com', 'escort', 'callgirl', 'dating.com',
    # Spam
    'click-here.com', 'download-now.com', 'free-download.com', 'torrent',
}


def _is_safe_content(title: str, url: str, snippet: str) -> bool:
    """
    Prüft ob Content sicher ist (kein NSFW/Spam).
    
    Args:
        title: Titel des Results
        url: URL des Results
        snippet: Content-Snippet
        
    Returns:
        True wenn sicher, False wenn gefiltert werden soll
    """
    # Check title
    title_lower = (title or '').lower()
    for keyword in NSFW_KEYWORDS:
        if keyword in title_lower:
            log.debug("🚫 NSFW keyword in title: %s", keyword)
            return False
    
    # Check snippet
    snippet_lower = (snippet or '').lower()
    for keyword in NSFW_KEYWORDS:
        if keyword in snippet_lower:
            log.debug("🚫 NSFW keyword in snippet: %s", keyword)
            return False
    
    # Check URL domain
    url_lower = (url or '').lower()
    for domain in SPAM_DOMAINS:
        if domain in url_lower:
            log.debug("🚫 Spam domain in URL: %s", domain)
            return False
    
    return True


# ============================================================================
# URL & DATA HELPERS
# ============================================================================

def _normalize_url(u: str) -> str:
    """Entfernt Tracking-Parameter und normalisiert URL."""
    try:
        p = urlparse(u)
        q = parse_qs(p.query)
        # Entferne Tracking
        for key in list(q.keys()):
            if key.startswith("utm_") or key in {"fbclid", "gclid", "ref"}:
                q.pop(key, None)
        path = re.sub(r"/+$", "", p.path or "")
        return urlunparse((p.scheme, p.netloc.lower(), path, "", urlencode(q, doseq=True), ""))
    except Exception:
        return u


def _extract_date(text: str) -> Optional[str]:
    """Extrahiert Datum im Format YYYY-MM-DD."""
    if not text:
        return None
    m = re.search(r"(20\d{2}-\d{2}-\d{2})", text)
    if m:
        return m.group(1)
    return None


def _price_hint(snippet: str) -> str:
    """Extrahiert Preis-Hinweis aus Snippet."""
    if not snippet:
        return "—"
    # Einfache Preis-Erkennung
    m = re.search(r"(\d{1,4}[,\.]?\d{0,2})\s*(€|EUR|Euro|\$|USD)\b", snippet, re.IGNORECASE)
    return f"{m.group(0)}" if m else "—"


def _trust_center(url: str) -> str:
    """Prüft ob URL Trust/Privacy-Infos enthält."""
    if any(x in url for x in ("/trust", "/security", "/privacy", "/compliance", "/gdpr", "/dsgvo")):
        return "Trust/Privacy"
    return "—"


# ============================================================================
# TAVILY CLIENT
# ============================================================================

@dataclass
class TavilyClient:
    """
    Tavily API Client mit NSFW-Filterung.
    
    Environment Variables:
        TAVILY_API_KEY: API Key (required)
        TAVILY_TIMEOUT: Timeout in Sekunden (default: 45)
    """
    api_key: str = os.getenv("TAVILY_API_KEY", "")
    endpoint: str = "https://api.tavily.com/search"
    timeout: int = int(os.getenv("TAVILY_TIMEOUT", "45"))

    def available(self) -> bool:
        """Prüft ob Client verfügbar ist (API Key gesetzt)."""
        return bool(self.api_key)

    def search(
        self, 
        query: str, 
        include_domains: Optional[List[str]] = None,
        exclude_domains: Optional[List[str]] = None,
        days: Optional[int] = None, 
        max_results: int = 10,
        apply_nsfw_filter: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Sucht über Tavily API.
        
        Args:
            query: Suchquery
            include_domains: Whitelist von Domains
            exclude_domains: Blacklist von Domains
            days: Zeitfenster in Tagen (7, 30, 60)
            max_results: Max. Anzahl Ergebnisse
            apply_nsfw_filter: NSFW-Filter anwenden (default: True)
            
        Returns:
            Liste von Result-Dicts mit keys: title, url, snippet, published_at, source, score, price_hint, tc
        """
        if not self.available():
            log.warning("❌ Tavily API key not set")
            return []
        
        payload = {
            "api_key": self.api_key,
            "query": query,
            "search_depth": "advanced",
            "max_results": max_results * 2 if apply_nsfw_filter else max_results,  # Mehr holen wegen Filter
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
            log.debug("🔍 Tavily search: query='%s' days=%s", query, days)
            r = requests.post(self.endpoint, json=payload, timeout=self.timeout)
            r.raise_for_status()
            data = r.json()
            
            items = []
            filtered_count = 0
            
            for it in data.get("results", []):
                url = _normalize_url(it.get("url", ""))
                if not url:
                    continue
                
                title = it.get("title") or url
                snippet = it.get("content") or ""
                
                # ✅ NSFW-Filter anwenden
                if apply_nsfw_filter and not _is_safe_content(title, url, snippet):
                    filtered_count += 1
                    continue
                
                items.append({
                    "title": title,
                    "url": url,
                    "snippet": snippet,
                    "published_at": _extract_date(json.dumps(it, ensure_ascii=False)),
                    "source": "tavily",
                    "score": 0.0,
                    "price_hint": _price_hint(snippet),
                    "tc": _trust_center(url),
                })
                
                # Stoppe wenn genug valide Ergebnisse
                if len(items) >= max_results:
                    break
            
            log.info("✅ Tavily: %d results (filtered %d NSFW/spam)", len(items), filtered_count)
            return items
            
        except requests.exceptions.Timeout:
            log.error("⏱️ Tavily timeout after %ds for query: %s", self.timeout, query)
            return []
        except requests.exceptions.RequestException as exc:
            log.error("❌ Tavily request failed for '%s': %s", query, exc)
            return []
        except Exception as exc:
            log.error("❌ Tavily error for '%s': %s", query, exc)
            return []


# ============================================================================
# PERPLEXITY CLIENT
# ============================================================================

@dataclass
class PerplexityClient:
    """
    Perplexity API Client mit NSFW-Filterung.
    
    Environment Variables:
        PERPLEXITY_API_KEY: API Key (required)
        PERPLEXITY_MODEL: Model name (default: sonar)
        PERPLEXITY_TIMEOUT: Timeout in Sekunden (default: 60)
    """
    api_key: str = os.getenv("PERPLEXITY_API_KEY", "")
    endpoint: str = "https://api.perplexity.ai/chat/completions"
    model: str = os.getenv("PERPLEXITY_MODEL", "sonar")
    timeout: int = int(os.getenv("PERPLEXITY_TIMEOUT", "60"))

    def available(self) -> bool:
        """Prüft ob Client verfügbar ist (API Key gesetzt)."""
        return bool(self.api_key)

    def ask_json(
        self, 
        question: str,
        apply_nsfw_filter: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Stellt Frage an Perplexity und erwartet JSON-Array zurück.
        
        Args:
            question: Frage/Prompt
            apply_nsfw_filter: NSFW-Filter anwenden (default: True)
            
        Returns:
            Liste von Result-Dicts
        """
        if not self.available():
            log.warning("❌ Perplexity API key not set")
            return []
        
        headers = {
            "Authorization": f"Bearer {self.api_key}", 
            "Content-Type": "application/json"
        }
        
        system = (
            "Return ONLY a JSON array of objects with keys: "
            "title, url, date (YYYY-MM-DD), summary. Prefer primary sources. "
            "NO adult/NSFW content."
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
            log.debug("🔍 Perplexity: question='%s'", question[:80])
            r = requests.post(self.endpoint, headers=headers, json=payload, timeout=self.timeout)
            r.raise_for_status()
            
            content = r.json()["choices"][0]["message"]["content"]
            
            # Parse JSON
            try:
                data = json.loads(content)
            except Exception:
                # Fallback: Extract JSON array from text
                m = re.search(r"(\[.*\])", content, re.DOTALL)
                data = json.loads(m.group(1)) if m else []
            
            items = []
            filtered_count = 0
            
            for x in data:
                url = _normalize_url(x.get("url", ""))
                if not url:
                    continue
                
                title = x.get("title") or url
                snippet = x.get("summary") or ""
                
                # ✅ NSFW-Filter anwenden
                if apply_nsfw_filter and not _is_safe_content(title, url, snippet):
                    filtered_count += 1
                    continue
                
                items.append({
                    "title": title,
                    "url": url,
                    "snippet": snippet,
                    "published_at": x.get("date") or _extract_date(json.dumps(x)),
                    "source": "perplexity",
                    "score": 0.0,
                    "price_hint": _price_hint(snippet),
                    "tc": _trust_center(url),
                })
            
            log.info("✅ Perplexity: %d results (filtered %d NSFW/spam)", len(items), filtered_count)
            return items
            
        except requests.exceptions.Timeout:
            log.error("⏱️ Perplexity timeout after %ds", self.timeout)
            return []
        except requests.exceptions.RequestException as exc:
            log.error("❌ Perplexity request failed: %s", exc)
            return []
        except Exception as exc:
            log.error("❌ Perplexity error: %s", exc)
            return []
