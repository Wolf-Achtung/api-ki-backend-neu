#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tool-Aktualitäts-Check (Quartals-Routine, KIS-1248).

Prüft alle Einträge in ``data/tools_seed.json`` auf das Alter ihrer
``verified_at``-Angabe und listet Kandidaten für eine Re-Verifikation
(Preise, DSGVO-/AVV-Status, Verfügbarkeit).

Aufruf:
    python scripts/check_tools_freshness.py [--max-age-days 100]

Exit-Code 1, wenn mindestens ein Tool veraltet oder unverifiziert ist —
so kann die Quartals-Routine/CI direkt darauf reagieren.
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import sys
from pathlib import Path

TOOLS_FILE = Path(__file__).resolve().parent.parent / "data" / "tools_seed.json"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--max-age-days", type=int, default=100,
                    help="Ab diesem Alter (Tage) gilt verified_at als veraltet "
                         "(Default 100 ≈ Quartalsrhythmus mit Puffer)")
    args = ap.parse_args()

    today = dt.date.today()
    stale: list[str] = []
    fresh = 0

    try:
        tools = json.loads(TOOLS_FILE.read_text(encoding="utf-8"))
    except Exception as exc:  # pragma: no cover
        print(f"FEHLER: {TOOLS_FILE} nicht lesbar: {exc}")
        return 1

    for tool in tools:
        name = tool.get("name", "?")
        verified = tool.get("verified_at")
        if not verified:
            stale.append(f"{name}: nie verifiziert (Preis: {tool.get('price', '?')})")
            continue
        try:
            age = (today - dt.date.fromisoformat(verified)).days
        except ValueError:
            stale.append(f"{name}: ungültiges verified_at {verified!r}")
            continue
        if age > args.max_age_days:
            stale.append(
                f"{name}: {age} Tage alt (verified {verified}, Preis: {tool.get('price', '?')})"
            )
        else:
            fresh += 1

    print(f"Tools geprüft: {len(tools)} · aktuell: {fresh} · veraltet/offen: {len(stale)}")
    if stale:
        print("\nRe-Verifikation nötig:")
        for line in stale:
            print(f"  - {line}")
        return 1
    print("Alle Tool-Einträge sind aktuell.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
