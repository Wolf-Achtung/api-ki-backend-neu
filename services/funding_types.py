# -*- coding: utf-8 -*-
"""
Funding Types - Unified type definitions for funding services.

This module provides type-safe dataclasses for funding programme data,
ensuring consistent structure across DE, EN-DE, and EU-Core funding flows.

Version: 1.0.0
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Literal, Optional


# =============================================================================
# Core Funding Programme Types
# =============================================================================


@dataclass
class FundingProgram:
    """
    Unified representation of a funding programme.

    Supports both German and English fields for bilingual handling.
    All fields are optional except 'id' to allow gradual migration.
    """

    id: str

    # English fields (primary for EN reports)
    name_en: Optional[str] = None
    summary_en: Optional[str] = None
    funding_type_en: Optional[str] = None
    funding_rate_en: Optional[str] = None
    max_amount_en: Optional[str] = None
    region_en: Optional[str] = None
    regions_en: Optional[List[str]] = None
    notes_en: Optional[str] = None
    ai_relevance_en: Optional[str] = None
    target_groups_en: Optional[List[str]] = None

    # German fields (primary for DE reports)
    name_de: Optional[str] = None
    title: Optional[str] = None  # Legacy DE field
    summary_de: Optional[str] = None
    focus: Optional[str] = None  # Legacy DE field
    funding_type_de: Optional[str] = None
    funding_rate_de: Optional[str] = None
    max_amount_de: Optional[str] = None
    region_de: Optional[str] = None
    region_label: Optional[str] = None  # Legacy DE field
    notes_de: Optional[str] = None

    # Common fields
    region: Optional[str] = None  # Region code (e.g., "DE", "BY", "EU")
    max_amount: Optional[int] = None  # Numeric amount for filtering
    priority: int = 99
    relevance_ki: Optional[str] = None  # "high", "medium", "low"
    suitable_for: Optional[List[str]] = None  # ["solo", "team", "kmu"]
    url: Optional[str] = None

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "FundingProgram":
        """Create FundingProgram from dictionary, handling legacy field names."""
        return cls(
            id=data.get("id", "unknown"),
            # EN fields
            name_en=data.get("name_en"),
            summary_en=data.get("summary_en"),
            funding_type_en=data.get("funding_type_en"),
            funding_rate_en=data.get("funding_rate_en"),
            max_amount_en=data.get("max_amount_en"),
            region_en=data.get("region_en"),
            regions_en=data.get("regions_en"),
            notes_en=data.get("notes_en"),
            ai_relevance_en=data.get("ai_relevance_en"),
            target_groups_en=data.get("target_groups_en"),
            # DE fields
            name_de=data.get("name_de"),
            title=data.get("title"),
            summary_de=data.get("summary_de"),
            focus=data.get("focus"),
            funding_type_de=data.get("funding_type"),
            funding_rate_de=data.get("funding_rate"),
            max_amount_de=data.get("max_amount_display"),
            region_de=data.get("region_de"),
            region_label=data.get("region_label"),
            notes_de=data.get("notes"),
            # Common
            region=data.get("region"),
            max_amount=data.get("max_amount"),
            priority=data.get("priority", 99),
            relevance_ki=data.get("relevance_ki"),
            suitable_for=data.get("suitable_for"),
            url=data.get("url"),
        )

    def get_name(self, lang: str = "de") -> str:
        """Get programme name for specified language."""
        if lang == "en":
            return self.name_en or self.name_de or self.title or self.id
        return self.name_de or self.title or self.name_en or self.id

    def get_summary(self, lang: str = "de") -> str:
        """Get programme summary for specified language."""
        if lang == "en":
            return self.summary_en or self.focus or ""
        return self.summary_de or self.focus or self.summary_en or ""


# =============================================================================
# Funding Result Types
# =============================================================================

FundingScope = Literal["DE", "DE_EN", "EU_CORE"]


@dataclass
class FundingResult:
    """
    Result of funding programme matching.

    Unified result type for all funding flows (DE, EN-DE, EU-Core).
    """

    programmes: List[FundingProgram] = field(default_factory=list)
    country: str = "DE"
    language: str = "de"
    scope: FundingScope = "DE"
    error: Optional[str] = None

    @property
    def has_programmes(self) -> bool:
        """Check if any programmes were found."""
        return len(self.programmes) > 0

    @property
    def programme_count(self) -> int:
        """Return number of matched programmes."""
        return len(self.programmes)

    @classmethod
    def from_programme_dicts(
        cls,
        programmes: List[Dict[str, Any]],
        country: str = "DE",
        language: str = "de",
        scope: FundingScope = "DE",
    ) -> "FundingResult":
        """Create FundingResult from list of programme dictionaries."""
        return cls(
            programmes=[FundingProgram.from_dict(p) for p in programmes],
            country=country,
            language=language,
            scope=scope,
        )


# =============================================================================
# Rendering Types
# =============================================================================


@dataclass
class FundingProgramView:
    """
    View model for rendering a funding programme.

    Simplified, language-specific representation for HTML rendering.
    """

    id: str
    name: str
    summary: str
    funding_type: Optional[str] = None
    funding_rate: Optional[str] = None
    max_amount: Optional[str] = None
    scope_label: Optional[str] = None  # e.g., "Germany", "EU-wide", "Bavaria"
    region: Optional[str] = None
    notes: Optional[str] = None
    ai_relevance: Optional[str] = None
    target_groups: Optional[List[str]] = None
    url: Optional[str] = None

    @classmethod
    def from_program(
        cls, program: FundingProgram, lang: str = "de", scope_label: Optional[str] = None
    ) -> "FundingProgramView":
        """Create view from FundingProgram for specified language."""
        if lang == "en":
            return cls(
                id=program.id,
                name=program.get_name("en"),
                summary=program.get_summary("en"),
                funding_type=program.funding_type_en,
                funding_rate=program.funding_rate_en,
                max_amount=program.max_amount_en,
                scope_label=scope_label or program.region_en or "Germany",
                region=program.region_en,
                notes=program.notes_en,
                ai_relevance=program.ai_relevance_en,
                target_groups=program.target_groups_en,
                url=program.url,
            )
        else:
            return cls(
                id=program.id,
                name=program.get_name("de"),
                summary=program.get_summary("de"),
                funding_type=program.funding_type_de,
                funding_rate=program.funding_rate_de,
                max_amount=program.max_amount_de,
                scope_label=scope_label or program.region_label or program.region_de,
                region=program.region_de or program.region_label,
                notes=program.notes_de,
                ai_relevance=program.relevance_ki,
                target_groups=None,
                url=program.url,
            )

    @classmethod
    def from_dict(
        cls, data: Dict[str, Any], lang: str = "de", scope_label: Optional[str] = None
    ) -> "FundingProgramView":
        """Create view directly from dictionary for backwards compatibility."""
        program = FundingProgram.from_dict(data)
        return cls.from_program(program, lang, scope_label)


@dataclass
class FundingRenderContext:
    """
    Context for rendering funding programmes.

    Provides all information needed to render funding HTML.
    """

    scope: FundingScope
    programmes: List[FundingProgramView]
    lang: str = "de"
    country: Optional[str] = None
    title: Optional[str] = None  # Optional override for section title
    show_disclaimer: bool = False  # For EU-Core

    @property
    def has_programmes(self) -> bool:
        """Check if there are programmes to render."""
        return len(self.programmes) > 0

    @property
    def programme_count(self) -> int:
        """Return number of programmes."""
        return len(self.programmes)
