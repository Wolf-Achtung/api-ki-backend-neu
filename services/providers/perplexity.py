# -*- coding: utf-8 -*-
from __future__ import annotations
import os
import requests
from typing import List, Dict, Any

PPLX_API_KEY = os.getenv("PPLX_API_KEY", "")

def perplexity_search(queries: List[str], max_items: int = 8) -> List[Dict[str, Any]]:
    if not PPLX_API_KEY:
        return []
    headers = {"Authorization": f"Bearer {PPLX_API_KEY}", "Content-Type": "application/json"}
    results: List[Dict[str, Any]] = []
    for q in queries:
        payload = {
            "model": "sonar-small-online",
            "messages": [{"role": "system", "content": "Return 5 concise links with single-sentence summaries."},
                         {"role": "user", "content": q}],
            "return_images": False,
            "top_k": 5,
        }
        resp = requests.post("https://api.perplexity.ai/chat/completions", json=payload, headers=headers, timeout=45)
        if not resp.ok:
            continue
        data = resp.json()
        # The API may include 'sources' in citations; we normalize to list of dicts
        msg = (data.get("choices") or [{}])[0].get("message", {}).get("content", "")
        # very lightweight link extractor
        import re
        for m in re.finditer(r"(https?://[^\s)]+)", msg):
            url = m.group(1)
            if url:
                results.append({"title": None, "url": url, "snippet": None})
    # Deduplicate
    seen = set(); uniq = []
    for it in results:
        if it["url"] in seen:
            continue
        seen.add(it["url"]); uniq.append(it)
    return uniq[:max_items]
