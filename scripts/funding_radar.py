#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""KIS-1263: Förder-Radar — automatisierte Pflege-Überwachung der kuratierten
Förderprogramm-Daten.

Warum kein Voll-Automatismus wie bei den Tools: Tool-Empfehlungen kommen bei
jeder Report-Generierung live aus der Recherche (Tavily/Perplexity) — ein
veralteter Tool-Preis ist harmlos. Förderquoten, Höchstbeträge und Fristen
sind dagegen ZUSAGEN mit finanzieller Tragweite in einer GF-Vorlage; LLM- und
Web-Recherche halluziniert Prozentsätze und liest Marketing-Seiten statt
Richtlinien. Deshalb bleibt die Programmliste kuratiert (Mensch entscheidet),
aber die ÜBERWACHUNG läuft maschinell: Dieser Radar prüft wöchentlich per CI

  dead_url       Programm-URL nicht mehr erreichbar (Programm evtl. eingestellt)
  expired        Frist abgelaufen oder status != active
  blacklisted    Programm steht auf der Runtime-Blacklist (b25_enforcer),
                 liegt aber noch im Datenbestand
  stale          verified_at fehlt oder älter als --max-age Tage

und öffnet bei Befunden ein GitHub-Issue (Workflow funding-radar.yml).
Der Mensch prüft die Richtlinie und aktualisiert die JSON — der Radar sorgt
dafür, dass das nie vergessen wird.

Usage:
  python scripts/funding_radar.py [--check-urls] [--max-age 120]
                                  [--report radar_report.md] [--fail-on-findings]
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

CORE_PATH = REPO_ROOT / "data" / "funding_programmes_core_2025.json"
FALLBACK_PATH = REPO_ROOT / "data" / "funding_programs.json"

# Fristen-Werte, die "kein festes Enddatum" bedeuten
_OPEN_DEADLINES = {"", "none", "laufend", "offen", "rolling", "ongoing", "k.a.", "n/a"}


def _parse_date(value: Any) -> Optional[date]:
    s = str(value or "").strip()
    if not s or s.lower() in _OPEN_DEADLINES:
        return None
    for fmt in ("%d.%m.%Y", "%Y-%m-%d", "%m/%Y", "%d.%m.%y"):
        try:
            return datetime.strptime(s, fmt).date()
        except ValueError:
            continue
    return None


def _blacklist_terms() -> List[str]:
    """Nur die Basis-Blacklist (tote Programme). Digitalbonus Bayern steht
    im Enforcer bedingt auf der Liste — es wird ausserhalb Bayerns
    gefiltert, ist aber kein totes Programm (KIS-1296: Laufzeit bis
    31.12.2027, am 05.09.2026 belegt)."""
    try:
        from b25_enforcer import _FUNDING_BLACKLIST_BASE
        return [t.lower() for t in _FUNDING_BLACKLIST_BASE]
    except Exception:
        try:
            from b25_enforcer import FUNDING_BLACKLIST
            return [t.lower() for t in FUNDING_BLACKLIST if "digitalbonus" not in t.lower() and "digital-bonus" not in t.lower()]
        except Exception:
            return ["go-digital"]


# ---------------------------------------------------------------------------
# KIS-1265: Tavily-Kandidaten — Recherche-Hinweise, keine Datenänderung
# ---------------------------------------------------------------------------

TAVILY_ENDPOINT = "https://api.tavily.com/search"


def build_candidate_query(name: str, year: int) -> str:
    """Suchanfrage für Änderungen an einem Programm — Frist, Stopp, Neuauflage."""
    clean = " ".join(str(name).replace("–", " ").replace("—", " ").split())
    return f"{clean} Förderprogramm {year} Frist Antragsstopp Änderung"


def tavily_candidates(name: str, year: int, api_key: str, *,
                      max_results: int = 3, days: int = 45,
                      timeout: float = 10.0) -> List[Dict[str, str]]:
    """Bis zu drei aktuelle Treffer zu einem Programm — Hinweise für den
    Menschen, der die Richtlinie prüft. Der Radar ändert keine Daten.

    Fail-open: Jeder Fehler ergibt eine leere Liste. Basissuche (1 Credit)
    statt „advanced": Es geht um Hinweise, nicht um Volltext.
    """
    if not api_key or not name:
        return []
    try:
        import requests
        resp = requests.post(
            TAVILY_ENDPOINT,
            json={"api_key": api_key, "query": build_candidate_query(name, year),
                  "search_depth": "basic", "max_results": max_results, "days": days,
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


def check_program(prog: Dict[str, Any], today: date, max_age_days: int = 120,
                  blacklist: Optional[List[str]] = None) -> List[Dict[str, str]]:
    """Deterministische Checks für EIN Programm (ohne Netz). Testbar."""
    findings: List[Dict[str, str]] = []
    name = str(prog.get("title") or prog.get("name") or "?")
    bl = blacklist if blacklist is not None else _blacklist_terms()

    status = str(prog.get("status") or "active").lower()
    # Explizit archivierte Einträge (status=expired/discontinued) sind
    # DOKUMENTIERTER Zustand — die Pflege ist erledigt, kein Befund.
    # Konsumenten filtern auf status=active; der Eintrag bleibt als
    # kuratierte Historie erhalten.
    if status in ("expired", "discontinued", "eingestellt", "archived"):
        return []

    # KIS-1268: "paused" ist ebenfalls dokumentierter Zustand — ein
    # befristeter Antragsstopp, kein Pflegerückstand (ZIM seit 07.07.2026).
    # Anders als bei "expired" kommt das Programm aber zurück. Damit der
    # Eintrag nicht für immer verstummt, trägt er ein Wiedervorlage-Datum:
    # Ab diesem Tag meldet der Radar ihn wieder zur Prüfung.
    if status == "paused":
        recheck = _parse_date(str(prog.get("recheck_after") or "").strip())
        if recheck and recheck <= today:
            return [{"type": "recheck", "program": name,
                     "detail": f"Antragsstopp seit Wiedervorlage {recheck} — "
                               "prüfen, ob wieder beantragbar (status=active)"}]
        return []
    deadline_raw = str(prog.get("deadline") or "").strip()
    deadline = _parse_date(deadline_raw)
    if status not in ("active", ""):
        findings.append({"type": "expired", "program": name,
                         "detail": f"status={status}"})
    elif deadline_raw.upper() == "ABGELAUFEN" or (deadline and deadline < today):
        findings.append({"type": "expired", "program": name,
                         "detail": f"deadline={deadline_raw}"})

    lname = name.lower()
    hits = [t for t in bl if t and t in lname]
    if hits:
        findings.append({"type": "blacklisted", "program": name,
                         "detail": f"Runtime-Blacklist-Treffer: {hits[0]} — "
                                   "Eintrag aus dem Datenbestand entfernen/ersetzen"})

    verified = _parse_date(prog.get("verified_at"))
    if verified is None:
        findings.append({"type": "stale", "program": name,
                         "detail": "verified_at fehlt — nie verifiziert"})
    elif today - verified > timedelta(days=max_age_days):
        findings.append({"type": "stale", "program": name,
                         "detail": f"verified_at={verified.isoformat()} "
                                   f"(> {max_age_days} Tage)"})
    return findings


def check_url(url: str, timeout: float = 15.0) -> Optional[str]:
    """Netz-Check: None = erreichbar, sonst Fehlerbeschreibung.

    403/405/429 gelten als erreichbar (Bot-Schutz der Förderportale)."""
    if not url or not url.startswith("http"):
        return "keine/ungültige URL"
    try:
        import requests
        resp = requests.get(url, timeout=timeout, allow_redirects=True,
                            headers={"User-Agent": "Mozilla/5.0 (FundingRadar; +ki-sicherheit.jetzt)"})
        if resp.status_code < 400 or resp.status_code in (403, 405, 429):
            return None
        return f"HTTP {resp.status_code}"
    except Exception as exc:
        return f"{type(exc).__name__}"


def load_programs() -> List[Dict[str, Any]]:
    programs: List[Dict[str, Any]] = []
    for path, source in ((CORE_PATH, "core_2025"), (FALLBACK_PATH, "fallback")):
        if not path.exists():
            continue
        data = json.loads(path.read_text(encoding="utf-8"))
        entries = data if isinstance(data, list) else (
            data.get("programmes") or data.get("programs") or [])
        for p in entries:
            p["_source"] = source
            programs.append(p)
    return programs


def run_radar(today: date, check_urls: bool = False,
              max_age_days: int = 120) -> List[Dict[str, str]]:
    findings: List[Dict[str, str]] = []
    blacklist = _blacklist_terms()
    for prog in load_programs():
        fs = check_program(prog, today, max_age_days=max_age_days, blacklist=blacklist)
        for f in fs:
            f["source"] = prog.get("_source", "?")
        findings.extend(fs)
        if check_urls:
            err = check_url(str(prog.get("url") or ""))
            if err:
                findings.append({"type": "dead_url", "source": prog.get("_source", "?"),
                                 "program": str(prog.get("title") or prog.get("name") or "?"),
                                 "detail": f"{prog.get('url')}: {err}"})
    return findings


def collect_candidates(programs: List[Dict[str, Any]], findings: List[Dict[str, str]],
                       api_key: str, year: int, *, scan_all: bool = False,
                       search=tavily_candidates) -> Dict[str, List[Dict[str, str]]]:
    """Tavily-Kandidaten je Programm — standardmäßig nur für Programme mit
    Befund (begrenzt die Kosten auf eine Handvoll Suchen pro Lauf), mit
    scan_all für alle aktiven Programme (Monatsroutine)."""
    if not api_key:
        return {}
    betroffen = {f["program"] for f in findings}
    out: Dict[str, List[Dict[str, str]]] = {}
    for prog in programs:
        name = str(prog.get("title") or prog.get("name") or "").strip()
        status = str(prog.get("status") or "active").lower()
        if not name or status in ("expired", "discontinued", "eingestellt", "archived"):
            continue
        if not scan_all and name not in betroffen:
            continue
        hits = search(name, year, api_key)
        if hits:
            out[name] = hits
    return out


def render_report(findings: List[Dict[str, str]], today: date,
                  candidates: Optional[Dict[str, List[Dict[str, str]]]] = None) -> str:
    lines = [f"# 🔎 Förder-Radar — {today.isoformat()}", ""]
    if not findings:
        lines.append("✅ Keine Befunde — alle Programme aktuell verifiziert und erreichbar.")
        lines.extend(_render_candidates(candidates))
        return "\n".join(lines)
    lines.append(f"**{len(findings)} Befund(e)** — bitte Richtlinien prüfen und "
                 "`data/funding_programmes_core_2025.json` aktualisieren "
                 "(danach `verified_at` auf das Prüfdatum setzen):")
    lines.append("")
    lines.append("| Typ | Programm | Quelle | Detail |")
    lines.append("|---|---|---|---|")
    order = {"blacklisted": 0, "expired": 1, "dead_url": 2, "stale": 3}
    for f in sorted(findings, key=lambda x: order.get(x["type"], 9)):
        lines.append(f"| {f['type']} | {f['program']} | {f.get('source', '?')} | {f['detail']} |")
    lines.append("")
    lines.append("_Hinweis: Förderquoten/Höchstbeträge sind bewusst NICHT "
                 "automatisch aktualisiert — Prozentsätze aus Web-Recherche sind "
                 "nicht richtliniensicher. Der Radar meldet, der Mensch entscheidet._")
    lines.extend(_render_candidates(candidates))
    return "\n".join(lines)


def _render_candidates(candidates: Optional[Dict[str, List[Dict[str, str]]]]) -> List[str]:
    """KIS-1265: Recherche-Hinweise (Tavily) als eigener Abschnitt —
    Lesestoff für die Prüfung, ausdrücklich keine verifizierten Fakten."""
    if not candidates:
        return []
    total = sum(len(v) for v in candidates.values())
    lines = ["", "## 🔍 Recherche-Kandidaten (Tavily, ungeprüft)", "",
             f"**{total} Kandidat(en)** zu {len(candidates)} Programm(en) — "
             "aktuelle Treffer der letzten Wochen. Nur Lesehinweise: Fristen und "
             "Quoten weiterhin gegen die Richtlinie prüfen.", ""]
    for name in sorted(candidates):
        lines.append(f"**{name}**")
        for hit in candidates[name]:
            lines.append(f"- [{hit['title']}]({hit['url']})")
        lines.append("")
    return lines


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check-urls", action="store_true")
    ap.add_argument("--max-age", type=int, default=120)
    ap.add_argument("--report", default="radar_report.md")
    ap.add_argument("--fail-on-findings", action="store_true")
    # KIS-1265: Tavily-Kandidaten. Ohne TAVILY_API_KEY still übersprungen.
    ap.add_argument("--tavily", action="store_true",
                    help="Recherche-Kandidaten für Programme mit Befund anhängen")
    ap.add_argument("--tavily-all", action="store_true",
                    help="Recherche-Kandidaten für ALLE aktiven Programme (Monatsroutine)")
    args = ap.parse_args()

    today = date.today()
    findings = run_radar(today, check_urls=args.check_urls, max_age_days=args.max_age)

    candidates: Dict[str, List[Dict[str, str]]] = {}
    if args.tavily or args.tavily_all:
        import os
        candidates = collect_candidates(load_programs(), findings,
                                        os.getenv("TAVILY_API_KEY", ""), today.year,
                                        scan_all=args.tavily_all)

    report = render_report(findings, today, candidates)
    Path(args.report).write_text(report, encoding="utf-8")
    print(report)
    print(f"\n::notice::Förder-Radar: {len(findings)} Befund(e), "
          f"{sum(len(v) for v in candidates.values())} Recherche-Kandidat(en)")
    if findings and args.fail_on_findings:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
