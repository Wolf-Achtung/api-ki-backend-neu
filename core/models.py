# -*- coding: utf-8 -*-
from __future__ import annotations
from datetime import datetime, timedelta
from typing import Optional

from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text
from sqlalchemy.dialects.sqlite import JSON as SQLITE_JSON
from sqlalchemy.types import JSON as PG_JSON

from core.db import Base

def JsonType():
    try:
        # Use PG JSON when available (postgres), else sqlite JSON (Text)
        import sqlalchemy.dialects.postgresql as pg
        return PG_JSON
    except Exception:
        return SQLITE_JSON

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(320), unique=True, nullable=False, index=True)
    is_admin = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

class OneTimeCode(Base):
    __tablename__ = "one_time_codes"
    id = Column(Integer, primary_key=True)
    email = Column(String(320), index=True, nullable=False)
    code = Column(String(12), nullable=False)
    expires_at = Column(DateTime, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

class Briefing(Base):
    __tablename__ = "briefings"
    id = Column(Integer, primary_key=True)
    user_email = Column(String(320), index=True)
    payload = Column(JsonType())
    lang = Column(String(8), default="de")
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

class Report(Base):
    __tablename__ = "reports"
    id = Column(Integer, primary_key=True)
    user_email = Column(String(320), index=True)
    briefing_id = Column(Integer, nullable=True)
    html_len = Column(Integer, default=0)
    pdf_url = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
