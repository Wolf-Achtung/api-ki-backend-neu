#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Förder-Aktualitäts-Check (Phase 1 Medien).

Prüft alle Programme in data/funding/*.json auf das Alter ihrer
``last_verified``-Angabe und listet Kandidaten für eine Re-Verifikation.

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

FUNDING_DIR = Path(__file__).resolve().parent.parent / "data" / "funding"
FILES = ["funding_de.json", "funding_eu.json", "funding_de_en.json", "funding_eu_core_en.json"]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--max-age-days", type=int, default=90,
                    help="Ab diesem Alter (Tage) gilt last_verified als veraltet")
    ap.add_argument("--branche", default="",
                    help="Nur Programme dieser Branche prüfen (z. B. medien); leer = alle")
    args = ap.parse_args()

    today = dt.date.today()
    stale: list[tuple[str, str, str, str]] = []  # (datei, id, titel, status)
    fresh = 0

    for fname in FILES:
        path = FUNDING_DIR / fname
        if not path.exists():
            continue
        data = json.loads(path.read_text(encoding="utf-8"))
        for prog in data.get("programmes", []):
            if args.branche:
                branchen = [str(b).lower() for b in prog.get("branchen", [])]
                if branchen and args.branche.lower() not in branchen:
                    continue
                if not branchen:
                    # Programme ohne Branchen-Tag gelten für alle -> mitprüfen
                    pass
            title = prog.get("title") or prog.get("name_de") or prog.get("id", "?")
            lv = prog.get("last_verified")
            if not lv:
                stale.append((fname, prog.get("id", "?"), title, "nie verifiziert"))
                continue
            try:
                age = (today - dt.date.fromisoformat(lv)).days
            except ValueError:
                stale.append((fname, prog.get("id", "?"), title, f"ungültiges Datum: {lv}"))
                continue
            if age > args.max_age_days:
                stale.append((fname, prog.get("id", "?"), title, f"{age} Tage alt ({lv})"))
            else:
                fresh += 1

    print(f"Förder-Aktualitäts-Check {today.isoformat()} "
          f"(max. Alter: {args.max_age_days} Tage"
          + (f", Branche: {args.branche}" if args.branche else "") + ")")
    print(f"  aktuell verifiziert: {fresh}")
    print(f"  zu prüfen:           {len(stale)}")
    if stale:
        print()
        for fname, pid, title, status in stale:
            print(f"  [{status}] {pid} — {title}  ({fname})")
        print()
        print("→ Diese Programme gegen die offiziellen Quellen re-verifizieren und")
        print("  last_verified aktualisieren (siehe docs/FOERDER_VERIFIKATION_*.md).")
        return 1
    print("Alle geprüften Programme sind aktuell verifiziert.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
