# -*- coding: utf-8 -*-
"""KIS-1267: Strategie-Fragen aus den R1-Antworten ableiten statt neu fragen.

Wolf am 03.09.2026 zum Lauf KIS-1262: "viele Fragen die ich im
Strategie-Fragebogen ausfuellen muss, sind Wiederholungen aus dem
Status-Fragebogen."

Der Abgleich der beiden Fragebogen im Briefing-PDF bestaetigt das: von
14 Strategie-Feldern haben 11 eine Entsprechung in R1. Das kostet nicht
nur Zeit, es erzeugt Widersprueche — im Lauf KIS-1262 stand im
Status-Report "uebersteigt diesen Rahmen" und im Strategiebericht "ist
ausreichend", weil dieselbe Budget-Frage zweimal gestellt und zweimal
anders beantwortet wurde.

Dieses Modul leitet nur die Felder ab, fuer die es eine BELASTBARE
Zuordnung gibt. Bewusst NICHT abgeleitet:

  s1_budget          — gleiche Enum-Skala wie investitionsbudget, aber
                       die Zahl ist die wichtigste im ganzen Bericht.
                       Die bleibt eine bewusste Nutzer-Eingabe.
  s2_zeitrahmen      — kein R1-Gegenstueck.
  s3_prioritaeten    — ki_ziele ueberschneidet sich, deckt sich aber nicht.
  s4_engpass         — ki_hemmnisse ist Mehrfachauswahl, s4 genau eine.
  s5_software        — R1 fragt nach Business-Systemen (CRM/ERP), FB2
                       nach real genutzten Werkzeugen. Genau diese
                       Differenz ist im Report ein Erkenntnisgewinn.
  s5_vision          — Freitext, nicht ableitbar.
  s7_entscheidung    — kein R1-Gegenstueck.
  wettbewerber_anzahl— marktposition sagt WO man steht, nicht WIE VIELE
                       Wettbewerber es gibt. Eine Ableitung waere geraten.
  kundenbindung_typ  — zielgruppen (B2B/KMU) sagt nichts ueber die Art
                       der Kundenbeziehung.

Geraten wird hier nichts: Fehlt die Quelle, fehlt die Ableitung, und die
Frage wird ganz normal gestellt.
"""
from __future__ import annotations

import logging
from typing import Any, Dict, List

log = logging.getLogger(__name__)

# Felder, die dieses Modul ableiten kann (Reihenfolge = Log-Reihenfolge).
ABLEITBARE_FELDER = (
    "s6_foerderinteresse",
    "s8_erfahrung",
    "s9_ansatz",
    "s10_datenschutz",
    "datenreife",
)

# s9_ansatz: 1:1, beide Enums beschreiben dasselbe.
_INFRASTRUKTUR = {
    "cloud": "Cloud-SaaS",
    "on_premise": "On-Premise",
    "hybrid": "Hybrid",
    "unklar": "Egal",
}

# s6_foerderinteresse: R1 kennt drei Stufen, FB2 vier.
_FOERDERINTERESSE = {
    "ja": "Ja, wenn passend",
    "nein": "Nein, eigenes Budget",
    "unklar": "Weiß nicht",
}

# Branchen, die schon per se eine hohe Datenschutz-Prioritaet bedeuten.
_REGULIERT = {"gesundheit", "finanzen", "oeffentlich", "recht", "vertraulich_nda"}


def _norm(wert: Any) -> str:
    """Skalar klein und ohne Rand. Listen bleiben Listen — dafuer _liste."""
    if isinstance(wert, (list, tuple, set)):
        return ""
    return str(wert or "").strip().lower()


def _liste(wert: Any) -> List[str]:
    """Mehrfachauswahl robust einlesen: Liste oder kommagetrennter String."""
    if isinstance(wert, (list, tuple, set)):
        roh = [str(v) for v in wert]
    else:
        roh = str(wert or "").split(",")
    return [e.strip().lower() for e in roh if e and e.strip()]


def _zahl(wert: Any) -> float:
    try:
        return float(str(wert).replace(",", "."))
    except (ValueError, TypeError):
        return 0.0


def _erfahrung(a: Dict[str, Any]) -> str:
    """s8_erfahrung aus ki_einsatz + ki_projekte + ki_kompetenz.

    Lauf KIS-1262: ki_einsatz "produktion", ki_projekte "noch keine",
    ki_kompetenz "mittel" — Wolf hat selbst "Experimentiert" gewaehlt.
    """
    einsatz = [e for e in _liste(a.get("ki_einsatz")) if e != "noch_keine"]
    projekte = _norm(a.get("ki_projekte"))
    kompetenz = _norm(a.get("ki_kompetenz") or a.get("ki_knowhow"))

    hat_projekte = bool(projekte) and not any(
        marker in projekte for marker in ("noch keine", "noch_keine", "keine projekte", "nein")
    )

    if not einsatz and not hat_projekte:
        if kompetenz in ("keine", "niedrig"):
            return "Noch keine"
        return ""  # zu duenn fuer eine Ableitung — lieber fragen
    if hat_projekte:
        return "Fortgeschritten" if kompetenz == "hoch" else "Erste Tools im Einsatz"
    return "Experimentiert"


def _datenschutz(a: Dict[str, Any]) -> str:
    """s10_datenschutz aus regulierter Branche und vorhandenen Maßnahmen."""
    reguliert = [b for b in _liste(a.get("regulierte_branche")) if b and b != "keine"]
    dsb = _norm(a.get("datenschutzbeauftragter"))
    massnahmen = _norm(a.get("technische_massnahmen"))

    if any(b in _REGULIERT for b in reguliert) or dsb == "ja":
        return "Hoch"
    if not reguliert and massnahmen == "keine" and dsb == "nein":
        return "Niedrig"
    if massnahmen or dsb:
        return "Mittel"
    return ""


def _datenreife(a: Dict[str, Any]) -> str:
    """datenreife aus Datenquellen und Digitalisierungsgrad.

    Genau dieses Feld hat im Lauf KIS-1262 ein erfundenes Zitat erzeugt:
    R1 fragt es nie, der Report las das leere Feld als "keine".
    """
    quellen = _liste(a.get("datenquellen"))
    digi = _zahl(a.get("digitalisierungsgrad"))
    if not quellen:
        return ""  # ohne Quelle keine Aussage — Frage stellen
    return "umfangreich" if digi >= 7 else "basis"


def ableiten_aus_r1(r1_antworten: Dict[str, Any] | None) -> Dict[str, str]:
    """Liefert die aus R1 belegbaren Strategie-Felder.

    Nur Felder mit belastbarer Quelle. Leere Ableitungen fallen raus —
    die zugehoerige Frage wird dann ganz normal gestellt.
    """
    a = r1_antworten or {}
    if not isinstance(a, dict):
        return {}

    kandidaten = {
        "s6_foerderinteresse": _FOERDERINTERESSE.get(_norm(a.get("interesse_foerderung")), ""),
        "s8_erfahrung": _erfahrung(a),
        "s9_ansatz": _INFRASTRUKTUR.get(_norm(a.get("it_infrastruktur")), ""),
        "s10_datenschutz": _datenschutz(a),
        "datenreife": _datenreife(a),
    }
    return {feld: wert for feld, wert in kandidaten.items() if wert}
