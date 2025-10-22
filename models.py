# -*- coding: utf-8 -*-
from __future__ import annotations
from datetime import datetime, timedelta
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, ForeignKey
from sqlalchemy.dialects.sqlite import JSON as SQLITE_JSON
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship, Mapped, mapped_column
from sqlalchemy import types as sqltypes
from core.db import Base

# JSON type portable
class JSONType(sqltypes.TypeDecorator):
    impl = SQLITE_JSON
    cache_ok = True
    def load_dialect_impl(self, dialect):
        if dialect.name == "postgresql":
            return dialect.type_descriptor(JSONB(astext_type=sqltypes.Text()))
        return dialect.type_descriptor(SQLITE_JSON())

class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    email: Mapped[str] = mapped_column(String(320), unique=True, index=True, nullable=False)
    is_admin: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    last_login_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    briefings = relationship("Briefing", back_populates="user")

class LoginCode(Base):
    __tablename__ = "login_codes"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    code_hash: Mapped[str] = mapped_column(String(128), nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    used: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

class Briefing(Base):
    __tablename__ = "briefings"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    lang: Mapped[str] = mapped_column(String(5), default="de", nullable=False)
    answers: Mapped[dict] = mapped_column(JSONType, nullable=False, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    user = relationship("User", back_populates="briefings")
    analyses = relationship("Analysis", back_populates="briefing")

class Analysis(Base):
    __tablename__ = "analyses"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    briefing_id: Mapped[int] = mapped_column(Integer, ForeignKey("briefings.id", ondelete="SET NULL"), nullable=True, index=True)
    html: Mapped[str] = mapped_column(Text, nullable=False)
    meta: Mapped[dict] = mapped_column(JSONType, nullable=False, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    briefing = relationship("Briefing", back_populates="analyses")

class Report(Base):
    __tablename__ = "reports"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    briefing_id: Mapped[int] = mapped_column(Integer, ForeignKey("briefings.id", ondelete="SET NULL"), nullable=True, index=True)
    analysis_id: Mapped[int] = mapped_column(Integer, ForeignKey("analyses.id", ondelete="SET NULL"), nullable=True, index=True)
    pdf_url: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    pdf_bytes_len: Mapped[int | None] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
