"""
Strategy Fact Sanitizer (FIX-SF1)
Fängt LLM-Halluzinationen in Strategy-Sektionen ab.
Läuft NACH der LLM-Generierung, VOR dem Renderer.
"""

import re
import logging

log = logging.getLogger(__name__)

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


# ── Hauptfunktion ────────────────────────────────────────────────────

def sanitize_strategy_sections(
    sections: dict,
    research_context: dict = None,
    report_year: int = 2026
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

    strategy_keys = [k for k in sections if isinstance(sections[k], str) and len(sections[k]) > 100]

    for key in strategy_keys:
        html = sections[key]

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
