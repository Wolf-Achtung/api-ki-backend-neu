#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""KIS-1296: Bestätigte Kandidaten aus der Handprüfung in die Daten schreiben.

Liest ``data/kandidaten_stufe4.json``. Nur Einträge mit ``"bestaetigt": true``
werden übernommen — Werkzeuge nach ``data/tools_seed.json``, Programme nach
``data/funding_programmes_core_2025.json``. Jeder Eintrag bekommt das
heutige Datum als ``verified_at``. Ein Preis wird nur übernommen, wenn das
Feld ``preis`` gefüllt ist — sonst zeigt der Report „siehe Anbieterseite".

Regeln:
  * ``host``/``gdpr`` leer → die Vermutung wird NICHT übernommen; der Lauf
    bricht mit einer Meldung ab. Was in die Daten kommt, hat ein Mensch
    auf der Anbieterseite gesehen.
  * Namen und IDs, die es schon gibt, werden übersprungen (idempotent).
  * ``--dry-run`` zeigt nur, was passieren würde.

Aufruf:
    python3 scripts/kandidaten_uebernehmen.py [--dry-run] [--datum YYYY-MM-DD]
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import date
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
KANDIDATEN = REPO / "data" / "kandidaten_stufe4.json"
TOOLS = REPO / "data" / "tools_seed.json"
FUNDING = REPO / "data" / "funding_programmes_core_2025.json"

GUELTIGE_SPARTEN = {"produktion", "post_vfx", "games", "verlag_publishing",
                    "musik_audio", "agentur_design", "content_creation"}


def _lade(p: Path):
    return json.loads(p.read_text(encoding="utf-8"))


def _schreibe(p: Path, daten) -> None:
    p.write_text(json.dumps(daten, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def werkzeug_eintrag(k: dict, datum: str) -> dict:
    fehlt = [f for f in ("host", "gdpr") if not str(k.get(f) or "").strip()]
    if fehlt:
        raise ValueError(f"{k['name']}: Feld(er) {fehlt} leer — die Vermutung zählt nicht, bitte von der Anbieterseite eintragen")
    sparten = [s for s in k.get("sparten", []) if s in GUELTIGE_SPARTEN]
    if not sparten:
        raise ValueError(f"{k['name']}: keine gültige Sparte")
    return {
        "name": k["name"],
        "url": k["url"],
        "trust_url": k.get("trust_url") or k["url"],
        "category": k.get("category") or "",
        "price": str(k.get("preis") or "").strip(),
        "gdpr": str(k["gdpr"]).strip(),
        "host": str(k["host"]).strip(),
        "best_for_size": ["solo", "team", "kmu"],
        "best_for_industries": ["medien"],
        "verified_at": datum,
        "sparten": sparten,
    }


def programm_eintrag(k: dict, datum: str) -> dict:
    fehlt = [f for f in ("focus", "funding_rate") if not str(k.get(f) or "").strip()]
    if fehlt:
        raise ValueError(f"{k['id']}: Feld(er) {fehlt} leer — bitte von der Programmseite eintragen")
    sparten = [s for s in k.get("sparten", []) if s in GUELTIGE_SPARTEN]
    return {
        "id": k["id"],
        "title": k["title"],
        "region": k.get("region") or "Deutschland (bundesweit)",
        "country_code": "DE",
        "status": "active",
        "funding_type": "Zuschuss",
        "funding_rate": str(k["funding_rate"]).strip(),
        "max_amount": str(k.get("max_amount") or "projektabhängig").strip(),
        "focus": str(k["focus"]).strip(),
        "suitable_for": ["solo", "team", "kmu"],
        "notes": str(k.get("_hinweis") or "").strip(),
        "priority": 2,
        "provider": k.get("provider") or "",
        "recheck_after": "",
        "relevance_ki": "mittel",
        "url": k["url"],
        "verified_at": datum,
        "branches": ["medien"],
        "branch_exclusive": True,
        "deadline": str(k.get("deadline") or "").strip(),
        "deadline_notes": "",
        "sparten": sparten,
    }


def uebernehmen(dry_run: bool = False, datum: str | None = None,
                kandidaten: Path = KANDIDATEN, tools: Path = TOOLS, funding: Path = FUNDING) -> dict:
    datum = datum or date.today().isoformat()
    kand = _lade(kandidaten)
    seed = _lade(tools)
    progs = _lade(funding)
    vorhandene_namen = {str(t.get("name") or "").strip().lower() for t in seed}
    vorhandene_ids = {str(p.get("id") or "") for p in progs}
    bericht = {"werkzeuge": [], "programme": [], "uebersprungen": [], "offen": []}

    for k in kand.get("werkzeuge", []):
        if k.get("bestaetigt") is not True:
            bericht["offen"].append(k["name"]); continue
        if k["name"].strip().lower() in vorhandene_namen:
            bericht["uebersprungen"].append(k["name"]); continue
        seed.append(werkzeug_eintrag(k, datum)); bericht["werkzeuge"].append(k["name"])

    for k in kand.get("programme", []):
        if k.get("bestaetigt") is not True:
            bericht["offen"].append(k["id"]); continue
        if k["id"] in vorhandene_ids:
            bericht["uebersprungen"].append(k["id"]); continue
        progs.append(programm_eintrag(k, datum)); bericht["programme"].append(k["id"])

    if not dry_run and (bericht["werkzeuge"] or bericht["programme"]):
        _schreibe(tools, seed)
        _schreibe(funding, progs)
    return bericht


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--datum", default=None, help="Prüfdatum, Standard heute")
    args = ap.parse_args()
    try:
        b = uebernehmen(dry_run=args.dry_run, datum=args.datum)
    except ValueError as exc:
        print(f"ABBRUCH: {exc}"); return 1
    print(("Probelauf — " if args.dry_run else "") + f"Werkzeuge: {b['werkzeuge'] or '—'}")
    print(f"Programme: {b['programme'] or '—'}")
    print(f"Übersprungen (schon vorhanden): {b['uebersprungen'] or '—'}")
    print(f"Noch offen (nicht bestätigt): {b['offen'] or '—'}")
    if not args.dry_run and (b["werkzeuge"] or b["programme"]):
        print("Danach: python3 -m pytest tests/golden tests/test_kis1292_sparte_daten.py -q")
    return 0


if __name__ == "__main__":
    sys.exit(main())
