# -*- coding: utf-8 -*-
"""
N4.3: Safety Assurance Layer v3
===============================

PLATIN+++ v5.3 - Enterprise Safety Layer

Comprehensive safety assurance for AI-generated content:
- Toxicity filtering
- Vendor-authority masking
- Compliance phrase detection and removal
- Governance conflict detection and auto-correction

Self-healing: Automatically corrects safety violations without fallbacks.

Multi-language support: DE, EN, FR, IT, ES

Version: 1.0.0 (N4.3 - PLATIN+++ v5.3)
Author: Claude + Wolf
"""

from __future__ import annotations

import hashlib
import logging
import re
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Pattern, Set, Tuple

from services.types import SectionDict, BriefingDict
from services.language_strategy_engine import SupportedLanguage

log = logging.getLogger(__name__)

__all__ = [
    "SafetyViolationType",
    "SafetySeverity",
    "SafetyViolation",
    "SafetyCheckResult",
    "SafetyAssuranceLayerV3",
    "check_content_safety",
    "filter_toxicity",
    "mask_vendor_authority",
    "detect_compliance_phrases",
    "detect_governance_conflicts",
    "heal_safety_violations",
    "validate_safety_compliance",
]


# =============================================================================
# ENUMS & CONSTANTS
# =============================================================================

class SafetyViolationType(Enum):
    """Types of safety violations."""
    TOXICITY = "toxicity"
    VENDOR_AUTHORITY = "vendor_authority"
    COMPLIANCE_PHRASE = "compliance_phrase"
    GOVERNANCE_CONFLICT = "governance_conflict"
    HALLUCINATION = "hallucination"
    PII_LEAK = "pii_leak"
    LEGAL_DISCLAIMER_MISSING = "legal_disclaimer_missing"
    UNSUBSTANTIATED_CLAIM = "unsubstantiated_claim"


class SafetySeverity(Enum):
    """Severity levels for safety violations."""
    CRITICAL = "critical"   # Must be resolved immediately
    HIGH = "high"           # Should be resolved before publication
    MEDIUM = "medium"       # Should be flagged for review
    LOW = "low"             # Informational


class ContentType(Enum):
    """Types of content sections."""
    EXECUTIVE = "executive"
    TECHNICAL = "technical"
    FINANCIAL = "financial"
    COMPLIANCE = "compliance"
    RECOMMENDATION = "recommendation"
    GENERAL = "general"


# Toxicity patterns by language
# KIS-1327: Die dritte Zeile je Sprache („garantiert", „zweifellos", „guaranteed"
# …) war kein Schimpfwort, wurde aber wie eines geheilt: Ersatz durch
# „[entfernt - unangemessener Inhalt]", den der Healer als Klammer-Platzhalter
# löscht. Ergebnis in Lauf KIS1296 (R1 S. 22): „… Rechteübertragung derzeit
# nicht ist." und in Lauf KIS1279 (KIS-1307): „… abgesicherte Datenhaltung ."
# Überzogene Sicherheit ist Sache der Prompts, nicht eines Wortfilters.
TOXICITY_PATTERNS: Dict[SupportedLanguage, List[str]] = {
    SupportedLanguage.DE: [
        r"\b(dumm|idiot|inkompetent|unfähig|versager|katastroph)\b",
        r"\b(schrecklich|furchtbar|miserabel|desaströs)\b",
    ],
    SupportedLanguage.EN: [
        r"\b(stupid|idiot|incompetent|failure|disaster)\b",
        r"\b(terrible|awful|miserable|disastrous)\b",
    ],
    SupportedLanguage.FR: [
        r"\b(stupide|idiot|incompétent|incapable|échec)\b",
        r"\b(terrible|affreux|misérable|désastreux)\b",
    ],
    SupportedLanguage.IT: [
        r"\b(stupido|idiota|incompetente|incapace|fallimento)\b",
        r"\b(terribile|orribile|miserabile|disastroso)\b",
    ],
    SupportedLanguage.ES: [
        r"\b(estúpido|idiota|incompetente|incapaz|fracaso)\b",
        r"\b(terrible|horrible|miserable|desastroso)\b",
    ],
}

# Vendor authority phrases that should be masked
# NOTE: Generic "Anbieter" pattern removed (v5.4) - caused grammatical case errors
#       (nominative "ein geeigneter" replaced accusative contexts).
#       Vendor neutrality is now enforced via prompts (PLATIN+++ v7.1).
VENDOR_AUTHORITY_PATTERNS: Dict[SupportedLanguage, List[Tuple[str, str]]] = {
    SupportedLanguage.DE: [
        # Pattern 1 REMOVED: "(nur)? (ein)? (spezifischer)? Anbieter (wie)? X" → grammar errors
        (r"(?:wir\s+)?empfehlen\s+(?:ausschließlich\s+)?(Microsoft|Google|Amazon|IBM|SAP|Oracle|Salesforce)(?:\s+als\s+Lösung)?", "wir empfehlen eine passende Lösung"),
        (r"(Microsoft|Google|Amazon|IBM|SAP|Oracle|Salesforce)\s+ist\s+(?:der\s+)?beste", "ein führender Anbieter bietet"),
        (r"(?:Sie\s+)?müssen\s+(?:unbedingt\s+)?(Microsoft|Google|Amazon|IBM|SAP|Oracle|Salesforce)\s+verwenden", "eine geeignete Lösung sollte gewählt werden"),
    ],
    SupportedLanguage.EN: [
        # KIS-1253 (Lauf 1132): generische Patterns entfernt — Spiegelung der
        # DE-v5.4-Entscheidung. "vendor \w+" traf JEDES "Vendor Audit"/"vendor
        # audit status" und zerstörte Überschriften ("a suitable vendor");
        # "recommend \w+" hätte jedes "recommend starting…" verstümmelt.
        # Vendor-Neutralität wird wie im DE-Pfad über Prompts erzwungen.
        (r"(?:we\s+)?recommend\s+(?:exclusively\s+)?(Microsoft|Google|Amazon|IBM|SAP|Oracle|Salesforce)(?:\s+as\s+a\s+solution)?", "we recommend a suitable solution"),
        (r"(?:Microsoft|Google|Amazon|IBM|SAP|Oracle|Salesforce)\s+is\s+(?:the\s+)?best", "a leading provider offers"),
        (r"(?:you\s+)?must\s+(?:definitely\s+)?use\s+(?:Microsoft|Google|Amazon|IBM|SAP|Oracle|Salesforce)\b", "a suitable solution should be chosen"),
    ],
    SupportedLanguage.FR: [
        (r"(?:un\s+)?fournisseur\s+(?:spécifique\s+)?(?:comme\s+)?\w+", "un fournisseur approprié"),
        (r"(?:nous\s+)?recommandons\s+(?:exclusivement\s+)?\w+", "nous recommandons une solution appropriée"),
    ],
    SupportedLanguage.IT: [
        (r"(?:un\s+)?fornitore\s+(?:specifico\s+)?(?:come\s+)?\w+", "un fornitore adatto"),
        (r"(?:raccomandiamo\s+)?(?:esclusivamente\s+)?\w+", "raccomandiamo una soluzione adatta"),
    ],
    SupportedLanguage.ES: [
        (r"(?:un\s+)?proveedor\s+(?:específico\s+)?(?:como\s+)?\w+", "un proveedor adecuado"),
        (r"(?:recomendamos\s+)?(?:exclusivamente\s+)?\w+", "recomendamos una solución adecuada"),
    ],
}

# Compliance phrases that should be removed (disclaimers that undermine authority)
COMPLIANCE_PHRASES: Dict[SupportedLanguage, List[str]] = {
    SupportedLanguage.DE: [
        r"wir können nicht garantieren",
        r"bitte wenden Sie sich an",
        r"dies ist keine rechtsverbindliche",
        r"wir übernehmen keine Haftung",
        r"ohne Gewähr",
        r"keine Beratung",
        r"konsultieren Sie einen Fachmann",
        r"auf eigene Gefahr",
        r"wir können keine Verantwortung übernehmen",
    ],
    SupportedLanguage.EN: [
        r"we cannot guarantee",
        r"please contact",
        r"this is not legally binding",
        r"we assume no liability",
        r"without warranty",
        r"not advice",
        r"consult a professional",
        r"at your own risk",
        r"we cannot take responsibility",
    ],
    SupportedLanguage.FR: [
        r"nous ne pouvons pas garantir",
        r"veuillez contacter",
        r"ceci n'est pas juridiquement",
        r"nous déclinons toute responsabilité",
        r"sans garantie",
        r"consultez un professionnel",
    ],
    SupportedLanguage.IT: [
        r"non possiamo garantire",
        r"si prega di contattare",
        r"questo non è legalmente vincolante",
        r"non ci assumiamo alcuna responsabilità",
        r"senza garanzia",
        r"consultare un professionista",
    ],
    SupportedLanguage.ES: [
        r"no podemos garantizar",
        r"por favor contacte",
        r"esto no es legalmente vinculante",
        r"no asumimos ninguna responsabilidad",
        r"sin garantía",
        r"consulte a un profesional",
    ],
}

# Governance conflict patterns
GOVERNANCE_CONFLICT_PATTERNS: Dict[str, Dict[str, List[str]]] = {
    "risk_understatement": {
        "high_risk_indicators": [
            r"high.?risk", r"hohes?\s+risiko", r"risque\s+élevé",
            r"alto\s+rischio", r"alto\s+riesgo",
        ],
        "low_risk_claims": [
            r"no\s+(?:protection|measures?)\s+(?:needed|required|necessary)",
            r"keine\s+(?:Schutz)?maßnahmen\s+(?:notwendig|erforderlich|nötig)",
            r"aucune\s+mesure\s+nécessaire",
            r"nessuna\s+misura\s+necessaria",
            r"ninguna\s+medida\s+necesaria",
        ],
    },
    "compliance_contradiction": {
        "non_compliant_indicators": [
            r"not\s+compliant", r"nicht\s+konform", r"non\s+conforme",
        ],
        "compliant_claims": [
            r"fully\s+compliant", r"vollständig\s+konform", r"entièrement\s+conforme",
        ],
    },
}

# PII patterns for detection
PII_PATTERNS: List[str] = [
    r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b",  # Email
    r"\b(?:\+49|0049|\+1|001|\+44|0044)\s*\d{3,4}[\s-]?\d{3,8}\b",  # Phone
    r"\b\d{5}\s+\w+(?:\s+\w+)?\b",  # German postal code + city
    r"\bDE\d{2}\s*\d{4}\s*\d{4}\s*\d{4}\s*\d{4}\s*\d{2}\b",  # IBAN
]

# Replacement templates for healed content
HEALING_TEMPLATES: Dict[SafetyViolationType, Dict[SupportedLanguage, str]] = {
    SafetyViolationType.TOXICITY: {
        SupportedLanguage.DE: "[entfernt - unangemessener Inhalt]",
        SupportedLanguage.EN: "[removed - inappropriate content]",
        SupportedLanguage.FR: "[supprimé - contenu inapproprié]",
        SupportedLanguage.IT: "[rimosso - contenuto inappropriato]",
        SupportedLanguage.ES: "[eliminado - contenido inapropiado]",
    },
    SafetyViolationType.PII_LEAK: {
        SupportedLanguage.DE: "[anonymisiert]",
        SupportedLanguage.EN: "[anonymized]",
        SupportedLanguage.FR: "[anonymisé]",
        SupportedLanguage.IT: "[anonimizzato]",
        SupportedLanguage.ES: "[anonimizado]",
    },
}


# =============================================================================
# DATA STRUCTURES
# =============================================================================

@dataclass
class SafetyViolation:
    """A single safety violation."""

    violation_id: str
    violation_type: SafetyViolationType
    severity: SafetySeverity
    section: str
    description: str
    original_text: str = ""
    suggested_fix: str = ""
    auto_healable: bool = True
    healed: bool = False

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "violation_id": self.violation_id,
            "violation_type": self.violation_type.value,
            "severity": self.severity.value,
            "section": self.section,
            "description": self.description,
            "original_text": self.original_text[:100] if self.original_text else "",
            "suggested_fix": self.suggested_fix[:100] if self.suggested_fix else "",
            "auto_healable": self.auto_healable,
            "healed": self.healed,
        }


@dataclass
class SafetyCheckResult:
    """Result of safety check on content."""

    is_safe: bool
    violations: List[SafetyViolation] = field(default_factory=list)
    toxicity_score: float = 0.0  # 0.0 - 1.0
    compliance_score: float = 1.0  # 0.0 - 1.0
    governance_score: float = 1.0  # 0.0 - 1.0
    pii_detected: bool = False

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "is_safe": self.is_safe,
            "violations_count": len(self.violations),
            "toxicity_score": round(self.toxicity_score, 3),
            "compliance_score": round(self.compliance_score, 3),
            "governance_score": round(self.governance_score, 3),
            "pii_detected": self.pii_detected,
            "critical_violations": sum(
                1 for v in self.violations if v.severity == SafetySeverity.CRITICAL
            ),
        }


@dataclass
class SafetyAssuranceReport:
    """Report from safety assurance layer."""

    engine_id: str = "SAFETY_ASSURANCE_V3"
    success: bool = True
    safety_validated: bool = False
    sections_checked: int = 0
    violations_found: int = 0
    violations_healed: int = 0
    critical_violations: int = 0
    toxicity_filtered: int = 0
    vendor_masked: int = 0
    compliance_removed: int = 0
    governance_conflicts: int = 0
    pii_anonymized: int = 0
    healed: bool = False
    issues: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "engine_id": self.engine_id,
            "success": self.success,
            "safety_validated": self.safety_validated,
            "sections_checked": self.sections_checked,
            "violations_found": self.violations_found,
            "violations_healed": self.violations_healed,
            "critical_violations": self.critical_violations,
            "toxicity_filtered": self.toxicity_filtered,
            "vendor_masked": self.vendor_masked,
            "compliance_removed": self.compliance_removed,
            "governance_conflicts": self.governance_conflicts,
            "pii_anonymized": self.pii_anonymized,
            "healed": self.healed,
            "issues": self.issues,
            "warnings": self.warnings,
            "timestamp": self.timestamp,
        }


# =============================================================================
# SAFETY ASSURANCE LAYER V3
# =============================================================================

class SafetyAssuranceLayerV3:
    """
    N4.3: Comprehensive Safety Assurance Layer.

    Provides multi-layer safety checks:
    1. Toxicity filtering
    2. Vendor-authority masking
    3. Compliance phrase detection/removal
    4. Governance conflict detection/correction
    5. PII leak prevention

    Self-healing: Automatically corrects violations without fallbacks.
    """

    def __init__(
        self,
        sections: SectionDict,
        briefing: BriefingDict,
        target_language: str = "de",
        strict_mode: bool = False,
    ) -> None:
        """
        Initialize Safety Assurance Layer v3.

        Args:
            sections: Section dictionary
            briefing: Briefing data
            target_language: Target language code
            strict_mode: Enable stricter safety checks
        """
        self.sections = sections
        self.briefing = briefing
        self.strict_mode = strict_mode

        try:
            self._language = SupportedLanguage(target_language.lower())
        except ValueError:
            self._language = SupportedLanguage.DE

        self._report = SafetyAssuranceReport()
        self._violations: List[SafetyViolation] = []
        self._violation_counter = 0

        log.info(
            "[N4.3-Safety] Layer initialized: lang=%s, strict=%s",
            self._language.value, strict_mode
        )

    def process(self) -> Tuple[SectionDict, SafetyAssuranceReport]:
        """
        Process sections through safety assurance layer.

        Returns:
            Tuple of (processed_sections, report)
        """
        log.info("[N4.3-Safety] Processing started")

        result_sections: SectionDict = {}

        for section_key, section_content in self.sections.items():
            # Skip internal keys
            if section_key.startswith("_"):
                result_sections[section_key] = section_content
                continue

            # Skip non-string content
            if not isinstance(section_content, str):
                result_sections[section_key] = section_content
                continue

            # Skip empty content
            if not section_content.strip():
                result_sections[section_key] = section_content
                continue

            self._report.sections_checked += 1

            # Process section through safety layers
            safe_content = self._process_section(section_key, section_content)
            result_sections[section_key] = safe_content

        # Calculate overall results
        self._report.violations_found = len(self._violations)
        self._report.violations_healed = sum(1 for v in self._violations if v.healed)
        self._report.critical_violations = sum(
            1 for v in self._violations if v.severity == SafetySeverity.CRITICAL
        )

        # Determine if safety is validated
        unhealed_critical = sum(
            1 for v in self._violations
            if v.severity == SafetySeverity.CRITICAL and not v.healed
        )
        self._report.safety_validated = unhealed_critical == 0
        self._report.healed = self._report.violations_healed > 0
        self._report.success = self._report.safety_validated

        # Store results
        result_sections["_safety_validated"] = self._report.safety_validated
        result_sections["_safety_report"] = self._report.to_dict()
        result_sections["_safety_healed"] = self._report.healed

        log.info(
            "[N4.3-Safety] Complete: violations=%d, healed=%d, validated=%s",
            self._report.violations_found,
            self._report.violations_healed,
            self._report.safety_validated
        )

        return result_sections, self._report

    def _process_section(self, section_key: str, content: str) -> str:
        """Process a single section through all safety layers."""
        processed = content

        # Layer 1: Toxicity filtering
        processed, toxicity_count = self._filter_toxicity(section_key, processed)
        self._report.toxicity_filtered += toxicity_count

        # Layer 2: Vendor authority masking
        processed, vendor_count = self._mask_vendor_authority(section_key, processed)
        self._report.vendor_masked += vendor_count

        # Layer 3: Compliance phrase removal
        processed, compliance_count = self._remove_compliance_phrases(section_key, processed)
        self._report.compliance_removed += compliance_count

        # Layer 4: Governance conflict detection and correction
        processed, conflict_count = self._handle_governance_conflicts(section_key, processed)
        self._report.governance_conflicts += conflict_count

        # Layer 5: PII anonymization
        processed, pii_count = self._anonymize_pii(section_key, processed)
        self._report.pii_anonymized += pii_count

        return processed

    def _filter_toxicity(self, section_key: str, content: str) -> Tuple[str, int]:
        """Filter toxic content from section."""
        patterns = TOXICITY_PATTERNS.get(
            self._language, TOXICITY_PATTERNS[SupportedLanguage.EN]
        )

        filtered = content
        count = 0
        replacement = HEALING_TEMPLATES[SafetyViolationType.TOXICITY].get(
            self._language, "[removed]"
        )

        # KIS-1327: Ersetzung über re.sub statt über gespeicherte Positionen —
        # nach dem ersten Treffer stimmten die Offsets der weiteren nicht mehr
        # („[entfernt - unangemessen[entfernt - unangemessener Inhalt]").
        def _heal(match: "re.Match[str]") -> str:
            nonlocal count
            violation = SafetyViolation(
                violation_id=self._get_violation_id(),
                violation_type=SafetyViolationType.TOXICITY,
                severity=SafetySeverity.HIGH,
                section=section_key,
                description=f"Toxic content detected: {match.group()[:50]}",
                original_text=match.group(),
                suggested_fix=replacement,
            )
            violation.healed = True
            count += 1
            self._violations.append(violation)
            return replacement

        for pattern in patterns:
            filtered = re.sub(pattern, _heal, filtered, flags=re.IGNORECASE)

        return filtered, count

    def _mask_vendor_authority(self, section_key: str, content: str) -> Tuple[str, int]:
        """Mask vendor-specific authority claims."""
        patterns = VENDOR_AUTHORITY_PATTERNS.get(
            self._language, VENDOR_AUTHORITY_PATTERNS[SupportedLanguage.EN]
        )

        masked = content
        count = 0

        for pattern, replacement in patterns:
            matches = list(re.finditer(pattern, masked, re.IGNORECASE))
            for match in matches:
                # Create violation
                violation = SafetyViolation(
                    violation_id=self._get_violation_id(),
                    violation_type=SafetyViolationType.VENDOR_AUTHORITY,
                    severity=SafetySeverity.MEDIUM,
                    section=section_key,
                    description=f"Vendor authority claim detected",
                    original_text=match.group(),
                    suggested_fix=replacement,
                )

                # Auto-heal
                masked = re.sub(pattern, replacement, masked, flags=re.IGNORECASE)
                violation.healed = True
                count += 1

                self._violations.append(violation)
                break  # Only process once per pattern to avoid double-counting

        return masked, count

    def _remove_compliance_phrases(self, section_key: str, content: str) -> Tuple[str, int]:
        """Remove problematic compliance phrases."""
        patterns = COMPLIANCE_PHRASES.get(
            self._language, COMPLIANCE_PHRASES[SupportedLanguage.EN]
        )

        cleaned = content
        count = 0

        for pattern in patterns:
            # Find sentences containing the phrase
            sentence_pattern = rf"[^.!?]*{pattern}[^.!?]*[.!?]"
            matches = list(re.finditer(sentence_pattern, cleaned, re.IGNORECASE))

            for match in matches:
                # Create violation
                violation = SafetyViolation(
                    violation_id=self._get_violation_id(),
                    violation_type=SafetyViolationType.COMPLIANCE_PHRASE,
                    severity=SafetySeverity.MEDIUM,
                    section=section_key,
                    description=f"Compliance disclaimer undermining authority",
                    original_text=match.group()[:100],
                    suggested_fix="[removed disclaimer]",
                )

                # Auto-heal by removing the sentence
                cleaned = cleaned[:match.start()] + cleaned[match.end():]
                violation.healed = True
                count += 1

                self._violations.append(violation)
                break  # Only process first match per pattern

        return cleaned.strip(), count

    def _handle_governance_conflicts(self, section_key: str, content: str) -> Tuple[str, int]:
        """Detect and correct governance conflicts."""
        corrected = content
        count = 0

        # Check for risk understatement conflicts
        risk_patterns = GOVERNANCE_CONFLICT_PATTERNS["risk_understatement"]

        high_risk_found = any(
            re.search(pattern, corrected, re.IGNORECASE)
            for pattern in risk_patterns["high_risk_indicators"]
        )

        if high_risk_found:
            for low_pattern in risk_patterns["low_risk_claims"]:
                matches = list(re.finditer(low_pattern, corrected, re.IGNORECASE))
                for match in matches:
                    # Create violation
                    violation = SafetyViolation(
                        violation_id=self._get_violation_id(),
                        violation_type=SafetyViolationType.GOVERNANCE_CONFLICT,
                        severity=SafetySeverity.CRITICAL,
                        section=section_key,
                        description="High risk identified but claims no measures needed",
                        original_text=match.group(),
                        suggested_fix="appropriate measures should be implemented",
                    )

                    # Auto-heal
                    healing_text = self._get_governance_healing_text()
                    corrected = corrected[:match.start()] + healing_text + corrected[match.end():]
                    violation.healed = True
                    count += 1

                    self._violations.append(violation)
                    break

        # Check for compliance contradictions
        compliance_patterns = GOVERNANCE_CONFLICT_PATTERNS["compliance_contradiction"]

        non_compliant = any(
            re.search(pattern, corrected, re.IGNORECASE)
            for pattern in compliance_patterns["non_compliant_indicators"]
        )

        if non_compliant:
            for claim_pattern in compliance_patterns["compliant_claims"]:
                matches = list(re.finditer(claim_pattern, corrected, re.IGNORECASE))
                for match in matches:
                    violation = SafetyViolation(
                        violation_id=self._get_violation_id(),
                        violation_type=SafetyViolationType.GOVERNANCE_CONFLICT,
                        severity=SafetySeverity.CRITICAL,
                        section=section_key,
                        description="Compliance contradiction detected",
                        original_text=match.group(),
                        suggested_fix="compliance status requires clarification",
                    )

                    # Remove contradicting claim
                    corrected = re.sub(
                        claim_pattern, "compliance status to be verified",
                        corrected, flags=re.IGNORECASE
                    )
                    violation.healed = True
                    count += 1

                    self._violations.append(violation)
                    break

        return corrected, count

    def _anonymize_pii(self, section_key: str, content: str) -> Tuple[str, int]:
        """Anonymize personally identifiable information."""
        anonymized = content
        count = 0

        for pattern in PII_PATTERNS:
            matches = list(re.finditer(pattern, anonymized))
            for match in matches:
                violation = SafetyViolation(
                    violation_id=self._get_violation_id(),
                    violation_type=SafetyViolationType.PII_LEAK,
                    severity=SafetySeverity.CRITICAL,
                    section=section_key,
                    description="PII detected in content",
                    original_text="[PII hidden]",
                    suggested_fix=HEALING_TEMPLATES[SafetyViolationType.PII_LEAK].get(
                        self._language, "[anonymized]"
                    ),
                )

                replacement = HEALING_TEMPLATES[SafetyViolationType.PII_LEAK].get(
                    self._language, "[anonymized]"
                )
                anonymized = anonymized[:match.start()] + replacement + anonymized[match.end():]
                violation.healed = True
                count += 1

                self._violations.append(violation)

        return anonymized, count

    def _get_governance_healing_text(self) -> str:
        """Get language-appropriate governance healing text."""
        healing_texts = {
            SupportedLanguage.DE: "entsprechende Schutzmaßnahmen sollten implementiert werden",
            SupportedLanguage.EN: "appropriate protective measures should be implemented",
            SupportedLanguage.FR: "des mesures de protection appropriées devraient être mises en œuvre",
            SupportedLanguage.IT: "dovrebbero essere implementate misure di protezione appropriate",
            SupportedLanguage.ES: "se deben implementar medidas de protección apropiadas",
        }
        return healing_texts.get(self._language, healing_texts[SupportedLanguage.EN])

    def _get_violation_id(self) -> str:
        """Generate unique violation ID."""
        self._violation_counter += 1
        return f"SAF-{self._violation_counter:04d}"

    def get_violations(self) -> List[SafetyViolation]:
        """Get all detected violations."""
        return self._violations

    def get_critical_violations(self) -> List[SafetyViolation]:
        """Get critical violations only."""
        return [v for v in self._violations if v.severity == SafetySeverity.CRITICAL]


# =============================================================================
# MODULE-LEVEL FUNCTIONS
# =============================================================================

def check_content_safety(
    content: str,
    language: str = "de",
    strict_mode: bool = False,
) -> SafetyCheckResult:
    """
    Check content for safety violations.

    Args:
        content: Content to check
        language: Language code
        strict_mode: Enable stricter checks

    Returns:
        SafetyCheckResult
    """
    try:
        lang = SupportedLanguage(language.lower())
    except ValueError:
        lang = SupportedLanguage.DE

    violations: List[SafetyViolation] = []
    toxicity_count = 0
    compliance_count = 0
    governance_count = 0
    pii_found = False

    # Check toxicity
    patterns = TOXICITY_PATTERNS.get(lang, TOXICITY_PATTERNS[SupportedLanguage.EN])
    for pattern in patterns:
        if re.search(pattern, content, re.IGNORECASE):
            toxicity_count += 1
            violations.append(SafetyViolation(
                violation_id=f"CHK-TOX-{toxicity_count}",
                violation_type=SafetyViolationType.TOXICITY,
                severity=SafetySeverity.HIGH,
                section="content",
                description="Toxic content detected",
            ))

    # Check compliance phrases
    phrases = COMPLIANCE_PHRASES.get(lang, COMPLIANCE_PHRASES[SupportedLanguage.EN])
    for phrase in phrases:
        if re.search(phrase, content, re.IGNORECASE):
            compliance_count += 1
            violations.append(SafetyViolation(
                violation_id=f"CHK-CMP-{compliance_count}",
                violation_type=SafetyViolationType.COMPLIANCE_PHRASE,
                severity=SafetySeverity.MEDIUM,
                section="content",
                description="Problematic compliance phrase detected",
            ))

    # Check PII
    for pattern in PII_PATTERNS:
        if re.search(pattern, content):
            pii_found = True
            violations.append(SafetyViolation(
                violation_id="CHK-PII-001",
                violation_type=SafetyViolationType.PII_LEAK,
                severity=SafetySeverity.CRITICAL,
                section="content",
                description="PII detected",
            ))
            break

    # Calculate scores
    content_length = len(content) if content else 1
    toxicity_score = min(1.0, toxicity_count * 0.2)
    compliance_score = max(0.0, 1.0 - (compliance_count * 0.15))
    governance_score = max(0.0, 1.0 - (governance_count * 0.2))

    is_safe = (
        toxicity_score < 0.5 and
        compliance_score > 0.5 and
        not pii_found and
        not any(v.severity == SafetySeverity.CRITICAL for v in violations)
    )

    return SafetyCheckResult(
        is_safe=is_safe,
        violations=violations,
        toxicity_score=toxicity_score,
        compliance_score=compliance_score,
        governance_score=governance_score,
        pii_detected=pii_found,
    )


def filter_toxicity(
    content: str,
    language: str = "de",
) -> Tuple[str, int]:
    """
    Filter toxic content.

    Args:
        content: Content to filter
        language: Language code

    Returns:
        Tuple of (filtered_content, count)
    """
    try:
        lang = SupportedLanguage(language.lower())
    except ValueError:
        lang = SupportedLanguage.DE

    patterns = TOXICITY_PATTERNS.get(lang, TOXICITY_PATTERNS[SupportedLanguage.EN])
    filtered = content
    count = 0

    for pattern in patterns:
        matches = re.findall(pattern, filtered, re.IGNORECASE)
        count += len(matches)
        replacement = HEALING_TEMPLATES[SafetyViolationType.TOXICITY].get(lang, "[removed]")
        filtered = re.sub(pattern, replacement, filtered, flags=re.IGNORECASE)

    return filtered, count


def mask_vendor_authority(
    content: str,
    language: str = "de",
) -> Tuple[str, int]:
    """
    Mask vendor authority claims.

    Args:
        content: Content to process
        language: Language code

    Returns:
        Tuple of (masked_content, count)
    """
    try:
        lang = SupportedLanguage(language.lower())
    except ValueError:
        lang = SupportedLanguage.DE

    patterns = VENDOR_AUTHORITY_PATTERNS.get(
        lang, VENDOR_AUTHORITY_PATTERNS[SupportedLanguage.EN]
    )
    masked = content
    count = 0

    for pattern, replacement in patterns:
        if re.search(pattern, masked, re.IGNORECASE):
            masked = re.sub(pattern, replacement, masked, flags=re.IGNORECASE)
            count += 1

    return masked, count


def detect_compliance_phrases(
    content: str,
    language: str = "de",
) -> List[str]:
    """
    Detect problematic compliance phrases.

    Args:
        content: Content to check
        language: Language code

    Returns:
        List of detected phrases
    """
    try:
        lang = SupportedLanguage(language.lower())
    except ValueError:
        lang = SupportedLanguage.DE

    patterns = COMPLIANCE_PHRASES.get(lang, COMPLIANCE_PHRASES[SupportedLanguage.EN])
    detected: List[str] = []

    for pattern in patterns:
        matches = re.findall(pattern, content, re.IGNORECASE)
        detected.extend(matches)

    return detected


def detect_governance_conflicts(
    content: str,
    risk_level: str = "minimal",
) -> List[Dict[str, Any]]:
    """
    Detect governance conflicts in content.

    Args:
        content: Content to check
        risk_level: Expected risk level

    Returns:
        List of conflict dictionaries
    """
    conflicts: List[Dict[str, Any]] = []

    # Check risk understatement
    risk_patterns = GOVERNANCE_CONFLICT_PATTERNS["risk_understatement"]

    high_risk_found = any(
        re.search(pattern, content, re.IGNORECASE)
        for pattern in risk_patterns["high_risk_indicators"]
    )

    if high_risk_found:
        for pattern in risk_patterns["low_risk_claims"]:
            if re.search(pattern, content, re.IGNORECASE):
                conflicts.append({
                    "type": "risk_understatement",
                    "severity": "critical",
                    "description": "High risk identified but protective measures dismissed",
                })
                break

    # Check compliance contradiction
    compliance_patterns = GOVERNANCE_CONFLICT_PATTERNS["compliance_contradiction"]

    non_compliant = any(
        re.search(pattern, content, re.IGNORECASE)
        for pattern in compliance_patterns["non_compliant_indicators"]
    )

    compliant_claimed = any(
        re.search(pattern, content, re.IGNORECASE)
        for pattern in compliance_patterns["compliant_claims"]
    )

    if non_compliant and compliant_claimed:
        conflicts.append({
            "type": "compliance_contradiction",
            "severity": "critical",
            "description": "Contradicting compliance claims detected",
        })

    return conflicts


def heal_safety_violations(
    content: str,
    violations: List[SafetyViolation],
    language: str = "de",
) -> Tuple[str, int]:
    """
    Heal safety violations in content.

    Args:
        content: Content to heal
        violations: List of violations to heal
        language: Language code

    Returns:
        Tuple of (healed_content, healed_count)
    """
    healed = content
    count = 0

    try:
        lang = SupportedLanguage(language.lower())
    except ValueError:
        lang = SupportedLanguage.DE

    for violation in violations:
        if not violation.auto_healable or violation.healed:
            continue

        if violation.original_text and violation.original_text in healed:
            replacement = violation.suggested_fix or HEALING_TEMPLATES.get(
                violation.violation_type, {}
            ).get(lang, "[corrected]")

            healed = healed.replace(violation.original_text, replacement, 1)
            violation.healed = True
            count += 1

    return healed, count


def validate_safety_compliance(
    sections: SectionDict,
    briefing: Optional[BriefingDict] = None,
    strict_mode: bool = False,
) -> Tuple[bool, Dict[str, Any]]:
    """
    Validate safety compliance for sections.

    Args:
        sections: Section dictionary
        briefing: Optional briefing data
        strict_mode: Enable strict mode

    Returns:
        Tuple of (is_compliant, details)
    """
    engine = SafetyAssuranceLayerV3(
        sections=sections,
        briefing=briefing or {},
        strict_mode=strict_mode,
    )
    _, report = engine.process()

    details = {
        "validated": report.safety_validated,
        "violations_found": report.violations_found,
        "violations_healed": report.violations_healed,
        "critical_violations": report.critical_violations,
        "toxicity_filtered": report.toxicity_filtered,
        "vendor_masked": report.vendor_masked,
        "compliance_removed": report.compliance_removed,
        "governance_conflicts": report.governance_conflicts,
        "pii_anonymized": report.pii_anonymized,
    }

    return report.safety_validated, details
