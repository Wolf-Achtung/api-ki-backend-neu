# -*- coding: utf-8 -*-
from __future__ import annotations
import os, json, logging, requests
from typing import List, Dict

LOGGER = logging.getLogger(__name__)
PPLX_API_KEY = os.getenv("PERPLEXITY_API_KEY", "")
PPLX_ENDPOINT = os.getenv("PPLX_ENDPOINT", "https://api.perplexity.ai/chat/completions")
PPLX_MODEL = os.getenv("PPLX_MODEL", "llama-3.1-sonar-large-128k-online")

SYSTEM = "You are a research assistant. Return concise JSON with a list of items [{title, url, summary}]. No markdown."
USER_TMPL = "Find the most recent (last {days} days) {topic}. Return JSON only."

def _post_json(url: str, payload: dict, timeout: int = 45) -> dict:
    headers = {"Content-Type":"application/json","Accept":"application/json","Authorization": f"Bearer {PPLX_API_KEY}" if PPLX_API_KEY else ""}
    resp = requests.post(url, headers=headers, data=json.dumps(payload), timeout=timeout)
    resp.raise_for_status()
    return resp.json()

def search(topic: str, days: int = 30, max_items: int = 8) -> List[Dict]:
    if not PPLX_API_KEY:
        LOGGER.warning("PERPLEXITY_API_KEY not set")
        return []
    messages = [{"role":"system","content":SYSTEM},{"role":"user","content":USER_TMPL.format(days=max(1,days), topic=topic)}]
    payload = {"model": PPLX_MODEL, "messages": messages, "temperature": 0.1}
    try:
        data = _post_json(PPLX_ENDPOINT, payload)
        content = data.get("choices", [{}])[0].get("message", {}).get("content", "")
        try:
            obj = json.loads(content)
            items = obj if isinstance(obj, list) else obj.get("items", [])
        except Exception:
            start, end = content.find("["), content.rfind("]")
            items = json.loads(content[start:end+1]) if start != -1 and end != -1 else []
        out = []
        for it in items[:max_items]:
            out.append({"title": it.get("title",""), "url": it.get("url",""), "content": it.get("summary",""), "source":"perplexity"})
        return out
    except Exception as exc:
        LOGGER.error("Perplexity search failed: %s", exc)
        return []
