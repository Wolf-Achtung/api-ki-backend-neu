# services/research_clients.py – Hybrid (Tavily + Perplexity)
import os, time, json, requests

TAVILY_API_KEY = os.getenv("TAVILY_API_KEY","")
PERPLEXITY_API_KEY = os.getenv("PERPLEXITY_API_KEY","")
TIMEOUT = float(os.getenv("RESEARCH_TIMEOUT","20"))

def tavily_search(q, num_results=10):
    if not TAVILY_API_KEY:
        return []
    url = "https://api.tavily.com/search"
    try:
        r = requests.post(url, json={"api_key": TAVILY_API_KEY, "query": q, "search_depth": "basic", "max_results": num_results}, timeout=TIMEOUT)
        r.raise_for_status()
        data = r.json() or {}
        return data.get("results", [])
    except Exception:
        return []

def perplexity_search(q, num_results=8):
    if not PERPLEXITY_API_KEY:
        return []
    url = "https://api.perplexity.ai/search"
    headers = {"Authorization": f"Bearer {PERPLEXITY_API_KEY}", "Content-Type":"application/json"}
    try:
        r = requests.post(url, headers=headers, json={"q": q, "size": num_results}, timeout=TIMEOUT)
        r.raise_for_status()
        data = r.json() or {}
        items = data.get("results", [])
        out = []
        for it in items:
            # normalize to fields: title, url, description
            out.append({"title": it.get("title") or it.get("source",""), "url": it.get("url") or "", "description": it.get("snippet") or ""})
        return out
    except Exception:
        return []

def hybrid_search(q, num_results=10):
    out = []
    out.extend(tavily_search(q, num_results))
    out.extend(perplexity_search(q, max(6, num_results//2)))
    # deduplicate by url
    seen = set(); uniq = []
    for x in out:
        url = (x.get("url") or "").strip()
        if not url or url in seen: 
            continue
        seen.add(url); uniq.append(x)
    return uniq[:max(num_results, 10)]
