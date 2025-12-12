# -*- coding: utf-8 -*-
"""
N4.2: Integration Module
========================

PLATIN+++ v5.2 - Multi-Language Intelligence Layer

Central integration point for N4.2 components in gpt_analyze.py pipeline.

Pipeline Integration Points:
1. detect_target_language() - Early in pipeline
2. LanguageStrategyEngine.apply() - After briefing load
3. Main Translation Pass - After section generation
4. Layout Language Adaption - Before render
5. Consistency Engine G22-X - Before render
6. PDF Render - Final stage

Version: 1.0.0 (N4.2 - PLATIN+++ v5.2)
Author: Claude + Wolf
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

from services.types import SectionDict, BriefingDict, EngineReport

log = logging.getLogger(__name__)

__all__ = [
    "N42PipelineStage",
    "N42IntegrationReport",
    "N42Pipeline",
    "apply_n42_pipeline",
    "detect_target_language",
    "apply_language_strategy",
    "apply_translation_pass",
    "apply_layout_adaptation",
    "apply_consistency_check",
    "get_n42_version",
]

# N4.2 Version
N42_VERSION = "5.2.0-PLATIN+++"


# =============================================================================
# PIPELINE STAGES
# =============================================================================

class N42PipelineStage:
    """N4.2 Pipeline stages."""
    LANGUAGE_DETECTION = "language_detection"
    LANGUAGE_STRATEGY = "language_strategy"
    TRANSLATION = "translation"
    LAYOUT_ADAPTATION = "layout_adaptation"
    CONSISTENCY_CHECK = "consistency_check"


# =============================================================================
# DATA STRUCTURES
# =============================================================================

@dataclass
class StageResult:
    """Result of a pipeline stage."""
    stage: str
    success: bool
    duration_ms: int = 0
    issues: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class N42IntegrationReport:
    """Complete N4.2 integration report."""

    version: str = N42_VERSION
    success: bool = True
    source_language: Optional[str] = None
    target_language: Optional[str] = None
    stages_completed: List[str] = field(default_factory=list)
    stages_skipped: List[str] = field(default_factory=list)
    stage_results: Dict[str, StageResult] = field(default_factory=dict)
    total_duration_ms: int = 0
    issues: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())

    def add_stage_result(self, result: StageResult) -> None:
        """Add a stage result."""
        self.stage_results[result.stage] = result
        if result.success:
            self.stages_completed.append(result.stage)
        else:
            self.success = False
        self.issues.extend(result.issues)
        self.warnings.extend(result.warnings)
        self.total_duration_ms += result.duration_ms

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "version": self.version,
            "success": self.success,
            "source_language": self.source_language,
            "target_language": self.target_language,
            "stages_completed": self.stages_completed,
            "stages_skipped": self.stages_skipped,
            "total_duration_ms": self.total_duration_ms,
            "issues_count": len(self.issues),
            "warnings_count": len(self.warnings),
            "timestamp": self.timestamp,
        }


# =============================================================================
# N4.2 PIPELINE
# =============================================================================

class N42Pipeline:
    """
    N4.2: Multi-Language Intelligence Pipeline.

    Orchestrates all N4.2 components in the correct order:
    1. Language Detection
    2. Language Strategy Application
    3. Translation Pass (if needed)
    4. Layout Adaptation
    5. Cross-Language Consistency Check
    """

    def __init__(
        self,
        sections: SectionDict,
        briefing: BriefingDict,
        source_language: Optional[str] = None,
        target_language: Optional[str] = None,
        enable_translation: bool = True,
    ) -> None:
        """
        Initialize N4.2 Pipeline.

        Args:
            sections: Section dictionary
            briefing: Briefing data
            source_language: Source language (auto-detected if None)
            target_language: Target language (from briefing if None)
            enable_translation: Whether to enable translation pass
        """
        self.sections = sections
        self.briefing = briefing
        self._source_lang = source_language
        self._target_lang = target_language
        self._enable_translation = enable_translation
        self._report = N42IntegrationReport()
        self._original_sections: Optional[SectionDict] = None

        log.info("[N4.2] Pipeline initialized")

    def process(self) -> Tuple[SectionDict, N42IntegrationReport]:
        """
        Process sections through N4.2 pipeline.

        Returns:
            Tuple of (processed_sections, report)
        """
        import time
        start_time = time.time()

        log.info("[N4.2] Pipeline processing started")

        try:
            # Stage 1: Language Detection
            self._stage_language_detection()

            # Stage 2: Language Strategy
            self._stage_language_strategy()

            # Stage 3: Translation (if enabled and needed)
            if self._enable_translation and self._needs_translation():
                self._stage_translation()
            else:
                self._report.stages_skipped.append(N42PipelineStage.TRANSLATION)

            # Stage 4: Layout Adaptation
            self._stage_layout_adaptation()

            # Stage 5: Consistency Check (if translation was done)
            if N42PipelineStage.TRANSLATION in self._report.stages_completed:
                self._stage_consistency_check()
            else:
                self._report.stages_skipped.append(N42PipelineStage.CONSISTENCY_CHECK)

        except Exception as e:
            log.error("[N4.2] Pipeline error: %s", str(e))
            self._report.success = False
            self._report.issues.append(f"Pipeline error: {str(e)}")

        self._report.total_duration_ms = int((time.time() - start_time) * 1000)

        # Store report in sections
        self.sections["_n42_report"] = self._report.to_dict()

        log.info(
            "[N4.2] Pipeline complete: %d stages, %dms",
            len(self._report.stages_completed),
            self._report.total_duration_ms,
        )

        return self.sections, self._report

    def _stage_language_detection(self) -> None:
        """Stage 1: Detect language."""
        import time
        start = time.time()

        try:
            from services.language_strategy_engine import detect_language

            result = detect_language(briefing_input=self.briefing)

            self._source_lang = self._source_lang or result.detected_language.value
            self._target_lang = self._target_lang or self.briefing.get("lang", self._source_lang)

            self._report.source_language = self._source_lang
            self._report.target_language = self._target_lang

            self._report.add_stage_result(StageResult(
                stage=N42PipelineStage.LANGUAGE_DETECTION,
                success=True,
                duration_ms=int((time.time() - start) * 1000),
                metadata={
                    "detected": result.detected_language.value,
                    "confidence": result.confidence,
                    "source": result.source,
                },
            ))

        except Exception as e:
            log.warning("[N4.2] Language detection failed: %s", e)
            self._source_lang = self._source_lang or "de"
            self._target_lang = self._target_lang or "de"
            self._report.source_language = self._source_lang
            self._report.target_language = self._target_lang

            self._report.add_stage_result(StageResult(
                stage=N42PipelineStage.LANGUAGE_DETECTION,
                success=False,
                duration_ms=int((time.time() - start) * 1000),
                issues=[f"Detection failed: {str(e)}"],
            ))

    def _stage_language_strategy(self) -> None:
        """Stage 2: Apply language strategy."""
        import time
        start = time.time()

        try:
            from services.language_strategy_engine import LanguageStrategyEngine

            engine = LanguageStrategyEngine(
                sections=self.sections,
                briefing=self.briefing,
                target_language=self._target_lang,
            )

            self.sections, engine_report = engine.process()

            self._report.add_stage_result(StageResult(
                stage=N42PipelineStage.LANGUAGE_STRATEGY,
                success=engine_report.success,
                duration_ms=int((time.time() - start) * 1000),
                warnings=engine_report.warnings,
                metadata={
                    "sections_processed": engine_report.sections_processed,
                    "model_selections": engine_report.model_selections,
                },
            ))

        except Exception as e:
            log.warning("[N4.2] Language strategy failed: %s", e)
            self._report.add_stage_result(StageResult(
                stage=N42PipelineStage.LANGUAGE_STRATEGY,
                success=False,
                duration_ms=int((time.time() - start) * 1000),
                issues=[f"Strategy failed: {str(e)}"],
            ))

    def _stage_translation(self) -> None:
        """Stage 3: Translation pass."""
        import time
        start = time.time()

        # Store original for consistency check
        self._original_sections = {k: v for k, v in self.sections.items()}

        try:
            from services.translation_engine_v3 import translate_sections

            self.sections, trans_report = translate_sections(
                sections=self.sections,
                source_language=self._source_lang or "de",
                target_language=self._target_lang or "en",
                briefing=self.briefing,
            )

            self._report.add_stage_result(StageResult(
                stage=N42PipelineStage.TRANSLATION,
                success=trans_report.success,
                duration_ms=int((time.time() - start) * 1000),
                warnings=trans_report.warnings,
                metadata={
                    "sections_translated": trans_report.sections_translated,
                    "avg_quality": trans_report.avg_quality_score,
                    "drift": trans_report.total_semantic_drift,
                },
            ))

        except Exception as e:
            log.warning("[N4.2] Translation failed: %s", e)
            self._report.add_stage_result(StageResult(
                stage=N42PipelineStage.TRANSLATION,
                success=False,
                duration_ms=int((time.time() - start) * 1000),
                issues=[f"Translation failed: {str(e)}"],
            ))

    def _stage_layout_adaptation(self) -> None:
        """Stage 4: Layout adaptation."""
        import time
        start = time.time()

        try:
            from services.layout_language_adapter import adapt_layout_for_language

            self.sections, layout_report = adapt_layout_for_language(
                sections=self.sections,
                language=self._target_lang or "de",
                briefing=self.briefing,
            )

            self._report.add_stage_result(StageResult(
                stage=N42PipelineStage.LAYOUT_ADAPTATION,
                success=layout_report.success,
                duration_ms=int((time.time() - start) * 1000),
                warnings=layout_report.warnings,
                metadata={
                    "sections_adapted": layout_report.sections_adapted,
                    "adaptations_applied": layout_report.adaptations_applied,
                },
            ))

        except Exception as e:
            log.warning("[N4.2] Layout adaptation failed: %s", e)
            self._report.add_stage_result(StageResult(
                stage=N42PipelineStage.LAYOUT_ADAPTATION,
                success=False,
                duration_ms=int((time.time() - start) * 1000),
                issues=[f"Layout adaptation failed: {str(e)}"],
            ))

    def _stage_consistency_check(self) -> None:
        """Stage 5: Cross-language consistency check."""
        import time
        start = time.time()

        if not self._original_sections:
            self._report.stages_skipped.append(N42PipelineStage.CONSISTENCY_CHECK)
            return

        try:
            from services.consistency_engine_g22x import check_cross_language_consistency

            consistency_report = check_cross_language_consistency(
                source_sections=self._original_sections,
                target_sections=self.sections,
                briefing=self.briefing,
                source_language=self._source_lang or "de",
                target_language=self._target_lang or "en",
            )

            # Store consistency report
            self.sections["_g22x_report"] = consistency_report.to_dict()

            self._report.add_stage_result(StageResult(
                stage=N42PipelineStage.CONSISTENCY_CHECK,
                success=consistency_report.success,
                duration_ms=int((time.time() - start) * 1000),
                warnings=consistency_report.warnings,
                metadata={
                    "grade": consistency_report.grade,
                    "score": consistency_report.score,
                    "rules_checked": consistency_report.rules_checked,
                },
            ))

        except Exception as e:
            log.warning("[N4.2] Consistency check failed: %s", e)
            self._report.add_stage_result(StageResult(
                stage=N42PipelineStage.CONSISTENCY_CHECK,
                success=False,
                duration_ms=int((time.time() - start) * 1000),
                issues=[f"Consistency check failed: {str(e)}"],
            ))

    def _needs_translation(self) -> bool:
        """Check if translation is needed."""
        if not self._source_lang or not self._target_lang:
            return False
        return self._source_lang != self._target_lang


# =============================================================================
# MODULE-LEVEL FUNCTIONS (Pipeline Hooks)
# =============================================================================

def apply_n42_pipeline(
    sections: SectionDict,
    briefing: BriefingDict,
    source_language: Optional[str] = None,
    target_language: Optional[str] = None,
    enable_translation: bool = True,
) -> Tuple[SectionDict, N42IntegrationReport]:
    """
    Apply full N4.2 pipeline to sections.

    Args:
        sections: Section dictionary
        briefing: Briefing data
        source_language: Source language (auto-detected if None)
        target_language: Target language (from briefing if None)
        enable_translation: Whether to enable translation

    Returns:
        Tuple of (processed_sections, report)
    """
    pipeline = N42Pipeline(
        sections=sections,
        briefing=briefing,
        source_language=source_language,
        target_language=target_language,
        enable_translation=enable_translation,
    )
    return pipeline.process()


def detect_target_language(
    briefing: BriefingDict,
) -> str:
    """
    Detect target language from briefing.

    Hook for early in gpt_analyze.py pipeline.

    Args:
        briefing: Briefing data

    Returns:
        Language code (de, en, fr, it, es)
    """
    try:
        from services.language_strategy_engine import detect_language
        result = detect_language(briefing_input=briefing)
        return result.detected_language.value
    except Exception as e:
        log.warning("[N4.2] Language detection failed: %s", e)
        return briefing.get("lang", "de")


def apply_language_strategy(
    sections: SectionDict,
    briefing: BriefingDict,
    target_language: str = "de",
) -> Tuple[SectionDict, Dict[str, Any]]:
    """
    Apply language strategy to sections.

    Hook for after briefing load in gpt_analyze.py.

    Args:
        sections: Section dictionary
        briefing: Briefing data
        target_language: Target language code

    Returns:
        Tuple of (sections, metadata)
    """
    try:
        from services.language_strategy_engine import LanguageStrategyEngine

        engine = LanguageStrategyEngine(
            sections=sections,
            briefing=briefing,
            target_language=target_language,
        )
        sections, report = engine.process()

        return sections, {
            "success": report.success,
            "language": target_language,
            "model_selections": report.model_selections,
        }
    except Exception as e:
        log.warning("[N4.2] Language strategy failed: %s", e)
        return sections, {"success": False, "error": str(e)}


def apply_translation_pass(
    sections: SectionDict,
    briefing: BriefingDict,
    source_language: str = "de",
    target_language: str = "en",
) -> Tuple[SectionDict, Dict[str, Any]]:
    """
    Apply translation pass to sections.

    Hook for after section generation in gpt_analyze.py.

    Args:
        sections: Section dictionary
        briefing: Briefing data
        source_language: Source language code
        target_language: Target language code

    Returns:
        Tuple of (translated_sections, metadata)
    """
    if source_language == target_language:
        return sections, {"success": True, "skipped": True}

    try:
        from services.translation_engine_v3 import translate_sections

        sections, report = translate_sections(
            sections=sections,
            source_language=source_language,
            target_language=target_language,
            briefing=briefing,
        )

        return sections, {
            "success": report.success,
            "sections_translated": report.sections_translated,
            "quality": report.avg_quality_score,
        }
    except Exception as e:
        log.warning("[N4.2] Translation failed: %s", e)
        return sections, {"success": False, "error": str(e)}


def apply_layout_adaptation(
    sections: SectionDict,
    language: str = "de",
    briefing: Optional[BriefingDict] = None,
) -> Tuple[SectionDict, Dict[str, Any]]:
    """
    Apply layout adaptation to sections.

    Hook for before render in gpt_analyze.py.

    Args:
        sections: Section dictionary
        language: Target language code
        briefing: Optional briefing data

    Returns:
        Tuple of (adapted_sections, metadata)
    """
    try:
        from services.layout_language_adapter import adapt_layout_for_language

        sections, report = adapt_layout_for_language(
            sections=sections,
            language=language,
            briefing=briefing or {},
        )

        return sections, {
            "success": report.success,
            "adaptations": report.adaptations_applied,
        }
    except Exception as e:
        log.warning("[N4.2] Layout adaptation failed: %s", e)
        return sections, {"success": False, "error": str(e)}


def apply_consistency_check(
    source_sections: SectionDict,
    target_sections: SectionDict,
    briefing: BriefingDict,
    source_language: str = "de",
    target_language: str = "en",
) -> Dict[str, Any]:
    """
    Apply cross-language consistency check.

    Hook for before render in gpt_analyze.py.

    Args:
        source_sections: Original sections
        target_sections: Translated sections
        briefing: Briefing data
        source_language: Source language code
        target_language: Target language code

    Returns:
        Consistency check metadata
    """
    if source_language == target_language:
        return {"success": True, "skipped": True}

    try:
        from services.consistency_engine_g22x import check_cross_language_consistency

        report = check_cross_language_consistency(
            source_sections=source_sections,
            target_sections=target_sections,
            briefing=briefing,
            source_language=source_language,
            target_language=target_language,
        )

        return {
            "success": report.success,
            "grade": report.grade,
            "score": report.score,
            "issues": len(report.issues),
        }
    except Exception as e:
        log.warning("[N4.2] Consistency check failed: %s", e)
        return {"success": False, "error": str(e)}


def get_n42_version() -> str:
    """Get N4.2 version string."""
    return N42_VERSION
