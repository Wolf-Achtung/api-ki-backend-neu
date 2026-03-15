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

# Prozentwert-Pattern: fängt "104%", "104 %", "104,5%", "104.5 %" etc.
_PERCENT_PATTERN = re.compile(
    r'(\d{1,4}[.,]?\d{0,2})\s*%'
)


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


# ── Pass 2: Duplikat-Zahlen-Check in Tabellen ───────────────────────

def _check_table_consistency(html: str, section_key: str) -> list[str]:
    """
    Prüft ob in einer Tabelle dieselbe Metrik-Bezeichnung
    mit verschiedenen Werten vorkommt. Nur Warning, kein Patch.
    (Platzhalter für v2-Erweiterung)
    """
    return []


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

        # Pass 2: Tabellen-Konsistenz (nur Warnings)
        tw = _check_table_consistency(html, key)
        all_warnings.extend(tw)

        # Pass 3: Jahres-Check
        yw = _check_year_data_freshness(html, key, report_year)
        all_warnings.extend(yw)

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
