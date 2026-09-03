#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""KIS-1265: Tool-Radar — Pflege-Überwachung der kuratierten Tool-Liste.

Gegenstück zum Förder-Radar für ``data/tools_seed.json`` (23 Tools mit
Preis, DSGVO-Status, Hosting, Prüfdatum). Der Quartals-Check
(scripts/check_tools_freshness.py) existierte, lief aber nie automatisch —
Stand 2026-09 waren 20 von 23 Tools nie verifiziert.

Prüft ohne Netz:
  stale     verified_at fehlt oder älter als --max-age Tage
Prüft mit --check-urls:
  dead_url  Produkt- oder Trust-URL nicht erreichbar
Mit --tavily (TAVILY_API_KEY): je Tool mit Befund bis zu drei aktuelle
Treffer zu Preis, Datenschutz und Hosting — Lesehinweise, keine Fakten.

Der Radar ändert keine Daten. Der Mensch prüft und setzt verified_at.

Usage:
  python scripts/tools_radar.py [--check-urls] [--tavily] [--max-age 120]
                                [--report tools_report.md]
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

TOOLS_PATH = REPO_ROOT / "data" / "tools_seed.json"
TAVILY_ENDPOINT = "https://api.tavily.com/search"


def _parse_date(value: Any) -> Optional[date]:
    s = str(value or "").strip()
    if not s:
        return None
    for fmt in ("%Y-%m-%d", "%d.%m.%Y"):
        try:
            return datetime.strptime(s, fmt).date()
        except ValueError:
            continue
    return None


def check_tool(tool: Dict[str, Any], today: date, max_age_days: int = 120) -> List[Dict[str, str]]:
    """Deterministische Checks für EIN Tool (ohne Netz). Testbar."""
    name = str(tool.get("name") or "?")
    verified = _parse_date(tool.get("verified_at"))
    if verified is None:
        return [{"type": "stale", "tool": name,
                 "detail": f"verified_at fehlt — nie verifiziert (Preis: {tool.get('price', '?')})"}]
    if today - verified > timedelta(days=max_age_days):
        return [{"type": "stale", "tool": name,
                 "detail": f"verified_at={verified.isoformat()} (> {max_age_days} Tage, "
                           f"Preis: {tool.get('price', '?')})"}]
    return []


def check_url(url: str, timeout: float = 15.0) -> Optional[str]:
    """None = erreichbar, sonst Fehlerbeschreibung. 403/405/429 = Bot-Schutz, gilt als erreichbar."""
    if not url or not str(url).startswith("http"):
        return "keine/ungültige URL"
    try:
        import requests
        resp = requests.get(url, timeout=timeout, allow_redirects=True,
                            headers={"User-Agent": "Mozilla/5.0 (ToolsRadar; +ki-sicherheit.jetzt)"})
        if resp.status_code < 400 or resp.status_code in (403, 405, 429):
            return None
        return f"HTTP {resp.status_code}"
    except Exception as exc:
        return f"{type(exc).__name__}"


def hersteller_domain(url: str) -> str:
    """Domain aus der Tool-URL, ohne "www." — die Suchbeschraenkung."""
    from urllib.parse import urlparse
    zerlegt = urlparse(str(url or ""))
    if zerlegt.scheme not in ("http", "https"):
        return ""
    host = (zerlegt.netloc or "").lower()
    return host[4:] if host.startswith("www.") else host


def build_candidate_query(name: str, year: int) -> str:
    """KIS-1273: ohne Jahreszahl und ohne Marketing-Woerter.

    Die alte Query lautete "<Name> Preise Preisaenderung Datenschutz AVV
    Hosting <Jahr>" und lief als freie Websuche. Bei mehrdeutigen
    Tool-Namen kam Unsinn heraus: Der Lauf vom 03.09.2026 lieferte fuer
    "Railway.app" Preise der indischen Eisenbahn und fuer "Perplexity
    API" die Fernwaermepreise der BEW Berlin. Die Suche laeuft jetzt
    zusaetzlich domainbeschraenkt (siehe tavily_candidates), deshalb
    reichen hier die Sachbegriffe.
    """
    clean = " ".join(str(name).split())
    return f"{clean} pricing plans privacy data processing agreement hosting"


def tavily_candidates(name: str, year: int, api_key: str, *, max_results: int = 3,
                      days: int = 60, timeout: float = 10.0,
                      domain: str = "") -> List[Dict[str, str]]:
    """Fail-open: jeder Fehler ergibt eine leere Liste. Basissuche (1 Credit).

    KIS-1273: Mit `domain` sucht Tavily nur auf der Herstellerseite. Ohne
    Domain wird gar nicht gesucht — ein Preis-Blog ist als Beleg fuer
    einen Report wertlos, und Rauschen kostet mehr Zeit als es spart.
    """
    if not api_key or not name or not domain:
        return []
    try:
        import requests
        resp = requests.post(
            TAVILY_ENDPOINT,
            json={"api_key": api_key, "query": build_candidate_query(name, year),
                  "search_depth": "basic", "max_results": max_results,
                  "include_domains": [domain],
                  "include_answer": False, "include_raw_content": False},
            timeout=timeout,
        )
        resp.raise_for_status()
        out = []
        for r in (resp.json() or {}).get("results") or []:
            url = str(r.get("url") or "").strip()
            title = " ".join(str(r.get("title") or "").split())[:120]
            if url and title:
                out.append({"title": title, "url": url})
        return out[:max_results]
    except Exception:
        return []


def load_tools() -> List[Dict[str, Any]]:
    if not TOOLS_PATH.exists():
        return []
    data = json.loads(TOOLS_PATH.read_text(encoding="utf-8"))
    return data if isinstance(data, list) else []


def run_radar(today: date, check_urls: bool = False, max_age_days: int = 120) -> List[Dict[str, str]]:
    findings: List[Dict[str, str]] = []
    for tool in load_tools():
        findings.extend(check_tool(tool, today, max_age_days=max_age_days))
        if check_urls:
            name = str(tool.get("name") or "?")
            for feld in ("url", "trust_url"):
                url = str(tool.get(feld) or "")
                if not url:
                    continue
                err = check_url(url)
                if err:
                    findings.append({"type": "dead_url", "tool": name,
                                     "detail": f"{feld}: {url}: {err}"})
    return findings


def collect_candidates(tools: List[Dict[str, Any]], findings: List[Dict[str, str]],
                       api_key: str, year: int, *, search=tavily_candidates,
                       limit: int = 12) -> Dict[str, List[Dict[str, str]]]:
    """Kandidaten nur für Tools mit Befund, höchstens `limit` Suchen je Lauf."""
    if not api_key:
        return {}
    domains = {str(t.get("name") or ""): hersteller_domain(t.get("url") or "")
               for t in tools}
    betroffen = []
    for f in findings:
        if f["tool"] not in betroffen:
            betroffen.append(f["tool"])
    out: Dict[str, List[Dict[str, str]]] = {}
    for name in betroffen[:limit]:
        hits = search(name, year, api_key, domain=domains.get(name, ""))
        if hits:
            out[name] = hits
    return out


def render_report(findings: List[Dict[str, str]], today: date,
                  candidates: Optional[Dict[str, List[Dict[str, str]]]] = None) -> str:
    lines = [f"# 🧰 Tool-Radar — {today.isoformat()}", ""]
    if not findings:
        lines.append("✅ Keine Befunde — alle Tools aktuell verifiziert und erreichbar.")
    else:
        lines.append(f"**{len(findings)} Befund(e)** — bitte Preis, DSGVO-/AVV-Status und "
                     "Hosting prüfen und `data/tools_seed.json` aktualisieren "
                     "(danach `verified_at` auf das Prüfdatum setzen):")
        lines.append("")
        lines.append("| Typ | Tool | Detail |")
        lines.append("|---|---|---|")
        order = {"dead_url": 0, "stale": 1}
        for f in sorted(findings, key=lambda x: order.get(x["type"], 9)):
            lines.append(f"| {f['type']} | {f['tool']} | {f['detail']} |")
        lines.append("")
        lines.append("_Hinweis: Preise werden bewusst NICHT automatisch übernommen — "
                     "Web-Treffer nennen Listenpreise, Aktionen oder falsche Währungen. "
                     "Der Radar meldet, der Mensch entscheidet._")
    if candidates:
        total = sum(len(v) for v in candidates.values())
        lines += ["", "## 🔍 Recherche-Kandidaten (Tavily, ungeprüft)", "",
                  f"**{total} Kandidat(en)** zu {len(candidates)} Tool(s) — nur Lesehinweise.", ""]
        for name in sorted(candidates):
            lines.append(f"**{name}**")
            for hit in candidates[name]:
                lines.append(f"- [{hit['title']}]({hit['url']})")
            lines.append("")
    return "\n".join(lines)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check-urls", action="store_true")
    ap.add_argument("--tavily", action="store_true")
    ap.add_argument("--max-age", type=int, default=120)
    ap.add_argument("--report", default="tools_report.md")
    args = ap.parse_args()

    today = date.today()
    findings = run_radar(today, check_urls=args.check_urls, max_age_days=args.max_age)
    candidates: Dict[str, List[Dict[str, str]]] = {}
    if args.tavily:
        candidates = collect_candidates(load_tools(), findings,
                                        os.getenv("TAVILY_API_KEY", ""), today.year)
    report = render_report(findings, today, candidates)
    Path(args.report).write_text(report, encoding="utf-8")
    print(report)
    print(f"\n::notice::Tool-Radar: {len(findings)} Befund(e), "
          f"{sum(len(v) for v in candidates.values())} Recherche-Kandidat(en)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
