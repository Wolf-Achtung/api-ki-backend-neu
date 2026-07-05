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
    try:
        from b25_enforcer import FUNDING_BLACKLIST
        return [t.lower() for t in FUNDING_BLACKLIST]
    except Exception:
        return ["go-digital"]


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


def render_report(findings: List[Dict[str, str]], today: date) -> str:
    lines = [f"# 🔎 Förder-Radar — {today.isoformat()}", ""]
    if not findings:
        lines.append("✅ Keine Befunde — alle Programme aktuell verifiziert und erreichbar.")
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
    return "\n".join(lines)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check-urls", action="store_true")
    ap.add_argument("--max-age", type=int, default=120)
    ap.add_argument("--report", default="radar_report.md")
    ap.add_argument("--fail-on-findings", action="store_true")
    args = ap.parse_args()

    today = date.today()
    findings = run_radar(today, check_urls=args.check_urls, max_age_days=args.max_age)
    report = render_report(findings, today)
    Path(args.report).write_text(report, encoding="utf-8")
    print(report)
    print(f"\n::notice::Förder-Radar: {len(findings)} Befund(e)")
    if findings and args.fail_on_findings:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
