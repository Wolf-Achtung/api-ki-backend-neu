# file: services/ai_act_table.py
# -*- coding: utf-8 -*-
from __future__ import annotations
"""Erzeugt AI‑Act‑Timeline (HTML + CSV) + 2 konkrete 30‑Tage‑Tasks (ohne LLM)."""
from datetime import datetime, timedelta
from typing import Any, Dict, List, Tuple, Optional
import csv, io, re

_MONTHS = {"januar":1,"februar":2,"märz":3,"maerz":3,"april":4,"mai":5,"juni":6,"juli":7,
           "august":8,"september":9,"oktober":10,"november":11,"dezember":12}
_DEFAULT: List[Tuple[str,str,str,str,str]] = [
    ("2025-02-02","Kap. I–II / Verbote","Verbote unzulässiger Systeme; Allg. Bestimmungen wirksam","alle","Blacklist & Transparenzhinweise in Richtlinie"),
    ("2025-08-02","GPAI & Governance","GPAI‑Pflichten, Governance & Durchsetzung greifen","Anbieter/Nutzer GPAI","Modellklasse klären; Hinweise/Policy ergänzen"),
    ("2026-08-02","Hochrisiko‑Kern","Pflichten für Hochrisiko‑KI (Doku, Logging, POMM) gelten","Anbieter/Betreiber HR","Risikomanagement & Nachweise aufsetzen"),
    ("2027-08-02","Erweiterte Kategorien","Erweiterte/Anhang‑Regeln vollständig anzuwenden","betroffene Kategorien","Konformitätsbewertung/Registry (falls zutreffend)"),
]
_DATE_RE = re.compile(r'(\d{1,2})\.\s*([A-Za-zäöüÄÖÜß]+)\s*(20\d{2})')

def _fmt(iso: str) -> str:
    return datetime.strptime(iso, "%Y-%m-%d").strftime("%d.%m.%Y")

def _parse_dates(txt: str) -> List[str]:
    out: List[str]=[]
    for m in _DATE_RE.finditer(txt or ""):
        day=int(m.group(1)); month=_MONTHS.get(m.group(2).lower().replace("ä","ae").replace("ö","oe").replace("ü","ue").replace("ß","ss"))
        year=int(m.group(3))
        if month: out.append(datetime(year,month,day).strftime("%Y-%m-%d"))
    return sorted(set(out))

def _csv_bytes(rows: List[Tuple[str,str,str,str,str]]) -> bytes:
    buf = io.StringIO(); w = csv.writer(buf, delimiter=';')
    w.writerow(["Datum","Regel/Abschnitt","Was gilt","Zielgruppe","Praxis‑Checkpoint"])
    for d, sec, what, who, tip in rows:
        w.writerow([_fmt(d), sec, what, who, tip])
    return buf.getvalue().encode("utf-8-sig")  # BOM für Excel

def _tasks_30d(now: Optional[datetime] = None) -> List[str]:
    base = now or datetime.now()
    t1=(base+timedelta(days=14)).strftime("%d.%m.%Y")
    t2=(base+timedelta(days=21)).strftime("%d.%m.%Y")
    return [
        f"<li>👤 Compliance · ⏱ ½ Tag · 🎯 hoch · 📆 {t1} — Verbotene Praktiken prüfen & Transparenzhinweise in die KI‑Policy übernehmen (AI‑Act Kap. I–II).</li>",
        f"<li>👤 IT/DSB · ⏱ 1 Tag · 🎯 hoch · 📆 {t2} — GPAI‑Nutzung/Modellklassen klären; Governance‑Owner & Nachweise festlegen.</li>",
    ]

def build_timeline(text: Optional[str], phase_label: str = "2025–2027") -> Dict[str, Any]:
    rows = list(_DEFAULT)
    for d in _parse_dates(text or ""):
        if d not in {r[0] for r in rows}:
            rows.append((d,"Meilenstein","Stichtag laut AI‑Act‑Info","—","—"))
    rows.sort(key=lambda r: r[0])
    body = "".join(f"<tr><td>{_fmt(d)}</td><td>{sec}</td><td>{what}</td><td>{who}</td><td>{tip}</td></tr>" for d,sec,what,who,tip in rows)
    table_html = ('<table class="table"><thead><tr>'
                  '<th>Datum</th><th>Regel/Abschnitt</th><th>Was gilt</th><th>Zielgruppe</th><th>Praxis‑Checkpoint</th>'
                  f'</tr></thead><tbody>{body}</tbody></table>')
    return {"table_html": table_html, "csv_bytes": _csv_bytes(rows), "tasks_li": _tasks_30d(), "phase_label": phase_label}
