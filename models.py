# file: app/models.py
# -*- coding: utf-8 -*-
from __future__ import annotations
"""
SQLAlchemy‑Modelle, Portabilität: Postgres JSONB mit Fallback auf generisches JSON (z. B. SQLite).
Warum: Dev/CI ohne Postgres soll nicht brechen.
"""

from datetime import datetime, timezone
from typing import Any, Optional

from sqlalchemy import (
    Boolean, DateTime, ForeignKey, Integer, String, Text,
    UniqueConstraint, Index
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

# Import Base aus core.db (KRITISCH für DB-Kompatibilität!)
from core.db import Base, is_sqlite

# Dynamische JSON-Type-Auswahl basierend auf der Datenbank
if is_sqlite:
    from sqlalchemy.types import JSON as JSONType  # SQLite verwendet JSON
else:
    try:
        from sqlalchemy.dialects.postgresql import JSONB as JSONType  # Postgres bevorzugt
    except ImportError:  # pragma: no cover
        from sqlalchemy.types import JSON as JSONType  # Fallback





class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    email: Mapped[str] = mapped_column(String(320), unique=True, index=True, nullable=False)
    is_admin: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False
    )

    def __repr__(self) -> str:  # pragma: no cover
        return f"<User id={self.id} email={self.email!r}>"


class Briefing(Base):
    __tablename__ = "briefings"
    __table_args__ = (
        Index("ix_briefings_status_accepted_at", "status", "accepted_at"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True
    )
    lang: Mapped[str] = mapped_column(String(5), default="de", nullable=False)
    answers: Mapped[dict] = mapped_column(JSONType, default=dict, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False
    )

    # Worker-Queue Status Fields (Sprint: DB-Backed Worker)
    status: Mapped[str] = mapped_column(
        String(20), default="accepted", nullable=False, index=True
    )
    accepted_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=True
    )
    processing_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    done_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    error: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    worker_id: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)

    user = relationship("User", lazy="joined")

    def __repr__(self) -> str:  # pragma: no cover
        return f"<Briefing id={self.id} status={self.status!r} user_id={self.user_id}>"


class Analysis(Base):
    __tablename__ = "analyses"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True
    )
    briefing_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("briefings.id", ondelete="SET NULL"), nullable=True, index=True
    )
    html: Mapped[str] = mapped_column(Text, nullable=False)
    meta: Mapped[dict] = mapped_column(JSONType, default=dict, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False
    )

    user = relationship("User", lazy="joined")
    briefing = relationship("Briefing", lazy="joined")

    @property
    def sections(self) -> dict:
        """Return sections from meta JSON. Supports dict or JSON string."""
        sections_data = (self.meta or {}).get("sections")
        if sections_data is None:
            return {}
        if isinstance(sections_data, dict):
            return sections_data
        if isinstance(sections_data, str):
            import json
            try:
                parsed = json.loads(sections_data)
                return parsed if isinstance(parsed, dict) else {}
            except (json.JSONDecodeError, ValueError):
                return {}
        return {}

    def __repr__(self) -> str:  # pragma: no cover
        return f"<Analysis id={self.id} briefing_id={self.briefing_id}>"


class Report(Base):
    __tablename__ = "reports"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True
    )
    user_email: Mapped[Optional[str]] = mapped_column(String(320), nullable=True)
    briefing_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("briefings.id", ondelete="SET NULL"), nullable=True, index=True
    )
    analysis_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("analyses.id", ondelete="SET NULL"), nullable=True, index=True
    )
    task_id: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    status: Mapped[str] = mapped_column(String(32), default="pending", nullable=False)
    pdf_url: Mapped[Optional[str]] = mapped_column(String(1024), nullable=True)
    pdf_bytes_len: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    email_sent_user: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    email_sent_admin: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    email_error_user: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    email_error_admin: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False
    )
    updated_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    user = relationship("User", lazy="joined")
    briefing = relationship("Briefing", lazy="joined")
    analysis = relationship("Analysis", lazy="joined")

    def __repr__(self) -> str:  # pragma: no cover
        return f"<Report id={self.id} status={self.status!r}>"


class LoginCode(Base):
    __tablename__ = "login_codes"
    __table_args__ = (
        UniqueConstraint("code", name="uq_login_codes_code"),
        Index("ix_login_codes_email", "email"),
        Index("ix_login_codes_expires_at", "expires_at"),
        Index("ix_login_codes_consumed_at", "consumed_at"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    email: Mapped[str] = mapped_column(String(320), nullable=False)
    code: Mapped[str] = mapped_column(String(64), nullable=False)
    purpose: Mapped[str] = mapped_column(String(40), default="login", nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False
    )
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    consumed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    attempts: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    ip_address: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    user_agent: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    def __repr__(self) -> str:  # pragma: no cover
        state = "consumed" if self.consumed_at else "active"
        return f"<LoginCode email={self.email!r} state={state} purpose={self.purpose!r}>"


class Feedback(Base):
    """
    Feedback submissions from users.

    Stores user feedback about reports, UX, and general comments.
    The payload field contains the full JSON submission.
    """
    __tablename__ = "feedbacks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    payload: Mapped[dict] = mapped_column(JSONType, default=dict, nullable=False)
    source: Mapped[str] = mapped_column(String(64), default="feedback_form_v1", nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False
    )

    def __repr__(self) -> str:  # pragma: no cover
        return f"<Feedback id={self.id} source={self.source!r}>"


# =============================================================================
# SPRINT G11: REPORT HISTORY & VERSIONING
# =============================================================================

class ReportHistory(Base):
    """
    Sprint G11: Report versioning and history tracking.

    Stores complete snapshots of reports for version comparison,
    delta analysis, and historical tracking.
    """
    __tablename__ = "reports_history"
    __table_args__ = (
        Index("ix_reports_history_user_report", "user_id", "report_id"),
        Index("ix_reports_history_created_at", "created_at"),
        UniqueConstraint("report_id", "version", name="uq_report_version"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True
    )
    report_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("reports.id", ondelete="CASCADE"), nullable=False, index=True
    )
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)

    # Core scores (Governance, Security, Benefit, etc.)
    scores_json: Mapped[dict] = mapped_column(JSONType, default=dict, nullable=False)

    # Business Case data (CAPEX, OPEX, ROI, Payback)
    bc_json: Mapped[dict] = mapped_column(JSONType, default=dict, nullable=False)

    # AI Act compliance data (Risk Level, Modifiers, Metrics)
    ai_act_json: Mapped[dict] = mapped_column(JSONType, default=dict, nullable=False)

    # Labels (BRANCH_*, OFFERING_*, CR_LABELS)
    labels_json: Mapped[dict] = mapped_column(JSONType, default=dict, nullable=False)

    # Section word counts for delta comparison
    section_stats_json: Mapped[dict] = mapped_column(JSONType, default=dict, nullable=False)

    # File paths
    html_path: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)
    pdf_path: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)

    # Metadata
    lang: Mapped[str] = mapped_column(String(5), default="de", nullable=False)
    size_category: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False
    )

    # Relationships
    user = relationship("User", lazy="joined")
    report = relationship("Report", lazy="joined")

    def __repr__(self) -> str:  # pragma: no cover
        return f"<ReportHistory report_id={self.report_id} version={self.version}>"

    def to_dict(self) -> dict:
        """Convert to dictionary for API responses."""
        return {
            "id": self.id,
            "user_id": self.user_id,
            "report_id": self.report_id,
            "version": self.version,
            "scores": self.scores_json,
            "business_case": self.bc_json,
            "ai_act": self.ai_act_json,
            "labels": self.labels_json,
            "section_stats": self.section_stats_json,
            "html_path": self.html_path,
            "pdf_path": self.pdf_path,
            "lang": self.lang,
            "size_category": self.size_category,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


# =============================================================================
# REPORT 3: KI-STRATEGIEBERICHT
# =============================================================================

class StrategyQuestion(Base):
    """
    Report 3: Additional strategy questions (S1-S10) per briefing.
    """
    __tablename__ = "strategy_questions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    briefing_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("briefings.id", ondelete="CASCADE"), nullable=False, index=True, unique=True
    )

    # Pflichtfragen S1-S7
    s1_budget: Mapped[str] = mapped_column(String(50), nullable=False)
    s2_zeitrahmen: Mapped[str] = mapped_column(String(50), nullable=False)
    s3_prioritaeten: Mapped[Any] = mapped_column(JSONType, nullable=False)  # JSONB: stores list[str]
    s4_engpass: Mapped[str] = mapped_column(String(100), nullable=False)
    s5_software: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    s6_foerderinteresse: Mapped[str] = mapped_column(String(50), nullable=False)
    s7_entscheidung: Mapped[str] = mapped_column(String(100), nullable=False)

    # Optionale Fragen S8-S10
    s8_erfahrung: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    s9_ansatz: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    s10_datenschutz: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)

    # Metadaten
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False
    )

    briefing = relationship("Briefing", lazy="joined")

    def __repr__(self) -> str:  # pragma: no cover
        return f"<StrategyQuestion id={self.id} briefing_id={self.briefing_id}>"

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "briefing_id": self.briefing_id,
            "s1_budget": self.s1_budget,
            "s2_zeitrahmen": self.s2_zeitrahmen,
            "s3_prioritaeten": self.s3_prioritaeten,
            "s4_engpass": self.s4_engpass,
            "s5_software": self.s5_software,
            "s6_foerderinteresse": self.s6_foerderinteresse,
            "s7_entscheidung": self.s7_entscheidung,
            "s8_erfahrung": self.s8_erfahrung,
            "s9_ansatz": self.s9_ansatz,
            "s10_datenschutz": self.s10_datenschutz,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class StrategyReport(Base):
    """
    Report 3: Strategy report status, cached data, generated sections, and PDF/email tracking.
    """
    __tablename__ = "strategy_reports"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    briefing_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("briefings.id", ondelete="CASCADE"), nullable=False, index=True, unique=True
    )

    # Status
    status: Mapped[str] = mapped_column(String(30), default="pending", nullable=False, index=True)

    # Recherche-Ergebnisse (JSON, gecached)
    research_context: Mapped[Optional[dict]] = mapped_column(JSONType, nullable=True)

    # Berechnete Werte (vom Backend-Calculator)
    calculated_values: Mapped[Optional[dict]] = mapped_column(JSONType, nullable=True)

    # Generierte Sections (JSON, jede Section separat)
    sections: Mapped[Optional[dict]] = mapped_column(JSONType, nullable=True)

    # Rohe LLM-Outputs VOR Sanitizer (für Re-Render und Sanitizer-Iteration)
    raw_sections: Mapped[Optional[dict]] = mapped_column(JSONType, nullable=True)

    # PDF
    pdf_available: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    pdf_generated_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # Email
    email_sent: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    email_sent_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # Timing
    research_duration_seconds: Mapped[Optional[float]] = mapped_column(nullable=True)
    generation_duration_seconds: Mapped[Optional[float]] = mapped_column(nullable=True)
    total_duration_seconds: Mapped[Optional[float]] = mapped_column(nullable=True)

    # Payment (Platzhalter für Mollie)
    payment_status: Mapped[str] = mapped_column(String(30), default="beta", nullable=False)
    payment_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    # Metadaten
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False
    )
    updated_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    briefing = relationship("Briefing", lazy="joined")

    def __repr__(self) -> str:  # pragma: no cover
        return f"<StrategyReport id={self.id} briefing_id={self.briefing_id} status={self.status!r}>"

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "briefing_id": self.briefing_id,
            "status": self.status,
            "pdf_available": self.pdf_available,
            "email_sent": self.email_sent,
            "research_duration_seconds": self.research_duration_seconds,
            "generation_duration_seconds": self.generation_duration_seconds,
            "total_duration_seconds": self.total_duration_seconds,
            "payment_status": self.payment_status,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
