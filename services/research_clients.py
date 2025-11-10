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


# --- Perplexity client (optional second research source) ---
import os, requests, time

def search_perplexity(query: str, k: int = 10, timeout: int = 40) -> list[dict]:
    """Query Perplexity Chat Completions API and extract citations as search results.
    Returns list of dicts with keys: title, url, source, score(optional).
    """
    api_key = os.getenv("PERPLEXITY_API_KEY", "")
    if not api_key:
        return []
    url = os.getenv("PERPLEXITY_API_URL", "https://api.perplexity.ai/chat/completions")
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    payload = {
        "model": os.getenv("PERPLEXITY_MODEL","sonar-pro"),
        "temperature": float(os.getenv("PERPLEXITY_TEMPERATURE","0.0")),
        "messages": [
            {"role": "system", "content": "Act as a research meta-search. Return concise answer and cite sources."},
            {"role": "user", "content": f"Find high-quality, current sources for: {query}. Return up to {k} citations with title and URL."}
        ]
    }
    try:
        r = requests.post(url, headers=headers, json=payload, timeout=timeout)
        r.raise_for_status()
        data = r.json()
    except Exception:
        return []
    citations = []
    # Try typical locations for citation links
    try:
        # Some responses include 'citations' at top level:
        for c in data.get("citations") or []:
            if isinstance(c, dict):
                citations.append({"title": c.get("title") or c.get("url") or "", "url": c.get("url") or "", "source": "perplexity"})
        # Or inside the first choice message content as JSON-like text
        if not citations:
            choice = (data.get("choices") or [{}])[0]
            msg = (choice.get("message") or {})
            content = (msg.get("content") or "") if isinstance(msg, dict) else ""
            # naive URL scrape
            urls = re.findall(r"https?://[^\s)]+", content)
            for u in urls:
                citations.append({"title": u, "url": u, "source": "perplexity"})
    except Exception:
        pass
    # Deduplicate
    seen = set()
    out = []
    for item in citations:
        href = (item.get("url") or "").strip()
        if not href or href in seen:
            continue
        seen.add(href)
        out.append(item)
        if len(out) >= k:
            break
    return out
