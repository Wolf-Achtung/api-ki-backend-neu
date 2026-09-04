#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""KIS-1269: Zwei Report-PDFs vergleichen — Kennzahlen und Rückfälle.

Wolf am 03.09.2026: "können wir das Briefing des letzten Reports nutzen,
um neue Reports zu generieren und die Ergebnisse direkt miteinander
vergleichen zu können".

Die eine Hälfte gibt es schon: POST /admin/testrun/replay/{briefing_id}
erzeugt einen Lauf mit identischen Antworten. Dieses Skript ist die
andere Hälfte.

Ein roher Textvergleich hilft nicht — die LLM-Prosa ist bei jedem Lauf
anders formuliert, ohne dass sich inhaltlich etwas ändert. Verglichen
werden deshalb zwei Dinge, die stabil sein MÜSSEN:

1. Die deterministischen Kennzahlen (Score, Business Case). Weichen sie
   bei identischen Antworten ab, ist das ein Befund, kein Rauschen.
2. Die Fehlermuster aus KIS-1267/1268. Taucht eines wieder auf, ist es
   ein Rückfall.

Aufruf:
    python scripts/compare_reports.py alt.pdf neu.pdf
    python scripts/compare_reports.py neu.pdf            # nur Rückfall-Check

Exit-Code 1, sobald ein Rückfall gefunden wird — damit taugt das Skript
auch als CI-Schritt.
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple

# PLATIN-QA meldet ab dieser Schwelle eine "thin_page".
THIN_PAGE_ZEICHEN = 350


# =========================================================================
# Text aus dem PDF holen
# =========================================================================

def seiten_text(pfad: Path) -> List[str]:
    """Text je Seite. PyMuPDF bevorzugt, pypdf als Rückfallebene —
    beide stehen in requirements.txt.

    KIS-1284: Geschützte Leerzeichen werden zu gewöhnlichen. Seit die
    Prozent-Schreibweise vereinheitlicht ist ("80 %" mit nbsp), würden die
    Kennzahl-Muster sonst je nach Lauf mal greifen und mal nicht."""
    try:
        import pymupdf  # type: ignore

        with pymupdf.open(pfad) as doc:
            seiten = [seite.get_text() for seite in doc]
    except ImportError:
        from pypdf import PdfReader  # type: ignore

        seiten = [(s.extract_text() or "") for s in PdfReader(str(pfad)).pages]
    return [s.replace(" ", " ").replace(" ", " ") for s in seiten]


# =========================================================================
# Kennzahlen
# =========================================================================

# (Feldname, Regex, Gruppe) — bewusst tolerant gegen Zeilenumbrüche im PDF.
_KENNZAHLEN: List[Tuple[str, str]] = [
    ("Score gesamt", r"(\d{1,3})\s*/\s*100"),
    ("Governance", r"GOVERNANCE\s+(\d{1,3})"),
    ("Sicherheit", r"SICHERHEIT\s+(\d{1,3})"),
    ("Wertschöpfung", r"WERTSCHÖPFUNG\s+(\d{1,3})"),
    ("Befähigung", r"BEFÄHIGUNG\s+(\d{1,3})"),
    ("Zeitersparnis/Monat", r"(\d{1,3})\s*h\s*\n?\s*Zeitersparnis"),
    ("Amortisation", r"([\d,]+)\s*Mon(?:ate|\.)\s*\n?\s*Amortisation"),
    ("Investition (CAPEX)", r"([\d.]+)\s*€\s*\n?\s*Investition"),
    ("Stundensatz", r"(\d{2,3})\s*€/h"),
    # KIS-1284: Der Kontext gehört ins Muster. Ohne ihn traf "€/Monat" im
    # Strategiebericht den Preis des ersten Werkzeugs in der Vergleichs-
    # tabelle ("Ab ca. 15 €/Monat") und meldete eine Kennzahl-Abweichung
    # 600 → 15, wo sich nichts geändert hatte.
    ("OPEX/Monat",
     r"([\d.]+)\s*€/Monat\s*(?:\n\s*)?(?:laufende|Tool-Kosten|OPEX|Betrieb)"
     r"|(?:laufende[nr]?\s+Tool-Kosten|OPEX)[^\d€]{0,40}?([\d.]+)\s*€/Monat"),
]


def kennzahlen(text: str) -> Dict[str, str]:
    gefunden: Dict[str, str] = {}
    for name, muster in _KENNZAHLEN:
        treffer = re.search(muster, text, re.IGNORECASE)
        if treffer:
            # Erste nicht-leere Gruppe (Muster mit Alternativen).
            wert = next((g for g in treffer.groups() if g), None)
            if wert:
                gefunden[name] = wert
    return gefunden


# =========================================================================
# Rückfall-Prüfungen (je ein behobener Defekt)
# =========================================================================

def _challenge_widerspruch(text: str) -> Optional[str]:
    """KIS-1267: Titel, Untertitel und Prognose müssen dieselbe Zahl nennen."""
    titel = re.search(r"Ihre (\d+)-Tage KI-Challenge", text)
    if not titel:
        return None
    tage = int(titel.group(1))
    fehler = []
    wochen = re.search(r"in (\d+) Wochen", text)
    if wochen:
        gerendert = len(set(re.findall(r"Woche (\d+):", text)))
        if gerendert and int(wochen.group(1)) != gerendert:
            fehler.append(f"Untertitel {wochen.group(1)} Wochen, gerendert {gerendert}")
    for prognose in re.findall(r"(?:Prognose|Gesamt) nach (\d+) Tagen", text):
        if int(prognose) != tage:
            fehler.append(f"Titel {tage} Tage, Prognose {prognose} Tage")
    return "; ".join(fehler) or None


# (Kurzname, Beschreibung, Prüffunktion -> Fundstelle oder None)
PRUEFUNGEN = [
    (
        "prompt_leak",
        "Prompt-Anweisung im Lesertext (KIS-1267)",
        lambda t: (m.group(0)[:70] if (m := re.search(
            r"\bKIS-\d{3,4}\s*:\s*[A-ZÄÖÜ][^<\n]{10,}"
            r"|\bErkl[äa]ren\s+Sie\s+dem\s+Leser\b", t)) else None),
    ),
    (
        "euro_verschluckt",
        "Betrag endet auf 'n. v.' statt auf € (KIS-1267)",
        lambda t: (m.group(0) if (m := re.search(
            r"\d[\d.]*\s*[–-]?\s*[\d.]*\s*n\.\s?v\.", t)) else None),
    ),
    (
        "bundesland_platzhalter",
        "'Ihr Bundesland' im Fließtext (KIS-1267)",
        lambda t: ("Ihr Bundesland" if "Ihr Bundesland" in t else None),
    ),
    (
        "erfundene_datenreife",
        "Zitat einer nie gegebenen Antwort (KIS-1267)",
        lambda t: (m.group(0) if (m := re.search(
            r"'?Datenreife:\s*keine'?", t)) else None),
    ),
    (
        "zim_empfohlen",
        "ZIM trotz Antragsstopp genannt (KIS-1268)",
        lambda t: ("ZIM" if re.search(r"\bZIM\b", t) else None),
    ),
    (
        "challenge_widerspruch",
        "Challenge nennt widersprüchliche Zahlen (KIS-1267)",
        _challenge_widerspruch,
    ),
    (
        "zerhackte_tabelle",
        "Tabellenzelle bricht buchstabenweise um (KIS-1284)",
        lambda t: _zerhackte_tabelle(t),
    ),
]


# KIS-1284: Zu schmale Tabellenspalten brachen Wörter ohne Trennstrich
# ("Na htl os in Mi cr os oft 36 5,", Strategie S. 20-23 im Lauf 1268).
# Im PDF-Text erscheint das als Folge sehr kurzer Zeilen aus Wortstücken.
# Ein einzelnes Fragment ist normal (Ampelwerte, "ca.", Spaltenköpfe) —
# gezählt wird deshalb erst eine Kette.
_FRAGMENT_RE = re.compile(r"^[A-Za-zÄÖÜäöüß]{1,3}$")
_FRAGMENT_KETTE = 4


def _zerhackte_tabelle(text: str) -> Optional[str]:
    kette: List[str] = []
    for zeile in text.split("\n"):
        if _FRAGMENT_RE.fullmatch(zeile.strip()):
            kette.append(zeile.strip())
            if len(kette) >= _FRAGMENT_KETTE:
                continue
        elif kette:
            if len(kette) >= _FRAGMENT_KETTE:
                return " ".join(kette[:8])
            kette = []
    if len(kette) >= _FRAGMENT_KETTE:
        return " ".join(kette[:8])
    return None


def rueckfaelle(text: str) -> List[Tuple[str, str, str]]:
    """Liefert (Kurzname, Beschreibung, Fundstelle) je Rückfall."""
    treffer = []
    for name, beschreibung, pruefe in PRUEFUNGEN:
        fund = pruefe(text)
        if fund:
            treffer.append((name, beschreibung, str(fund)))
    return treffer


# KIS-1280: Kennzeichen der Abschluss-Seite. Sie trägt bewusst wenig Text —
# Ausblick plus Kontaktbox sind das gewollte Ende, keine Layout-Panne.
_ABSCHLUSS_MERKMALE = ("Website besuchen", "Kontakt aufnehmen")


def ist_abschluss_seite(text: str) -> bool:
    """Trägt die Seite die Kontaktbox (Handlungsaufruf am Berichtsende)?"""
    return all(m in text for m in _ABSCHLUSS_MERKMALE)


# KIS-1285: Der Score gehört auf das Deckblatt. Im Lauf 1269 fehlte er im
# Strategiebericht — eine CSS-Regel war zerstört, die Box rutschte aus einem
# overflow:hidden. Das Skript meldete zwar die dünne Seite 1, aber niemand
# las das als "die Kennzahl ist weg". Deshalb sagt es das jetzt selbst.
_SCORE_AUF_SEITE_RE = re.compile(r"\b\d{1,3}\s*/\s*100\b")


def fehlende_deckblatt_kennzahl(seiten: List[str]) -> Optional[str]:
    """Fehlt auf Seite 1 der Score (»79 / 100«)?"""
    if not seiten:
        return None
    if _SCORE_AUF_SEITE_RE.search(seiten[0]):
        return None
    if not _SCORE_AUF_SEITE_RE.search("\n".join(seiten)):
        return None  # Report ohne Score — kein Deckblatt-Befund
    return ("Auf Seite 1 fehlt der Score (»79 / 100«), im Bericht steht er. "
            "Prüfen, ob eine CSS-Regel den Score-Ring leer laufen lässt.")


def wiederholte_annahmen(text: str) -> List[Tuple[str, int]]:
    """Annahmen-Absätze, die wörtlich mehrfach im Bericht stehen.

    KIS-1280: Der Strategiebericht verlangt je Abschnitt einen Absatz
    „Annahmen:". Im Lauf KIS-1265 stand dreimal wörtlich derselbe Satz —
    „Stabiles Marktumfeld …; aktuelle Teamgröße bleibt bestehen; keine
    regulatorischen Verschärfungen". Das ist eine Leerformel: Sie trägt
    keine einzige Zahl des Abschnitts und wäre für jedes Unternehmen
    gleich richtig. Der Leser überblättert sie beim zweiten Mal, und mit
    ihr die Stellen, an denen echte Annahmen stehen.
    """
    absaetze = re.findall(r"Annahmen:\s*(.{40,400}?)(?=\s*(?:Quellen?:|Seite\s+\d))",
                          re.sub(r"\s+", " ", text))
    zaehler: Dict[str, int] = {}
    for a in absaetze:
        schluessel = a.strip().lower()
        zaehler[schluessel] = zaehler.get(schluessel, 0) + 1
    return [(a, n) for a, n in zaehler.items() if n > 1]


def duenne_seiten(seiten: List[str]) -> List[Tuple[int, int]]:
    """(Seitenzahl, Zeichen) für jede Seite unter der PLATIN-QA-Schwelle.

    KIS-1280: Die Abschluss-Seite zählt nicht mit. Im Lauf KIS-1265 trug
    Seite 8 der Potenzialanalyse 348 Zeichen — Ausblick und Kontaktbox,
    also genau das vorgesehene Ende. Im Lauf davor waren es 790 Zeichen,
    weil zufällig noch eine Handlung mit drauf gerutscht war. Beide Male
    dieselbe Seite, dieselbe Absicht. Eine Prüfung, die je nach Textlänge
    mal meldet und mal nicht, bringt niemandem etwas: Man gewöhnt sich
    das Wegsehen an, und dann übersieht man die echte leere Seite.
    """
    return [(i, len(t.strip())) for i, t in enumerate(seiten, 1)
            if len(t.strip()) < THIN_PAGE_ZEICHEN and not ist_abschluss_seite(t)]


# =========================================================================
# Ausgabe
# =========================================================================

def _tabelle(alt: Dict[str, str], neu: Dict[str, str]) -> List[str]:
    zeilen = ["| Kennzahl | alt | neu | |", "|---|---|---|---|"]
    for name, _ in _KENNZAHLEN:
        a, n = alt.get(name, "—"), neu.get(name, "—")
        zeichen = "" if a == n else "  ← abweichend"
        zeilen.append(f"| {name} | {a} | {n} |{zeichen} |")
    return zeilen


def main(argv: Optional[List[str]] = None) -> int:
    p = argparse.ArgumentParser(description="Zwei Report-PDFs vergleichen.")
    p.add_argument("pdfs", nargs="+", type=Path, help="[alt.pdf] neu.pdf")
    args = p.parse_args(argv)

    if len(args.pdfs) > 2:
        p.error("höchstens zwei PDFs")
    alt_pfad = args.pdfs[0] if len(args.pdfs) == 2 else None
    neu_pfad = args.pdfs[-1]

    for pfad in args.pdfs:
        if not pfad.exists():
            print(f"Datei fehlt: {pfad}", file=sys.stderr)
            return 2

    neu_seiten = seiten_text(neu_pfad)
    neu_text = "\n".join(neu_seiten)

    print(f"# Report-Vergleich\n\nNeu: `{neu_pfad.name}` ({len(neu_seiten)} Seiten)")

    if alt_pfad:
        alt_seiten = seiten_text(alt_pfad)
        alt_text = "\n".join(alt_seiten)
        print(f"Alt: `{alt_pfad.name}` ({len(alt_seiten)} Seiten)\n")
        print("## Kennzahlen\n")
        print("\n".join(_tabelle(kennzahlen(alt_text), kennzahlen(neu_text))))
        abweichend = [n for n, _ in _KENNZAHLEN
                      if kennzahlen(alt_text).get(n) != kennzahlen(neu_text).get(n)]
        if abweichend:
            print(f"\n{len(abweichend)} Kennzahl(en) weichen ab. Bei identischen "
                  "Antworten gehören sie geprüft.")
        else:
            print("\nAlle Kennzahlen unverändert.")

    duenn = duenne_seiten(neu_seiten)
    print("\n## Dünne Seiten\n")
    if duenn:
        for nr, zeichen in duenn:
            print(f"- Seite {nr}: {zeichen} Zeichen (Schwelle {THIN_PAGE_ZEICHEN})")
    else:
        print("Keine.")

    doppelt = wiederholte_annahmen(neu_text)
    if doppelt:
        print("\n## Wiederholte Annahmen\n")
        for satz, anzahl in doppelt:
            print(f"- {anzahl}× wörtlich gleich: „{satz[:110]}…\"")
        print("\nAnnahmen sollen die Zahlen ihres Abschnitts tragen. "
              "Ein Satz, der überall passt, erklärt nirgends etwas.")

    fehlt = fehlende_deckblatt_kennzahl(neu_seiten)
    if fehlt:
        print("\n## Deckblatt\n")
        print(f"- {fehlt}")

    treffer = rueckfaelle(neu_text)
    print("\n## Rückfall-Prüfung\n")
    if not treffer:
        print(f"Keiner der {len(PRUEFUNGEN)} behobenen Fehler ist zurück.")
        return 0
    for name, beschreibung, fund in treffer:
        print(f"- **{name}** — {beschreibung}\n  Fundstelle: `{fund}`")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
