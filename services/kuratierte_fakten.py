# -*- coding: utf-8 -*-
"""KIS-1281, Stufe 1: Das Modell darf keine Tatsachen mehr erfinden.

Im Report stehen zwei Sorten Aussagen, und bisher erzeugte das
Sprachmodell beide:

  * **Prüfbare Tatsache** — „Tally kostet 29 €/Monat", „ZIM nimmt keine
    Anträge an". Die gehört aus gepflegten Daten.
  * **Beratende Einordnung** — „Für Ihre Postproduktion lohnt sich
    zuerst der Schnitt". Die gehört zum Modell.

Weil beide aus derselben Quelle kamen, stand ZIM in einem Report,
obwohl das Programm seit Juli 2026 pausiert, und der Werkzeug-Abschnitt
nannte Software ohne belegte Datenschutzlage.

Dieser Baustein reicht die gepflegten Daten als Faktenblock in die
Prompts von ``tools_empfehlungen`` und ``foerderpotenzial``. Er ergänzt
den Live-Recherche-Block aus ``research_grounding`` — mit einem
Unterschied: Er braucht kein Netz. Fällt Tavily aus, stehen die
kuratierten Tatsachen trotzdem im Prompt.

Die Regel im Block ist eng gefasst: Nenne nur, was hier steht. Ein
Werkzeug oder Programm, das fehlt, existiert für diesen Abschnitt nicht.
"""
from __future__ import annotations

import logging
import os
from typing import Any, Dict, List

log = logging.getLogger(__name__)

KURATIERTE_FAKTEN_ENABLED = (
    os.getenv("KURATIERTE_FAKTEN_ENABLED", "1").strip() == "1"
)

MAX_TOOLS = int(os.getenv("KURATIERTE_FAKTEN_MAX_TOOLS", "10"))
MAX_PROGRAMME = int(os.getenv("KURATIERTE_FAKTEN_MAX_PROGRAMME", "12"))

_KOPF_TOOLS = (
    "\n\n=== GEPRÜFTE WERKZEUG-DATEN ===\n"
    "Diese Liste wird redaktionell gepflegt. VERBINDLICH:\n"
    "- Nenne als konkrete Produkte AUSSCHLIESSLICH Werkzeuge aus dieser "
    "Liste. Ein Werkzeug, das hier fehlt, existiert für diesen Abschnitt "
    "nicht.\n"
    "- Übernimm KEINE Preise und KEINE Datenschutz-Einstufungen in den "
    "Fließtext. Beides steht in der Tabelle unter dem Abschnitt; eine "
    "Wiederholung im Text veraltet und widerspricht ihr irgendwann.\n"
    "- Deine Aufgabe ist die Einordnung: Warum passt dieses Werkzeug zu "
    "diesem Betrieb, in welcher Reihenfolge, mit welchem ersten Schritt.\n"
    "- Kategorien und Gattungsbegriffe („Schnittsoftware\", "
    "„Transkriptionsdienst\") darfst du frei verwenden.\n\n"
)

_KOPF_FOERDER = (
    "\n\n=== GEPRÜFTE FÖRDERPROGRAMME ===\n"
    "Diese Programme sind auf Stand geprüft und antragsfähig. "
    "VERBINDLICH:\n"
    "- Nenne AUSSCHLIESSLICH Programme aus dieser Liste. Programme "
    "ausserhalb sind entweder ausgelaufen, pausiert oder nicht geprüft.\n"
    "- Übernimm Förderquoten, Beträge und Fristen NUR so, wie sie hier "
    "stehen. Erfinde keine Zahlen dazu.\n"
    "- Deine Aufgabe ist die Einordnung: Welches Programm passt zu "
    "diesem Vorhaben, warum, und was ist der erste Schritt.\n\n"
)

_FUSS = "=== ENDE ===\n"


def _tool_zeile(t: Dict[str, Any]) -> str:
    name = str(t.get("name") or "").strip()
    if not name:
        return ""
    teile = [name]
    if t.get("category"):
        teile.append(str(t["category"]).strip())
    hosting = " / ".join(x for x in (str(t.get("host") or "").strip(),
                                     str(t.get("gdpr") or "").strip()) if x)
    if hosting:
        teile.append(f"Hosting: {hosting}")
    return "- " + " | ".join(teile)


def build_tool_fakten(answers: Dict[str, Any], max_tools: int = MAX_TOOLS) -> str:
    """Faktenblock aus ``data/tools_seed.json`` — ohne Preise.

    Preise fehlen mit Absicht: 20 von 23 Einträgen tragen kein
    Prüfdatum (Stand 04.09.2026). Was der Mensch nicht bestätigt hat,
    soll das Modell nicht in den Fließtext schreiben. Die geprüften
    Angaben zeigt der Tabellen-Block (KIS-1280).
    """
    try:
        from services.tools_recommender import recommend_tools
        tools = recommend_tools(answers, max_tools=max_tools) or []
    except Exception as exc:
        log.warning("[KIS-1281] Werkzeugliste nicht lesbar: %s", exc)
        return ""

    zeilen = [z for z in (_tool_zeile(t) for t in tools[:max_tools]) if z]
    if not zeilen:
        return ""
    return _KOPF_TOOLS + "\n".join(zeilen) + "\n" + _FUSS


def _programm_zeile(p: Dict[str, Any]) -> str:
    name = str(p.get("title") or p.get("name") or "").strip()
    if not name:
        return ""
    teile = [name]
    # Die Feldnamen der Kernmatrix. Genau diese Angaben darf das Modell
    # uebernehmen — deshalb muessen sie im Block stehen, sonst fuellt es
    # die Luecke aus dem Trainingswissen.
    for schluessel, etikett in (("region", ""),
                                ("funding_type", ""),
                                ("funding_rate", "Quote"),
                                ("max_amount", "bis"),
                                ("deadline", "Frist"),
                                ("focus", "Schwerpunkt")):
        wert = str(p.get(schluessel) or "").strip()
        if not wert or wert.lower() == "none":
            continue
        # "bis" + "bis 2,5 Mio €" ergibt "bis bis 2,5 Mio €".
        if etikett and wert.lower().startswith(etikett.lower()):
            etikett = ""
        teile.append(f"{etikett} {wert}".strip() if etikett else wert)
    return "- " + " | ".join(teile)


def build_foerder_fakten(answers: Dict[str, Any],
                         max_programme: int = MAX_PROGRAMME) -> str:
    """Faktenblock aus der Kern-Fördermatrix.

    ``load_funding_programs`` filtert bereits über
    ``funding_recommender.ist_beantragbar`` — ausgelaufene und pausierte
    Programme (ZIM seit 07.07.2026) sind hier nicht enthalten.
    """
    try:
        from services.funding_recommender import load_funding_programs
        programme = load_funding_programs() or []
    except Exception as exc:
        log.warning("[KIS-1281] Förderliste nicht lesbar: %s", exc)
        return ""

    zeilen = [z for z in (_programm_zeile(p) for p in programme[:max_programme]) if z]
    if not zeilen:
        return ""
    return _KOPF_FOERDER + "\n".join(zeilen) + "\n" + _FUSS


def build_kuratierte_grounding(answers: Dict[str, Any]) -> Dict[str, str]:
    """{Sektionsname: Faktenblock}. Fail-open: Fehler ergeben ein leeres Dict."""
    if not KURATIERTE_FAKTEN_ENABLED:
        log.info("[KIS-1281] kuratierte Fakten per ENV abgeschaltet")
        return {}

    grounding: Dict[str, str] = {}
    try:
        tools = build_tool_fakten(answers)
        if tools:
            grounding["tools_empfehlungen"] = tools
        foerder = build_foerder_fakten(answers)
        if foerder:
            grounding["foerderpotenzial"] = foerder
    except Exception as exc:  # pragma: no cover - Schutznetz
        log.warning("[KIS-1281] Faktenblöcke übersprungen: %s", exc)
        return {}

    if grounding:
        log.info("[KIS-1281] Faktenblöcke für %d Sektion(en): %s",
                 len(grounding), ", ".join(sorted(grounding)))
    return grounding


def verbinde_grounding(*quellen: Dict[str, str]) -> Dict[str, str]:
    """Führt mehrere Grounding-Dicts je Sektion zusammen.

    Die kuratierten Fakten und die Live-Recherche schliessen einander
    nicht aus: Die Liste sagt, WAS genannt werden darf, die Recherche
    liefert aktuelle Einordnung dazu. Wer eines der beiden verwirft,
    verliert entweder die Aktualität oder die Verlässlichkeit.
    """
    zusammen: Dict[str, List[str]] = {}
    for quelle in quellen:
        for sektion, block in (quelle or {}).items():
            if block:
                zusammen.setdefault(sektion, []).append(block)
    return {sektion: "".join(bloecke) for sektion, bloecke in zusammen.items()}
