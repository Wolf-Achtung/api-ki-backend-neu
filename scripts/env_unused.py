#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Prueft eine Liste von ENV-Namen gegen den Quelltext.

Anlass: Am 03.09.2026 stand eine Loeschliste mit 37 Variablen im Repo.
Von diesen 37 existierte in Railway genau eine. Die Liste war gegen den
Code geprueft, aber nie gegen die tatsaechlich gesetzten Variablen — und
das Suchverfahren hatte vier blinde Flecken:

  1. Namen, die nur in einer Konstanten stehen
     (``MODE = os.getenv("AI_ACT_MODE")`` -> Treffer erst spaeter ueber
     ``MODE``). Loesung: nach dem nackten Namen suchen, nicht nach einem
     ``os.getenv``-Muster.
  2. Namen, die zur Laufzeit zusammengesetzt werden
     (``f"OPENAI_MAX_TOKENS_{section}"``). Die stehen nirgends im Code.
     Loesung: bekannte Praefixe kennen (PRAEFIXE).
  3. Teilzeichenketten: ``RATE_LIMIT_PER_MINUTE`` findet sich in
     ``REPORT_RATE_LIMIT_PER_MINUTE`` — der Code liest aber nur den
     langen Namen. Loesung: Wortgrenzen, die ``_`` einschliessen.
  4. Helfer statt ``os.getenv``: ``_bool_env("X")``, ``get_bool("X")``,
     ``_truthy("X")``. Auch hier hilft die Suche nach dem nackten Namen.

Aufruf:

    python scripts/env_unused.py meine_variablen.txt

Die Datei enthaelt die Namen, durch Leerzeichen oder Zeilen getrennt —
so, wie Railway sie in der Variablen-Uebersicht anzeigt.

Ausgabe: drei Gruppen. ``LOESCHBAR`` nennt nur Namen ohne jeden Treffer
im Laufzeit-Code. Das Urteil bleibt beim Menschen: ein Name, der nur in
einem Workflow oder in ``tools/`` vorkommt, wirkt in Railway nicht, kann
aber in der CI gebraucht werden.
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path
from typing import Dict, List, Set

REPO = Path(__file__).resolve().parent.parent

# Verzeichnisse, deren Code im Railway-Dienst laeuft.
LAUFZEIT_ORDNER = (
    "adapter", "admin", "briefing", "config", "content", "core", "i18n",
    "middleware", "migrations", "routes", "schemas", "services", "storage",
    "utils", "workers",
)
LAUFZEIT_DATEIEN = (
    "main.py", "settings.py", "models.py", "gpt_analyze.py",
    "field_registry.py", "b25_enforcer.py", "setup_database.py",
)

# Ordner, die nicht im Dienst laufen: ein Treffer hier heisst "wirkt in
# Railway nicht", nicht "kann weg".
#
# ``tests`` und ``docs`` fehlen mit Absicht. Beide nennen ENV-Namen, um
# ueber sie zu reden — eine Loeschliste in ``docs/`` wuerde jeden Namen
# darauf als "benutzt" melden und sich selbst widerlegen.
NEBEN_ORDNER = ("scripts", "tools", ".github", "ops")

# Namen, die die Plattform liest, nicht der Code. Sie stehen nirgends im
# Repo und wuerden sonst als loeschbar gemeldet.
PLATTFORM_VARIABLEN = frozenset({
    "DATABASE_URL", "PORT", "MISE_PYTHON_GITHUB_ATTESTATIONS",
    "PYTHONUNBUFFERED", "PYTHONPATH", "TZ", "NIXPACKS_PYTHON_VERSION",
})

# Praefixe, hinter denen der Code den Rest zur Laufzeit anhaengt.
# Quelle: CLAUDE.md, Abschnitt "ENV-Vertrag".
PRAEFIXE = (
    "USE_ANTHROPIC_FOR_",
    "ANTHROPIC_MAX_TOKENS_",
    "ANTHROPIC_MODEL_",
    "ANTHROPIC_TEMP_",
    "OPENAI_MAX_TOKENS_",
    "OPENAI_MODEL_",
    "OPENAI_TEMP_",
    "BRAND_",
)

TEXT_ENDUNGEN = {".py", ".yml", ".yaml", ".toml", ".cfg", ".sh", ".json"}


def wortgrenze(name: str) -> re.Pattern:
    """Findet ``name`` nur als ganzen Namen.

    ``\\b`` allein reicht nicht: ``_`` ist ein Wortzeichen, also trennt
    ``\\b`` nicht zwischen ``RATE_LIMIT`` und ``REPORT_RATE_LIMIT``.
    Genau das erzeugte den dritten blinden Fleck.
    """
    return re.compile(rf"(?<![A-Za-z0-9_]){re.escape(name)}(?![A-Za-z0-9_])")


def sammle_dateien() -> List[Path]:
    dateien: List[Path] = []
    for ordner in LAUFZEIT_ORDNER + NEBEN_ORDNER:
        pfad = REPO / ordner
        if not pfad.is_dir():
            continue
        for datei in pfad.rglob("*"):
            if not (datei.is_file() and datei.suffix in TEXT_ENDUNGEN):
                continue
            # Diese Datei nennt Beispielnamen in ihrer eigenen Erklaerung
            # und wuerde sie sonst als "benutzt" melden.
            if datei.resolve() == Path(__file__).resolve():
                continue
            dateien.append(datei)
    for name in LAUFZEIT_DATEIEN:
        pfad = REPO / name
        if pfad.is_file():
            dateien.append(pfad)
    if (REPO / "Procfile").is_file():
        dateien.append(REPO / "Procfile")
    return dateien


def ist_laufzeit(datei: Path) -> bool:
    rel = datei.relative_to(REPO)
    return rel.parts[0] in LAUFZEIT_ORDNER or str(rel) in LAUFZEIT_DATEIEN


def lies_namen(pfad: Path) -> List[str]:
    roh = pfad.read_text(encoding="utf-8")
    namen: List[str] = []
    gesehen: Set[str] = set()
    for stueck in re.split(r"[\s,]+", roh):
        stueck = stueck.strip()
        if not re.fullmatch(r"[A-Z][A-Z0-9_]*", stueck or ""):
            continue
        if stueck not in gesehen:
            gesehen.add(stueck)
            namen.append(stueck)
    return namen


def pruefe(namen: List[str]) -> Dict[str, Dict[str, object]]:
    dateien = sammle_dateien()
    inhalte = []
    for datei in dateien:
        try:
            inhalte.append((datei, datei.read_text(encoding="utf-8", errors="ignore")))
        except OSError:
            continue

    ergebnis: Dict[str, Dict[str, object]] = {}
    for name in namen:
        muster = wortgrenze(name)
        zitiert = re.compile(rf"""["']{re.escape(name)}["']""")
        laufzeit: List[str] = []
        neben: List[str] = []
        als_string = False
        for datei, text in inhalte:
            if not muster.search(text):
                continue
            rel = str(datei.relative_to(REPO))
            if ist_laufzeit(datei):
                laufzeit.append(rel)
                if zitiert.search(text):
                    als_string = True
            else:
                neben.append(rel)

        # Die Reihenfolge ist wichtig: Ein Praefix-Name wie
        # ANTHROPIC_MODEL_FALLBACK steht auch woertlich im Code. Erst den
        # woertlichen Treffer pruefen, sonst verschwindet er in der
        # dynamischen Gruppe und niemand sieht ihn mehr an.
        if name in PLATTFORM_VARIABLEN:
            art = "plattform"
        elif laufzeit == ["settings.py"] and als_string:
            # Blinder Fleck 5: settings.py liest den Wert in ein Feld ein.
            # Liest niemand dieses Feld, ist die Variable trotz Treffer
            # wirkungslos. Sieben Variablen lagen am 04.09.2026 so
            # (ENABLE_PERPLEXITY, PERPLEXITY_MAX_TOKENS, RESEARCH_LANG …):
            # Der Research-Code liest seine eigenen Namen direkt.
            art = "nur_settings"
        elif laufzeit and als_string:
            art = "gelesen"
        elif laufzeit:
            art = "nur_bezeichner"
        elif name.startswith(PRAEFIXE):
            art = "dynamisch"
        elif neben:
            art = "nur_nebenpfad"
        else:
            art = "loeschbar"
        ergebnis[name] = {"art": art, "treffer": laufzeit + neben}
    return ergebnis


def main(argv: List[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("datei", type=Path, help="Datei mit den ENV-Namen")
    p.add_argument("--alle", action="store_true",
                   help="auch die gelesenen Namen mit Fundstellen zeigen")
    args = p.parse_args(argv)

    if not args.datei.is_file():
        print(f"Datei nicht gefunden: {args.datei}", file=sys.stderr)
        return 2

    namen = lies_namen(args.datei)
    ergebnis = pruefe(namen)

    gruppen: Dict[str, List[str]] = {"loeschbar": [], "nur_settings": [],
                                     "nur_nebenpfad": [], "nur_bezeichner": [],
                                     "dynamisch": [], "plattform": [],
                                     "gelesen": []}
    for name, info in ergebnis.items():
        gruppen[str(info["art"])].append(name)

    print(f"{len(namen)} Namen geprueft gegen {len(sammle_dateien())} Dateien.\n")

    print(f"LOESCHBAR — kein Treffer im ganzen Repo ({len(gruppen['loeschbar'])}):")
    for name in gruppen["loeschbar"]:
        print(f"  {name}")

    print(f"\nNUR SETTINGS — nur in settings.py eingelesen "
          f"({len(gruppen['nur_settings'])}):")
    for name in gruppen["nur_settings"]:
        print(f"  {name}")
    if gruppen["nur_settings"]:
        print("  (Pruefen: liest ueberhaupt jemand das Feld, in das der Wert "
              "geht? Sonst wirkungslos.)")

    print(f"\nNUR NEBENPFAD — wirkt im Dienst nicht ({len(gruppen['nur_nebenpfad'])}):")
    for name in gruppen["nur_nebenpfad"]:
        print(f"  {name}  <- {', '.join(ergebnis[name]['treffer'][:3])}")

    print(f"\nNUR BEZEICHNER — Name steht im Code, aber nie in Anfuehrungszeichen "
          f"({len(gruppen['nur_bezeichner'])}):")
    for name in gruppen["nur_bezeichner"]:
        print(f"  {name}  <- {', '.join(ergebnis[name]['treffer'][:3])}")
    if gruppen["nur_bezeichner"]:
        print("  (Verdacht: Python-Konstante gleichen Namens, kein ENV-Zugriff. "
              "Jede Stelle einzeln ansehen.)")

    print(f"\nDYNAMISCH — Praefix wird zur Laufzeit ergaenzt ({len(gruppen['dynamisch'])}):")
    for name in gruppen["dynamisch"]:
        print(f"  {name}")

    if gruppen["plattform"]:
        print(f"\nPLATTFORM — liest Railway, nicht der Code ({len(gruppen['plattform'])}):")
        for name in gruppen["plattform"]:
            print(f"  {name}")

    print(f"\nGELESEN — bleiben stehen ({len(gruppen['gelesen'])})")
    if args.alle:
        for name in gruppen["gelesen"]:
            print(f"  {name}  <- {', '.join(ergebnis[name]['treffer'][:3])}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
