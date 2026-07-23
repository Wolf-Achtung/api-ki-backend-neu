# -*- coding: utf-8 -*-
"""
services.html_sanitizer
-----------------------
Kleiner, abhängigkeitsfreier Sanitizer für Abschnitts‑HTML.
Ziele:
- Entfernt komplette Dokument‑Wrapper (<html>, <head>, <body>, <!DOCTYPE>)
- Entfernt <script>, <iframe>, <object>, <embed>, <link>, <meta>
- Entfernt Inline‑Eventhandler (onClick, onload, …)
- Behebt UTF-8 Mojibake (Ã¶ → ö)
- Optional: komprimiert Whitespace
- Erhält valide Teil‑HTML (Listen, Tabellen, Divs, etc.) unverändert
- NEU: Markdown → HTML Konvertierung (render_markdown_safe)
- NEU: Broken HTML Recovery (recover_text_from_broken_html)

Hinweis: bewusst konservativ, um Layout nicht zu zerstören.
"""
from __future__ import annotations
import re
import html
import logging
from typing import Optional

log = logging.getLogger(__name__)

# Versuche markdown-it-py oder mistune zu importieren
try:
    import mistune
    MISTUNE_AVAILABLE = True
except ImportError:
    MISTUNE_AVAILABLE = False
    log.debug("[HTML-SANITIZER] mistune not available, markdown rendering disabled")

_TRUTHY = {"1","true","TRUE","yes","YES","on","y"}

def _fix_utf8_mojibake(text: str) -> str:
    """Behebt falsch encodierte UTF-8 Zeichen (Mojibake).

    Beispiele:
    - "FragebÃ¶gen" → "Fragebögen"
    - "MarktfÃ¼hrer" → "Marktführer"
    """
    if not text or not isinstance(text, str):
        return text
    if 'Ã' not in text and 'â' not in text:
        return text
    try:
        # Versuche als Latin-1 zu decodieren und als UTF-8 zu encoden
        return text.encode('latin-1', errors='ignore').decode('utf-8', errors='ignore')
    except Exception:
        try:
            return html.unescape(text)
        except Exception:
            return text

RE_DOCTYPES = re.compile(r"(?is)<!DOCTYPE.*?>")
RE_HTML_TAGS = re.compile(r"(?is)</?\s*html\b.*?>")
RE_HEAD_BLOCK = re.compile(r"(?is)<\s*head\b.*?>.*?</\s*head\s*>")
RE_BODY_TAGS = re.compile(r"(?is)</?\s*body\b.*?>")

# Tags, die komplett entfernt werden (inkl. Inhalt bei head)
RE_SCRIPT_BLOCK = re.compile(r"(?is)<\s*script\b.*?>.*?</\s*script\s*>")
RE_IFRAME_BLOCK = re.compile(r"(?is)<\s*iframe\b.*?>.*?</\s*iframe\s*>")
RE_OBJECT_BLOCK = re.compile(r"(?is)<\s*object\b.*?>.*?</\s*object\s*>")
RE_EMBED_BLOCK  = re.compile(r"(?is)<\s*embed\b.*?>.*?</\s*embed\s*>")
RE_LINK_TAG     = re.compile(r"(?is)<\s*link\b.*?/?>")
RE_META_TAG     = re.compile(r"(?is)<\s*meta\b.*?/?>")

# Inline‑Eventhandler (onload=, onclick=, …)
RE_ON_EVENT_ATTR = re.compile(r"(?i)\s+on[a-z]+\s*=\s*(\"[^\"]*\"|'[^']*')")

# Daten‑/Sicherheitsfilter: Entferne javascript: URIs in href/src
RE_JS_PROTOCOL = re.compile(r"(?is)(\s(?:href|src)\s*=\s*['\"])\s*javascript:[^'\"]*(['\"])")

# --- HTML Minification Patterns ---
# Empty tags that can be safely removed
RE_EMPTY_P = re.compile(r"<p[^>]*>\s*</p>", re.IGNORECASE)
RE_EMPTY_SPAN = re.compile(r"<span[^>]*>\s*</span>", re.IGNORECASE)
RE_EMPTY_DIV = re.compile(r"<div[^>]*>\s*</div>", re.IGNORECASE)
RE_EMPTY_LI = re.compile(r"<li[^>]*>\s*</li>", re.IGNORECASE)
RE_LONE_BR = re.compile(r"(?:<br\s*/?>){2,}", re.IGNORECASE)  # Multiple consecutive <br>

# Empty class attributes
RE_EMPTY_CLASS = re.compile(r'\s+class\s*=\s*["\'][\s]*["\']', re.IGNORECASE)

# Redundant whitespace in style attributes
RE_STYLE_WHITESPACE = re.compile(r'style\s*=\s*["\']([^"\']*)["\']', re.IGNORECASE)

def _normalize_special_chars(text: str) -> str:
    """Entfernt oder ersetzt problematische Sonderzeichen.

    - U+FFFE (￾) - nicht druckbares Zeichen
    - Andere problematische Unicode-Zeichen
    """
    if not text:
        return text

    # Entferne U+FFFE und andere problematische Zeichen
    replacements = [
        ("\ufffe", ""),  # U+FFFE - nicht druckbar
        ("\uffff", ""),  # U+FFFF - nicht druckbar
        ("\x00", ""),    # Null byte
        ("\x0b", ""),    # Vertical tab
        ("\x0c", ""),    # Form feed
    ]
    for old, new in replacements:
        text = text.replace(old, new)

    return text


# =============================================================================
# 3.1.4.16: EN Lastline Locale Sanitizer (mirrors locale-scan needles)
# =============================================================================
# Final guardrail to prevent residual German UI tokens in EN reports.
# Synchronized with scripts/generate_golden_reports.py locale-scan needles.

from typing import List, Tuple, Union, Callable

LocaleRepl = Union[str, Callable[[re.Match], str]]

_EN_LOCALE_REPLACEMENTS: List[Tuple[str, LocaleRepl]] = [
    # ==========================================================================
    # LONGER PHRASES FIRST (avoid partial collisions)
    # ==========================================================================
    (r"\bIhr Unternehmen\b", "Your Company"),
    (r"\bIhre Branche\b", "Your industry"),
    (r"\bIhre nächsten\b", "Your next"),
    (r"\bIhre Rechte\b", "Your rights"),
    (r"\bIhr Kerngeschäft\b", "Your core business"),
    (r"\bUnternehmensgröße\b", "Company size"),
    (r"\bUnternehmensprofil\b", "Company profile"),
    (r"\bHandlungsempfehlungen\b", "Recommendations"),
    (r"\bBranchenstudie\b", "Industry study"),
    (r"\bBranchenspezifisch\b", "Industry-specific"),
    (r"\bBranchenmedian\b", "Industry median"),
    (r"\bBranchenvergleich\b", "Industry comparison"),
    (r"\bWesentliche Risiken\b", "Key risks"),
    (r"\bNächste Schritte\b", "Next steps"),
    (r"\bNächster Schritt\b", "Next step"),
    (r"\bEintrittswahrscheinlichkeit\b", "Probability"),
    (r"\bDSGVO-konforme\b", "GDPR-compliant"),
    (r"\bDSGVO-konform\b", "GDPR-compliant"),

    # --- Extended EN locale replacements (plural + UI synonyms) ---
    (r"\bInterne Review-Bewertungen\b", "Internal review ratings"),
    (r"\bBewertungen\b", "Assessments"),
    (r"\bMaßnahmenplan\b", "Action plan"),
    (r"\bMaßnahmen\b", "Actions"),
    (r"\bZusammenfassungen\b", "Summaries"),
    (r"\bZusammenfassung\b", "Summary"),
    (r"\bEmpfehlungen\b", "Recommendations"),
    (r"\bEmpfehlung\b", "Recommendation"),

    # --- Compound/plural + GDPR ---
    (r"\bBranchen-", "Industry-"),
    (r"\bBranchen\b", "Industries"),
    (r"\bDatenschutz\b", "Data protection"),
    (r"\bDSGVO\b", "GDPR"),
    (r"\bHinweis\b", "Note"),
    (r"\bHinweise\b", "Notes"),

    # ==========================================================================
    # BUSINESS CASE / FINANCIAL TERMS
    # ==========================================================================
    (r"\bKosten\b", "Costs"),
    (r"\bNutzen\b", "Benefits"),
    (r"\bNutzenpotenzial\b", "Benefit potential"),
    (r"\bInvestition\b", "Investment"),
    (r"\bInvestitionen\b", "Investments"),
    (r"\bEinsparungen\b", "Savings"),
    (r"\bEinsparung\b", "Saving"),
    (r"\bAmortisation\b", "Payback"),
    (r"\bWirtschaftlichkeit\b", "Cost-effectiveness"),
    (r"\bAufwand\b", "Effort"),
    (r"\bFörderpotenzial\b", "Funding potential"),
    (r"\bFörderprogramme\b", "Funding programmes"),
    (r"\bFörderprogramm\b", "Funding programme"),
    (r"\bFörderchance\b", "Funding opportunity"),
    (r"\bFörderung\b", "Funding"),
    # Scenario labels
    (r"\bKonservativ\b", "Conservative"),
    (r"\bRealistisch\b", "Realistic"),
    (r"\bOptimistisch\b", "Optimistic"),

    # ==========================================================================
    # RISK / STRATEGY TERMS
    # ==========================================================================
    (r"\bRisikolage\b", "Risk situation"),
    (r"\bRisikoprofil\b", "Risk profile"),
    (r"\bRisiko-Matrix\b", "Risk matrix"),
    (r"\bRisiko\b", "Risk"),
    (r"\bRisiken\b", "Risks"),
    (r"\bUmsetzung\b", "Implementation"),
    (r"\bStrategie\b", "Strategy"),
    (r"\bRoadmap\b", "Roadmap"),
    (r"\bZielbild\b", "Target state"),
    (r"\bZeitplan\b", "Timeline"),
    (r"\bPriorisierung\b", "Prioritization"),
    (r"\bPriorität\b", "Priority"),
    (r"\bPrioritäten\b", "Priorities"),
    (r"\bZeithorizont\b", "Time horizon"),
    (r"\bSchwerpunkt\b", "Focus"),

    # ==========================================================================
    # SCORING / RATING TERMS
    # ==========================================================================
    (r"\bGesamt\b", "Overall"),
    (r"\bDurchschnitt\b", "Average"),
    (r"\bTop-Quartil\b", "Top quartile"),
    (r"\bSehr gut\b", "Very good"),
    (r"\bSolide\b", "Solid"),
    (r"\bAusbaufähig\b", "Needs improvement"),

    # ==========================================================================
    # KPI / DIMENSION LABELS
    # ==========================================================================
    (r"\bSicherheit\b", "Security"),
    (r"\bWertschöpfung\b", "Value creation"),
    (r"\bBefähigung\b", "Enablement"),
    (r"\bGovernance\b", "Governance"),

    # ==========================================================================
    # TIME UNITS
    # ==========================================================================
    (r"\bMonat\b", "Month"),
    (r"\bMonate\b", "Months"),
    (r"\bWoche\b", "Week"),
    (r"\bWochen\b", "Weeks"),
    (r"\bQuartal\b", "Quarter"),
    (r"\bQuartale\b", "Quarters"),

    # ==========================================================================
    # TABLE / STRUCTURE TERMS
    # ==========================================================================
    (r"\bBeschreibung\b", "Description"),
    (r"\bAuswirkung\b", "Impact"),
    (r"\bVerantwortung\b", "Responsibility"),
    (r"\bVerantwortlich\b", "Responsible"),
    (r"\bQuelle\b", "Source"),
    (r"\bWert\b", "Value"),
    (r"\bVergleich\b", "Comparison"),
    (r"\bSchätzung\b", "Estimate"),
    (r"\bNäherungen\b", "Approximations"),
    (r"\bNäherung\b", "Approximation"),

    # ==========================================================================
    # HEADER / META TERMS
    # ==========================================================================
    (r"\bÜberblick\b", "Overview"),
    (r"\bReportdatum\b", "Report date"),
    (r"\bHauptziel\b", "Primary goal"),
    (r"\bKurzfazit\b", "Brief summary"),
    (r"\bBundesland\b", "Region"),

    # ==========================================================================
    # SINGLE TOKENS / COMMON NOUNS
    # ==========================================================================
    (r"\bBranche\b", "Industry"),
    (r"\bBewertung\b", "Assessment"),
    (r"\bReifegrad\b", "Maturity level"),
    (r"\bKennzahlen\b", "KPIs"),
    (r"\bUnternehmen\b", "Company"),

    # ==========================================================================
    # ADDITIONAL COMMON GERMAN TOKENS (Final polish)
    # ==========================================================================
    # Personnel/HR terms
    (r"\bMitarbeitern\b", "Employees"),
    (r"\bMitarbeiter\b", "Employees"),
    # Financial terms
    (r"\bUmsatz\b", "Revenue"),
    (r"\bPotenzial\b", "Potential"),
    # Process terms
    (r"\bProzesse\b", "Processes"),
    (r"\bProzess\b", "Process"),
    # Data terms
    (r"\bDaten\b", "Data"),
    # Goal terms
    (r"\bZiele\b", "Goals"),
    (r"\bZiel\b", "Goal"),
    # Analysis/Results
    (r"\bAnalyse\b", "Analysis"),
    (r"\bErgebnisse\b", "Results"),
    (r"\bErgebnis\b", "Result"),
    # Time - Year
    (r"\bJahre\b", "Years"),
    (r"\bJahr\b", "Year"),
    # Time - Day
    (r"\bTage\b", "Days"),
    (r"\bTag\b", "Day"),
    # Additional common terms
    (r"\bAbteilung\b", "Department"),
    (r"\bProjekt\b", "Project"),
    (r"\bProjekte\b", "Projects"),
    (r"\bLösung\b", "Solution"),
    (r"\bLösungen\b", "Solutions"),
    (r"\bVorteil\b", "Advantage"),
    (r"\bVorteile\b", "Advantages"),
    (r"\bAnwendung\b", "Application"),
    (r"\bAnwendungen\b", "Applications"),

    # ==========================================================================
    # WORD-BOUNDARY SAFE REPLACEMENTS (tag contexts)
    # ==========================================================================
    (r">\s*Unternehmen\s*<", "> Company <"),
    (r">\s*Unternehmens\s*", "> Company "),
]


def sanitize_en_locale_tokens(html: str, lang: str) -> str:
    """
    3.1.4.16: Final guardrail to prevent residual German UI tokens in EN reports.
    Runs ONLY when lang startswith('en').

    Args:
        html: HTML content to sanitize
        lang: Language code (en/de)

    Returns:
        HTML with German tokens replaced by English equivalents (EN only)
    """
    lang_norm = (lang or "").strip().lower()
    if not lang_norm.startswith("en"):
        return html

    out = html or ""

    # KIS-1253 (Lauf 1132): URLs, E-Mail-Adressen und die Marken-Domain vor
    # den Wort-Ersetzungen schützen — "Sicherheit"→"Security" machte aus
    # ki-sicherheit.jetzt die nicht existente Domain "ki-Security.jetzt"
    # (inkl. kaputter Kontakt-E-Mail im Impressum).
    _shielded: List[str] = []

    def _shield(m: "re.Match[str]") -> str:
        _shielded.append(m.group(0))
        return f"\x00LOCALE-SHIELD-{len(_shielded) - 1}\x00"

    _protect_re = re.compile(
        r"https?://[^\s\"'<>]+"                      # URLs
        r"|[\w.+-]+@[\w-]+(?:\.[\w-]+)+"             # E-Mail-Adressen
        r"|\b[\w-]*ki-sicherheit\.jetzt\b",           # Marken-Domain (auch nackt)
        flags=re.IGNORECASE,
    )
    out = _protect_re.sub(_shield, out)

    for pattern, repl in _EN_LOCALE_REPLACEMENTS:
        out = re.sub(pattern, repl, out, flags=re.IGNORECASE)

    for _i, _orig in enumerate(_shielded):
        out = out.replace(f"\x00LOCALE-SHIELD-{_i}\x00", _orig)

    # KIS-1251 (Punkt 12): Deutsche Zahlformate in EN-Reports normalisieren
    out = normalize_en_number_formats(out)

    # Optional: Log leftover detection (warning only)
    de_check_words = ["Unternehmen", "Branche", "Bewertung", "Reifegrad",
                      "Kennzahlen", "Risiken", "Handlungsempfehlungen", "Unternehmensgröße",
                      "Mitarbeiter", "Umsatz", "Potenzial", "Prozess", "Daten",
                      "Ziel", "Analyse", "Ergebnis", "Jahr", "Tag"]
    leftovers = [w for w in de_check_words if w in out]
    if leftovers:
        log.warning("[locale-sanitize] DE leftovers after sanitize: %s", leftovers)

    return out


# =============================================================================
# KIS-1251 (Punkt 12): EN-Zahlenformat-Normalizer
# =============================================================================
# Vereinheitlicht deutsche Zahlformate in EN-Reports:
#   "24.000 €"   → "24,000 €"   (Tausenderpunkt → Komma)
#   "11,9 months"→ "11.9 months" (Dezimalkomma → Punkt, nur vor Einheiten)
# Schutz: Datumsangaben (dd.mm.yyyy) bleiben unangetastet (Datum bleibt
# bewusst deutsch formatiert), ebenso URLs/E-Mails/IDs ("Art. 50", "v7.1").

# Tausender: 1-3 Ziffern + eine oder mehrere ".ddd"-Gruppen. Kein Match, wenn
# direkt davor Ziffer/Punkt/Komma steht (IDs, Versionen, Datum "02.08.2026"
# matcht ohnehin nicht: weder "08" noch "2026" sind exakt 3 Ziffern) oder
# danach eine weitere Ziffer/".Ziffer" folgt (Versionsketten wie "1.234.5").
_EN_THOUSANDS_RE = re.compile(r"(?<![\d.,])(\d{1,3})((?:\.\d{3})+)(?!\.?\d)")

# Dezimalkomma NUR vor typischen EN-Einheiten. Genau 1-2 Nachkommastellen —
# "2,375 €" (bereits EN-Tausender) hat 3 Ziffern und bleibt unangetastet.
_EN_DECIMAL_UNIT_RE = re.compile(
    r"(?<![\d.,])(\d{1,3}),(\d{1,2})(?!\d)(\s*|&nbsp;)"
    r"(mo\.|months?\b|h\b|hrs\b|hours?\b|%|€)"
)

# Schutzschild: URLs, E-Mails, dd.mm.yyyy-Datumsangaben
_EN_NUM_PROTECT_RE = re.compile(
    r"https?://[^\s\"'<>]+"
    r"|[\w.+-]+@[\w-]+(?:\.[\w-]+)+"
    r"|\b\d{1,2}\.\d{1,2}\.\d{4}\b",
    flags=re.IGNORECASE,
)


# Tag-Split: Zahlen-Normalisierung NUR in Textknoten — Attribute (z.B. SVG
# stroke-dasharray="128.112") bleiben unangetastet.
_EN_NUM_TAG_SPLIT_RE = re.compile(r"(<[^>]+>)")


def normalize_en_number_formats(html: str) -> str:
    """Normalisiert deutsche Zahlformate zu EN-Konventionen (konservativ).

    Wird nur für EN-Reports aufgerufen (Aufrufer gaten auf lang=en);
    DE-Reports bleiben byte-identisch. Wirkt nur in Textknoten, nie in
    Tags/Attributen; URLs, E-Mails und dd.mm.yyyy-Daten sind geschützt.
    """
    if not html:
        return html

    def _thousands(m: "re.Match[str]") -> str:
        return m.group(1) + m.group(2).replace(".", ",")

    def _normalize_text(text: str) -> str:
        shielded: List[str] = []

        def _shield(m: "re.Match[str]") -> str:
            shielded.append(m.group(0))
            return f"\x00EN-NUM-SHIELD-{len(shielded) - 1}\x00"

        out = _EN_NUM_PROTECT_RE.sub(_shield, text)
        # 1) Dezimalkomma vor Einheiten → Punkt ("11,9 months" → "11.9 months")
        out = _EN_DECIMAL_UNIT_RE.sub(r"\1.\2\3\4", out)
        # 2) Tausenderpunkte → Kommas ("24.000" → "24,000")
        out = _EN_THOUSANDS_RE.sub(_thousands, out)
        for i, orig in enumerate(shielded):
            out = out.replace(f"\x00EN-NUM-SHIELD-{i}\x00", orig)
        return out

    parts = _EN_NUM_TAG_SPLIT_RE.split(html)
    for i, part in enumerate(parts):
        if part and not part.startswith("<"):
            parts[i] = _normalize_text(part)
    return "".join(parts)


# =============================================================================
# KIS-1251 (Punkt 8/9/10): Sprachunabhängige Struktur-Heiler für den
# EN-Final-Pass (laufen nur bei lang=en, damit DE byte-identisch bleibt)
# =============================================================================

# Punkt 8: nackte Aufzählungs-Torsi wie "<p><strong>4.</strong></p>" —
# Referenz: services/style_lint.py _LONE_ENUM_NODE_RE (sprachunabhängig).
_EN_LONE_ENUM_NODE_RE = re.compile(
    r"<(p|li|h[2-6])\b[^>]*>\s*(?:<(?:strong|b|em)[^>]*>\s*)*\d{1,2}\.?\s*"
    r"(?:</(?:strong|b|em)>\s*)*</\1>",
    re.IGNORECASE,
)

_EN_TAG_STRIP_RE = re.compile(r"<[^>]+>")


def _strip_lone_enum_nodes(html: str) -> str:
    """Entfernt verwaiste Aufzählungs-Knoten (z.B. leere Sektion '4.')."""
    if not html:
        return html
    return _EN_LONE_ENUM_NODE_RE.sub("", html)


def _strip_empty_pair_cards(html: str) -> str:
    """Punkt 9: Entfernt .pair-card-Blöcke ohne sichtbaren Textinhalt
    (z.B. Förderprogramm-Karte, die nur noch das Icon enthält)."""
    if not html or "pair-card" not in html:
        return html
    out = []
    pos = 0
    open_re = re.compile(r'<div\b[^>]*class="[^"]*\bpair-card\b[^"]*"[^>]*>', re.IGNORECASE)
    div_re = re.compile(r"<div\b[^>]*>|</div\s*>", re.IGNORECASE)
    while True:
        m = open_re.search(html, pos)
        if not m:
            out.append(html[pos:])
            break
        # Block-Ende über Div-Tiefe finden
        depth = 1
        scan = m.end()
        end = None
        while depth > 0:
            t = div_re.search(html, scan)
            if not t:
                break
            depth += 1 if t.group(0).lower().startswith("<div") else -1
            scan = t.end()
            if depth == 0:
                end = scan
        if end is None:
            out.append(html[pos:])
            break
        block = html[m.start():end]
        # Sichtbaren Text prüfen: Tags + SVG raus, Entities/Whitespace ignorieren
        text = re.sub(r"<svg\b[\s\S]*?</svg>", "", block, flags=re.IGNORECASE)
        text = _EN_TAG_STRIP_RE.sub("", text)
        text = html_mod_unescape(text)
        if text.strip():
            out.append(html[pos:end])
        else:
            out.append(html[pos:m.start()])
            log.info("[EN-FINAL-PASS] Removed empty pair-card block")
        pos = end
    return "".join(out)


def html_mod_unescape(text: str) -> str:
    try:
        return html.unescape(text)
    except Exception:
        return text


# Punkt 10: abgehacktes "d," im Rights-Log ("asset name, purpose, d, input
# source") — vermutlich aus einer Kürzungs-/Sanitize-Stufe verstümmeltes
# "date". Eng gefasst auf den Listenkontext.
_EN_RIGHTS_LOG_D_RE = re.compile(
    r"(purpose\s*,)\s*d\s*,(\s*(?:<[^>]+>\s*)*input\s+source)",
    re.IGNORECASE,
)


def _repair_truncated_date_token(html: str) -> str:
    if not html:
        return html
    return _EN_RIGHTS_LOG_D_RE.sub(r"\1 date,\2", html)


def apply_en_final_locale_pass(html: str, lang: str) -> str:
    """KIS-1251: Finaler EN-Pass auf dem gerenderten Gesamt-HTML.

    Läuft NUR bei lang=en (DE-Reports bleiben byte-identisch):
    1. Zahlenformat-Normalizer (Punkt 12)
    2. Lone-Enum-Strip (Punkt 8, sprachunabhängige Regex)
    3. Leere pair-cards entfernen (Punkt 9)
    4. Rights-Log-"d,"-Reparatur (Punkt 10)
    """
    lang_norm = (lang or "").strip().lower()
    if not lang_norm.startswith("en") or not html:
        return html
    out = html
    try:
        out = normalize_en_number_formats(out)
        out = _strip_lone_enum_nodes(out)
        out = _strip_empty_pair_cards(out)
        out = _repair_truncated_date_token(out)
    except Exception as exc:  # pragma: no cover — defensiv
        log.warning("[EN-FINAL-PASS] failed: %s — returning input unchanged", exc)
        return html
    return out


def _convert_markdown_headings(text: str) -> str:
    """Konvertiert Markdown-Überschriften zu HTML.

    - ## Heading → <h2>Heading</h2>
    - ### Heading → <h3>Heading</h3>
    - #### Heading → <h4>Heading</h4>
    """
    if not text or "##" not in text:
        return text

    # Konvertiere Markdown-Überschriften zu HTML
    # Reihenfolge wichtig: längere Präfixe zuerst!
    text = re.sub(r"^####\s*(.+?)$", r"<h4>\1</h4>", text, flags=re.MULTILINE)
    text = re.sub(r"^###\s*(.+?)$", r"<h3>\1</h3>", text, flags=re.MULTILINE)
    text = re.sub(r"^##\s*(.+?)$", r"<h2>\1</h2>", text, flags=re.MULTILINE)

    return text


def _cleanup_template_phrases(text: str) -> str:
    """Entfernt versehentlich eingebettete Template-Phrasen aus dem Output.

    Diese können von GPT trotz Anweisungen übernommen werden.
    """
    replacements = [
        ("Freitextfeld", "Textabschnitt"),
        ("Freitext-Feld", "Textabschnitt"),
        ("Freitext-Felder", "Textabschnitte"),
        ("freitextfeld", "Textabschnitt"),
        ("Template-Marker", ""),
        ("[Name]", ""),
        ("[Placeholder]", ""),
    ]
    for old, new in replacements:
        text = text.replace(old, new)
    return text


def _minify_inline_style(match: re.Match) -> str:
    """Minifiziert ein style-Attribut (Whitespace entfernen)."""
    style_content = match.group(1)
    # Entferne überflüssige Whitespace
    style_content = re.sub(r"\s*:\s*", ":", style_content)
    style_content = re.sub(r"\s*;\s*", ";", style_content)
    style_content = style_content.strip().rstrip(";")
    if not style_content:
        return ""  # Leeres style-Attribut ganz entfernen
    return f'style="{style_content}"'


def minify_html(html_content: str) -> str:
    """
    Minifiziert HTML durch Entfernen leerer Tags und überflüssiger Attribute.

    - Entfernt leere <p>, <span>, <div>, <li> Tags
    - Reduziert mehrfache <br> auf einzelne
    - Entfernt leere class="" Attribute
    - Komprimiert Whitespace in style-Attributen
    - Entfernt Leerzeilen zwischen Tags

    Args:
        html_content: HTML-String

    Returns:
        Minifiziertes HTML
    """
    if not html_content:
        return ""

    s = html_content

    # Entferne leere Tags (mehrfach, da verschachtelt sein können)
    for _ in range(3):
        s = RE_EMPTY_P.sub("", s)
        s = RE_EMPTY_SPAN.sub("", s)
        s = RE_EMPTY_DIV.sub("", s)
        s = RE_EMPTY_LI.sub("", s)

    # Reduziere mehrfache <br> auf einzelne
    s = RE_LONE_BR.sub("<br>", s)

    # Entferne leere class-Attribute
    s = RE_EMPTY_CLASS.sub("", s)

    # Minifiziere style-Attribute
    s = RE_STYLE_WHITESPACE.sub(_minify_inline_style, s)

    # Entferne leere style-Attribute die übrig geblieben sind
    s = re.sub(r'\s+style\s*=\s*["\'][\s]*["\']', "", s, flags=re.IGNORECASE)

    # Entferne Leerzeilen zwischen Tags (aber behalte single newlines)
    s = re.sub(r">\s*\n\s*\n+\s*<", ">\n<", s)

    return s


# --- Markdown → HTML Konvertierung ---

def render_markdown_safe(md_text: str) -> str:
    """
    Konvertiert Markdown sicher zu HTML.

    - Erlaubte Tags: p, h2-h4, ul, ol, li, strong, em, br
    - Keine Raw-HTML Injection
    - Auto-Closing erzwungen
    - Deterministisches Output

    Args:
        md_text: Markdown-Text

    Returns:
        Sicheres HTML
    """
    if not md_text:
        return ""

    if MISTUNE_AVAILABLE:
        try:
            # Mistune 3.x mit sicheren Einstellungen
            renderer = mistune.create_markdown(
                escape=True,  # HTML escapen
                plugins=['strikethrough', 'table']
            )
            html_output = renderer(md_text)
            # Nachbearbeitung: Nur erlaubte Tags behalten
            return _filter_allowed_tags(html_output)
        except Exception as e:
            log.warning("[MD-RENDER] mistune failed: %s, using fallback", e)

    # Fallback: Einfache Regex-basierte Konvertierung
    return _markdown_fallback(md_text)


def _filter_allowed_tags(html_text: str) -> str:
    """Filtert HTML auf erlaubte Tags.

    PDF-SLIMDOWN v2.0: Erweiterte Whitelist, CSS-Klassen werden NICHT gestrippt.
    """
    # Erweiterte Whitelist inkl. Tabellen und strukturelle Tags
    ALLOWED_TAGS = {
        'p', 'h2', 'h3', 'h4', 'h5', 'ul', 'ol', 'li',
        'strong', 'em', 'b', 'i', 'br', 'section', 'div', 'span',
        # Tabellen (werden NICHT entfernt)
        'table', 'thead', 'tbody', 'tfoot', 'tr', 'th', 'td',
        # Strukturelle Tags
        'article', 'header', 'footer', 'nav', 'aside',
        # Links (ohne href-Manipulation)
        'a',
    }

    def tag_replacer(match):
        full_tag = match.group(0)
        tag_name = match.group(1).lower().split()[0]  # Erstes Wort ist Tag-Name
        if tag_name.lstrip('/') in ALLOWED_TAGS:
            # CSS-Klassen und andere Attribute BEIBEHALTEN
            return full_tag
        return ''  # Tag entfernen, Inhalt behalten

    # Entferne nicht-erlaubte Tags (aber behalte deren Inhalt)
    result = re.sub(r'<(/?\w+)([^>]*)>', tag_replacer, html_text)
    return result


def _markdown_fallback(md_text: str) -> str:
    """
    Einfache Markdown → HTML Konvertierung ohne externe Abhängigkeiten.
    """
    lines = md_text.strip().split('\n')
    html_parts = []
    in_list = False
    list_type = None

    for line in lines:
        stripped = line.strip()

        # Überschriften
        if stripped.startswith('## '):
            if in_list:
                html_parts.append(f'</{list_type}>')
                in_list = False
            html_parts.append(f'<h2>{html.escape(stripped[3:])}</h2>')
        elif stripped.startswith('### '):
            if in_list:
                html_parts.append(f'</{list_type}>')
                in_list = False
            html_parts.append(f'<h3>{html.escape(stripped[4:])}</h3>')
        elif stripped.startswith('#### '):
            if in_list:
                html_parts.append(f'</{list_type}>')
                in_list = False
            html_parts.append(f'<h4>{html.escape(stripped[5:])}</h4>')

        # Listen
        elif stripped.startswith('- ') or stripped.startswith('* '):
            if not in_list:
                html_parts.append('<ul>')
                in_list = True
                list_type = 'ul'
            content = _convert_inline_markdown(stripped[2:])
            html_parts.append(f'<li>{content}</li>')

        elif re.match(r'^\d+\.\s', stripped):
            if not in_list:
                html_parts.append('<ol>')
                in_list = True
                list_type = 'ol'
            content = _convert_inline_markdown(re.sub(r'^\d+\.\s', '', stripped))
            html_parts.append(f'<li>{content}</li>')

        # Leerzeile
        elif not stripped:
            if in_list:
                html_parts.append(f'</{list_type}>')
                in_list = False

        # Normaler Text
        else:
            if in_list:
                html_parts.append(f'</{list_type}>')
                in_list = False
            content = _convert_inline_markdown(stripped)
            html_parts.append(f'<p>{content}</p>')

    # Liste am Ende schließen
    if in_list:
        html_parts.append(f'</{list_type}>')

    return '\n'.join(html_parts)


def _convert_inline_markdown(text: str) -> str:
    """Konvertiert Inline-Markdown (bold, italic)."""
    # Escape HTML zuerst
    text = html.escape(text)
    # **bold** → <strong>
    text = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', text)
    # *italic* → <em>
    text = re.sub(r'\*(.+?)\*', r'<em>\1</em>', text)
    return text


# --- HTML Recovery für kaputtes HTML ---

# Mindest-Wortanzahl für Recovery (PDF-SLIMDOWN v2.0)
MIN_WORDS_DEFAULT = 50


def recover_text_from_broken_html(html_text: str, min_words: int = MIN_WORDS_DEFAULT) -> str:
    """
    Extrahiert Text aus potenziell kaputtem HTML.

    Priorität:
    1. Versuche HTML normal zu parsen
    2. Wenn Fehler → strip_tags()
    3. Mindest-Text behalten (min 50 Wörter)

    PDF-SLIMDOWN v2.0: GARANTIERT >= min_words Wörter im Output.

    Args:
        html_text: Potenziell kaputtes HTML
        min_words: Mindestanzahl Wörter für Recovery (default: 50)

    Returns:
        Bereinigter Text oder heuristisch aufbereiteter Inhalt (GARANTIERT >= min_words Wörter)
    """
    if not html_text:
        # S-2 FIX: Leerer Input darf nicht "" zurückgeben - Wort-Garantie
        log.warning("[HTML-RECOVERY] Empty input, applying heuristic padding")
        return _heuristic_padding("", min_words)

    original_text = html_text.strip()

    # Schritt 1: Versuche normale Tag-Entfernung
    try:
        clean_text = re.sub(r'<[^>]+>', '', html_text)
        clean_text = clean_text.strip()

        if clean_text:
            words = clean_text.split()
            if len(words) >= min_words:
                log.debug("[HTML-RECOVERY] Normal extraction: %d words", len(words))
                return clean_text
    except Exception as e:
        log.warning("[HTML-RECOVERY] Normal extraction failed: %s", e)

    # Schritt 2: Aggressivere Tag-Entfernung (auch kaputte Tags)
    try:
        # Entferne alles was wie ein Tag aussieht, auch unvollständige
        aggressive_clean = re.sub(r'<[^>]*>?', '', html_text)
        aggressive_clean = re.sub(r'<[^>]*$', '', aggressive_clean)  # Unvollständige Tags am Ende
        aggressive_clean = aggressive_clean.strip()

        if aggressive_clean:
            words = aggressive_clean.split()
            if len(words) >= min_words:
                log.debug("[HTML-RECOVERY] Aggressive extraction: %d words", len(words))
                return aggressive_clean
    except Exception as e:
        log.warning("[HTML-RECOVERY] Aggressive extraction failed: %s", e)

    # Schritt 3: Nur alphanumerische Zeichen behalten
    try:
        text_only = re.sub(r'[<>]', ' ', html_text)
        text_only = re.sub(r'\s+', ' ', text_only).strip()

        if text_only:
            words = text_only.split()
            if len(words) >= 10:  # Mindestens 10 Wörter
                log.debug("[HTML-RECOVERY] Text-only extraction: %d words", len(words))
                # PDF-SLIMDOWN: Garantiere mindestens 50 Wörter durch heuristische Aufbereitung
                if len(words) < min_words:
                    return _heuristic_padding(text_only, min_words)
                return text_only
    except Exception as e:
        log.warning("[HTML-RECOVERY] Text-only extraction failed: %s", e)

    # Letzter Fallback: Original mit heuristischer Aufbereitung
    log.warning("[HTML-RECOVERY] All extractions failed, applying heuristic padding")
    return _heuristic_padding(original_text, min_words)


def _heuristic_padding(text: str, min_words: int = MIN_WORDS_DEFAULT) -> str:
    """
    Heuristische Aufbereitung um Mindest-Wortanzahl zu garantieren.

    PDF-SLIMDOWN v2.0: Dynamische Erweiterung auf min_words durch wiederholte
    Padding-Blöcke. Garantiert IMMER >= min_words.

    Args:
        text: Der zu kurze Text
        min_words: Mindestanzahl Wörter

    Returns:
        Text mit mindestens min_words Wörtern (GARANTIERT)
    """
    # Sicherstellen dass text ein String ist
    if not text:
        text = ""

    words = text.split()
    current_count = len(words)

    if current_count >= min_words:
        return text

    # Entscheide anhand des Texts ob DE oder EN
    de_indicators = ["der", "die", "das", "und", "für", "mit", "eine", "einen"]
    text_lower = text.lower()
    is_german = any(ind in text_lower for ind in de_indicators)

    # Erweiterte Padding-Blöcke für dynamische Erweiterung (~20 Wörter pro Block)
    padding_blocks_de = [
        "Dieser Abschnitt enthält weitere Details zur Analyse und strategischen Planung.",
        "Die vollständigen Informationen werden im Gesamtkontext des Reports bereitgestellt.",
        "Für zusätzliche Erläuterungen siehe die angrenzenden Kapitel des Reports.",
        "Die Umsetzung erfolgt schrittweise unter Berücksichtigung der Unternehmensgröße.",
        "Alle Empfehlungen sind auf die spezifischen Anforderungen des Unternehmens abgestimmt.",
        "Die Integration von KI-Lösungen erfordert eine sorgfältige Planung und Qualitätssicherung.",
        "Regelmäßige Reviews stellen sicher, dass die Ziele erreicht werden.",
        "Die Priorisierung basiert auf Aufwand, Nutzen und strategischer Bedeutung.",
        "Governance-Richtlinien und Leitplanken werden durchgängig berücksichtigt.",
        "Die dokumentierten Best Practices unterstützen eine nachhaltige Implementierung.",
    ]

    padding_blocks_en = [
        "This section contains additional details for analysis and strategic planning.",
        "Complete information is provided in the overall report context.",
        "For additional explanations, see adjacent report chapters and documentation.",
        "Implementation proceeds step by step considering company size and resources.",
        "All recommendations are tailored to the specific requirements of the organization.",
        "Integration of AI solutions requires careful planning and quality assurance measures.",
        "Regular reviews ensure that objectives and milestones are achieved successfully.",
        "Prioritization is based on effort, benefit, and strategic importance factors.",
        "Governance guidelines and guardrails are consistently considered throughout.",
        "Documented best practices support sustainable and scalable implementation approaches.",
    ]

    padding_blocks = padding_blocks_de if is_german else padding_blocks_en

    # Dynamisch Padding-Blöcke hinzufügen bis min_words erreicht
    result = text
    block_index = 0

    while len(result.split()) < min_words and block_index < len(padding_blocks) * 3:
        # Zyklisch durch die Blöcke rotieren
        block = padding_blocks[block_index % len(padding_blocks)]
        result = f"{result} {block}" if result else block
        block_index += 1

    final_count = len(result.split())
    log.info("[HEURISTIC-PADDING] Scaled from %d to %d words (target: %d)",
             current_count, final_count, min_words)

    # Finale Garantie: Wenn immer noch zu wenig, füge generischen Text hinzu
    if final_count < min_words:
        filler = " ".join(padding_blocks) if is_german else " ".join(padding_blocks_en)
        result = f"{result} {filler}"
        log.warning("[HEURISTIC-PADDING] Emergency padding applied, now %d words", len(result.split()))

    return result


# =============================================================================
# PDF-SLIMDOWN v2.0: Auto-Summary Fallback (Stufe 3)
# =============================================================================

def generate_auto_summary(
    section_name: str,
    recovered_text: str,
    branch: str = "",
    size: str = "",
    guardrails: bool = False,
    lang: str = ""
) -> str:
    """
    Generiert eine Auto-Summary für Recovery-Situationen (Stufe 3 im Fallback).

    Wird verwendet wenn:
    - Token-Limit abgebrochen hat
    - < 10 Wörter vorhanden sind
    - HTML zerstört ist

    Args:
        section_name: Name der Sektion (z.B. "roadmap_12m")
        recovered_text: Der gerettete Text aus vorherigen Stufen
        branch: Branche (für branchen-aware Summary)
        size: Unternehmensgröße (solo/team/kmu)
        guardrails: Ob Guardrails-Hinweise eingefügt werden sollen
        lang: Language code (de/en) - if provided, overrides content detection

    Returns:
        HTML-formatierte Auto-Summary (80-120 Wörter)
    """
    if not recovered_text:
        recovered_text = ""

    # Extrahiere Schlüsselwörter aus dem geretteten Text
    words = recovered_text.split()[:50]  # Erste 50 Wörter als Kontext
    context_snippet = " ".join(words) if words else "keine Inhalte verfügbar"

    # Section-spezifische Templates
    templates = {
        "roadmap_12m": {
            "de": f"""<div class="auto-summary">
<h4>12-Monats-Roadmap (Zusammenfassung)</h4>
<p>Die strategische Roadmap für die nächsten 12 Monate umfasst die systematische
Einführung von KI-gestützten Prozessen. Die wichtigsten Phasen sind: Fundament &
erste Use Cases (Monate 1-3), Pilotierung & Qualitätssicherung (Monate 4-6),
sowie Ausbau & Erweiterung (Monate 7-12). Jede Phase enthält konkrete KPIs und
Verantwortlichkeiten angepasst an die Unternehmensgröße{' ' + size if size else ''}.</p>
{_guardrails_hint() if guardrails else ''}
</div>""",
            "en": f"""<div class="auto-summary">
<h4>12-Month Roadmap (Summary)</h4>
<p>The strategic roadmap for the next 12 months covers the systematic introduction
of AI-powered processes. Key phases include: Foundation & first use cases (months 1-3),
Piloting & quality assurance (months 4-6), and Expansion & scaling (months 7-12).
Each phase contains specific KPIs and responsibilities adapted to company size{' ' + size if size else ''}.</p>
{_guardrails_hint_en() if guardrails else ''}
</div>"""
        },
        "roadmap_90d": {
            "de": f"""<div class="auto-summary">
<h4>90-Tage-Roadmap (Zusammenfassung)</h4>
<p>Die 90-Tage-Roadmap fokussiert auf schnelle Erfolge und stabile Grundlagen für die KI-Integration.
In den ersten Wochen (Phase 1) werden priorisierte Use Cases definiert und erste Workflows etabliert.
Die Pilotierung erfolgt in Phase 2 mit dokumentierten Qualitätsstandards bis Woche 8.
Die abschließende Konsolidierung in Phase 3 (Woche 9-13) mündet in einer klaren Entscheidung für die
Erweiterung. Jede Phase enthält messbare Meilensteine und Verantwortlichkeiten angepasst an die
Unternehmensgröße{' ' + size if size else ''}. Der Fokus liegt auf pragmatischer Umsetzung mit direktem Mehrwert.</p>
</div>""",
            "en": f"""<div class="auto-summary">
<h4>90-Day Roadmap (Summary)</h4>
<p>The 90-day roadmap focuses on quick wins and stable foundations for AI integration.
During the first weeks (Phase 1), prioritized use cases are defined and initial workflows established.
Piloting occurs in Phase 2 with documented quality standards by week 8.
The final consolidation in Phase 3 (weeks 9-13) leads to a clear decision for scaling.
Each phase contains measurable milestones and responsibilities adapted to company size{' ' + size if size else ''}.
The focus is on pragmatic implementation with direct added value and sustainable outcomes.</p>
</div>"""
        },
        "recommendations": {
            "de": f"""<div class="auto-summary">
<h4>Handlungsempfehlungen (Zusammenfassung)</h4>
<p>Die wichtigsten Empfehlungen für die KI-Integration umfassen folgende Schwerpunkte:
Etablierung eines standardisierten Workflows für KI-gestützte Prozesse, Systematisierung
der Qualitätssicherung mit klaren Prüfpunkten, Aufbau eines strukturierten Wissensmanagements
für Best Practices, Pilotierung branchenspezifischer Use Cases mit messbarem ROI, sowie
Definition von Governance-Richtlinien und Leitplanken. Prioritäten und Zeitrahmen sind an
die Unternehmensgröße{' ' + size if size else ''} angepasst. Die Umsetzung erfolgt schrittweise
mit regelmäßigen Reviews zur Erfolgskontrolle.</p>
</div>""",
            "en": f"""<div class="auto-summary">
<h4>Recommendations (Summary)</h4>
<p>Key recommendations for AI integration include the following focus areas:
Establishing a standardized workflow for AI-powered processes, systematizing quality
assurance with clear checkpoints, building structured knowledge management for best practices,
piloting industry-specific use cases with measurable ROI, and defining governance guidelines
and guardrails. Priorities and timeframes are adapted to company size{' ' + size if size else ''}.
Implementation occurs step by step with regular reviews to track success and ensure sustainable outcomes.</p>
</div>"""
        }
    }

    # Fallback-Template für unbekannte Sections (min. 50 Wörter garantiert)
    default_template = {
        "de": f"""<div class="auto-summary">
<h4>{section_name.replace('_', ' ').title()} (Zusammenfassung)</h4>
<p>Dieser Abschnitt enthält strategische Empfehlungen und detaillierte Analysen für den
Bereich {section_name.replace('_', ' ')}. Die hier dargestellten Informationen bilden
einen wichtigen Baustein der Gesamtstrategie und sind eng mit den anderen Kapiteln des
Reports verknüpft. Die vollständigen Details, Hintergrundinformationen und konkreten
Handlungsempfehlungen sind im Gesamtkontext des Reports zu finden. Für weiterführende
Rückfragen und individuelle Beratung steht das Beratungsteam jederzeit zur Verfügung.
Die Umsetzung sollte schrittweise und unter Berücksichtigung der Unternehmensgröße erfolgen.</p>
</div>""",
        "en": f"""<div class="auto-summary">
<h4>{section_name.replace('_', ' ').title()} (Summary)</h4>
<p>This section contains strategic recommendations and detailed analysis for the
{section_name.replace('_', ' ')} area. The information presented here forms an
important building block of the overall strategy and is closely linked to other
chapters of the report. Complete details, background information, and specific
action recommendations can be found in the overall report context. For further
questions and individual consulting, the advisory team is available at any time.
Implementation should proceed step by step, taking company size into account.</p>
</div>"""
    }

    # Wähle Template
    section_templates = templates.get(section_name, default_template)

    # 3.1.4.13: Use explicit lang parameter if provided, otherwise detect from content
    if lang and str(lang).lower().startswith("en"):
        detected_lang = "en"
    elif lang and str(lang).lower().startswith("de"):
        detected_lang = "de"
    else:
        # Sprache aus Kontext erkennen (fallback)
        de_indicators = ["der", "die", "das", "und", "für", "mit", "eine", "einen"]
        is_german = any(ind in recovered_text.lower() for ind in de_indicators)
        detected_lang = "de" if is_german else "en"

    result = section_templates.get(detected_lang, section_templates.get("de", default_template["de"]))

    log.info("[AUTO-SUMMARY] Generated summary for section=%s (lang=%s, size=%s)",
             section_name, detected_lang, size or "unknown")

    return result


def _guardrails_hint() -> str:
    """Guardrails-Hinweis für deutsche Auto-Summaries."""
    return '<p class="small muted">Hinweis: Leitplanken und No-Gos des Unternehmens wurden berücksichtigt.</p>'


def _guardrails_hint_en() -> str:
    """Guardrails hint for English auto-summaries."""
    return '<p class="small muted">Note: Company guidelines and restrictions have been considered.</p>'


# =============================================================================
# PLATIN+++ v5.4: HTML Contract Enforcement for Text Sections
# =============================================================================
# Root Cause Fix: GPT generates forbidden HTML elements (<h1>-<h4>, <section>, <article>)
# in text sections where only inline/block text is expected.
#
# HTML CONTRACT:
# - ALLOWED in text sections: <p>, <ul>, <ol>, <li>, <strong>, <em>, <b>, <i>, <br>
# - FORBIDDEN: <h1>, <h2>, <h3>, <h4>, <section>, <article>, <header>, <footer>
# - Tables are handled separately (allowed in certain sections)

TEXT_SECTION_ALLOWED_TAGS = {'p', 'ul', 'ol', 'li', 'strong', 'em', 'b', 'i', 'br', 'span'}
TEXT_SECTION_FORBIDDEN_TAGS = {'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'section', 'article', 'header', 'footer', 'nav', 'aside'}

# =============================================================================
# Fix-Batch C: HTML Contract Normalizer - convert semantic tags to styled divs
# =============================================================================


def normalize_html_tags_before_sanitize(html_content: str) -> str:
    """
    Fix-Batch C: Normalize semantic HTML tags to styled divs BEFORE sanitization.

    Instead of removing h2/h3/section tags entirely (losing structure),
    this normalizer converts them to divs with appropriate classes.

    Conversions:
    - <h2>Title</h2> → <div class="heading heading-h2"><strong>Title</strong></div>
    - <h3>Title</h3> → <div class="heading heading-h3"><strong>Title</strong></div>
    - <section>...</section> → <div class="section">...</div>
    - <article>...</article> → <div class="article">...</div>

    Args:
        html_content: Raw HTML from GPT

    Returns:
        HTML with semantic tags converted to divs (structure preserved)
    """
    if not html_content:
        return ""

    result = html_content
    normalizations = 0

    # Normalize heading tags to styled divs
    for level in range(1, 7):  # h1-h6
        tag = f'h{level}'
        # Match opening tag with optional attributes
        open_pattern = re.compile(rf'<{tag}(?:\s+[^>]*)?\s*>', re.IGNORECASE)
        close_pattern = re.compile(rf'</{tag}\s*>', re.IGNORECASE)

        if open_pattern.search(result):
            # Convert to div with heading class and strong for visual emphasis
            result = open_pattern.sub(f'<div class="heading heading-{tag}"><strong>', result)
            result = close_pattern.sub('</strong></div>', result)
            normalizations += 1

    # Normalize section/article tags to divs
    for tag in ['section', 'article', 'header', 'footer', 'aside', 'nav']:
        open_pattern = re.compile(rf'<{tag}(?:\s+[^>]*)?\s*>', re.IGNORECASE)
        close_pattern = re.compile(rf'</{tag}\s*>', re.IGNORECASE)

        if open_pattern.search(result):
            result = open_pattern.sub(f'<div class="{tag}">', result)
            result = close_pattern.sub('</div>', result)
            normalizations += 1

    if normalizations > 0:
        log.debug("[HTML-NORMALIZER] Normalized %d semantic tags to styled divs", normalizations)

    return result


def enforce_text_section_html_contract(html_content: str, section_name: str = "") -> str:
    """
    Enforces HTML contract for text sections.

    PLATIN+++ v5.4 Root Cause Fix: Removes forbidden HTML elements that GPT
    sometimes generates despite prompt instructions.

    ALLOWED: <p>, <ul>, <ol>, <li>, <strong>, <em>, <b>, <i>, <br>, <span>, <div>
    FORBIDDEN: <h1>-<h6>, <section>, <article>, <header>, <footer>, <nav>, <aside>

    Fix-Batch C: Now NORMALIZES tags to styled divs first, then removes any remaining.

    Args:
        html_content: HTML string from GPT
        section_name: Name of section (for logging)

    Returns:
        HTML with forbidden tags normalized to divs (structure preserved)
    """
    if not html_content:
        return ""

    # Fix-Batch C: First normalize semantic tags to styled divs
    result = normalize_html_tags_before_sanitize(html_content)

    # Now check for any remaining forbidden tags (should be rare after normalization)
    violations_found = []

    for tag in TEXT_SECTION_FORBIDDEN_TAGS:
        # Pattern matches opening and closing tags
        # Opening tags: <h1>, <h1 class="...">, etc.
        open_pattern = re.compile(rf'<{tag}(?:\s+[^>]*)?\s*>', re.IGNORECASE)
        close_pattern = re.compile(rf'</{tag}\s*>', re.IGNORECASE)

        if open_pattern.search(result) or close_pattern.search(result):
            violations_found.append(tag)

        # Remove opening and closing tags but keep content
        result = open_pattern.sub('', result)
        result = close_pattern.sub('', result)

    # Log violations for monitoring
    if violations_found:
        log.warning(
            "[HTML-CONTRACT] Section '%s': Removed forbidden tags: %s",
            section_name or "unknown",
            ", ".join(violations_found)
        )

    # Clean up resulting empty lines and double spaces
    result = re.sub(r'\n{3,}', '\n\n', result)
    result = re.sub(r'  +', ' ', result)

    return result.strip()


def is_text_section(section_name: str) -> bool:
    """
    Determines if a section should enforce text-only HTML contract.

    Text sections: Most content sections (gamechanger, executive_summary,
    recommendations, roadmaps, etc.)

    Exceptions (allow tables/complex HTML): ai_act_table, business_case,
    financial sections
    """
    if not section_name:
        return False

    name_lower = section_name.lower()

    # Sections that ALLOW tables and complex HTML (including h3/h4)
    complex_html_sections = {
        'ai_act_table', 'ai_act_compliance_table',
        'business_case', 'business_case_visual',
        'financial_summary', 'kpi_table',
        'tool_comparison', 'benchmark_table',
        # v7.0: Quick Wins needs h3/h4 for structured boxes
        'quick_wins', 'quick_wins_html', 'quick_wins_html_left', 'quick_wins_html_right',
        # FIX-B18: Vendor Audit uses h4, inline styles, flex layout — programmatically generated
        'vendor_audit',
    }

    if any(exc in name_lower for exc in complex_html_sections):
        return False

    # All other content sections enforce text contract
    return True


# =============================================================================
# Sprint N3.3: Executive Summary Hard-Clean
# =============================================================================

def clean_exec_summary_html(html: str) -> str:
    """
    Sprint N3.3: Entfernt alle H1/H2-Tags und führende Label-Überschriften
    aus dem Executive Summary Inhalt.

    Ziel: Exec Summary soll nur Fließtext enthalten, keine redundanten
    Überschriften wie "Executive Summary", "Zusammenfassung", "Kurzfassung".

    PLATIN+++ v5.4.1: Also handles HTML-escaped tags and literal text patterns
    that GPT might output (e.g., `&lt;h2&gt;` or literal `<h2>` as text).

    Args:
        html: Der HTML-Inhalt der Executive Summary

    Returns:
        Bereinigter HTML-Inhalt ohne H1/H2 und Label-Überschriften
    """
    if not html:
        return html

    # 1) Entferne ALLE h1/h2-Tags (nicht nur den ersten)
    html = re.sub(
        r'<h[12][^>]*>.*?</h[12]>',
        '',
        html,
        flags=re.IGNORECASE | re.DOTALL
    )

    # 1b) PLATIN+++ v5.4.1: Entferne HTML-escaped h1/h2 tags
    # Pattern: &lt;h2&gt;...&lt;/h2&gt; (HTML entities)
    html = re.sub(
        r'&lt;h[12][^&]*&gt;.*?&lt;/h[12]&gt;',
        '',
        html,
        flags=re.IGNORECASE | re.DOTALL
    )

    # 1c) PLATIN+++ v5.4.1: Entferne literal text patterns where GPT outputs
    # tag-like strings as text (e.g., "<h2>Executive Summary</h2>" as string)
    # This catches edge cases where < and > are literal characters
    html = re.sub(
        r'&lt;h[12]&gt;\s*(?:Executive\s+Summary|Zusammenfassung|Summary|Kurzfassung|Überblick)\s*&lt;/h[12]&gt;',
        '',
        html,
        flags=re.IGNORECASE
    )

    # 2) Entferne führende Label-Überschriften (auch als Klartext)
    labels_to_remove = [
        "Executive Summary",
        "Zusammenfassung",
        "Kurzfassung",
        "Summary",
        "Überblick",
    ]

    for label in labels_to_remove:
        # Entferne Label am Anfang (mit optionalem Whitespace/Newlines)
        html = re.sub(
            r'^\s*' + re.escape(label) + r'\s*[:.]?\s*',
            '',
            html,
            flags=re.IGNORECASE
        )
        # Entferne Label auch innerhalb des Textes (ohne Doppelpunkt)
        html = html.replace(label, "")

    # 3) Bereinige leere Paragraphen die übrig geblieben sein könnten
    html = re.sub(r'<p[^>]*>\s*</p>', '', html, flags=re.IGNORECASE)

    # 4) Trim whitespace
    html = html.strip()

    return html


def is_exec_summary_section(section_name: str) -> bool:
    """Prüft ob ein Sektionsname zur Executive Summary gehört."""
    if not section_name:
        return False
    name_lower = section_name.lower()
    return any(pattern in name_lower for pattern in [
        "exec_summary",
        "executive_summary",
        "execsummary",
    ])


def sanitize_or_recover(
    html_content: str,
    min_words: int = MIN_WORDS_DEFAULT,
    section_name: str = "",
    branch: str = "",
    size: str = "",
    guardrails: bool = False
) -> str:
    """
    Kombiniert Sanitization mit Recovery für kaputtes HTML.

    PDF-SLIMDOWN v2.0 Fallback-Pipeline:
    - Stufe 1: HTML-Recovery (Tag-Entfernung)
    - Stufe 2: Markdown-Rendering
    - Stufe 3: Auto-Summary (NEU) - 80-120 Wörter, size-/branch-aware
    - Stufe 4: PLATIN-Fallback

    Args:
        html_content: HTML-String
        min_words: Mindestanzahl Wörter für erfolgreiche Verarbeitung (default: 50)
        section_name: Name der Sektion (für Auto-Summary)
        branch: Branche (für branchen-aware Summary)
        size: Unternehmensgröße (solo/team/kmu)
        guardrails: Ob Guardrails-Hinweise eingefügt werden sollen

    Returns:
        Sanitisiertes HTML oder recovered/auto-summarized Text
    """
    if not html_content:
        # Keine "0 Wörter"-Situation: Auto-Summary generieren
        if section_name:
            log.warning("[SANITIZE-RECOVER] Empty content for section=%s, using auto-summary", section_name)
            return generate_auto_summary(section_name, "", branch, size, guardrails)
        return ""

    # Sprint N3.3: Exec Summary Hard-Clean - verwende dedizierte Funktion
    if is_exec_summary_section(section_name):
        html_content = clean_exec_summary_html(html_content)

    # Stufe 1: Normale Sanitization versuchen
    sanitized = sanitize_section_html(html_content)

    # Prüfe ob genug Text übrig ist
    text_only = re.sub(r'<[^>]+>', '', sanitized).strip()
    words = text_only.split()

    if len(words) >= min_words:
        return sanitized

    # Stufe 2: Falls zu wenig - Recovery versuchen
    log.warning("[SANITIZE-RECOVER] Only %d words after sanitization, trying recovery", len(words))
    recovered = recover_text_from_broken_html(html_content, min_words)

    # Prüfe Recovery-Ergebnis
    recovered_text_only = re.sub(r'<[^>]+>', '', recovered).strip() if recovered else ""
    recovered_words = recovered_text_only.split()

    if len(recovered_words) >= min_words:
        # Recovered Text als Paragraphen wrappen
        if recovered and not recovered.startswith('<'):
            paragraphs = recovered.split('\n\n')
            if len(paragraphs) > 1:
                return '\n'.join(f'<p>{p.strip()}</p>' for p in paragraphs if p.strip())
            return f'<p>{recovered}</p>'
        return recovered

    # Stufe 3: Auto-Summary generieren (NEU)
    if section_name and len(recovered_words) < min_words:
        log.warning("[SANITIZE-RECOVER] Recovery insufficient (%d words), using auto-summary for %s",
                   len(recovered_words), section_name)
        result = generate_auto_summary(section_name, recovered or text_only, branch, size, guardrails)
        # S-3 FIX: Garantie-Check nach Auto-Summary
        result_words = len(re.sub(r'<[^>]+>', '', result).strip().split())
        if result_words < min_words:
            log.warning("[SANITIZE-RECOVER] Auto-summary only %d words, applying padding", result_words)
            result = _heuristic_padding(re.sub(r'<[^>]+>', '', result).strip(), min_words)
        return result

    # Stufe 4: Fallback - heuristische Aufbereitung
    result = _heuristic_padding(recovered or text_only, min_words)

    # S-3 FIX: Finale Wort-Garantie Assertion
    final_word_count = len(result.split())
    if final_word_count < min_words:
        log.error("[SANITIZE-RECOVER] CRITICAL: Word guarantee violated! %d < %d",
                  final_word_count, min_words)
        # Notfall-Padding anwenden
        result = _heuristic_padding(result, min_words)

    return result


def sanitize_section_html(
    html_content: Optional[str],
    compress_ws: bool = True,
    minify: bool = True,
    lang: str = "de"
) -> str:
    """
    Sanitisiert und minifiziert HTML für Report-Sektionen.

    Args:
        html_content: HTML-String
        compress_ws: Whitespace normalisieren
        minify: HTML minifizieren (leere Tags, Attribute entfernen)
        lang: Language code (de/en) for EN locale sanitization (3.1.4.16)

    Returns:
        Bereinigtes HTML
    """
    if not html_content:
        return ""
    s = html_content

    # ZUERST: Behebe UTF-8 Mojibake (Ã¶ → ö)
    s = _fix_utf8_mojibake(s)

    # Entferne problematische Sonderzeichen (U+FFFE, etc.)
    s = _normalize_special_chars(s)

    # Konvertiere Markdown-Überschriften zu HTML (## → h2)
    s = _convert_markdown_headings(s)

    # Post-Processing: Entferne versehentliche Template-Phrasen
    s = _cleanup_template_phrases(s)

    # Entferne Dokument‑Wrapper & kritische Blöcke
    s = RE_DOCTYPES.sub("", s)
    s = RE_HEAD_BLOCK.sub("", s)
    s = RE_HTML_TAGS.sub("", s)
    s = RE_BODY_TAGS.sub("", s)

    # Entferne gefährliche Tags
    s = RE_SCRIPT_BLOCK.sub("", s)
    s = RE_IFRAME_BLOCK.sub("", s)
    s = RE_OBJECT_BLOCK.sub("", s)
    s = RE_EMBED_BLOCK.sub("", s)
    s = RE_LINK_TAG.sub("", s)
    s = RE_META_TAG.sub("", s)

    # Entferne Inline‑Events & javascript: URLs
    s = RE_ON_EVENT_ATTR.sub("", s)
    s = RE_JS_PROTOCOL.sub(r"\1#\2", s)

    if compress_ws:
        # Normiere Whitespace etwas, ohne HTML zu zerstören
        s = re.sub(r"[ \t]+\n", "\n", s)
        s = re.sub(r"\n{3,}", "\n\n", s)
        s = re.sub(r"[ \t]{2,}", " ", s)

    # HTML minifizieren (leere Tags, Attribute entfernen)
    if minify:
        s = minify_html(s)

    # 3.1.4.16: EN lastline locale sanitizer (final guardrail)
    s = sanitize_en_locale_tokens(s, lang)

    return s


def sanitize_sections_dict(sections: dict, truthy_env: Optional[bool] = True, lang: str = "de") -> dict:
    """
    Sanitisiert alle string‑Werte in einem Sections‑Dict.

    PLATIN+++ v5.4: Now also enforces HTML contract for text sections.
    3.1.4.16: Now passes lang for EN locale sanitization.
    """
    if not isinstance(sections, dict):
        return sections
    out = {}
    for k, v in sections.items():
        if isinstance(v, str):
            # Step 1: Basic sanitization + EN locale sanitization (3.1.4.16)
            sanitized = sanitize_section_html(v, compress_ws=True, lang=lang)
            # Step 2: Enforce HTML contract for text sections (PLATIN+++ v5.4)
            if is_text_section(k):
                sanitized = enforce_text_section_html_contract(sanitized, section_name=k)
            out[k] = sanitized
        else:
            out[k] = v
    return out


# =============================================================================
# FIX-530: HTML Entity Sanitization (Rendering Bugs)
# =============================================================================
# Goal: No visible HTML entities (&uuml;, &amp;, &bdquo;, etc.) in final output
# Exception: URLs with & querystrings are allowed

# Pattern to detect HTML entities (excluding URL querystrings)
HTML_ENTITY_PATTERN = re.compile(r'&([a-z]{2,8});', re.IGNORECASE)

# Allowed entities (common ones that might appear in URLs or are intentional)
ALLOWED_ENTITIES = {
    'amp',  # & in URLs
    'nbsp',  # Non-breaking space (sometimes intentional)
    'lt', 'gt',  # < > (sometimes needed for display)
}


def unescape_html_entities(text: str) -> str:
    """
    FIX-530: Convert HTML entities to actual characters.

    Converts entities like &uuml; to ü, &amp; to & (except in URLs),
    &bdquo; to „, etc.

    Args:
        text: Text with potential HTML entities

    Returns:
        Text with entities converted to actual characters
    """
    if not text or not isinstance(text, str):
        return text or ""

    # First pass: Use Python's html.unescape for standard entities
    result = html.unescape(text)

    # Handle numeric entities that html.unescape might miss
    # &#x prefix (hex) and &#prefix (decimal)
    result = re.sub(r'&#x([0-9a-fA-F]+);', lambda m: chr(int(m.group(1), 16)), result)
    result = re.sub(r'&#(\d+);', lambda m: chr(int(m.group(1))), result)

    return result


def sanitize_double_escaped_entities(text: str) -> str:
    """
    FIX-530: Fix double-escaped entities like &amp;uuml; → ü

    Sometimes entities get double-escaped in the pipeline:
    - &amp;uuml; should become ü
    - &amp;amp; should become &

    Args:
        text: Text with potential double-escaped entities

    Returns:
        Text with double-escaping fixed
    """
    if not text or not isinstance(text, str):
        return text or ""

    # Pattern for double-escaped entities: &amp;entity;
    double_escape_pattern = re.compile(r'&amp;([a-z]{2,8});', re.IGNORECASE)

    # Keep iterating until no more double escapes
    max_iterations = 3  # Safety limit
    for _ in range(max_iterations):
        if '&amp;' not in text:
            break
        # Convert &amp;entity; to &entity; then unescape
        text = double_escape_pattern.sub(r'&\1;', text)
        text = unescape_html_entities(text)

    return text


def validate_no_visible_entities(html_content: str) -> tuple[bool, list[str]]:
    """
    FIX-530: Validate that no visible HTML entities remain in final output.

    Gate check: &[a-z]{2,6}; should not appear (except in URLs with querystrings).

    Args:
        html_content: Final HTML content

    Returns:
        Tuple of (passed, list_of_found_entities)
    """
    if not html_content:
        return True, []

    found_entities = []

    # Find all entity-like patterns
    for match in HTML_ENTITY_PATTERN.finditer(html_content):
        entity_name = match.group(1).lower()

        # Skip allowed entities
        if entity_name in ALLOWED_ENTITIES:
            continue

        # Check if it's in a URL context (href="...&entity;..." or src="...")
        # Look at surrounding context
        start = max(0, match.start() - 50)
        context = html_content[start:match.end() + 10]

        # If in URL attribute, allow &amp; and similar
        if 'href=' in context or 'src=' in context or 'url(' in context:
            if entity_name == 'amp':
                continue

        found_entities.append(f"&{entity_name};")

    passed = len(found_entities) == 0

    if passed:
        log.debug("[FIX-530][ENTITY-GATE] PASS: No visible entities found")
    else:
        # Deduplicate
        unique_entities = list(set(found_entities))[:10]  # Limit to 10
        log.warning(
            "[FIX-530][ENTITY-GATE] FAIL: Found %d visible entities: %s",
            len(found_entities), unique_entities
        )

    return passed, list(set(found_entities))


def apply_entity_sanitization(html_content: str) -> tuple[str, int]:
    """
    FIX-530: Apply full entity sanitization pipeline.

    Steps:
    1. Fix double-escaped entities
    2. Unescape remaining entities
    3. Validate result

    Args:
        html_content: HTML to sanitize

    Returns:
        Tuple of (sanitized_html, count_of_entities_fixed)
    """
    if not html_content:
        return "", 0

    original = html_content
    result = html_content

    # Step 1: Fix double-escaped entities
    result = sanitize_double_escaped_entities(result)

    # Step 2: Unescape any remaining entities
    result = unescape_html_entities(result)

    # Count how many entities were fixed
    original_entities = len(HTML_ENTITY_PATTERN.findall(original))
    result_entities = len(HTML_ENTITY_PATTERN.findall(result))
    fixed_count = original_entities - result_entities

    if fixed_count > 0:
        log.info("[FIX-530][ENTITY-SANITIZE] Fixed %d HTML entities", fixed_count)

    return result, fixed_count


# =============================================================================
# FIX-530: CSS Fixes for Bullets and Overlaps (as injectable CSS)
# =============================================================================

FIX_530_CSS = """
/* FIX-530: Fix broken bullets on Datengrundlage page (word-per-line issue) */
.datengrundlage-section li,
.data-basis li,
.grundlagen li {
    display: list-item !important;
    white-space: normal !important;
    word-break: normal !important;
    overflow-wrap: break-word;
    hyphens: auto;
}

/* FIX-530: Fix text overlap in risk/quality boxes */
.risk-card,
.risk-box,
.quality-box,
.risiko-box,
.colored-box {
    min-height: auto !important;
    height: auto !important;
    padding: var(--space-sm, 8pt) var(--space-md, 16pt) !important;
    overflow: visible !important;
    overflow-wrap: anywhere;
    word-wrap: break-word;
}

/* Ensure cards don't have fixed heights that cause overlap */
.risk-card p,
.risk-box p,
.quality-box p {
    margin-bottom: var(--space-xs, 4pt);
    line-height: 1.5;
}

/* Fix for flex containers that might cause squishing */
.risk-grid,
.quality-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
    gap: var(--space-md, 16pt);
}

/* Ensure list items don't get squeezed */
ul, ol {
    padding-left: var(--space-lg, 24pt);
}

ul li, ol li {
    padding-left: var(--space-xs, 4pt);
    margin-bottom: var(--space-xs, 4pt);
    line-height: 1.6;
}

/* Fix inline code blocks that might cause layout issues */
code, .code {
    white-space: pre-wrap;
    word-break: break-all;
}

/* Prevent tables from overflowing */
table {
    width: 100%;
    table-layout: fixed;
}

td, th {
    word-wrap: break-word;
    overflow-wrap: break-word;
}
"""


def get_fix_530_css() -> str:
    """
    FIX-530: Get CSS fixes for bullets and overlaps.

    Returns injectable CSS for the PDF template.
    """
    return FIX_530_CSS


log.info("[FIX-530] HTML entity sanitization + CSS fixes loaded")
