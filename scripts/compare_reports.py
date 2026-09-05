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
    (
        "stichtag_als_zukunft",
        "Art.-50-Stichtag 02.08.2026 als bevorstehend beschrieben (KIS-1293)",
        lambda t: (m.group(0)[:80] if (m := re.search(
            r"Stichtag[^.\n]{0,60}in wenigen Wochen"
            r"|in wenigen Wochen[^.\n]{0,60}(?:Stichtag|02\.08\.2026)"
            r"|bevorstehende[nr]? Stichtag"
            r"|deadline[^.\n]{0,60}in a few weeks|in a few weeks[^.\n]{0,60}deadline", t)) else None),
    ),
    (
        "erfundenes_werkzeug",
        "Werkzeug ausserhalb der gepflegten Liste empfohlen (KIS-1293)",
        # KIS-1302: Otter/Fathom/Fireflies sind echte US-Dienste ohne Zeile in
        # tools_seed.json — R1 S. 10 (Lauf KIS1275) empfahl „Otter" als Quick Win.
        lambda t: (m.group(0) if (m := re.search(
            r"Adobe Sensei|Legiscope|TrustArc|OpenDP|\bAIVA\b|Azure Cognitive Services"
            r"|\bOtter(?:\.ai)?\b|\bFathom\b|\bFireflies(?:\.ai)?\b", t)) else None),
    ),
    (
        "satzabbruch_vor_block",
        "Absatz endet mitten im Satz, direkt davor ein Quartals-/Phasenblock (KIS-1302)",
        lambda t: _satzabbruch_vor_block(t),
    ),
    (
        "werkzeug_als_hochrisiko",
        "Standard-Werkzeug als Hochrisiko-System eingestuft (KIS-1293)",
        # KIS-1304: „… fallen nicht unter die Hochrisiko-Systeme" ist die
        # richtige Aussage, kein Befund (Lauf KIS1276, Strategie S. 33).
        lambda t: (m.group(0)[:100] if (m := re.search(
            r"(?:Copilot|Runway|Firefly|ChatGPT|Claude|Descript|Sensei|DeepL)"
            r"(?:(?!\bnicht\b|\bkein[e]?\b|\bnot\b|\bno\b)[^.\n]){0,160}(?:hochrisk|high-risk|Hochrisiko)", t)) else None),
    ),
    (
        "ankuendigung_ohne_liste",
        "Satz kündigt eine Liste an, danach folgt keine (KIS-1298)",
        lambda t: _ankuendigung_ohne_liste(t),
    ),
    (
        "us_werkzeug_als_eu",
        "US-Anbieter als EU-konform oder EU-gehostet bezeichnet (KIS-1298)",
        lambda t: _us_werkzeug_als_eu(t),
    ),
    (
        "ai_act_verordnungsnummer",
        "AI Act mit erfundener Verordnungsnummer statt (EU) 2024/1689 (KIS-1305)",
        lambda t: _ai_act_verordnungsnummer(t),
    ),
    (
        "lokal_als_eu_gehostet",
        "Lokal installiertes Werkzeug als EU-gehostet bezeichnet (KIS-1305)",
        lambda t: _lokal_als_eu_gehostet(t),
    ),
    (
        "einwort_absatz_am_kapitelende",
        "Kapitel endet mit einem einzelnen Wort — Rest einer Überschrift ohne Inhalt (KIS-1305)",
        lambda t: _einwort_absatz_am_kapitelende(t),
    ),
    (
        "abgelaufene_frist",
        "Förderfrist liegt vor dem Reportdatum (KIS-1306)",
        lambda t: _abgelaufene_frist(t),
    ),
]


# KIS-1305: Strategie S. 37 (Lauf KIS1277): „EU AI Act (Verordnung 2021/0691)".
# Die KI-Verordnung ist (EU) 2024/1689; jede andere Jahr/Nummer-Angabe neben
# dem Namen ist erfunden (2021/0206 war der Kommissionsvorschlag).
_AI_ACT_NUMMER_RE = re.compile(
    r"(?:AI[\s-]*Act|KI-Verordnung|AI Regulation)[^.\n]{0,30}?(?:Verordnung|Regulation|VO)?\s*\(?(?:EU\)?\s*)?(\d{4}/\d{3,4})",
    re.IGNORECASE,
)


def _ai_act_verordnungsnummer(text: str) -> Optional[str]:
    text = _zellen_zusammenfuegen(text)
    for m in _AI_ACT_NUMMER_RE.finditer(text):
        if m.group(1) != "2024/1689":
            return re.sub(r"\s+", " ", m.group(0))[:100]
    return None


# KIS-1305: Strategie S. 36 (Lauf KIS1277): „EU-gehostete Tools wie Amberscript
# für Transkription und DaVinci Resolve für Postproduktion". DaVinci Resolve
# und Topaz Video AI laufen lokal — kein Hosting, also auch kein EU-Hosting.
_LOKALE_WERKZEUGE = r"DaVinci(?: Resolve)?|Topaz(?: Video AI)?|iZotope(?: RX)?"
_LOKAL_ALS_EU_RE = re.compile(
    r"(?:EU-gehostet\w*|EU-Hosting|EU-hosted)(?:(?!\bUS\b|\blokal\w*|\blocal\w*|\bzu\b|\bstatt\b|\banstelle\b)[^.!?\n]){0,120}?\b(?:" + _LOKALE_WERKZEUGE + r")\b"
    r"|\b(?:" + _LOKALE_WERKZEUGE + r")\b(?:(?!\blokal\w*|\blocal\w*|\bnicht\b|\bkein\b)[^.!?·|\n]){0,80}?(?:EU-gehostet|EU-Hosting|EU-hosted|EU / EU|EU-Server)",
    re.IGNORECASE,
)


def _lokal_als_eu_gehostet(text: str) -> Optional[str]:
    text = _zellen_zusammenfuegen(text)
    treffer = [re.sub(r"\s+", " ", m.group(0))[:120] for m in _LOKAL_ALS_EU_RE.finditer(text)]
    if not treffer:
        return None
    return " | ".join(dict.fromkeys(treffer))


# KIS-1305: R1 S. 31 (Lauf KIS1277): Der 12-Monats-Ausblick endete mit der
# Zeile „Jahresabschluss." — eine Überschrift, deren Liste fehlte. Im
# Seitentext: eine Zeile aus einem einzigen Wort mit Punkt, davor ein
# vollständiger Satz, danach ein Kapitelanfang oder der Seitenfuß.
_EINWORT_RE = re.compile(r"^[A-ZÄÖÜ][a-zäöüß-]{5,40}\.$")
_KAPITELANFANG_RE = re.compile(r"^(?:Auf einen Blick:|At a glance:|Seite \d+ / \d+|Page \d+ / \d+|===== SEITE)")


def _einwort_absatz_am_kapitelende(text: str) -> Optional[str]:
    zeilen = [z.strip() for z in text.split("\n")]
    for i in range(1, len(zeilen) - 1):
        if not _EINWORT_RE.match(zeilen[i]):
            continue
        vorher = zeilen[i - 1]
        if len(vorher) < 40 or vorher[-1] not in ".!?":
            continue
        j = i + 1
        while j < len(zeilen) and not zeilen[j]:
            j += 1
        if j < len(zeilen) and _KAPITELANFANG_RE.match(zeilen[j]):
            return zeilen[i]
    return None


# KIS-1298: Lauf KIS1274, R1 S. 24 und 26 — "Ein pragmatischer 3-Schritte-
# Prozess unterstützt Ihre Organisation dabei:" und "kommen vor allem
# folgende Kategorien infrage:" standen ohne Liste im PDF. Ein Filter hatte
# die Zeilen entfernt. Im Seitentext heisst das: Eine laengere Zeile endet
# auf Doppelpunkt, und die naechste ist eine Ueberschrift, ein Hinweis oder
# der Seitenfuss statt eines Listenpunkts.
_ANKUENDIGUNG_FOLGE = re.compile(
    r"^(?:\d+\.\s+\S|Wichtig:|Hinweis:|Checkliste|Keine Rechtsberatung|Seite \d+ / \d+"
    r"|Important:|Note:|Checklist|No legal advice|Page \d+ / \d+)"
)


def _ankuendigung_ohne_liste(text: str) -> Optional[str]:
    zeilen = [z.strip() for z in text.split("\n")]
    for i, zeile in enumerate(zeilen):
        if len(zeile) < 25 or not zeile.endswith(":") or zeile.isupper():
            continue
        j = i + 1
        # KIS-1304: Seitenfuß, Seitenkopf und Leerzeilen überspringen — die
        # Liste folgt oft auf der nächsten Seite (Lauf KIS1276, R1 S. 27/28).
        while j < len(zeilen) and (not zeilen[j] or re.match(
                r"^(?:Seite \d+ / \d+|Page \d+ / \d+|Report-ID:|===== SEITE)", zeilen[j])):
            j += 1
        if j >= len(zeilen):
            return zeile[-80:]
        # KIS-1302: „1. Phase 1 – Aufbau von KI-Know-how und Schulung: …" ist
        # ein nummerierter Listenpunkt, keine Kapitelüberschrift (Lauf
        # KIS1275, Strategie S. 15 nach „Empfehlung zur Reihenfolge:").
        if re.match(r"^\d+\.\s+\S", zeilen[j]) and len(zeilen[j]) >= 45:
            continue
        if _ANKUENDIGUNG_FOLGE.match(zeilen[j]):
            return zeile[-80:]
    return None


# KIS-1298: Strategiebericht KIS1274 nannte Claude "EU-konforme Alternative"
# (Hosting "EU / EU-Anbieter") und Runway "EU-konform" — beide US-Anbieter,
# R1 stufte Claude im selben Lauf rot ein. Ein "US" zwischen Name und
# EU-Begriff (Tabellenzeile "US / US (AVV prüfen)") entwarnt.
_US_ANBIETER = ("ChatGPT", "OpenAI", "Claude", "Anthropic", "Perplexity", "Runway",
                "Gemini", "Midjourney")
_EU_BEGRIFF = (r"EU-konform|EU-gehostet|EU-Hosting|EU / EU|EU-Anbieter|EU-Server"
               r"|EU-compliant|EU-hosted|EU-based provider")
_US_NAMEN = "|".join(_US_ANBIETER)
# Vorwaerts: "Claude (Anthropic) als EU-konforme Alternative", Tabellenzeile
# "Claude … EU / EU Anbieter". Kein Satzende dazwischen — sonst traefe
# "ChatGPT ist nicht DSGVO-konform. Priorisieren Sie EU-konforme …".
# Woerter wie "aber", "statt", "priorisieren" markieren den Gegensatz.
_GEGENSATZ = r"\baber\b|\bstatt\b|\bstattdessen\b|\banstelle\b|\bdaher\b|priorisier|bevorzug|\binstead\b|\brather\b|\bprefer"
# KIS-1302: Steht zwischen US-Name und EU-Begriff ein EU-Werkzeug („Runway
# … und Amberscript für EU-konform"), gilt die Aussage dem EU-Werkzeug.
# Der Feldtrenner „·" des R1-Werkzeugblocks beendet die Suche („US-
# Subprozessoren (Learneo, OpenAI) · EU-Anbieter" ist eine Feldliste,
# kein Satz).
_EU_WERKZEUGE = r"Amberscript|Aleph Alpha|DeepL|Mistral|LanguageTool|Auphonic|Duden|Make \(Integromat\)|\bMake\b"
_US_ALS_EU_RE = re.compile(
    r"\b(?:" + _US_NAMEN + r")\b(?:(?!\bUS\b|Subprozessor|sub-?processor|" + _GEGENSATZ + r"|" + _EU_WERKZEUGE + r")[^.!?·|]){0,140}?(?:" + _EU_BEGRIFF + r")"
    # Rueckwaerts: "EU-gehostete Alternativen wie Claude" — aber nicht
    # "EU-konforme Alternativen zu ChatGPT" (zu/statt/anstelle/für).
    # KIS-1304: „EU / EU-Server · Kann mit Microsoft 365, OpenAI API verbunden
    # werden" ist die Integrationsspalte, keine Hosting-Aussage über OpenAI.
    r"|(?:" + _EU_BEGRIFF + r")(?:(?!\bUS\b|\bzu\b|\bstatt\b|\banstelle\b|\bfür\b|\bmit\b|verbunden|integr|\bto\b|\bof\b|\bwith\b|connect)[^.!?\n]){0,80}?\b(?:" + _US_NAMEN + r")\b",
    re.IGNORECASE,
)


def _zellen_zusammenfuegen(text: str) -> str:
    """Tabellenzellen im PDF-Text: weiche Trennstriche raus, „EU-\\nkonforme"
    wieder ein Wort, kurze Zeilen (Zellenumbrüche) zu einer Zeile. Der
    S8-Satz in Lauf KIS1275 stand so: „Priori\\xadsieren Sie EU-\\nkonforme
    Tools wie\\nMicrosoft 365\\nCopilot, Runway\\nund Ambers\\xadcript."."""
    text = text.replace("­", "")
    text = re.sub(r"-\n(?=[a-zäöüß])", "-", text)
    out: List[str] = []
    anhaengen = False  # eine kurze Zeile zieht auch die nächste zu sich
    for z in text.split("\n"):
        s = z.strip()
        kurz = 0 < len(s) < 25
        if out and out[-1] and s and (anhaengen or kurz):
            out[-1] = out[-1] + " " + s
        else:
            out.append(z)
        anhaengen = kurz
    return "\n".join(out)


def _us_werkzeug_als_eu(text: str) -> Optional[str]:
    # KIS-1302: alle Treffer melden — der erste (ein Falschtreffer im
    # Werkzeugblock) verdeckte in Lauf KIS1275 den echten Fehler in S8.
    text = _zellen_zusammenfuegen(text)
    treffer = [re.sub(r"\s+", " ", m.group(0))[:120] for m in _US_ALS_EU_RE.finditer(text)]
    if not treffer:
        return None
    return " | ".join(dict.fromkeys(treffer))


# KIS-1302: R1 S. 28 (Lauf KIS1275): „… überhaupt weiter Material zur Verfügung"
# und direkt darunter „Q1 (Monate 1–3)". Ein Absatz, der ohne Satzzeichen
# endet, gefolgt von einem Quartals- oder Phasenblock.
_BLOCKSTART_RE = re.compile(r"^(?:Q[1-4]\b|Phase\s+\d|Monat(?:e)?\s+\d|Quarter\s+[1-4]|Months?\s+\d)")


def _satzabbruch_vor_block(text: str) -> Optional[str]:
    """Nur Fortsetzungszeilen eines Absatzes zählen: Die Zeile davor ist lang
    und endet ohne Satzzeichen. Eine Überschrift wie „90-Tage-Fahrplan –
    Entscheidungsfassung" vor „Phase 1" folgt auf einen fertigen Satz."""
    zeilen = [z.rstrip() for z in text.split("\n")]
    for i in range(1, len(zeilen) - 1):
        z = zeilen[i].strip()
        vorher = zeilen[i - 1].strip()
        if len(z) < 30 or z[-1] in ".!?:;)»”\"" or z.isupper():
            continue
        if not re.search(r"[a-zäöüß]$", z):
            continue
        if len(vorher) < 60 or vorher[-1] in ".!?:;)»”\"":
            continue
        folge = zeilen[i + 1].strip()
        if not _BLOCKSTART_RE.match(folge):
            continue
        # KIS-1306: „… Break-Even-Zeiten zwischen" + „Monat 8 und 17." ist ein
        # umgebrochener Satz, kein Phasenblock (Strategie S. 21, Lauf KIS1278).
        # Ein Blockanfang trägt Doppelpunkt, Gedankenstrich oder Klammer
        # („Monate 1–3 – Fundament", „Q1 (Monate 1–3):"); ein Satzrest endet
        # mit Punkt und ist kurz.
        if folge.startswith(("Monat", "Month")) and not re.search(r"[:–—(]", folge):
            continue
        if len(folge) < 45 and folge.endswith(".") and not re.search(r"[:–—(]", folge):
            continue
        return z[-80:] + " → " + folge[:20]
    return None


# KIS-1306: Strategie S. 27/29 (Lauf KIS1278 vom 05.09.2026): Medienboard mit
# „14.07.2026 (Einreichfrist Filmförderung 2026)" und Praxis-Tipp „Einreichfrist
# im Juli 2026" — beide vor dem Reportdatum. Das Reportdatum steht im
# Seitenfuß („Report-ID: KIS-1278 • 05.09.2026").
_REPORT_DATUM_RE = re.compile(r"Report-ID:[^\n]*?•\s*(\d{2})\.(\d{2})\.(\d{4})")
_FRIST_DATUM_RE = re.compile(
    r"(?:Frist|frist|Deadline|deadline|Einreich)[^.\n]{0,40}?(\d{2})\.(\d{2})\.(\d{4})"
    r"|(\d{2})\.(\d{2})\.(\d{4})\s*\((?:Einreich|Antrags)?[Ff]rist"
)
_FRIST_MONAT_RE = re.compile(
    r"(?:Einreichfrist|Antragsfrist|Frist|Deadline)\s+(?:im|bis|zum|am|in|by)\s+"
    r"(Januar|Februar|März|April|Mai|Juni|Juli|August|September|Oktober|November|Dezember"
    r"|January|February|March|April|May|June|July|August|September|October|November|December)\s+(\d{4})"
)
_MONATSNAMEN = ("januar", "februar", "märz", "april", "mai", "juni", "juli", "august",
                "september", "oktober", "november", "dezember", "january", "february",
                "march", "april", "may", "june", "july", "august", "september", "october",
                "november", "december")


def _abgelaufene_frist(text: str) -> Optional[str]:
    m = _REPORT_DATUM_RE.search(text)
    if not m:
        return None
    heute = (int(m.group(3)), int(m.group(2)), int(m.group(1)))
    flach = _zellen_zusammenfuegen(text)
    for f in _FRIST_DATUM_RE.finditer(flach):
        t, mo, j = (f.group(1), f.group(2), f.group(3)) if f.group(1) else (f.group(4), f.group(5), f.group(6))
        if (int(j), int(mo), int(t)) < heute:
            return re.sub(r"\s+", " ", f.group(0))[:80]
    for f in _FRIST_MONAT_RE.finditer(flach):
        idx = _MONATSNAMEN.index(f.group(1).lower()) % 12 + 1
        if (int(f.group(2)), idx) < (heute[0], heute[1]):
            return f.group(0)[:80]
    return None


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
