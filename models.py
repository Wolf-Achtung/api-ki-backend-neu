# file: app/models.py
# -*- coding: utf-8 -*-
from __future__ import annotations
"""
SQLAlchemy‑Modelle, Portabilität: Postgres JSONB mit Fallback auf generisches JSON (z. B. SQLite).
Warum: Dev/CI ohne Postgres soll nicht brechen.
"""

from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import (
    Boolean, DateTime, ForeignKey, Integer, String, Text,
    UniqueConstraint, Index
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

# Import Base aus core.db (KRITISCH für DB-Kompatibilität!)
from core.db import Base

# Fallback für nicht‑Postgres‑Umgebungen
try:
    from sqlalchemy.dialects.postgresql import JSONB as JSONType  # Postgres bevorzugt
except Exception:  # pragma: no cover
    from sqlalchemy.types import JSON as JSONType  # z. B. SQLite





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

    user = relationship("User", lazy="joined")

    def __repr__(self) -> str:  # pragma: no cover
        return f"<Briefing id={self.id} user_id={self.user_id}>"


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
