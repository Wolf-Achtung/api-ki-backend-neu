# -*- coding: utf-8 -*-
from __future__ import annotations
import os
import requests
from typing import List, Dict, Any

TAVILY_API_KEY = os.getenv("TAVILY_API_KEY", "")

def tavily_search(queries: List[str], max_items: int = 8) -> List[Dict[str, Any]]:
    if not TAVILY_API_KEY:
        return []
    headers = {"Content-Type": "application/json", "Authorization": f"Bearer {TAVILY_API_KEY}"}
    results: List[Dict[str, Any]] = []
    for q in queries:
        payload = {"api_key": TAVILY_API_KEY, "query": q, "search_depth": "advanced", "max_results": max_items}
        resp = requests.post("https://api.tavily.com/search", json=payload, headers=headers, timeout=30)
        if resp.ok:
            data = resp.json()
            for r in data.get("results", []):
                results.append({"title": r.get("title"), "url": r.get("url"), "snippet": r.get("content")})
    # Deduplicate by url
    seen = set()
    uniq: List[Dict[str, Any]] = []
    for it in results:
        if it["url"] in seen:
            continue
        seen.add(it["url"])
        uniq.append(it)
    return uniq[:max_items]
