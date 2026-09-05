# -*- coding: utf-8 -*-
"""KIS-1298: Erfundene Förder-Platzhalter im R1-Förderkapitel ersetzen.

Bis Lauf KIS1274 löschte ``gpt_analyze`` jede HTML-Zeile des Kapitels
„Förderpotenzial", die „Digitalprämie" oder „Ihr Bundesland" enthielt
(FIX-KIS-1098-R1-FUNDING-2). Das Modell schreibt gern „regionale
Digitalprämien" — und weil eine LLM-Zeile meist ein ganzes Element ist,
verschwanden Listen, Überschriften und die Abschnitte 2, 3 und 5 des
Kapitels („kommen vor allem folgende Kategorien infrage:" ohne Liste,
seit mindestens Lauf KIS1269).

Jetzt: Platzhalter werden durch den echten Wert oder einen ehrlichen
Gattungsbegriff ersetzt. Gelöscht werden nur noch Zeilen mit
Fremdprogrammen (Österreich, Schweiz, UK), die ein deutscher Kunde nicht
beantragen kann.
"""
from __future__ import annotations

import re
from typing import List, Tuple

# Programme anderer Länder — für DE-Kunden nicht beantragbar.
FREMDPROGRAMM_MARKER: Tuple[str, ...] = (
    "aws digi", "Forschungsprämie", "forschungsprämie",
    "digi4KMU", "digi4kmu", "Innosuisse", "innosuisse",
    "Innovate UK", "innovate uk",
    "Österreich", "österreich", "Schweiz", "schweiz",
)

_BUNDESLAND_RE = re.compile(r"Ihr[_ ]Bundesland", re.IGNORECASE)
_DIGITALPRAEMIE_RE = re.compile(r"(?:regionale[nr]?\s+)?Digitalprämien?", re.IGNORECASE)
_DIGITALPRAEMIE_ERSATZ = "Landesprogramme zur Digitalisierung"


def ersetze_platzhalter(html: str, bundesland_label: str = "") -> Tuple[str, int]:
    """Ersetzt „Ihr Bundesland" durch das echte Land und „Digitalprämie"
    durch einen Gattungsbegriff. Liefert (html, Anzahl Ersetzungen)."""
    if not html:
        return html, 0
    ersatz = (bundesland_label or "").strip() or "Ihre Region"
    html, n_bl = _BUNDESLAND_RE.subn(ersatz, html)
    html, n_dp = _DIGITALPRAEMIE_RE.subn(_DIGITALPRAEMIE_ERSATZ, html)
    return html, n_bl + n_dp


def entferne_fremdprogramme(html: str) -> Tuple[str, int]:
    """Löscht Zeilen, die ein Fremdprogramm als Hauptgegenstand haben.
    Listenpunkte und Tabellenzeilen fallen ganz; Fließtext nur, wenn das
    Fremdprogramm am Zeilenanfang steht."""
    if not html:
        return html, 0
    behalten: List[str] = []
    entfernt = 0
    for zeile in html.split("\n"):
        treffer = [m for m in FREMDPROGRAMM_MARKER if m in zeile]
        if treffer:
            klein = zeile.lower()
            if "<tr" in klein or "<li" in klein or "<td" in klein:
                entfernt += 1
                continue
            if zeile.strip().startswith("<") or any(m in zeile[:80] for m in treffer):
                entfernt += 1
                continue
        behalten.append(zeile)
    return ("\n".join(behalten) if entfernt else html), entfernt
