import logging
import re
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)

VERSION = "1.1.0-GOLD-PLUS"

# ---------------------------------------------------------------------------
# Datenklassen
# ---------------------------------------------------------------------------


@dataclass
class ValidationError:
    code: str
    section: str
    severity: str  # "critical" oder "warning"
    message: str
    details: Optional[str] = None


# ---------------------------------------------------------------------------
# Konfiguration: Platzhalter, Templates, Size-Filter
# ---------------------------------------------------------------------------

# Platzhalter-Muster, die im finalen HTML NICHT auftauchen dürfen.
# Dazu gehören u.a.:
#   - Backend-Platzhalter: {TOOLS_AKTUELL}, {CONTEXT_QUICK_WINS}, ...
#   - Template-Platzhalter aus Prompts: {{score_gesamt}}, {{branch_typische_einheit}}, ...
#   - Typische [Platzhalter in eckigen Klammern] aus Beispiel-Strukturen.
PLACEHOLDER_PATTERNS: List[Tuple[str, str, str]] = [
    # {UPPERCASE_PLACEHOLDER}
    (
        r"\{[A-Z_]+\}",
        "PLACEHOLDER_NOT_REPLACED",
        "Placeholder nicht ersetzt: {placeholder}",
    ),
    # {{lowercase_placeholder}}
    (
        r"\{\{[a-z_]+\}\}",
        "PLACEHOLDER_NOT_REPLACED",
        "Template-Variable nicht ersetzt: {placeholder}",
    ),
    # Spezifische Muster aus Roadmap-/Pilot-Prompts
    (
        r"\[Deliverable \d+\]",
        "PLACEHOLDER_NOT_REPLACED",
        "Deliverable-Platzhalter nicht ersetzt: {placeholder}",
    ),
    (
        r"\[KPI [0-9]+\]",
        "PLACEHOLDER_NOT_REPLACED",
        "KPI-Platzhalter nicht ersetzt: {placeholder}",
    ),
    (
        r"\[Rollen\]",
        "PLACEHOLDER_NOT_REPLACED",
        "Rollen-Platzhalter nicht ersetzt: {placeholder}",
    ),
    (
        r"\[Name\]",
        "PLACEHOLDER_NOT_REPLACED",
        "Namens-Platzhalter nicht ersetzt: {placeholder}",
    ),
    (
        r"\[Feature/System [0-9]+\]",
        "PLACEHOLDER_NOT_REPLACED",
        "Feature-/System-Platzhalter nicht ersetzt: {placeholder}",
    ),
    (
        r"\[Kompletter Meilenstein[^\]]*\]",
        "PLACEHOLDER_NOT_REPLACED",
        "Meilenstein-Platzhalter nicht ersetzt: {placeholder}",
    ),
    (
        r"\[Konkrete Zahlen\]",
        "PLACEHOLDER_NOT_REPLACED",
        "Zahlen-Platzhalter nicht ersetzt: {placeholder}",
    ),
    (
        r"\[€\]",
        "PLACEHOLDER_NOT_REPLACED",
        "Euro-Platzhalter nicht ersetzt: {placeholder}",
    ),
]

# Typische Template-Phrasen, die in finalen Texten nicht stehen sollen
TEMPLATE_PHRASES: List[str] = [
    "Hier kurz erklären, warum",
    "Beispielhafte Struktur",
    "Nutze eine Section mit klaren Unterüberschriften",
    "Platzhaltertext",
    "Lorem ipsum",
]

# Mindestlängen pro Section (nach HTML-Sanitizing)
MIN_SECTION_LENGTH: Dict[str, int] = {
    "EXEC_SUMMARY_HTML": 400,
    "BUSINESS_CASE_HTML": 400,
    "ROADMAP_90D_HTML": 400,
    "ROADMAP_12M_HTML": 400,
    "PILOT_PLAN_HTML": 400,
    "QUICK_WINS_HTML_LEFT": 400,
    "QUICK_WINS_HTML_RIGHT": 400,
}

# Begriffe, die für bestimmte Größenklassen unpassend sind
SIZE_FORBIDDEN_TERMS: Dict[str, List[str]] = {
    "solo": [
        "Abteilung",
        "Abteilungen",
        "Steering Committee",
        "PMO",
        "Change Manager",
        "Change-Agents",
        "Town Hall",
        "Belegschaft",
        "Mitarbeiter:innen",
        "MitarbeiterInnen",
        "Belegschaft",
    ],
    "team": [
        "PMO-Team",
        "Projektportfolioboard",
        "Konzernzentrale",
        "Vorstandssitzung",
        "Betriebsrat",
    ],
}

# Begriffe, die im Text darauf hindeuten, dass eigentlich ein Solo-Szenario
# gemeint ist – in Team/KMU-Reports unerwünscht.
SOLO_HINT_TERMS: List[str] = [
    "als Solo-Selbstständige",
    "als Solo-Selbständiger",
    "als Freelancer:in",
    "als Einzelunternehmer:in",
]


# ---------------------------------------------------------------------------
# Validator-Klasse
# ---------------------------------------------------------------------------


class ReportValidator:
    """
    Validiert generierte HTML-Sektionen auf Platzhalter, Minimalumfang,
    unerwünschte Template-Phrasen und größen-inkonsistente Sprache.
    """

    def __init__(self, sections: Dict[str, Any], meta: Dict[str, Any]):
        """
        :param sections: Dict mit allen Sections, z.B. {"EXEC_SUMMARY_HTML": "<section>...</section>", ...}
        :param meta:     Metadaten wie {"company_size": "solo", "briefing_id": 123, ...}
        """
        self.sections = sections
        self.meta = meta or {}
        self.company_size: Optional[str] = self.meta.get("company_size")
        self.errors: List[ValidationError] = []

    # ------------------------------------------------------------------ #
    # Öffentliche API
    # ------------------------------------------------------------------ #

    def validate(self) -> Tuple[bool, List[ValidationError]]:
        """Führt alle Checks aus und gibt (is_valid, errors) zurück."""
        logger.info("Running ReportValidator %s", VERSION)

        self._check_placeholders()
        self._check_empty_sections()
        self._check_template_phrases()
        self._check_section_lengths()
        self._check_size_specific_content()
        self._check_duplicate_context_blocks()
        self._check_roadmap_quality()

        critical = [e for e in self.errors if e.severity == "critical"]

        if critical:
            logger.info("🔴 CRITICAL ERRORS: %d", len(critical))
        else:
            logger.info("✅ Keine kritischen Fehler im Report-Validator gefunden.")

        return (len(critical) == 0), self.errors

    # ------------------------------------------------------------------ #
    # Einzelne Checks
    # ------------------------------------------------------------------ #

    def _iter_html_sections(self) -> List[Tuple[str, str]]:
        """Hilfsfunktion: liefere nur die Einträge, die *_HTML heißen."""
        results: List[Tuple[str, str]] = []
        for key, value in self.sections.items():
            if not key.endswith("_HTML"):
                continue
            if not isinstance(value, str):
                continue
            results.append((key, value))
        return results

    def _add_error(
        self,
        code: str,
        section: str,
        message: str,
        severity: str = "critical",
        details: Optional[str] = None,
    ) -> None:
        self.errors.append(
            ValidationError(
                code=code, section=section, severity=severity, message=message, details=details
            )
        )

    def _check_placeholders(self) -> None:
        """Sucht nach Platzhalter-Mustern (geschweifte oder eckige Klammern)."""
        for section, html in self._iter_html_sections():
            for pattern, code, msg in PLACEHOLDER_PATTERNS:
                for match in re.finditer(pattern, html):
                    placeholder = match.group(0)
                    self._add_error(
                        code=code,
                        section=section,
                        message=msg.format(placeholder=placeholder),
                        severity="critical",
                        details=f"Section={section}, match={placeholder}",
                    )

    def _check_empty_sections(self) -> None:
        """Leere oder extrem knappe Sections markieren."""
        for section, html in self._iter_html_sections():
            content = re.sub(r"\s+", " ", html).strip()
            if not content:
                self._add_error(
                    code="EMPTY_SECTION",
                    section=section,
                    message="Section ist komplett leer.",
                    severity="critical",
                )

    def _check_template_phrases(self) -> None:
        """Typische Template-Phrasen aus Prompts finden."""
        lowered_phrases = [p.lower() for p in TEMPLATE_PHRASES]
        for section, html in self._iter_html_sections():
            text = html.lower()
            for phrase in lowered_phrases:
                if phrase in text:
                    self._add_error(
                        code="TEMPLATE_PHRASE_LEFT",
                        section=section,
                        message="Template-/Beispieltext nicht entfernt.",
                        severity="warning",
                        details=f"Gefundene Phrase: {phrase}",
                    )

    def _check_section_lengths(self) -> None:
        """Sections mit deutlich zu wenig Inhalt markieren."""
        for section, html in self._iter_html_sections():
            min_len = MIN_SECTION_LENGTH.get(section)
            if not min_len:
                continue
            # HTML-Tags entfernen
            text = re.sub(r"<[^>]+>", " ", html)
            text = re.sub(r"\s+", " ", text).strip()
            if len(text) < min_len:
                self._add_error(
                    code="SECTION_TOO_SHORT",
                    section=section,
                    message=f"Section ist sehr kurz ({len(text)} Zeichen, Minimum {min_len}).",
                    severity="warning",
                )

    def _check_size_specific_content(self) -> None:
        """Prüft, ob die Sprache zur Unternehmensgröße passt."""
        size = (self.company_size or "").lower()
        if not size:
            return

        forbidden = SIZE_FORBIDDEN_TERMS.get(size, [])
        if not forbidden and size != "solo":
            return

        for section, html in self._iter_html_sections():
            text = html.lower()

            # Verbotene Begriffe für die jeweilige Größe
            for term in forbidden:
                if term.lower() in text:
                    self._add_error(
                        code="SIZE_INAPPROPRIATE_CONTENT",
                        section=section,
                        message=f"Formulierung passt nicht zu company_size='{size}'.",
                        severity="warning",
                        details=f"Begriff: {term}",
                    )

            # Solo-Hinweise in Nicht-Solo-Reports
            if size in {"team", "kmu"}:
                for solo_term in SOLO_HINT_TERMS:
                    if solo_term.lower() in text:
                        self._add_error(
                            code="SOLO_HINT_IN_NON_SOLO",
                            section=section,
                            message="Solo-spezifische Formulierung in Team/KMU-Report.",
                            severity="warning",
                            details=f"Begriff: {solo_term}",
                        )

    def _check_duplicate_context_blocks(self) -> None:
        """
        Grobe Heuristik: Wenn identische längere Textblöcke mehrfach in
        verschiedenen Sections auftauchen, kann das ein Hinweis auf
        unreflektiertes Copy-Paste von Kontext sein.
        """
        texts = {section: re.sub(r"\s+", " ", html).strip() for section, html in self._iter_html_sections()}

        # sehr grobe Duplikatsprüfung: identische Strings über 800 Zeichen
        seen: Dict[str, str] = {}
        for section, text in texts.items():
            if len(text) < 800:
                continue
            if text in seen:
                other = seen[text]
                self._add_error(
                    code="DUPLICATE_CONTEXT_BLOCK",
                    section=section,
                    message="Großer Textblock identisch in zwei Sections.",
                    severity="warning",
                    details=f"Doppelt in {section} und {other}",
                )
            else:
                seen[text] = section

    def _check_roadmap_quality(self) -> None:
        """
        Spezifische Heuristik für Roadmaps:
        - Warnen, wenn keine 'Woche X-Y: ...' Struktur erkennbar ist.
        """
        for key in ("ROADMAP_90D_HTML", "ROADMAP_12M_HTML"):
            html = self.sections.get(key)
            if not html or not isinstance(html, str):
                continue

            # Sehr einfache Heuristik: 'Woche 1-2', 'Woche 3-4', ...
            weeks = re.findall(r"Woche\s+\d+-\d+", html)
            if len(weeks) < 3:
                self._add_error(
                    code="ROADMAP_TOO_VAGUE",
                    section=key,
                    message="Roadmap hat keine klaren Wochen-/Deliverable-Strukturen.",
                    severity="warning",
                    details="Zu wenige 'Woche X-Y' Muster gefunden.",
                )
