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


def _tool_zeile(t: Dict[str, Any], mit_url: bool = False) -> str:
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
    # KIS-1293: Der Strategiebericht verlangt Quellenangaben — ohne URL im
    # Block erfand das Modell „Vendor-Audit-Status Report 1 (Kundenunterlagen)".
    if mit_url and t.get("url"):
        teile.append(str(t["url"]).strip())
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


_KOPF_TOOLS_STRATEGIE_DE = (
    "\n\n=== GEPRÜFTE WERKZEUG-DATEN (VERBINDLICH FÜR DIESE SECTION) ===\n"
    "Diese Liste wird redaktionell gepflegt. Regeln:\n"
    "- Nenne als konkrete Produkte AUSSCHLIESSLICH Werkzeuge aus dieser Liste "
    "oder Software, die der Kunde laut Stack bereits nutzt (und deren "
    "hauseigene KI-Zusätze, z. B. Copilot bei Microsoft 365). Ein anderes "
    "Produkt existiert für diese Section nicht — auch nicht aus der "
    "Live-Recherche. Gattungsbegriffe ('Schnittsoftware', "
    "'Compliance-Werkzeug') sind erlaubt.\n"
    "- Preise: nur die Art (Abonnement, nutzungsbasiert, im Abo enthalten) — "
    "keine Beträge.\n"
    "- Datenschutz: übernimm die Hosting-Angabe aus der Liste wörtlich. "
    "Erfinde keine eigene Einstufung, keinen Audit-Status und keine Quelle. "
    "Der Vendor-Audit-Status aus Report 1 gilt für die Werkzeuge, die der "
    "Kunde im Fragebogen genannt hat — nie für ein empfohlenes Werkzeug.\n"
    "- Stack-Software ohne Zeile in dieser Liste (z. B. Microsoft 365 Copilot): "
    "Datenschutz = 'laut Anbieter prüfen'. Übernimm nie die Hosting-Angabe "
    "einer anderen Zeile.\n"
    "- US-Anbieter aus dem Stack (ChatGPT/OpenAI, Claude/Anthropic, Perplexity, "
    "Gemini, Midjourney): Datenschutz = 'US-Anbieter, AVV prüfen'. Nenne sie nie "
    "'EU-konform', 'EU-gehostet' oder 'EU / EU'. Eine EU-Alternative ist nur ein "
    "Werkzeug, dessen Zeile in dieser Liste EU als Hosting nennt.\n"
    "- 'Nicht bestanden' aus dem Vendor-Audit steht nur bei Werkzeugen, die der "
    "Kunde im Fragebogen genannt hat, und heißt 'mit AVV nutzbar' — nie bei "
    "Runway, Make oder einem anderen empfohlenen Werkzeug.\n"
    "- Quellen am Ende: nur die Anbieteradressen aus dieser Liste.\n\n"
)
_KOPF_TOOLS_STRATEGIE_EN = (
    "\n\n=== VERIFIED TOOL DATA (BINDING FOR THIS SECTION) ===\n"
    "This list is maintained editorially. Rules:\n"
    "- Name as concrete products ONLY tools from this list or software the "
    "client already uses according to the stack (and its built-in AI add-ons, "
    "e.g. Copilot with Microsoft 365). Any other product does not exist for "
    "this section — not even from the live research. Generic terms "
    "('editing software', 'compliance tool') are allowed.\n"
    "- Prices: only the type (subscription, usage-based, included) — no amounts.\n"
    "- Data protection: quote the hosting note from the list verbatim. Do not "
    "invent a rating, an audit status or a source. The vendor audit status "
    "from Report 1 applies to the tools the client named in the questionnaire "
    "— never to a recommended tool.\n"
    "- Stack software without a row in this list (e.g. Microsoft 365 Copilot): "
    "data protection = 'check with the vendor'. Never copy the hosting note "
    "of another row.\n"
    "- US vendors from the stack (ChatGPT/OpenAI, Claude/Anthropic, Perplexity, "
    "Gemini, Midjourney): data protection = 'US vendor, check DPA'. Never call "
    "them 'EU-compliant', 'EU-hosted' or 'EU / EU'. An EU alternative is only a "
    "tool whose row in this list names EU hosting.\n"
    "- 'Failed' from the vendor audit applies only to tools the client named in "
    "the questionnaire and means 'usable with a DPA' — never to Runway, Make or "
    "any other recommended tool.\n"
    "- Sources at the end: only the vendor addresses from this list.\n\n"
)
_FALLBACK_TOOLS_DE = (
    "\n\n=== WERKZEUG-DATEN ===\nKein Faktenblock verfügbar. Nenne als konkrete "
    "Produkte nur Software aus dem Stack des Kunden; sonst Gattungsbegriffe. "
    "Keine Preise, keine Datenschutz-Einstufungen, kein Audit-Status.\n\n"
)
_FALLBACK_TOOLS_EN = (
    "\n\n=== TOOL DATA ===\nNo fact block available. Name as concrete products "
    "only software from the client's stack; otherwise generic terms. No prices, "
    "no data protection ratings, no audit status.\n\n"
)


def build_tool_fakten_strategie(answers: Dict[str, Any], lang: str = "de",
                                max_tools: int = MAX_TOOLS) -> str:
    """KIS-1293: Faktenblock für S4 des Strategieberichts.

    S4 hatte bis Lauf KIS1272 keinen Faktenblock und erfand Produkte
    („Adobe Sensei", „Legiscope"), Preismodelle, DSGVO-Einstufungen und
    einen „Vendor-Audit-Status: nicht bestanden" für Claude und Runway.
    Nie leer: ohne Daten kommt die Rückfall-Regel, damit die Section nicht
    frei erfindet.
    """
    en = str(lang or "de").lower().startswith("en")
    try:
        from services.tools_recommender import recommend_tools
        tools = recommend_tools(answers, max_tools=max_tools) or []
    except Exception as exc:
        log.warning("[KIS-1293] Werkzeugliste nicht lesbar: %s", exc)
        tools = []
    zeilen = [z for z in (_tool_zeile(t, mit_url=True) for t in tools[:max_tools]) if z]
    if not zeilen:
        return _FALLBACK_TOOLS_EN if en else _FALLBACK_TOOLS_DE
    kopf = _KOPF_TOOLS_STRATEGIE_EN if en else _KOPF_TOOLS_STRATEGIE_DE
    return kopf + "\n".join(zeilen) + "\n" + _FUSS


def tool_namen_strategie(answers: Dict[str, Any], max_tools: int = MAX_TOOLS) -> str:
    """KIS-1293: Nur die Namen — für Sections, die Werkzeuge nebenbei nennen
    (S3b „KI-Hebel"). Lauf KIS1273 nannte dort „Adobe Sensei" und „Azure
    Cognitive Services", weil nur S4 den vollen Block bekam."""
    try:
        from services.tools_recommender import recommend_tools
        tools = recommend_tools(answers, max_tools=max_tools) or []
    except Exception as exc:
        log.warning("[KIS-1293] Werkzeugnamen nicht lesbar: %s", exc)
        tools = []
    namen = [str(t.get("name") or "").strip() for t in tools[:max_tools]]
    namen = [n for n in namen if n]
    return ", ".join(namen) if namen else "(keine Liste — nur Stack oder Gattungsbegriff)"


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
