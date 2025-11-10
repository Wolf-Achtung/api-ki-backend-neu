
# -*- coding: utf-8 -*-
"""
services.research_pipeline – Hybrid Research (Tavily + Perplexity) with Redis cache.
Generates HTML blocks for Tools and Funding tables.

Outputs (dict):
- TOOLS_TABLE_HTML (optional)
- FUNDING_TABLE_HTML
- NEWS_BOX_HTML (optional)
- last_updated (ISO date)

This implementation degrades gracefully if APIs are missing: it will use any
seed JSON files in data/funding_programs.json and data/tools_seed.json.
"""
from __future__ import annotations
import os, re, json, html, time
from . import research_clients as rc
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import urlparse

import requests

from .cache import cache  # type: ignore

OFFICIAL_DOMAINS = {
    # Federal & EU
    "foerderdatenbank.de", "bmwk.de", "bund.de", "europa.eu", "ec.europa.eu", "commission.europa.eu",
    # Berlin
    "berlin.de", "service.berlin.de", "ibb.de", "technologiestiftung-berlin.de",
    # Bavaria
    "bayern.de", "stmwi.bayern.de", "bayerisches-staatsministerium.de", "bayern-innovativ.de",
}
MEDIA_DOMAINS = {"heise.de", "handelsblatt.com", "t3n.de", "faz.net", "gruenderszene.de"}

def _domain_rank(href: str) -> Tuple[int, str]:
    d = urlparse(href).netloc.lower()
    if any(d == x or d.endswith("." + x) for x in OFFICIAL_DOMAINS):
        return (0, d)
    if any(d == x or d.endswith("." + x) for x in MEDIA_DOMAINS):
        return (1, d)
    return (2, d)

def _now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d")

# ---------------- Tavily / Perplexity wrappers ----------------
def _tavily_search(query: str, max_results: int = 8) -> List[Dict[str, Any]]:
    key = os.getenv("TAVILY_API_KEY", "").strip()
    if not key:
        return []
    try:
        r = requests.post("https://api.tavily.com/search", json={
            "api_key": key, "query": query, "max_results": max_results, "include_answer": False,
            "include_raw_content": False, "search_depth": "basic"
        }, timeout=20)
        r.raise_for_status()
        data = r.json()
        results = []
        for item in data.get("results", []):
            results.append({
                "title": item.get("title", ""),
                "url": item.get("url", ""),
                "snippet": item.get("content", "")[:400]
            })
        return results
    except Exception:
        return []

def _pplx_search(query: str, max_results: int = 5) -> List[Dict[str, Any]]:
    # Simple "quick answer" extraction using Perplexity chat endpoint
    key = os.getenv("PERPLEXITY_API_KEY", "").strip()
    if not key:
        return []
    try:
        # Ask Perplexity to list relevant official links for the query
        payload = {
            "model": os.getenv("PERPLEXITY_MODEL", "pplx-70b-online"),
            "messages": [
                {"role": "system", "content": "Listiere 3-6 offizielle Links (mit Titel) zum Thema. Antworte als JSON-Liste [{\"title\":\"...\",\"url\":\"...\"}] ohne weiteren Text."},
                {"role": "user", "content": query}
            ],
            "temperature": 0.0,
            "max_tokens": 500
        }
        r = requests.post("https://api.perplexity.ai/chat/completions",
                          headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
                          json=payload, timeout=25)
        r.raise_for_status()
        content = r.json()["choices"][0]["message"]["content"]
        # Try to parse as JSON; if not, fall back to regex
        try:
            items = json.loads(content)
            results = []
            for it in items:
                if isinstance(it, dict) and it.get("url"):
                    results.append({"title": it.get("title",""), "url": it.get("url"), "snippet": ""})
            return results[:max_results]
        except Exception:
            # very simple fallback: extract links
            links = re.findall(r'https?://\S+', content)[:max_results]
            return [{"title": "", "url": u, "snippet": ""} for u in links]
    except Exception:
        return []

# ---------------- Helpers ----------------
def _unique_by_url(items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    seen = set(); out = []
    for it in items:
        u = it.get("url","").strip()
        if not u or u in seen:
            continue
        seen.add(u); out.append(it)
    return out

def _load_seed_json(path: str) -> Dict[str, Any]:
    if os.path.exists(path):
        try:
            with open(path, "r", encoding="utf-8") as fh:
                return json.load(fh)
        except Exception:
            pass
    alt = os.path.join("/mnt/data", os.path.basename(path))
    if os.path.exists(alt):
        try:
            with open(alt, "r", encoding="utf-8") as fh:
                return json.load(fh)
        except Exception:
            pass
    return {}

def _fit_for_size(text: str, company_size: str) -> str:
    t = (text or "").lower()
    fit = []
    if "kmu" in t or "kleine und mittlere" in t or "kmus" in t:
        fit.append("KMU")
    if "freiberuf" in t or "solo" in t or "einzelunternehmer" in t or "gründung" in t:
        fit.append("Solo")
    if "unter 10" in t or "bis 10" in t or "mikro" in t or "kleinstunternehmen" in t:
        fit.append("Team")
    # default heuristic if nothing found
    if not fit:
        fit = ["KMU"]
        if company_size == "solo":
            fit = ["Solo", "Team"]
        elif company_size == "team":
            fit = ["Team", "KMU"]
    return "/".join(fit)

def _extract_deadline(snippet: str) -> str:
    m = re.search(r"(?:(?:Frist|Deadline|Einreichung)\D{0,20})(\d{1,2}\.\d{1,2}\.\d{2,4})", snippet or "", flags=re.IGNORECASE)
    if m:
        return m.group(1)
    # fallbacks
    if "fortlaufend" in (snippet or "").lower() or "laufend" in (snippet or "").lower():
        return "laufend"
    return "—"

def _prio_score(fit: str, deadline: str, href: str) -> int:
    score = 50
    # fit boost
    if "Solo" in fit: score += 10
    if "Team" in fit: score += 8
    if "KMU" in fit: score += 6
    # official domain boost
    score += max(0, 12 - _domain_rank(href)[0] * 6)
    # deadline proximity
    try:
        if deadline and deadline not in ("—", "laufend"):
            from datetime import datetime as _dt
            d = _dt.strptime(deadline, "%d.%m.%Y")
            days = (d - _dt.now()).days
            if days <= 0:
                score -= 10
            elif days <= 30:
                score += 12
            elif days <= 90:
                score += 6
    except Exception:
        pass
    return score

def _render_funding_table(rows: List[Dict[str, str]], state_label: str) -> str:
    head = "<thead><tr><th>Prio</th><th>Programm</th><th>Förderung</th><th>Zielgruppe</th><th>Deadline</th><th>Fit</th><th>Quelle</th></tr></thead>"
    body_rows = []
    for r in rows:
        pr = html.escape(str(r.get("prio","")))
        name = html.escape(r.get("title",""))
        foerd = html.escape(r.get("funding",""))
        ziel = html.escape(r.get("target",""))
        dl = html.escape(r.get("deadline",""))
        fit = html.escape(r.get("fit",""))
        url = r.get("url","")
        link = f"<a href='{html.escape(url)}' target='_blank' rel='noopener'>Link</a>" if url else ""
        body_rows.append(f"<tr><td>{pr}</td><td><strong>{name or '—'}</strong></td><td>{foerd or '—'}</td><td>{ziel or '—'}</td><td>{dl or '—'}</td><td>{fit or '—'}</td><td>{link}</td></tr>")
    body = "<tbody>" + "".join(body_rows) + "</tbody>"
    stand = f"<div class='stand'>Stand: {_now_iso()} · Region: {html.escape(state_label)}</div>"
    return f"<div class='stand-hint'>{stand}</div><table class='table'>{head}{body}</table>"

def _state_label(code_or_label: str) -> str:
    m = {
        "be": "Berlin", "by": "Bayern",
        "bw": "Baden-Württemberg", "he": "Hessen", "nw": "Nordrhein-Westfalen"
    }
    c = (code_or_label or "").strip().lower()
    return m.get(c, code_or_label if code_or_label else "—")

# ---------------- Funding research ----------------
def _research_funding(state_code: str, company_size: str) -> Dict[str, Any]:
    cache_key = f"funding:{state_code}:{company_size}".lower()
    cached = cache.get_json(cache_key)
    if cached:
        return cached

    state_label = _state_label(state_code)
    # Build queries for state + federal + EU
    base_queries = [
        f"{state_label} Förderung Digitalisierung KI KMU Frist",
        f"{state_label} Zuschuss Beratung Digitalisierung KMU Frist",
        "BMWK go-digital Frist KMU",
        "ZIM Mittelstand Förderprogramm Frist",
        "EU Förderung Digitalisierung KMU call deadline"
    ]
    q_extra_be = ["IBB Pro FIT Frist Berlin", "Transfer BONUS Berlin Frist", "Coaching BONUS Berlin Frist"]
    q_extra_by = ["Digitalbonus Bayern Frist", "Bayern Innovativ Förderung Frist", "BayTOU Frist"]
    if state_label.lower().startswith("berlin"):
        base_queries.extend(q_extra_be)
    if state_label.lower().startswith("bayern"):
        base_queries.extend(q_extra_by)

    results: List[Dict[str, Any]] = []
    for q in base_queries:
        results.extend(_tavily_search(q, max_results=6))
        results.extend(_pplx_search(q, max_results=4))

    # dedupe & rank
    results = _unique_by_url(results)
    # keep only official/credible first
    results.sort(key=lambda r: _domain_rank(r.get("url","")))

    rows: List[Dict[str, str]] = []
    for it in results[:40]:
        url = it.get("url","")
        title = (it.get("title") or urlparse(url).netloc).strip()
        snip = (it.get("snippet") or "").strip()

        # quick heuristics
        fit = _fit_for_size(f"{title} {snip}", company_size)
        deadline = _extract_deadline(snip)
        target = "KMU" if "KMU" in (title + snip) else "Unternehmen"
        foerd = "Zuschuss/Programm"
        prio = _prio_score(fit, deadline, url)

        rows.append({
            "title": title,
            "funding": foerd,
            "target": target,
            "deadline": deadline,
            "fit": fit,
            "url": url,
            "prio": str(prio)
        })

    # Fallback to seed json if nothing found
    if not rows:
        seed = _load_seed_json(os.getenv("FUNDING_SEED_PATH", "data/funding_programs.json"))
        for item in seed.get(state_label.lower(), []):
            rows.append({
                "title": item.get("title",""),
                "funding": item.get("funding",""),
                "target": item.get("target",""),
                "deadline": item.get("deadline","—"),
                "fit": item.get("fit","KMU"),
                "url": item.get("url",""),
                "prio": str(item.get("priority", 50))
            })

    # Sort by priority desc
    rows.sort(key=lambda r: int(r.get("prio","0")), reverse=True)

    html_block = _render_funding_table(rows[:12], state_label)

    out = {
        "FUNDING_TABLE_HTML": html_block,
        "last_updated": _now_iso()
    }
    cache.set_json(cache_key, out, ttl=int(os.getenv("CACHE_TTL_FUNDING", "43200")))  # 12h
    return out

# ---------------- Tools research (optional / stub) ----------------
def _research_tools(branch_label: str) -> Dict[str, Any]:
    # Optional: left as simple stub – can be extended similarly.
    return {"TOOLS_TABLE_HTML": ""}

# ---------------- News box ----------------
def _build_news_box() -> str:
    # Very small static "news/changes" box; can be filled by research as needed.
    items = [
        "EU‑AI‑Act: gestaffelte Anwendung 2025–2027 (Risk‑Management, Logging, Monitoring).",
        "BMWK „go‑digital“: Modul KI/Datenschutz in Prüfung – Fristen je nach Autorisierungspartner.",
        "Berlin/IBB: Programme wie Pro‑FIT/Transfer‑BONUS regelmäßig mit Batches – Fristen prüfen."
    ]
    lis = "".join(f"<li>{html.escape(x)}</li>" for x in items)
    return f"<aside class='card'><h3>News & Änderungen</h3><ul>{lis}</ul><div class='stand'>Stand: {_now_iso()}</div></aside>"

# ---------------- Public entry point ----------------
def run_research(answers: Dict[str, Any]) -> Dict[str, Any]:
    state_code = (answers.get("bundesland") or answers.get("BUNDESLAND_LABEL") or "").strip().lower()
    company_size = (answers.get("unternehmensgroesse") or answers.get("UNTERNEHMENSGROESSE_LABEL") or "").strip().lower()
    branch_label = (answers.get("BRANCHE_LABEL") or answers.get("branche") or "")

    out: Dict[str, Any] = {}
    try:
        out.update(_research_funding(state_code=state_code, company_size=company_size))
    except Exception:
        # never break report generation
        out["FUNDING_TABLE_HTML"] = "<p>Hinweis: Förderprogramme konnten nicht automatisch recherchiert werden.</p>"
        out["last_updated"] = _now_iso()

    try:
        out.update(_research_tools(branch_label))
    except Exception:
        pass

    try:
        out["NEWS_BOX_HTML"] = _build_news_box()
    except Exception:
        pass

    return out


def _merge_results(*lists):
    seen = set()
    out = []
    for lst in lists:
        for item in (lst or []):
            href = (item.get("url") or "").strip()
            if not href or href in seen:
                continue
            seen.add(href)
            out.append(item)
    return out
