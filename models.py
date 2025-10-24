# -*- coding: utf-8 -*-
from __future__ import annotations
from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, ForeignKey
from sqlalchemy.orm import declarative_base, relationship, Mapped, mapped_column
from sqlalchemy.dialects.postgresql import JSONB

Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    email: Mapped[str] = mapped_column(String(320), unique=True, index=True, nullable=False)
    is_admin: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

class Briefing(Base):
    __tablename__ = "briefings"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    lang: Mapped[str] = mapped_column(String(5), default="de", nullable=False)
    answers = mapped_column(JSONB, nullable=False, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

class Analysis(Base):
    __tablename__ = "analyses"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    briefing_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("briefings.id", ondelete="SET NULL"), nullable=True, index=True)
    html: Mapped[str] = mapped_column(Text, nullable=False)
    meta = mapped_column(JSONB, nullable=False, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

class Report(Base):
    __tablename__ = "reports"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    user_email: Mapped[str | None] = mapped_column(String(320), nullable=True)  # <- wichtig gegen NOT NULL-Fehler
    briefing_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("briefings.id", ondelete="SET NULL"), nullable=True, index=True)
    analysis_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("analyses.id", ondelete="SET NULL"), nullable=True, index=True)
    task_id: Mapped[str | None] = mapped_column(String(128), nullable=True)
    status: Mapped[str] = mapped_column(String(32), default="pending", nullable=False)
    pdf_url: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    pdf_bytes_len: Mapped[int | None] = mapped_column(Integer, nullable=True)
    email_sent_user: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    email_sent_admin: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    email_error_user: Mapped[str | None] = mapped_column(Text, nullable=True)
    email_error_admin: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
