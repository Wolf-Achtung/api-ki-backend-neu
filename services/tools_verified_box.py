# -*- coding: utf-8 -*-
"""KIS-1280: Die geprueften Tool-Daten sichtbar machen.

Ausgangslage (Lauf KIS-1265, drei Berichte untersucht): Die kuratierte
Liste ``data/tools_seed.json`` — 23 Werkzeuge mit Preis, DSGVO-Status,
Hosting und Trust-URL — erreichte keinen Leser. Zwei Wege fuehrten aus
der Datei heraus, beide endeten vorher:

  * ``services/tools_html_output.py`` — kein Aufrufer.
  * ``tools_funding_alignment`` — erzeugt den Block (nachgestellt: 6.089
    Zeichen, 8 Kombinationen), er sitzt aber in Anhang A12, und kein
    Anhang erscheint in den Berichten.

Was der Leser stattdessen sah: Werkzeugnamen, die das Sprachmodell
genannt hat — ohne belegten Preis, ohne belegten Datenschutzstatus, ohne
Link zur Anbieterseite. Fuer einen Bericht, der mit DSGVO-Konformitaet
wirbt, ist das die schwaechste Stelle.

Dieser Baustein rendert die kuratierten Daten deterministisch: kein
Modell dazwischen, keine Erfindung moeglich.

Die Regel, die alles andere traegt
----------------------------------
**Ein Preis erscheint nur mit Pruefdatum.** Stand 2026-09-04 haben 20
von 23 Eintraegen kein ``verified_at``. Diese Preise stammen aus der
Ersteingabe und hat niemand bestaetigt. Sie als Tatsache zu drucken
waere schlechter als der bisherige Zustand — der Leser wuerde einer Zahl
vertrauen, die keiner geprueft hat. Ohne Pruefdatum steht deshalb der
Verweis auf die Anbieterseite.

Nebenwirkung mit Absicht: Die Luecke wird sichtbar und schafft den
Anlass, die Preise zu bestaetigen. Der Tool-Radar meldet dieselben
Eintraege.
"""
from __future__ import annotations

import html
import logging
import os
from datetime import date, datetime
from typing import Any, Dict, List, Optional

log = logging.getLogger(__name__)

# Kill-Switch, falls der Block im Betrieb stoert.
VERIFIED_TOOLS_BOX_ENABLED = os.getenv("VERIFIED_TOOLS_BOX_ENABLED", "1").strip() == "1"

MAX_TOOLS_DEFAULT = int(os.getenv("VERIFIED_TOOLS_BOX_MAX", "6"))

_TEXTE = {
    "de": {
        "titel": "Geprüfte Werkzeug-Daten",
        "unterzeile": ("Aus der gepflegten Werkzeugliste — Datenschutzangaben "
                       "verlinkt, damit Sie sie selbst nachlesen können."),
        "sp_tool": "Werkzeug",
        "sp_kategorie": "Einsatzbereich",
        "sp_hosting": "Hosting / Datenschutz",
        "sp_preis": "Preis",
        "sp_beleg": "Beleg",
        "beleg_label": "Datenschutz",
        "kein_preis": "siehe Anbieterseite",
        "fuss_geprueft": "Preisangabe bestätigt am",
        # KIS-1282: Kein "wir". Eine globale Ersetzung in gpt_analyze.py
        # (\bwir\b -> ich, Berater-Stimme im Singular) traf im Lauf
        # KIS-1266 diesen festen Text und machte daraus "weisen ich nicht
        # aus". Die Regel tauscht Wörter, nicht Verbformen — statischer
        # Text muss ihr deshalb ausweichen.
        "fuss_ungeprueft": (
            "Ein Preis erscheint hier nur mit Prüfdatum. Den aktuellen "
            "Preis nennt der Anbieter auf der verlinkten Seite."),
    },
    "en": {
        "titel": "Verified tool data",
        "unterzeile": ("From the curated tool list — privacy statements linked "
                       "so you can check them yourself."),
        "sp_tool": "Tool",
        "sp_kategorie": "Use case",
        "sp_hosting": "Hosting / privacy",
        "sp_preis": "Price",
        "sp_beleg": "Source",
        "beleg_label": "Privacy",
        "kein_preis": "see vendor page",
        "fuss_geprueft": "Price confirmed on",
        "fuss_ungeprueft": (
            "Prices without a check date are not stated here. The vendor "
            "lists the current price on the linked page."),
    },
}


def _parse_datum(wert: Any) -> Optional[date]:
    s = str(wert or "").strip()
    if not s:
        return None
    for fmt in ("%Y-%m-%d", "%d.%m.%Y"):
        try:
            return datetime.strptime(s, fmt).date()
        except ValueError:
            continue
    return None


def preis_anzeige(tool: Dict[str, Any], texte: Dict[str, str]) -> str:
    """Preis nur mit Prüfdatum, sonst Verweis auf den Anbieter.

    Die eine Regel, die diesen Baustein von einer Behauptung
    unterscheidet.
    """
    if _parse_datum(tool.get("verified_at")) is None:
        return texte["kein_preis"]
    preis = str(tool.get("price") or "").strip()
    return preis or texte["kein_preis"]


def _zelle(text: str) -> str:
    return html.escape(str(text or "—").strip() or "—")


def _beleg(tool: Dict[str, Any], texte: Dict[str, str]) -> str:
    url = str(tool.get("trust_url") or "").strip()
    if not url.startswith(("http://", "https://")):
        return "—"
    return (f'<a href="{html.escape(url, quote=True)}">'
            f'{html.escape(texte["beleg_label"])}</a>')


def build_verified_tools_html(
    answers: Dict[str, Any],
    lang: str = "de",
    max_tools: int = MAX_TOOLS_DEFAULT,
    tools: Optional[List[Dict[str, Any]]] = None,
) -> str:
    """Deterministische Tabelle aus der kuratierten Werkzeugliste.

    Leerer String, wenn keine Werkzeuge vorliegen — dann faellt der Block
    im Template weg, statt eine leere Ueberschrift zu hinterlassen.
    """
    if not VERIFIED_TOOLS_BOX_ENABLED:
        return ""

    texte = _TEXTE.get(str(lang or "de").lower()[:2], _TEXTE["de"])

    if tools is None:
        try:
            from services.tools_recommender import recommend_tools
            tools = recommend_tools(answers, max_tools=max_tools)
        except Exception as exc:  # pragma: no cover - Schutznetz
            log.warning("[KIS-1280] Werkzeugliste nicht lesbar: %s", exc)
            return ""

    tools = [t for t in (tools or []) if str(t.get("name") or "").strip()][:max_tools]
    if not tools:
        return ""

    zeilen = []
    for t in tools:
        hosting = " · ".join(x for x in (str(t.get("host") or "").strip(),
                                         str(t.get("gdpr") or "").strip()) if x)
        zeilen.append(
            "<tr>"
            f"<td><strong>{_zelle(t.get('name'))}</strong></td>"
            f"<td>{_zelle(t.get('category'))}</td>"
            f"<td>{_zelle(hosting)}</td>"
            f"<td>{_zelle(preis_anzeige(t, texte))}</td>"
            f"<td>{_beleg(t, texte)}</td>"
            "</tr>"
        )

    geprueft = [d for d in (_parse_datum(t.get("verified_at")) for t in tools) if d]
    if geprueft:
        fuss = (f"{texte['fuss_geprueft']} "
                f"{max(geprueft).strftime('%d.%m.%Y')}. {texte['fuss_ungeprueft']}")
    else:
        fuss = texte["fuss_ungeprueft"]

    return (
        '<div class="verified-tools-box" style="margin-top:16px;">'
        f'<h3 style="margin:0 0 4px 0;font-size:15px;">{html.escape(texte["titel"])}</h3>'
        f'<p style="margin:0 0 8px 0;font-size:12px;color:#4b5563;">'
        f'{html.escape(texte["unterzeile"])}</p>'
        '<table class="verified-tools-table" style="width:100%;border-collapse:collapse;font-size:12px;">'
        "<thead><tr>"
        f"<th>{html.escape(texte['sp_tool'])}</th>"
        f"<th>{html.escape(texte['sp_kategorie'])}</th>"
        f"<th>{html.escape(texte['sp_hosting'])}</th>"
        f"<th>{html.escape(texte['sp_preis'])}</th>"
        f"<th>{html.escape(texte['sp_beleg'])}</th>"
        "</tr></thead>"
        f"<tbody>{''.join(zeilen)}</tbody>"
        "</table>"
        f'<p style="margin:6px 0 0 0;font-size:11px;color:#6b7280;">{html.escape(fuss)}</p>'
        "</div>"
    )


def inject_verified_tools(sections: Dict[str, Any], answers: Dict[str, Any],
                          lang: str = "de") -> Dict[str, Any]:
    """Setzt ``VERIFIED_TOOLS_HTML``. Fail-open: Fehler lassen den Bericht laufen."""
    try:
        sections["VERIFIED_TOOLS_HTML"] = build_verified_tools_html(answers, lang=lang)
    except Exception as exc:  # pragma: no cover - Schutznetz
        log.warning("[KIS-1280] Werkzeug-Block uebersprungen: %s", exc)
        sections.setdefault("VERIFIED_TOOLS_HTML", "")
    return sections
