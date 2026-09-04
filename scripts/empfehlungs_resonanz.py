#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""KIS-1281 Stufe 4: Welche Empfehlung hat getragen?

Aus dem Feedback floss bisher nichts in die Empfehlungen zurueck. Die
Felder ``tools_adopted`` und ``funding_applied`` (routes/feedback.py)
schliessen den Kreis, und dieses Skript liest sie aus.

Drei Zahlen sind interessant, und die dritte am meisten:

  1. Wie oft wurde ein empfohlenes Werkzeug tatsaechlich eingefuehrt?
  2. Welche Empfehlungen nennt nie jemand? — Kandidaten zum Streichen.
  3. Welche Werkzeuge nennen Leute, die wir gar nicht empfehlen? —
     Kandidaten zum Aufnehmen. Das ist die einzige Stelle im ganzen
     System, an der etwas Neues von aussen hereinkommt, ohne dass ein
     Sprachmodell es sich ausdenkt.

Aufruf:

    python scripts/empfehlungs_resonanz.py                 # aus der DB
    python scripts/empfehlungs_resonanz.py --datei fb.json # aus einem Export

Die Datei enthaelt eine Liste von Feedback-Payloads (JSON).

Auswertung ab etwa dreissig Rueckmeldungen. Darunter zeigt das Skript
die Zahlen trotzdem, weist aber darauf hin: Aus fuenf Antworten laesst
sich keine Empfehlung streichen.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any, Dict, Iterable, List, Tuple

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

# Unter dieser Zahl ist jede Aussage ueber "wird nie genannt" Zufall.
BELASTBAR_AB = 30

# Trennzeichen in Freitextantworten: "Notion, Make und Descript"
_TRENNER = re.compile(r"[,;/\n]| und | sowie | plus ", re.IGNORECASE)

# Fuellwoerter, die als eigener "Name" durchrutschen wuerden.
_LEER = {"", "-", "keine", "keins", "keine ahnung", "nichts", "noch nichts",
         "weiss nicht", "weiß nicht", "n/a", "na", "unklar", "bisher keine"}


def normalisiere(name: str) -> str:
    """Vergleichsform: klein, ohne Zusaetze in Klammern und Randzeichen."""
    name = re.sub(r"\([^)]*\)", " ", str(name or ""))
    name = re.sub(r"[^\w\s.+-]", " ", name, flags=re.UNICODE)
    return " ".join(name.lower().split())


def zerlege(antwort: Any) -> List[str]:
    """Freitext -> Liste einzelner Nennungen."""
    teile = []
    for roh in _TRENNER.split(str(antwort or "")):
        name = normalisiere(roh)
        if name and name not in _LEER and len(name) > 1:
            teile.append(name)
    return teile


def kuratierte_werkzeuge() -> List[str]:
    from services.tools_recommender import _load_seed
    return [str(t.get("name") or "") for t in _load_seed() if t.get("name")]


def kuratierte_programme() -> List[str]:
    from services.funding_recommender import load_funding_programs
    return [str(p.get("title") or p.get("name") or "")
            for p in load_funding_programs()]


def _passt(nennung: str, kuratiert: str) -> bool:
    """Grosszuegiger Vergleich: „Notion" trifft „Notion", „make" trifft
    „Make (Integromat)". Menschen tippen keine Katalognamen."""
    k = normalisiere(kuratiert)
    if not k or not nennung:
        return False
    return nennung == k or nennung in k.split() or k.startswith(nennung + " ")


def auswerten(payloads: Iterable[Dict[str, Any]], feld: str,
              kuratiert: List[str]) -> Tuple[Dict[str, int], Dict[str, int], int]:
    """(getroffen, unbekannt, Anzahl Antworten mit Inhalt)."""
    getroffen: Dict[str, int] = {}
    unbekannt: Dict[str, int] = {}
    antworten = 0
    for p in payloads:
        nennungen = zerlege((p or {}).get(feld))
        if not nennungen:
            continue
        antworten += 1
        for n in nennungen:
            treffer = next((k for k in kuratiert if _passt(n, k)), None)
            if treffer:
                getroffen[treffer] = getroffen.get(treffer, 0) + 1
            else:
                unbekannt[n] = unbekannt.get(n, 0) + 1
    return getroffen, unbekannt, antworten


def _abschnitt(titel: str, kuratiert: List[str],
               getroffen: Dict[str, int], unbekannt: Dict[str, int],
               antworten: int) -> List[str]:
    zeilen = [f"## {titel}", "", f"{antworten} Rückmeldung(en) mit Inhalt."]
    if antworten < BELASTBAR_AB:
        zeilen.append(f"_Unter {BELASTBAR_AB} Antworten ist „wird nie genannt\" "
                      "Zufall, keine Aussage._")
    zeilen.append("")

    if getroffen:
        zeilen += ["**Übernommen:**", ""]
        for name, n in sorted(getroffen.items(), key=lambda x: -x[1]):
            zeilen.append(f"- {name}: {n}×")
        zeilen.append("")

    nie = [k for k in kuratiert if k not in getroffen]
    if nie:
        zeilen += [f"**Nie genannt ({len(nie)} von {len(kuratiert)}):**", "",
                   ", ".join(nie), ""]

    if unbekannt:
        zeilen += ["**Genannt, aber nicht von uns empfohlen:**", ""]
        for name, n in sorted(unbekannt.items(), key=lambda x: -x[1]):
            zeilen.append(f"- {name}: {n}×")
        zeilen += ["", "_Hier kommt Neues von aussen herein, ohne dass ein "
                   "Sprachmodell es sich ausdenkt. Vor der Aufnahme gilt "
                   "dieselbe Regel wie sonst: Preis und Datenschutzlage "
                   "bestätigt ein Mensch._", ""]
    return zeilen


def lade_aus_db() -> List[Dict[str, Any]]:
    from models import Feedback
    from core.database import SessionLocal  # type: ignore
    with SessionLocal() as db:
        return [f.payload or {} for f in db.query(Feedback).all()]


def main(argv: List[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--datei", type=Path,
                    help="JSON-Liste von Feedback-Payloads statt Datenbank")
    ap.add_argument("--report", type=Path, help="Ausgabe zusätzlich in diese Datei")
    args = ap.parse_args(argv)

    if args.datei:
        if not args.datei.is_file():
            print(f"Datei fehlt: {args.datei}", file=sys.stderr)
            return 2
        payloads = json.loads(args.datei.read_text(encoding="utf-8"))
    else:
        try:
            payloads = lade_aus_db()
        except Exception as exc:
            print(f"Datenbank nicht erreichbar: {exc}", file=sys.stderr)
            return 2

    if not isinstance(payloads, list):
        print("Erwartet wird eine Liste von Payloads.", file=sys.stderr)
        return 2

    werkzeuge, programme = kuratierte_werkzeuge(), kuratierte_programme()
    zeilen = [f"# Empfehlungs-Resonanz ({len(payloads)} Rückmeldungen)", ""]
    zeilen += _abschnitt("Werkzeuge", werkzeuge,
                         *auswerten(payloads, "tools_adopted", werkzeuge))
    zeilen += _abschnitt("Förderprogramme", programme,
                         *auswerten(payloads, "funding_applied", programme))

    text = "\n".join(zeilen)
    print(text)
    if args.report:
        args.report.write_text(text, encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
