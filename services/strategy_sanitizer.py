"""
Strategy Fact Sanitizer (FIX-SF1)
Fängt LLM-Halluzinationen in Strategy-Sektionen ab.
Läuft NACH der LLM-Generierung, VOR dem Renderer.
"""

import re
import logging
from datetime import date
from typing import Optional

log = logging.getLogger(__name__)


def beraterstimme_in_singular(html: str):
    """KIS-1283, fail-open: Ohne den Baustein bleibt der Text, wie er ist."""
    try:
        from services.beraterstimme import in_singular
        return in_singular(html)
    except Exception as exc:  # pragma: no cover - Schutznetz
        log.debug("[KIS-1283] Beraterstimme nicht verfuegbar: %s", exc)
        return html, 0

# ── Pass 1: Plausibilitätsprüfung für Prozentwerte ──────────────────

# Kontextwörter die auf Adoptions-/Nutzungs-Metriken hindeuten
_ADOPTION_CONTEXT = re.compile(
    r'(nutz|adopt|einsatz|einsetzen|verwend|implementier|test|erpro|anwend|verbreit)',
    re.IGNORECASE
)

# ROI-Kontext-Keywords: Prozentwerte >100% sind hier normal und valide
ROI_CONTEXT_KEYWORDS = [
    "roi", "return on investment", "rendite", "amortisation", "amortisierung",
    "break-even", "break even", "breakeven", "nettonutzen", "netto-nutzen",
    "szenario", "konservativ", "realistisch", "optimistisch",
    "investition", "kapitalrendite", "wirtschaftlichkeit",
]

# Prozentwert-Pattern: fängt "104%", "104 %", "104,5%", "104.5 %" etc.
_PERCENT_PATTERN = re.compile(
    r'(\d{1,4}[.,]?\d{0,2})\s*%'
)


def _is_roi_context(text: str, match_start: int, match_end: int) -> str | None:
    """Check if percentage is in ROI context (where >100% is valid).

    Returns the matched keyword if ROI context detected, None otherwise.
    """
    context_window = 200
    start = max(0, match_start - context_window)
    end = min(len(text), match_end + context_window)
    context = text[start:end].lower()
    for kw in ROI_CONTEXT_KEYWORDS:
        if kw in context:
            return kw
    return None


def _check_percent_plausibility(html: str, section_key: str) -> tuple[str, list[str]]:
    """
    Scannt HTML auf Prozentwerte >100% in Adoptions-/Nutzungs-Kontexten.
    Gibt (ggf. gepatchtes HTML, Liste von Warnings) zurück.

    Strategie:
    - Für jeden Prozentwert >100%: prüfe ob im umgebenden Text (±200 Zeichen)
      ein Adoptions-Kontextwort vorkommt
    - Wenn ja: ersetze mit "–*" (Auslassung) um keinen falschen Wert anzuzeigen
    """
    warnings = []
    offset_adjustment = 0

    for match in _PERCENT_PATTERN.finditer(html):
        try:
            val = float(match.group(1).replace(',', '.'))
        except ValueError:
            continue

        if val > 100.0:
            start = max(0, match.start() - 200)
            end = min(len(html), match.end() + 200)
            context = html[start:end]

            # FIX-SF1v2: Skip ROI context — >100% is valid for ROI values
            roi_kw = _is_roi_context(html, match.start(), match.end())
            if roi_kw:
                log.debug(
                    "[FIX-SF1-SKIP] '%s' in %s is ROI context (keyword: '%s') — not patched",
                    match.group(0), section_key, roi_kw
                )
                continue

            if _ADOPTION_CONTEXT.search(context):
                warning = (
                    f"[FIX-SF1] Section '{section_key}': "
                    f"Implausible percentage {val}% in adoption/usage context. "
                    f"Context: ...{context[max(0, match.start() - start - 30):match.end() - start + 30]}..."
                )
                log.warning(warning)
                warnings.append(warning)

                old = match.group(0)
                adj_start = match.start() + offset_adjustment
                adj_end = match.end() + offset_adjustment
                replacement = "\u2013*"
                html = html[:adj_start] + replacement + html[adj_end:]
                offset_adjustment += len(replacement) - len(old)

                log.info(
                    "[FIX-SF1] Patched '%s' → '–*' in %s "
                    "(implausible adoption percentage >100%%)",
                    old, section_key
                )

    return html, warnings


# ── Pass 2: Benchmark table >100% validator (FIX-KIS-1082) ──────────

_TABLE_RE = re.compile(r'<table[^>]*>.*?</table>', re.DOTALL | re.IGNORECASE)

def _check_table_consistency(html: str, section_key: str) -> tuple[list[str], str]:
    """
    FIX-KIS-1082: In benchmark tables (S2), percentage values >100% are
    ALWAYS invalid (benchmark = market data, not financial returns).
    Patches them to "–*" and logs a warning.
    Also catches non-S2 table issues (placeholder for v2).
    """
    if section_key != "S2":
        return [], html

    warnings = []

    def _patch_table_percents(table_match):
        table_html = table_match.group(0)

        def _replace_over100(m):
            try:
                val = float(m.group(1).replace(',', '.'))
            except ValueError:
                return m.group(0)
            if val > 100.0:
                warnings.append(
                    f"[FIX-KIS-1082] Section '{section_key}': "
                    f"Benchmark table value {val}% > 100% — likely ROI leak. Patched to '–*'."
                )
                log.warning(warnings[-1])
                return "\u2013*"
            return m.group(0)

        return _PERCENT_PATTERN.sub(_replace_over100, table_html)

    new_html = _TABLE_RE.sub(_patch_table_percents, html)
    return warnings, new_html


# ── Pass 3: Jahres-Zuordnungs-Check ─────────────────────────────────

_YEAR_PERCENT = re.compile(
    r'(20[0-9]{2})\D{0,20}?(\d{1,3}[.,]?\d{0,2})\s*%',
    re.IGNORECASE
)


def _check_year_data_freshness(html: str, section_key: str, report_year: int = 2026) -> list[str]:
    """
    Warnt wenn Daten mit Jahreszahlen >report_year zitiert werden
    (kann nicht existieren) oder wenn Daten sehr alt sind (>3 Jahre).
    """
    warnings = []
    for match in _YEAR_PERCENT.finditer(html):
        year = int(match.group(1))
        if year > report_year:
            warnings.append(
                f"[FIX-SF1] Section '{section_key}': "
                f"Future year {year} cited with data ({match.group(0)})"
            )
            log.warning(warnings[-1])
    return warnings


# ── Pass 4: Plain-Language Safety Net (S31-FIX-B) ────────────────────
# Catches common jargon that the LLM may still produce despite prompt instructions.
# Only replaces in running text (<p>, <li>), not in table headers or headings.

_PLAIN_LANGUAGE_RULES = [
    # (pattern, replacement, flags)
    (r'\bUse\s+Cases?\b', 'Anwendungsbeispiele', 0),
    (r'\bUse\s+Case\b', 'Anwendungsbeispiel', 0),
    (r'\bStakeholder[ns]?\b', 'Beteiligte', 0),
    (r'\bBest\s+Practices?\b', 'bewährte Methoden', 0),
    (r'\bBest\s+Practice\b', 'bewährte Methode', 0),
    (r'\bOnboarding[s]?\b', 'Einarbeitung', re.IGNORECASE),
    (r'\bEnd-to-End\b', 'durchgängig', re.IGNORECASE),
    (r'\bOrchestrier\w+\b', 'Steuerung', 0),
    (r'\borchestrier\w+\b', 'Steuerung', 0),
]

# HTML tag pattern to identify text segments (only replace in <p> and <li> content)
_TEXT_TAG_RE = re.compile(r'(<(?:p|li)\b[^>]*>)(.*?)(</(?:p|li)>)', re.DOTALL | re.IGNORECASE)


def _apply_plain_language(html: str, section_key: str) -> tuple:
    """Replace jargon with plain German in running text only."""
    fixes = []

    def _replace_in_tag(m):
        prefix, content, suffix = m.group(1), m.group(2), m.group(3)
        new_content = content
        for pattern, replacement, flags in _PLAIN_LANGUAGE_RULES:
            new_content = re.sub(pattern, replacement, new_content, flags=flags)
        if new_content != content:
            fixes.append(f"{section_key}: plain-language substitution")
        return prefix + new_content + suffix

    new_html = _TEXT_TAG_RE.sub(_replace_in_tag, html)
    return new_html, fixes


# ── KIS-1305: Verordnungsnummer des AI Act ───────────────────────────

AI_ACT_VERORDNUNG = "(EU) 2024/1689"
# „EU AI Act (Verordnung 2021/0691)", „KI-Verordnung (EU) 2021/0206",
# „AI Act, Regulation (EU) 2023/1234" — die Nummer folgt dem Namen innerhalb
# weniger Zeichen. Nur Jahr/Nummer-Paare werden angefasst, nie Artikel.
_AI_ACT_NUMMER_RE = re.compile(
    r"((?:EU[\s-]*AI[\s-]*Act|AI[\s-]*Act|KI-Verordnung|AI Regulation)"
    r"[^.\n<>]{0,25}?(?:Verordnung|Regulation|VO)?\s*\(?(?:EU\)?\s*)?)"
    r"(\d{4}/\d{3,4})",
    re.IGNORECASE,
)


AI_ACT_CELEX = "32024R1689"
# EUR-Lex-Adresse: „…/TXT/?uri=CELEX%3A32021R0691" oder „CELEX:32021R0691",
# innerhalb desselben Links oder Klammerausdrucks nach dem Namen.
_AI_ACT_CELEX_RE = re.compile(
    r"((?:EU[\s-]*AI[\s-]*Act|AI[\s-]*Act|KI-Verordnung|AI Regulation)"
    r"[^<>\n]{0,160}?CELEX(?:%3A|:))(3\d{4}R\d{4})",
    re.IGNORECASE,
)


def ai_act_verordnungsnummer_korrigieren(html: str) -> tuple:
    """Ersetzt eine falsche Verordnungsnummer neben „AI Act" durch
    (EU) 2024/1689. Liefert (html, Anzahl Ersetzungen)."""
    if not html or not re.search(r"\d{4}/\d{3,4}|CELEX", html, re.IGNORECASE):
        return html, 0
    count = 0

    def _fix(m: "re.Match[str]") -> str:
        nonlocal count
        if m.group(2) == "2024/1689":
            return str(m.group(0))
        count += 1
        prefix = str(m.group(1))
        # „(Verordnung 2021/0691)" → „(Verordnung (EU) 2024/1689)"; steht
        # „(EU)" schon davor, nur die Nummer tauschen.
        if re.search(r"\(?EU\)?\s*$", prefix):
            return prefix + "2024/1689"
        return prefix + AI_ACT_VERORDNUNG

    html = _AI_ACT_NUMMER_RE.sub(_fix, html)

    # KIS-1314: Lauf KIS1284 (Strategie S. 31) verlinkte den AI Act auf
    # EUR-Lex mit CELEX 32021R0691 — die KI-Verordnung ist 32024R1689.
    def _fix_celex(m: "re.Match[str]") -> str:
        nonlocal count
        if m.group(2).upper() == AI_ACT_CELEX:
            return str(m.group(0))
        count += 1
        return str(m.group(1)) + AI_ACT_CELEX

    html = _AI_ACT_CELEX_RE.sub(_fix_celex, html)
    if count:
        log.info("[KIS-1305][AI-ACT-NUMMER] %d falsche Verordnungsnummer(n) ersetzt", count)
    return html, count


# ── KIS-1306: Abgelaufene Fristen im Förderkapitel ────────────────────

_MONATE_DE = ("januar", "februar", "märz", "april", "mai", "juni", "juli",
              "august", "september", "oktober", "november", "dezember")
_MONATE_EN = ("january", "february", "march", "april", "may", "june", "july",
              "august", "september", "october", "november", "december")
_FRIST_DATUM_RE = re.compile(r"\b(\d{2})\.(\d{2})\.(\d{4})\b")
_FRIST_MONAT_RE = re.compile(
    r"(Einreichfrist|Antragsfrist|Frist|Deadline|submission deadline)\s+"
    r"(?:im|bis|zum|am|in|by|until)\s+(" + "|".join(_MONATE_DE + _MONATE_EN) + r")\s+(\d{4})\b",
    re.IGNORECASE,
)


def abgelaufene_fristen_korrigieren(html: str, report_date: Optional[date] = None,
                                     lang: str = "de") -> tuple:
    """Ersetzt Datumsangaben im Förderkapitel, die vor dem Reportdatum liegen,
    durch „Aktuell prüfen". Lauf KIS1278 (05.09.2026): Die S7-Tabelle nannte
    „14.07.2026 (Einreichfrist Filmförderung 2026)" und der Praxis-Tipp die
    „Einreichfrist im Juli 2026" — beide aus der Recherche, beide vorbei.
    Liefert (html, Anzahl Ersetzungen)."""
    if not html:
        return html, 0
    heute = report_date or date.today()
    ersatz = "check current call" if lang == "en" else "Aktuell prüfen"
    count = 0

    def _datum(m: "re.Match[str]") -> str:
        nonlocal count
        try:
            d = date(int(m.group(3)), int(m.group(2)), int(m.group(1)))
        except ValueError:
            return str(m.group(0))
        if d >= heute:
            return str(m.group(0))
        count += 1
        return ersatz

    html = _FRIST_DATUM_RE.sub(_datum, html)
    # „14.07.2026 (Einreichfrist …)" → „Aktuell prüfen (Einreichfrist …)":
    # der Klammerzusatz erklärt nichts mehr, weg damit.
    html = re.sub(re.escape(ersatz) + r"\s*\((?:Einreich|Antrags)?frist[^)]{0,60}\)", ersatz, html, flags=re.IGNORECASE)

    def _monat(m: "re.Match[str]") -> str:
        nonlocal count
        name = m.group(2).lower()
        idx = (_MONATE_DE.index(name) if name in _MONATE_DE else _MONATE_EN.index(name)) + 1
        jahr = int(m.group(3))
        if (jahr, idx) >= (heute.year, heute.month):
            return str(m.group(0))
        count += 1
        return ("next call (check with the funder)" if lang == "en"
                else "nächsten Einreichtermin (beim Fördergeber prüfen)")

    html = _FRIST_MONAT_RE.sub(_monat, html)
    if count:
        log.info("[KIS-1306][FRIST] %d abgelaufene Frist(en) im Förderkapitel ersetzt", count)
    return html, count


# ── KIS-1311: Genus von „Score" ───────────────────────────────────────

# „die Governance-Score zeigt", „Die Compliance-Score" (Strategie S. 10/11,
# Lauf KIS1280). Score ist maskulin; nur Artikel direkt vor dem Wort.
_SCORE_GENUS_RE = re.compile(r"\b([Dd])ie(\s+(?:[A-Za-zÄÖÜäöüß]+-)?Score)(?![\wäöüß-])")


def score_genus_korrigieren(html: str) -> tuple:
    """„die X-Score" → „der X-Score". Liefert (html, Anzahl)."""
    if not html or "Score" not in html:
        return html, 0
    neu, n = _SCORE_GENUS_RE.subn(r"\1er\2", html)
    if n:
        log.info('[KIS-1311][SCORE-GENUS] %d Artikel vor "Score" korrigiert', n)
    return neu, n


# ── KIS-1313: Benchmark-Prozente ohne Beleg in der Recherche ──────────

# Lauf KIS1282, S2: „ca. 35–45 % der Medienbetriebe nutzen KI-Tools in
# Redaktion und Lektorat — RTR 2025, Bertelsmann 2025" und „60–65 % der
# Verlage setzen KI-Übersetzungstools ein — RTR 2025". Die Recherche
# enthielt keine dieser Zahlen; die Quellen waren Film-Artikel. Regel
# (KIS-1294): Eine Zahl ohne Messung heißt „Richtwert". Der Prompt sagt das,
# das Modell hält sich nicht daran — hier das Netz: Jeder Prozentwert in S2,
# dessen Zahl nicht in der Recherche steht, bekommt den Zusatz.
_S2_PROZENT_RE = re.compile(r"(?<![\d,.])(\d{1,3})(?:\s?[–-]\s?(\d{1,3}))?\s?%")
_RICHTWERT_NAH_RE = re.compile(r"Richtwert|guide value|Sch[äa]tz", re.IGNORECASE)


def research_text_aus_kontext(research_context: Optional[dict]) -> str:
    """Alle Recherche-Ergebnisse als ein Text (Schlüssel → {"results": str})."""
    if not isinstance(research_context, dict):
        return ""
    teile = []
    for v in research_context.values():
        if isinstance(v, dict):
            teile.append(str(v.get("results") or v.get("text") or ""))
        elif isinstance(v, str):
            teile.append(v)
    return " ".join(t for t in teile if t)


_BRUCH_WORTE = {
    "75": r"drei von vier|3 von 4|three (?:in|out of) four|drei Viertel|three[- ]quarters",
    "80": r"vier von fünf|4 von 5|four (?:in|out of) five",
    "90": r"neun von zehn|9 von 10|nine (?:in|out of) ten",
    "67": r"zwei Drittel|two[- ]thirds",
    "66": r"zwei Drittel|two[- ]thirds",
    "60": r"drei von fünf|3 von 5|three (?:in|out of) five",
    "50": r"jede[rs]? zweite|die Hälfte|1 von 2|one in two|half of",
    "40": r"zwei von fünf|2 von 5|two (?:in|out of) five",
    "33": r"jede[rs]? dritte|ein Drittel|1 von 3|one in three|a third",
    "25": r"jede[rs]? vierte|ein Viertel|1 von 4|one in four|a quarter",
    "20": r"jede[rs]? fünfte|ein Fünftel|1 von 5|one in five",
    "10": r"jede[rs]? zehnte|ein Zehntel|1 von 10|one in ten",
}

# KIS-1315: „EU-konforme Werkzeuge wie DeepL Pro oder Adobe Firefly" (Lauf
# KIS1285, S3). Die Prompt-Regel hielt in vier Läufen nicht; jetzt fällt ein
# US-Werkzeug deterministisch aus der Aufzählung hinter „EU-konform… wie".
_US_WERKZEUGE_RE = re.compile(
    r"\b(?:ChatGPT(?:\s*/\s*OpenAI)?|OpenAI(?:\s+API)?|Claude|Anthropic|Perplexity(?:\s+AI)?|Runway(?:ML)?|"
    r"Gemini|Midjourney|Adobe Firefly|Firefly|Descript|ElevenLabs|Canva(?:\s+Magic\s+Studio)?|"
    r"Microsoft 365 Copilot|Copilot|Notion(?:\s+AI)?|Frame\.io|"
    r"Adobe Premiere Pro(?:\s*\(Speech to Text\))?|Adobe After Effects)\b"
)
_EU_AUFZAEHLUNG_RE = re.compile(
    r"(EU-(?:konform|gehostet|basiert)\w*\s+(?:KI-)?(?:Werkzeuge?n?|Tools?|Alternativen?|Lösungen|Anbieter|Dienste?)"
    r"\s+(?:wie|etwa|z\.\s?B\.|beispielsweise|such as|like)\s+"
    # KIS-1316: „… mit EU-konformem Vendor-Audit-Status. Die Umstellung auf
    # Werkzeuge wie Adobe Firefly oder DeepL Pro" (Lauf KIS1286, S3) — die
    # Aufzählung folgt dem EU-Bezug im nächsten Satz.
    r"|EU-konform\w*[^<]{0,160}?(?:Umstellung|Wechsel|Migration)\s+(?:auf|zu)\s+(?:EU-konforme?n?\s+|datenschutzkonforme?n?\s+)?"
    r"(?:Werkzeuge?n?|Tools?|Alternativen?)\s+(?:wie|etwa|z\.\s?B\.)\s+)"
    r"([^.;:<\n]+?)(?=[.;:<\n]| ist\b| sind\b| kann\b| bietet| bieten| ermöglich| statt\b| anstelle\b"
    r"| für\b| zur\b| zum\b| bei\b| in\b| um\b| als\b)",
    re.IGNORECASE,
)

# KIS-1316: „Die von Ihnen empfohlenen Tools" (Lauf KIS1286, S8) — der Kunde
# empfiehlt nichts, der Bericht tut es.
_VON_IHNEN_EMPFOHLEN_RE = re.compile(r"\b(?:die|der|das|den|dem)?\s*von Ihnen empfohlene(n|s|r)?\b", re.IGNORECASE)
# KIS-1316: Ein Listenpunkt, der nur aus einem Werkzeugnamen besteht
# („<li>Runway</li>", Lauf KIS1286, S4 S. 19) — Rest einer gekappten Zeile.
_NACKTER_LI_RE = re.compile(r"<li\b[^>]*>\s*(?:<(?:strong|b|em)>)?\s*([^<>]{1,40}?)\s*(?:</(?:strong|b|em)>)?\s*</li>", re.IGNORECASE)


def nackte_werkzeug_punkte_entfernen(html: str) -> tuple:
    """Entfernt <li>, deren Text nur ein Werkzeugname ohne Satz ist."""
    if not html or "<li" not in html:
        return html, 0
    count = 0

    def _fix(m: "re.Match[str]") -> str:
        nonlocal count
        text = m.group(1).strip()
        if len(text.split()) <= 2 and not re.search(r"[:.!?\d]", text) and _US_WERKZEUGE_RE.fullmatch(text):
            count += 1
            return ""
        return str(m.group(0))

    return _NACKTER_LI_RE.sub(_fix, html), count


def von_ihnen_empfohlen_korrigieren(html: str) -> tuple:
    if not html or "von Ihnen empfohlen" not in html:
        return html, 0

    def _fix(m: "re.Match[str]") -> str:
        art = m.group(0).strip().split(" ")[0]
        art = art + " " if art.lower() in ("die", "der", "das", "den", "dem") else ""
        return f"{art}empfohlene{m.group(1) or ''}"

    return _VON_IHNEN_EMPFOHLEN_RE.subn(_fix, html)



def us_werkzeug_aus_eu_aufzaehlung(html: str) -> tuple:
    """Streicht US-Werkzeuge aus einer Aufzählung nach „EU-konforme Werkzeuge
    wie …". Bleibt nichts übrig, fällt das „wie …" ganz. Liefert (html, n)."""
    if not html or "EU-" not in html:
        return html, 0
    count = 0

    def _fix(m: "re.Match[str]") -> str:
        nonlocal count
        kopf, liste = m.group(1), m.group(2)
        if not _US_WERKZEUGE_RE.search(liste):
            return str(m.group(0))
        teile = [t.strip() for t in re.split(r",|\s+oder\s+|\s+und\s+|\s+or\s+|\s+and\s+", liste) if t.strip()]
        rest = [t for t in teile if not _US_WERKZEUGE_RE.search(t)]
        if len(rest) == len(teile):
            return str(m.group(0))
        count += 1
        if not rest:
            # „EU-konforme Werkzeuge wie X" → „EU-konforme Werkzeuge"
            return re.sub(r"\s+(?:wie|etwa|z\.\s?B\.|beispielsweise|such as|like)\s+$", "", kopf)
        konj = " oder " if re.search(r"\s+oder\s+|\s+or\s+", liste) else " und "
        if re.search(r"\s+or\s+|\s+and\s+|such as|like", m.group(0)) and not re.search(r"wie|etwa|z\.\s?B\.", kopf):
            konj = " or " if " or " in liste else " and "
        neu = rest[0] if len(rest) == 1 else ", ".join(rest[:-1]) + konj + rest[-1]
        return kopf + neu

    html = _EU_AUFZAEHLUNG_RE.sub(_fix, html)
    if count:
        log.info("[KIS-1315][US-AUS-EU] %d US-Werkzeug(e) aus EU-Aufzählung gestrichen", count)
    return html, count


# KIS-1315: „Die erwartete jährliche Zeitersparnis von 50 Stunden pro Monat"
# (Lauf KIS1285, S5) — jährlich und pro Monat im selben Satz.
_JAEHRLICH_PRO_MONAT_RE = re.compile(
    r"\bjährliche[nrs]?\s+(Zeitersparnis|Einsparung|Ersparnis|Zeitgewinn)\s+von\s+(\d[\d.]*)\s+Stunden\s+pro\s+Monat"
    r"|\bannual\s+(time\s+saving|saving)s?\s+of\s+(\d[\d.]*)\s+hours\s+per\s+month",
    re.IGNORECASE,
)


def jaehrlich_pro_monat_korrigieren(html: str) -> tuple:
    if not html or "pro Monat" not in html and "per month" not in html:
        return html, 0
    count = 0

    def _fix(m: "re.Match[str]") -> str:
        nonlocal count
        count += 1
        if m.group(1):
            return f"{m.group(1)} von {m.group(2)} Stunden pro Monat"
        return f"{m.group(3)} of {m.group(4)} hours per month"

    return _JAEHRLICH_PRO_MONAT_RE.sub(_fix, html), count


# KIS-1315: „Quelle: … des KI-Strategieberichts für Ihr Unternehmen, Stand
# 2024." (Lauf KIS1285, S6, Report vom 06.09.2026). Ein Stand vor dem
# Reportjahr in einer Quellenzeile ist erfunden — es gibt kein datiertes
# Dokument dieses Namens.
_QUELLEN_STAND_RE = re.compile(
    r"(<p[^>]*>(?:(?!</p>).)*?\b(?:Quellen?|Sources?)\s*:(?:(?!</p>).)*?)(,?\s*\(?(?:Stand|as of|status)\s+(20\d{2})\)?)",
    re.IGNORECASE | re.DOTALL,
)


def quellen_stand_jahr_korrigieren(html: str, report_year: int) -> tuple:
    if not html or not report_year or not re.search(r"\b(?:Stand|as of)\s+20\d{2}", html, re.IGNORECASE):
        return html, 0
    count = 0

    def _fix(m: "re.Match[str]") -> str:
        nonlocal count
        if int(m.group(3)) >= report_year:
            return str(m.group(0))
        count += 1
        return str(m.group(1))

    return _QUELLEN_STAND_RE.sub(_fix, html), count


# KIS-1317: „Jahreslizenz zwischen 30.000 € und 40.000 €" und „25.000 €
# monatlich bei 1–2 Jahreslizenzen" (Lauf KIS1287, S3b) — nach KIS-1312 und
# KIS-1315 der dritte Lauf mit falscher Division. Die Rechnung wird Code:
# Monatsumsatz = Abonnenten (Obergrenze) × Jahrespreis (Untergrenze) / 12.
_JAHRESPREIS_RE = re.compile(
    r"Jahres(?:abo(?:nnement)?|lizenz)\w*\s+(?:ab|von|zu|für|zwischen)\s+([\d.]{4,})\s*€"
    r"|([\d.]{4,})\s*€(?:\s*[–-]\s*[\d.]{4,}\s*€)?\s+Jahres(?:abo(?:nnement)?|lizenz)",
    re.IGNORECASE,
)
_MONATSUMSATZ_RE = re.compile(
    r"([\d.]{4,})(\s*€\s+(?:(?:monatlich|im Monat|pro Monat)\s+)?bei\s+(\d+)(?:\s?[–-]\s?(\d+))?\s+Jahres(?:abonnent|lizenz|kund))",
    re.IGNORECASE,
)


def umsatz_jahresabo_korrigieren(html: str) -> tuple:
    """Rechnet einen Monatsumsatz nach, der zu Jahresabonnenten × Jahrespreis
    nicht passt, und ersetzt ihn. Liefert (html, Anzahl)."""
    if not html or "Jahres" not in html:
        return html, 0
    text = re.sub(r"<[^>]+>", " ", html)
    preis_m = _JAHRESPREIS_RE.search(text)
    if not preis_m:
        return html, 0
    preis = int((preis_m.group(1) or preis_m.group(2)).replace(".", ""))
    if preis < 1000:
        return html, 0
    count = 0

    def _fix(m: "re.Match[str]") -> str:
        nonlocal count
        monat = int(m.group(1).replace(".", ""))
        n_max = int(m.group(4) or m.group(3))
        soll = n_max * preis / 12
        if monat <= soll * 1.5:
            return str(m.group(0))
        korr = int(round(soll / 100.0) * 100)
        count += 1
        return f"{korr:,}".replace(",", ".") + m.group(2)

    html = _MONATSUMSATZ_RE.sub(_fix, html)
    if count:
        log.info("[KIS-1317][JAHRESABO] %d Monatsumsatz/-umsätze nachgerechnet (Jahrespreis %d €)", count, preis)
    return html, count


def benchmark_prozent_richtwert(html: str, research_text: str, lang: str = "de") -> tuple:
    """Hängt „(Richtwert)" an Prozentwerte, deren Zahl nicht in der Recherche
    vorkommt. Nur Textknoten, keine Tags. Liefert (html, Anzahl)."""
    if not html or "%" not in html:
        return html, 0
    zusatz = " (guide value)" if lang == "en" else " (Richtwert)"
    belegt_cache: dict[str, bool] = {}

    def _belegt(zahl: str) -> bool:
        if zahl in belegt_cache:
            return bool(belegt_cache[zahl])
        ok = bool(research_text) and bool(
            re.search(r"(?<![\d,.])" + re.escape(zahl) + r"(?:[,.]\d+)?\s?(?:%|Prozent|percent)", research_text)
        )
        # KIS-1315: Die Recherche sagt „drei von vier", das Modell schreibt
        # „75 %" — Lauf KIS1285 (S2) bekam dafür „75 % (Richtwert)" neben der
        # Quelle Metricool 2026. Bruchangaben zählen als Beleg.
        if not ok and research_text and zahl in _BRUCH_WORTE:
            ok = bool(re.search(_BRUCH_WORTE[zahl], research_text, re.IGNORECASE))
        belegt_cache[zahl] = ok
        return ok

    count = 0
    teile = re.split(r"(<[^>]+>)", html)
    for i, teil in enumerate(teile):
        if not teil or teil.startswith("<") or "%" not in teil:
            continue

        def _ersatz(m: "re.Match[str]") -> str:
            nonlocal count
            zahlen = [z for z in (m.group(1), m.group(2)) if z]
            if any(_belegt(z) for z in zahlen):
                return str(m.group(0))
            nach = teil[m.end():m.end() + 30]
            vor = teil[max(0, m.start() - 30):m.start()]
            if _RICHTWERT_NAH_RE.search(nach) or _RICHTWERT_NAH_RE.search(vor):
                return str(m.group(0))
            count += 1
            return str(m.group(0)) + zusatz

        teile[i] = _S2_PROZENT_RE.sub(_ersatz, teil)
    if count:
        log.info("[KIS-1313][RICHTWERT] %d Prozentwert(e) ohne Beleg in der Recherche markiert", count)
    return "".join(teile), count


# ── Hauptfunktion ────────────────────────────────────────────────────

_EXEC_FUNDING_NEUTRAL = (
    "Durch Förderprogramme lässt sich ein Teil der Investition abfedern "
    "(Details in Kapitel 7)."
)
# Sätze mit konkreten Förderquoten/-summen oder förderbereinigten
# Kennzahlen in der Executive Summary (KIS-1235).
_EXEC_FUNDING_CLAIM_RES = [
    re.compile(r"[^.!?<>]*Förder(?:potenzial|quote|summe)[^.!?<>]*\d+\s*(?:%|€)[^.!?<>]*[.!?]"),
    re.compile(r"[^.!?<>]*\d+\s*%[^.!?<>]*(?:der\s+Gesamtinvestition|Förderquote)[^.!?<>]*[.!?]"),
    re.compile(r"[^.!?<>]*(?:max\.|maximal)\s*[\d.]+\s*€[^.!?<>]*Förder[^.!?<>]*[.!?]"),
    re.compile(r"[^.!?<>]*Netto-ROI[^.!?<>]*(?:Förder|über\s*\d{3,}\s*%)[^.!?<>]*[.!?]"),
    re.compile(r"[^.!?<>]*Break-Even[^.!?<>]*(?:nach|dank|durch)[^.!?<>]*Förder[^.!?<>]*[.!?]"),
]


def _neutralize_exec_funding_claims(html: str) -> tuple:
    """Ersetzt den ersten konkreten Förder-Claim durch die neutrale
    Formulierung, entfernt weitere. Liefert (html, warnings)."""
    warnings = []
    replaced_once = False
    for rx in _EXEC_FUNDING_CLAIM_RES:
        while True:
            m = rx.search(html)
            if not m:
                break
            claim = m.group(0).strip()
            replacement = "" if replaced_once else " " + _EXEC_FUNDING_NEUTRAL
            html = html[:m.start()] + replacement + html[m.end():]
            replaced_once = True
            warnings.append(f"EXEC-Förder-Claim neutralisiert: {claim[:90]}")
    return html, warnings


def sanitize_strategy_sections(
    sections: dict,
    research_context: dict = None,
    report_year: int = 2026,
    report_date: Optional[date] = None,
) -> dict:
    """
    Haupteinstieg: Scannt alle Strategy-Sektionen auf Fakten-Plausibilität.

    Args:
        sections: Dict mit S1–S8 + EXEC HTML-Sektionen
        research_context: Optional, Recherche-Ergebnisse für Source-Abgleich (v2)
        report_year: Aktuelles Berichtsjahr

    Returns:
        Gepatchtes sections-Dict + '_strategy_sanitizer_report' Key mit Zusammenfassung
    """
    all_warnings = []
    patches_applied = 0
    _research_text = research_text_aus_kontext(research_context)

    strategy_keys = [k for k in sections if isinstance(sections[k], str) and len(sections[k]) > 100]

    # KIS-1234: Ampel-Emojis rendern im PDF-Service als leere Kästchen
    # (Emoji-Font fehlt in Puppeteer). Der Prompt fordert jetzt CSS-Spans;
    # dieses Netz fängt Läufe ab, in denen das LLM trotzdem Emojis liefert.
    _AMPEL_EMOJI_MAP = [
        ("\U0001F7E2", '<span class="ampel-green">\u25cf</span>'),
        ("\U0001F7E1", '<span class="ampel-yellow">\u25cf</span>'),
        ("\U0001F534", '<span class="ampel-red">\u25cf</span>'),
    ]

    for key in strategy_keys:
        html = sections[key]

        # Pass 0a (KIS-1283): Beraterstimme in den Singular. Der
        # Status-Report macht das seit jeher (Ersetzung in
        # gpt_analyze.py), der Strategiebericht bisher nicht — im Lauf
        # KIS-1267 standen darin zehn Stellen in der ersten Person
        # Plural neben sechs im Singular. Derselbe Kunde las in einem
        # Dokument "ich" und im anderen "wir".
        html, _bs = beraterstimme_in_singular(html)
        if _bs:
            sections[key] = html
            patches_applied += _bs

        # Pass 0 (KIS-1234): Ampel-Emojis -> CSS-Spans
        for _emoji, _span in _AMPEL_EMOJI_MAP:
            if _emoji in html:
                html = html.replace(_emoji, _span)
                sections[key] = html
                patches_applied += 1

        # Pass 0b (KIS-1235): Konkrete Fördersummen/-quoten in der Executive
        # Summary neutralisieren. Die Prompt-Regel ("Nenne NIE eine konkrete
        # Fördersumme in der ES") wurde im Lauf 1235 verletzt ("bis zu 70 %
        # der Gesamtinvestition (max. 8.400 €) … Netto-ROI von über 200 %");
        # die gelisteten Programme trugen das rechnerisch nicht.
        if key.lower() in ("exec", "exec_summary", "executive_summary"):
            html, _fw = _neutralize_exec_funding_claims(html)
            if _fw:
                sections[key] = html
                patches_applied += len(_fw)
                all_warnings.extend(_fw)

        # Pass 1: Prozent-Plausibilität
        html, pw = _check_percent_plausibility(html, key)
        if pw:
            sections[key] = html
            patches_applied += len(pw)
            all_warnings.extend(pw)

        # Pass 2: Benchmark table >100% validator (FIX-KIS-1082)
        tw, html = _check_table_consistency(html, key)
        if tw:
            sections[key] = html
            patches_applied += len(tw)
            all_warnings.extend(tw)

        # Pass 3: Jahres-Check
        yw = _check_year_data_freshness(html, key, report_year)
        all_warnings.extend(yw)

        # Pass 4: Plain-Language Safety Net (S31-FIX-B)
        html, plw = _apply_plain_language(html, key)
        if plw:
            sections[key] = html
            patches_applied += len(plw)
            all_warnings.extend(plw)

        # Pass 5: FIX-KIS-1027.4-3C — Doppel-Annahme in Szenario-Boxen entfernen.
        # LLM emittiert trotz Prompt-Anweisung manchmal "Einordnung der Annahmen:
        # Annahme: …" oder "Annahme: Annahme: …". Belt+Suspenders zum Prompt-Fix.
        import re as _re
        annahme_patches = 0
        before = html
        # Doppelpräfix "Annahme: Annahme:" -> "Annahme:"
        html = _re.sub(r'(?i)\bAnnahme:\s*Annahme:\s*', 'Annahme: ', html)
        # "Einordnung der Annahmen: Annahme:" -> "Annahme:"
        html = _re.sub(
            r'(?i)<strong>\s*Einordnung\s+der\s+Annahmen:\s*</strong>\s*<strong>\s*Annahme:\s*</strong>\s*',
            '<strong>Annahme:</strong> ', html,
        )
        html = _re.sub(
            r'(?i)Einordnung\s+der\s+Annahmen:\s*Annahme:\s*', 'Annahme: ', html,
        )
        if html != before:
            sections[key] = html
            annahme_patches = 1
            patches_applied += 1
            all_warnings.append(f"{key}: Szenario-Box Doppel-Annahme bereinigt (1027.4-3C)")

        # Pass 6 (KIS-1305): Verordnungsnummer des AI Act. Lauf KIS1277, S8
        # Quellenzeile: „EU AI Act (Verordnung 2021/0691)" — die Nummer ist
        # erfunden. Die KI-Verordnung ist (EU) 2024/1689; jede andere Nummer
        # neben „AI Act"/„KI-Verordnung" wird ersetzt.
        html, _vn = ai_act_verordnungsnummer_korrigieren(html)
        if _vn:
            sections[key] = html
            patches_applied += _vn
            all_warnings.append(f"{key}: {_vn} falsche AI-Act-Verordnungsnummer(n) ersetzt (KIS-1305)")

        # Pass 6b (KIS-1311): „die Governance-Score" → „der Governance-Score".
        html, _sg = score_genus_korrigieren(html)
        if _sg:
            sections[key] = html
            patches_applied += _sg

        # Pass 6d (KIS-1315): US-Werkzeug aus „EU-konforme Werkzeuge wie …".
        html, _ue = us_werkzeug_aus_eu_aufzaehlung(html)
        if _ue:
            sections[key] = html
            patches_applied += _ue
            all_warnings.append(f"{key}: {_ue} US-Werkzeug(e) aus EU-Aufzählung gestrichen (KIS-1315)")

        # Pass 6e (KIS-1315): „jährliche Zeitersparnis von 50 Stunden pro Monat".
        html, _jm = jaehrlich_pro_monat_korrigieren(html)
        if _jm:
            sections[key] = html
            patches_applied += _jm

        # Pass 6f (KIS-1315): „Quelle: …, Stand 2024" vor dem Reportjahr.
        html, _qs = quellen_stand_jahr_korrigieren(html, int(report_year or 0))
        if _qs:
            sections[key] = html
            patches_applied += _qs
            all_warnings.append(f"{key}: {_qs} veralteter Quellen-Stand entfernt (KIS-1315)")

        # Pass 6g (KIS-1316): „Die von Ihnen empfohlenen Tools" → „Die empfohlenen Tools".
        html, _ve = von_ihnen_empfohlen_korrigieren(html)
        if _ve:
            sections[key] = html
            patches_applied += _ve

        # Pass 6h (KIS-1316): „<li>Runway</li>" — Listenpunkt ohne Satz.
        html, _nl = nackte_werkzeug_punkte_entfernen(html)
        if _nl:
            sections[key] = html
            patches_applied += _nl
            all_warnings.append(f"{key}: {_nl} nackte(r) Werkzeug-Listenpunkt(e) entfernt (KIS-1316)")

        # Pass 6i (KIS-1317): Monatsumsatz bei Jahresabonnenten nachrechnen (S3b).
        if key.lower().startswith("s3b"):
            html, _ja = umsatz_jahresabo_korrigieren(html)
            if _ja:
                sections[key] = html
                patches_applied += _ja
                all_warnings.append(f"{key}: {_ja} Monatsumsatz bei Jahresabo nachgerechnet (KIS-1317)")

        # Pass 6c (KIS-1313): Benchmark-Prozente in S2 ohne Beleg in der
        # Recherche heißen „Richtwert".
        # Nur wenn der Aufrufer die Recherche mitgibt — ohne sie bleibt das
        # Verhalten älterer Aufrufer und Tests unverändert.
        if key.lower().startswith("s2") and research_context is not None:
            _lang2 ="en" if re.search(r"\bcompetitor|\bbenchmark figures|\bmarket\b", html, re.IGNORECASE) and not re.search(r"Wettbewerb", html) else "de"
            html, _rw = benchmark_prozent_richtwert(html, _research_text, _lang2)
            if _rw:
                sections[key] = html
                patches_applied += _rw
                all_warnings.append(f"{key}: {_rw} Prozentwert(e) ohne Recherche-Beleg als Richtwert markiert (KIS-1313)")

        # Pass 7 (KIS-1306): Abgelaufene Fristen im Förderkapitel (S7).
        if key.lower().startswith("s7"):
            _lang = "en" if re.search(r"\bfunding\b|\bdeadline\b", html, re.IGNORECASE) and not re.search(r"Förder", html) else "de"
            html, _fr = abgelaufene_fristen_korrigieren(html, report_date, _lang)
            if _fr:
                sections[key] = html
                patches_applied += _fr
                all_warnings.append(f"{key}: {_fr} abgelaufene Frist(en) ersetzt (KIS-1306)")

    report = {
        'warnings': all_warnings,
        'patches_applied': patches_applied,
        'sections_scanned': len(strategy_keys),
    }
    sections['_strategy_sanitizer_report'] = report

    log.info(
        "[FIX-SF1] Strategy Sanitizer complete: "
        "scanned=%d, patches=%d, warnings=%d",
        len(strategy_keys), patches_applied, len(all_warnings)
    )

    return sections
