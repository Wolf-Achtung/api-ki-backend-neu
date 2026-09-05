#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Förder-Aktualitäts-Check.

Prüft die Förderdaten, die in den Reports wirken, auf das Alter ihres
Prüfdatums und listet Kandidaten für eine Re-Verifikation.

Drei Quellen (KIS-1297, 05.09.2026):

* ``data/funding_programmes_core_2025.json`` — die wirksame Quelle der
  deutschen Reports (Recommender und R1-Fördertabelle). Prüfdatum im Feld
  ``verified_at``. Bis KIS-1297 fehlte die Datei hier — die monatliche
  Routine pflegte ``data/funding/funding_de.json``, die kein Report liest.
* ``data/funding/funding_de_en.json`` und ``funding_eu_core_en.json`` —
  Quelle der englischen Reports (``services/funding_service_en``).
  Prüfdatum im Feld ``last_verified``.

Aufruf:
    python scripts/check_funding_freshness.py [--max-age-days 90] [--branche medien]

Exit-Code 1, wenn mindestens ein Programm veraltet oder unverifiziert ist —
so kann eine Routine/CI direkt darauf reagieren.
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Tuple

REPO = Path(__file__).resolve().parent.parent
FUNDING_DIR = REPO / "data" / "funding"

# (Pfad, Feld mit dem Prüfdatum, Feld mit der Branchenliste)
QUELLEN: List[Tuple[Path, str, str]] = [
    (REPO / "data" / "funding_programmes_core_2025.json", "verified_at", "branches"),
    (FUNDING_DIR / "funding_de_en.json", "last_verified", "branchen"),
    (FUNDING_DIR / "funding_eu_core_en.json", "last_verified", "branchen"),
]

Befund = Tuple[str, str, str, str]  # (datei, id, titel, status)


def _programme(pfad: Path) -> List[Dict[str, Any]]:
    """Beide Formen: nackte Liste (core_2025) oder ``{"programmes": [...]}``."""
    roh = json.loads(pfad.read_text(encoding="utf-8"))
    if isinstance(roh, list):
        return roh
    return roh.get("programmes") or roh.get("programs") or []


def pruefe(max_age_days: int = 90, branche: str = "",
           today: dt.date | None = None,
           quellen: List[Tuple[Path, str, str]] | None = None) -> Tuple[int, List[Befund]]:
    """Liefert (aktuell, veraltet). Ohne Netz, testbar."""
    today = today or dt.date.today()
    stale: List[Befund] = []
    fresh = 0

    for pfad, datumsfeld, branchenfeld in (quellen or QUELLEN):
        if not pfad.exists():
            continue
        for prog in _programme(pfad):
            if branche:
                branchen = [str(b).lower() for b in prog.get(branchenfeld) or []]
                # Programme ohne Branchen-Tag gelten für alle -> mitprüfen
                if branchen and branche.lower() not in branchen:
                    continue
            title = prog.get("title") or prog.get("name_de") or prog.get("name_en") or prog.get("id", "?")
            pid = prog.get("id", "?")
            lv = prog.get(datumsfeld)
            if not lv:
                stale.append((pfad.name, pid, title, "nie verifiziert"))
                continue
            try:
                age = (today - dt.date.fromisoformat(str(lv))).days
            except ValueError:
                stale.append((pfad.name, pid, title, f"ungültiges Datum: {lv}"))
                continue
            if age > max_age_days:
                stale.append((pfad.name, pid, title, f"{age} Tage alt ({lv})"))
            else:
                fresh += 1
    return fresh, stale


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--max-age-days", type=int, default=90,
                    help="Ab diesem Alter (Tage) gilt das Prüfdatum als veraltet")
    ap.add_argument("--branche", default="",
                    help="Nur Programme dieser Branche prüfen (z. B. medien); leer = alle")
    args = ap.parse_args()

    today = dt.date.today()
    fresh, stale = pruefe(args.max_age_days, args.branche, today)

    print(f"Förder-Aktualitäts-Check {today.isoformat()} "
          f"(max. Alter: {args.max_age_days} Tage"
          + (f", Branche: {args.branche}" if args.branche else "") + ")")
    print("  Quellen: " + ", ".join(p.name for p, _, _ in QUELLEN if p.exists()))
    print(f"  aktuell verifiziert: {fresh}")
    print(f"  zu prüfen:           {len(stale)}")
    if stale:
        print()
        for fname, pid, title, status in stale:
            print(f"  [{status}] {pid} — {title}  ({fname})")
        print()
        print("→ Diese Programme gegen die amtlichen Programmseiten re-verifizieren und")
        print("  das Prüfdatum (verified_at bzw. last_verified) nur nach gelesener Seite")
        print("  setzen (siehe docs/FOERDER_VERIFIKATION_*.md).")
        return 1
    print("Alle geprüften Programme sind aktuell verifiziert.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
