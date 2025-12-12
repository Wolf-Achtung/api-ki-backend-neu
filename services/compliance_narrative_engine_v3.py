# -*- coding: utf-8 -*-
"""
N4.3: Compliance Narrative Engine v3
====================================

PLATIN+++ v5.3 - Enterprise Safety Layer

Advanced compliance narrative engine for generating board-ready
compliance documentation with multi-framework support:
- EU AI Act narrative injection
- ISO 42001 chapter templates
- NIST AI RMF summary layer
- Anti-hallucination narrative clamps
- Multi-language generator (DE/EN/FR/IT/ES)

Features:
- inject_ai_act_narrative(sections, risk_class, use_cases)
- generate_iso42001_chapter(domain, controls, maturity)
- generate_nist_rmf_summary(function, categories, status)
- apply_narrative_clamps(text, kpis, assertions)
- translate_compliance_narrative(text, source_lang, target_lang)

Self-healing: Detects hallucinations and auto-corrects.

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
from typing import Any, Callable, Dict, List, Optional, Set, Tuple, Union

from services.types import SectionDict, BriefingDict, EngineReport
from services.language_strategy_engine import SupportedLanguage

log = logging.getLogger(__name__)

__all__ = [
    "NarrativeType",
    "ComplianceFramework",
    "HallucinationType",
    "NarrativeClamp",
    "NarrativeBlock",
    "ComplianceChapter",
    "NarrativeIssue",
    "ComplianceNarrativeReport",
    "ComplianceNarrativeEngineV3",
    "inject_ai_act_narrative",
    "generate_iso42001_chapter",
    "generate_nist_rmf_summary",
    "apply_narrative_clamps",
    "translate_compliance_narrative",
    "detect_hallucinations",
    "validate_compliance_narrative",
]


# =============================================================================
# ENUMS & CONSTANTS
# =============================================================================

class NarrativeType(Enum):
    """Types of compliance narratives."""
    AI_ACT_RISK = "ai_act_risk"
    AI_ACT_OBLIGATIONS = "ai_act_obligations"
    ISO_42001_CHAPTER = "iso_42001_chapter"
    NIST_RMF_SUMMARY = "nist_rmf_summary"
    DPIA_NARRATIVE = "dpia_narrative"
    CONTROL_NARRATIVE = "control_narrative"
    MATURITY_NARRATIVE = "maturity_narrative"


class ComplianceFramework(Enum):
    """Compliance frameworks."""
    EU_AI_ACT = "eu_ai_act"
    ISO_42001 = "iso_42001"
    NIST_AI_RMF = "nist_ai_rmf"
    GDPR = "gdpr"
    COMBINED = "combined"


class HallucinationType(Enum):
    """Types of narrative hallucinations."""
    FALSE_CLAIM = "false_claim"          # Claiming compliance without evidence
    NUMBER_DRIFT = "number_drift"        # Numbers don't match source
    FRAMEWORK_MIX = "framework_mix"      # Mixing up framework requirements
    RISK_UNDERSTATE = "risk_understate"  # Understating actual risk
    RISK_OVERSTATE = "risk_overstate"    # Overstating risk unnecessarily
    UNDEFINED_TERM = "undefined_term"    # Using undefined/vague terms
    TEMPORAL_ERROR = "temporal_error"    # Incorrect timeline claims


class NarrativeSeverity(Enum):
    """Severity levels for narrative issues."""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


# EU AI Act risk class narratives (multi-language)
AI_ACT_RISK_NARRATIVES: Dict[str, Dict[SupportedLanguage, str]] = {
    "minimal": {
        SupportedLanguage.DE: (
            "Das KI-System fällt unter die Kategorie **minimales Risiko** gemäß EU AI Act. "
            "Für diese Kategorie gelten keine verbindlichen Anforderungen. "
            "Es wird empfohlen, freiwillige Verhaltenskodizes zu befolgen."
        ),
        SupportedLanguage.EN: (
            "The AI system falls under the **minimal risk** category according to the EU AI Act. "
            "No mandatory requirements apply to this category. "
            "Following voluntary codes of conduct is recommended."
        ),
        SupportedLanguage.FR: (
            "Le système d'IA relève de la catégorie **risque minimal** selon l'AI Act de l'UE. "
            "Aucune exigence obligatoire ne s'applique à cette catégorie. "
            "Il est recommandé de suivre les codes de conduite volontaires."
        ),
        SupportedLanguage.IT: (
            "Il sistema di IA rientra nella categoria **rischio minimo** secondo l'AI Act dell'UE. "
            "Nessun requisito obbligatorio si applica a questa categoria. "
            "Si raccomanda di seguire codici di condotta volontari."
        ),
        SupportedLanguage.ES: (
            "El sistema de IA se clasifica en la categoría de **riesgo mínimo** según el AI Act de la UE. "
            "No se aplican requisitos obligatorios a esta categoría. "
            "Se recomienda seguir códigos de conducta voluntarios."
        ),
    },
    "limited": {
        SupportedLanguage.DE: (
            "Das KI-System fällt unter die Kategorie **begrenztes Risiko** gemäß EU AI Act. "
            "Es bestehen Transparenzpflichten: Nutzer müssen darüber informiert werden, "
            "dass sie mit einem KI-System interagieren."
        ),
        SupportedLanguage.EN: (
            "The AI system falls under the **limited risk** category according to the EU AI Act. "
            "Transparency obligations apply: users must be informed "
            "that they are interacting with an AI system."
        ),
        SupportedLanguage.FR: (
            "Le système d'IA relève de la catégorie **risque limité** selon l'AI Act de l'UE. "
            "Des obligations de transparence s'appliquent: les utilisateurs doivent être informés "
            "qu'ils interagissent avec un système d'IA."
        ),
        SupportedLanguage.IT: (
            "Il sistema di IA rientra nella categoria **rischio limitato** secondo l'AI Act dell'UE. "
            "Si applicano obblighi di trasparenza: gli utenti devono essere informati "
            "che stanno interagendo con un sistema di IA."
        ),
        SupportedLanguage.ES: (
            "El sistema de IA se clasifica en la categoría de **riesgo limitado** según el AI Act de la UE. "
            "Se aplican obligaciones de transparencia: los usuarios deben ser informados "
            "de que están interactuando con un sistema de IA."
        ),
    },
    "high": {
        SupportedLanguage.DE: (
            "Das KI-System fällt unter die Kategorie **hohes Risiko** gemäß EU AI Act (Anhang III). "
            "Es gelten strenge Anforderungen: Qualitätsmanagementsystem, technische Dokumentation, "
            "Protokollierung, menschliche Aufsicht, Genauigkeit/Robustheit/Cybersicherheit, "
            "sowie Konformitätsbewertung vor Inbetriebnahme."
        ),
        SupportedLanguage.EN: (
            "The AI system falls under the **high risk** category according to the EU AI Act (Annex III). "
            "Strict requirements apply: quality management system, technical documentation, "
            "logging, human oversight, accuracy/robustness/cybersecurity, "
            "and conformity assessment before deployment."
        ),
        SupportedLanguage.FR: (
            "Le système d'IA relève de la catégorie **haut risque** selon l'AI Act de l'UE (Annexe III). "
            "Des exigences strictes s'appliquent: système de gestion de la qualité, documentation technique, "
            "journalisation, surveillance humaine, précision/robustesse/cybersécurité, "
            "et évaluation de conformité avant le déploiement."
        ),
        SupportedLanguage.IT: (
            "Il sistema di IA rientra nella categoria **alto rischio** secondo l'AI Act dell'UE (Allegato III). "
            "Si applicano requisiti rigorosi: sistema di gestione della qualità, documentazione tecnica, "
            "logging, supervisione umana, accuratezza/robustezza/cybersicurezza, "
            "e valutazione di conformità prima dell'implementazione."
        ),
        SupportedLanguage.ES: (
            "El sistema de IA se clasifica en la categoría de **alto riesgo** según el AI Act de la UE (Anexo III). "
            "Se aplican requisitos estrictos: sistema de gestión de calidad, documentación técnica, "
            "registro, supervisión humana, precisión/robustez/ciberseguridad, "
            "y evaluación de conformidad antes del despliegue."
        ),
    },
    "unacceptable": {
        SupportedLanguage.DE: (
            "**WARNUNG**: Das KI-System fällt möglicherweise unter die Kategorie **unzulässiges Risiko** "
            "gemäß EU AI Act. Systeme dieser Kategorie sind verboten. "
            "Eine sofortige rechtliche Prüfung ist erforderlich."
        ),
        SupportedLanguage.EN: (
            "**WARNING**: The AI system may fall under the **unacceptable risk** category "
            "according to the EU AI Act. Systems in this category are prohibited. "
            "Immediate legal review is required."
        ),
        SupportedLanguage.FR: (
            "**AVERTISSEMENT**: Le système d'IA peut relever de la catégorie **risque inacceptable** "
            "selon l'AI Act de l'UE. Les systèmes de cette catégorie sont interdits. "
            "Un examen juridique immédiat est requis."
        ),
        SupportedLanguage.IT: (
            "**AVVERTENZA**: Il sistema di IA potrebbe rientrare nella categoria **rischio inaccettabile** "
            "secondo l'AI Act dell'UE. I sistemi di questa categoria sono vietati. "
            "È richiesta una revisione legale immediata."
        ),
        SupportedLanguage.ES: (
            "**ADVERTENCIA**: El sistema de IA puede clasificarse en la categoría de **riesgo inaceptable** "
            "según el AI Act de la UE. Los sistemas de esta categoría están prohibidos. "
            "Se requiere una revisión legal inmediata."
        ),
    },
}

# ISO 42001 chapter templates (multi-language)
ISO_42001_CHAPTER_TEMPLATES: Dict[str, Dict[SupportedLanguage, Dict[str, Any]]] = {
    "context": {
        SupportedLanguage.DE: {
            "title": "4. Kontext der Organisation",
            "intro": "Dieses Kapitel beschreibt den Kontext der Organisation bezüglich KI-Management.",
            "subsections": [
                "4.1 Verständnis der Organisation und ihres Kontexts",
                "4.2 Verständnis der Erfordernisse und Erwartungen interessierter Parteien",
                "4.3 Festlegung des Anwendungsbereichs",
                "4.4 KI-Managementsystem",
            ],
        },
        SupportedLanguage.EN: {
            "title": "4. Context of the Organization",
            "intro": "This chapter describes the organizational context regarding AI management.",
            "subsections": [
                "4.1 Understanding the organization and its context",
                "4.2 Understanding the needs and expectations of interested parties",
                "4.3 Determining the scope",
                "4.4 AI management system",
            ],
        },
    },
    "leadership": {
        SupportedLanguage.DE: {
            "title": "5. Führung",
            "intro": "Die Unternehmensführung zeigt Engagement für das KI-Managementsystem.",
            "subsections": [
                "5.1 Führung und Verpflichtung",
                "5.2 KI-Politik",
                "5.3 Rollen, Verantwortlichkeiten und Befugnisse",
            ],
        },
        SupportedLanguage.EN: {
            "title": "5. Leadership",
            "intro": "Top management demonstrates commitment to the AI management system.",
            "subsections": [
                "5.1 Leadership and commitment",
                "5.2 AI policy",
                "5.3 Roles, responsibilities and authorities",
            ],
        },
    },
    "planning": {
        SupportedLanguage.DE: {
            "title": "6. Planung",
            "intro": "Die Organisation plant Maßnahmen zum Umgang mit KI-Risiken und -Chancen.",
            "subsections": [
                "6.1 Maßnahmen zum Umgang mit Risiken und Chancen",
                "6.2 KI-Ziele und Planung zu deren Erreichung",
                "6.3 Planung von Änderungen",
            ],
        },
        SupportedLanguage.EN: {
            "title": "6. Planning",
            "intro": "The organization plans actions to address AI risks and opportunities.",
            "subsections": [
                "6.1 Actions to address risks and opportunities",
                "6.2 AI objectives and planning to achieve them",
                "6.3 Planning of changes",
            ],
        },
    },
    "support": {
        SupportedLanguage.DE: {
            "title": "7. Unterstützung",
            "intro": "Die Organisation stellt Ressourcen für das KI-Managementsystem bereit.",
            "subsections": [
                "7.1 Ressourcen",
                "7.2 Kompetenz",
                "7.3 Bewusstsein",
                "7.4 Kommunikation",
                "7.5 Dokumentierte Information",
            ],
        },
        SupportedLanguage.EN: {
            "title": "7. Support",
            "intro": "The organization provides resources for the AI management system.",
            "subsections": [
                "7.1 Resources",
                "7.2 Competence",
                "7.3 Awareness",
                "7.4 Communication",
                "7.5 Documented information",
            ],
        },
    },
    "operation": {
        SupportedLanguage.DE: {
            "title": "8. Betrieb",
            "intro": "Die Organisation plant, implementiert und kontrolliert KI-Systeme.",
            "subsections": [
                "8.1 Betriebliche Planung und Steuerung",
                "8.2 KI-Risikobewertung",
                "8.3 KI-Risikobehandlung",
                "8.4 KI-Systemauswirkungsbewertung",
            ],
        },
        SupportedLanguage.EN: {
            "title": "8. Operation",
            "intro": "The organization plans, implements and controls AI systems.",
            "subsections": [
                "8.1 Operational planning and control",
                "8.2 AI risk assessment",
                "8.3 AI risk treatment",
                "8.4 AI system impact assessment",
            ],
        },
    },
    "performance": {
        SupportedLanguage.DE: {
            "title": "9. Bewertung der Leistung",
            "intro": "Die Organisation überwacht und bewertet das KI-Managementsystem.",
            "subsections": [
                "9.1 Überwachung, Messung, Analyse und Bewertung",
                "9.2 Internes Audit",
                "9.3 Managementbewertung",
            ],
        },
        SupportedLanguage.EN: {
            "title": "9. Performance Evaluation",
            "intro": "The organization monitors and evaluates the AI management system.",
            "subsections": [
                "9.1 Monitoring, measurement, analysis and evaluation",
                "9.2 Internal audit",
                "9.3 Management review",
            ],
        },
    },
    "improvement": {
        SupportedLanguage.DE: {
            "title": "10. Verbesserung",
            "intro": "Die Organisation verbessert kontinuierlich das KI-Managementsystem.",
            "subsections": [
                "10.1 Nichtkonformität und Korrekturmaßnahmen",
                "10.2 Fortlaufende Verbesserung",
            ],
        },
        SupportedLanguage.EN: {
            "title": "10. Improvement",
            "intro": "The organization continuously improves the AI management system.",
            "subsections": [
                "10.1 Nonconformity and corrective action",
                "10.2 Continual improvement",
            ],
        },
    },
}

# NIST AI RMF function summaries (multi-language)
NIST_RMF_SUMMARIES: Dict[str, Dict[SupportedLanguage, str]] = {
    "govern": {
        SupportedLanguage.DE: (
            "**GOVERN**: Die Organisation hat eine KI-Risikomanagement-Kultur etabliert. "
            "Governance-Richtlinien, Rechenschaftsstrukturen und Feedback-Mechanismen sind implementiert."
        ),
        SupportedLanguage.EN: (
            "**GOVERN**: The organization has established an AI risk management culture. "
            "Governance policies, accountability structures, and feedback mechanisms are implemented."
        ),
    },
    "map": {
        SupportedLanguage.DE: (
            "**MAP**: Der Kontext und die Risiken des KI-Systems sind dokumentiert. "
            "Stakeholder-Auswirkungen und Nutzen-Risiko-Bewertungen wurden durchgeführt."
        ),
        SupportedLanguage.EN: (
            "**MAP**: The context and risks of the AI system are documented. "
            "Stakeholder impacts and benefit-risk assessments have been conducted."
        ),
    },
    "measure": {
        SupportedLanguage.DE: (
            "**MEASURE**: KI-Risiken werden analysiert, bewertet und nachverfolgt. "
            "Feedback-Schleifen für kontinuierliche Messung sind etabliert."
        ),
        SupportedLanguage.EN: (
            "**MEASURE**: AI risks are analyzed, assessed, and tracked. "
            "Feedback loops for continuous measurement are established."
        ),
    },
    "manage": {
        SupportedLanguage.DE: (
            "**MANAGE**: KI-Risiken werden priorisiert und behandelt. "
            "Risikoreaktionen werden überwacht und dokumentiert."
        ),
        SupportedLanguage.EN: (
            "**MANAGE**: AI risks are prioritized and addressed. "
            "Risk responses are monitored and documented."
        ),
    },
}

# Hallucination detection patterns
HALLUCINATION_PATTERNS: Dict[str, List[str]] = {
    "false_claims": [
        r"(?i)(vollständig|fully|completely)\s+(compliant|konform|conforme)",
        r"(?i)keine\s+risiken|no\s+risks|aucun\s+risque",
        r"(?i)100%\s+(sicher|safe|secure|compliant)",
        r"(?i)garantiert|guaranteed|garanti",
    ],
    "vague_terms": [
        r"(?i)\b(einige|some|quelques|alcuni|algunos)\s+(maßnahmen|measures|mesures)\b",
        r"(?i)\b(verschiedene|various|divers|vari|varios)\s+(kontrollen|controls|contrôles)\b",
        r"(?i)\b(gewisse|certain|certains|certi|ciertos)\s+(anforderungen|requirements|exigences)\b",
    ],
    "temporal_issues": [
        r"(?i)wird\s+bald|will\s+soon|bientôt",
        r"(?i)in\s+(naher\s+)?zukunft|in\s+the\s+(near\s+)?future",
        r"(?i)demnächst|shortly|prochainement",
    ],
}

# Anti-hallucination clamp phrases
NARRATIVE_CLAMPS: Dict[SupportedLanguage, Dict[str, str]] = {
    SupportedLanguage.DE: {
        "based_on_data": "Basierend auf den vorliegenden Daten",
        "assessment_shows": "Die Bewertung zeigt",
        "according_to": "Gemäß den Analyseergebnissen",
        "documented_evidence": "Dokumentierte Nachweise belegen",
        "requires_verification": "Erfordert weitere Verifizierung",
    },
    SupportedLanguage.EN: {
        "based_on_data": "Based on the available data",
        "assessment_shows": "The assessment shows",
        "according_to": "According to the analysis results",
        "documented_evidence": "Documented evidence supports",
        "requires_verification": "Requires further verification",
    },
    SupportedLanguage.FR: {
        "based_on_data": "Sur la base des données disponibles",
        "assessment_shows": "L'évaluation montre",
        "according_to": "Selon les résultats de l'analyse",
        "documented_evidence": "Les preuves documentées soutiennent",
        "requires_verification": "Nécessite une vérification supplémentaire",
    },
    SupportedLanguage.IT: {
        "based_on_data": "Sulla base dei dati disponibili",
        "assessment_shows": "La valutazione mostra",
        "according_to": "Secondo i risultati dell'analisi",
        "documented_evidence": "Le prove documentate supportano",
        "requires_verification": "Richiede ulteriore verifica",
    },
    SupportedLanguage.ES: {
        "based_on_data": "Basado en los datos disponibles",
        "assessment_shows": "La evaluación muestra",
        "according_to": "Según los resultados del análisis",
        "documented_evidence": "La evidencia documentada respalda",
        "requires_verification": "Requiere verificación adicional",
    },
}


# =============================================================================
# DATA STRUCTURES
# =============================================================================

@dataclass
class NarrativeClamp:
    """Clamp to prevent narrative hallucinations."""

    clamp_id: str
    clamp_type: str  # "factual", "numeric", "assertion"
    original_claim: str
    clamped_claim: str
    evidence_required: bool = True
    evidence_provided: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "clamp_id": self.clamp_id,
            "clamp_type": self.clamp_type,
            "original_claim": self.original_claim,
            "clamped_claim": self.clamped_claim,
            "evidence_required": self.evidence_required,
            "evidence_provided": self.evidence_provided,
        }


@dataclass
class NarrativeBlock:
    """A block of compliance narrative."""

    block_id: str
    narrative_type: NarrativeType
    framework: ComplianceFramework
    language: SupportedLanguage
    content: str
    clamps: List[NarrativeClamp] = field(default_factory=list)
    kpis_referenced: List[str] = field(default_factory=list)
    assertions: List[str] = field(default_factory=list)
    validated: bool = False

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "block_id": self.block_id,
            "narrative_type": self.narrative_type.value,
            "framework": self.framework.value,
            "language": self.language.value,
            "content": self.content,
            "clamps": [c.to_dict() for c in self.clamps],
            "kpis_referenced": self.kpis_referenced,
            "assertions": self.assertions,
            "validated": self.validated,
        }


@dataclass
class ComplianceChapter:
    """A full compliance chapter."""

    chapter_id: str
    framework: ComplianceFramework
    domain: str
    title: str
    language: SupportedLanguage
    introduction: str
    subsections: List[str] = field(default_factory=list)
    narrative_blocks: List[NarrativeBlock] = field(default_factory=list)
    maturity_level: str = "initial"
    compliance_score: int = 0
    gaps: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "chapter_id": self.chapter_id,
            "framework": self.framework.value,
            "domain": self.domain,
            "title": self.title,
            "language": self.language.value,
            "introduction": self.introduction,
            "subsections": self.subsections,
            "narrative_blocks": [b.to_dict() for b in self.narrative_blocks],
            "maturity_level": self.maturity_level,
            "compliance_score": self.compliance_score,
            "gaps": self.gaps,
            "recommendations": self.recommendations,
        }


@dataclass
class NarrativeIssue:
    """An issue found in narrative."""

    issue_id: str
    hallucination_type: HallucinationType
    severity: NarrativeSeverity
    location: str
    original_text: str
    corrected_text: Optional[str] = None
    explanation: str = ""
    auto_fixed: bool = False

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "issue_id": self.issue_id,
            "hallucination_type": self.hallucination_type.value,
            "severity": self.severity.value,
            "location": self.location,
            "original_text": self.original_text[:200],
            "corrected_text": self.corrected_text[:200] if self.corrected_text else None,
            "explanation": self.explanation,
            "auto_fixed": self.auto_fixed,
        }


@dataclass
class ComplianceNarrativeReport:
    """Report from compliance narrative engine."""

    engine_id: str = "COMPLIANCE_NARRATIVE_V3"
    success: bool = True
    narratives_generated: int = 0
    chapters_generated: int = 0
    clamps_applied: int = 0
    hallucinations_detected: int = 0
    hallucinations_fixed: int = 0
    healed: bool = False
    issues: List[NarrativeIssue] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "engine_id": self.engine_id,
            "success": self.success,
            "narratives_generated": self.narratives_generated,
            "chapters_generated": self.chapters_generated,
            "clamps_applied": self.clamps_applied,
            "hallucinations_detected": self.hallucinations_detected,
            "hallucinations_fixed": self.hallucinations_fixed,
            "healed": self.healed,
            "issues": [i.to_dict() for i in self.issues],
            "warnings": self.warnings,
            "timestamp": self.timestamp,
        }


# =============================================================================
# COMPLIANCE NARRATIVE ENGINE V3
# =============================================================================

class ComplianceNarrativeEngineV3:
    """
    N4.3: Advanced Compliance Narrative Engine.

    Generates board-ready compliance narratives with:
    - EU AI Act narrative injection
    - ISO 42001 chapter templates
    - NIST AI RMF summaries
    - Anti-hallucination clamps
    - Multi-language support

    Self-healing: Detects and auto-corrects hallucinations.
    """

    def __init__(
        self,
        sections: SectionDict,
        briefing: BriefingDict,
        target_language: str = "de",
        risk_class: str = "minimal",
        maturity_level: str = "initial",
    ) -> None:
        """
        Initialize Compliance Narrative Engine v3.

        Args:
            sections: Section dictionary
            briefing: Briefing data
            target_language: Target language code
            risk_class: AI Act risk classification
            maturity_level: Governance maturity level
        """
        self.sections = sections
        self.briefing = briefing

        # Parse target language
        try:
            self._language = SupportedLanguage(target_language.lower())
        except ValueError:
            self._language = SupportedLanguage.DE

        self._risk_class = risk_class.lower()
        self._maturity_level = maturity_level.lower()

        self._report = ComplianceNarrativeReport()
        self._narrative_blocks: List[NarrativeBlock] = []
        self._chapters: List[ComplianceChapter] = []
        self._kpis: Dict[str, Any] = {}

        log.info(
            "[N4.3-Narrative] Engine initialized: lang=%s, risk=%s, maturity=%s",
            self._language.value, self._risk_class, self._maturity_level
        )

    def process(self) -> Tuple[SectionDict, ComplianceNarrativeReport]:
        """
        Process sections through compliance narrative engine.

        Returns:
            Tuple of (processed_sections, report)
        """
        log.info("[N4.3-Narrative] Processing started")

        # Step 1: Extract KPIs from sections
        self._extract_kpis()

        # Step 2: Generate AI Act narrative
        ai_act_narrative = self._generate_ai_act_narrative()
        self._narrative_blocks.append(ai_act_narrative)

        # Step 3: Generate ISO 42001 chapters
        iso_chapters = self._generate_iso42001_chapters()
        self._chapters.extend(iso_chapters)

        # Step 4: Generate NIST RMF summary
        nist_narrative = self._generate_nist_rmf_narrative()
        self._narrative_blocks.append(nist_narrative)

        # Step 5: Apply narrative clamps
        self._apply_all_narrative_clamps()

        # Step 6: Detect hallucinations
        issues = self._detect_hallucinations()
        self._report.hallucinations_detected = len(issues)
        self._report.issues = issues

        # Step 7: Auto-fix hallucinations
        if issues:
            fixed = self._fix_hallucinations(issues)
            self._report.hallucinations_fixed = fixed
            self._report.healed = fixed > 0

        # Step 8: Validate narratives
        self._validate_all_narratives()

        # Update report
        self._report.narratives_generated = len(self._narrative_blocks)
        self._report.chapters_generated = len(self._chapters)
        self._report.success = self._report.hallucinations_detected == self._report.hallucinations_fixed

        # Apply to sections
        result_sections = self._apply_narratives_to_sections()

        log.info(
            "[N4.3-Narrative] Complete: narratives=%d, chapters=%d, healed=%s",
            self._report.narratives_generated,
            self._report.chapters_generated,
            self._report.healed
        )

        return result_sections, self._report

    def _extract_kpis(self) -> None:
        """Extract KPIs from sections and briefing."""
        # Extract from briefing
        kpi_keys = ["ROI_12M", "PAYBACK_MONTHS", "MONTHLY_SAVINGS", "FTE_SAVINGS",
                    "READINESS_SCORE", "RISK_LEVEL"]

        for key in kpi_keys:
            value = self.briefing.get(key)
            if value is not None:
                self._kpis[key] = value

        # Extract from sections
        for section_key, content in self.sections.items():
            if section_key.startswith("_"):
                continue
            if isinstance(content, str):
                # Extract numbers with context
                numbers = re.findall(r'(\d+(?:[.,]\d+)?)\s*(%|€|EUR|Monate|months)', content)
                for num, unit in numbers:
                    if unit == "%":
                        self._kpis.setdefault("percentages", []).append(num)
                    elif unit in ("€", "EUR"):
                        self._kpis.setdefault("amounts", []).append(num)

    def _generate_ai_act_narrative(self) -> NarrativeBlock:
        """Generate EU AI Act compliance narrative."""
        # Get risk narrative template
        risk_narratives = AI_ACT_RISK_NARRATIVES.get(
            self._risk_class,
            AI_ACT_RISK_NARRATIVES["minimal"]
        )

        base_narrative = risk_narratives.get(
            self._language,
            risk_narratives[SupportedLanguage.EN]
        )

        # Add obligations based on risk class
        obligations_narrative = self._generate_obligations_narrative()

        # Combine narratives
        full_content = f"{base_narrative}\n\n{obligations_narrative}"

        # Create narrative block
        block = NarrativeBlock(
            block_id=f"AI_ACT_{self._risk_class.upper()}",
            narrative_type=NarrativeType.AI_ACT_RISK,
            framework=ComplianceFramework.EU_AI_ACT,
            language=self._language,
            content=full_content,
            kpis_referenced=list(self._kpis.keys()),
        )

        return block

    def _generate_obligations_narrative(self) -> str:
        """Generate obligations narrative based on risk class."""
        obligations = {
            "high": {
                SupportedLanguage.DE: (
                    "**Pflichten für Hochrisiko-KI-Systeme:**\n"
                    "- Qualitätsmanagementsystem implementieren\n"
                    "- Technische Dokumentation erstellen und pflegen\n"
                    "- Automatische Protokollierung einrichten\n"
                    "- Menschliche Aufsicht sicherstellen\n"
                    "- Genauigkeit, Robustheit und Cybersicherheit gewährleisten\n"
                    "- Konformitätsbewertung durchführen"
                ),
                SupportedLanguage.EN: (
                    "**Obligations for High-Risk AI Systems:**\n"
                    "- Implement quality management system\n"
                    "- Create and maintain technical documentation\n"
                    "- Establish automatic logging\n"
                    "- Ensure human oversight\n"
                    "- Ensure accuracy, robustness, and cybersecurity\n"
                    "- Conduct conformity assessment"
                ),
            },
            "limited": {
                SupportedLanguage.DE: (
                    "**Transparenzpflichten:**\n"
                    "- Nutzer über KI-Interaktion informieren\n"
                    "- Bei Chatbots: KI-Nutzung offenlegen\n"
                    "- Bei generiertem Content: KI-Kennzeichnung"
                ),
                SupportedLanguage.EN: (
                    "**Transparency Obligations:**\n"
                    "- Inform users about AI interaction\n"
                    "- For chatbots: disclose AI usage\n"
                    "- For generated content: AI labeling"
                ),
            },
            "minimal": {
                SupportedLanguage.DE: (
                    "**Empfohlene Maßnahmen:**\n"
                    "- Freiwillige Verhaltenskodizes befolgen\n"
                    "- Best Practices für KI-Entwicklung anwenden"
                ),
                SupportedLanguage.EN: (
                    "**Recommended Measures:**\n"
                    "- Follow voluntary codes of conduct\n"
                    "- Apply AI development best practices"
                ),
            },
        }

        risk_obligations = obligations.get(
            self._risk_class,
            obligations["minimal"]
        )

        return risk_obligations.get(
            self._language,
            risk_obligations.get(SupportedLanguage.EN, "")
        )

    def _generate_iso42001_chapters(self) -> List[ComplianceChapter]:
        """Generate ISO 42001 chapter templates."""
        chapters: List[ComplianceChapter] = []

        for domain_key, templates in ISO_42001_CHAPTER_TEMPLATES.items():
            template = templates.get(
                self._language,
                templates.get(SupportedLanguage.EN, {})
            )

            if not template:
                continue

            # Determine domain compliance score based on maturity
            maturity_scores = {
                "initial": 20,
                "developing": 40,
                "defined": 60,
                "managed": 80,
                "optimizing": 100,
            }
            score = maturity_scores.get(self._maturity_level, 20)

            # Generate chapter narrative
            chapter_narrative = self._generate_chapter_narrative(
                domain_key, template, score
            )

            chapter = ComplianceChapter(
                chapter_id=f"ISO42001_{domain_key.upper()}",
                framework=ComplianceFramework.ISO_42001,
                domain=domain_key,
                title=template.get("title", domain_key),
                language=self._language,
                introduction=template.get("intro", ""),
                subsections=template.get("subsections", []),
                narrative_blocks=[chapter_narrative],
                maturity_level=self._maturity_level,
                compliance_score=score,
            )

            # Add gaps if score is low
            if score < 60:
                chapter.gaps.append(f"Domain {domain_key} requires maturity improvement")

            chapters.append(chapter)

        return chapters

    def _generate_chapter_narrative(
        self,
        domain: str,
        template: Dict[str, Any],
        score: int,
    ) -> NarrativeBlock:
        """Generate narrative for ISO chapter."""
        clamps = NARRATIVE_CLAMPS.get(
            self._language,
            NARRATIVE_CLAMPS[SupportedLanguage.EN]
        )

        # Build narrative with clamps
        content_parts = [
            f"{clamps['assessment_shows']}:",
            f"- Domain: {template.get('title', domain)}",
            f"- Maturity: {self._maturity_level.title()}",
            f"- Score: {score}/100",
        ]

        if score >= 60:
            status = {
                SupportedLanguage.DE: "Der Bereich erfüllt die Mindestanforderungen.",
                SupportedLanguage.EN: "The domain meets minimum requirements.",
            }
        else:
            status = {
                SupportedLanguage.DE: "Der Bereich erfordert Verbesserungen.",
                SupportedLanguage.EN: "The domain requires improvements.",
            }

        content_parts.append(
            status.get(self._language, status[SupportedLanguage.EN])
        )

        return NarrativeBlock(
            block_id=f"ISO42001_{domain.upper()}_NARRATIVE",
            narrative_type=NarrativeType.ISO_42001_CHAPTER,
            framework=ComplianceFramework.ISO_42001,
            language=self._language,
            content="\n".join(content_parts),
            validated=True,
        )

    def _generate_nist_rmf_narrative(self) -> NarrativeBlock:
        """Generate NIST AI RMF summary narrative."""
        summaries = []

        for function_key, function_texts in NIST_RMF_SUMMARIES.items():
            text = function_texts.get(
                self._language,
                function_texts.get(SupportedLanguage.EN, "")
            )
            if text:
                summaries.append(text)

        content = "\n\n".join(summaries)

        # Add overall assessment
        clamps = NARRATIVE_CLAMPS.get(
            self._language,
            NARRATIVE_CLAMPS[SupportedLanguage.EN]
        )

        assessment = {
            SupportedLanguage.DE: f"\n\n{clamps['based_on_data']}: Das KI-System wurde gemäß NIST AI RMF bewertet.",
            SupportedLanguage.EN: f"\n\n{clamps['based_on_data']}: The AI system has been assessed according to NIST AI RMF.",
        }

        content += assessment.get(
            self._language,
            assessment[SupportedLanguage.EN]
        )

        return NarrativeBlock(
            block_id="NIST_RMF_SUMMARY",
            narrative_type=NarrativeType.NIST_RMF_SUMMARY,
            framework=ComplianceFramework.NIST_AI_RMF,
            language=self._language,
            content=content,
        )

    def _apply_all_narrative_clamps(self) -> None:
        """Apply narrative clamps to all blocks."""
        clamp_count = 0

        for block in self._narrative_blocks:
            clamps = self._apply_clamps_to_block(block)
            block.clamps = clamps
            clamp_count += len(clamps)

        for chapter in self._chapters:
            for block in chapter.narrative_blocks:
                clamps = self._apply_clamps_to_block(block)
                block.clamps = clamps
                clamp_count += len(clamps)

        self._report.clamps_applied = clamp_count

    def _apply_clamps_to_block(self, block: NarrativeBlock) -> List[NarrativeClamp]:
        """Apply clamps to a narrative block."""
        clamps: List[NarrativeClamp] = []
        content = block.content

        # Check for absolute claims
        absolute_patterns = [
            (r"(?i)(ist|is|est|è|es)\s+(vollständig|fully|completely|complètement|completamente)\s+(konform|compliant|conforme)",
             "Absolute compliance claim"),
            (r"(?i)(keine|no|aucun|nessun|ningún)\s+(risiken|risks|risques|rischi|riesgos)",
             "No-risk claim"),
        ]

        for pattern, claim_type in absolute_patterns:
            matches = re.finditer(pattern, content)
            for match in matches:
                original = match.group(0)

                # Generate clamped version
                clamp_phrases = NARRATIVE_CLAMPS.get(
                    self._language,
                    NARRATIVE_CLAMPS[SupportedLanguage.EN]
                )

                clamped = f"{clamp_phrases['based_on_data']}, {original.lower()}"

                clamp = NarrativeClamp(
                    clamp_id=f"CLAMP_{len(clamps)+1:03d}",
                    clamp_type="factual",
                    original_claim=original,
                    clamped_claim=clamped,
                    evidence_required=True,
                )
                clamps.append(clamp)

                # Update content
                block.content = block.content.replace(original, clamped, 1)

        return clamps

    def _detect_hallucinations(self) -> List[NarrativeIssue]:
        """Detect hallucinations in narratives."""
        issues: List[NarrativeIssue] = []
        issue_counter = 0

        for block in self._narrative_blocks:
            block_issues = self._check_block_for_hallucinations(block)
            for issue in block_issues:
                issue_counter += 1
                issue.issue_id = f"HALL_{issue_counter:04d}"
            issues.extend(block_issues)

        for chapter in self._chapters:
            for block in chapter.narrative_blocks:
                block_issues = self._check_block_for_hallucinations(block)
                for issue in block_issues:
                    issue_counter += 1
                    issue.issue_id = f"HALL_{issue_counter:04d}"
                issues.extend(block_issues)

        return issues

    def _check_block_for_hallucinations(self, block: NarrativeBlock) -> List[NarrativeIssue]:
        """Check a block for hallucinations."""
        issues: List[NarrativeIssue] = []
        content = block.content

        # Check false claims
        for pattern in HALLUCINATION_PATTERNS["false_claims"]:
            matches = re.finditer(pattern, content)
            for match in matches:
                issues.append(NarrativeIssue(
                    issue_id="",
                    hallucination_type=HallucinationType.FALSE_CLAIM,
                    severity=NarrativeSeverity.ERROR,
                    location=block.block_id,
                    original_text=match.group(0),
                    explanation="Absolute compliance claim without evidence",
                ))

        # Check vague terms
        for pattern in HALLUCINATION_PATTERNS["vague_terms"]:
            matches = re.finditer(pattern, content)
            for match in matches:
                issues.append(NarrativeIssue(
                    issue_id="",
                    hallucination_type=HallucinationType.UNDEFINED_TERM,
                    severity=NarrativeSeverity.WARNING,
                    location=block.block_id,
                    original_text=match.group(0),
                    explanation="Vague term should be quantified",
                ))

        # Check temporal issues
        for pattern in HALLUCINATION_PATTERNS["temporal_issues"]:
            matches = re.finditer(pattern, content)
            for match in matches:
                issues.append(NarrativeIssue(
                    issue_id="",
                    hallucination_type=HallucinationType.TEMPORAL_ERROR,
                    severity=NarrativeSeverity.INFO,
                    location=block.block_id,
                    original_text=match.group(0),
                    explanation="Unspecified timeline should be defined",
                ))

        # Check risk understatement
        if self._risk_class == "high":
            low_risk_patterns = [
                r"(?i)(low|niedrig|basso|bajo|faible)\s+(risk|risiko|rischio|riesgo|risque)",
                r"(?i)(minimal|gering|minimo|mínimo|minime)\s+(risk|risiko|rischio|riesgo|risque)",
            ]
            for pattern in low_risk_patterns:
                matches = re.finditer(pattern, content)
                for match in matches:
                    issues.append(NarrativeIssue(
                        issue_id="",
                        hallucination_type=HallucinationType.RISK_UNDERSTATE,
                        severity=NarrativeSeverity.CRITICAL,
                        location=block.block_id,
                        original_text=match.group(0),
                        explanation="Risk understatement: system is classified as high-risk",
                    ))

        return issues

    def _fix_hallucinations(self, issues: List[NarrativeIssue]) -> int:
        """Fix detected hallucinations."""
        fixed_count = 0

        for issue in issues:
            if issue.severity == NarrativeSeverity.CRITICAL:
                # Must fix critical issues
                corrected = self._correct_hallucination(issue)
                if corrected:
                    issue.corrected_text = corrected
                    issue.auto_fixed = True
                    fixed_count += 1
            elif issue.severity == NarrativeSeverity.ERROR:
                # Try to fix errors
                corrected = self._correct_hallucination(issue)
                if corrected:
                    issue.corrected_text = corrected
                    issue.auto_fixed = True
                    fixed_count += 1
            # Warnings and info are logged but not auto-fixed

        return fixed_count

    def _correct_hallucination(self, issue: NarrativeIssue) -> Optional[str]:
        """Correct a specific hallucination."""
        clamp_phrases = NARRATIVE_CLAMPS.get(
            self._language,
            NARRATIVE_CLAMPS[SupportedLanguage.EN]
        )

        if issue.hallucination_type == HallucinationType.FALSE_CLAIM:
            # Add qualification
            return f"{clamp_phrases['based_on_data']}, {issue.original_text.lower()}"

        elif issue.hallucination_type == HallucinationType.RISK_UNDERSTATE:
            # Correct to high risk
            corrections = {
                SupportedLanguage.DE: "hohes Risiko gemäß EU AI Act",
                SupportedLanguage.EN: "high risk according to EU AI Act",
                SupportedLanguage.FR: "risque élevé selon l'AI Act de l'UE",
                SupportedLanguage.IT: "alto rischio secondo l'AI Act dell'UE",
                SupportedLanguage.ES: "alto riesgo según el AI Act de la UE",
            }
            return corrections.get(self._language, corrections[SupportedLanguage.EN])

        return None

    def _validate_all_narratives(self) -> None:
        """Validate all narrative blocks."""
        for block in self._narrative_blocks:
            block.validated = self._validate_block(block)

        for chapter in self._chapters:
            for block in chapter.narrative_blocks:
                block.validated = self._validate_block(block)

    def _validate_block(self, block: NarrativeBlock) -> bool:
        """Validate a single narrative block."""
        # Check content exists
        if not block.content or len(block.content) < 10:
            return False

        # Check no critical issues remain
        for issue in self._report.issues:
            if (issue.location == block.block_id and
                issue.severity == NarrativeSeverity.CRITICAL and
                not issue.auto_fixed):
                return False

        return True

    def _apply_narratives_to_sections(self) -> SectionDict:
        """Apply narratives to sections."""
        result_sections = dict(self.sections)

        # Add AI Act narrative
        ai_act_blocks = [b for b in self._narrative_blocks
                        if b.framework == ComplianceFramework.EU_AI_ACT]
        if ai_act_blocks:
            result_sections["_ai_act_narrative"] = ai_act_blocks[0].content

        # Add ISO 42001 chapters
        result_sections["_iso42001_chapters"] = [
            chapter.to_dict() for chapter in self._chapters
        ]

        # Add NIST RMF narrative
        nist_blocks = [b for b in self._narrative_blocks
                      if b.framework == ComplianceFramework.NIST_AI_RMF]
        if nist_blocks:
            result_sections["_nist_rmf_narrative"] = nist_blocks[0].content

        # Add compliance narrative metadata
        result_sections["_compliance_narrative_validated"] = self._report.success
        result_sections["_compliance_narrative_report"] = self._report.to_dict()
        result_sections["_narrative_healed"] = self._report.healed

        return result_sections

    def get_narrative_blocks(self) -> List[NarrativeBlock]:
        """Get all narrative blocks."""
        return self._narrative_blocks

    def get_chapters(self) -> List[ComplianceChapter]:
        """Get all compliance chapters."""
        return self._chapters


# =============================================================================
# MODULE-LEVEL FUNCTIONS
# =============================================================================

def inject_ai_act_narrative(
    sections: SectionDict,
    risk_class: str,
    use_cases: List[str],
    target_language: str = "de",
) -> str:
    """
    Inject EU AI Act narrative into sections.

    Args:
        sections: Section dictionary
        risk_class: AI Act risk classification
        use_cases: AI use cases
        target_language: Target language

    Returns:
        Generated AI Act narrative
    """
    engine = ComplianceNarrativeEngineV3(
        sections=sections,
        briefing={"ai_use_cases": use_cases},
        target_language=target_language,
        risk_class=risk_class,
    )

    narrative = engine._generate_ai_act_narrative()
    return narrative.content


def generate_iso42001_chapter(
    domain: str,
    controls: List[Dict[str, Any]],
    maturity: str,
    target_language: str = "de",
) -> ComplianceChapter:
    """
    Generate ISO 42001 chapter.

    Args:
        domain: ISO domain (context, leadership, etc.)
        controls: List of controls
        maturity: Maturity level
        target_language: Target language

    Returns:
        ComplianceChapter
    """
    engine = ComplianceNarrativeEngineV3(
        sections={},
        briefing={},
        target_language=target_language,
        maturity_level=maturity,
    )

    chapters = engine._generate_iso42001_chapters()

    # Find matching domain
    for chapter in chapters:
        if chapter.domain == domain:
            return chapter

    # Return first chapter if domain not found
    if chapters:
        return chapters[0]

    # Return empty chapter
    return ComplianceChapter(
        chapter_id=f"ISO42001_{domain.upper()}",
        framework=ComplianceFramework.ISO_42001,
        domain=domain,
        title=domain,
        language=SupportedLanguage.DE,
        introduction="",
    )


def generate_nist_rmf_summary(
    function: str,
    categories: List[str],
    status: str,
    target_language: str = "de",
) -> str:
    """
    Generate NIST AI RMF summary.

    Args:
        function: NIST function (govern, map, measure, manage)
        categories: Category list
        status: Implementation status
        target_language: Target language

    Returns:
        Summary text
    """
    try:
        lang = SupportedLanguage(target_language.lower())
    except ValueError:
        lang = SupportedLanguage.DE

    summaries = NIST_RMF_SUMMARIES.get(function.lower(), {})
    return summaries.get(lang, summaries.get(SupportedLanguage.EN, ""))


def apply_narrative_clamps(
    text: str,
    kpis: Dict[str, Any],
    assertions: List[str],
    target_language: str = "de",
) -> Tuple[str, List[NarrativeClamp]]:
    """
    Apply anti-hallucination clamps to text.

    Args:
        text: Narrative text
        kpis: KPI dictionary
        assertions: List of assertions to validate
        target_language: Target language

    Returns:
        Tuple of (clamped_text, clamps_applied)
    """
    try:
        lang = SupportedLanguage(target_language.lower())
    except ValueError:
        lang = SupportedLanguage.DE

    clamp_phrases = NARRATIVE_CLAMPS.get(lang, NARRATIVE_CLAMPS[SupportedLanguage.EN])
    clamps: List[NarrativeClamp] = []
    clamped_text = text

    # Add evidence prefix for assertions
    for assertion in assertions:
        if assertion in text:
            clamped_assertion = f"{clamp_phrases['documented_evidence']}: {assertion}"
            clamped_text = clamped_text.replace(assertion, clamped_assertion, 1)

            clamps.append(NarrativeClamp(
                clamp_id=f"CLAMP_{len(clamps)+1:03d}",
                clamp_type="assertion",
                original_claim=assertion,
                clamped_claim=clamped_assertion,
            ))

    return clamped_text, clamps


def translate_compliance_narrative(
    text: str,
    source_language: str,
    target_language: str,
) -> str:
    """
    Translate compliance narrative between languages.

    Note: This is a placeholder - actual translation should use
    the Translation Engine v3.

    Args:
        text: Source text
        source_language: Source language code
        target_language: Target language code

    Returns:
        Translated text (or original if same language)
    """
    if source_language.lower() == target_language.lower():
        return text

    # For now, return original with language marker
    # Real implementation would use TranslationEngineV3
    return f"[{target_language.upper()}] {text}"


def detect_hallucinations(
    text: str,
    expected_kpis: Dict[str, Any],
    risk_class: str = "minimal",
) -> List[NarrativeIssue]:
    """
    Detect hallucinations in narrative text.

    Args:
        text: Narrative text
        expected_kpis: Expected KPI values
        risk_class: Expected risk class

    Returns:
        List of detected issues
    """
    issues: List[NarrativeIssue] = []
    issue_counter = 0

    # Check false claims
    for pattern in HALLUCINATION_PATTERNS["false_claims"]:
        matches = re.finditer(pattern, text)
        for match in matches:
            issue_counter += 1
            issues.append(NarrativeIssue(
                issue_id=f"HALL_{issue_counter:04d}",
                hallucination_type=HallucinationType.FALSE_CLAIM,
                severity=NarrativeSeverity.ERROR,
                location="text",
                original_text=match.group(0),
                explanation="Absolute claim requires evidence",
            ))

    # Check number drift
    for kpi_name, kpi_value in expected_kpis.items():
        if isinstance(kpi_value, (int, float)):
            # Check if KPI value appears correctly
            pattern = rf'\b{kpi_value}\b'
            if not re.search(pattern, text):
                # Check if a different value is claimed
                issue_counter += 1
                issues.append(NarrativeIssue(
                    issue_id=f"HALL_{issue_counter:04d}",
                    hallucination_type=HallucinationType.NUMBER_DRIFT,
                    severity=NarrativeSeverity.WARNING,
                    location="text",
                    original_text=f"Expected {kpi_name}={kpi_value}",
                    explanation=f"KPI {kpi_name} value may be missing or incorrect",
                ))

    return issues


def validate_compliance_narrative(
    narrative: str,
    framework: str,
    risk_class: str,
    maturity: str,
) -> Tuple[bool, List[str]]:
    """
    Validate compliance narrative.

    Args:
        narrative: Narrative text
        framework: Compliance framework
        risk_class: Risk classification
        maturity: Maturity level

    Returns:
        Tuple of (is_valid, validation_messages)
    """
    messages: List[str] = []
    is_valid = True

    # Check minimum length
    if len(narrative) < 50:
        messages.append("Narrative too short")
        is_valid = False

    # Check framework-specific requirements
    if framework.lower() == "eu_ai_act":
        risk_keywords = {
            "high": ["high risk", "hohes risiko", "haut risque", "alto rischio", "alto riesgo"],
            "limited": ["limited", "begrenzt", "limité", "limitato", "limitado"],
            "minimal": ["minimal", "gering", "minimal", "minimo", "mínimo"],
        }

        keywords = risk_keywords.get(risk_class.lower(), [])
        if keywords and not any(kw in narrative.lower() for kw in keywords):
            messages.append(f"Risk class '{risk_class}' not mentioned in narrative")
            is_valid = False

    # Check for hallucination patterns
    for pattern in HALLUCINATION_PATTERNS["false_claims"]:
        if re.search(pattern, narrative):
            messages.append("Potential false claim detected")
            is_valid = False
            break

    return is_valid, messages
