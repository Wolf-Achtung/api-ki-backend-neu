# -*- coding: utf-8 -*-
"""KIS-1288: Die Sparte — ein Baustein, eine Wahrheit.

Der Fragebogen erhebt ``medien_sparte`` mit sieben Werten
(``field_registry.py``). Bis zum Branchen-Audit vom 04.09.2026 erreichte
die Sparte drei Stellen: einen Prompt, die Fallstudie, das Deckblatt.
Der Strategiebericht, die Potenzialanalyse und der Resilienz-Check
kannten sie nicht — und der Resilienz-Check fuehrte seine eigene
Slug-Liste mit drei falschen Schluesseln.

Dieser Baustein liefert das Label, deutsch oder englisch, aus der
Referenz. Wer die Sparte braucht, holt sie hier.
"""
from __future__ import annotations

from typing import Dict, List, Optional

# Referenz: field_registry.fields["medien_sparte"]["options"].
# Hier gespiegelt, damit der Baustein ohne das 70-KB-Registry importierbar
# bleibt; ein Test haelt beide Listen gleich.
SPARTEN: List[str] = [
    "produktion",
    "post_vfx",
    "games",
    "verlag_publishing",
    "musik_audio",
    "agentur_design",
    "content_creation",
]

LABELS_DE: Dict[str, str] = {
    "produktion": "Film-/TV-Produktion",
    "post_vfx": "Postproduktion / VFX / Animation",
    "games": "Games / Interactive",
    "verlag_publishing": "Verlag / Publishing / Redaktion",
    "musik_audio": "Musik / Audio / Tonstudio / Podcast",
    "agentur_design": "Agentur / Werbung / PR / Webdesign",
    "content_creation": "Content Creation / Social Media",
}

LABELS_EN: Dict[str, str] = {
    "produktion": "Film/TV production",
    "post_vfx": "Post-production / VFX / animation",
    "games": "Games / interactive",
    "verlag_publishing": "Publishing / editorial",
    "musik_audio": "Music / audio / recording studio / podcast",
    "agentur_design": "Agency / advertising / PR / web design",
    "content_creation": "Content creation / social media",
}

# Deutsche Anzeige-Labels zurueck auf den Slug — manche Pfade tragen das
# Label statt des Werts (KIS-1251).
_LABEL_TO_SLUG: Dict[str, str] = {
    **{v.lower(): k for k, v in LABELS_DE.items()},
    **{v.lower(): k for k, v in LABELS_EN.items()},
}


def slug(wert: Optional[str]) -> str:
    """Normalisiert Rohwert oder Anzeige-Label auf den Slug; leer, wenn unbekannt."""
    s = str(wert or "").strip().lower()
    if not s:
        return ""
    if s in LABELS_DE:
        return s
    return _LABEL_TO_SLUG.get(s, "")


def label(wert: Optional[str], lang: str = "de") -> str:
    """Anzeige-Label zur Sparte. Unbekannte Werte bleiben leer — kein Roh-Slug
    landet je im Bericht."""
    s = slug(wert)
    if not s:
        return ""
    if str(lang or "de").lower().startswith("en"):
        return LABELS_EN.get(s, "")
    return LABELS_DE.get(s, "")


def aus_antworten(answers: Optional[dict], lang: str = "de") -> str:
    """Label direkt aus einem Antwort-Dict (``medien_sparte``)."""
    if not answers:
        return ""
    return label(answers.get("medien_sparte"), lang=lang)
