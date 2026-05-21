# -*- coding: utf-8 -*-
"""
Prompt Enhancer - Injects context into existing prompts
Optimized for ki-sicherheit.jetzt backend

This service works WITH the existing prompt_loader.py system.
It loads prompts via prompt_loader, injects context, and returns enhanced prompts.

Version: 2.9.0-PLATIN++ (Sprint G6 - Final Polish & Cross-Section Redundancy)

SPRINT N CHANGES:
- Extended SOLO_FORBIDDEN_TERMS list to prevent team/KMU terminology leaks
- Added SOLO_REPLACEMENTS for automatic term substitution
- Updated token budgets for length stabilization

SPRINT G2.4 CHANGES:
- Added BRANCH_CORE_LABEL, OFFERING_LABEL, REGULATORY_LABEL generation
- Implemented redundancy detection and replacement system
- Short labels replace long-form descriptions after first occurrence
"""
from __future__ import annotations

import logging
import re
from dataclasses import dataclass
from typing import Any, Dict, List, Set, TypedDict, Optional

from services.prompt_builder import PromptBuilder

# G19.1-MAP: Import branch mapping
try:
    from services.branch_mapping import map_frontend_branch_to_engine
except ImportError:
    def map_frontend_branch_to_engine(raw_value: str) -> str:
        """Fallback if branch_mapping not available."""
        return raw_value.lower().strip() if raw_value else "beratung"

# G9.4: Import centralized min-length configuration
try:
    from services.config_validation import get_min_words as get_central_min_words
except ImportError:
    get_central_min_words = None

log = logging.getLogger(__name__)


# =============================================================================
# FIX-QW-PROMPT-STABILIZE: Deterministic Prompt Sanitizer
# =============================================================================

# Regex patterns for sanitize_for_prompt
_CODE_FENCE_RE = re.compile(r'`{3,}[a-zA-Z]*\n?|`{3,}')
_DIGIT_FRAGMENT_RE = re.compile(
    r'\b\d+[\.,]?\d*\s*(?:€|EUR|Euro|%|h/(?:Monat|Woche|Tag)|Stunden?|Minuten?|Tage?|Monate?|Jahre?|Wochen?)(?:\b|(?=\s|$|[.,;:!?]))',
    re.IGNORECASE
)
_BARE_DIGITS_RE = re.compile(r'\b\d+(?:[\.,]\d+)?\b')
_CORPORATE_WORDING_REPLACEMENTS: List[tuple] = [
    (re.compile(r'\bRollout\b', re.IGNORECASE), 'Einführung'),
    (re.compile(r'\bSkalierung\b', re.IGNORECASE), 'Ausbau'),
    (re.compile(r'\bModul\b', re.IGNORECASE), 'Baustein'),
    (re.compile(r'\bStack\b', re.IGNORECASE), 'Tool-Set'),
    (re.compile(r'\b1000\+\b'), ''),
    (re.compile(r'\bca\.\s*', re.IGNORECASE), ''),
    (re.compile(r'\betwa\s+', re.IGNORECASE), ''),
    (re.compile(r'\btypischerweise\s*', re.IGNORECASE), ''),
    (re.compile(r'\bangenommen\s*', re.IGNORECASE), ''),
    (re.compile(r'\bz\.\s*B\.', re.IGNORECASE), 'optional'),
]


def sanitize_for_prompt(text: str) -> str:
    """
    FIX-QW-PROMPT-STABILIZE CHANGE 2: Deterministic prompt sanitizer.

    Removes/neutralizes content that could cause the LLM to echo
    numbers, time ranges, or corporate jargon in its JSON output.

    Specifically:
    - Removes backticks/code-fence markers
    - Removes digits and time/price fragments
    - Replaces corporate wording with simple terms

    Args:
        text: Raw user input text (e.g. zeitersparnis_prioritaet)

    Returns:
        Sanitized text safe for prompt injection (no digits, no jargon)
    """
    if not text or not text.strip():
        return ""

    result = text.strip()

    # Step 1: Remove code fences
    result = _CODE_FENCE_RE.sub('', result)

    # Step 2: Remove digit+unit fragments (e.g. "10 Stunden", "500€", "6-10 h/Monat")
    result = _DIGIT_FRAGMENT_RE.sub('', result)

    # Step 3: Remove remaining bare digits
    result = _BARE_DIGITS_RE.sub('', result)

    # Step 4: Corporate wording replacements
    for pattern, replacement in _CORPORATE_WORDING_REPLACEMENTS:
        result = pattern.sub(replacement, result)

    # Step 5: Clean up whitespace artifacts
    result = re.sub(r'\s{2,}', ' ', result)
    result = re.sub(r'\s+([.,;:!?])', r'\1', result)
    result = result.strip()

    return result


# =============================================================================
# SPRINT G2.4: KURZLABEL-SYSTEM für Redundanzabbau
# =============================================================================

# Branch → short label mappings (max 8-12 words, no subclauses)
BRANCH_CORE_LABELS_DE: Dict[str, str] = {
    "beratung": "KI-gestützte Prozess- & Strategieberatung",
    "consulting": "KI-gestützte Prozess- & Strategieberatung",
    "it_software": "KI-gestützte Softwareentwicklung & IT-Dienstleistungen",
    "finanzen": "KI-gestützte Analyse & Reporting für Finanzdienstleister",
    "versicherung": "KI-gestützte Risikoanalyse & Schadenbearbeitung",
    "handel": "KI-gestützter E-Commerce & Handelsoptimierung",
    "industrie": "KI-gestützte Fertigung & Prozessautomatisierung",
    "gesundheit": "KI-gestützte Diagnostik & Patientenversorgung",
    "marketing": "KI-gestützte Content-Erstellung & Kampagnenoptimierung",
    "recht": "KI-gestützte Dokumentenanalyse & Rechtsrecherche",
    "bildung": "KI-gestützte Lernplattformen & Bildungsservices",
    "immobilien": "KI-gestützte Immobilienbewertung & -verwaltung",
    "logistik": "KI-gestützte Lieferketten- & Routenoptimierung",
    "energie": "KI-gestütztes Energiemanagement & Netzoptimierung",
    "medien": "KI-gestützte Content-Produktion & Medienanalyse",
    "tourismus": "KI-gestützte Buchungssysteme & Reiseplanung",
    "handwerk": "KI-gestützte Auftragsplanung & Ressourcensteuerung",
    "gastronomie": "KI-gestützte Bestellsysteme & Küchenoptimierung",
    "landwirtschaft": "KI-gestützte Ertragsoptimierung & Precision Farming",
}

BRANCH_CORE_LABELS_EN: Dict[str, str] = {
    "beratung": "AI-driven business & process consulting",
    "consulting": "AI-driven business & process consulting",
    "it_software": "AI-powered software development & IT services",
    "finanzen": "AI-driven analytics & reporting for financial services",
    "versicherung": "AI-powered risk analysis & claims processing",
    "handel": "AI-driven e-commerce & retail optimization",
    "industrie": "AI-powered manufacturing & process automation",
    "gesundheit": "AI-driven diagnostics & patient care",
    "marketing": "AI-powered content creation & campaign optimization",
    "recht": "AI-driven document analysis & legal research",
    "bildung": "AI-powered learning platforms & education services",
    "immobilien": "AI-driven property valuation & management",
    "logistik": "AI-powered supply chain & route optimization",
    "energie": "AI-driven energy management & grid optimization",
    "medien": "AI-powered content production & media analytics",
    "tourismus": "AI-driven booking systems & travel planning",
    "handwerk": "AI-powered scheduling & resource management",
    "gastronomie": "AI-driven ordering systems & kitchen optimization",
    "landwirtschaft": "AI-powered yield optimization & precision farming",
}

# Offering labels (max 6-10 words)
OFFERING_LABELS_DE: Dict[str, str] = {
    "beratung": "KI-Readiness-Analysen & Workflow-Automatisierung",
    "consulting": "KI-Readiness-Analysen & Workflow-Automatisierung",
    "it_software": "Softwareentwicklung & KI-Integration",
    "finanzen": "Finanzanalyse & automatisiertes Reporting",
    "versicherung": "Schadenbearbeitung & Risikobewertung",
    "handel": "E-Commerce-Optimierung & Bestandsmanagement",
    "industrie": "Produktionssteuerung & Qualitätssicherung",
    "gesundheit": "Diagnostik-Unterstützung & Patientendokumentation",
    "marketing": "Content-Generierung & Performance-Analyse",
    "recht": "Vertragsanalyse & Due-Diligence-Automatisierung",
    "bildung": "Lernmanagement & personalisierte Bildung",
    "immobilien": "Objektbewertung & Mieterverwaltung",
    "logistik": "Routenplanung & Lageroptimierung",
    "energie": "Verbrauchsanalyse & Lastprognose",
    "medien": "Content-Produktion & Reichweitenanalyse",
    "tourismus": "Buchungsmanagement & Kundenerlebnis",
    "handwerk": "Auftragsplanung & Materialwirtschaft",
    "gastronomie": "Bestellmanagement & Küchenplanung",
    "landwirtschaft": "Ertragsplanung & Ressourcenmanagement",
}

OFFERING_LABELS_EN: Dict[str, str] = {
    "beratung": "AI readiness & workflow automation",
    "consulting": "AI readiness & workflow automation",
    "it_software": "Software development & AI integration",
    "finanzen": "Financial analysis & automated reporting",
    "versicherung": "Claims processing & risk assessment",
    "handel": "E-commerce optimization & inventory management",
    "industrie": "Production control & quality assurance",
    "gesundheit": "Diagnostic support & patient documentation",
    "marketing": "Content generation & performance analytics",
    "recht": "Contract analysis & due diligence automation",
    "bildung": "Learning management & personalized education",
    "immobilien": "Property valuation & tenant management",
    "logistik": "Route planning & warehouse optimization",
    "energie": "Consumption analysis & load forecasting",
    "medien": "Content production & reach analytics",
    "tourismus": "Booking management & customer experience",
    "handwerk": "Job scheduling & material management",
    "gastronomie": "Order management & kitchen planning",
    "landwirtschaft": "Yield planning & resource management",
}

# Regulatory labels (only for regulated industries)
REGULATED_BRANCHES = {"finanzen", "versicherung", "gesundheit", "recht"}

REGULATORY_LABELS_DE: Dict[str, str] = {
    "finanzen": "Ihr Compliance-Rahmen (BAIT, VAIT, MaRisk, DSGVO)",
    "versicherung": "Ihr Compliance-Rahmen (VAIT, Solvency II, DSGVO)",
    "gesundheit": "Ihr Compliance-Rahmen (MDR, DSGVO, Patientendatenschutz)",
    "recht": "Ihr Compliance-Rahmen (BRAO, DSGVO, Berufsgeheimnis)",
}

REGULATORY_LABELS_EN: Dict[str, str] = {
    "finanzen": "Your compliance framework (BAIT, VAIT, MaRisk, GDPR)",
    "versicherung": "Your compliance framework (VAIT, Solvency II, GDPR)",
    "gesundheit": "Your compliance framework (MDR, GDPR, patient data protection)",
    "recht": "Your compliance framework (BRAO, GDPR, professional confidentiality)",
}

# SPRINT G4.2: BRANCH_CONTEXT_LABEL (4-6 words, pure categorization)
BRANCH_CONTEXT_LABELS_DE: Dict[str, str] = {
    "beratung": "KI-Consulting",
    "consulting": "KI-Consulting",
    "it_software": "IT & Software",
    "finanzen": "Finance Advisory",
    "versicherung": "Versicherungsberatung",
    "handel": "Handel & E-Commerce",
    "industrie": "Industrie & Fertigung",
    "gesundheit": "Healthcare Services",
    "marketing": "Marketing & Creative",
    "recht": "Legal Services",
    "bildung": "Education & Training",
    "immobilien": "Real Estate",
    "logistik": "Logistics & Supply Chain",
    "energie": "Energy & Utilities",
    "medien": "Media & Publishing",
    "tourismus": "Tourism & Hospitality",
    "handwerk": "Handwerk & Services",
    "gastronomie": "Gastro & Food",
    "landwirtschaft": "AgriTech",
}

BRANCH_CONTEXT_LABELS_EN: Dict[str, str] = {
    "beratung": "AI Consulting",
    "consulting": "AI Consulting",
    "it_software": "IT & Software",
    "finanzen": "Finance Advisory",
    "versicherung": "Insurance Services",
    "handel": "Retail & E-Commerce",
    "industrie": "Manufacturing",
    "gesundheit": "Healthcare",
    "marketing": "Marketing & Creative",
    "recht": "Legal Services",
    "bildung": "Education",
    "immobilien": "Real Estate",
    "logistik": "Logistics",
    "energie": "Energy & Utilities",
    "medien": "Media & Publishing",
    "tourismus": "Tourism & Hospitality",
    "handwerk": "Skilled Trades",
    "gastronomie": "Food & Beverage",
    "landwirtschaft": "AgriTech",
}

# =============================================================================
# SPRINT G17.S: BRANCH_SHORT_LABEL (3-5 words, minimal redundancy)
# =============================================================================
# Used to replace overly long branch descriptions after first occurrence

BRANCH_SHORT_LABELS_DE: Dict[str, str] = {
    # Format: size_branch -> "Ihr [kurze Beschreibung]"
    "solo_beratung": "Ihr KI-Readiness-Beratungsangebot",
    "solo_consulting": "Ihr KI-Readiness-Beratungsangebot",
    "solo_it_software": "Ihre IT-Dienstleistung",
    "solo_finanzen": "Ihre Finanzberatung",
    "solo_versicherung": "Ihre Versicherungsberatung",
    "solo_handel": "Ihr Handelsgeschäft",
    "solo_industrie": "Ihre Fertigungsdienstleistung",
    "solo_gesundheit": "Ihre Gesundheitsdienstleistung",
    "solo_marketing": "Ihre Marketing-Dienstleistung",
    "solo_recht": "Ihre Rechtsberatung",
    "solo_bildung": "Ihre Bildungsdienstleistung",
    "solo_immobilien": "Ihre Immobiliendienstleistung",
    "solo_logistik": "Ihre Logistikdienstleistung",
    "solo_energie": "Ihre Energiedienstleistung",
    "solo_medien": "Ihre Mediendienstleistung",
    "solo_tourismus": "Ihre Tourismusdienstleistung",
    "solo_handwerk": "Ihr Handwerksbetrieb",
    "solo_gastronomie": "Ihr Gastronomiebetrieb",
    "solo_landwirtschaft": "Ihr Agrarbetrieb",
    # Team variants
    "team_beratung": "Ihr KI-Beratungsteam",
    "team_consulting": "Ihr KI-Beratungsteam",
    "team_it_software": "Ihr IT-Team",
    "team_finanzen": "Ihr daten- & risikoorientiertes Finanzteam",
    "team_versicherung": "Ihr Versicherungsteam",
    "team_handel": "Ihr Handelsteam",
    "team_industrie": "Ihr Produktionsteam",
    "team_gesundheit": "Ihr Gesundheitsteam",
    "team_marketing": "Ihr Marketingteam",
    "team_recht": "Ihr Rechtsteam",
    "team_bildung": "Ihr Bildungsteam",
    "team_immobilien": "Ihr Immobilienteam",
    "team_logistik": "Ihr Logistikteam",
    "team_energie": "Ihr Energieteam",
    "team_medien": "Ihr Medienteam",
    "team_tourismus": "Ihr Tourismusteam",
    "team_handwerk": "Ihr Handwerksteam",
    "team_gastronomie": "Ihr Gastro-Team",
    "team_landwirtschaft": "Ihr Agrarteam",
    # KMU variants
    "kmu_beratung": "Ihr europäisches Business Consulting-Profil",
    "kmu_consulting": "Ihr europäisches Business Consulting-Profil",
    "kmu_it_software": "Ihre IT-Organisation",
    "kmu_finanzen": "Ihre Finanzorganisation",
    "kmu_versicherung": "Ihre Versicherungsorganisation",
    "kmu_handel": "Ihre Handelsorganisation",
    "kmu_industrie": "Ihr Produktionsunternehmen",
    "kmu_gesundheit": "Ihre Gesundheitsorganisation",
    "kmu_marketing": "Ihre Marketingorganisation",
    "kmu_recht": "Ihre Rechtsorganisation",
    "kmu_bildung": "Ihre Bildungsorganisation",
    "kmu_immobilien": "Ihre Immobilienorganisation",
    "kmu_logistik": "Ihre Logistikorganisation",
    "kmu_energie": "Ihre Energieorganisation",
    "kmu_medien": "Ihre Medienorganisation",
    "kmu_tourismus": "Ihre Tourismusorganisation",
    "kmu_handwerk": "Ihr Handwerksunternehmen",
    "kmu_gastronomie": "Ihr Gastrounternehmen",
    "kmu_landwirtschaft": "Ihr Agrarunternehmen",
}

BRANCH_SHORT_LABELS_EN: Dict[str, str] = {
    # Solo variants
    "solo_beratung": "your AI readiness consulting",
    "solo_consulting": "your AI readiness consulting",
    "solo_it_software": "your IT services",
    "solo_finanzen": "your financial advisory",
    "solo_versicherung": "your insurance advisory",
    "solo_handel": "your retail business",
    "solo_industrie": "your manufacturing services",
    "solo_gesundheit": "your healthcare services",
    "solo_marketing": "your marketing services",
    "solo_recht": "your legal services",
    "solo_bildung": "your education services",
    "solo_immobilien": "your real estate services",
    "solo_logistik": "your logistics services",
    "solo_energie": "your energy services",
    "solo_medien": "your media services",
    "solo_tourismus": "your tourism services",
    "solo_handwerk": "your skilled trade",
    "solo_gastronomie": "your food service",
    "solo_landwirtschaft": "your agricultural business",
    # Team variants
    "team_beratung": "your AI consulting team",
    "team_consulting": "your AI consulting team",
    "team_it_software": "your IT team",
    "team_finanzen": "your data-driven finance team",
    "team_versicherung": "your insurance team",
    "team_handel": "your retail team",
    "team_industrie": "your production team",
    "team_gesundheit": "your healthcare team",
    "team_marketing": "your marketing team",
    "team_recht": "your legal team",
    "team_bildung": "your education team",
    "team_immobilien": "your real estate team",
    "team_logistik": "your logistics team",
    "team_energie": "your energy team",
    "team_medien": "your media team",
    "team_tourismus": "your tourism team",
    "team_handwerk": "your skilled trades team",
    "team_gastronomie": "your food & beverage team",
    "team_landwirtschaft": "your agricultural team",
    # KMU variants
    "kmu_beratung": "your European business consulting profile",
    "kmu_consulting": "your European business consulting profile",
    "kmu_it_software": "your IT organization",
    "kmu_finanzen": "your financial organization",
    "kmu_versicherung": "your insurance organization",
    "kmu_handel": "your retail organization",
    "kmu_industrie": "your manufacturing company",
    "kmu_gesundheit": "your healthcare organization",
    "kmu_marketing": "your marketing organization",
    "kmu_recht": "your legal organization",
    "kmu_bildung": "your education organization",
    "kmu_immobilien": "your real estate organization",
    "kmu_logistik": "your logistics organization",
    "kmu_energie": "your energy organization",
    "kmu_medien": "your media organization",
    "kmu_tourismus": "your tourism organization",
    "kmu_handwerk": "your skilled trades company",
    "kmu_gastronomie": "your food & beverage company",
    "kmu_landwirtschaft": "your agricultural company",
}


def generate_short_labels(briefing_data: Dict[str, Any], lang: str = "de") -> Dict[str, str]:
    """
    Sprint G2.4/G4.2/G17.S: Generate short labels for a profile.

    Args:
        briefing_data: Briefing data with branche, hauptleistung, company_size, etc.
        lang: Language code ('de' or 'en')

    Returns:
        Dict with BRANCH_CORE_LABEL, OFFERING_LABEL, REGULATORY_LABEL, BRANCH_CONTEXT_LABEL, BRANCH_SHORT_LABEL
    """
    # G19.1-MAP: Map frontend branch to engine key
    raw_branch = briefing_data.get("branche", "") or briefing_data.get("branch", "") or ""
    branche = map_frontend_branch_to_engine(raw_branch)

    # SPRINT G17.S: Get company size for BRANCH_SHORT_LABEL
    company_size = briefing_data.get("company_size", "").lower().strip()
    if not company_size:
        # Try to infer from unternehmensgroesse
        ug = briefing_data.get("unternehmensgroesse", "").lower()
        try:
            from services.company_size_normalizer import get_segment
            company_size = get_segment(ug)
        except Exception:
            if "solo" in ug or "1 " in ug or "freiberuf" in ug:
                company_size = "solo"
            elif "2-10" in ug or "klein" in ug or "team" in ug:
                company_size = "team"
            else:
                company_size = "kmu"

    # Select language-specific mappings
    if lang == "en":
        branch_labels = BRANCH_CORE_LABELS_EN
        offering_labels = OFFERING_LABELS_EN
        regulatory_labels = REGULATORY_LABELS_EN
        context_labels = BRANCH_CONTEXT_LABELS_EN
        short_labels = BRANCH_SHORT_LABELS_EN
    else:
        branch_labels = BRANCH_CORE_LABELS_DE
        offering_labels = OFFERING_LABELS_DE
        regulatory_labels = REGULATORY_LABELS_DE
        context_labels = BRANCH_CONTEXT_LABELS_DE
        short_labels = BRANCH_SHORT_LABELS_DE

    # Get labels with fallbacks - TEIL 3.1.1: Language-aware fallbacks
    if lang == "en":
        default_branch = "AI Consulting"
        default_offering = "AI Solutions"
        default_short = "Your Company"
    else:
        default_branch = "KI-Beratung"
        default_offering = "KI-Lösungen"
        default_short = "Ihr Unternehmen"

    branch_core = branch_labels.get(branche, branch_labels.get("beratung", default_branch))
    offering = offering_labels.get(branche, offering_labels.get("beratung", default_offering))
    # SPRINT G4.2: Short context label (4-6 words)
    branch_context = context_labels.get(branche, context_labels.get("beratung", "Consulting"))

    # SPRINT G17.S: Size-aware short label (3-5 words)
    short_key = f"{company_size}_{branche}"
    branch_short = short_labels.get(short_key, short_labels.get(f"{company_size}_beratung", default_short))

    # Regulatory label only for regulated industries
    regulatory = ""
    if branche in REGULATED_BRANCHES:
        regulatory = regulatory_labels.get(branche, "")

    return {
        "BRANCH_CORE_LABEL": branch_core,
        "OFFERING_LABEL": offering,
        "REGULATORY_LABEL": regulatory,
        "BRANCH_CONTEXT_LABEL": branch_context,  # SPRINT G4.2
        "BRANCH_SHORT_LABEL": branch_short,  # SPRINT G17.S
    }


# =============================================================================
# SPRINT G2.4: REDUNDANZ-ERKENNUNG & ERSETZUNG
# =============================================================================

class RedundancyTracker:
    """
    Tracks long sentences that have already appeared in the report.
    Used to replace repeated descriptions with short labels.
    """

    def __init__(self) -> None:
        self.seen_long_sentences: Set[str] = set()
        self.first_occurrence_section: Dict[str, str] = {}

    def reset(self) -> None:
        """Reset tracker for new report generation."""
        self.seen_long_sentences.clear()
        self.first_occurrence_section.clear()

    def normalize_sentence(self, sentence: str) -> str:
        """Normalize a sentence for comparison."""
        return re.sub(r'\s+', ' ', sentence.lower().strip())

    def is_redundant(self, sentence: str, min_words: int = 12) -> bool:
        """Check if a sentence is redundant (already seen)."""
        words = sentence.split()
        if len(words) < min_words:
            return False
        normalized = self.normalize_sentence(sentence)
        return normalized in self.seen_long_sentences

    def mark_seen(self, sentence: str, section_name: str, min_words: int = 12) -> None:
        """Mark a sentence as seen."""
        words = sentence.split()
        if len(words) >= min_words:
            normalized = self.normalize_sentence(sentence)
            if normalized not in self.seen_long_sentences:
                self.seen_long_sentences.add(normalized)
                self.first_occurrence_section[normalized] = section_name


# Global redundancy tracker (reset per report generation)
_redundancy_tracker = RedundancyTracker()


def get_redundancy_tracker() -> RedundancyTracker:
    """Get the global redundancy tracker."""
    return _redundancy_tracker


def reset_redundancy_tracker() -> None:
    """Reset redundancy tracker for new report."""
    _redundancy_tracker.reset()
    log.debug("🔄 Redundancy tracker reset")


def apply_redundancy_filter(text: str, section_name: str, short_labels: Dict[str, str]) -> str:
    """
    Sprint G2.4: Replace redundant long sentences with short labels.

    Args:
        text: Text to filter
        section_name: Current section name
        short_labels: Dict with BRANCH_CORE_LABEL, OFFERING_LABEL, etc.

    Returns:
        Filtered text with redundancies replaced
    """
    if not text or not short_labels:
        return text

    tracker = get_redundancy_tracker()
    result = text
    replacements_made = 0

    # Patterns for long branch/offering descriptions (40-400 chars)
    # These patterns match typical long-form descriptions
    long_desc_patterns = [
        # German patterns
        r'((?:Beratung|Consulting|Dienstleistung)[^.,]{40,300}(?:Prozess|Strategie|KI|AI|Compliance|Transformation))',
        r'((?:Business|Digital)[^.,]{40,300}(?:consulting|transformation|services))',
        # English patterns
        r'((?:consulting|advisory)[^.,]{40,300}(?:process|strategy|AI|compliance|transformation))',
    ]

    branch_label = short_labels.get("BRANCH_CORE_LABEL", "")
    offering_label = short_labels.get("OFFERING_LABEL", "")
    replacement = f"({branch_label})"
    if offering_label:
        replacement = f"({branch_label}, {offering_label})"

    for pattern in long_desc_patterns:
        matches = re.finditer(pattern, result, re.IGNORECASE)
        for match in matches:
            sentence = match.group(1)
            if tracker.is_redundant(sentence):
                # Replace with short label
                result = result.replace(sentence, replacement, 1)
                replacements_made += 1
                log.debug(f"🔄 Replaced redundant description in {section_name}")
            else:
                # First occurrence - mark as seen
                tracker.mark_seen(sentence, section_name)

    if replacements_made > 0:
        log.info(f"📝 Sprint G2.4: {replacements_made} redundancies replaced in {section_name}")

    return result


# =============================================================================
# ANTI-REDUNDANZ: Pain-Point und Tool Deduplizierung
# =============================================================================

class DeduplicationCache:
    """
    Cache für bereits verwendete Pain Points und Tools.
    Verhindert Wiederholungen über Sektionen hinweg.
    """

    def __init__(self) -> None:
        self.used_pain_points: Set[str] = set()
        self.used_tools: Set[str] = set()
        self.section_order: List[str] = []

    def reset(self) -> None:
        """Reset cache for new report generation."""
        self.used_pain_points.clear()
        self.used_tools.clear()
        self.section_order.clear()

    def mark_pain_point_used(self, pain_point: str) -> None:
        """Mark a pain point as used."""
        normalized = pain_point.strip().lower()
        if normalized:
            self.used_pain_points.add(normalized)

    def mark_tool_used(self, tool: str) -> None:
        """Mark a tool as used."""
        normalized = tool.strip().lower()
        if normalized:
            self.used_tools.add(normalized)

    def is_pain_point_used(self, pain_point: str) -> bool:
        """Check if pain point was already used."""
        return pain_point.strip().lower() in self.used_pain_points

    def is_tool_used(self, tool: str) -> bool:
        """Check if tool was already used."""
        return tool.strip().lower() in self.used_tools


# Global deduplication cache (reset per report generation)
_dedupe_cache = DeduplicationCache()


def get_dedupe_cache() -> DeduplicationCache:
    """Get the global deduplication cache."""
    return _dedupe_cache


def reset_dedupe_cache() -> None:
    """Reset deduplication cache for new report."""
    _dedupe_cache.reset()
    log.debug("🔄 Deduplication cache reset")


def dedupe_pain_points(text: str, section_name: str) -> str:
    """
    Entfernt oder kürzt Pain Points, die bereits in früheren Sektionen verarbeitet wurden.

    Logik:
    - Quick Wins: Verarbeitet alle Pain Points vollständig (markiert als used)
    - Roadmap 90d: Darf Pain Points nur ergänzend erwähnen
    - Roadmap 12m: Darf Pain Points nicht wiederholen, nur "darauf aufbauen"

    Args:
        text: Der Text mit potenziellen Pain-Point-Wiederholungen
        section_name: Name der aktuellen Sektion

    Returns:
        Text mit deduplizierten Pain Points
    """
    cache = get_dedupe_cache()

    # Quick Wins ist die primäre Sektion für Pain Points
    if section_name == "quick_wins":
        # Markiere Pain Points als verwendet, aber ändere nichts
        _extract_and_mark_pain_points(text, cache)
        return text

    # Für Roadmaps: füge Deduplizierungs-Hinweis hinzu
    if section_name in ("roadmap_90d", "roadmap_12m") and cache.used_pain_points:
        dedupe_hint = _build_pain_point_dedupe_hint(section_name, cache)
        return dedupe_hint + text

    return text


def dedupe_tools(text: str, section_name: str) -> str:
    """
    Kürzt Tool-Empfehlungen, die bereits in früheren Sektionen erschienen sind.

    Logik:
    - Quick Wins: Kurz-Empfehlungen (markiert als used)
    - Tools-Empfehlungen: Volltext mit Details
    - Roadmap 90d & 12m: Nur "Tool X nutzen (bereits oben erwähnt)"

    Args:
        text: Der Text mit potenziellen Tool-Wiederholungen
        section_name: Name der aktuellen Sektion

    Returns:
        Text mit deduplizierten Tools
    """
    cache = get_dedupe_cache()

    # Quick Wins und Tools-Empfehlungen markieren Tools als verwendet
    if section_name in ("quick_wins", "tools_empfehlungen"):
        _extract_and_mark_tools(text, cache)
        return text

    # Für Roadmaps: füge Deduplizierungs-Hinweis hinzu
    if section_name in ("roadmap_90d", "roadmap_12m") and cache.used_tools:
        dedupe_hint = _build_tool_dedupe_hint(section_name, cache)
        return dedupe_hint + text

    return text


def _extract_and_mark_pain_points(text: str, cache: DeduplicationCache) -> None:
    """Extract pain points from text and mark them as used."""
    # Common pain point patterns
    pain_patterns = [
        r"(?:zeitfresser|pain.?point|schmerzpunkt|problem|herausforderung)[:\s]+([^.!?\n]+)",
        r"(?:manuell|aufwändig|zeitintensiv)[^.!?\n]*(?:prozess|arbeit|aufgabe)[^.!?\n]*",
    ]

    text_lower = text.lower()
    for pattern in pain_patterns:
        matches = re.findall(pattern, text_lower, re.IGNORECASE)
        for match in matches:
            if isinstance(match, str) and len(match) > 10:
                cache.mark_pain_point_used(match[:50])  # First 50 chars as key


def _extract_and_mark_tools(text: str, cache: DeduplicationCache) -> None:
    """Extract tool names from text and mark them as used."""
    # Common tool name patterns
    tool_patterns = [
        r"(?:tool|software|lösung|plattform|system)[:\s]+([A-Z][a-zA-Z0-9\s]+)",
        r"(?:ChatGPT|GPT-4|Claude|Copilot|Notion|Slack|Teams|Asana|Monday|Trello)",
        r"(?:Microsoft\s+\w+|Google\s+\w+|SAP\s+\w+)",
    ]

    for pattern in tool_patterns:
        matches = re.findall(pattern, text, re.IGNORECASE)
        for match in matches:
            if isinstance(match, str) and len(match) > 2:
                cache.mark_tool_used(match.strip())


def _build_pain_point_dedupe_hint(section_name: str, cache: DeduplicationCache) -> str:
    """Build instruction hint for pain point deduplication."""
    if section_name == "roadmap_90d":
        return """
## Anti-Redundanz Hinweis (Pain Points)

Die folgenden Pain Points wurden bereits in den Quick Wins adressiert – erwähne sie hier nur ergänzend oder verweise auf die Quick-Wins-Sektion:
- Fokussiere auf NEUE Aspekte oder Vertiefungen
- Vermeide wörtliche Wiederholungen

---

"""
    elif section_name == "roadmap_12m":
        return """
## Anti-Redundanz Hinweis (Pain Points)

Die folgenden Pain Points wurden bereits in Quick Wins und 90-Tage-Roadmap behandelt:
- Wiederhole sie NICHT
- Baue logisch darauf auf
- Zeige die WEITERENTWICKLUNG, nicht die Grundlagen

---

"""
    return ""


def _build_tool_dedupe_hint(section_name: str, cache: DeduplicationCache) -> str:
    """Build instruction hint for tool deduplication."""
    if section_name in ("roadmap_90d", "roadmap_12m"):
        return """
## Anti-Redundanz Hinweis (Tools)

Bereits empfohlene Tools nicht erneut ausführlich beschreiben.
Bei Erwähnung: "Tool X nutzen (siehe Quick Wins / Tools-Empfehlungen)"

---

"""
    return ""


# =============================================================================
# SOLO-PERSONA MODULATION: Vereinfachte Governance-Sprache
# =============================================================================

# Sprint N3/N3.1: Phrase-based filtering (applied FIRST, before word-based)
# These are multi-word phrases that must be replaced as units
SOLO_FORBIDDEN_PHRASES: List[str] = [
    # Team-bezogen
    "team aufbauen",
    "teams aufbauen",
    "team einbinden",
    "teams einbinden",
    "im team",
    "das team",
    "ihr team",
    "unser team",
    # Mitarbeiter-bezogen
    "mitarbeiter einstellen",
    "mitarbeitende einstellen",
    "personal einstellen",
    "neue mitarbeiter",
    "mitarbeiter schulen",
    # Abteilungs-/Fachbereichs-bezogen
    "fachbereiche einbinden",
    "fachbereich einbinden",
    "in fachbereichen",
    "die fachbereiche",
    "alle fachbereiche",
    "verschiedene fachbereiche",
    "abteilungen einbinden",
    "abteilung einbinden",
    # Management-/Führungs-bezogen
    "führungsteam",
    "management-team",
    "bereichsleitung",
    "fachabteilung",
    "fachabteilungen",
]

SOLO_PHRASE_REPLACEMENTS: Dict[str, str] = {
    # Team-Phrasen → Solo-passend
    "team aufbauen": "Kapazität aufbauen",
    "teams aufbauen": "Kapazitäten erweitern",
    "team einbinden": "externe Expertise einbinden",
    "teams einbinden": "Kooperationspartner einbinden",
    "im team": "gemeinsam mit Partnern",
    "das team": "Ihre Kapazität",
    "ihr team": "Ihre Kapazität",
    "unser team": "unsere Kapazität",
    # Mitarbeiter-Phrasen → Solo-passend
    "mitarbeiter einstellen": "Ressourcen erweitern",
    "mitarbeitende einstellen": "Ressourcen erweitern",
    "personal einstellen": "externe Unterstützung hinzuziehen",
    "neue mitarbeiter": "zusätzliche Kapazitäten",
    "mitarbeiter schulen": "sich weiterbilden",
    # Fachbereichs-Phrasen → Solo-passend
    "fachbereiche einbinden": "Arbeitsbereiche strukturieren",
    "fachbereich einbinden": "Arbeitsfeld strukturieren",
    "in fachbereichen": "in Ihren Arbeitsbereichen",
    "die fachbereiche": "Ihre Arbeitsbereiche",
    "alle fachbereiche": "alle Ihre Arbeitsbereiche",
    "verschiedene fachbereiche": "verschiedene Arbeitsbereiche",
    "abteilungen einbinden": "Arbeitsbereiche strukturieren",
    "abteilung einbinden": "Arbeitsbereich einbeziehen",
    # Management/Führung → Solo-passend
    "führungsteam": "Ihre Entscheidungsfindung",
    "management-team": "Ihre strategische Planung",
    "bereichsleitung": "Verantwortungsbereich",
    "fachabteilung": "Arbeitsfeld",
    "fachabteilungen": "Arbeitsbereiche",
    # SPRINT G15.1-B: Bereichsleiter persona leak fix for Solo
    "bereichsleiter:innen": "verantwortliche Ansprechpersonen im Unternehmen",
    "bereichsleiter": "verantwortliche Ansprechpartner:innen im Unternehmen",
}

# Corporate terms → Solo-appropriate replacements (word-based)
# Sprint N3.2: "abteilung" uses "Arbeitsbereich" as per user requirement
SOLO_GOVERNANCE_REPLACEMENTS: Dict[str, str] = {
    # Governance terms (case-insensitive replacements)
    "governance framework": "einfache Regeln",
    "governance-framework": "einfache Regeln",
    "rollenmodell": "persönliche Verantwortung",
    "verantwortlichkeitsmatrix": "klare Zuständigkeit",
    "steuerungskreis": "regelmäßige Selbstkontrolle",
    "steering committee": "regelmäßige Selbstkontrolle",
    "gremium": "Prüfroutine",
    "board": "Prüfroutine",
    "abteilung": "Arbeitsbereich",
    "abteilungen": "Arbeitsbereiche",
    "organisationsentwicklung": "Arbeitsweise verbessern",
    "change management": "Veränderung umsetzen",
    "change-management": "Veränderung umsetzen",
    # Team references inappropriate for solo (Sprint N2)
    "team aufbauen": "Arbeitsweise strukturieren",
    "mitarbeiter schulen": "sich weiterbilden",
    "mitarbeiterschulung": "Weiterbildung",
    "teams": "Kapazitäten",
    "team": "Kapazität",
    "fachbereiche": "Arbeitsbereiche",
    "fachbereich": "Arbeitsfeld",
    "projektteam": "Projektstruktur",
    "mitarbeiter einstellen": "externe Unterstützung hinzuziehen",
    "mitarbeiter": "Ressourcen",
    "mitarbeitende": "Beteiligte",
    "mitarbeitenden": "Beteiligten",
    "personalentscheidungen": "Ressourcenentscheidungen",
    "personaldaten": "vertrauliche Daten",
    "belegschaft": "Kapazität",
    # SPRINT G15.1-B: Bereichsleiter persona leak fix
    "bereichsleiter:innen": "verantwortliche Ansprechpersonen",
    "bereichsleiter": "Ansprechpartner:innen",
    # EN equivalents for Solo
    "department": "work area",
    "departments": "work areas",
    "staff": "resources",
    "employees": "collaborators",
    "employee": "collaborator",
}

# =============================================================================
# SPRINT N: SOLO PERSONA LEAK ELIMINATION
# =============================================================================
# These terms MUST NEVER appear in Solo reports - they indicate team/KMU context

# v14.35.19+: Protected product names that should NOT be replaced
# These are proper nouns for tools/software - "Microsoft Teams" should stay as-is
PROTECTED_PRODUCT_NAMES: List[str] = [
    "Microsoft Teams",
    "Google Teams",  # hypothetical
    "Teams Copilot",
    "MS Teams",
]

# Hotfix 1027.2.1 F4: Standalone "Teams" als Tool-Name (z.B. „Zoom oder Teams")
# wurde von der Kette SOLO_GOVERNANCE_REPLACEMENTS (teams→Kapazitäten) und
# content_quality_enforcer (Kapazitäten→Zeitbudget) als „Kapazitäten" missdeutet
# → Output: „Zoom oder Zeitbudget". PROTECTED_PRODUCT_NAMES nutzt re.escape
# und kann nur Literale; für kontextuelle Erkennung („Teams" als Tool im
# Meeting-Tool-Cluster) brauchen wir Regex-Patterns. Match-Text wird durch
# Placeholder vor der Filter-Pipeline ersetzt und nach den Replacements
# 1:1 rekonstruiert (siehe apply_solo_persona_filter Z.998+).
#
# Heuristik: „Teams" gilt als Tool-Name, wenn es in einer Liste mit anderen
# bekannten Meeting-/Collaboration-Tools (Zoom, Google Meet, Webex, Slack,
# Otter, Loom, Jitsi) steht (durch /,/und/oder/„or"/„and" verbunden). In
# allen anderen Kontexten greift die bisherige Solo-Lexicon-Ersetzung.
_TOOL_NEIGHBORS = r"(?:Zoom|Google\s+Meet|Webex|Slack|Otter|Loom|Jitsi|GoToMeeting|BlueJeans|Skype)"
PROTECTED_PRODUCT_PATTERNS: List[str] = [
    # „Zoom oder Teams" / „Zoom, Teams" / „Zoom und Teams"
    rf"\b{_TOOL_NEIGHBORS}\s*(?:,|/|\s+oder\s+|\s+und\s+|\s+or\s+|\s+and\s+)\s*Teams\b",
    # „Teams oder Zoom" / „Teams, Zoom" / „Teams und Zoom"
    rf"\bTeams\s*(?:,|/|\s+oder\s+|\s+und\s+|\s+or\s+|\s+and\s+)\s*{_TOOL_NEIGHBORS}\b",
]

SOLO_FORBIDDEN_TERMS: List[str] = [
    # Team-specific terms (German)
    "team",
    "teams",
    "teamstruktur",
    "teamwork",
    "team aufbauen",
    "teamrollen",
    "teammitglieder",
    # Employee/HR terms (German)
    "mitarbeiter",
    "mitarbeitende",
    "mitarbeiter einstellen",
    "mitarbeiterschulung",
    "personalstrategien",
    "personal",
    "belegschaft",
    # Department/Organization terms (German)
    "fachbereich",
    "fachbereiche",
    "abteilung",
    "abteilungen",
    "bereichsleiter",
    "bereichsübergreifend",
    # English equivalents
    "team building",
    "team members",
    "hire employees",
    "staff",
    "department",
    "departments",
]


def apply_solo_persona_filter(text: str) -> str:
    """
    Sprint N3/N3.1: Applies comprehensive Solo persona filtering.

    Replaces phrases and terms inappropriate for Solo professionals.
    This is the main entry point for Solo text filtering.

    IMPORTANT: Uses word boundaries to avoid replacing within compound words
    like "Kundenabteilung" (customer department references should be preserved).

    v14.35.19+: Protects product names like "Microsoft Teams" from replacement.

    Args:
        text: Text to filter

    Returns:
        Filtered text with Solo-appropriate language
    """
    if not text:
        return text

    result = text
    replacements_made = []

    # v14.35.19+: Protect product names before replacement
    # Map: placeholder → original product name
    protected_map: Dict[str, str] = {}
    for i, product_name in enumerate(PROTECTED_PRODUCT_NAMES):
        placeholder = f"__PROTECTED_PRODUCT_{i}__"
        if product_name.lower() in result.lower():
            # Case-insensitive replacement with placeholder
            pattern = re.compile(re.escape(product_name), re.IGNORECASE)
            # Capture the actual case used in the text
            match = pattern.search(result)
            if match:
                original = match.group(0)
                protected_map[placeholder] = original
                result = pattern.sub(placeholder, result)

    # Hotfix 1027.2.1 F4: Kontextuelle Regex-Patterns für „Teams" als Tool-Name
    # im Meeting-Tool-Cluster. Jedes Match wird per Index-Placeholder maskiert,
    # damit Mehrfachvorkommen mit unterschiedlicher Schreibweise erhalten bleiben.
    for i, regex_pattern in enumerate(PROTECTED_PRODUCT_PATTERNS):
        compiled = re.compile(regex_pattern, re.IGNORECASE)
        # Use callback to capture each match's actual text individually
        def _replace(match: 're.Match[str]', start_idx=i) -> str:
            idx = len(protected_map)
            placeholder = f"__PROTECTED_PATTERN_{start_idx}_{idx}__"
            protected_map[placeholder] = match.group(0)
            return placeholder
        result = compiled.sub(_replace, result)

    # 1) Apply phrase replacements FIRST (multi-word patterns)
    for phrase, replacement in SOLO_PHRASE_REPLACEMENTS.items():
        pattern = re.compile(re.escape(phrase), re.IGNORECASE)
        if pattern.search(result):
            result = pattern.sub(replacement, result)
            replacements_made.append(f"[phrase] {phrase} → {replacement}")

    # 2) Apply word-based replacements
    # Sprint N3.2: Sort by length (longest first) to avoid partial matches
    # e.g., "abteilungen" must be processed before "abteilung"
    sorted_replacements = sorted(
        SOLO_GOVERNANCE_REPLACEMENTS.items(),
        key=lambda x: len(x[0]),
        reverse=True
    )

    for term, replacement in sorted_replacements:
        if term.lower() in ("abteilung", "abteilungen"):
            # Special handling for Abteilung: protect customer-related compound words
            # but catch all other cases including "IT-Abteilung", "HR-Abteilung", etc.
            pattern = re.compile(
                r'(?<![Kk]unden)(' + re.escape(term) + r')',
                re.IGNORECASE
            )
        elif term.lower() in ("board", "gremium"):
            # SPRINT G15.1-A: Use word boundaries for short terms that could match
            # inside other words (e.g., "board" in "Onboarding")
            pattern = re.compile(
                r'\b' + re.escape(term) + r'\b',
                re.IGNORECASE
            )
        else:
            # Standard case-insensitive replacement
            pattern = re.compile(re.escape(term), re.IGNORECASE)

        if pattern.search(result):
            result = pattern.sub(replacement, result)
            replacements_made.append(f"[word] {term} → {replacement}")

    if replacements_made:
        log.debug(f"🔧 Solo-Persona-Filter: {len(replacements_made)} Ersetzungen")

    # v14.35.19+: Restore protected product names
    for placeholder, original in protected_map.items():
        result = result.replace(placeholder, original)

    return result


def simplify_solo_governance(text: str, company_size: str) -> str:
    """
    Vereinfacht Governance-Sprache für Solo-Unternehmer.

    Sprint N3: Now uses apply_solo_persona_filter for comprehensive filtering.

    Args:
        text: Der zu vereinfachende Text
        company_size: Unternehmensgröße ('solo', 'team', 'kmu')

    Returns:
        Vereinfachter Text für Solo, unverändert für andere Größen
    """
    if company_size != "solo":
        return text

    return apply_solo_persona_filter(text)


def check_solo_persona_leaks(text: str, company_size: str) -> List[str]:
    """
    SPRINT N: Prüft auf verbleibende Team/KMU-Begriffe in Solo-Reports.

    Returns:
        Liste der gefundenen verbotenen Begriffe (leer wenn keine Leaks)
    """
    if company_size != "solo":
        return []

    leaks_found = []
    text_lower = text.lower()

    for term in SOLO_FORBIDDEN_TERMS:
        if term.lower() in text_lower:
            # Double-check with word boundary for short terms
            if len(term) <= 6:
                pattern = re.compile(r'\b' + re.escape(term) + r'\b', re.IGNORECASE)
                if pattern.search(text):
                    leaks_found.append(term)
            else:
                leaks_found.append(term)

    if leaks_found:
        log.warning(f"⚠️ Solo-Persona-Leaks gefunden: {leaks_found}")

    return leaks_found


def get_solo_governance_hint(company_size: str) -> str:
    """
    Gibt einen Hinweis-Block für Solo-spezifische Governance zurück.

    Args:
        company_size: Unternehmensgröße ('solo', 'team', 'kmu')

    Returns:
        Hinweis-String für Solo, leerer String für andere Größen
    """
    if company_size != "solo":
        return ""

    return """
## Solo-Persona Hinweis

Für Einzelunternehmer/Freiberufler bitte EINFACHE Sprache verwenden:
- ✅ "Checkliste", "persönliche Routine", "eigene Prüfpunkte"
- ✅ "Dokumentation light", "einfache Notiz", "pragmatischer Standard"
- ❌ KEINE: "Governance Framework", "Rollenmodell", "Gremium", "Board"
- ❌ KEINE: Team-Begriffe wie "Mitarbeiter", "Abteilung", "Schulung"

---

"""


# =============================================================================
# PLATIN+ STABILIZATION: Konfiguration für kritische Sektionen
# =============================================================================
# PDF-SLIMDOWN v2.0: Token-Limits um 20-30% reduziert für kürzere Outputs
# ohne Qualitätseinbußen. Stop-Sequences erweitert.
#
# Ziel: PDF < 10-12 MB, weniger LLM-Abbrüche
# =============================================================================

# PLATIN+ Token-Limits (SPRINT N: Length Stabilization)
# Updated values for minimum word count compliance
PLATIN_MAX_TOKENS_DEFAULT = 3000  # Default für kritische Sections
PLATIN_MAX_TOKENS_COMPACT = 2500  # Für reduzierte Sections (roadmap, recommendations)
PLATIN_MAX_TOKENS_EXTENDED = 4200  # Für längere Sections (roadmap_12m, gamechanger)


class PlatinSectionConfig(TypedDict):
    """Configuration for PLATIN+ critical sections."""
    max_tokens: int  # Token-Limit für LLM-Output (REDUZIERT für PDF-SLIMDOWN)
    temperature: float
    presence_penalty: float
    frequency_penalty: float
    min_words: int  # Minimum word count expected


# STOP-SEQUENCES für frühzeitiges Beenden (verhindert Überlänge)
PLATIN_STOP_SEQUENCES = [
    "\n\n---\n",           # Markdown-Abschnitt-Ende
    "</section>",          # HTML-Section-Ende
    "## Abschluss",        # Roadmap-Endsignal DE
    "## Conclusion",       # Roadmap-Endsignal EN
    "## Ausblick",         # Alternatives Endsignal DE
    "## Outlook",          # Alternatives Endsignal EN
]


PLATIN_CRITICAL_SECTIONS: Dict[str, PlatinSectionConfig] = {
    # NOTE: executive_summary and tools_empfehlungen are NOT in this list
    # They are handled by report_validator.py MIN_SECTION_LENGTH_BY_SIZE for Sprint N

    # Foerderpotenzial: bleibt hoch (braucht detaillierte Förderinfos)
    "foerderpotenzial": {
        "max_tokens": 3200,  # Reduziert von 4096 (-22%)
        "temperature": 0.4,
        "presence_penalty": 0.0,
        "frequency_penalty": 0.0,
        "min_words": 700,  # Reduziert von 900
    },
    # Risks: bleibt relativ hoch (wichtige Compliance-Infos)
    "risks": {

        "max_tokens": 6000,  # v14.30: Erhöht für vollständige Risk-Cards
        "temperature": 0.4,
        "presence_penalty": 0.0,
        "frequency_penalty": 0.0,
        "min_words": 600,  # Reduziert von 800
    },
    # Recommendations: erhöht um Truncation zu vermeiden
    "recommendations": {
        "max_tokens": 6000,  # v14.30: Erhöht für vollständige Recommendation-Cards
        "temperature": 0.4,
        "presence_penalty": 0.1,  # Leichte Penalty gegen Wiederholungen
        "frequency_penalty": 0.1,
        "min_words": 400,  # Reduziert von 800
    },
    # Roadmap 12m: Erhöht um Truncation zu vermeiden
    # Sprint N min_words enforced via report_validator.py (size-aware: 500/600/700)
    "roadmap_12m": {
        "max_tokens": 4000,  # FIX: Erhöht von 2800 um Truncation zu vermeiden
        "temperature": 0.4,
        "presence_penalty": 0.1,
        "frequency_penalty": 0.1,
        "min_words": 350,  # PDF-SLIMDOWN v2.0 base (size-aware in validator)
    },
    # Roadmap 90d: Sprint G17.R - Roadmap-Booster (extended with KPI + Change sections)
    # Size-aware min_words: Solo 250, Team 320, KMU 350 (after multipliers)
    "roadmap_90d": {
        "max_tokens": 4000,  # FIX: Erhöht von 2800 um Truncation zu vermeiden
        "temperature": 0.4,
        "presence_penalty": 0.1,
        "frequency_penalty": 0.1,
        "min_words": 320,  # G17.R: Base 320 → Solo 256 (0.8x), Team 320 (1.0x), KMU 368 (1.15x)
    },
    # Quick Wins: v7.0 format needs more tokens for structured boxes, blockquotes, prompts
    "quick_wins": {
        "max_tokens": 4500,  # FIX: Erhöht von 3500 um Truncation zu vermeiden
        "temperature": 0.3,
        "presence_penalty": 0.1,
        "frequency_penalty": 0.1,
        "min_words": 150,
    },
    # Gamechanger: PDF-SLIMDOWN v2.0 token budget
    # Sprint N min_words enforced via report_validator.py (750 for all sizes)
    "gamechanger": {
        "max_tokens": 3000,  # PDF-SLIMDOWN v2.0 value
        "temperature": 0.5,  # Etwas kreativer
        "presence_penalty": 0.0,
        "frequency_penalty": 0.0,
        "min_words": 500,  # PDF-SLIMDOWN v2.0 base (750 enforced in validator)
    },
    # Unternehmensprofil: bleibt relativ hoch (wichtige Kontextinfos)
    "unternehmensprofil_markt": {
        "max_tokens": 3000,  # Reduziert von 4096 (-27%)
        "temperature": 0.4,
        "presence_penalty": 0.0,
        "frequency_penalty": 0.0,
        "min_words": 400,  # Reduziert von 500
    },
    # Transparency Box: kompakt (180-250 Wörter)
    "transparency_box": {
        "max_tokens": 1500,
        "temperature": 0.3,
        "presence_penalty": 0.0,
        "frequency_penalty": 0.0,
        "min_words": 150,
    },
    # Technologie & Prozesse: kompakt (300-400 Wörter)
    "technologie_prozesse": {
        "max_tokens": 2000,
        "temperature": 0.3,
        "presence_penalty": 0.0,
        "frequency_penalty": 0.0,
        "min_words": 200,
    },
    # Sprint N2: Org Change - niedrige min_words für Solo
    "org_change": {
        "max_tokens": 2000,
        "temperature": 0.4,
        "presence_penalty": 0.0,
        "frequency_penalty": 0.0,
        "min_words": 100,  # Niedrig für Solo (wird zu 80 mit 0.8x Multiplikator)
    },
}


# PE-3 FIX: Size-aware token multipliers
# Solo = shorter reports (0.8x), Team = standard (1.0x), KMU = longer (1.15x)
SIZE_TOKEN_MULTIPLIERS: Dict[str, float] = {
    "solo": 0.8,   # 20% reduction for solopreneurs (shorter, focused)
    "team": 1.0,   # Standard baseline
    "kmu": 1.15,   # 15% increase for larger companies (more detail)
}


def get_platin_config(section_name: str, size: Optional[str] = None) -> Optional[PlatinSectionConfig]:
    """
    Get PLATIN+ configuration for a section if it's a critical section.

    PE-3 FIX: Now supports size-aware max_tokens scaling.

    Args:
        section_name: Name of the section (e.g., 'foerderpotenzial')
        size: Company size ('solo', 'team', 'kmu') for token adjustment

    Returns:
        PlatinSectionConfig if section is critical, None otherwise.
        If size is provided, max_tokens will be adjusted accordingly.
    """
    base_config = PLATIN_CRITICAL_SECTIONS.get(section_name.lower())
    if not base_config:
        return None

    # If no size specified, return base config unchanged
    if not size:
        return base_config

    # Get size multiplier (default to team/1.0 if unknown)
    multiplier = SIZE_TOKEN_MULTIPLIERS.get(size.lower(), 1.0)

    # Create adjusted config (copy to avoid modifying original)
    adjusted_config: PlatinSectionConfig = {
        **base_config,
        "max_tokens": int(base_config["max_tokens"] * multiplier),
    }
    return adjusted_config


def is_platin_critical_section(section_name: str) -> bool:
    """
    Check if a section is a PLATIN+ critical section that needs special handling.

    Args:
        section_name: Name of the section

    Returns:
        True if section needs PLATIN+ handling
    """
    return section_name.lower() in PLATIN_CRITICAL_SECTIONS


def get_platin_min_words(section_name: str, size: Optional[str] = None) -> int:
    """
    Get minimum word count for a section, adjusted for company size.

    Sprint G9.4: Uses centralized config_validation.py as primary source.
    Falls back to PLATIN_SECTION_SPECS if central config unavailable.

    Args:
        section_name: Name of the section
        size: Company size ('solo', 'team', 'kmu') for min_words adjustment

    Returns:
        Minimum word count (size-adjusted), or 0 if not a critical section
    """
    # G9.4: Try centralized config first (single source of truth)
    if callable(get_central_min_words) and size:
        central_min = get_central_min_words(size, section_name)
        if central_min > 0:
            log.debug(
                "[G9.4] Using centralized min_words: section=%s, size=%s, min=%d",
                section_name, size, central_min
            )
            return central_min

    # Fallback to PLATIN_SECTION_SPECS (for sections not in central config)
    config = get_platin_config(section_name)
    if not config:
        return 0

    base_min_words = config["min_words"]

    # Sprint N2: Reduce min_words for Solo to prevent fallback flooding
    if size and size.lower() == "solo":
        # Apply 0.8x multiplier for Solo (same as token multiplier)
        return max(50, int(base_min_words * 0.8))

    return base_min_words


class RoadmapConstraints(TypedDict):
    """Typed structure for roadmap size constraints."""
    max_budget_total: int
    max_budget_per_phase: int
    team_structure: str
    phase_duration_weeks: int
    example_team: str
    realistic_capacity: str


# Roadmap constraints by company size
ROADMAP_CONSTRAINTS: Dict[str, RoadmapConstraints] = {
    "solo": {
        "max_budget_total": 10000,
        "max_budget_per_phase": 3000,
        "team_structure": "Sie + maximal 1–2 Freelancer",
        "phase_duration_weeks": 4,
        "example_team": "1 Backend-Dev (Freelance, 20h)",
        "realistic_capacity": "Sie arbeiten hauptsächlich selbst, Freelancer für Spezialaufgaben",
    },
    "team": {
        "max_budget_total": 50000,
        "max_budget_per_phase": 15000,
        "team_structure": "Kernteam + externe Experten",
        "phase_duration_weeks": 4,
        "example_team": "2–3 Entwickler + 1 Projektleiter:in",
        "realistic_capacity": "Kleines internes Team + punktuelle Verstärkung",
    },
    "kmu": {
        "max_budget_total": 200000,
        "max_budget_per_phase": 60000,
        "team_structure": "Dediziertes Projektteam",
        "phase_duration_weeks": 6,
        "example_team": "5–8 Entwickler:innen + PM + Architect",
        "realistic_capacity": "Vollständiges Projektteam mit verschiedenen Rollen",
    },
}


def _normalize_size(raw_size: str | None) -> str:
    """
    Normalize size value from briefing to internal ROADMAP_CONSTRAINTS key.

    Supports legacy values ("klein", "mittel", "small", "small_team") for
    backwards compatibility, mappt aber intern immer auf 'solo' | 'team' | 'kmu'.

    PE-2 FIX: Default changed from 'team' to 'solo' for safer assumptions
    (Solo-Freelancer reports are more common and team terminology would be inappropriate)
    """
    if not raw_size:
        return "solo"  # PE-2 FIX: Default to solo (was: team)

    raw = raw_size.strip().lower()
    alias_map: Dict[str, str] = {
        "klein": "team",
        "small": "team",
        "small_team": "team",
        "mittel": "kmu",
        "medium": "kmu",
    }
    size = alias_map.get(raw, raw)
    if size not in ROADMAP_CONSTRAINTS:
        return "solo"  # PE-2 FIX: Default to solo (was: team)
    return size


def enhance_roadmap_prompt(base_prompt: str, context: Dict[str, Any]) -> str:
    """
    Inject size-specific constraints into roadmap prompt.

    Args:
        base_prompt: Original prompt text
        context: Briefing data with unternehmensgroesse, investitionsbudget

    Returns:
        Enhanced prompt with size constraints
    """
    size = _normalize_size(context.get("unternehmensgroesse"))  # maps to solo/team/kmu
    constraints = ROADMAP_CONSTRAINTS[size]

    # Get investment budget from briefing (aligned mit Formular-Optionen)
    investment_budget = context.get("investitionsbudget", "2000_10000")
    investment_map: Dict[str, int] = {
        "unter_2000": 2000,
        "2000_10000": 10000,
        "10000_50000": 50000,
        # Für „ueber_50000“ und „unklar“ nutzen wir die maximale sinnvolle Größe laut Size-Constraints
        "ueber_50000": constraints["max_budget_total"],
        "unklar": constraints["max_budget_total"],
    }
    budget_from_map: int = investment_map.get(
        investment_budget, constraints["max_budget_total"]
    )

    max_budget_total: int = constraints["max_budget_total"]
    max_realistic_budget = min(max_budget_total, budget_from_map)

    size_context = f"""
KRITISCHE VORGABEN – Unternehmensgröße: {size.upper()}

Budget-Grenzen (STRIKT EINHALTEN!):
- Gesamt-Budget für 90 Tage: MAX €{max_realistic_budget:,}
- Budget pro Phase: MAX €{constraints['max_budget_per_phase']:,}
- Angegebenes Investment-Budget (Kategorie): {investment_budget}

Team-Struktur (REALISTISCH!):
- {constraints['team_structure']}
- Beispiel: {constraints['example_team']}
- Kapazität: {constraints['realistic_capacity']}

Für {size} nicht empfohlen:
- Keine Projektteams, die nicht zur Unternehmensgröße passen
- Budget-Obergrenze beachten: max. €{max_realistic_budget:,}
- Realistische Team-Kapazitäten berücksichtigen

Die Roadmap MUSS mit dem realen Budget und der Unternehmensgröße umsetzbar sein!

---

"""

    return size_context + base_prompt


class PromptEnhancer:
    """
    Enhances existing prompts with contextual information.
    Works with the existing prompt_loader.py system.
    """

    def __init__(self, data_dir: str = "data") -> None:
        """
        Initialize PromptEnhancer.

        Args:
            data_dir: Path to context data directory
        """
        self.builder = PromptBuilder(data_dir=data_dir)
        log.info("✅ PromptEnhancer initialized (data_dir=%s)", data_dir)

    def build_context_block(self, briefing_data: Dict[str, Any]) -> str:
        """
        Build HTML-formatted context block for injection into prompts.

        v14.35.19: Hauptleistung-first - primäres Individualisierungs-Kriterium

        Args:
            briefing_data: Complete briefing data with branche, unternehmensgroesse, hauptleistung, etc.

        Returns:
            HTML string with context information
        """
        # G19.1-MAP: Map frontend branch to engine key
        raw_branch = briefing_data.get("branche", "") or briefing_data.get("branch", "") or ""
        branche = map_frontend_branch_to_engine(raw_branch)

        groesse = briefing_data.get("unternehmensgroesse", "")

        # v14.35.19: Hauptleistung ist primäres Kriterium
        hauptleistung = (
            briefing_data.get("hauptleistung", "") or
            briefing_data.get("HAUPTLEISTUNG", "") or ""
        )

        # 3.1.4.15: Get language for i18n context labels
        lang_raw = (briefing_data.get("lang") or briefing_data.get("LANG") or briefing_data.get("sprache") or "de")
        report_lang = str(lang_raw).lower().strip()

        if not branche or not groesse:
            return "<!-- Context data incomplete -->"

        # Load contexts
        branch_ctx = self.builder.load_context("branch", branche)
        size_ctx = self.builder.load_context("size", groesse)

        log.info("✅ Context loaded: hauptleistung=%s, branch=%s, size=%s, lang=%s",
                 hauptleistung[:30] + "..." if len(hauptleistung) > 30 else hauptleistung,
                 branche, groesse, report_lang)

        # Build compact HTML context block with hauptleistung-first
        context_html = self._build_html_block(branch_ctx, size_ctx, report_lang, hauptleistung)

        return context_html

    def _build_html_block(
        self, branch_ctx: Dict[str, Any], size_ctx: Dict[str, Any], lang: str = "de",
        hauptleistung: str = ""
    ) -> str:
        """Build compact HTML context block with i18n support

        v14.35.19: hauptleistung-first - primäres Individualisierungs-Kriterium
        """

        # 3.1.4.15: i18n labels for EN/DE
        is_en = str(lang or "de").lower().startswith("en")

        # i18n label definitions
        L = {
            "hauptleistung_label": "🎯 Core Service (Main Offering):" if is_en else "🎯 Kernleistung (Hauptleistung):",
            "branch_context": "📋 Industry Context:" if is_en else "📋 Branchen-Context:",
            "size_context": "🏢 Size Context:" if is_en else "🏢 Größen-Context:",
            "unknown": "Unknown" if is_en else "Unbekannt",
            "no_data": "(No data available)" if is_en else "(Keine Angaben)",
            "typical_workflows": "Typical Workflows:" if is_en else "Typische Workflows:",
            "pain_points": "Common Pain Points:" if is_en else "Häufigste Pain Points:",
            "typical_tools": "Typical Tools in Use:" if is_en else "Typische Tools im Einsatz:",
            "characteristics": "Characteristics:" if is_en else "Charakteristika:",
            "employees": "Employees:" if is_en else "Mitarbeiter:",
            "per_month": "/month" if is_en else "/Monat",
            "focus_priorities": "Focus Priorities:" if is_en else "Fokus-Prioritäten:",
            "not_recommended": "Not recommended for your current size:" if is_en else "In Ihrer aktuellen Größe nicht sinnvoll:",
        }

        # Helper to format list items
        def format_items(items: list, max_items: int = 4) -> str:
            if not items:
                return f"<li>{L['no_data']}</li>"
            return "\n    ".join([f"<li>{item}</li>" for item in items[:max_items]])

        # v14.35.19: HAUPTLEISTUNG section FIRST (primäres Individualisierungs-Kriterium)
        hauptleistung_html = ""
        if hauptleistung and hauptleistung != "—":
            hauptleistung_html = f"""
<div class="context-block hauptleistung-first" style="background:#fef3c7;padding:12px;border-left:4px solid #f59e0b;margin:16px 0;font-size:12px;">
  <h4 style="margin:0 0 8px 0;font-size:13px;color:#b45309;font-weight:bold;">{L['hauptleistung_label']}</h4>
  <p style="margin:0;font-size:12px;color:#78350f;"><strong>{hauptleistung}</strong></p>
</div>
"""

        # Branch section
        branch_html = f"""
<div class="context-block" style="background:#f3f4f6;padding:12px;border-left:3px solid #2563eb;margin:16px 0;font-size:11px;">
  <h4 style="margin:0 0 8px 0;font-size:12px;color:#1e40af;">{L['branch_context']} {branch_ctx.get('display_name', L['unknown'])}</h4>

  <p style="margin:6px 0;"><strong>{L['typical_workflows']}</strong></p>
  <ul style="margin:4px 0;padding-left:20px;">
    {format_items(branch_ctx.get('typical_workflows', []))}
  </ul>

  <p style="margin:6px 0;"><strong>{L['pain_points']}</strong></p>
  <ul style="margin:4px 0;padding-left:20px;">
    {format_items(branch_ctx.get('common_pain_points', []))}
  </ul>

  <p style="margin:6px 0;"><strong>{L['typical_tools']}</strong></p>
  <ul style="margin:4px 0;padding-left:20px;">
    {format_items(branch_ctx.get('typical_tools', []))}
  </ul>"""

        # Size section
        chars = size_ctx.get("characteristics", {})
        budget = size_ctx.get("budget_realistic", {})

        size_html = f"""
  <hr style="margin:12px 0;border:none;border-top:1px solid #cbd5e1;">

  <h4 style="margin:8px 0 8px 0;font-size:12px;color:#1e40af;">{L['size_context']} {size_ctx.get('display_name', L['unknown'])}</h4>

  <p style="margin:6px 0;"><strong>{L['characteristics']}</strong></p>
  <ul style="margin:4px 0;padding-left:20px;">
    <li>{L['employees']} {chars.get('mitarbeiter', L['unknown'])}</li>
    <li>Budget CAPEX max: {budget.get('capex_max', 0):,}€</li>
    <li>Budget OPEX max: {budget.get('opex_monthly_max', 0)}€{L['per_month']}</li>
  </ul>

  <p style="margin:6px 0;"><strong>{L['focus_priorities']}</strong></p>
  <ul style="margin:4px 0;padding-left:20px;">
    {format_items(size_ctx.get('focus_priorities', []), max_items=3)}
  </ul>

  <p style="margin:6px 0;"><strong>{L['not_recommended']}</strong></p>
  <ul style="margin:4px 0;padding-left:20px;color:#64748b;">
    {format_items(size_ctx.get('forbidden_recommendations', []), max_items=5)}
  </ul>
</div>"""

        # 3.1.4.15: EN hard guard - catch any German strings that slipped through
        if is_en:
            # v14.35.19: hauptleistung_html FIRST
            result = hauptleistung_html + branch_html + size_html
            de_markers = ["Branchen-Context:", "Größen-Context:", "Unbekannt", "Keine Angaben",
                          "Typische Workflows:", "Häufigste Pain Points:", "Typische Tools im Einsatz:",
                          "Charakteristika:", "Mitarbeiter:", "/Monat", "Fokus-Prioritäten:",
                          "In Ihrer aktuellen Größe nicht sinnvoll:", "Kernleistung (Hauptleistung):"]
            found_de = [m for m in de_markers if m in result]
            if found_de:
                import logging
                logging.warning(f"[3.1.4.15] EN context block contains DE strings: {found_de}")
            return result

        # v14.35.19: hauptleistung_html FIRST - primäres Individualisierungs-Kriterium
        return hauptleistung_html + branch_html + size_html

    def _build_strategic_context_prompt_block(self, briefing_data: Dict[str, Any]) -> str:
        """
        Build the strategic context block for prompt injection.

        This block is injected into ALL prompts to provide strategic context
        from the user's freetext answers.

        Args:
            briefing_data: Complete briefing data including strategic_context_block

        Returns:
            Formatted string for prompt injection
        """
        strategic_context = briefing_data.get("strategic_context_block", "")

        if not strategic_context or strategic_context.strip() == "":
            # Fallback for empty context
            return """
## Strategischer Kontext (Originalangaben des Unternehmens)

Es liegen keine zusätzlichen strategischen Freitext-Angaben vor; orientiere dich an den übrigen Antworten.

---

"""

        # Build the full strategic context block
        return f"""
## Strategischer Kontext (Originalangaben des Unternehmens)

{strategic_context}

**WICHTIG:** Wenn der Block Angaben zu No-Gos, roten Linien oder sensiblen Themen enthält (z.B. unter "No-Gos & Leitplanken"), sind diese strikt zu respektieren. Triff keine Empfehlungen, die diesen Leitplanken widersprechen.

---

"""

    def _build_strategic_alignment_instructions(
        self, prompt_name: str, briefing_data: Dict[str, Any]
    ) -> str:
        """
        Build prompt-specific instructions for strategic alignment.

        These instructions tell the LLM HOW to use the strategic context
        for specific prompt types (Quick Wins, Roadmaps).

        Args:
            prompt_name: Name of the prompt (e.g., 'quick_wins', 'roadmap_90d')
            briefing_data: Complete briefing data

        Returns:
            Formatted instruction string, or empty string if not applicable
        """
        strategic_context = briefing_data.get("strategic_context_block", "")

        # Only add alignment instructions if strategic context exists
        if not strategic_context or strategic_context.strip() == "":
            return ""

        # Quick Wins alignment instructions
        QUICK_WIN_PROMPTS = {"quick_wins"}
        if prompt_name in QUICK_WIN_PROMPTS:
            return """
## Anleitung zur Nutzung des Strategischen Kontexts

Nutze den Strategischen Kontext wie folgt:

- **Priorisiere alle Empfehlungen** entlang der "Strategischen Prioritäten".
- **Tackle die genannten "Zeitfresser & Prozess-Pain-Points" zuerst** – diese haben höchste Dringlichkeit.
- **Richte die Beispiele, Formulierungen und Use-Cases** an der "Wichtigsten Leistung / Hauptprodukt" aus.
- **Berücksichtige laufende KI-Projekte nur ergänzend** (keine Doppelarbeit, keine Redundanz).
- **Wenn es Ideen zur Geschäftsmodell-Entwicklung gibt:** erwähne 1–2 schnelle Validierungsschritte als Quick Win.

---

"""

        # Roadmap alignment instructions (90d, 12m, etc.)
        ROADMAP_PROMPTS = {"roadmap", "roadmap_12m", "roadmap_90d", "pilot_plan"}
        if prompt_name in ROADMAP_PROMPTS:
            return """
## Roadmap-Regeln basierend auf Strategischem Kontext

- **In den ersten 90 Tagen:** Fokus auf Quick Wins und operative Entlastung basierend auf den genannten "Zeitfressern & Prozess-Pain-Points".
- **Im 6–12 Monatszeitraum:** Maßnahmen festlegen, die das Zielbild ("Vision 2–3 Jahre") und die "Strategischen Prioritäten" systematisch vorbereiten.
- **Falls Geschäftsmodell-Ideen angegeben wurden:** zeige konkret, wie sie getestet und validiert werden können (MVP, Pilotkunden, Experimente).
- **Laufende oder geplante KI-Projekte:** integriere sie sinnvoll in die Roadmap, vermeide Doppelarbeit.
- **Wichtigste Leistung / Hauptprodukt:** alle Roadmap-Maßnahmen sollten letztlich diesen Kernprozess stärken oder effizienter machen.

---

"""

        # No specific instructions for other prompts
        return ""

    def _build_guardrails_instructions(
        self, prompt_name: str, strategic_context_block: str
    ) -> str:
        """
        Build prompt-specific guardrails/no-gos instructions.

        These instructions ensure that LLM outputs respect any no-gos or
        guardrails specified by the user in their strategic context.

        Args:
            prompt_name: Name of the prompt (e.g., 'risks', 'org_change')
            strategic_context_block: The strategic context string

        Returns:
            Formatted guardrails instruction string, or empty string if not applicable
        """
        # Return empty if no strategic context or no guardrails mentioned
        if not strategic_context_block or strategic_context_block.strip() == "":
            return ""

        # Check if guardrails/no-gos are mentioned in the strategic context
        # Extended keyword list for intelligent detection (v4.0)
        guardrails_keywords = [
            # Original keywords
            "no-gos", "leitplanken", "no gos", "rote linien", "sensible themen",
            "tabu", "ausgeschlossen", "nicht erlaubt",
            # Extended keywords (v3.1)
            "heikel", "empfindlich", "kritisch", "bitte vermeiden",
            "nicht automatisieren", "nicht delegieren", "nicht kommunizieren",
            "nicht an ki auslagern", "unter keinen umständen",
            "nur menschlich entscheiden", "heikle themen",
            # A) Negative Verben + Objekte (v4.0)
            "nicht nutzen", "nicht verwenden", "nicht freigeben",
            "nicht veröffentlichen", "nicht ohne freigabe", "nicht ohne rücksprache",
            "nicht mit kunden teilen", "nicht extern speichern",
            # B) Phrasen zur Einschränkung / Vorsicht (v4.0)
            "nur manuell entscheiden", "nur intern verwenden", "vorsicht bei",
            "kritische themen", "empfindliche daten", "nicht ohne absprache",
            # C) Sensitive areas (v4.0)
            "personalentscheidungen", "bewerberdaten", "gesundheitsdaten",
            "teamkommunikation", "rechtsfragen", "kundenbeschwerden",
            "compliance-relevante", "personaldaten", "mitarbeiterdaten",
            "vertrauliche", "geheimhaltung", "datenschutz-kritisch",
        ]

        # Negation + Action detection (v4.0)
        negation_words = ["nicht", "kein", "keine", "ohne", "niemals", "nie"]
        action_words = [
            "automatisieren", "delegieren", "freigabe", "speichern", "teilen",
            "verwenden", "weitergeben", "veröffentlichen", "kommunizieren",
        ]

        context_lower = strategic_context_block.lower()

        # Check 1: Explicit keywords
        has_explicit_keyword = any(kw in context_lower for kw in guardrails_keywords)

        # Check 2: Negation + Action combination
        has_negation = any(neg in context_lower for neg in negation_words)
        has_action = any(act in context_lower for act in action_words)
        has_negation_action = has_negation and has_action

        has_guardrails = has_explicit_keyword or has_negation_action

        if not has_guardrails:
            return ""

        prompt_lower = prompt_name.lower()

        # a) Risk/Compliance prompts
        RISK_COMPLIANCE_KEYWORDS = [
            "compliance",
            "risikoanalyse",
            "risiko",
            "risk",
            "risks",
            "ai_act",
            "dsgvo",
            "datenschutz",
        ]
        if any(kw in prompt_lower for kw in RISK_COMPLIANCE_KEYWORDS):
            return """
## Leitplanken & No-Gos (verbindlich zu beachten)

- **Keine Empfehlung darf** irgendeinem der genannten No-Gos widersprechen.
- **Wenn eine gute Praxis im Konflikt mit einer Leitplanke steht:** benenne den Konflikt und schlage eine sichere Alternative vor.
- **Erkläre Risiken immer im Kontext** der angegebenen Leitplanken.
- **Erwähne die Leitplanken ausdrücklich,** wenn du Risiko-Minderungsmaßnahmen beschreibst.

---

"""

        # b) Change/Culture prompts
        CHANGE_CULTURE_KEYWORDS = [
            "change",
            "kultur",
            "akzeptanz",
            "team",
            "org_change",
            "organisation",
            "mitarbeiter",
        ]
        if any(kw in prompt_lower for kw in CHANGE_CULTURE_KEYWORDS):
            return """
## Hinweise zur Kommunikation im Rahmen der Leitplanken

- **Passe alle Change- und Kommunikationsbeispiele** an die angegebenen Leitplanken an.
- **Vermeide Aussagen,** die sensibel oder kritisch im Kontext der No-Gos wären.
- **Wenn Leitplanken Team- oder Betriebsrat-Sensitivität betreffen:** nutze besonders vorsichtige, neutrale Formulierungen.

---

"""

        # c) Executive Summary prompts
        EXECUTIVE_SUMMARY_KEYWORDS = [
            "summary",
            "executive",
            "management_summary",
            "zusammenfassung",
            "überblick",
        ]
        if any(kw in prompt_lower for kw in EXECUTIVE_SUMMARY_KEYWORDS):
            return """
## Leitplanken-Hinweis für Executive Summary

- **Falls Leitplanken angegeben sind:** formuliere einen knappen Hinweis darauf („Das Unternehmen legt besonderen Wert auf …").
- **Keine Details, keine Risiken** – nur eine sehr kurze Erwähnung als Rahmenbedingung.

---

"""

        # d) All other prompts - no specific guardrails instructions
        return ""

    def _build_short_label_instructions(self, briefing_data: Dict[str, Any]) -> str:
        """
        Sprint G2.4/G4.1: Build short-label instructions for redundancy reduction.

        Returns instruction block telling LLM to use short labels instead of
        repeating long-form branch/offering descriptions.

        Sprint G4.1: Now size-aware - uses Team/KMU perspective for non-Solo profiles.
        """
        # Determine language from briefing (robust: lang > LANG > sprache)
        lang_raw = briefing_data.get("lang") or briefing_data.get("LANG") or briefing_data.get("sprache") or "de"
        lang = "en" if str(lang_raw).lower().strip().startswith("en") else "de"
        short_labels = generate_short_labels(briefing_data, lang=lang)

        branch_label = short_labels.get("BRANCH_CORE_LABEL", "")
        offering_label = short_labels.get("OFFERING_LABEL", "")
        regulatory_label = short_labels.get("REGULATORY_LABEL", "")
        context_label = short_labels.get("BRANCH_CONTEXT_LABEL", "")  # G4.2

        if not branch_label:
            return ""

        # SPRINT G4.1: Determine size category for perspective
        size_raw = (briefing_data.get("unternehmensgroesse") or "").lower()
        if "solo" in size_raw or "1" in size_raw or "freiberuf" in size_raw:
            size_key = "solo"
            size_perspective_de = "als Einzelperson/Freiberufler"
            size_perspective_en = "as a solo professional"
        elif "team" in size_raw or "klein" in size_raw or "2" in size_raw:
            size_key = "team"
            size_perspective_de = "als kleines Team (2-10 Personen)"
            size_perspective_en = "as a small team (2-10 people)"
        else:
            size_key = "kmu"
            size_perspective_de = "als KMU/Unternehmen"
            size_perspective_en = "as an SME/company"

        if lang == "en":
            # FIX: Ensure labels are not empty
            branch_label_safe = branch_label or "Your Industry"
            offering_label_safe = offering_label or "Your Core Services"
            context_label_safe = context_label or "Your Business"

            instructions = f"""
## Anti-Redundancy: Use Short Labels (Sprint G4)

**IMPORTANT: The following labels are for reference only - do NOT output them literally!**
**Use natural language with these concepts instead:**
- Industry: {branch_label_safe}
- Service Area: {offering_label_safe}
- Context: {context_label_safe}
"""
            if regulatory_label:
                instructions += f"- **Compliance:** {regulatory_label}\n"

            instructions += f"""
**SIZE PERSPECTIVE:** Write from the perspective of {size_perspective_en}.
"""
            if size_key != "solo":
                instructions += """
- Use collective language: "Your team...", "Your organization...", "Your company..."
- NEVER use solo-specific terms like "as an individual", "solo entrepreneur", "freelancer"
"""
            instructions += """
**IMPORTANT - Anti-Redundancy Rules:**
- Never repeat full branch/offering descriptions (>12 words)
- Use short labels above instead
- The strategic context block already contains the full description

**CROSS-SECTION REDUNDANCY (Sprint G6):**
- **Executive Summary:** Max 1 sentence per topic. Details in subsequent chapters.
- **Never copy entire paragraphs** from other sections.
- **Subsequent chapters:** Do NOT repeat opening sentences from Executive Summary.
- **Use cross-references:** "→ see [Section]" instead of repeating content.

---

"""
        else:
            # FIX: Sicherstellen dass Labels nicht leer sind
            branch_label_safe = branch_label or "Ihr Fachbereich"
            offering_label_safe = offering_label or "Ihre Kernleistung"
            context_label_safe = context_label or "Ihr Geschäftsbereich"

            instructions = f"""
## Anti-Redundanz: Kurzlabels verwenden (Sprint G4)

**WICHTIG: Die folgenden Labels dienen nur als Referenz - gib sie NICHT wortwörtlich im Output aus!**
**Nutze stattdessen natürliche Formulierungen mit diesen Begriffen:**
- Branche: {branch_label_safe}
- Leistungsbereich: {offering_label_safe}
- Kontext: {context_label_safe}
"""
            if regulatory_label:
                instructions += f"- **Compliance:** {regulatory_label}\n"

            instructions += f"""
**GRÖSSENPERSPEKTIVE:** Schreibe aus der Perspektive {size_perspective_de}.
"""
            if size_key != "solo":
                instructions += """
- Verwende kollektive Sprache: "Ihr Team...", "Ihre Organisation...", "Ihr Unternehmen..."
- NIEMALS Solo-spezifische Begriffe wie "als Einzelperson", "Solo-Selbstständige", "Freiberufler"
"""
            instructions += """
**WICHTIG - Anti-Redundanz-Regeln:**
- Wiederhole niemals vollständige Branchen- oder Leistungsbeschreibungen (>12 Wörter)
- Nutze stattdessen die Kurzlabels oben
- Der strategische Kontextblock enthält bereits die ausführliche Beschreibung

**KAPITELÜBERGREIFENDE REDUNDANZ (Sprint G6):**
- **Executive Summary:** Maximal 1 Satz pro Thema. Detailtiefe in Folgekapiteln.
- **Niemals ganze Absätze** aus anderen Kapiteln kopieren.
- **Folgekapitel:** NICHT mit Satz-Wiederholung aus Exec-Summary beginnen.
- **Querverweise nutzen:** „→ siehe [Abschnitt]" statt Inhalte zu wiederholen.

---

"""
        return instructions

    def _build_tools_whitelist_context(self, briefing_data: Dict[str, Any]) -> str:
        """
        Build tools whitelist context for tools_empfehlungen prompt.

        FIX-TOOL-WHITELIST: Injects allowed tool categories and considers
        vorhandene_tools (user's existing tools).

        Args:
            briefing_data: Complete briefing data

        Returns:
            Formatted tools context for prompt injection
        """
        try:
            from services.tool_whitelist import get_tools_context_for_prompt
        except ImportError:
            log.warning("[TOOL-WHITELIST] Could not import tool_whitelist module")
            return ""

        # Get company size
        company_size = briefing_data.get("COMPANY_SIZE", "").lower() or "team"
        if not company_size or company_size not in ("solo", "team", "kmu"):
            ug = str(briefing_data.get("unternehmensgroesse", "")).lower()
            if "solo" in ug or "1" == ug or "freiberuf" in ug:
                company_size = "solo"
            elif "2-10" in ug or "2–10" in ug or "klein" in ug:
                company_size = "team"
            else:
                company_size = "kmu"

        # Get branch
        branch = briefing_data.get("branche_engine_key", "") or briefing_data.get("branche", "")

        # Get vorhandene_tools
        vorhandene_tools = (
            briefing_data.get("VORHANDENE_TOOLS_LABELS", "")
            or briefing_data.get("vorhandene_tools", "")
            or ""
        )

        # Get language
        lang_raw = briefing_data.get("lang", "") or briefing_data.get("LANG", "") or "de"
        lang = "en" if str(lang_raw).lower().startswith("en") else "de"

        try:
            context = get_tools_context_for_prompt(
                size=company_size,
                branch=branch,
                vorhandene_tools=vorhandene_tools,
                lang=lang
            )

            if context:
                log.debug(
                    "[TOOL-WHITELIST] Injected tools context: size=%s branch=%s vorhandene=%d chars",
                    company_size, branch, len(vorhandene_tools)
                )
                return f"\n{context}\n\n---\n\n"

        except Exception as e:
            log.warning("[TOOL-WHITELIST] Failed to build tools context: %s", e)

        return ""

    def enhance_prompt(self, prompt_name: str, briefing_data: Dict[str, Any]) -> str:
        """
        Load a prompt and inject context.

        This method:
        1. Loads the base prompt from /prompts/de/ via prompt_loader
        2. Injects strategic context block into ALL prompts (from user freetext answers)
        3. Builds additional context block from branch/size contexts (for whitelisted prompts)
        4. Applies roadmap constraints for roadmap prompts
        5. FIX-TOOL-WHITELIST: Injects tools whitelist for tools_empfehlungen
        6. Returns the enhanced prompt

        Args:
            prompt_name: Name of the prompt (e.g., 'quick_wins')
            briefing_data: Complete briefing data including strategic_context_block

        Returns:
            Enhanced prompt with injected context
        """
        # Only these prompts get ADDITIONAL branch/size context block (v4.0 extended)
        # PLATIN++ V5: All SIZE-AWARE prompts should be in this list
        PROMPTS_WITH_BRANCH_SIZE_CONTEXT = {
            "unternehmensprofil_markt",  # Main profile page - needs context
            # Extended whitelist (v4.0)
            "quick_wins",               # Quick Wins benefit from branch-specific context
            "roadmap",                  # Roadmap needs size constraints
            "roadmap_90d",              # 90-day roadmap
            "roadmap_12m",              # 12-month roadmap
            "risk",                     # Risk analysis benefits from industry context
            "risks",                    # Alternative name
            "compliance",               # Compliance needs branch-specific regulations
            "change_management",        # Change management varies by size
            "executive_summary",        # Summary should reflect branch/size
            # Neue Sektionen (Sprint 2025) - persona-aware
            "monetarisierung",          # Pricing-Modelle anpassbar an Solo/Team/KMU
            "ki_skillplan",             # Skill-Entwicklung nach Unternehmensgröße
            "templates_start",          # Templates für Solo/Team/KMU unterschiedlich
            # Neue Sektionen (Sprint 2025 - Phase 2) - persona-aware
            "roi_tracking",             # Erfolgs-Tracking nach Unternehmensgröße
            "ai_policy_mini",           # Policy-Regeln nach Komplexität
            "kickoff_vorlage",          # Kickoff-Agenda nach Team-Größe
            "prompt_framework",         # Prompt-Anleitung nach Erfahrungslevel
            # PLATIN++ V5 Integration Check - Missing SIZE-AWARE prompts added
            "business_case",            # ROI/Payback nach Unternehmensgröße
            "gamechanger",              # Transformation nach Solo/Team/KMU
            "foerderpotenzial",         # Förderprogramme nach Größe
            "tools_empfehlungen",       # Tool-Empfehlungen nach Komplexität
            "strategie_governance",     # Governance nach Organisationsgröße
            "strategy_governance",      # EN alternative name
            "wettbewerb_benchmark",     # Wettbewerbsanalyse nach Marktposition
            "competition_benchmark",    # EN alternative name
            "org_change",               # Change Management nach Teamgröße
            "next_actions",             # Nächste Schritte nach Priorität
            "costs_overview",           # Kostenübersicht nach Budget
            "ai_act_summary",           # AI Act nach Risikoklasse
            "recommendations",          # Empfehlungen nach Kontext
            "technologie_prozesse",     # RUN-625: Fehlte! Technologie nach IT-Infrastruktur
            "data_readiness",           # RUN-625: Datenreife nach Infrastruktur
            "ki_aktivitaeten_ziele",    # RUN-625: KI-Aktivitäten nach Erfahrung
            "transparency_box",         # RUN-625: Transparenz-Box
            "branch_deep_dive",         # RUN-625: Branch Deep Dive
        }

        try:
            from services.prompt_loader import load_prompt

            # TEIL 3.1.4.x: Dynamic language from briefing_data
            lang_raw = briefing_data.get("lang") or briefing_data.get("LANG") or "de"
            lang = str(lang_raw).lower().strip()
            prompt_lang = "en" if lang.startswith("en") else "de"

            base_prompt = load_prompt(prompt_name, lang=prompt_lang, vars_dict=None)

            if not isinstance(base_prompt, str):
                log.warning(
                    "⚠️ Prompt '%s' returned non-string type: %s",
                    prompt_name,
                    type(base_prompt),
                )
                return str(base_prompt)

            # === STEP 1: Inject strategic context block into ALL prompts ===
            # This is the user's own strategic input - always include it
            strategic_block = self._build_strategic_context_prompt_block(briefing_data)
            strategic_context_raw = briefing_data.get("strategic_context_block", "")

            # === STEP 1b: Add prompt-specific alignment instructions ===
            # For Quick Wins and Roadmaps, add specific instructions on HOW to use the context
            alignment_instructions = self._build_strategic_alignment_instructions(
                prompt_name, briefing_data
            )

            # === STEP 1c: Add guardrails/no-gos instructions ===
            # For Risk, Change, Executive prompts, add specific guardrails handling
            guardrails_instructions = self._build_guardrails_instructions(
                prompt_name, strategic_context_raw
            )

            # === STEP 1d: Add short-label instructions (Sprint G2.4) ===
            # Reduces redundancy by telling LLM to use compact labels
            short_label_instructions = self._build_short_label_instructions(briefing_data)

            # === STEP 1e: Add tools whitelist context (FIX-TOOL-WHITELIST) ===
            # For tools_empfehlungen, inject allowed categories and vorhandene_tools
            tools_whitelist_context = ""
            if prompt_name == "tools_empfehlungen":
                tools_whitelist_context = self._build_tools_whitelist_context(briefing_data)

            # Combine: strategic block + alignment + guardrails + short-labels + tools whitelist
            full_context_injection = (
                strategic_block + alignment_instructions + guardrails_instructions +
                short_label_instructions + tools_whitelist_context
            )

            # Find the best injection point: after Developer comment, before HTML
            # Look for the end of the Developer comment block
            import re

            # Try to find the end of the Developer comment (-->)
            comment_end_match = re.search(r"-->\s*\n", base_prompt)
            if comment_end_match:
                # Inject after the Developer comment
                inject_pos = comment_end_match.end()
                enhanced = (
                    base_prompt[:inject_pos]
                    + "\n"
                    + full_context_injection
                    + base_prompt[inject_pos:]
                )
                log.debug(
                    "✅ Injected strategic context after Developer comment in '%s'",
                    prompt_name,
                )
                if alignment_instructions:
                    log.debug(
                        "✅ Added strategic alignment instructions for '%s'",
                        prompt_name,
                    )
                if guardrails_instructions:
                    log.debug(
                        "✅ Added guardrails/no-gos instructions for '%s'",
                        prompt_name,
                    )
            else:
                # No Developer comment found - prepend to the prompt
                enhanced = full_context_injection + base_prompt
                log.debug(
                    "⚠️ No Developer comment found, prepended strategic context to '%s'",
                    prompt_name,
                )

            # === STEP 2: Apply roadmap constraints if applicable ===
            ROADMAP_PROMPTS = {"roadmap", "roadmap_12m", "pilot_plan", "roadmap_90d"}
            if prompt_name in ROADMAP_PROMPTS:
                log.info("🎯 Applying roadmap size constraints for '%s'", prompt_name)
                enhanced = enhance_roadmap_prompt(enhanced, briefing_data)

            # === STEP 3: Add branch/size context for whitelisted prompts ===
            if prompt_name in PROMPTS_WITH_BRANCH_SIZE_CONTEXT:
                context_block = self.build_context_block(briefing_data)

                # Kontext injizieren
                if "{CONTEXT_BLOCK}" in enhanced:
                    enhanced = enhanced.replace("{CONTEXT_BLOCK}", context_block)
                    log.info("✅ Injected branch/size context block into prompt '%s'", prompt_name)
                else:
                    match = re.search(
                        r"(<(?:section|div)[^>]*>)", enhanced, re.IGNORECASE
                    )
                    if match is not None:
                        pos = match.end()
                        enhanced = (
                            enhanced[:pos]
                            + "\n"
                            + context_block
                            + "\n"
                            + enhanced[pos:]
                        )
                        log.debug(
                            "✅ Prepended branch/size context block to prompt '%s'",
                            prompt_name,
                        )
                    else:
                        # Add at end before </section> or at absolute end
                        section_end_match = re.search(r"</section>\s*$", enhanced, re.IGNORECASE)
                        if section_end_match:
                            pos = section_end_match.start()
                            enhanced = enhanced[:pos] + context_block + "\n" + enhanced[pos:]
                        else:
                            enhanced = enhanced + "\n" + context_block
                        log.debug(
                            "⚠️ No suitable injection point found, appended branch/size context to '%s'",
                            prompt_name,
                        )
            else:
                log.debug(
                    "⏭️  Skipping branch/size context for '%s' (not in whitelist)", prompt_name
                )

            return enhanced

        except FileNotFoundError as exc:
            log.error("❌ Prompt file not found for '%s': %s", prompt_name, exc)
            raise
        except Exception as exc:  # pragma: no cover - defensive
            log.error("❌ Failed to enhance prompt '%s': %s", prompt_name, exc)
            raise

    def get_context_summary(self, briefing_data: Dict[str, Any]) -> str:
        """
        Get a plain text summary of the context (for debugging).

        Args:
            briefing_data: Briefing data

        Returns:
            Plain text summary
        """
        return self.builder.build_context_summary(briefing_data)


# =============================================================================
# SPRINT G17.2-B: SMART DEFAULTS FOR PROMPT ENGINE
# =============================================================================
#
# Automatically adjusts prompting based on what has worked for real reports.
# Analyzes segment feedback to optimize:
# - Roadmap lengths (based on "too short" warning frequency)
# - Branch-specific phrases (based on warning patterns)
# - Cost ranges for business case (based on CAPEX/OPEX trends)
# =============================================================================

import os
from datetime import datetime
from typing import Tuple

# Smart Defaults Configuration
PROMPT_SMART_DEFAULTS_ENABLED = os.environ.get("PROMPT_SMART_DEFAULTS_ENABLED", "1") == "1"
PROMPT_DEFAULT_WORD_INCREASE_FACTOR = float(os.environ.get("PROMPT_DEFAULT_WORD_INCREASE_FACTOR", "1.12"))

# G17.5: Prompt Tuner Integration
try:
    from services.prompt_tuner import (
        PROMPT_TUNER_ENABLED,
        get_tuning_profile as _get_tuning_profile,
        TuningProfile,
    )
    _TUNER_AVAILABLE = True
except ImportError:
    _TUNER_AVAILABLE = False
    PROMPT_TUNER_ENABLED = False

# Cache for smart defaults analysis
_smart_defaults_cache: Dict[str, Any] = {
    "last_refresh": None,
    "adjustments": {},
    "analysis_results": {},
}

SMART_DEFAULTS_CACHE_TTL_SECONDS = 3600  # 1 hour


@dataclass
class SmartDefaultAdjustment:
    """A single smart default adjustment."""
    adjustment_type: str  # word_count, phrase, cost_range
    target_section: str  # roadmap_90d, business_case, etc.
    original_value: Any
    adjusted_value: Any
    reason: str
    segment_key: Optional[str] = None
    confidence: float = 0.5


class SmartDefaultsEngine:
    """
    Engine for applying smart defaults to prompts based on segment feedback.

    G17.2-B: Automatically optimizes prompts based on real-world performance.
    """

    def __init__(self) -> None:
        self.adjustments: List[SmartDefaultAdjustment] = []
        self._load_segment_analysis()

    def _load_segment_analysis(self) -> None:
        """Load segment analysis data for smart defaults."""
        if not PROMPT_SMART_DEFAULTS_ENABLED:
            return

        global _smart_defaults_cache

        # Check cache freshness
        if _smart_defaults_cache["last_refresh"]:
            age = (datetime.now() - _smart_defaults_cache["last_refresh"]).total_seconds()
            if age < SMART_DEFAULTS_CACHE_TTL_SECONDS:
                return

        try:
            from services.feedback_analyzer import build_segments_snapshot

            snapshot = build_segments_snapshot(days=30, force=False)
            _smart_defaults_cache["analysis_results"] = self._analyze_segments(snapshot)
            _smart_defaults_cache["last_refresh"] = datetime.now()
            log.debug("Smart defaults cache refreshed")

        except Exception as e:
            log.warning(f"Failed to load segment analysis for smart defaults: {e}")

    def _analyze_segments(self, snapshot: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze segments to determine optimal defaults."""
        analysis: Dict[str, Any] = {
            "word_count_adjustments": {},
            "phrase_preferences": {},
            "cost_range_adjustments": {},
            "total_segments_analyzed": len(snapshot),
        }

        for segment_key, stats in snapshot.items():
            # Analyze warning patterns
            top_warnings = getattr(stats, "top_warning_types", [])

            # Check for "too short" warnings
            for warning_type, count in top_warnings:
                if "min-word" in warning_type or "short" in warning_type.lower():
                    if count > 3:
                        # This segment frequently has too-short content
                        size_label = getattr(stats, "segment_key", ("", "", "", ""))[0]
                        if size_label not in analysis["word_count_adjustments"]:
                            analysis["word_count_adjustments"][size_label] = {
                                "factor": PROMPT_DEFAULT_WORD_INCREASE_FACTOR,
                                "affected_sections": ["roadmap_90d", "roadmap_12m", "quick_wins"],
                                "warning_count": count,
                            }

            # Check for persona mismatch warnings
            for warning_type, count in top_warnings:
                if "persona" in warning_type.lower() and count > 2:
                    size_label = getattr(stats, "segment_key", ("", "", "", ""))[0]
                    analysis["phrase_preferences"][size_label] = {
                        "avoid_patterns": self._get_problematic_phrases(warning_type),
                        "warning_count": count,
                    }

            # Analyze cost trends from segment
            avg_roi = getattr(stats, "avg_roi_percent", 0)
            if avg_roi > 0:
                size_label = getattr(stats, "segment_key", ("", "", "", ""))[0]
                analysis["cost_range_adjustments"][size_label] = {
                    "avg_roi": avg_roi,
                    "suggested_multiplier": 1.0 + (avg_roi / 1000),  # Subtle adjustment
                }

        return analysis

    def _get_problematic_phrases(self, warning_type: str) -> List[str]:
        """Get list of phrases that may cause issues for a warning type."""
        # Default problematic phrases for persona mismatches
        if "solo" in warning_type.lower():
            return ["team", "mitarbeiter", "abteilung"]
        if "team" in warning_type.lower():
            return ["solo", "einzelperson"]
        return []

    def get_word_count_adjustment(
        self,
        section_name: str,
        size: str,
        base_min_words: int,
    ) -> Tuple[int, Optional[SmartDefaultAdjustment]]:
        """
        Get adjusted word count for a section based on segment analysis.

        Args:
            section_name: Name of the section
            size: Company size (solo/team/kmu)
            base_min_words: Base minimum word count

        Returns:
            Tuple of (adjusted_min_words, adjustment_record or None)
        """
        if not PROMPT_SMART_DEFAULTS_ENABLED:
            return base_min_words, None

        analysis = _smart_defaults_cache.get("analysis_results", {})
        word_adjustments = analysis.get("word_count_adjustments", {})

        size_lower = size.lower() if size else "team"
        adjustment_data = word_adjustments.get(size_lower)

        if not adjustment_data:
            return base_min_words, None

        # Check if this section is affected
        affected_sections = adjustment_data.get("affected_sections", [])
        if section_name not in affected_sections:
            return base_min_words, None

        # Apply adjustment
        factor = adjustment_data.get("factor", PROMPT_DEFAULT_WORD_INCREASE_FACTOR)
        adjusted = int(base_min_words * factor)

        adjustment = SmartDefaultAdjustment(
            adjustment_type="word_count",
            target_section=section_name,
            original_value=base_min_words,
            adjusted_value=adjusted,
            reason=f"Segment '{size_lower}' hatte {adjustment_data.get('warning_count', 0)}x 'too short' Warnings",
            segment_key=size_lower,
            confidence=min(0.8, 0.5 + adjustment_data.get("warning_count", 0) / 20),
        )

        self.adjustments.append(adjustment)
        log.debug(f"Smart default: Increased min_words for {section_name} from {base_min_words} to {adjusted}")

        return adjusted, adjustment

    def get_phrase_preferences(
        self,
        size: str,
        branch: str,
    ) -> Dict[str, Any]:
        """
        Get phrase preferences based on segment analysis.

        Args:
            size: Company size
            branch: Industry branch

        Returns:
            Dict with phrase preferences (avoid_patterns, preferred_patterns)
        """
        if not PROMPT_SMART_DEFAULTS_ENABLED:
            return {}

        analysis = _smart_defaults_cache.get("analysis_results", {})
        phrase_prefs = analysis.get("phrase_preferences", {})

        size_lower = size.lower() if size else "team"
        prefs: Dict[str, Any] = phrase_prefs.get(size_lower, {})

        if prefs:
            log.debug(f"Smart default: Applied phrase preferences for size={size_lower}")

        return prefs

    def get_cost_range_adjustment(
        self,
        size: str,
        base_capex_max: int,
        base_opex_max: int,
    ) -> Tuple[int, int, Optional[SmartDefaultAdjustment]]:
        """
        Get adjusted cost ranges based on segment trends.

        Args:
            size: Company size
            base_capex_max: Base CAPEX maximum
            base_opex_max: Base OPEX maximum

        Returns:
            Tuple of (adjusted_capex, adjusted_opex, adjustment_record or None)
        """
        if not PROMPT_SMART_DEFAULTS_ENABLED:
            return base_capex_max, base_opex_max, None

        analysis = _smart_defaults_cache.get("analysis_results", {})
        cost_adjustments = analysis.get("cost_range_adjustments", {})

        size_lower = size.lower() if size else "team"
        adjustment_data = cost_adjustments.get(size_lower)

        if not adjustment_data:
            return base_capex_max, base_opex_max, None

        multiplier = adjustment_data.get("suggested_multiplier", 1.0)

        # Apply subtle adjustments
        adjusted_capex = int(base_capex_max * multiplier)
        adjusted_opex = int(base_opex_max * multiplier)

        if multiplier != 1.0:
            adjustment = SmartDefaultAdjustment(
                adjustment_type="cost_range",
                target_section="business_case",
                original_value={"capex": base_capex_max, "opex": base_opex_max},
                adjusted_value={"capex": adjusted_capex, "opex": adjusted_opex},
                reason=f"Segment zeigt durchschnittlichen ROI von {adjustment_data.get('avg_roi', 0):.0f}%",
                segment_key=size_lower,
                confidence=0.6,
            )
            self.adjustments.append(adjustment)
            log.debug(f"Smart default: Adjusted cost ranges by {multiplier:.2f}x for size={size_lower}")
            return adjusted_capex, adjusted_opex, adjustment

        return base_capex_max, base_opex_max, None

    def get_all_adjustments(self) -> List[Dict[str, Any]]:
        """Get all adjustments made in this session."""
        return [
            {
                "adjustment_type": a.adjustment_type,
                "target_section": a.target_section,
                "original_value": a.original_value,
                "adjusted_value": a.adjusted_value,
                "reason": a.reason,
                "segment_key": a.segment_key,
                "confidence": a.confidence,
            }
            for a in self.adjustments
        ]

    def reset_adjustments(self) -> None:
        """Reset adjustment tracking for new report."""
        self.adjustments = []

    # =========================================================================
    # G17.5: PROMPT TUNER INTEGRATION
    # =========================================================================

    def get_tuning_adjusted_values(
        self,
        prompt_file: str,
        section_id: str,
        segment_key: str,
        base_min_words: int,
        base_persona_strictness: float = 1.0,
    ) -> Dict[str, Any]:
        """
        Get tuning-adjusted values from the Prompt Tuner (G17.5).

        Args:
            prompt_file: Path to the prompt file
            section_id: Section identifier
            segment_key: Full segment key (e.g., "solo|beratung|minimal|DE")
            base_min_words: Base minimum word count
            base_persona_strictness: Base persona strictness

        Returns:
            Dict with adjusted values:
            - min_words: Adjusted minimum word count
            - emphasis_weights: Dict of emphasis weights
            - redundancy_sensitivity: Adjusted redundancy sensitivity
            - persona_strictness: Adjusted persona guard strength
            - tuning_applied: Boolean indicating if tuning was applied
        """
        result = {
            "min_words": base_min_words,
            "emphasis_weights": {},
            "redundancy_sensitivity": 1.0,
            "persona_strictness": base_persona_strictness,
            "tuning_applied": False,
        }

        if not _TUNER_AVAILABLE or not PROMPT_TUNER_ENABLED:
            return result

        try:
            profile = _get_tuning_profile(prompt_file, section_id, segment_key)

            # Apply target_word_factor
            result["min_words"] = int(base_min_words * profile.target_word_factor)

            # Apply emphasis_weights
            result["emphasis_weights"] = profile.emphasis_weights.copy()

            # Apply redundancy_sensitivity
            result["redundancy_sensitivity"] = profile.redundancy_sensitivity

            # Apply persona_strictness (combined with base)
            result["persona_strictness"] = base_persona_strictness * profile.persona_strictness

            # Mark that tuning was applied if any value differs from default
            if (
                profile.target_word_factor != 1.0 or
                profile.emphasis_weights or
                profile.redundancy_sensitivity != 1.0 or
                profile.persona_strictness != 1.0
            ):
                result["tuning_applied"] = True

                # Record adjustment
                self.adjustments.append(SmartDefaultAdjustment(
                    adjustment_type="tuner_profile",
                    target_section=section_id,
                    original_value={
                        "min_words": base_min_words,
                        "persona_strictness": base_persona_strictness,
                    },
                    adjusted_value={
                        "min_words": result["min_words"],
                        "persona_strictness": result["persona_strictness"],
                        "redundancy_sensitivity": result["redundancy_sensitivity"],
                    },
                    reason=f"G17.5 Tuner profile applied (source: {profile.source})",
                    segment_key=segment_key,
                    confidence=0.7 if profile.source == "auto" else 0.9,
                ))

                log.debug(
                    f"[G17.5] Applied tuning for {section_id}: "
                    f"word_factor={profile.target_word_factor:.2f}, "
                    f"redundancy={profile.redundancy_sensitivity:.2f}"
                )

        except Exception as e:
            log.warning(f"[G17.5] Failed to get tuning profile: {e}")

        return result


# Global smart defaults engine instance
_smart_defaults_engine: Optional[SmartDefaultsEngine] = None


def get_smart_defaults_engine() -> SmartDefaultsEngine:
    """Get the global smart defaults engine instance."""
    global _smart_defaults_engine
    if _smart_defaults_engine is None:
        _smart_defaults_engine = SmartDefaultsEngine()
    return _smart_defaults_engine


def apply_smart_defaults_to_prompt(
    prompt_text: str,
    section_name: str,
    briefing_data: Dict[str, Any],
) -> str:
    """
    Apply smart defaults to a prompt based on segment analysis.

    G17.2-B: Main entry point for smart defaults application.

    Args:
        prompt_text: Original prompt text
        section_name: Name of the section
        briefing_data: Briefing data with size, branch, etc.

    Returns:
        Enhanced prompt with smart defaults applied
    """
    if not PROMPT_SMART_DEFAULTS_ENABLED:
        return prompt_text

    engine = get_smart_defaults_engine()

    size = briefing_data.get("unternehmensgroesse", "team")
    branch = briefing_data.get("branche", "")

    enhanced = prompt_text
    modifications = []

    # 1. Apply word count adjustments
    base_min_words = get_platin_min_words(section_name, size)
    if base_min_words > 0:
        adjusted_words, adjustment = engine.get_word_count_adjustment(
            section_name, size, base_min_words
        )
        if adjustment and adjusted_words != base_min_words:
            # Inject word count hint into prompt
            word_hint = f"\n\n[SMART DEFAULT: Mindestens {adjusted_words} Wörter für diese Sektion (angepasst basierend auf Segment-Performance)]\n"
            enhanced = word_hint + enhanced
            modifications.append("word_count")

    # 2. Apply phrase preferences
    phrase_prefs = engine.get_phrase_preferences(size, branch)
    if phrase_prefs.get("avoid_patterns"):
        avoid_list = ", ".join(phrase_prefs["avoid_patterns"])
        phrase_hint = f"\n\n[SMART DEFAULT: Vermeide folgende Begriffe basierend auf Segment-Feedback: {avoid_list}]\n"
        enhanced = phrase_hint + enhanced
        modifications.append("phrase_preferences")

    if modifications:
        log.info(f"Smart defaults applied to {section_name}: {modifications}")

    return enhanced


def get_smart_defaults_analysis() -> Dict[str, Any]:
    """
    Get current smart defaults analysis for dashboard.

    Returns:
        Dict with analysis results and statistics
    """
    if not PROMPT_SMART_DEFAULTS_ENABLED:
        return {"enabled": False}

    engine = get_smart_defaults_engine()
    analysis = _smart_defaults_cache.get("analysis_results", {})

    return {
        "enabled": True,
        "last_refresh": _smart_defaults_cache.get("last_refresh", "").isoformat() if _smart_defaults_cache.get("last_refresh") else None,
        "total_segments_analyzed": analysis.get("total_segments_analyzed", 0),
        "word_count_adjustments": analysis.get("word_count_adjustments", {}),
        "phrase_preferences": analysis.get("phrase_preferences", {}),
        "cost_range_adjustments": analysis.get("cost_range_adjustments", {}),
        "recent_adjustments": engine.get_all_adjustments()[-20:],  # Last 20 adjustments
    }


def get_smart_defaults_statistics() -> Dict[str, Any]:
    """
    Get statistics about smart defaults usage.

    Returns:
        Dict with usage statistics
    """
    engine = get_smart_defaults_engine()
    adjustments = engine.get_all_adjustments()

    by_type: Dict[str, int] = {}
    by_section: Dict[str, int] = {}

    for adj in adjustments:
        adj_type = adj["adjustment_type"]
        section = adj["target_section"]

        by_type[adj_type] = by_type.get(adj_type, 0) + 1
        by_section[section] = by_section.get(section, 0) + 1

    return {
        "total_adjustments": len(adjustments),
        "by_type": by_type,
        "by_section": by_section,
        "enabled": PROMPT_SMART_DEFAULTS_ENABLED,
    }


# =============================================================================
# MODULE INITIALIZATION
# =============================================================================

log.info(
    "[G17.2-B] Smart Defaults loaded - enabled=%s, word_increase_factor=%s",
    PROMPT_SMART_DEFAULTS_ENABLED,
    PROMPT_DEFAULT_WORD_INCREASE_FACTOR,
)


if __name__ == "__main__":  # pragma: no cover - manual test harness
    logging.basicConfig(level=logging.DEBUG)

    enhancer = PromptEnhancer(data_dir="data")

    test_briefing: Dict[str, Any] = {
        "branche": "beratung",
        "unternehmensgroesse": "solo",
        "hauptleistung": "Beratung von Unternehmen zur Integration von KI",
    }

    context_block = enhancer.build_context_block(test_briefing)
    print("=" * 80)
    print("CONTEXT BLOCK (HTML):")
    print("=" * 80)
    print(context_block)
    print("=" * 80)

    summary = enhancer.get_context_summary(test_briefing)
    print("\nCONTEXT SUMMARY (TEXT):")
    print("=" * 80)
    print(summary)
    print("=" * 80)

    print("\n" + "=" * 80)
    print("WHITELIST TEST:")
    print("=" * 80)

    for prompt_name in ["unternehmensprofil_markt", "quick_wins", "executive_summary"]:
        try:
            enhanced = enhancer.enhance_prompt(prompt_name, test_briefing)
            has_context = ("Branchen-Context:" in enhanced) or ("Industry Context:" in enhanced)
            print(f"✅ {prompt_name}: Context={'YES ✓' if has_context else 'NO ✗'}")
        except Exception as exc:
            print(f"❌ {prompt_name}: Error - {exc}")
