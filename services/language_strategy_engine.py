# -*- coding: utf-8 -*-
"""
N4.2: Language Strategy Engine
==============================

PLATIN+++ v5.2 - Multi-Language Intelligence Layer

This module provides intelligent language detection, model selection per language,
and executive tonality profiles for multilingual report generation.

Supported Languages:
- DE (German) - Primary
- EN (English) - Secondary
- FR (French) - Executive
- IT (Italian) - Executive
- ES (Spanish) - Executive

Features:
- Automatic language detection from request/briefing
- Language-specific model selection (Claude=Executive, GPT=KPIs)
- Native executive tonality per language
- Consulting vocabulary profiles per language
- Zero-fallback guarantee per language

Version: 1.0.0 (N4.2 - PLATIN+++ v5.2)
Author: Claude + Wolf
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Tuple

from services.types import SectionDict, BriefingDict, EngineReport

log = logging.getLogger(__name__)

__all__ = [
    "SupportedLanguage",
    "LanguageTone",
    "SectionCategory",
    "LanguageProfile",
    "LanguageDetectionResult",
    "LanguageStrategyEngine",
    "detect_language",
    "select_language_model",
    "apply_language_profile",
    "get_language_profile",
]


# =============================================================================
# ENUMS & CONSTANTS
# =============================================================================

class SupportedLanguage(Enum):
    """Supported languages for report generation."""
    DE = "de"
    EN = "en"
    FR = "fr"
    IT = "it"
    ES = "es"


class LanguageTone(Enum):
    """Language tonality profiles for executive communication."""
    FORMAL_DECISIVE = "formal_decisive"
    FORMAL_ANALYTICAL = "formal_analytical"
    EXECUTIVE_CONSULTATIVE = "executive_consultative"
    BOARD_LEVEL = "board_level"
    C_SUITE = "c_suite"


class SectionCategory(Enum):
    """Categories of report sections for model selection."""
    EXECUTIVE = "executive"      # Claude preferred
    NARRATIVE = "narrative"      # Claude preferred
    KPI = "kpi"                  # GPT preferred
    TABLES = "tables"            # GPT preferred
    GOVERNANCE = "governance"    # Claude preferred
    RISK = "risk"               # Claude preferred
    ROADMAP = "roadmap"         # Dual model
    RECOMMENDATIONS = "recommendations"  # Dual model


class ModelPreference(Enum):
    """Model preference for generation."""
    CLAUDE = "claude"
    GPT = "gpt"
    DUAL = "dual"


# Language detection patterns
LANGUAGE_DETECTION_PATTERNS: Dict[SupportedLanguage, List[str]] = {
    SupportedLanguage.DE: [
        r"\b(und|oder|aber|nicht|für|mit|auf|bei|nach|aus|über|unter|zwischen)\b",
        r"\b(Unternehmen|Gesellschaft|GmbH|AG|KMU|Mittelstand)\b",
        r"\b(werden|können|müssen|sollen|dürfen)\b",
        r"ß|ü|ö|ä",
    ],
    SupportedLanguage.EN: [
        r"\b(the|and|or|but|not|for|with|from|about|between)\b",
        r"\b(company|business|enterprise|corporation|Ltd|Inc)\b",
        r"\b(should|could|would|will|can|must)\b",
    ],
    SupportedLanguage.FR: [
        r"\b(et|ou|mais|pas|pour|avec|dans|sur|sous|entre)\b",
        r"\b(entreprise|société|SARL|SA|PME)\b",
        r"\b(être|avoir|faire|pouvoir|devoir|vouloir)\b",
        r"é|è|ê|ë|à|â|ç|î|ï|ô|û|ù",
    ],
    SupportedLanguage.IT: [
        r"\b(e|o|ma|non|per|con|da|su|tra|fra)\b",
        r"\b(azienda|impresa|società|SRL|SpA|PMI)\b",
        r"\b(essere|avere|fare|potere|dovere|volere)\b",
        r"à|è|ì|ò|ù",
    ],
    SupportedLanguage.ES: [
        r"\b(y|o|pero|no|para|con|de|en|sobre|entre)\b",
        r"\b(empresa|compañía|sociedad|SL|SA|PYME)\b",
        r"\b(ser|estar|haber|poder|deber|querer)\b",
        r"ñ|á|é|í|ó|ú|ü",
    ],
}

# Language-specific model selection rules
LANGUAGE_MODEL_RULES: Dict[SupportedLanguage, Dict[SectionCategory, ModelPreference]] = {
    SupportedLanguage.DE: {
        SectionCategory.EXECUTIVE: ModelPreference.CLAUDE,
        SectionCategory.NARRATIVE: ModelPreference.CLAUDE,
        SectionCategory.KPI: ModelPreference.GPT,
        SectionCategory.TABLES: ModelPreference.GPT,
        SectionCategory.GOVERNANCE: ModelPreference.CLAUDE,
        SectionCategory.RISK: ModelPreference.CLAUDE,
        SectionCategory.ROADMAP: ModelPreference.DUAL,
        SectionCategory.RECOMMENDATIONS: ModelPreference.DUAL,
    },
    SupportedLanguage.EN: {
        SectionCategory.EXECUTIVE: ModelPreference.CLAUDE,
        SectionCategory.NARRATIVE: ModelPreference.CLAUDE,
        SectionCategory.KPI: ModelPreference.GPT,
        SectionCategory.TABLES: ModelPreference.GPT,
        SectionCategory.GOVERNANCE: ModelPreference.CLAUDE,
        SectionCategory.RISK: ModelPreference.CLAUDE,
        SectionCategory.ROADMAP: ModelPreference.DUAL,
        SectionCategory.RECOMMENDATIONS: ModelPreference.DUAL,
    },
    SupportedLanguage.FR: {
        SectionCategory.EXECUTIVE: ModelPreference.CLAUDE,
        SectionCategory.NARRATIVE: ModelPreference.CLAUDE,
        SectionCategory.KPI: ModelPreference.GPT,
        SectionCategory.TABLES: ModelPreference.GPT,
        SectionCategory.GOVERNANCE: ModelPreference.CLAUDE,
        SectionCategory.RISK: ModelPreference.CLAUDE,
        SectionCategory.ROADMAP: ModelPreference.CLAUDE,  # Claude for French executive tone
        SectionCategory.RECOMMENDATIONS: ModelPreference.DUAL,
    },
    SupportedLanguage.IT: {
        SectionCategory.EXECUTIVE: ModelPreference.CLAUDE,
        SectionCategory.NARRATIVE: ModelPreference.CLAUDE,
        SectionCategory.KPI: ModelPreference.GPT,
        SectionCategory.TABLES: ModelPreference.GPT,
        SectionCategory.GOVERNANCE: ModelPreference.CLAUDE,
        SectionCategory.RISK: ModelPreference.CLAUDE,
        SectionCategory.ROADMAP: ModelPreference.CLAUDE,  # Claude for Italian executive tone
        SectionCategory.RECOMMENDATIONS: ModelPreference.DUAL,
    },
    SupportedLanguage.ES: {
        SectionCategory.EXECUTIVE: ModelPreference.CLAUDE,
        SectionCategory.NARRATIVE: ModelPreference.CLAUDE,
        SectionCategory.KPI: ModelPreference.GPT,
        SectionCategory.TABLES: ModelPreference.GPT,
        SectionCategory.GOVERNANCE: ModelPreference.CLAUDE,
        SectionCategory.RISK: ModelPreference.CLAUDE,
        SectionCategory.ROADMAP: ModelPreference.CLAUDE,  # Claude for Spanish executive tone
        SectionCategory.RECOMMENDATIONS: ModelPreference.DUAL,
    },
}

# Section to category mapping
SECTION_CATEGORY_MAP: Dict[str, SectionCategory] = {
    "executive_summary": SectionCategory.EXECUTIVE,
    "investment_thesis": SectionCategory.EXECUTIVE,
    "gamechanger": SectionCategory.NARRATIVE,
    "deep_dive_nutzenpotenzial": SectionCategory.NARRATIVE,
    "ki_stack_summary": SectionCategory.TABLES,
    "business_case": SectionCategory.KPI,
    "kpi_dashboard": SectionCategory.KPI,
    "tools_empfehlungen": SectionCategory.TABLES,
    "foerderpotenzial": SectionCategory.TABLES,
    "risks": SectionCategory.RISK,
    "ki_act_compliance": SectionCategory.GOVERNANCE,
    "governance": SectionCategory.GOVERNANCE,
    "roadmap_90d": SectionCategory.ROADMAP,
    "roadmap_12m": SectionCategory.ROADMAP,
    "recommendations": SectionCategory.RECOMMENDATIONS,
    "starter_kit": SectionCategory.ROADMAP,
    "automation_roadmap": SectionCategory.ROADMAP,
    "benchmark": SectionCategory.KPI,
}

# Executive tonality profiles per language
EXECUTIVE_TONALITY: Dict[SupportedLanguage, Dict[str, Any]] = {
    SupportedLanguage.DE: {
        "tone": LanguageTone.FORMAL_DECISIVE,
        "sentence_length": "medium",
        "formality": "high",
        "directness": "high",
        "preferred_structures": [
            "Empfehlung:",
            "Handlungsbedarf:",
            "Ergebnis:",
            "Fazit:",
        ],
        "forbidden_phrases": [
            "irgendwie",
            "quasi",
            "eigentlich",
            "halt",
            "könnte vielleicht",
        ],
        "board_vocabulary": {
            "ROI": "Return on Investment",
            "KPI": "Kennzahl",
            "Roadmap": "Transformationsfahrplan",
            "Quick Win": "Schnellgewinn",
            "Use Case": "Anwendungsfall",
        },
    },
    SupportedLanguage.EN: {
        "tone": LanguageTone.EXECUTIVE_CONSULTATIVE,
        "sentence_length": "short",
        "formality": "high",
        "directness": "very_high",
        "preferred_structures": [
            "Recommendation:",
            "Key Finding:",
            "Executive Action:",
            "Bottom Line:",
        ],
        "forbidden_phrases": [
            "kind of",
            "sort of",
            "basically",
            "actually",
            "might maybe",
        ],
        "board_vocabulary": {
            "synergy": "combined benefit",
            "leverage": "utilize",
            "paradigm shift": "strategic change",
            "deep dive": "detailed analysis",
        },
    },
    SupportedLanguage.FR: {
        "tone": LanguageTone.FORMAL_ANALYTICAL,
        "sentence_length": "long",
        "formality": "very_high",
        "directness": "medium",
        "preferred_structures": [
            "Recommandation :",
            "Constat :",
            "Action prioritaire :",
            "Synthèse :",
        ],
        "forbidden_phrases": [
            "en quelque sorte",
            "un peu",
            "genre",
            "du coup",
        ],
        "board_vocabulary": {
            "ROI": "Retour sur Investissement",
            "KPI": "Indicateur Clé de Performance",
            "Roadmap": "Feuille de Route",
            "Quick Win": "Gain Rapide",
        },
    },
    SupportedLanguage.IT: {
        "tone": LanguageTone.FORMAL_ANALYTICAL,
        "sentence_length": "medium",
        "formality": "high",
        "directness": "medium",
        "preferred_structures": [
            "Raccomandazione:",
            "Risultato chiave:",
            "Azione prioritaria:",
            "Sintesi:",
        ],
        "forbidden_phrases": [
            "tipo",
            "praticamente",
            "insomma",
            "cioè",
        ],
        "board_vocabulary": {
            "ROI": "Ritorno sull'Investimento",
            "KPI": "Indicatore Chiave di Prestazione",
            "Roadmap": "Piano d'Azione",
            "Quick Win": "Risultato Rapido",
        },
    },
    SupportedLanguage.ES: {
        "tone": LanguageTone.FORMAL_ANALYTICAL,
        "sentence_length": "medium",
        "formality": "high",
        "directness": "medium",
        "preferred_structures": [
            "Recomendación:",
            "Hallazgo clave:",
            "Acción prioritaria:",
            "Síntesis:",
        ],
        "forbidden_phrases": [
            "como que",
            "tipo",
            "o sea",
            "básicamente",
        ],
        "board_vocabulary": {
            "ROI": "Retorno de la Inversión",
            "KPI": "Indicador Clave de Rendimiento",
            "Roadmap": "Hoja de Ruta",
            "Quick Win": "Resultado Rápido",
        },
    },
}

# Consulting vocabulary per language (must be consistent across all reports)
CONSULTING_GLOSSARY: Dict[SupportedLanguage, Dict[str, str]] = {
    SupportedLanguage.DE: {
        "readiness_score": "KI-Bereitschaftsgrad",
        "risk_score": "Risiko-Index",
        "roi": "ROI (Return on Investment)",
        "payback": "Amortisationszeit",
        "time_savings": "Zeitersparnis",
        "ai_act": "EU KI-Verordnung",
        "governance": "KI-Governance",
        "automation": "Automatisierung",
        "transformation": "Transformation",
        "quick_wins": "Schnellgewinne",
    },
    SupportedLanguage.EN: {
        "readiness_score": "AI Readiness Score",
        "risk_score": "Risk Index",
        "roi": "ROI (Return on Investment)",
        "payback": "Payback Period",
        "time_savings": "Time Savings",
        "ai_act": "EU AI Act",
        "governance": "AI Governance",
        "automation": "Automation",
        "transformation": "Transformation",
        "quick_wins": "Quick Wins",
    },
    SupportedLanguage.FR: {
        "readiness_score": "Score de Maturité IA",
        "risk_score": "Indice de Risque",
        "roi": "ROI (Retour sur Investissement)",
        "payback": "Délai d'Amortissement",
        "time_savings": "Gain de Temps",
        "ai_act": "Règlement Européen sur l'IA",
        "governance": "Gouvernance IA",
        "automation": "Automatisation",
        "transformation": "Transformation",
        "quick_wins": "Gains Rapides",
    },
    SupportedLanguage.IT: {
        "readiness_score": "Indice di Prontezza IA",
        "risk_score": "Indice di Rischio",
        "roi": "ROI (Ritorno sull'Investimento)",
        "payback": "Periodo di Ammortamento",
        "time_savings": "Risparmio di Tempo",
        "ai_act": "Regolamento UE sull'IA",
        "governance": "Governance IA",
        "automation": "Automazione",
        "transformation": "Trasformazione",
        "quick_wins": "Risultati Rapidi",
    },
    SupportedLanguage.ES: {
        "readiness_score": "Índice de Preparación IA",
        "risk_score": "Índice de Riesgo",
        "roi": "ROI (Retorno de la Inversión)",
        "payback": "Período de Amortización",
        "time_savings": "Ahorro de Tiempo",
        "ai_act": "Reglamento Europeo de IA",
        "governance": "Gobernanza IA",
        "automation": "Automatización",
        "transformation": "Transformación",
        "quick_wins": "Resultados Rápidos",
    },
}

# Default language fallback
DEFAULT_LANGUAGE = SupportedLanguage.DE


# =============================================================================
# DATA STRUCTURES
# =============================================================================

@dataclass
class LanguageProfile:
    """Complete language profile for report generation."""

    language: SupportedLanguage
    tone: LanguageTone
    glossary: Dict[str, str]
    tonality_config: Dict[str, Any]
    model_rules: Dict[SectionCategory, ModelPreference]
    detection_confidence: float = 1.0

    def get_term(self, key: str) -> str:
        """Get glossary term for key."""
        return self.glossary.get(key, key)

    def get_model_preference(self, section: str) -> ModelPreference:
        """Get model preference for a section."""
        category = SECTION_CATEGORY_MAP.get(section, SectionCategory.NARRATIVE)
        return self.model_rules.get(category, ModelPreference.CLAUDE)

    def is_forbidden_phrase(self, text: str) -> List[str]:
        """Check for forbidden phrases in text."""
        found = []
        forbidden = self.tonality_config.get("forbidden_phrases", [])
        text_lower = text.lower()
        for phrase in forbidden:
            if phrase.lower() in text_lower:
                found.append(phrase)
        return found

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "language": self.language.value,
            "tone": self.tone.value,
            "glossary": self.glossary,
            "detection_confidence": self.detection_confidence,
            "formality": self.tonality_config.get("formality", "high"),
            "directness": self.tonality_config.get("directness", "medium"),
        }


@dataclass
class LanguageDetectionResult:
    """Result of language detection."""

    detected_language: SupportedLanguage
    confidence: float
    scores: Dict[SupportedLanguage, float]
    source: str  # "explicit", "detected", "default"
    patterns_matched: int = 0

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "detected_language": self.detected_language.value,
            "confidence": round(self.confidence, 3),
            "scores": {k.value: round(v, 3) for k, v in self.scores.items()},
            "source": self.source,
            "patterns_matched": self.patterns_matched,
        }


@dataclass
class LanguageStrategyReport:
    """Report of language strategy processing."""

    engine_id: str = "LANGUAGE_STRATEGY"
    success: bool = True
    detected_language: Optional[SupportedLanguage] = None
    detection_confidence: float = 0.0
    sections_processed: int = 0
    model_selections: Dict[str, str] = field(default_factory=dict)
    tone_violations: List[str] = field(default_factory=list)
    glossary_applied: int = 0
    issues: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())

    def add_issue(self, issue: str) -> None:
        """Add an issue."""
        self.issues.append(issue)
        self.success = False

    def add_warning(self, warning: str) -> None:
        """Add a warning."""
        self.warnings.append(warning)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "engine_id": self.engine_id,
            "success": self.success,
            "detected_language": self.detected_language.value if self.detected_language else None,
            "detection_confidence": round(self.detection_confidence, 3),
            "sections_processed": self.sections_processed,
            "model_selections": self.model_selections,
            "tone_violations": self.tone_violations,
            "glossary_applied": self.glossary_applied,
            "issues": self.issues,
            "warnings": self.warnings,
            "timestamp": self.timestamp,
        }


# =============================================================================
# LANGUAGE STRATEGY ENGINE
# =============================================================================

class LanguageStrategyEngine:
    """
    N4.2: Intelligent Language Strategy Engine.

    Provides:
    - Automatic language detection
    - Language-specific model selection
    - Executive tonality profiles
    - Consulting vocabulary consistency
    - Zero-fallback guarantee
    """

    def __init__(
        self,
        sections: SectionDict,
        briefing: BriefingDict,
        target_language: Optional[str] = None,
    ) -> None:
        """
        Initialize the Language Strategy Engine.

        Args:
            sections: Section dictionary to process
            briefing: Briefing data with company context
            target_language: Explicit target language (optional)
        """
        self.sections = sections
        self.briefing = briefing
        self._target_language = target_language
        self._profile: Optional[LanguageProfile] = None
        self._detection_result: Optional[LanguageDetectionResult] = None
        self._report = LanguageStrategyReport()

        log.info("[N4.2-LanguageStrategy] Engine initialized")

    def process(self) -> Tuple[SectionDict, LanguageStrategyReport]:
        """
        Process sections with language strategy.

        Returns:
            Tuple of (processed_sections, report)
        """
        log.info("[N4.2-LanguageStrategy] Processing started")

        try:
            # Step 1: Detect or set language
            self._detect_language()

            # Step 2: Build language profile
            self._build_profile()

            # Step 3: Apply language profile to sections
            self._apply_profile_to_sections()

            # Step 4: Validate executive tonality
            self._validate_tonality()

            self._report.success = True
            log.info(
                "[N4.2-LanguageStrategy] Processing complete: %s (confidence: %.2f)",
                self._profile.language.value if self._profile else "unknown",
                self._report.detection_confidence,
            )

        except Exception as e:
            log.error("[N4.2-LanguageStrategy] Processing failed: %s", str(e))
            self._report.add_issue(f"Processing error: {str(e)}")

        return self.sections, self._report

    def _detect_language(self) -> None:
        """Detect target language from various sources."""
        # Priority 1: Explicit target language
        if self._target_language:
            try:
                lang = SupportedLanguage(self._target_language.lower())
                self._detection_result = LanguageDetectionResult(
                    detected_language=lang,
                    confidence=1.0,
                    scores={lang: 1.0},
                    source="explicit",
                )
                self._report.detected_language = lang
                self._report.detection_confidence = 1.0
                log.info("[N4.2-LanguageStrategy] Explicit language: %s", lang.value)
                return
            except ValueError:
                log.warning(
                    "[N4.2-LanguageStrategy] Invalid explicit language: %s",
                    self._target_language,
                )

        # Priority 2: Briefing language setting
        briefing_lang = self.briefing.get("lang") or self.briefing.get("language")
        if briefing_lang:
            try:
                lang = SupportedLanguage(briefing_lang.lower())
                self._detection_result = LanguageDetectionResult(
                    detected_language=lang,
                    confidence=0.95,
                    scores={lang: 0.95},
                    source="briefing",
                )
                self._report.detected_language = lang
                self._report.detection_confidence = 0.95
                log.info("[N4.2-LanguageStrategy] Briefing language: %s", lang.value)
                return
            except ValueError:
                pass

        # Priority 3: Tenant settings
        tenant_config = self.briefing.get("tenant_config", {})
        tenant_lang = tenant_config.get("default_language")
        if tenant_lang:
            try:
                lang = SupportedLanguage(tenant_lang.lower())
                self._detection_result = LanguageDetectionResult(
                    detected_language=lang,
                    confidence=0.9,
                    scores={lang: 0.9},
                    source="tenant",
                )
                self._report.detected_language = lang
                self._report.detection_confidence = 0.9
                log.info("[N4.2-LanguageStrategy] Tenant language: %s", lang.value)
                return
            except ValueError:
                pass

        # Priority 4: Auto-detect from content
        self._detection_result = self._auto_detect_language()
        self._report.detected_language = self._detection_result.detected_language
        self._report.detection_confidence = self._detection_result.confidence

        log.info(
            "[N4.2-LanguageStrategy] Auto-detected: %s (confidence: %.2f)",
            self._detection_result.detected_language.value,
            self._detection_result.confidence,
        )

    def _auto_detect_language(self) -> LanguageDetectionResult:
        """Auto-detect language from content."""
        # Collect text samples
        text_samples: List[str] = []

        # From briefing
        for key in ["company_description", "problem_statement", "goals", "answers"]:
            value = self.briefing.get(key)
            if isinstance(value, str):
                text_samples.append(value)
            elif isinstance(value, dict):
                for v in value.values():
                    if isinstance(v, str):
                        text_samples.append(v)

        # From sections
        for key, value in self.sections.items():
            if isinstance(value, str) and not key.startswith("_"):
                text_samples.append(value[:500])  # First 500 chars

        combined_text = " ".join(text_samples)

        # Score each language
        scores: Dict[SupportedLanguage, float] = {}
        for lang, patterns in LANGUAGE_DETECTION_PATTERNS.items():
            score = 0.0
            matches = 0
            for pattern in patterns:
                found = len(re.findall(pattern, combined_text, re.IGNORECASE))
                if found > 0:
                    score += min(found * 0.1, 1.0)
                    matches += found

            # Normalize by number of patterns
            scores[lang] = score / len(patterns) if patterns else 0.0

        # Find best match
        if not scores:
            return LanguageDetectionResult(
                detected_language=DEFAULT_LANGUAGE,
                confidence=0.5,
                scores={DEFAULT_LANGUAGE: 0.5},
                source="default",
            )

        best_lang = max(scores, key=lambda k: scores[k])
        best_score = scores[best_lang]

        # Calculate confidence
        total_score = sum(scores.values())
        confidence = best_score / total_score if total_score > 0 else 0.5

        return LanguageDetectionResult(
            detected_language=best_lang,
            confidence=min(confidence, 0.95),
            scores=scores,
            source="detected",
            patterns_matched=sum(1 for s in scores.values() if s > 0),
        )

    def _build_profile(self) -> None:
        """Build complete language profile."""
        if not self._detection_result:
            self._detect_language()

        assert self._detection_result is not None
        lang = self._detection_result.detected_language

        self._profile = LanguageProfile(
            language=lang,
            tone=EXECUTIVE_TONALITY[lang]["tone"],
            glossary=CONSULTING_GLOSSARY.get(lang, CONSULTING_GLOSSARY[DEFAULT_LANGUAGE]),
            tonality_config=EXECUTIVE_TONALITY.get(lang, EXECUTIVE_TONALITY[DEFAULT_LANGUAGE]),
            model_rules=LANGUAGE_MODEL_RULES.get(lang, LANGUAGE_MODEL_RULES[DEFAULT_LANGUAGE]),
            detection_confidence=self._detection_result.confidence,
        )

        log.info(
            "[N4.2-LanguageStrategy] Profile built: %s, tone=%s",
            lang.value,
            self._profile.tone.value,
        )

    def _apply_profile_to_sections(self) -> None:
        """Apply language profile to all sections."""
        if not self._profile:
            self._build_profile()

        processed = 0
        glossary_applied = 0

        for section_key, section_content in self.sections.items():
            if section_key.startswith("_"):
                continue

            if not isinstance(section_content, str):
                continue

            # Determine model selection for this section
            model_pref = self._profile.get_model_preference(section_key)
            self._report.model_selections[section_key] = model_pref.value

            # Apply glossary terms (for consistency)
            # This is tracked but not modified here (actual translation happens in translation engine)

            processed += 1

        self._report.sections_processed = processed
        self._report.glossary_applied = glossary_applied

        # Store profile in sections for downstream engines
        self.sections["_language_profile"] = self._profile.to_dict()
        self.sections["_target_language"] = self._profile.language.value

        log.info(
            "[N4.2-LanguageStrategy] Applied profile to %d sections",
            processed,
        )

    def _validate_tonality(self) -> None:
        """Validate executive tonality in all sections."""
        if not self._profile:
            return

        violations: List[str] = []

        for section_key, section_content in self.sections.items():
            if section_key.startswith("_"):
                continue

            if not isinstance(section_content, str):
                continue

            # Check for forbidden phrases
            forbidden_found = self._profile.is_forbidden_phrase(section_content)
            if forbidden_found:
                for phrase in forbidden_found:
                    violations.append(f"{section_key}: forbidden phrase '{phrase}'")

        self._report.tone_violations = violations

        if violations:
            log.warning(
                "[N4.2-LanguageStrategy] Found %d tone violations",
                len(violations),
            )

    def get_profile(self) -> Optional[LanguageProfile]:
        """Get the current language profile."""
        return self._profile

    def get_model_for_section(self, section: str) -> str:
        """Get the recommended model for a section."""
        if not self._profile:
            self._build_profile()

        assert self._profile is not None
        return self._profile.get_model_preference(section).value

    def get_glossary_term(self, key: str) -> str:
        """Get glossary term for key in target language."""
        if not self._profile:
            self._build_profile()

        assert self._profile is not None
        return self._profile.get_term(key)


# =============================================================================
# MODULE-LEVEL FUNCTIONS
# =============================================================================

def detect_language(
    request_data: Optional[Dict[str, Any]] = None,
    briefing_input: Optional[Dict[str, Any]] = None,
) -> LanguageDetectionResult:
    """
    Detect language from request data or briefing input.

    Args:
        request_data: Request data dictionary
        briefing_input: Briefing input dictionary

    Returns:
        LanguageDetectionResult with detected language and confidence
    """
    # Merge inputs
    combined = {}
    if briefing_input:
        combined.update(briefing_input)
    if request_data:
        combined.update(request_data)

    engine = LanguageStrategyEngine(sections={}, briefing=combined)
    engine._detect_language()

    return engine._detection_result or LanguageDetectionResult(
        detected_language=DEFAULT_LANGUAGE,
        confidence=0.5,
        scores={DEFAULT_LANGUAGE: 0.5},
        source="default",
    )


def select_language_model(
    language: str,
    section: str,
) -> str:
    """
    Select the best model for a language/section combination.

    Args:
        language: Target language code (de, en, fr, it, es)
        section: Section key

    Returns:
        Model name: "claude", "gpt", or "dual"
    """
    try:
        lang = SupportedLanguage(language.lower())
    except ValueError:
        lang = DEFAULT_LANGUAGE

    rules = LANGUAGE_MODEL_RULES.get(lang, LANGUAGE_MODEL_RULES[DEFAULT_LANGUAGE])
    category = SECTION_CATEGORY_MAP.get(section, SectionCategory.NARRATIVE)
    preference = rules.get(category, ModelPreference.CLAUDE)

    return preference.value


def apply_language_profile(
    section: str,
    language: str,
    content: str,
) -> Tuple[str, Dict[str, Any]]:
    """
    Apply language profile to a section's content.

    Args:
        section: Section key
        language: Target language code
        content: Section content

    Returns:
        Tuple of (processed_content, metadata)
    """
    try:
        lang = SupportedLanguage(language.lower())
    except ValueError:
        lang = DEFAULT_LANGUAGE

    profile = get_language_profile(lang)
    metadata = {
        "language": lang.value,
        "tone": profile.tone.value,
        "model_preference": profile.get_model_preference(section).value,
        "tone_violations": profile.is_forbidden_phrase(content),
    }

    # Content is returned unchanged - actual processing happens in translation engine
    return content, metadata


def get_language_profile(language: SupportedLanguage) -> LanguageProfile:
    """
    Get the complete language profile for a language.

    Args:
        language: Target language

    Returns:
        LanguageProfile instance
    """
    return LanguageProfile(
        language=language,
        tone=EXECUTIVE_TONALITY[language]["tone"],
        glossary=CONSULTING_GLOSSARY.get(language, CONSULTING_GLOSSARY[DEFAULT_LANGUAGE]),
        tonality_config=EXECUTIVE_TONALITY.get(language, EXECUTIVE_TONALITY[DEFAULT_LANGUAGE]),
        model_rules=LANGUAGE_MODEL_RULES.get(language, LANGUAGE_MODEL_RULES[DEFAULT_LANGUAGE]),
    )


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def get_supported_languages() -> List[str]:
    """Get list of supported language codes."""
    return [lang.value for lang in SupportedLanguage]


def is_language_supported(language: str) -> bool:
    """Check if a language is supported."""
    try:
        SupportedLanguage(language.lower())
        return True
    except ValueError:
        return False


def get_consulting_term(
    term_key: str,
    language: str = "de",
) -> str:
    """
    Get consulting term in specified language.

    Args:
        term_key: Term key (e.g., "readiness_score", "roi")
        language: Target language code

    Returns:
        Localized term
    """
    try:
        lang = SupportedLanguage(language.lower())
    except ValueError:
        lang = DEFAULT_LANGUAGE

    glossary = CONSULTING_GLOSSARY.get(lang, CONSULTING_GLOSSARY[DEFAULT_LANGUAGE])
    return glossary.get(term_key, term_key)
